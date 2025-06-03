"""
Central dispatcher for all commands and messages.
Handles console commands, GUI MQTT messages, prototype messages, and Jupyter commands.
"""

import json
from typing import Dict, List, Any, Optional, Callable


class CommandDispatcher:
    """Dispatches commands from various sources to appropriate handlers."""
    
    def __init__(self, app_state, smart_grid_table, config_loader, mqtt_manager=None):
        self.app_state = app_state
        self.table = smart_grid_table
        self.config_loader = config_loader
        self.mqtt_manager = mqtt_manager
        
        # Command registries
        self._console_commands: Dict[str, Callable] = {}
        self._ui_message_handlers: Dict[str, Callable] = {}
        self._proto_message_handlers: Dict[str, Callable] = {}
        self._jupyter_commands: Dict[str, Callable] = {}
        
        self._register_handlers()
        
    def _register_handlers(self):
        """Register all command and message handlers."""
        # Console commands
        self._console_commands.update({
            "help": self._handle_help,
            "shutdown": self._handle_shutdown,
            "calculate": self._handle_calculate,
            "debug": self._handle_debug,
            "transformer_capacity": self._handle_transformer_capacity,
            "summation": self._handle_summation,
            "run": self._handle_run,
            "stop": self._handle_stop,
            "index": self._handle_index,
            "photo": self._handle_photo,
            "tablesection": self._handle_tablesection,
            "voltage": self._handle_voltage,
            "module generation": self._handle_module_generation,
            "module load": self._handle_module_load,
            "module storage": self._handle_module_storage,
            "modules list": self._handle_modules_list,
            "table list": self._handle_table_list,
            "table update firmware": self._handle_table_update_firmware,
            "table update config": self._handle_table_update_config,
            "table reboot all": self._handle_table_reboot_all,
            "table reboot": self._handle_table_reboot,
            "table shutdown": self._handle_table_shutdown,
            "table poweron": self._handle_table_poweron,
            "scenario reload": self._handle_scenario_reload,
            "scenario list": self._handle_scenario_list,
            "scenario current": self._handle_scenario_current,
            "scenario set": self._handle_scenario_set,
            "mode set": self._handle_mode_set,
            "simulate": self._handle_simulate,
        })
        
        # UI MQTT message handlers
        self._ui_message_handlers.update({
            'SEND_SCENARIO_JSON': self._ui_send_scenario_json,
            'SEND_RESTRICTIONS': self._ui_send_restrictions,
            'CHANGE_MODULE_PARAMETER': self._ui_change_module_parameter,
            'SEND_ACTIVE_MODULES': self._ui_send_active_modules,
            'SEND_SCENARIO_LIST': self._ui_send_scenario_list,
            'CHANGE_SCENARIO': self._ui_change_scenario,
            'CHANGE_RESTRICTIONS': self._ui_change_restrictions,
            'SEND_SNAPSHOTS': self._ui_send_snapshots,
            'SEND_LINE_STATUSES': self._ui_send_line_statuses,
            'CHANGE_LINE': self._ui_change_line,
            'PLACE_MODULE': self._ui_place_module,
            'REMOVE_MODULE': self._ui_remove_module,
            'LOAD_SCENARIO': self._ui_load_scenario,
        })
        
    # ============== Console Command Dispatch ==============
    
    def dispatch_console_command(self, command_str: str):
        """Dispatch a console command string to the appropriate handler."""
        parts = command_str.split()
        if not parts:
            return
            
        # Try to match command patterns (up to 3 parts for complex commands)
        for i in range(min(3, len(parts)), 0, -1):
            command_key = " ".join(parts[:i]).lower()
            if command_key in self._console_commands:
                handler = self._console_commands[command_key]
                args = parts[i:]
                try:
                    handler(*args)
                except TypeError as e:
                    print(f"Error: Invalid number of arguments for command '{command_key}'")
                except Exception as e:
                    print(f"Error executing command '{command_key}': {e}")
                return
                
        print(f"Unknown command: {command_str}. Type 'help' for available commands.")
        
    # ============== Console Command Handlers ==============
    
    def _handle_help(self):
        """Print all available commands."""
        print("────────────────────────────────────────────────────────────────")
        print("help                     ─> Print all commands")
        print("shutdown                 ─> Close the program")
        print("table list               ─> Print the names of all table sections")
        print("table reboot all         ─> Reboot all table sections")
        print("table reboot [SECTION]   ─> Reboot given table section")
        print("table shutdown [SECTION] ─> Shutdown the given table section")
        print("table poweron [SECTION]  ─> Boot up the given table section")
        print("table update firmware    ─> Update the Smart Grid Table to the latest version")
        print("table update config      ─> Update the Smart Grid Table with the latest configuration")
        print("scenario reload          ─> Find and reload all scenarios in Static/")
        print("scenario list            ─> Print the names of all available scenarios")
        print("scenario current         ─> Print the current active scenario")
        print("scenario set -s [NAME]   ─> Switch to given static scenario")
        print("scenario set -d [NAME]   ─> Switch to given dynamic scenario")
        print("mode set optimize        ─> Set calculation type to Optimized")
        print("mode set lopf            ─> Set calculation type to Linear Optimal Power Flow (LOPF)")
        print("mode set lpf             ─> Set calculation type to Linear Power Flow (LPF)")
        print("mode set pf              ─> Set calculation type to Power Flow (PF)")
        print("modules list             ─> Print the number of modules placed on each table section")
        print("calculate                ─> Recalculate the current power grid model")
        print("index [NUM]              -> Set dynamic scenario index")
        print("stop                     -> Stop automatic dynamic index increment")
        print("run                      -> Start automatic dynamic index increment")
        print("tablesection [NAME]      -> Show generation/load sum for a table section")
        print("voltage [LV|MV|HV]       -> Show generation/load sum for a voltage level")
        print("module generation [TABLE]-> Show generation per module for a table section")
        print("module load [TABLE]      -> Show load per module for a table section")
        print("module storage [TABLE]   -> Show storage per module for a table section")
        print("transformer_capacity     -> Show transformer power and capacity")
        print("summation                -> Show total generation/load/storage for the grid")
        print("photo [dir] [module_id]  -> Change PV panel direction (South, East, West, None)")
        print("simulate                 -> Simulate module placement or removal")
        print("────────────────────────────────────────────────────────────────")
        
    def _handle_shutdown(self):
        """Handle shutdown command."""
        print("Shutting down program...")
        self.app_state.request_shutdown()
        
    def _handle_calculate(self):
        """Force a recalculation."""
        print("Forcing simulation update...")
        self.app_state.request_update()
        
    def _handle_debug(self):
        """Debug Pandapower model and add slack bus if missing."""
        print("🔍 Debugging Pandapower model...")
        
        # Get model and check for slack bus
        model = self.table.get_model()
        if not model:
            print("❌ No model available")
            return
            
        print(f"📊 Model: {len(model.buses)} buses, {len(model.lines)} lines, {len(model.generators)} gens, {len(model.loads)} loads, {len(model.transformers)} transformers")
        
        # Check HV buses for potential slack bus
        hv_buses = [bus for bus in model.buses if "Table1" in bus.name and bus.active]
        print(f"🔌 HV buses found: {[bus.name for bus in hv_buses]}")
        
        # Add slack bus to Table1_bus0 (HV main bus)
        print("⚡ Adding slack bus (external grid) to Table1_bus0...")
        success = self._add_slack_bus_to_model()
        if success:
            print("✅ Slack bus added successfully")
            print("🔄 Recalculating...")
            self.app_state.request_update()
        else:
            print("❌ Failed to add slack bus")
            
    def _add_slack_bus_to_model(self):
        """Add external grid (slack bus) to the model."""
        try:
            # This is a hack - we need to modify the Pandapower model directly
            # In a proper implementation, this would be done via the Model structure
            calculator = self.table._SmartGridTable__model_calculator
            if hasattr(calculator, '_pandapower_model') and calculator._pandapower_model is not None:
                import pandapower as pp
                
                # Find Table1_bus0 index
                bus_df = calculator._pandapower_model.get('bus')
                if bus_df is not None and 'name' in bus_df.columns:
                    table1_buses = bus_df[bus_df['name'].str.contains('Table1_bus0', na=False)]
                    if not table1_buses.empty:
                        bus_idx = table1_buses.index[0]
                        
                        # Check if ext_grid already exists
                        ext_grid_df = calculator._pandapower_model.get('ext_grid')
                        if ext_grid_df is not None and not ext_grid_df.empty:
                            print("⚠️  External grid already exists")
                            return True
                            
                        # Add external grid (slack bus)
                        pp.create_ext_grid(calculator._pandapower_model, bus=bus_idx, vm_pu=1.0, name="Grid Connection")
                        print(f"✅ Added external grid to bus index {bus_idx}")
                        return True
                    else:
                        print("❌ Table1_bus0 not found")
                        return False
                else:
                    print("❌ Bus dataframe not available")
                    return False
            else:
                print("❌ Pandapower model not accessible")
                return False
        except Exception as e:
            print(f"❌ Error adding slack bus: {e}")
            return False
        
    def _handle_transformer_capacity(self):
        """Show transformer capacity information."""
        transformer_df, capacity_df = self.table.transformer_capacity()
        print(transformer_df)
        print(capacity_df)
        
    def _handle_summation(self):
        """Show grid summation data."""
        print(self.table.get_full_grid_sum_generation_loads_storage())
        
    def _handle_run(self):
        """Start automatic index increment."""
        print("Starting automatic index increment.")
        self.table.start_running()
        
    def _handle_stop(self):
        """Stop automatic index increment."""
        print("Stopping automatic index increment.")
        self.table.stop_running()
        
    def _handle_index(self, *args):
        """Set dynamic scenario index."""
        if len(args) >= 1:
            try:
                index_val = int(args[0])
                self.table.set_index(index_val)
            except ValueError:
                print("Error: Index must be an integer.")
        else:
            print("Usage: index [NUMBER]")
            
    def _handle_photo(self, *args):
        """Change photovoltaic panel direction."""
        if len(args) >= 2:
            direction = args[0]
            module_id = args[1]
            self.table.change_photovoltaic(direction, module_id)
            self.app_state.request_update()
        else:
            print("Usage: photo [South|East|West|None] [MODULE_ID]")
            
    def _handle_tablesection(self, *args):
        """Show table section generation/load sum."""
        if len(args) >= 1:
            print(self.table.get_table_sum(args[0]))
        else:
            print("Usage: tablesection [TABLE_NAME]")
            
    def _handle_voltage(self, *args):
        """Show voltage level generation/load sum."""
        if len(args) >= 1:
            print(self.table.get_voltage_sum(args[0]))
        else:
            print("Usage: voltage [LV|MV|HV]")
            
    def _handle_module_generation(self, *args):
        """Show module generation for a table."""
        if len(args) >= 1:
            print(self.table.get_table_section_module_generation(args[0]))
        else:
            print("Usage: module generation [TABLE_NAME]")
            
    def _handle_module_load(self, *args):
        """Show module load for a table."""
        if len(args) >= 1:
            print(self.table.get_table_section_module_load(args[0]))
        else:
            print("Usage: module load [TABLE_NAME]")
            
    def _handle_module_storage(self, *args):
        """Show module storage for a table."""
        if len(args) >= 1:
            print(self.table.get_table_section_module_storage(args[0]))
        else:
            print("Usage: module storage [TABLE_NAME]")
            
    def _handle_modules_list(self):
        """List all modules."""
        self.table.modules_print_status()
        print("────────────────────────────────────────────────────────────────")
        
    def _handle_table_list(self):
        """List all table sections."""
        self.table.table_print_list()
        
    def _handle_table_update_firmware(self):
        """Update firmware on all tables."""
        print("Updating all table tiles to the latest firmware")
        self.table.table_update_firmware_all()
        
    def _handle_table_update_config(self):
        """Update config on all tables."""
        print("Updating all table tiles to the latest config settings")
        self.table.table_update_config_all()
        
    def _handle_table_reboot_all(self):
        """Reboot all table sections."""
        print("Restarting all table sections...")
        self.table.table_reboot_all()
        
    def _handle_table_reboot(self, *args):
        """Reboot specific table section."""
        if len(args) >= 1:
            target = args[0]
            print(f"Restarting section -> {target}")
            self.table.table_reboot(target)
        else:
            print("Usage: table reboot [SECTION_NAME]")
            
    def _handle_table_shutdown(self, *args):
        """Shutdown specific table section."""
        if len(args) >= 1:
            target = args[0]
            print(f"Shutting down section -> {target}")
            self.table.table_shutdown(target)
        else:
            print("Usage: table shutdown [SECTION_NAME]")
            
    def _handle_table_poweron(self, *args):
        """Power on specific table section."""
        if len(args) >= 1:
            target = args[0]
            print(f"Activating section -> {target}")
            self.table.table_poweron(target)
        else:
            print("Usage: table poweron [SECTION_NAME]")
            
    def _handle_scenario_reload(self):
        """Reload scenarios."""
        print("Reloading scenarios...")
        self.table.scenario_refresh_list()
        
    def _handle_scenario_list(self):
        """List available scenarios."""
        self.table.scenario_print_list()
        
    def _handle_scenario_current(self):
        """Show current scenario."""
        self.table.scenario_print_current()
        
    def _handle_scenario_set(self, *args):
        """Set a scenario."""
        if len(args) >= 2:
            flag = args[0].lower()
            scenario_name = args[1]
            if flag == "-s":
                self.table.scenario_set(scenario_name, static=True)
                self.app_state.request_update()
            elif flag == "-d":
                self.table.scenario_set(scenario_name, static=False)
                self.app_state.request_update()
            else:
                print("Usage: scenario set [-s|-d] [SCENARIO_NAME]")
        else:
            print("Usage: scenario set [-s|-d] [SCENARIO_NAME]")
            
    def _handle_mode_set(self, *args):
        """Set calculation mode."""
        if len(args) >= 1:
            new_mode = args[0].lower()
            if self.app_state.set_mode(new_mode):
                self.table.set_calculation_method(new_mode)
                print(f"Setting mode to {new_mode.upper()} (using Pandapower backend)")
            else:
                print(f"Invalid mode '{new_mode}'. Valid modes: optimize, lopf, lpf, pf")
        else:
            print("Usage: mode set [optimize|lopf|lpf|pf]")
            
    def _handle_simulate(self, *args):
        """Handle simulate command with subcommands."""
        if not self.app_state.simulation_mode:
            print("Simulate commands only work in simulation mode")
            return
            
        if len(args) < 1:
            print("Usage: simulate <quick|place|remove|simple>")
            return
            
        subcommand = args[0].lower()
        
        if subcommand == "quick":
            self._simulate_quick_setup()
        elif subcommand == "simple":
            self._simulate_simple_setup()
        elif subcommand == "place" and len(args) >= 4:
            rfid = args[1]
            table = args[2]
            position = int(args[3])
            self._simulate_module_placement(rfid, table, position)
        elif subcommand == "remove" and len(args) >= 3:
            table = args[1]
            position = int(args[2])
            self._simulate_module_removal(table, position)
        else:
            print("Usage:")
            print("  simulate quick     - Place a balanced set of modules")
            print("  simulate simple    - Place minimal modules for testing")
            print("  simulate place <RFID> <table> <position>")
            print("  simulate remove <table> <position>")
        
    # ============== UI MQTT Message Dispatch ==============
    
    def dispatch_ui_message(self, message_dict: dict):
        """Dispatch a UI MQTT message to the appropriate handler."""
        msg_type = message_dict.get('type')
        payload = message_dict.get('payload', {})
        
        handler = self._ui_message_handlers.get(msg_type)
        if handler:
            try:
                handler(payload)
            except Exception as e:
                print(f"Error processing UI message (type: {msg_type}): {e}")
        else:
            print(f"Unknown UI message type: {msg_type}")
            
    # ============== UI MQTT Message Handlers ==============
    
    def _ui_send_scenario_json(self, payload):
        """Send scenario JSON to GUI."""
        response = {
            'type': 'SCENARIO_JSON',
            'payload': {
                "scenario_json": self.table.get_referenceless_catalog(),
                "is_static": self.table.get_scenario_type()
            }
        }
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
    def _ui_send_restrictions(self, payload):
        """Send restrictions to GUI."""
        rest = self.table.get_current_restrictions()
        response = {
            'type': 'RESTRICTIONS_JSON',
            'payload': rest
        }
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
    def _ui_change_module_parameter(self, payload_dict):
        """Change module parameters."""
        catalog = self.table.get_referenceless_catalog()
        updates = {}
        
        if isinstance(payload_dict, dict):
            for id_key, value in payload_dict.items():
                catalog[id_key] = value
                updates[id_key] = value
        else:
            print("Warning: CHANGE_MODULE_PARAMETER payload was not a dictionary.")
            return
            
        # Send updates to other clients
        response = {
            "type": "SCENARIO_UPDATE",
            "payload": {"scenario_updates": updates}
        }
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
        # Push changes to scenario
        self.table.change_current_scenario_catalog(catalog)
        self.table.modules_reload()
        self.app_state.request_update()
        
    def _ui_send_active_modules(self, payload):
        """Send active modules to GUI."""
        changes = self.table.get_module_changes()
        self.table.empty_module_change_buffer()
        
        active_modules_payload = []
        for change in changes:
            table_section = change["table_section"]
            modules = change["buffer"]
            for module_info in modules:
                if module_info.get("state") == "placed":
                    active_modules_payload.append({
                        "module_id": module_info.get("RFID_tag"),
                        "position": module_info.get("location"),
                        "type": module_info.get("name")
                    })
                    
        response = {"type": "ACTIVE_MODULES", "payload": active_modules_payload}
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
    def _ui_send_scenario_list(self, payload):
        """Send scenario list to GUI."""
        is_static_payload = payload.get('is_static', True)
        scenario_list = self.table.get_scenario_list(isStatic=is_static_payload)
        response = {
            "type": "SCENARIO_LIST",
            "payload": {
                "scenario_list": scenario_list,
                "is_static": is_static_payload
            }
        }
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
    def _ui_change_scenario(self, payload):
        """Change the active scenario."""
        scenario_name = payload.get('scenario_name')
        is_static_payload = payload.get('is_static')
        
        if scenario_name is not None and is_static_payload is not None:
            print(f"UI Request: Changing scenario to '{scenario_name}' (static={is_static_payload})")
            self.table.scenario_set(scenario_name, is_static_payload)
            self.table.set_restrictions(is_static_payload)
            
            # Send back confirmation
            self._ui_send_scenario_json({})
            self._ui_send_restrictions({})
            
            self.app_state.request_update()
        else:
            print("Warning: CHANGE_SCENARIO message missing 'scenario_name' or 'is_static'.")
            
    def _ui_change_restrictions(self, payload):
        """Update user restrictions."""
        if isinstance(payload, list):
            print("UI Request: Changing restrictions.")
            self.table.change_restrictions(changes=payload)
            
            # Notify other clients
            response = {
                "type": "RESTRICTIONS_UPDATE",
                "payload": payload
            }
            if self.mqtt_manager:
                self.mqtt_manager.publish_to_gui(json.dumps(response))
                
            self.app_state.request_update()
        else:
            print("Warning: CHANGE_RESTRICTIONS payload was not a list.")
            
    def _ui_send_snapshots(self, payload):
        """Send network snapshots."""
        print("UI Request: Sending snapshots.")
        response = self.table.get_snapshot_response_gui()
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
    def _ui_send_line_statuses(self, payload):
        """Send line statuses to GUI."""
        print("UI Request: Sending line statuses.")
        response_dict = {
            "type": "LINE_UPDATE",
            "payload": []
        }
        
        line_remaps = self.config_loader.get_gui_line_remaps()
        for section_id, remap_obj in enumerate(line_remaps):
            if hasattr(remap_obj, 'line_state') and isinstance(remap_obj.line_state, list):
                for line_idx, line_active in enumerate(remap_obj.line_state):
                    response_dict["payload"].append({
                        "table": section_id + 1,
                        "line": line_idx,
                        "active": line_active
                    })
                    
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response_dict))
            
    def _ui_change_line(self, payload_dict):
        """Change line status."""
        table_id_req = payload_dict.get("table")
        line_id_req = payload_dict.get("line")
        active_req = payload_dict.get("active")
        
        if table_id_req is None or line_id_req is None or active_req is None:
            print("Warning: CHANGE_LINE message missing required fields.")
            return
            
        table_idx = table_id_req - 1  # Convert to 0-based
        line_remaps = self.config_loader.get_gui_line_remaps()
        
        if not (0 <= table_idx < len(line_remaps)):
            print(f"Warning: Invalid table index {table_idx} in CHANGE_LINE.")
            return
            
        remap_obj = line_remaps[table_idx]
        if not (hasattr(remap_obj, 'line_state') and isinstance(remap_obj.line_state, list)):
            print(f"Warning: line_state missing for table index {table_idx}.")
            return
            
        if not (0 <= line_id_req < len(remap_obj.line_state)):
            print(f"Warning: Invalid line index {line_id_req} for table {table_idx}.")
            return
            
        print(f"UI Request: Setting line {line_id_req} on table {table_id_req} to {active_req}")
        remap_obj.line_state[line_id_req] = active_req
        
        # Get actual simulation line indices
        line_output_indices = remap_obj.get_mapped_indices(line_id_req)
        if line_output_indices:
            for sim_line_id in line_output_indices:
                self.table.table_set_line_status(table_idx, sim_line_id, active_req)
                
        # Broadcast change
        response = {
            "type": "LINE_UPDATE",
            "payload": [{
                "table": table_id_req,
                "line": line_id_req,
                "active": active_req
            }]
        }
        if self.mqtt_manager:
            self.mqtt_manager.publish_to_gui(json.dumps(response))
            
        self.app_state.request_update()
        
    def _ui_place_module(self, payload):
        """Handle module placement from GUI."""
        module_id = payload.get('module_id')
        position = payload.get('position')
        
        if module_id and position:
            print(f"GUI Request: Simulating placement of '{module_id}' at '{position}'")
            # TODO: Implement simulated placement
            self.app_state.request_update()
        else:
            print("Warning: PLACE_MODULE message missing 'module_id' or 'position'.")
            
    def _ui_remove_module(self, payload):
        """Handle module removal from GUI."""
        position = payload.get('position')
        
        if position:
            print(f"GUI Request: Simulating removal from '{position}'")
            # TODO: Implement simulated removal
            self.app_state.request_update()
        else:
            print("Warning: REMOVE_MODULE message missing 'position'.")
            
    def _ui_load_scenario(self, payload):
        """Load scenario from GUI request."""
        scenario_file = payload.get('scenario_file')
        is_static_payload = True  # Default to static for now
        
        if scenario_file:
            print(f"GUI Request: Loading scenario '{scenario_file}' (static={is_static_payload})")
            self.table.scenario_set(scenario_file, is_static_payload)
            self.table.set_restrictions(is_static_payload)
            self.app_state.request_update()
        else:
            print("Warning: LOAD_SCENARIO message missing 'scenario_file'.")
            
    # ============== Prototype MQTT Message Dispatch ==============
    
    def dispatch_proto_message(self, message_dict: dict):
        """Dispatch a prototype MQTT message."""
        direction = message_dict.get('direction')
        module_id = message_dict.get('module')
        
        if direction is not None and module_id is not None:
            self.table.change_photovoltaic(direction, module_id)
            self.app_state.request_update()
        else:
            print("Warning: Received proto message missing 'direction' or 'module'.")
            
    # ============== Jupyter Command Dispatch ==============
    
    def dispatch_jupyter_command(self, command_str: str):
        """Dispatch a Jupyter command."""
        print(f"Received from Jupyter: {command_str}")
        
        # For now, reuse console command dispatcher
        # Could implement separate Jupyter-specific handlers if needed
        console_result = self.dispatch_console_command(command_str)
        
        # Send response back to Jupyter
        if self.mqtt_manager:
            if console_result:
                self.mqtt_manager.publish_to_jupyter(json.dumps({'status': 'Command executed'}))
            else:
                self.mqtt_manager.publish_to_jupyter(json.dumps({'error': f'Unknown command: {command_str}'}))

    def _simulate_module_placement(self, rfid, table_name, position):
        """Simulate placing a module on a table section."""
        if not self.app_state.simulation_mode:
            print("Warning: Module simulation only works in simulation mode")
            return
            
        # Find the section
        section = None
        for sec in self.table._SmartGridTable__table_sections:
            if sec.name.lower() == table_name.lower():
                section = sec
                break
                
        if not section:
            print(f"Error: Table section '{table_name}' not found")
            print(f"Available sections: {[s.name for s in self.table._SmartGridTable__table_sections]}")
            return
            
        # Find the platform
        platform = None
        for plat in section.platforms:
            if plat.RFID_location == position:
                platform = plat
                break
                
        if not platform:
            print(f"Error: Position {position} not found on {table_name}")
            print(f"Available positions: {[p.RFID_location for p in section.platforms]}")
            return
            
        # Get the module from the current scenario
        scenario = self.table._SmartGridTable__current_scenario
        if not scenario:
            print("Error: No current scenario loaded")
            return
            
        module = scenario.get_module(rfid)
        if not module:
            print(f"Error: Module with RFID {rfid} not found in current scenario")
            print("Available modules in scenario can be checked with 'scenario current'")
            return
            
        # Place the module
        platform.name_prefix = section._Section__prefix
        platform.add_module(module)
        
        # Trigger update
        self.app_state.request_update()
        print(f"✅ Placed {module.name} on {table_name} position {position}")
        
    def _simulate_module_removal(self, table_name, position):
        """Simulate removing a module from a table section."""
        if not self.app_state.simulation_mode:
            print("Warning: Module simulation only works in simulation mode")
            return
            
        # Find the section
        section = None
        for sec in self.table._SmartGridTable__table_sections:
            if sec.name.lower() == table_name.lower():
                section = sec
                break
                
        if not section:
            print(f"Error: Table section '{table_name}' not found")
            return
            
        # Find the platform
        platform = None
        for plat in section.platforms:
            if plat.RFID_location == position:
                platform = plat
                break
                
        if not platform:
            print(f"Error: Position {position} not found on {table_name}")
            return
            
        # Remove the module
        if platform.module:
            module_name = platform.module.name
            platform.clear_module()
            self.app_state.request_update()
            print(f"✅ Removed {module_name} from {table_name} position {position}")
        else:
            print(f"⚠️  No module at {table_name} position {position}")
            
    def _simulate_quick_setup(self):
        """Quickly place some test modules for demonstration."""
        if not self.app_state.simulation_mode:
            print("Warning: Module simulation only works in simulation mode")
            return
            
        test_modules = [
            # Transformers (critical for grid connectivity!)
            {"rfid": "1071746625", "table": "Table1", "position": 0},  # HV-MV TF1 (connects HV to MV)
            {"rfid": "3113060275", "table": "Table1", "position": 3},  # HV-MV TF6 (connects HV to MV)
            {"rfid": "1071746557", "table": "Table4", "position": 0},  # MV-LV TF 1 (connects MV to LV)
            {"rfid": "1072051579", "table": "Table5", "position": 0},  # MV-LV TF 2 (connects MV to LV)
            {"rfid": "1072040213", "table": "Table6", "position": 0},  # MV-LV TF 3 (connects MV to LV)
            # Generators
            {"rfid": "1071771887", "table": "Table1", "position": 1},  # Coal powerplant (60 MW)
            {"rfid": "1071966141", "table": "Table1", "position": 5},  # Gas powerplant (60 MW) - fixed position
            {"rfid": "1071766506", "table": "Table3", "position": 0},  # Solar farm (6.2 MW)
            {"rfid": "643269249", "table": "Table3", "position": 1},   # Solar farm (6.2 MW)
            # Loads
            {"rfid": "1072066624", "table": "Table3", "position": 2},  # Processing factory (22 MW load)
            {"rfid": "2041806607", "table": "Table3", "position": 3},  # Processing factory 4 (22 MW load)
            {"rfid": "1072051546", "table": "Table4", "position": 1},  # Chemical factory (10 MW load)
            {"rfid": "522332469", "table": "Table5", "position": 1},   # Chemical factory 2 (10 MW load)
        ]
        
        print("🔧 Quick setup: Placing transformers, generators and loads for connected grid...")
        for module in test_modules:
            self._simulate_module_placement(module["rfid"], module["table"], module["position"])
            
        print("🔌 Transformers: 5 transformers to connect HV→MV→LV")
        print("📊 Balance: ~132 MW generation vs ~64 MW loads")
        print("✅ Grid should now be fully connected for successful power flow calculation")

    def _simulate_simple_setup(self):
        """Place minimal modules for testing."""
        if not self.app_state.simulation_mode:
            print("Warning: Module simulation only works in simulation mode")
            return
            
        # Place minimal modules for testing
        self._simulate_module_placement("1071746625", "Table1", 0)  # HV-MV TF1 (connects HV to MV)
        self._simulate_module_placement("1071746557", "Table4", 0)  # MV-LV TF 1 (connects MV to LV)
        self._simulate_module_placement("1071771887", "Table1", 1)  # Coal powerplant (60 MW)
        self._simulate_module_placement("1071766506", "Table3", 0)  # Solar farm (6.2 MW)
        self._simulate_module_placement("1072066624", "Table3", 2)  # Processing factory (22 MW load)
        self._simulate_module_placement("1072051546", "Table4", 1)  # Chemical factory (10 MW load)
        
        print("🔌 Minimal setup: 5 modules to test grid connectivity")
        print("✅ Grid should now be fully connected for successful power flow calculation") 