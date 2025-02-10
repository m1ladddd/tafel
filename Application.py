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
import json
import warnings
import socket
from time import sleep
from threading import Thread
from src.SmartGridTable import SmartGridTable
from src.networking.UDPBroadcaster import UDPBroadcaster
from src.GUI_MQTT import GUI_MQTT
from src.Prototype_MQTT import Prototype_MQTT
from src.Jupyter_Prototype_Mqtt import Jupyter_MQTT
from src.IndexRemap import IndexRemap

# We take the local ip address and put it as local broker.
# (the broker server need to run on the same computer than the one executing the code).
## Socket used to retrieve local IP.
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))

## Local IP of the computer executing the program.
local_broker_ip = s.getsockname()[0]
mqtt_public_broker = "localhost"
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
    global running

    while(running):
        try:    
            global_console_input = input()
        except EOFError as e:
            break
        if (global_console_input == "shutdown"):
            break


udp_broadcaster: UDPBroadcaster = UDPBroadcaster()

def init():
    """! 
    Initialize the program.
    """

    if (table.get_local_setup()):

        ## Load the GUI LED remapping objects
        for i in range(6):
            line_remap_gui.append(IndexRemap())

        line_remap_gui[0].load("configuration/gui_line_remap/gui_remap_table1.json")
        line_remap_gui[1].load("configuration/gui_line_remap/gui_remap_table2.json")
        line_remap_gui[2].load("configuration/gui_line_remap/gui_remap_table3.json")
        line_remap_gui[3].load("configuration/gui_line_remap/gui_remap_table4.json")
        line_remap_gui[4].load("configuration/gui_line_remap/gui_remap_table5.json")
        line_remap_gui[5].load("configuration/gui_line_remap/gui_remap_table6.json")

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
        udp_broadcaster.set_message(message.encode('UTF─8'))
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

    while(table.mqtt_is_connected() == False):
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

    while(table.table_is_online() == False and timeout == False):
        sleep(refresh_rate)
        timer += refresh_rate
        if (timer >= timer_limit):
            time_left = timeout_limit - timer_limit
            print("Timeout in [" + str(time_left) + "] seconds...")
            timer_limit = timer_limit + 1.0
        if (timer >= timeout_limit):
            print("Timeout when trying to connect...")
            timeout = True

    print("────────────────────────────────────────────────────────────────")
    print("────────────── Retrieving SmartGridTable Modules ───────────────")
    print("────────────────────────────────────────────────────────────────")

    udp_broadcaster.set_interval(1)
    
    table.table_retrieve_modules()

    timer = 0
    timeout_limit = 3.0
    timeout = False

    while(table.table_is_rfid_online() == False and timeout == False):
        sleep(refresh_rate)
        timer += refresh_rate
        if (timer >= timeout_limit):
            timeout = True

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
    print("────────────────────────────────────────────────────────────────")


def console_handler(input):
    """! 
    Converts input strings into actions 
    @param input (str) The console string given by the user
    """

    global force_update
    global mode
    global running
    console_input = input.split()
    known_command = False

    if (len(console_input) >= 1):

        # global commands
        if (console_input[0] == "help"):
            print_help_commands()
            known_command = True
        if(console_input[0]=="transformer_capacity"):
            transformer_df, capacity_df = table.transformer_capacity()
            print(transformer_df)
            print(capacity_df)
            known_command=True
        if(console_input[0]=="module"):
            if(len(console_input)>=2):
                #table.get_table_section_module_all(console_input[1])
                print(table.get_table_section_module_generation(console_input[1]))
                known_command=True
        if(console_input[0]=="run"):
            print(table.start_running())
            known_command=True
        if(console_input[0]=="summation"):
            print(table.get_full_grid_sum_generation_loads_storage())
            known_command=True
        if(console_input[0]=="stop"):
            table.stop_running()
            known_command=True
        if(console_input[0]=="index"):
            if(len(console_input)>=2):
                table.set_index(console_input[1])
                known_command=True
        if(console_input[0]=="photo"):
            if(len(console_input)>=3):
                table.change_photovoltaic(console_input[1],console_input[2])
                known_command=True
                force_update = True
        if(console_input[0]=="tablesection"):
            if(len(console_input)>=2):
                print(table.get_table_sum(console_input[1]))
                known_command=True
        if(console_input[0]=="voltage"):
            if(len(console_input)>=2):
                print(table.get_voltage_sum(console_input[1]))
                known_command=True
        if (console_input[0] == "shutdown"):
            print("Shutting down program...")
            running = False
            known_command = True

        if (console_input[0] == "calculate"):
            print("Forcing simulation update...")
            force_update = True
            known_command = True

        if (console_input[0] == "modules"):
            if (len(console_input) >= 2):
                if (console_input[1] == "list"):
                    table.modules_print_status()
                    known_command = True
                    print("────────────────────────────────────────────────────────────────")

        # table commands
        if (console_input[0] == "table"):
            if (len(console_input) >= 2):
                if (console_input[1] == "list"):
                    table.table_print_list()
                    known_command = True
                    print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "update"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "firmware"):
                            print("Updating all table tiles to the latest firmware")
                            table.table_update_firmware_all()
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")
                        if (console_input[2] == "config"):
                            print("Updating all table tiles to the latest config settings")
                            table.table_update_config_all()
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")
                            
                if (console_input[1] == "reboot"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "all"):
                            print("Restarting all table sections...")
                            table.table_reboot_all()
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")
                        else:
                            print("Restarting section ─> " + console_input[2])
                            table.table_reboot(console_input[2])
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "shutdown"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "all"):
                            print("Shutting down all table sections...")
                            table.mqtt_disconnect()
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")
                        else:
                            print("Shutting down section ─> " + console_input[2])
                            table.table_shutdown(console_input[2])
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "poweron"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "all"):
                            print("Activating all table sections...")
                            table.mqtt_connect()
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")
                        else:
                            print("Activating section ─> " + console_input[2])
                            table.table_poweron(console_input[2])
                            known_command = True
                            print("────────────────────────────────────────────────────────────────")

        # scenario commands
        if (console_input[0] == "scenario"):
            if (len(console_input) >= 2):
                if (console_input[1] == "reload"):
                    print("Reloading scenarios...")
                    table.scenario_refresh_list()
                    known_command = True
                    print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "list"):
                    table.scenario_print_list()
                    known_command = True
                    print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "current"):
                    table.scenario_print_current()
                    known_command = True
                    print("────────────────────────────────────────────────────────────────")

                if (console_input[1] == "set"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "-s"):
                            if (len(console_input) >= 4):
                                table.scenario_set(console_input[3], static=True)
                                force_update = True
                                known_command = True
                                print("────────────────────────────────────────────────────────────────")

                        if (console_input[2] == "-d"):
                            if (len(console_input) >= 4):
                                table.scenario_set(console_input[3], static=False)
                                force_update = True
                                known_command = True
                                print("────────────────────────────────────────────────────────────────")

        # mode commands
        if (console_input[0] == "mode"):
            if (len(console_input) >= 2):
                if (console_input[1] == "set"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "optimize"):
                            print("Setting mode to the Optimize power flow method")
                            mode = "optimize"
                            known_command = True
                            force_update = True

                        if (console_input[2] == "lopf"):
                            print("Setting mode to Linear Optimal Power Flow (LOPF)")
                            mode = "lopf"
                            known_command = True
                            force_update = True

                        if (console_input[2] == "lpf"):
                            print("Setting mode to Linear Power Flow (LPF)")
                            mode = "lpf"
                            known_command = True
                            force_update = True

                        if (console_input[2] == "pf"):
                            print("Setting mode to Power Flow (PF)")
                            mode = "pf"
                            known_command = True
                            force_update = True

        if (known_command == False):
            print("Unknown command ─> " + input)
            print("Type help for all available commands")


def ui_handler(input):

    global force_update

    # Command for sending complete scenario catalog.
    if input['type'] == 'SEND_SCENARIO_JSON':
        response = {
            'type': 'SCENARIO_JSON', 
            'payload': {
                "scenario_json": table.get_referenceless_catalog(), 
                "is_static": table.get_scenario_type()
            }
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending complete restrictions object.
    if input['type'] == 'SEND_RESTRICTIONS':
        rest = table.get_current_restrictions()
        response = {
            'type': 'RESTRICTIONS_JSON', 
            'payload': rest
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for changing module properties.
    if input['type'] == 'CHANGE_MODULE_PARAMETER':
        updates = {}

        # Update copy of catalog.
        catalog = table.get_referenceless_catalog()
        for id, value in input['payload'].items():
            catalog[id] = value
            updates.update({id:value})

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
    if input['type'] == 'SEND_ACTIVE_MODULES':
        table.table_retrieve_modules()

        # Command for sending the list of available scenarios.
    if input['type'] == 'SEND_SCENARIO_LIST':
        scenario_list = table.get_scenario_list(isStatic=input['payload']['is_static'])
        response = {
            "type": "SCENARIO_LIST", 
            "payload": {
                "scenario_list": scenario_list, 
                "is_static": input['payload']['is_static']
            }
        }

        mqtt_gui.mqtt_publish(json.dumps(response))
    
    # Command for changing the selected scenario.
    if input['type'] == 'CHANGE_SCENARIO':
        table.scenario_set(input['payload']['scenario_name'], input['payload']['is_static'])
        table.set_restrictions(input['payload']['is_static'])
    
        response = {
            'type': 'SCENARIO_JSON', 
            'payload': {
                "scenario_json": table.get_referenceless_catalog(), 
                "is_static": table.get_scenario_type()
            }
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

        response = {'type': 'RESTRICTIONS_JSON', 'payload': table.get_current_restrictions()}
        mqtt_gui.mqtt_publish(json.dumps(response))

        force_update = True

    # Command for updating a users restrictions.
    if input['type'] == 'CHANGE_RESTRICTIONS':
        table.change_restrictions(changes = input['payload'])
        
        # Notify other clients of changes made
        response = {
            "type": "RESTRICTIONS_UPDATE", 
            "payload": input['payload']
        }
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending network snapshots of total generation and consumption.
    if input['type'] == 'SEND_SNAPSHOTS':
        response = table.get_snapshot_response_gui()
        mqtt_gui.mqtt_publish(json.dumps(response))

    # Command for sending all line statuses.
    if input['type'] == 'SEND_LINE_STATUSES':

        response_dict = {
            "type": "LINE_UPDATE",
            "payload": [] # Array of line states
        }

        sections_num: int = len(line_remap_gui)

        for section_id in range(sections_num):
            for line_id in range(len(line_remap_gui[section_id].line_state)):
                line_active: bool = line_remap_gui[section_id].line_state[line_id]
                line_dict = {
                    "table": section_id + 1,
                    "line": line_id,
                    "active": line_active
                }
                response_dict["payload"].append(line_dict)

        mqtt_gui.mqtt_publish(json.dumps(response_dict))

    # Command for changing the state of a line.
    if input['type'] == 'CHANGE_LINE':
        table_id: int = input['payload']["table"] - 1
        line_id: int = input['payload']["line"]
        active: bool = input['payload']["active"]

        sections_num: int = len(line_remap_gui)

        if (table_id >= sections_num):
            return
        
        line_num: int = len(line_remap_gui[table_id].line_state)

        if (line_id >= line_num):
            return
        
        line_remap_gui[table_id].line_state[line_id] = active
        line_output = line_remap_gui[table_id].get_mapped_indices(line_id)

        for line_id in line_output:
            table.table_set_line_status(table_id, line_id, active)

        response = {
            "type": "LINE_UPDATE",
            "payload": [input['payload']]
        }

        # Response
        mqtt_gui.mqtt_publish(json.dumps(response))
        force_update = True

def proto_handler(input):
    #Pv prototype handler
    global force_update
    table.change_photovoltaic(input['direction'],input['module'])
    force_update = True

def jupyter_handler(input):
    #Jupyter handler to receive and send information
    console_input = input.split()
    print(input)
    known_command = False
    if(console_input[0]=="tablesection"):
            if(len(console_input)>=2):
                df2=table.get_table_sum(console_input[1])
                if(df2 is not  None):
                    jupyter.mqtt_publish(df2.to_json())
    if(console_input[0]=="voltage"):
            if(len(console_input)>=2):
                df1=table.get_voltage_sum(console_input[1])
                jupyter.mqtt_publish(df1.to_json())
    if(console_input[0]=="transformer"):
            df1=table.transformer_capacity()
            jupyter.mqtt_publish(df1.to_json())
    if(console_input[0]=="summation"):
            df1=table.get_full_grid_sum_generation_loads_storage()
            jupyter.mqtt_publish(df1.to_json())
    if(console_input[0]=="index"):
            if(len(console_input)>=2):
                table.set_index(console_input[1])
                known_command=True
    if(console_input[0]=="stop"):
            table.stop_running()
            known_command=True
    if(console_input[0]=="module"):
            if(len(console_input)>=3):
                if(console_input[1]=='generation'):
                    df1=table.get_table_section_module_generation(console_input[2])
                    print(df1)
                    if(df1 is not None):
                        jupyter.mqtt_publish(df1.to_json())
                if(console_input[1]=='load'):
                    df1=table.get_table_section_module_load(console_input[2])
                    print(df1)
                    if(df1 is not None):
                        jupyter.mqtt_publish(df1.to_json())
                if(console_input[1]=='storage'):
                    df1=table.get_table_section_module_storage(console_input[2])
                    print(df1)
                    if(df1 is not None):
                        jupyter.mqtt_publish(df1.to_json())
                known_command=True
    if (console_input[0] == "scenario"):
            if (len(console_input) >= 2):
                if (console_input[1] == "reload"):
                    print("Reloading scenarios...")
                    table.scenario_refresh_list()
                    known_command = True
                    print("----------------------------------------------------------------")

                if (console_input[1] == "list"):
                    table.scenario_print_list()
                    known_command = True
                    print("----------------------------------------------------------------")

                if (console_input[1] == "current"):
                    table.scenario_print_current()
                    known_command = True
                    print("----------------------------------------------------------------")

                if (console_input[1] == "set"):
                    if (len(console_input) >= 3):
                        if (console_input[2] == "-s"):
                            if (len(console_input) >= 4):
                                table.scenario_set(console_input[3], static=True)
                                known_command = True
                                print("----------------------------------------------------------------")

                        if (console_input[2] == "-d"):
                            if (len(console_input) >= 4):
                                table.scenario_set(console_input[3], static=False)
                                known_command = True
                                print("----------------------------------------------------------------")
       

# Main routine
init()

# seperate thread so table routine keeps running during keyboard input
# (keyboard input stalls main thread)
console_thread = Thread(target=console_thread_function)
console_thread.start()

timer = 0
force_update = True

while(running):

    sleep(refresh_rate)

    # GUI mqtt message handler
    if (len(mqtt_gui.message_buffer) > 0):
        for message in mqtt_gui.message_buffer:
            ui_handler(message)
        mqtt_gui.message_buffer.clear()

    if (len(prototype_gui.message_buffer) > 0):
        for message in prototype_gui.message_buffer:
            proto_handler(message)
        prototype_gui.message_buffer.clear()

    if (len(jupyter.message_buffer) > 0):
        for message in jupyter.message_buffer:
            jupyter_handler(message)
        jupyter.message_buffer.clear()

    # Console input message handler
    if (global_console_input != ""):
        console_handler(global_console_input)
        global_console_input  = ""

    # Update elapsed time for table instance
    table.append_delta_time(refresh_rate)
    table.update()

    timer = timer + refresh_rate

    if(force_update):
        force_update = False
        timer = 0

        table.simulation_changed = True

        if (mode == "optimize" or mode == "lopf" or mode == "lpf" or mode == "pf"):
            table.set_calculation_method(mode)
            
        table.force_calculate()
        ui_handler({'type': 'SEND_SNAPSHOTS'})
        print("────────────────────────────────────────────────────────────────")

    if(table.modules_if_changed()):
        timer = 0            
        table.set_calculation_method(mode)
        table.selective_calculate()
        print("────────────────────────────────────────────────────────────────")

        ui_handler({'type': 'SEND_SNAPSHOTS'})
        
    if (table.get_lep_update_flag()):
        table.reset_led_update_flag()
        table.update_ledstrips(0)
        table.mqtt_selective_publish()

    if (table.simulation_changed == True):
        table.simulation_changed = False

        changes = table.get_module_changes()
        table.empty_module_change_buffer()

        for change in changes:
            table_section = change["table_section"]
            modules = change["buffer"]
            for module in modules:
                message = {"type": "MODULE_UPDATE", "payload": {"table_section": table_section, **module}}
                mqtt_gui.mqtt_publish(json.dumps(message))


# on program shutdown
if (table.get_local_setup()):
    udp_broadcaster.stop_broadcasting()

console_thread.join()

table.mqtt_disconnect()
table.shutdown()

print("────────────────────────────────────────────────────────────────")
print("───────────────── Goodbye, until next time! ────────────────────")
print("────────────────────────────────────────────────────────────────")
