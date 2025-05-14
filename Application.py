##
# @mainpage Smart Grid Table Project
#
# @section description_main Description
# A Python program which controls the behavior of the Smart Grid Table.
#
# @section notes_main Notes
# Version 1.1 (Utilizes Pandapower for calculations)
#
# @file Application.py
#
# @brief Python program which calculates the Smart Grid Table network using Pandapower.
#
# @section description_Application Description.
# O_o
#
# @section libraries_main Libraries/Modules
# ─ socket standard library (https://docs.python.org/3/library/socket.html)
#   ─ Access to socket class.
# - paho-mqtt (MQTT communication)
# - pandapower (Power system analysis)
# - pandas, numpy (Data handling)
#
# @section notes_Application Notes
# ─ Comments are Doxygen compatible.
#
# @section todo_Application TODO
# ─ Separate command handler.
# ─ Refactor SmartGridTable/ModelProcessor/CalculatorThreadManager to exclusively use Pandapower calculators.
#
# @section author_Application Author(s)
# ─ Created by Jop Merz, Thijs van Elsacker on 31/01/2023.
# ─ Modified by Jop Merz on 31/01/2023.
##

# Imports
import json
import warnings
import socket
import sys
from time import sleep
from threading import Thread
# SmartGridTable wordt hier geïmporteerd. Zorg dat DIT bestand geen PyPSA meer nodig heeft!
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
## Forces the simulation to recalculate in the next cycle.
force_update: bool = False

## Current calculation mode (maps to Pandapower methods: PF, LPF, LOPF, Optimize).
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

## Main table instance. This instance links table sections and simulation (using Pandapower).
# BELANGRIJK: Zorg ervoor dat SmartGridTable intern correct met Pandapower werkt!
table: SmartGridTable = SmartGridTable("config.json")

if (not table.table_succes()):
    print("Error while starting program, aborting...")
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
    # global running # Lezen van global is ok zonder declaratie hier

    while(running): # Leest globale 'running'
        try:
            global_console_input = input()
        except EOFError as e:
            # Handle EOFError if input stream closes unexpectedly
            print("EOFError encountered in console input. Shutting down.")
            break
        if (global_console_input == "shutdown"):
            # Signal main thread via the input string, console_handler will set running=False
            break


udp_broadcaster: UDPBroadcaster = UDPBroadcaster()

def init():
    """!
    Initialize the program.
    """
    # global simulation_mode # Lezen van global is ok zonder declaratie hier

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
        message = protocol_version + opcode + str(local_broker_ip)

        # Add NULL terminator at end of IP address.
        stringLenght = len(message)
        message = message[:stringLenght] + '\0' + message[stringLenght + 1:]

        udp_broadcaster.set_interval(0.1)
        udp_broadcaster.set_port(5005)
        udp_broadcaster.set_message(message.encode('UTF-8'))
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

    # Wacht tot table MQTT verbonden is (indien nodig)
    # while(not table.mqtt_is_connected()): # Let op: deze functie bestaat misschien niet?
    #    sleep(refresh_rate)

    sleep(1) # Geef clients tijd om te verbinden

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
            if (timer >= timer_limit and timer < timeout_limit):
                time_left = timeout_limit - timer
                print(f"Timeout in [{time_left:.1f}] seconds...")
                timer_limit += 1.0
            if (timer >= timeout_limit):
                print("Timeout when trying to connect...")
                timeout = True
    else:
        print("Simulation mode: Tables connected automatically")

    print("────────────────────────────────────────────────────────────────")
    print("────────────── Retrieving SmartGridTable Modules ───────────────")
    print("────────────────────────────────────────────────────────────────")

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
        print("Simulation mode: RFID readers connected automatically")

    table.modules_print_status()
    table.modules_enable_messages(True)

    print("────────────────────────────────────────────────────────────────")
    print("───────────── SmartGridTable (Pandapower) up and running! ──────")
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


def console_handler(input_str):
    """!
    Converts input strings into actions
    @param input_str (str) The console string given by the user
    """
    # Deze functie wijst waarden toe aan global vars, dus declaraties nodig
    global force_update
    global mode
    global running
    console_input = input_str.split()
    known_command = False

    if not console_input:
        return

    command = console_input[0].lower()

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
                          table.mqtt_disconnect() # Disconnect MQTT first? Might prevent shutdown command delivery
                          # table.table_shutdown_all() # Assuming such a function exists or implement loop
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
                        table.mqtt_connect() # Reconnect all MQTT
                        # table.table_poweron_all() # Assuming such a function exists or implement loop/ping
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
            # BELANGRIJK: Verifieer of deze modes overeenkomen met de
            # beschikbare Pandapower calculators in CalculatorThreadManager!
            valid_modes = ["optimize", "lopf", "lpf", "pf"]
            if new_mode in valid_modes:
                print(f"Setting mode to {new_mode.upper()} (using Pandapower backend)")
                mode = new_mode # Assign to global mode
                table.set_calculation_method(mode) # Geef door aan de onderliggende lagen
                force_update = True
                known_command = True
            else:
                print(f"Invalid mode '{new_mode}'. Valid modes for Pandapower backend are: {', '.join(valid_modes)}")
        else:
            print("Usage: mode set [optimize|lopf|lpf|pf]")

    if not known_command:
        print(f"Unknown command -> {input_str}")
        print("Type 'help' for all available commands")


def ui_handler(input_data):
    """Handles messages received from the GUI MQTT topic."""
    global force_update # Nodig want we wijzigen deze variabele

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
        changes = table.get_module_changes() # Get buffered changes
        table.empty_module_change_buffer() # Clear buffer immediately
        # Send current state based on buffered changes (might need better state tracking)
        # This logic might need refinement based on how state is maintained
        active_modules_payload = []
        for change in changes:
            table_section = change["table_section"]
            modules = change["buffer"]
            for module_info in modules:
                 # Assuming module_info contains keys like 'module_id', 'position', 'type'
                 if module_info.get("state") == "placed": # Check state if available
                      active_modules_payload.append({
                           "module_id": module_info.get("RFID_tag"), # Use RFID_tag?
                           "position": module_info.get("location"), # Use location?
                           "type": module_info.get("name") # Use name for type?
                           # Adjust keys based on actual content of module_info
                      })
        # Send the composed list (might be empty if no recent changes)
        response = {"type": "ACTIVE_MODULES", "payload": active_modules_payload}
        mqtt_gui.mqtt_publish(json.dumps(response))
        print("Info: Sent current active module status estimate to GUI.")


    # Command for sending the list of available scenarios.
    elif message_type == 'SEND_SCENARIO_LIST':
        is_static_payload = payload.get('is_static', True)
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
            print(f"UI Request: Changing scenario to '{scenario_name}' (static={is_static_payload})")
            table.scenario_set(scenario_name, is_static_payload)
            table.set_restrictions(is_static_payload) # Update restrictions as well

            # Send back the new scenario and restrictions for confirmation
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

            force_update = True # Force recalculation with new scenario
        else:
             print("Warning: CHANGE_SCENARIO message missing 'scenario_name' or 'is_static'.")

    # Command for updating a users restrictions.
    elif message_type == 'CHANGE_RESTRICTIONS':
        if isinstance(payload, list):
             print("UI Request: Changing restrictions.")
             table.change_restrictions(changes=payload)
             # Notify other clients of changes made
             response = {
                 "type": "RESTRICTIONS_UPDATE",
                 "payload": payload
             }
             mqtt_gui.mqtt_publish(json.dumps(response))
             # Do restrictions change require recalculation? Assume yes for now.
             force_update = True
        else:
             print("Warning: CHANGE_RESTRICTIONS payload was not a list.")


    # Command for sending network snapshots of total generation and consumption.
    elif message_type == 'SEND_SNAPSHOTS':
        print("UI Request: Sending snapshots.")
        response = table.get_snapshot_response_gui()
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending all line statuses.
    elif message_type == 'SEND_LINE_STATUSES':
        print("UI Request: Sending line statuses.")
        response_dict = {
            "type": "LINE_UPDATE",
            "payload": [] # Array of line states
        }
        sections_num = len(line_remap_gui)
        for section_id in range(sections_num):
            if section_id < len(line_remap_gui):
                 # Ensure line_state exists and is a list
                 if hasattr(line_remap_gui[section_id], 'line_state') and isinstance(line_remap_gui[section_id].line_state, list):
                     for line_id_idx, line_active in enumerate(line_remap_gui[section_id].line_state):
                          line_dict = {
                              "table": section_id + 1,
                              "line": line_id_idx, # Use index as line ID for GUI
                              "active": line_active
                          }
                          response_dict["payload"].append(line_dict)
                 else:
                     print(f"Warning: line_state missing or not a list for table index {section_id}.")
            else:
                 print(f"Warning: section_id {section_id} out of bounds for line_remap_gui.")

        mqtt_gui.mqtt_publish(json.dumps(response_dict))

    # Command for changing the state of a line.
    elif message_type == 'CHANGE_LINE':
        table_id_req = payload.get("table")
        line_id_req = payload.get("line") # This is the GUI line index (0-based)
        active_req = payload.get("active")

        if table_id_req is None or line_id_req is None or active_req is None:
             print("Warning: CHANGE_LINE message missing 'table', 'line', or 'active'.")
             return

        table_idx = table_id_req - 1 # Convert GUI table ID (1-based) to 0-based index

        if not (0 <= table_idx < len(line_remap_gui)):
             print(f"Warning: Invalid table index {table_idx} in CHANGE_LINE.")
             return

        # Ensure line_state exists and is a list
        if not (hasattr(line_remap_gui[table_idx], 'line_state') and isinstance(line_remap_gui[table_idx].line_state, list)):
             print(f"Warning: line_state missing or not a list for table index {table_idx}.")
             return

        line_num = len(line_remap_gui[table_idx].line_state)
        if not (0 <= line_id_req < line_num):
             print(f"Warning: Invalid line index {line_id_req} for table {table_idx} in CHANGE_LINE.")
             return

        print(f"UI Request: Setting line {line_id_req} on table {table_id_req} to {active_req}")
        # Update the state in the remap object
        line_remap_gui[table_idx].line_state[line_id_req] = active_req
        # Get the actual lines in the simulation model to update
        # Assuming get_mapped_indices translates GUI line index to simulation line indices
        line_output_indices = line_remap_gui[table_idx].get_mapped_indices(line_id_req)

        if line_output_indices:
            for sim_line_id in line_output_indices:
                # Assuming table_set_line_status uses table_idx (0-based) and sim_line_id
                table.table_set_line_status(table_idx, sim_line_id, active_req)

        # Respond / Broadcast the change back to GUIs
        response = {
            "type": "LINE_UPDATE",
            "payload": [{ # Send update as a list containing the changed item
                    "table": table_id_req,
                    "line": line_id_req,
                    "active": active_req
            }]
        }
        mqtt_gui.mqtt_publish(json.dumps(response))
        force_update = True # Line change requires recalculation

    # --- Handle NEW MQTT messages from Python GUI ---
    elif message_type == 'PLACE_MODULE': # Topic: sgt/command/place
        module_id = payload.get('module_id')
        position = payload.get('position')
        if module_id and position:
            print(f"GUI Request: Simulating placement of '{module_id}' at '{position}'")
            # TODO: Need a method in SmartGridTable or Section to handle simulated placement
            # This likely involves finding the section/platform and calling its _handle_rfid method
            # table.simulate_placement(position, module_id) # Placeholder
            # For now, just acknowledge and force update
            force_update = True
        else:
            print("Warning: PLACE_MODULE message missing 'module_id' or 'position'.")

    elif message_type == 'REMOVE_MODULE': # Topic: sgt/command/remove
        position = payload.get('position')
        if position:
            print(f"GUI Request: Simulating removal from '{position}'")
            # TODO: Need a method in SmartGridTable or Section to handle simulated removal
            # table.simulate_removal(position) # Placeholder
            force_update = True
        else:
            print("Warning: REMOVE_MODULE message missing 'position'.")

    elif message_type == 'LOAD_SCENARIO': # Topic: sgt/command/scenario/load
        scenario_file = payload.get('scenario_file')
        # Assuming static for now based on GUI implementation
        is_static_payload = True # TODO: Make this flexible if GUI supports dynamic
        if scenario_file:
             print(f"GUI Request: Loading scenario '{scenario_file}' (static={is_static_payload})")
             table.scenario_set(scenario_file, is_static_payload)
             table.set_restrictions(is_static_payload) # Update restrictions
             force_update = True
             # Optionally send confirmation back via MQTT? Or rely on status updates?
        else:
            print("Warning: LOAD_SCENARIO message missing 'scenario_file'.")

    else:
         print(f"Warning: Received unknown UI message type from GUI MQTT topic: {message_type}")


def proto_handler(input_data):
    """Handles messages received from the prototype MQTT topic."""
    global force_update # Nodig want we wijzigen deze variabele
    direction = input_data.get('direction')
    module_id = input_data.get('module')
    if direction is not None and module_id is not None:
        table.change_photovoltaic(direction, module_id)
        force_update = True
    else:
         print("Warning: Received proto message missing 'direction' or 'module'.")


def jupyter_handler(input_str):
    """Handles messages received from the Jupyter MQTT topic."""
    global force_update # Nodig want we wijzigen deze variabele
    # Jupyter handler to receive and send information
    console_input = input_str.split()
    print(f"Received from Jupyter: {input_str}") # Log received command
    known_command = False

    if not console_input: return
    command = console_input[0].lower()

    # Reusing console handler logic but publishing results via jupyter.mqtt_publish
    # Note: This duplicates logic from console_handler. Consider refactoring.
    # ... (rest of jupyter handler logic) ...

    if command == "scenario":
        if len(console_input) >= 4 and console_input[1].lower() == "set":
             flag = console_input[2].lower()
             name = console_input[3]
             if flag == "-s": table.scenario_set(name, static=True); force_update=True
             elif flag == "-d": table.scenario_set(name, static=False); force_update=True
             known_command = True
             # Optionally send confirmation or new state back to Jupyter
             jupyter.mqtt_publish(json.dumps({'status': f'Scenario set to {name}'}))


    if not known_command:
         print(f"Jupyter: Unknown command '{input_str}'")
         jupyter.mqtt_publish(json.dumps({'error': f'Unknown command: {input_str}'}))


# --- Main Program Entry Point ---
def application_main(simulation_mode_param=None, simulate_table_connection=None):
    """Main execution function."""
    # === Globale variabelen declareren die binnen deze functie scope worden GEWIJZIGD ===
    global running
    global force_update
    # === Einde declaraties ===

    global simulation_mode # Wordt mogelijk ook gewijzigd
    global global_console_input
    # mode wordt hier alleen gelezen, declaratie niet nodig (wel in console_handler)

    # Override simulation_mode if provided as parameter
    if simulation_mode_param is not None:
        simulation_mode = simulation_mode_param

    # Run initialization
    init()

    # Start console input thread
    console_thread = Thread(target=console_thread_function, daemon=True)
    console_thread.start()

    timer = 0
    force_update = True # Start with an initial calculation

    print("Entering main loop...")
    while(running): # Leest globale 'running'
        try:
            # Main loop logic
            sleep(refresh_rate)

            # --- MQTT Message Handlers ---
            # GUI mqtt message handler (Checkt nu eigen buffer)
            if hasattr(mqtt_gui, 'message_buffer') and mqtt_gui.message_buffer: # Defensive check
                # Probeer JSON te parsen voor berichten van de Python GUI
                messages_to_process = []
                raw_messages = mqtt_gui.message_buffer[:]
                mqtt_gui.message_buffer.clear()

                for raw_msg_str in raw_messages:
                    try:
                        # Check if it's a dict first (already parsed?)
                        if isinstance(raw_msg_str, dict):
                            messages_to_process.append(raw_msg_str)
                        else:
                            # Try parsing as JSON
                            parsed_msg = json.loads(raw_msg_str)
                            messages_to_process.append(parsed_msg)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not parse GUI MQTT message as JSON: {raw_msg_str}")
                        # Handle non-JSON message? Or ignore? For now, ignore.
                    except Exception as e:
                         print(f"Error preparing GUI message for handler: {e}")

                # Verwerk de geparste berichten
                for message in messages_to_process:
                    try:
                        ui_handler(message) # Stuur het geparste dictionary object
                    except Exception as e: print(f"Error in ui_handler: {e}")

            # Prototype mqtt message handler
            if hasattr(prototype_gui, 'message_buffer') and prototype_gui.message_buffer:
                messages = prototype_gui.message_buffer[:]
                prototype_gui.message_buffer.clear()
                for message in messages:
                     try: proto_handler(message) # Assuming this expects dict
                     except Exception as e: print(f"Error in proto_handler: {e}")

            # Jupyter mqtt message handler
            if hasattr(jupyter, 'message_buffer') and jupyter.message_buffer:
                messages = jupyter.message_buffer[:]
                jupyter.message_buffer.clear()
                for message in messages:
                    # Jupyter handler verwacht een string, geen dict
                    try: jupyter_handler(str(message))
                    except Exception as e: print(f"Error in jupyter_handler: {e}")

            # --- Console Input Handler ---
            if global_console_input:
                input_cmd = global_console_input
                global_console_input = "" # Clear immediately
                try: console_handler(input_cmd)
                except Exception as e: print(f"Error in console_handler: {e}")


            # --- Dynamic Scenario Update ---
            table.append_delta_time(refresh_rate)
            table.update()

            timer += refresh_rate # Timer voor eventuele periodieke taken

            # --- Calculation Logic Trigger ---
            recalculate = False
            calc_reason = ""

            if force_update:
                recalculate = True
                calc_reason = "Forced update requested"
                force_update = False # Reset flag
            elif table.modules_if_changed():
                 recalculate = True
                 calc_reason = "Module change detected"

            if recalculate:
                print(f"Recalculating simulation ({calc_reason}) using Pandapower...")
                # Zorg dat de huidige mode correct is doorgegeven aan 'table'
                # via console_handler of ui_handler
                # table.set_calculation_method(mode) # Gebeurt al in handlers

                if calc_reason == "Module change detected":
                    table.selective_calculate() # Calls ModelProcessor -> ThreadManager -> PandapowerCalculator
                else:
                    table.force_calculate()     # Calls ModelProcessor -> ThreadManager -> PandapowerCalculator

                # Send updates after calculation
                if table.get_simulation_succes():
                    print("Calculation complete.")
                    # Stuur snapshot data naar GUI
                    ui_handler({'type': 'SEND_SNAPSHOTS'})
                    # Stuur module updates naar GUI (check of dit nodig is of al via table updates gaat)
                    # ui_handler({'type': 'SEND_ACTIVE_MODULES'}) # Deze is dubbelop?
                else:
                    print("Calculation failed. Check logs.")
                print("────────────────────────────────────────────────────────────────")

            # --- LED Update Logic ---
            if table.get_lep_update_flag(): # Gebruik getter functie
                table.reset_led_update_flag()
                current_snapshot_index = 0 # TODO: Haal correcte index op
                table.update_ledstrips(current_snapshot_index)
                table.mqtt_selective_publish() # Send LED updates


        except KeyboardInterrupt:
             print("\nCtrl+C detected. Shutting down...")
             running = False # Signal shutdown (global is al gedeclareerd)

    # --- Shutdown Sequence ---
    print("Exited main loop. Starting shutdown sequence...")
    if table.get_local_setup() and udp_broadcaster:
        print("Stopping UDP broadcaster...")
        udp_broadcaster.stop_broadcasting()

    print("Disconnecting MQTT clients...")
    table.mqtt_disconnect()
    mqtt_gui.mqtt_disconnect()
    prototype_gui.mqtt_disconnect()
    jupyter.mqtt_disconnect()

    print("Shutting down table simulation...")
    table.shutdown() # Graceful shutdown (ModelProcessor -> ThreadManager)

    print("Waiting for console thread to finish...")
    console_thread.join(timeout=1.0)

    print("────────────────────────────────────────────────────────────────")
    print("───────────────── Goodbye, until next time! ────────────────────")
    print("────────────────────────────────────────────────────────────────")

# --- Entry Point ---
if __name__ == "__main__":
    # Check if the script is run with --simulation flag
    is_simulation = "--simulation" in sys.argv
    # Pass the flag to the main function
    application_main(simulation_mode_param=is_simulation)