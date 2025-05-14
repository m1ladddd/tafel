import sys
import json
import random
import time
from threading import Thread
import paho.mqtt.client as mqtt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QLabel, QPushButton, QComboBox, QSlider, QGraphicsView, 
                               QGraphicsScene, QGraphicsItem, QGraphicsEllipseItem, 
                               QGraphicsLineItem, QGroupBox)
from PySide6.QtGui import QPen, QBrush, QColor, QPainter
from PySide6.QtCore import Qt, QTimer, QPointF, Signal, Slot, QRectF, QLineF

class PowerNode(QGraphicsEllipseItem):
    """Represents a node (bus) in the power grid"""
    
    NODE_TYPES = {
        "generator": QColor(50, 205, 50),  # Green
        "load": QColor(255, 99, 71),       # Red
        "bus": QColor(135, 206, 250),      # Light blue
        "storage": QColor(255, 215, 0),    # Gold
        "transformer": QColor(210, 180, 140)  # Tan
    }
    
    def __init__(self, x, y, node_type="bus", name="", power=0.0, voltage=0.0):
        super().__init__(0, 0, 30, 30)
        self.setPos(x - 15, y - 15)  # Center at the x,y coordinates
        self.node_type = node_type
        self.name = name
        self.power = power  # Power generation/consumption in MW
        self.voltage = voltage  # Voltage in kV
        self.setBrush(QBrush(self.NODE_TYPES.get(node_type, QColor(200, 200, 200))))
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        painter.setPen(Qt.black)
        
        # Draw the node name in the center
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        
        # Add text showing node name and power (if available)
        if abs(self.power) > 0.001:  # Only show power if non-zero
            text = f"{self.name}\n{self.power:.2f} MW"
        else:
            text = self.name
            
        painter.drawText(self.boundingRect(), Qt.AlignCenter, text)


class PowerLine(QGraphicsLineItem):
    """Represents a power line in the grid"""
    
    def __init__(self, x1, y1, x2, y2, power_flow=0.0, capacity=100.0, name=""):
        super().__init__(x1, y1, x2, y2)
        self.power_flow = power_flow  # Power flow in MW
        self.capacity = capacity      # Line capacity in MW
        self.name = name
        self.update_appearance()
        self.setZValue(-1)  # Make sure lines are drawn under nodes
        
    def update_appearance(self):
        # Line thickness based on capacity
        thickness = max(1, min(8, int(self.capacity / 20)))
        
        # Line color based on power flow as percent of capacity
        if abs(self.capacity) < 0.001:  # Avoid division by zero
            load_percent = 0
        else:
            load_percent = abs(self.power_flow) / self.capacity * 100
            
        if load_percent > 90:
            color = QColor(255, 0, 0)  # Red (overloaded)
        elif load_percent > 75:
            color = QColor(255, 165, 0)  # Orange (high load)
        elif load_percent > 50:
            color = QColor(255, 255, 0)  # Yellow (medium load)
        else:
            color = QColor(0, 128, 0)  # Green (low load)
            
        self.setPen(QPen(color, thickness))
        
    def set_power_flow(self, power_flow):
        self.power_flow = power_flow
        self.update_appearance()


class NetworkView(QGraphicsView):
    """Custom QGraphicsView for displaying and interacting with the power network"""
    
    node_clicked = Signal(str)  # Signal emitted when a node is clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.nodes = {}  # Dictionary to store nodes by name
        self.lines = {}  # Dictionary to store lines by name
        self.setMinimumSize(600, 400)
        
    def wheelEvent(self, event):
        # Implement zoom functionality
        zoom_factor = 1.1
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1 / zoom_factor, 1 / zoom_factor)
            
    def mousePressEvent(self, event):
        # Call the parent implementation to maintain drag functionality
        super().mousePressEvent(event)
        
        # Check if a node was clicked
        item = self.itemAt(event.pos())
        if isinstance(item, PowerNode) and item.isSelected():
            self.node_clicked.emit(item.name)
            
    def clear_network(self):
        self.scene().clear()
        self.nodes.clear()
        self.lines.clear()
        
    def add_node(self, name, x, y, node_type="bus", power=0.0, voltage=0.0):
        """Add a node to the network"""
        node = PowerNode(x, y, node_type, name, power, voltage)
        self.scene().addItem(node)
        self.nodes[name] = node
        return node
        
    def add_line(self, name, node1_name, node2_name, power_flow=0.0, capacity=100.0):
        """Add a line between two nodes"""
        if node1_name in self.nodes and node2_name in self.nodes:
            node1 = self.nodes[node1_name]
            node2 = self.nodes[node2_name]
            
            # Get the center points of the nodes
            x1 = node1.pos().x() + 15
            y1 = node1.pos().y() + 15
            x2 = node2.pos().x() + 15
            y2 = node2.pos().y() + 15
            
            line = PowerLine(x1, y1, x2, y2, power_flow, capacity, name)
            self.scene().addItem(line)
            self.lines[name] = line
            return line
            
        return None
        
    def update_node(self, name, power=None, voltage=None, node_type=None):
        """Update an existing node's properties"""
        if name in self.nodes:
            node = self.nodes[name]
            if power is not None:
                node.power = power
            if voltage is not None:
                node.voltage = voltage
            if node_type is not None:
                node.node_type = node_type
                node.setBrush(QBrush(PowerNode.NODE_TYPES.get(node_type, QColor(200, 200, 200))))
            self.scene().update()
            
    def update_line(self, name, power_flow=None, capacity=None):
        """Update an existing line's properties"""
        if name in self.lines:
            line = self.lines[name]
            if power_flow is not None:
                line.power_flow = power_flow
            if capacity is not None:
                line.capacity = capacity
            line.update_appearance()
            self.scene().update()
            
    def create_example_network(self):
        """Create an example network for testing"""
        self.clear_network()
        
        # Add some nodes
        self.add_node("Generator 1", 100, 100, "generator", 40.0)
        self.add_node("Load 1", 300, 100, "load", -15.0)
        self.add_node("Bus 1", 200, 200, "bus")
        self.add_node("Storage 1", 400, 200, "storage", 5.0)
        self.add_node("Transformer 1", 300, 300, "transformer")
        
        # Add lines between nodes
        self.add_line("Line 1", "Generator 1", "Bus 1", 25.0, 50.0)
        self.add_line("Line 2", "Bus 1", "Load 1", 15.0, 20.0)
        self.add_line("Line 3", "Bus 1", "Storage 1", 10.0, 30.0)
        self.add_line("Line 4", "Storage 1", "Transformer 1", 5.0, 40.0)
        self.add_line("Line 5", "Transformer 1", "Load 1", 5.0, 40.0)
        
        # Set view to fit all items
        self.fitInView(self.scene().itemsBoundingRect(), Qt.KeepAspectRatio)


class MQTTClient:
    """Handles MQTT communication with the simulation backend"""
    
    def __init__(self, broker="localhost", port=1883, topic_prefix="SmartDemoTable2"):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.connected = False
        self.message_callbacks = []
        
    def connect(self):
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT broker")
            self.connected = True
            # Subscribe to relevant topics
            self.client.subscribe(f"{self.topic_prefix}/GUI/Outgoing")
            self.client.subscribe(f"{self.topic_prefix}/+/Outgoing")
        else:
            print(f"Failed to connect to MQTT broker with result code {rc}")
            
    def on_message(self, client, userdata, msg):
        try:
            # Decode the message
            message = msg.payload.decode("utf-8")
            topic = msg.topic
            
            # Try to parse as JSON if possible
            try:
                data = json.loads(message)
                parsed_message = data
            except json.JSONDecodeError:
                parsed_message = message
                
            # Notify all registered callbacks
            for callback in self.message_callbacks:
                callback(topic, parsed_message)
                
        except Exception as e:
            print(f"Error processing message: {e}")
            
    def publish(self, subtopic, message):
        """Publish a message to a specific subtopic"""
        if isinstance(message, dict):
            message = json.dumps(message)
            
        topic = f"{self.topic_prefix}/GUI/Ingoing"
        if subtopic:
            topic = f"{self.topic_prefix}/{subtopic}"
            
        self.client.publish(topic, message)
        
    def register_callback(self, callback):
        """Register a function to be called when a message is received"""
        if callback not in self.message_callbacks:
            self.message_callbacks.append(callback)


class SmartGridVisualizer(QMainWindow):
    """Main application window for visualizing the smart grid"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Grid Visualizer")
        self.resize(1000, 700)
        
        # Initialize MQTT client
        self.mqtt_client = MQTTClient()
        self.mqtt_client.register_callback(self.handle_mqtt_message)
        
        # Main widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create UI components
        self.create_toolbar(main_layout)
        self.create_network_view(main_layout)
        self.create_control_panel(main_layout)
        self.create_status_bar()
        
        # Timer for simulation when in demo mode
        self.simulation_timer = QTimer(self)
        self.simulation_timer.timeout.connect(self.update_simulation)
        self.simulation_active = False
        
        # Connect to MQTT broker
        self.mqtt_connected = False
        self.connect_to_mqtt()
        
    def create_toolbar(self, layout):
        """Create the toolbar with simulation controls"""
        toolbar_layout = QHBoxLayout()
        
        # Scenario selection
        scenario_label = QLabel("Scenario:")
        self.scenario_combo = QComboBox()
        self.scenario_combo.addItems(["Simple Network", "Residential Area", "Industrial Grid", "Renewable Integration"])
        
        # Control buttons
        self.connect_button = QPushButton("Connect to Simulation")
        self.connect_button.clicked.connect(self.toggle_mqtt_connection)
        
        self.start_button = QPushButton("Start Simulation")
        self.start_button.clicked.connect(self.start_simulation)
        self.start_button.setEnabled(False)
        
        self.stop_button = QPushButton("Stop Simulation")
        self.stop_button.clicked.connect(self.stop_simulation)
        self.stop_button.setEnabled(False)
        
        self.demo_button = QPushButton("Demo Mode")
        self.demo_button.clicked.connect(self.toggle_demo_mode)
        
        # Add components to toolbar
        toolbar_layout.addWidget(scenario_label)
        toolbar_layout.addWidget(self.scenario_combo)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.connect_button)
        toolbar_layout.addWidget(self.start_button)
        toolbar_layout.addWidget(self.stop_button)
        toolbar_layout.addWidget(self.demo_button)
        
        layout.addLayout(toolbar_layout)
        
    def create_network_view(self, layout):
        """Create the network visualization view"""
        self.network_view = NetworkView()
        self.network_view.node_clicked.connect(self.handle_node_clicked)
        layout.addWidget(self.network_view, 1)  # Give it a stretch factor of 1
        
        # Create a demo network initially
        self.network_view.create_example_network()
        
    def create_control_panel(self, layout):
        """Create the control panel for adjusting simulation parameters"""
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Network statistics group
        stats_group = QGroupBox("Network Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.total_generation_label = QLabel("Total Generation: 0 MW")
        self.total_load_label = QLabel("Total Load: 0 MW")
        self.line_utilization_label = QLabel("Avg. Line Utilization: 0%")
        
        stats_layout.addWidget(self.total_generation_label)
        stats_layout.addWidget(self.total_load_label)
        stats_layout.addWidget(self.line_utilization_label)
        
        # Generator control group
        gen_group = QGroupBox("Generator Control")
        gen_layout = QVBoxLayout(gen_group)
        
        gen_layout.addWidget(QLabel("Generator 1 Output:"))
        self.gen1_slider = QSlider(Qt.Horizontal)
        self.gen1_slider.setRange(0, 100)
        self.gen1_slider.setValue(40)
        self.gen1_slider.valueChanged.connect(lambda v: self.update_generator("Generator 1", v))
        gen_layout.addWidget(self.gen1_slider)
        
        gen_layout.addWidget(QLabel("Storage 1 Output:"))
        self.storage_slider = QSlider(Qt.Horizontal)
        self.storage_slider.setRange(-50, 50)
        self.storage_slider.setValue(5)
        self.storage_slider.valueChanged.connect(lambda v: self.update_generator("Storage 1", v))
        gen_layout.addWidget(self.storage_slider)
        
        # Load control group
        load_group = QGroupBox("Load Control")
        load_layout = QVBoxLayout(load_group)
        
        load_layout.addWidget(QLabel("Load 1 Demand:"))
        self.load1_slider = QSlider(Qt.Horizontal)
        self.load1_slider.setRange(0, 50)
        self.load1_slider.setValue(15)
        self.load1_slider.valueChanged.connect(lambda v: self.update_load("Load 1", v))
        load_layout.addWidget(self.load1_slider)
        
        # Add groups to control panel
        control_layout.addWidget(stats_group)
        control_layout.addWidget(gen_group)
        control_layout.addWidget(load_group)
        
        layout.addWidget(control_panel)
        
    def create_status_bar(self):
        """Create the status bar at the bottom of the window"""
        self.statusBar().showMessage("Ready")
        
    def connect_to_mqtt(self):
        """Connect to the MQTT broker"""
        success = self.mqtt_client.connect()
        if success:
            self.mqtt_connected = True
            self.connect_button.setText("Disconnect from Simulation")
            self.start_button.setEnabled(True)
            self.statusBar().showMessage("Connected to MQTT broker")
        else:
            self.statusBar().showMessage("Failed to connect to MQTT broker")
            
    def disconnect_from_mqtt(self):
        """Disconnect from the MQTT broker"""
        self.mqtt_client.disconnect()
        self.mqtt_connected = False
        self.connect_button.setText("Connect to Simulation")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Disconnected from MQTT broker")
        
    def toggle_mqtt_connection(self):
        """Toggle MQTT connection state"""
        if self.mqtt_connected:
            self.disconnect_from_mqtt()
        else:
            self.connect_to_mqtt()
            
    def start_simulation(self):
        """Start the simulation by sending a command to the backend"""
        self.mqtt_client.publish("command", {"type": "SIMULATION_START"})
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.simulation_active = True
        self.statusBar().showMessage("Simulation started")
        
    def stop_simulation(self):
        """Stop the simulation by sending a command to the backend"""
        self.mqtt_client.publish("command", {"type": "SIMULATION_STOP"})
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.simulation_active = False
        self.statusBar().showMessage("Simulation stopped")
        
    def toggle_demo_mode(self):
        """Toggle the demo mode (local simulation without backend)"""
        if self.simulation_timer.isActive():
            self.simulation_timer.stop()
            self.demo_button.setText("Demo Mode")
            self.statusBar().showMessage("Demo mode deactivated")
        else:
            self.simulation_timer.start(1000)  # Update every second
            self.demo_button.setText("Stop Demo")
            self.statusBar().showMessage("Demo mode activated - simulating locally")
            
    def update_simulation(self):
        """Update the simulation in demo mode (random changes)"""
        # Update generators with small random changes
        for name, node in self.network_view.nodes.items():
            if node.node_type == "generator":
                power = node.power + random.uniform(-5, 5)
                power = max(0, min(100, power))  # Clamp between 0 and 100
                self.network_view.update_node(name, power=power)
            elif node.node_type == "load":
                power = node.power - random.uniform(-2, 2)
                power = min(0, max(-50, power))  # Clamp between -50 and 0
                self.network_view.update_node(name, power=power)
            elif node.node_type == "storage":
                power = node.power + random.uniform(-3, 3)
                power = max(-30, min(30, power))  # Clamp between -30 and 30
                self.network_view.update_node(name, power=power)
                
        # Update line power flows based on nodes
        for name, line in self.network_view.lines.items():
            power_flow = line.power_flow + random.uniform(-2, 2)
            power_flow = max(-line.capacity, min(line.capacity, power_flow))
            self.network_view.update_line(name, power_flow=power_flow)
            
        # Update statistics
        self.update_statistics()
        
    def update_generator(self, name, value):
        """Update a generator's output"""
        if name in self.network_view.nodes:
            self.network_view.update_node(name, power=float(value))
            
            # Publish change to MQTT if connected
            if self.mqtt_connected:
                self.mqtt_client.publish("generator", {"name": name, "power": value})
                
            # Update lines connected to this generator
            self.update_connected_lines(name)
            
            # Update statistics
            self.update_statistics()
            
    def update_load(self, name, value):
        """Update a load's demand"""
        if name in self.network_view.nodes:
            self.network_view.update_node(name, power=-float(value))  # Loads have negative power
            
            # Publish change to MQTT if connected
            if self.mqtt_connected:
                self.mqtt_client.publish("load", {"name": name, "power": -value})
                
            # Update lines connected to this load
            self.update_connected_lines(name)
            
            # Update statistics
            self.update_statistics()
            
    def update_connected_lines(self, node_name):
        """Update the power flow in lines connected to a node"""
        for line_name, line in self.network_view.lines.items():
            # This is a simplified approach - in a real power flow calculation, 
            # you'd use load flow equations to determine actual power flows
            pass
            
    def update_statistics(self):
        """Update the network statistics"""
        total_generation = 0
        total_load = 0
        total_utilization = 0
        line_count = 0
        
        # Calculate totals
        for name, node in self.network_view.nodes.items():
            if node.power > 0:
                total_generation += node.power
            else:
                total_load += abs(node.power)
                
        for name, line in self.network_view.lines.items():
            if line.capacity > 0:
                utilization = abs(line.power_flow) / line.capacity * 100
                total_utilization += utilization
                line_count += 1
                
        # Update labels
        self.total_generation_label.setText(f"Total Generation: {total_generation:.2f} MW")
        self.total_load_label.setText(f"Total Load: {total_load:.2f} MW")
        
        if line_count > 0:
            avg_utilization = total_utilization / line_count
            self.line_utilization_label.setText(f"Avg. Line Utilization: {avg_utilization:.1f}%")
            
    def handle_node_clicked(self, node_name):
        """Handle when a node is clicked in the network view"""
        self.statusBar().showMessage(f"Selected node: {node_name}")
        
    def handle_mqtt_message(self, topic, message):
        """Process incoming MQTT messages"""
        try:
            print(f"Received message on topic {topic}: {message}")
            
            # Process different types of messages based on topic and content
            if "Outgoing" in topic:
                if isinstance(message, dict):
                    if "network_state" in message:
                        self.update_network_from_message(message["network_state"])
                    elif "current_snapshot" in message:
                        self.statusBar().showMessage(f"Current snapshot: {message['current_snapshot']}")
                        
        except Exception as e:
            print(f"Error handling MQTT message: {e}")
            
    def update_network_from_message(self, network_state):
        """Update the network visualization based on received state"""
        # This would parse and apply the network state from the backend
        # The exact format would depend on your backend implementation
        pass
        
    def closeEvent(self, event):
        """Handle the window close event"""
        if self.mqtt_connected:
            self.mqtt_client.disconnect()
            
        if self.simulation_timer.isActive():
            self.simulation_timer.stop()
            
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartGridVisualizer()
    window.show()
    sys.exit(app.exec()) 