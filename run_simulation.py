# Create this file as run_simulation.py in the same directory as Application.py
# This script will start the simulation without requiring the physical table

import os
import json
import sys

def modify_config():
    """
    Modify the configuration to run in standalone mode with simulated tables
    """
    config_path = "config.json"
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as file:
                config = json.load(file)
                
                # Set to standalone mode
                config["mqtt_config"] = "local"
                
                # Add simulation mode if needed
                config["simulation_mode"] = True
                
                # Disable waiting for physical table connection
                config["wait_for_connection"] = False
            
            # Write modified config back
            with open(config_path, "w") as file:
                json.dump(config, file, indent=4)
                print("Modified configuration for simulation mode")
                
        except Exception as e:
            print(f"Error modifying config: {e}")
    else:
        print(f"Config file not found at {config_path}")

def patch_smartgridtable_class():
    """
    This function patches the SmartGridTable class to support simulation mode
    It will be applied before importing the main application
    """
    # This is a simplified example - you would need to modify this based on your actual class
    # You may need to create a more complex monkey patch depending on your implementation
    
    import types
    from src.SmartGridTable import SmartGridTable
    
    original_init = SmartGridTable.__init__
    original_mqtt_connect = SmartGridTable.mqtt_connect
    original_table_is_online = SmartGridTable.table_is_online
    original_table_is_rfid_online = SmartGridTable.table_is_rfid_online
    
    def patched_init(self, config_file):
        original_init(self, config_file)
        if hasattr(self, 'config') and self.config.get('simulation_mode', False):
            print("Initializing SmartGridTable in simulation mode")
            # Import mock sections
            from mock_sections import create_mock_sections
            self.mock_sections = create_mock_sections()
            self.simulation_mode = True
    
    def patched_mqtt_connect(self):
        result = original_mqtt_connect(self)
        if hasattr(self, 'simulation_mode') and self.simulation_mode:
            # In simulation mode, we'll pretend all connections worked
            return True
        return result
    
    def patched_table_is_online(self):
        if hasattr(self, 'simulation_mode') and self.simulation_mode:
            # In simulation mode, we'll pretend the table is always online
            return True
        return original_table_is_online(self)
    
    def patched_table_is_rfid_online(self):
        if hasattr(self, 'simulation_mode') and self.simulation_mode:
            # In simulation mode, we'll pretend the RFID readers are always online
            return True
        return original_table_is_rfid_online(self)
    
    # Apply the patches
    SmartGridTable.__init__ = patched_init
    SmartGridTable.mqtt_connect = patched_mqtt_connect
    SmartGridTable.table_is_online = patched_table_is_online
    SmartGridTable.table_is_rfid_online = patched_table_is_rfid_online
    
    print("SmartGridTable class patched for simulation mode")

if __name__ == "__main__":
    # 1. First modify the config
    modify_config()
    
    # 2. Patch the SmartGridTable class to support simulation
    try:
        patch_smartgridtable_class()
    except Exception as e:
        print(f"Warning: Could not patch SmartGridTable class: {e}")
    
    # 3. Add simulation flag to command line arguments
    sys.argv.append("--simulation")
    
    # 4. Import and run the application
    try:
        import Application
        print("Application started successfully in simulation mode")
    except Exception as e:
        print(f"Error starting application: {e}")