"""
MQTT Manager for centralizing MQTT client management.
This module handles all MQTT connections and provides a unified interface.
"""

import json
import time
from typing import Dict, List, Any, Optional
from threading import Lock


class MQTTManager:
    """Centralized MQTT client management."""
    
    def __init__(self, app_state, config_loader):
        self.app_state = app_state
        self.config_loader = config_loader
        self.connections_active = False
        self.connection_lock = Lock()
        
        # MQTT clients (to be injected)
        self.gui_mqtt = None
        self.proto_mqtt = None
        self.jupyter_mqtt = None
        self.table_mqtt = None
        
        # Message buffers
        self._message_buffers = {
            'gui': [],
            'proto': [],
            'jupyter': []
        }
        
    def set_clients(self, gui_mqtt=None, proto_mqtt=None, jupyter_mqtt=None, table_mqtt=None):
        """Set MQTT client instances."""
        if gui_mqtt:
            self.gui_mqtt = gui_mqtt
        if proto_mqtt:
            self.proto_mqtt = proto_mqtt
        if jupyter_mqtt:
            self.jupyter_mqtt = jupyter_mqtt
        if table_mqtt:
            self.table_mqtt = table_mqtt
    
    def connect_all(self) -> bool:
        """Connect all MQTT clients."""
        with self.connection_lock:
            try:
                broker_ip = self._determine_broker_ip()
                success_count = 0
                total_clients = 0
                
                # Connect GUI MQTT
                if self.gui_mqtt:
                    total_clients += 1
                    if self._connect_client(self.gui_mqtt, "GUI", broker_ip):
                        success_count += 1
                
                # Connect Prototype MQTT
                if self.proto_mqtt:
                    total_clients += 1
                    if self._connect_client(self.proto_mqtt, "Prototype", broker_ip):
                        success_count += 1
                
                # Connect Jupyter MQTT
                if self.jupyter_mqtt:
                    total_clients += 1
                    if self._connect_client(self.jupyter_mqtt, "Jupyter", broker_ip):
                        success_count += 1
                
                # Connect Table MQTT (if available)
                if self.table_mqtt:
                    total_clients += 1
                    if self._connect_client(self.table_mqtt, "Table", broker_ip):
                        success_count += 1
                
                self.connections_active = success_count > 0
                print(f"MQTT Manager: {success_count}/{total_clients} clients connected")
                return self.connections_active
                
            except Exception as e:
                print(f"MQTT Manager Error: Failed to connect clients: {e}")
                self.connections_active = False
                return False
    
    def disconnect_all(self):
        """Disconnect all MQTT clients."""
        with self.connection_lock:
            try:
                clients = [
                    (self.gui_mqtt, "GUI"),
                    (self.proto_mqtt, "Prototype"), 
                    (self.jupyter_mqtt, "Jupyter"),
                    (self.table_mqtt, "Table")
                ]
                
                for client, name in clients:
                    if client:
                        self._disconnect_client(client, name)
                
                self.connections_active = False
                print("MQTT Manager: All clients disconnected")
                
            except Exception as e:
                print(f"MQTT Manager Error: Failed to disconnect clients: {e}")
    
    def _determine_broker_ip(self) -> str:
        """Determine the broker IP address."""
        # Try to get from config first
        if self.config_loader:
            broker_ip = self.config_loader.get_config_value("mqtt_broker_ip")
            if broker_ip:
                return broker_ip
        
        # Fall back to app state
        if self.app_state and self.app_state.local_broker_ip:
            return self.app_state.local_broker_ip
            
        # Default fallback
        return "localhost"
    
    def _connect_client(self, client, client_name: str, broker_ip: str) -> bool:
        """Connect a single MQTT client."""
        try:
            client.mqtt_set_broker(broker_ip)
            client.mqtt_connect()
            
            # Give client time to connect
            time.sleep(0.1)
            
            print(f"MQTT Manager: {client_name} client connected to {broker_ip}")
            return True
            
        except Exception as e:
            print(f"MQTT Manager Warning: Failed to connect {client_name} client: {e}")
            return False
    
    def _disconnect_client(self, client, client_name: str):
        """Disconnect a single MQTT client."""
        try:
            if hasattr(client, 'mqtt_disconnect'):
                client.mqtt_disconnect()
            print(f"MQTT Manager: {client_name} client disconnected")
        except Exception as e:
            print(f"MQTT Manager Warning: Failed to disconnect {client_name} client: {e}")
    
    def get_gui_messages(self) -> List[Dict]:
        """Get and clear GUI MQTT messages."""
        if self.gui_mqtt and hasattr(self.gui_mqtt, 'message_buffer'):
            messages = self.gui_mqtt.message_buffer.copy()
            self.gui_mqtt.message_buffer.clear()
            return messages
        return []
    
    def get_proto_messages(self) -> List[Dict]:
        """Get and clear Prototype MQTT messages."""
        if self.proto_mqtt and hasattr(self.proto_mqtt, 'message_buffer'):
            messages = self.proto_mqtt.message_buffer.copy()
            self.proto_mqtt.message_buffer.clear()
            return messages
        return []
    
    def get_jupyter_messages(self) -> List[str]:
        """Get and clear Jupyter MQTT messages."""
        if self.jupyter_mqtt and hasattr(self.jupyter_mqtt, 'message_buffer'):
            messages = self.jupyter_mqtt.message_buffer.copy()
            self.jupyter_mqtt.message_buffer.clear()
            return messages
        return []
    
    def publish_to_gui(self, message: str) -> bool:
        """Publish message to GUI MQTT topic."""
        if self.gui_mqtt and self.connections_active:
            try:
                self.gui_mqtt.mqtt_publish(message)
                return True
            except Exception as e:
                print(f"MQTT Manager: Failed to publish to GUI: {e}")
        return False
    
    def publish_to_jupyter(self, message: str) -> bool:
        """Publish message to Jupyter MQTT topic."""
        if self.jupyter_mqtt and self.connections_active:
            try:
                self.jupyter_mqtt.mqtt_publish(message)
                return True
            except Exception as e:
                print(f"MQTT Manager: Failed to publish to Jupyter: {e}")
        return False
    
    def are_connections_active(self) -> bool:
        """Check if any MQTT connections are active."""
        return self.connections_active
    
    def get_connection_status(self) -> Dict[str, bool]:
        """Get the connection status of all clients."""
        status = {}
        
        clients = [
            (self.gui_mqtt, "gui"),
            (self.proto_mqtt, "proto"),
            (self.jupyter_mqtt, "jupyter"),
            (self.table_mqtt, "table")
        ]
        
        for client, name in clients:
            if client:
                # Check if client has a connection status method
                if hasattr(client, 'mqtt_is_connected'):
                    status[name] = client.mqtt_is_connected()
                else:
                    # Assume connected if we have the client
                    status[name] = self.connections_active
            else:
                status[name] = False
                
        return status
    
    def reconnect_failed_clients(self):
        """Attempt to reconnect any failed clients."""
        if not self.connections_active:
            print("MQTT Manager: Attempting to reconnect failed clients...")
            self.connect_all() 