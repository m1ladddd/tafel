# main_controller.py
"""
Main application controller for the Smart Grid Table.
Orchestrates initialization, main loop, and shutdown.
"""

import time
import sys
import socket
import subprocess
import threading
from threading import Thread
from typing import Optional

# Import new root-level modules
from app_state import AppState
from config_loader import ConfigLoader
from input_handling.command_dispatcher import CommandDispatcher

# Import modules from the src map
from src.SmartGridTable import SmartGridTable
from src.networking.UDPBroadcaster import UDPBroadcaster
from src.GUI_MQTT import GUI_MQTT
from src.Prototype_MQTT import Prototype_MQTT
from src.Jupyter_Prototype_Mqtt import Jupyter_MQTT


class MainApplicationController:
    """Main controller that orchestrates the Smart Grid Table application."""
    
    def __init__(self):
        # Initialize application state
        self.app_state = AppState()
        self.app_state.simulation_mode = "--simulation" in sys.argv
        self._determine_local_broker_ip()
        
        # Load configurations
        self.config_loader = ConfigLoader("config.json")
        
        # Initialize main components
        self.table = SmartGridTable("config.json")
        
        # Initialize MQTT clients directly
        self.gui_mqtt = GUI_MQTT()
        self.proto_mqtt = Prototype_MQTT()
        self.jupyter_mqtt = Jupyter_MQTT()
        
        # Initialize command dispatcher with all dependencies
        self.command_dispatcher = CommandDispatcher(
            self.app_state, 
            self.table, 
            self.config_loader,
            self  # Pass self instead of mqtt_manager
        )
        
        # Initialize UDP broadcaster if local setup
        self.udp_broadcaster = None
        if self.table.get_local_setup():
            self.udp_broadcaster = UDPBroadcaster()
            
        # Thread management
        self.console_thread = None
        
    def _determine_local_broker_ip(self):
        """Determine the local IP address for MQTT broker."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            self.app_state.local_broker_ip = s.getsockname()[0]
        except OSError:
            self.app_state.local_broker_ip = "127.0.0.1"
        finally:
            s.close()
        print(f"Local broker IP set to: {self.app_state.local_broker_ip}")
        
    def _initialize_system(self):
        """Initialize all system components."""
        print("────────────────────────────────────────────────────────────────")
        print("─────────────── Loading SmartGridTable scenarios ───────────────")
        print("────────────────────────────────────────────────────────────────")
        
        if not self.table.table_succes():
            print("Error while starting program, aborting...")
            sys.exit(1)
            
        # Handle simulation mode
        if self.app_state.simulation_mode:
            print("────────────────────────────────────────────────────────────────")
            print("─────────── Running in simulation mode without table ───────────")
            print("────────────────────────────────────────────────────────────────")
            
            try:
                from mock_sections import simulate_table_connection, simulate_rfid_modules
                simulate_table_connection()
                simulate_rfid_modules()
            except ImportError:
                print("Warning: mock_sections.py not found, simulation may not work correctly")
                
        # Setup UDP broadcaster if local
        if self.table.get_local_setup() and self.udp_broadcaster:
            protocol_version = "0000"
            opcode = "0000"
            message = protocol_version + opcode + str(self.app_state.local_broker_ip)
            
            # Add NULL terminator
            stringLength = len(message)
            message = message[:stringLength] + '\0' + message[stringLength + 1:]
            
            self.udp_broadcaster.set_interval(0.1)
            self.udp_broadcaster.set_port(5005)
            self.udp_broadcaster.set_message(message.encode('UTF-8'))
            self.udp_broadcaster.start_broadcasting()
            
        print("────────────────────────────────────────────────────────────────")
        print("──────────────────── Starting MQTT clients ─────────────────────")
        print("────────────────────────────────────────────────────────────────")
        
        # Connect MQTT clients
        try:
            broker_ip = self.app_state.local_broker_ip if not self.app_state.simulation_mode else "localhost"
            
            # Set broker for each client
            self.gui_mqtt.mqtt_set_broker(broker_ip)
            self.proto_mqtt.mqtt_set_broker(broker_ip)
            self.jupyter_mqtt.mqtt_set_broker(broker_ip)
            
            # Connect each client
            self.gui_mqtt.mqtt_connect()
            self.proto_mqtt.mqtt_connect()
            self.jupyter_mqtt.mqtt_connect()
            
            print("MQTT clients connected successfully")
        except Exception as e:
            print(f"WARNING: MQTT connection failed: {e}")
            print("Continuing without MQTT connectivity")
        
        # Try to connect table MQTT (sections)
        try:
            self.table.mqtt_connect()
        except ConnectionRefusedError:
            print("WARNING: Table MQTT connection failed. Continuing without table MQTT.")
        except Exception as e:
            print(f"WARNING: Table MQTT error: {e}")
            print("Continuing without table MQTT connectivity.")
        
        time.sleep(1)  # Give clients time to connect
        
        print("────────────────────────────────────────────────────────────────")
        print("──────────── Connecting to SmartGridTable sections ─────────────")
        print("────────────────────────────────────────────────────────────────")
        
        self.table.table_ping_all()
        self.table.modules_enable_messages(False)
        
        # Wait for tables to come online (skip in simulation mode)
        if not self.app_state.simulation_mode:
            timer = 0
            timer_limit = 3.0
            timeout_limit = 6.0
            timeout = False
            
            while not self.table.table_is_online() and not timeout:
                time.sleep(self.app_state.refresh_rate)
                timer += self.app_state.refresh_rate
                if timer >= timer_limit and timer < timeout_limit:
                    time_left = timeout_limit - timer
                    print(f"Timeout in [{time_left:.1f}] seconds...")
                    timer_limit += 1.0
                if timer >= timeout_limit:
                    print("Timeout when trying to connect...")
                    timeout = True
                    
            if self.table.table_is_online():
                print("Physical table is online - starting normal operation...")
        else:
            print("Simulation mode: Tables connected automatically")
            
        print("────────────────────────────────────────────────────────────────")
        print("────────────── Retrieving SmartGridTable Modules ───────────────")
        print("────────────────────────────────────────────────────────────────")
        
        if self.table.get_local_setup() and self.udp_broadcaster:
            self.udp_broadcaster.set_interval(1)
            
        self.table.table_retrieve_modules()
        
        # Wait for RFID readers (skip in simulation mode)
        if not self.app_state.simulation_mode:
            timer = 0
            timeout_limit = 3.0
            timeout = False
            
            while not self.table.table_is_rfid_online() and not timeout:
                time.sleep(self.app_state.refresh_rate)
                timer += self.app_state.refresh_rate
                if timer >= timeout_limit:
                    print("Timeout waiting for RFID readers.")
                    timeout = True
        else:
            print("Simulation mode: RFID readers connected automatically")
            
        self.table.modules_print_status()
        self.table.modules_enable_messages(True)
        
        print("────────────────────────────────────────────────────────────────")
        print("───────────── SmartGridTable (Pandapower) up and running! ──────")
        print("────────────────────────────────────────────────────────────────")
        
    def _console_input_loop(self):
        """Background thread for console input."""
        while self.app_state.is_running:
            try:
                console_text = input()
                if self.app_state.is_running:
                    self.app_state.console_input_buffer = console_text
                    if console_text == "shutdown":
                        self.app_state.request_shutdown()
                        break
            except EOFError:
                if self.app_state.is_running:
                    print("EOFError encountered in console input. Shutting down.")
                    self.app_state.request_shutdown()
                break
            except Exception as e:
                if self.app_state.is_running:
                    print(f"Error in console input loop: {e}")
                break
                
    def run(self):
        """Main application execution loop."""
        # Initialize system
        self._initialize_system()
        
        # Start console input thread
        self.console_thread = Thread(target=self._console_input_loop, daemon=True)
        self.console_thread.start()
        
        print("Entering main loop...")
        timer = 0
        
        try:
            while self.app_state.is_running:
                time.sleep(self.app_state.refresh_rate)
                
                # 1. Process MQTT messages
                gui_messages = self.gui_mqtt.message_buffer[:]
                self.gui_mqtt.message_buffer.clear()
                for msg in gui_messages:
                    self.command_dispatcher.dispatch_ui_message(msg)
                    
                jupyter_messages = self.jupyter_mqtt.message_buffer[:]
                self.jupyter_mqtt.message_buffer.clear()
                for msg_str in jupyter_messages:
                    self.command_dispatcher.dispatch_jupyter_command(msg_str)
                    
                proto_messages = self.proto_mqtt.message_buffer[:]
                self.proto_mqtt.message_buffer.clear()
                for msg_dict in proto_messages:
                    self.command_dispatcher.dispatch_proto_message(msg_dict)
                    
                # 2. Process console input
                if self.app_state.console_input_buffer:
                    cmd_input = self.app_state.console_input_buffer
                    self.app_state.console_input_buffer = ""
                    self.command_dispatcher.dispatch_console_command(cmd_input)
                    
                # 3. Dynamic scenario & table update
                self.table.append_delta_time(self.app_state.refresh_rate)
                self.table.update()
                
                timer += self.app_state.refresh_rate
                
                # 4. Calculation trigger
                recalculate = False
                calc_reason = ""
                
                if self.app_state.consume_force_update():
                    recalculate = True
                    calc_reason = "Forced update requested"
                elif self.table.modules_if_changed():
                    recalculate = True
                    calc_reason = "Module change detected"
                    
                if recalculate:
                    print(f"Recalculating simulation ({calc_reason}) using Pandapower...")
                    
                    if calc_reason == "Module change detected":
                        self.table.selective_calculate()
                    else:
                        self.table.force_calculate()
                        
                    if self.table.get_simulation_succes():
                        print("Calculation complete.")
                        # Send updates after calculation
                        self.command_dispatcher.dispatch_ui_message({
                            'type': 'SEND_SNAPSHOTS', 
                            'payload': {}
                        })
                    else:
                        print("Calculation failed. Check logs.")
                    print("────────────────────────────────────────────────────────────────")
                    
                # 5. LED updates
                if self.table.get_lep_update_flag():
                    self.table.reset_led_update_flag()
                    current_snapshot_index = 0  # TODO: Get correct index
                    self.table.update_ledstrips(current_snapshot_index)
                    self.table.mqtt_selective_publish()
                    
        except KeyboardInterrupt:
            print("\nCtrl+C detected. Shutting down...")
        finally:
            self.app_state.request_shutdown()
            self._shutdown_system()
            
    def _shutdown_system(self):
        """Perform system shutdown."""
        print("Exited main loop. Starting shutdown sequence...")
        
        if self.table.get_local_setup() and self.udp_broadcaster:
            print("Stopping UDP broadcaster...")
            self.udp_broadcaster.stop_broadcasting()
            
        print("Disconnecting MQTT clients...")
        self.table.mqtt_disconnect()
        self.gui_mqtt.mqtt_disconnect()
        self.proto_mqtt.mqtt_disconnect()
        self.jupyter_mqtt.mqtt_disconnect()
        
        print("Shutting down table simulation...")
        self.table.shutdown()
        
        print("Waiting for console thread to finish...")
        if self.console_thread and self.console_thread.is_alive():
            self.console_thread.join(timeout=1.0)
            
        print("────────────────────────────────────────────────────────────────")
        print("───────────────── Goodbye, until next time! ────────────────────")
        print("────────────────────────────────────────────────────────────────")
        
    def publish_to_gui(self, message: str):
        """
        Publish a message to the GUI MQTT client.
        @param message (str) JSON string message to publish
        """
        if self.gui_mqtt:
            self.gui_mqtt.mqtt_publish(message)
            
    def publish_to_jupyter(self, message: str):
        """
        Publish a message to the Jupyter MQTT client.
        @param message (str) JSON string message to publish
        """
        if self.jupyter_mqtt:
            self.jupyter_mqtt.mqtt_publish(message) 