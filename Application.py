##
# @mainpage Smart Grid Table Project
#
# @section description_main Description
# A Python program which controls the behavior of the Smart Grid Table.
#
# @section notes_main Notes
# Version 1.1
#
# @file Application.py
#
# @brief Python program which calculates the Smart Grid Table network.
#
# @section description_Application Description.
# O_o
#
# @section libraries_main Libraries/Modules
# ─ socket standard library (https://docs.python.org/3/library/socket.html)
#   ─ Access to socket class.
#
# @section notes_Application Notes
# ─ Comments are Doxygen compatible.
#
# @section todo_Application TODO
# ─ Seperate command handler.
#
# @section author_Application Author(s)
# ─ Created by Jop Merz, Thijs van Elsacker on 31/01/2023.
# ─ Modified by Jop Merz on 31/01/2023.
##

# Imports
#import fix_pandapower  # Deze patch moet vóór alles anders worden geladen
import json
import warnings
import socket
import sys
from time import sleep
from threading import Thread
from src.SmartGridTable import SmartGridTable
from src.networking.UDPBroadcaster import UDPBroadcaster
from src.GUI_MQTT import GUI_MQTT
from src.Prototype_MQTT import Prototype_MQTT
from src.Jupyter_Prototype_Mqtt import Jupyter_MQTT
from src.IndexRemap import IndexRemap


# Check if simulation mode is enabled via command line
simulation_mode = "--simulation" in sys.argv

# We take the local ip address and put it as local broker.
# (the broker server need to run on the same computer than the one executing the code).
## Socket used to retrieve local IP.
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Try connecting to a public DNS server to find the preferred local IP
try:
    s.connect(("8.8.8.8", 80))
    local_broker_ip = s.getsockname()[0]
except OSError:
    # Fallback if connection fails (e.g., offline)
    local_broker_ip = "127.0.0.1" # Use localhost as fallback
finally:
    s.close()

mqtt_public_broker = "localhost" # Default, may be overridden by config?
warnings.simplefilter(action='ignore', category=FutureWarning)

# Global Constants
## Forces PyPSA to simulate with the current mode (PF, LPF or LOPF).
force_update: bool = False

## Current mode (PF, LPF or LOPF).
mode: str = "optimize"

## Terminal input from a seperate thread so the program wont pause.
global_console_input: str = ""

## Indicator if the shutdown command is given (True = no shutdown, False = shutdown).
running: bool = True

## Time between each update in seconds. Each update will check if the table has changed and act accordingly.
refresh_rate: float = 0.01

print("────────────────────────────────────────────────────────────────")
print("─────────────── Loading SmartGridTable scenarios ───────────────")
print("────────────────────────────────────────────────────────────────")

## Main table instance. This instance lays the link between all table sections and the connection between these sections and PyPSA network
table: SmartGridTable = SmartGridTable("config.json")

if (not table.table_succes()):
    print("Error while starting program, arborting...")
    exit()

## Seperate MQTT client for the GUI app.
mqtt_gui: GUI_MQTT = GUI_MQTT()
line_remap_gui: list[IndexRemap] = []

prototype_gui=Prototype_MQTT()
jupyter=Jupyter_MQTT()

# Functions
def console_thread_function():
    """!
    Thread running in the background waiting for user input.
    """
    global global_console_input
    # global running # <-- Verwijderd (F824), alleen lezen hier

    while(running): # Leest globale 'running'
        try:
            global_console_input = input()
        except EOFError as e:
            # Handle EOFError if input stream closes unexpectedly
            print("EOFError encountered in console input. Shutting down.")
            # Need to signal the main thread to stop
            # Using global running here *might* be needed if we wanted this thread
            # to set running = False, but currently it signals via the input string.
            # Let's assume console_handler sets running=False based on input.
            break
        if (global_console_input == "shutdown"):
            # Signal main thread via the input string, console_handler will set running=False
            break


udp_broadcaster: UDPBroadcaster = UDPBroadcaster()

def init():
    """!
    Initialize the program.
    """
    # global simulation_mode # <-- Verwijderd (F824), alleen lezen hier

    # Handle simulation mode
    if simulation_mode: # Leest globale 'simulation_mode'
        print("────────────────────────────────────────────────────────────────")
        print("─────────── Running in simulation mode without table ───────────")
        print("────────────────────────────────────────────────────────────────")

        # Import mock sections if we're in simulation mode
        try:
            from mock_sections import simulate_table_connection
            simulate_table_connection()
        except ImportError:
            print("Warning: mock_sections.py not found, simulation may not work correctly")

    if (table.get_local_setup()):

        ## Load the GUI LED remapping objects
        for i in range(6):
            line_remap_gui.append(IndexRemap())

        # Consider error handling if files don't exist
        try:
            line_remap_gui[0].load("configuration/gui_line_remap/gui_remap_table1.json")
            line_remap_gui[1].load("configuration/gui_line_remap/gui_remap_table2.json")
            line_remap_gui[2].load("configuration/gui_line_remap/gui_remap_table3.json")
            line_remap_gui[3].load("configuration/gui_line_remap/gui_remap_table4.json")
            line_remap_gui[4].load("configuration/gui_line_remap/gui_remap_table5.json")
            line_remap_gui[5].load("configuration/gui_line_remap/gui_remap_table6.json")
        except FileNotFoundError as e:
            print(f"Error loading GUI line remap config: {e}")
            # Decide how to handle - exit or continue without remap?

        protocol_version =  "0000"
        opcode = "0000"

        ## UDP broadcast message structure
        ## [protocol id ─ 4 bytes]
        ## [opcode      ─ 4 bytes]
        ## [IP address  ─ string of variable lenght, NULL terminated]
        message = protocol_version + opcode + str(local_broker_ip)

        # Add NULL terminator at end of IP address.
        # EPS32 boards uses raw char types and only supports NULL terminated strings.
        stringLenght = len(message)
        message = message[:stringLenght] + '\0' + message[stringLenght + 1:]

        udp_broadcaster.set_interval(0.1)
        udp_broadcaster.set_port(5005)
        udp_broadcaster.set_message(message.encode('UTF-8')) # Correct encoding 'UTF-8'
        udp_broadcaster.start_broadcasting()


    print("────────────────────────────────────────────────────────────────")
    print("──────────────────── Starting MQTT clients ─────────────────────")
    print("────────────────────────────────────────────────────────────────")

    mqtt_gui.mqtt_set_broker(mqtt_public_broker)
    mqtt_gui.mqtt_connect()
    prototype_gui.mqtt_set_broker(mqtt_public_broker)
    prototype_gui.mqtt_connect()
    jupyter.mqtt_set_broker(mqtt_public_broker)
    jupyter.mqtt_connect()

    table.mqtt_connect()

    while(not table.mqtt_is_connected()): # Simpler check
        sleep(refresh_rate)

    sleep(1)

    print("────────────────────────────────────────────────────────────────")
    print("──────────── Connecting to SmartGridTable sections ─────────────")
    print("────────────────────────────────────────────────────────────────")

    table.table_ping_all()
    table.modules_enable_messages(False)

    timer = 0
    timer_limit = 3.0
    timeout_limit = 6.0
    timeout = False

    # Skip waiting for physical connections if in simulation mode
    if not simulation_mode:
        while(not table.table_is_online() and not timeout):
            sleep(refresh_rate)
            timer += refresh_rate
            if (timer >= timer_limit and timer < timeout_limit): # Avoid multiple prints
                time_left = timeout_limit - timer
                print(f"Timeout in [{time_left:.1f}] seconds...")
                timer_limit += 1.0 # Increase limit for next message
            if (timer >= timeout_limit):
                print("Timeout when trying to connect...")
                timeout = True
    else:
        # In simulation mode, we pretend tables are already connected
        print("Simulation mode: Tables connected automatically")

    print("────────────────────────────────────────────────────────────────")
    print("────────────── Retrieving SmartGridTable Modules ───────────────")
    print("────────────────────────────────────────────────────────────────")

    # Only change interval if broadcaster was started
    if table.get_local_setup() and udp_broadcaster:
         udp_broadcaster.set_interval(1)

    table.table_retrieve_modules()

    timer = 0
    timeout_limit = 3.0
    timeout = False

    # Skip waiting for RFID readers if in simulation mode
    if not simulation_mode:
        while(not table.table_is_rfid_online() and not timeout):
            sleep(refresh_rate)
            timer += refresh_rate
            if (timer >= timeout_limit):
                print("Timeout waiting for RFID readers.")
                timeout = True
    else:
        # In simulation mode, we pretend RFID readers are already online
        print("Simulation mode: RFID readers connected automatically")

    table.modules_print_status()
    table.modules_enable_messages(True)

    print("────────────────────────────────────────────────────────────────")
    print("───────────── SmartGridTable 2022 up and running! ──────────────")
    print("────────────────────────────────────────────────────────────────")


def print_help_commands():
    """!
    Print all available commands.
    """

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
    print("────────────────────────────────────────────────────────────────")


def console_handler(input_str): # Renamed parameter to avoid conflict with input()
    """!
    Converts input strings into actions
    @param input_str (str) The console string given by the user
    """

    global force_update
    global mode
    global running # NEEDED here because we ASSIGN to running = False
    console_input = input_str.split()
    known_command = False

    if not console_input: # Handle empty input
        return

    command = console_input[0].lower() # Use lower case for commands

    # global commands
    if (command == "help"):
        print_help_commands()
        known_command = True
    elif (command == "transformer_capacity"):
        transformer_df, capacity_df = table.transformer_capacity()
        print(transformer_df)
        print(capacity_df)
        known_command = True
    elif (command == "module"):
        if len(console_input) >= 3:
            sub_command = console_input[1].lower()
            table_name = console_input[2]
            if sub_command == 'generation':
                 print(table.get_table_section_module_generation(table_name))
            elif sub_command == 'load':
                 print(table.get_table_section_module_load(table_name))
            elif sub_command == 'storage':
                 print(table.get_table_section_module_storage(table_name))
            # Removed all (covered by individual commands)
            else:
                 print("Unknown module sub-command. Use generation, load, or storage.")
            known_command = True
        else:
             print("Usage: module [generation|load|storage] [TABLE_NAME]")
    elif (command == "run"):
        print("Starting automatic index increment.")
        table.start_running()
        known_command = True
    elif (command == "summation"):
        print(table.get_full_grid_sum_generation_loads_storage())
        known_command = True
    elif (command == "stop"):
        print("Stopping automatic index increment.")
        table.stop_running()
        known_command = True
    elif (command == "index"):
        if len(console_input) >= 2:
            try:
                 index_val = int(console_input[1])
                 table.set_index(index_val)
            except ValueError:
                 print("Error: Index must be an integer.")
            known_command = True
        else:
            print("Usage: index [NUMBER]")
    elif (command == "photo"):
        if len(console_input) >= 3:
            direction = console_input[1]
            module_id = console_input[2]
            table.change_photovoltaic(direction, module_id)
            force_update = True # Recalculate after changing PV
            known_command = True
        else:
             print("Usage: photo [South|East|West|None] [MODULE_ID]")
    elif (command == "tablesection"):
        if len(console_input) >= 2:
            print(table.get_table_sum(console_input[1]))
            known_command = True
        else:
            print("Usage: tablesection [TABLE_NAME]")
    elif (command == "voltage"):
        if len(console_input) >= 2:
            print(table.get_voltage_sum(console_input[1]))
            known_command = True
        else:
            print("Usage: voltage [LV|MV|HV]")
    elif (command == "shutdown"):
        print("Shutting down program...")
        running = False # Assign False to the global variable
        known_command = True
    elif (command == "calculate"):
        print("Forcing simulation update...")
        force_update = True
        known_command = True
    elif (command == "modules"):
        if len(console_input) >= 2 and console_input[1].lower() == "list":
            table.modules_print_status()
            known_command = True
            print("────────────────────────────────────────────────────────────────")
        else:
            print("Usage: modules list")

    # table commands
    elif (command == "table"):
        if len(console_input) >= 2:
            sub_command = console_input[1].lower()
            if sub_command == "list":
                table.table_print_list()
                known_command = True
            elif sub_command == "update":
                if len(console_input) >= 3:
                    update_target = console_input[2].lower()
                    if update_target == "firmware":
                        print("Updating all table tiles to the latest firmware")
                        table.table_update_firmware_all()
                        known_command = True
                    elif update_target == "config":
                        print("Updating all table tiles to the latest config settings")
                        table.table_update_config_all()
                        known_command = True
                    else:
                         print("Usage: table update [firmware|config]")
                else:
                    print("Usage: table update [firmware|config]")
            elif sub_command == "reboot":
                if len(console_input) >= 3:
                    target = console_input[2]
                    if target.lower() == "all":
                        print("Restarting all table sections...")
                        table.table_reboot_all()
                        known_command = True
                    else:
                        print(f"Restarting section -> {target}")
                        table.table_reboot(target)
                        known_command = True
                else:
                    print("Usage: table reboot [all|SECTION_NAME]")
            elif sub_command == "shutdown":
                 if len(console_input) >= 3:
                     target = console_input[2]
                     if target.lower() == "all":
                          print("Shutting down all table sections...")
                          table.mqtt_disconnect() # Disconnect MQTT first
                          known_command = True
                     else:
                          print(f"Shutting down section -> {target}")
                          table.table_shutdown(target)
                          known_command = True
                 else:
                     print("Usage: table shutdown [all|SECTION_NAME]")
            elif sub_command == "poweron":
                if len(console_input) >= 3:
                    target = console_input[2]
                    if target.lower() == "all":
                        print("Activating all table sections...")
                        table.mqtt_connect()
                        known_command = True
                    else:
                        print(f"Activating section -> {target}")
                        table.table_poweron(target)
                        known_command = True
                else:
                    print("Usage: table poweron [all|SECTION_NAME]")
            else:
                print("Unknown table command. Use list, update, reboot, shutdown, poweron.")
            if known_command: print("────────────────────────────────────────────────────────────────")


    # scenario commands
    elif (command == "scenario"):
        if len(console_input) >= 2:
            sub_command = console_input[1].lower()
            if sub_command == "reload":
                print("Reloading scenarios...")
                table.scenario_refresh_list()
                known_command = True
            elif sub_command == "list":
                table.scenario_print_list()
                known_command = True
            elif sub_command == "current":
                table.scenario_print_current()
                known_command = True
            elif sub_command == "set":
                if len(console_input) >= 4:
                    flag = console_input[2].lower()
                    scenario_name = console_input[3]
                    if flag == "-s":
                        table.scenario_set(scenario_name, static=True)
                        force_update = True
                        known_command = True
                    elif flag == "-d":
                        table.scenario_set(scenario_name, static=False)
                        force_update = True
                        known_command = True
                    else:
                        print("Usage: scenario set [-s|-d] [SCENARIO_NAME]")
                else:
                     print("Usage: scenario set [-s|-d] [SCENARIO_NAME]")
            else:
                print("Unknown scenario command. Use reload, list, current, set.")
            if known_command: print("────────────────────────────────────────────────────────────────")


    # mode commands
    elif (command == "mode"):
        if len(console_input) >= 3 and console_input[1].lower() == "set":
            new_mode = console_input[2].lower()
            valid_modes = ["optimize", "lopf", "lpf", "pf"]
            if new_mode in valid_modes:
                print(f"Setting mode to {new_mode.upper()}")
                mode = new_mode # Assign to global mode
                table.set_calculation_method(mode) # Inform table instance
                force_update = True
                known_command = True
            else:
                print(f"Invalid mode '{new_mode}'. Valid modes are: {', '.join(valid_modes)}")
        else:
            print("Usage: mode set [optimize|lopf|lpf|pf]")


    if not known_command:
        print(f"Unknown command -> {input_str}")
        print("Type 'help' for all available commands")


def ui_handler(input_data): # Renamed parameter
    """Handles messages received from the GUI MQTT topic."""
    global force_update

    # Use .get() for safer dictionary access
    message_type = input_data.get('type')
    payload = input_data.get('payload', {}) # Default to empty dict if no payload

    if not message_type:
         print("Warning: Received UI message without 'type'.")
         return

    # Command for sending complete scenario catalog.
    if message_type == 'SEND_SCENARIO_JSON':
        response = {
            'type': 'SCENARIO_JSON',
            'payload': {
                "scenario_json": table.get_referenceless_catalog(),
                "is_static": table.get_scenario_type()
            }
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending complete restrictions object.
    elif message_type == 'SEND_RESTRICTIONS':
        rest = table.get_current_restrictions()
        response = {
            'type': 'RESTRICTIONS_JSON',
            'payload': rest
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for changing module properties.
    elif message_type == 'CHANGE_MODULE_PARAMETER':
        updates = {}
        # Update copy of catalog.
        catalog = table.get_referenceless_catalog()
        if isinstance(payload, dict):
            for id_key, value in payload.items(): # Use items() for dict iteration
                catalog[id_key] = value
                updates.update({id_key:value})
        else:
             print("Warning: CHANGE_MODULE_PARAMETER payload was not a dictionary.")

        # Send updates to other clients.
        response = {
            "type": "SCENARIO_UPDATE",
            "payload": {
                "scenario_updates": updates
            }
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

        # Push changes to scenario.
        table.change_current_scenario_catalog(catalog)
        table.modules_reload()

        # Force update the simulation.
        force_update = True

    # Command for sending all active modules on grid.
    elif message_type == 'SEND_ACTIVE_MODULES':
        # Maybe this should trigger sending module status updates?
        # The table.table_retrieve_modules() sends a request *to* the tables,
        # it doesn't send data *from* the server *to* the GUI immediately.
        # We might need a separate function to get current module state.
        # For now, let's just trigger the MQTT update of current state.
        changes = table.get_module_changes() # Get buffered changes
        table.empty_module_change_buffer() # Clear buffer
        for change in changes:
            table_section = change["table_section"]
            modules = change["buffer"]
            for module_info in modules: # Renamed 'module' to 'module_info'
                message = {"type": "MODULE_UPDATE", "payload": {"table_section": table_section, **module_info}}
                mqtt_gui.mqtt_publish(json.dumps(message))
        print("Info: Sent current active module status to GUI.")


    # Command for sending the list of available scenarios.
    elif message_type == 'SEND_SCENARIO_LIST':
        is_static_payload = payload.get('is_static', True) # Default to static if missing
        scenario_list = table.get_scenario_list(isStatic=is_static_payload)
        response = {
            "type": "SCENARIO_LIST",
            "payload": {
                "scenario_list": scenario_list,
                "is_static": is_static_payload
            }
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for changing the selected scenario.
    elif message_type == 'CHANGE_SCENARIO':
        scenario_name = payload.get('scenario_name')
        is_static_payload = payload.get('is_static')
        if scenario_name is not None and is_static_payload is not None:
            table.scenario_set(scenario_name, is_static_payload)
            table.set_restrictions(is_static_payload)

            # Send back the new scenario and restrictions
            response_scenario = {
                'type': 'SCENARIO_JSON',
                'payload': {
                    "scenario_json": table.get_referenceless_catalog(),
                    "is_static": table.get_scenario_type()
                }
            }
            mqtt_gui.mqtt_publish(json.dumps(response_scenario))

            response_restrictions = {'type': 'RESTRICTIONS_JSON', 'payload': table.get_current_restrictions()}
            mqtt_gui.mqtt_publish(json.dumps(response_restrictions))

            force_update = True
        else:
             print("Warning: CHANGE_SCENARIO message missing 'scenario_name' or 'is_static'.")

    # Command for updating a users restrictions.
    elif message_type == 'CHANGE_RESTRICTIONS':
        if isinstance(payload, list): # Ensure payload is a list
             table.change_restrictions(changes=payload)
             # Notify other clients of changes made
             response = {
                 "type": "RESTRICTIONS_UPDATE",
                 "payload": payload
             }
             mqtt_gui.mqtt_publish(json.dumps(response))
        else:
             print("Warning: CHANGE_RESTRICTIONS payload was not a list.")


    # Command for sending network snapshots of total generation and consumption.
    elif message_type == 'SEND_SNAPSHOTS':
        response = table.get_snapshot_response_gui()
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending all line statuses.
    elif message_type == 'SEND_LINE_STATUSES':
        response_dict = {
            "type": "LINE_UPDATE",
            "payload": [] # Array of line states
        }
        sections_num = len(line_remap_gui)
        for section_id in range(sections_num):
            if section_id < len(line_remap_gui): # Boundary check
                 for line_id in range(len(line_remap_gui[section_id].line_state)):
                      line_active = line_remap_gui[section_id].line_state[line_id]
                      line_dict = {
                          "table": section_id + 1,
                          "line": line_id,
                          "active": line_active
                      }
                      response_dict["payload"].append(line_dict)
            else:
                 print(f"Warning: section_id {section_id} out of bounds for line_remap_gui.")

        mqtt_gui.mqtt_publish(json.dumps(response_dict))

    # Command for changing the state of a line.
    elif message_type == 'CHANGE_LINE':
        table_id_req = payload.get("table")
        line_id_req = payload.get("line")
        active_req = payload.get("active")

        if table_id_req is None or line_id_req is None or active_req is None:
             print("Warning: CHANGE_LINE message missing 'table', 'line', or 'active'.")
             return

        table_idx = table_id_req - 1 # Convert to 0-based index
        sections_num = len(line_remap_gui)

        if not (0 <= table_idx < sections_num):
             print(f"Warning: Invalid table index {table_idx} in CHANGE_LINE.")
             return

        line_num = len(line_remap_gui[table_idx].line_state)
        if not (0 <= line_id_req < line_num):
             print(f"Warning: Invalid line index {line_id_req} for table {table_idx} in CHANGE_LINE.")
             return

        # Update the state
        line_remap_gui[table_idx].line_state[line_id_req] = active_req
        # Get the actual lines in the simulation model to update
        line_output_indices = line_remap_gui[table_idx].get_mapped_indices(line_id_req)

        if line_output_indices: # Check if list is not empty
            for sim_line_id in line_output_indices:
                table.table_set_line_status(table_idx, sim_line_id, active_req)

        # Respond / Broadcast the change
        response = {
            "type": "LINE_UPDATE",
            "payload": [payload] # Send back the original payload structure
        }
        mqtt_gui.mqtt_publish(json.dumps(response))
        force_update = True

    else:
         print(f"Warning: Received unknown UI message type: {message_type}")


def proto_handler(input_data): # Renamed parameter
    """Handles messages received from the prototype MQTT topic."""
    global force_update
    direction = input_data.get('direction')
    module_id = input_data.get('module')
    if direction is not None and module_id is not None:
        table.change_photovoltaic(direction, module_id)
        force_update = True
    else:
         print("Warning: Received proto message missing 'direction' or 'module'.")


def jupyter_handler(input_str): # Renamed parameter
    """Handles messages received from the Jupyter MQTT topic."""
    # Jupyter handler to receive and send information
    console_input = input_str.split()
    print(f"Received from Jupyter: {input_str}") # Log received command
    known_command = False

    if not console_input: return
    command = console_input[0].lower()

    # Reusing console handler logic but publishing results via jupyter.mqtt_publish
    # Note: This duplicates logic from console_handler. Consider refactoring.

    if command == "tablesection":
        if len(console_input) >= 2:
            df = table.get_table_sum(console_input[1])
            if df is not None and not df.empty: jupyter.mqtt_publish(df.to_json())
            known_command = True
    elif command == "voltage":
        if len(console_input) >= 2:
            df = table.get_voltage_sum(console_input[1])
            if df is not None and not df.empty: jupyter.mqtt_publish(df.to_json())
            known_command = True
    elif command == "transformer": # Assuming this means transformer_capacity
        df_power, df_capacity = table.transformer_capacity()
        # Combine results into one JSON object for easier parsing
        result_json = json.dumps({
             'power': json.loads(df_power.to_json(orient='split')), # Use split orient for better structure
             'capacity': json.loads(df_capacity.to_json(orient='split'))
        })
        jupyter.mqtt_publish(result_json)
        known_command = True
    elif command == "summation":
        df = table.get_full_grid_sum_generation_loads_storage()
        if df is not None and not df.empty: jupyter.mqtt_publish(df.to_json())
        known_command = True
    elif command == "index":
        if len(console_input) >= 2:
            try: table.set_index(int(console_input[1]))
            except ValueError: print("Jupyter Error: Index must be int")
            known_command = True
    elif command == "stop":
        table.stop_running()
        known_command = True
    elif command == "run": # Added run command
        table.start_running()
        known_command = True
    elif command == "module":
        if len(console_input) >= 3:
            sub_cmd = console_input[1].lower()
            table_name = console_input[2]
            df = None
            if sub_cmd == 'generation': df = table.get_table_section_module_generation(table_name)
            elif sub_cmd == 'load': df = table.get_table_section_module_load(table_name)
            elif sub_cmd == 'storage': df = table.get_table_section_module_storage(table_name)

            if df is not None and not df.empty: jupyter.mqtt_publish(df.to_json())
            known_command = True
    elif command == "scenario":
        # Implement scenario commands similar to console_handler if needed for Jupyter
        # Example: Change scenario
        if len(console_input) >= 4 and console_input[1].lower() == "set":
             flag = console_input[2].lower()
             name = console_input[3]
             if flag == "-s": table.scenario_set(name, static=True); force_update=True
             elif flag == "-d": table.scenario_set(name, static=False); force_update=True
             known_command = True
             # Optionally send confirmation or new state back to Jupyter
    # Add other commands as needed, mirroring console_handler structure

    if not known_command:
         print(f"Jupyter: Unknown command '{input_str}'")
         # Optionally send error back to Jupyter
         # jupyter.mqtt_publish(json.dumps({'error': f'Unknown command: {input_str}'}))


# Main Program Entry Point
def application_main(simulation_mode_param=None, simulate_table_connection=None):
    """Main execution function."""
    global simulation_mode # Needed because we might assign to it
    global global_console_input
    # global running <-- Removed (F824) - Modified via console_handler
    global force_update
    # global mode <-- Removed (F824) - Modified via console_handler

    # Override simulation_mode if provided as parameter
    if simulation_mode_param is not None:
        simulation_mode = simulation_mode_param

    # Run initialization
    init()

    # Start console input thread
    console_thread = Thread(target=console_thread_function, daemon=True) # Set as daemon
    console_thread.start()

    timer = 0
    force_update = True # Start with an initial calculation

    print("Entering main loop...")
    while(running): # Reads global 'running'
        try:
            # Main loop logic
            sleep(refresh_rate)

            # GUI mqtt message handler
            if mqtt_gui.message_buffer: # Check if list is not empty
                messages = mqtt_gui.message_buffer[:] # Copy buffer
                mqtt_gui.message_buffer.clear() # Clear original immediately
                for message in messages:
                    try: ui_handler(message)
                    except Exception as e: print(f"Error in ui_handler: {e}")

            # Prototype mqtt message handler
            if prototype_gui.message_buffer:
                messages = prototype_gui.message_buffer[:]
                prototype_gui.message_buffer.clear()
                for message in messages:
                     try: proto_handler(message)
                     except Exception as e: print(f"Error in proto_handler: {e}")

            # Jupyter mqtt message handler
            if jupyter.message_buffer:
                messages = jupyter.message_buffer[:]
                jupyter.message_buffer.clear()
                for message in messages:
                    try: jupyter_handler(message)
                    except Exception as e: print(f"Error in jupyter_handler: {e}")

            # Console input message handler
            if global_console_input: # Check if string is not empty
                input_cmd = global_console_input
                global_console_input = "" # Clear immediately
                try: console_handler(input_cmd)
                except Exception as e: print(f"Error in console_handler: {e}")


            # Update elapsed time for table instance (dynamic scenarios)
            table.append_delta_time(refresh_rate)
            table.update() # Handles snapshot changes for dynamic mode

            timer += refresh_rate

            # --- Calculation Logic ---
            recalculate = False
            calc_reason = ""

            if force_update:
                recalculate = True
                calc_reason = "Forced update requested"
                force_update = False # Reset flag
                timer = 0
            elif table.modules_if_changed():
                 recalculate = True
                 calc_reason = "Module change detected"
                 timer = 0

            if recalculate:
                print(f"Recalculating simulation ({calc_reason})...")
                # Ensure calculation method is set (mode is global)
                table.set_calculation_method(mode)

                if calc_reason == "Module change detected":
                    table.selective_calculate() # Use selective if possible
                else:
                    table.force_calculate() # Use full recalculation otherwise

                # Send updates after calculation
                ui_handler({'type': 'SEND_SNAPSHOTS'}) # Send snapshot data to GUI
                changes = table.get_module_changes()
                table.empty_module_change_buffer()
                for change in changes:
                    table_section = change["table_section"]
                    modules = change["buffer"]
                    for module_info in modules:
                        message = {"type": "MODULE_UPDATE", "payload": {"table_section": table_section, **module_info}}
                        mqtt_gui.mqtt_publish(json.dumps(message))

                print("Calculation complete.")
                print("────────────────────────────────────────────────────────────────")


            # --- LED Update Logic ---
            # Separate from calculation logic
            if table.get_lep_update_flag(): # Renamed function assumed
                print("LED update flag detected, updating LEDs...")
                table.reset_led_update_flag()
                current_snapshot_index = 0 # Default to 0 for static or use table.get_current_snapshot_index() if available
                # Need a way to get the current index if dynamic
                # current_snapshot_index = table.get_current_snapshot_index() # Placeholder
                table.update_ledstrips(current_snapshot_index) # Update LED states based on results
                table.mqtt_selective_publish() # Send LED updates


            # Check if simulation results changed state that needs broadcasting
            # (This check might be redundant if SEND_SNAPSHOTS covers it)
            # if table.simulation_changed: # Flag set by calculate methods?
            #     table.simulation_changed = False
            #     ui_handler({'type': 'SEND_SNAPSHOTS'}) # Send updated snapshots

        except KeyboardInterrupt:
             print("\nCtrl+C detected. Shutting down...")
             global running
             running = False # Signal shutdown

    # --- Shutdown Sequence ---
    print("Exited main loop. Starting shutdown sequence...")
    if table.get_local_setup() and udp_broadcaster:
        print("Stopping UDP broadcaster...")
        udp_broadcaster.stop_broadcasting()

    # Console thread is daemon, might not need explicit join if main exits
    # print("Waiting for console thread...")
    # console_thread.join() # Might block if input() is stuck

    print("Disconnecting MQTT clients...")
    table.mqtt_disconnect()
    mqtt_gui.mqtt_disconnect()
    prototype_gui.mqtt_disconnect()
    jupyter.mqtt_disconnect()

    print("Shutting down table simulation...")
    table.shutdown() # Graceful shutdown of simulation threads

    print("────────────────────────────────────────────────────────────────")
    print("───────────────── Goodbye, until next time! ────────────────────")
    print("────────────────────────────────────────────────────────────────")

# If this file is run directly, start the application
if __name__ == "__main__":
    # Pass command line args if needed, or handle them internally
    application_main(simulation_mode_param=simulation_mode)