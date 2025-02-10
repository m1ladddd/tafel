##
# @file Section.py
#
# @brief The base of all table sections
# This class controls the MQTT connections and message handlers
#
# @section libraries_Section Libraries/Modules
# - 
#
# @section todo_Section TODO
# - None
#
# @section author_Section Author(s)
# - Created by Thijs van Elsacker on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.model.Model import Model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.StorageUnit import StorageUnit
from src.model.components.Transformer import Transformer
from src.Platform import Platform
from src.MQTTConfig import MQTTConfig
from src.Module import Module
from src.led.LEDDatatype import RBGColor
from src.led.LEDStrip import LEDStrip, compare_led_background, compare_led_power_flow
from src.networking.Decoder import Decoder
from src.networking.Encoder import Encoder
from src.Opcodes import OPCODE_SERVER, OPCODE_TABLE

# External imports
from threading import Lock
from time import perf_counter
from copy import deepcopy
import paho.mqtt.client as mqtt
import numpy as np

class Section:
    """! 
    Objects of this class represents Medium Voltage table sections (industry with factories).
    All platforms on this section only accepts MV modules.
    """

    ## Static string which indicates the voltage level of this section (LV, MV or HV).
    voltage = ""

    def __init__(self, section_name):
        """! 
        Constructor.
        @param section_name (str) String name of this table section.
        """

        ## String name of this table section.
        self.name: str = section_name

        ## String prefix used for unique name generation in PyPSA components (for example "Table1_Line12").
        self.__prefix: str = section_name + "_"

        ## MQTT client object using paho-mqtt libary.
        self.__mqtt_client: mqtt.Client = mqtt.Client()

        ## MQTT broker to connect to.
        self.__mqtt_config: MQTTConfig = MQTTConfig()

        ## MQTT base topic to subscribe and publish to.
        self.__mqtt_base_topic: str = "SmartDemoTable2"

        ## MQTT subscribe topic string.
        self.__mqtt_subscribe: str = self.__mqtt_base_topic + "/" + self.name + "/Outgoing"

        ## MQTT publish topic string.
        self.__mqtt_publish: str = self.__mqtt_base_topic + "/" + self.name + "/Ingoing"

        ## Threading lock which prevents reading and writing component data at the same time.
        self.__mqtt_read_lock: Lock = Lock()

        ## PIng command send time, used to calculate microcontroller response time
        self.__mqtt_ping_start: float = 0.0

        ## MQTT response time of this table section
        self.__mqtt_ping: float = 0.0

        ## Power grid model of this table section.
        self.model: Model = Model()

        ## Array of Ledstrip objects present in this table section.
        self.ledstrips: list[LEDStrip] = []

        ## Array of Ledstrip objects present in this table section.
        self._previous_ledstrips: list[LEDStrip] = []

        ## Array of Platform objects present in this table section.
        self.platforms: list[Platform] = []

        ## Bool indicating if module place messages should be displayed. (True = print messages, False = no messages).
        self.print_module_messages: bool = False

        ## Event flag trigering a LED update. True if LED strips needs to be updated, False if not
        self.__led_update_flag: bool = False

        ## Current Scenario object to load 3D model values from.
        self.__scenario = None

        ## Bool indicating if MQTT is conencted to the broker.
        self.__mqtt_connected: bool = False

        ## Bool indicating the table section is connected with the simulation server.
        self.__online: bool = False

        ## Bool indicating if the table section has received any rfid upupdate messages.
        self.__rfid_online: bool = False

        ## List of dicts containing rfid and locations of placed modules. This will be used for the GUI application.
        self.__input_buffer = []

        ## Static int indicating critical power level of a power line.
        ## Active power values above this level are considered critical.
        self.threshold_critical: float = 4.0

        ## Static int indicating high power level of a power line.
        ## Active power values above this level are considered high.
        self.threshold_high: float = 3.0

        ## Static int indicating normal power level of a power line.
        ## Active power values above this level are considered normal.
        self.threshold_normal: float = 2.0

        ## Static int indicating low power level of a power line.
        ## Active power values above this level are considered low.
        self.threshold_low: float = 1.0

        ## Color of the LED background
        self.background_color: RBGColor = RBGColor(0xFF, 0xFF, 0xFF)


    def set_scenario(self, scenario):
        """! 
        Give scenario object to which this table section will load its 3D module values from.
        @param scenario Scenario instance to reference to.
        """
        self.__scenario = scenario


    def reload_modules(self):
        """! 
        Loops trough all platforms and checks if a module has been placed.
        If a module has been placed, load it into this table section module array.
        """
        self.__mqtt_read_lock.acquire()

        for platform in self.platforms:
            rfid_tag = platform.RFID_tag
            platform.clear_module()
            module = None
            if (rfid_tag != "0"):
                module = self.__scenario.get_module(rfid_tag)            
            if (module):
                platform.add_module(module)

        self.__mqtt_read_lock.release()


    def reset_changed(self):
        """! 
        Resets the platform changed flag.
        """
        for platform in self.platforms:
            platform.reset_changed()


    def has_changed(self):
        """! 
        Returns if modules are placed or removed.
        @return Bool (True = module are placed or removed, False = no change).
        """
        for platform in self.platforms:
            if (platform.has_changed()):
                return True
        return False
    

    def get_led_update_flag(self) -> bool:
        """! 
        Returns a bool indicating if an LED update is required
        @return Bool (True = LED update requested).
        """
        return self.__led_update_flag


    def reset_led_update_flag(self) -> None:
        """! 
        Clears the LED update flag
        """
        self.__led_update_flag = False


    def get_led_update_flag(self) -> bool:
        """! 
        Returns a bool indicating if an LED update is required
        @return Bool (True = LED update requested).
        """
        return self.__led_update_flag


    def reset_led_update_flag(self) -> None:
        """! 
        Clears the LED update flag
        """
        self.__led_update_flag = False


    def add_line(self, name: str, bus0: str, bus1: str, x: float, r: float, s_nom: float,type: str, length:float ):
        """! 
        Add a Line object to this table section.
        @param name (str) Unique line name for PyPSA.
        @param bus0 (str) Start point of the line connection. 
        @param bus1 (str) End point of the line connection. 
        @param x (float) Series reactance, must be non-zero for AC branch in linear power flow. 
        @param r (float) Series resistance, must be non-zero for DC branch in linear power flow. 
        @param s_nom is the maximum capacity of the energy throughput that a line can have
        """
        self.model.add_line(Line(self.__prefix+name, bus0=self.__prefix+bus0, bus1=self.__prefix+bus1, x=x, r=r, s_nom=s_nom, type=type, length=length))


    def add_bus(self, name, v_nom):
        """! 
        Add a Bus object to this table section.
        @param name (str) Unique bus name for PyPSA.
        @param v_nom (float) Nominal voltage of the bus.
        """
        self.model.add_bus(Bus(self.__prefix + name, v_nom=v_nom))


    def add_platform(self, bus: str, voltage: str, rfid_location: str, error_lines, rfid_tags):
        """! 
        Add a Platform object to this table section.
        @param bus (str) Bus name connected to this platform.
        @param voltage (str) Voltage level of the platform (LV, MV or HV).
        @param rfid_location (str) Unique identifier of the platform (rfid 1, rfid 2, etc).
        @param error_lines (int[]) Array of line indexes used to indicate wrongly placed modules.
        @param rfid_tags (str[]) Array of component type strings used to indicate which components.
        can be placed on this platform (for example ["Transformer", "Load"]).
        """
        self.platforms.append(Platform(bus, voltage, rfid_location, error_lines, rfid_tags))


    def reload_model(self):
        """! 
        Refresh the component list of this table section.
        The components will be loaded depending which 3D objects are placed on the platforms.
        """
        
        ## Clear previous components.
        self.model.generators.clear()
        self.model.loads.clear()
        self.model.storage_units.clear()
        self.model.transformers.clear()

        ## Set MQTT write lock
        self.__mqtt_read_lock.acquire()

        ## Load in components from all platforms.
        for platform in self.platforms:
            for component in platform.components:
                if(isinstance(component, Transformer)):
                    self.model.add_transformer(component)
                if(isinstance(component, Generator)):
                    self.model.add_generator(component)
                if(isinstance(component, Load)):
                    self.model.add_load(component)
                if(isinstance(component, StorageUnit)):
                    self.model.add_storage_unit(component)

        ## Release MQTT write lock
        self.__mqtt_read_lock.release()


    def section_is_online(self):
        """! 
        Return if the table section responds to messages.
        @return Bool (True = table section is online, False = offline).
        """
        return self.__online
    

    def section_is_rfid_online(self):
        """! 
        Return if the table section responds to messages.
        @return Bool (True = table section is online, False = offline).
        """
        return self.__rfid_online


    def print_module_status(self):
        """! 
        Print how many modules are placed and how many platforms are present on this table section.
        """
        num_of_platforms = len(self.platforms)
        num_of_modules = 0
        for platform in self.platforms:
            if (platform.module):
                num_of_modules = num_of_modules + 1
        print(self.name + ": Modules -> " + str(num_of_modules) + " / " + str(num_of_platforms))


    def mqtt_set_config(self, config_instance: MQTTConfig):
        """! 
        Set the MQTT broker of this table section.
        @param broker (str) String containing a IP address or hostname of the MQTT broker.
        """
        self.__mqtt_config = config_instance
       

    def mqtt_set_base_topic(self, topic: str):
        """! 
        Set the MQTT base topic of this table section.
        @param topic (str) String with the MQTT base topic.
        """
        self.__mqtt_base_topic = topic
        self.__mqtt_subscribe = self.__mqtt_base_topic + "/" + self.name + "/Outgoing"
        self.__mqtt_publish = self.__mqtt_base_topic + "/" + self.name + "/Ingoing"


    def mqtt_is_connected(self):
        """! 
        Return if this table section MQTT service is connected to the broker.
        @return Bool (True = MQTT is connected, False = not conencted).
        """
        return self.__mqtt_connected


    def reboot_section(self):
        """! 
        Send a reboot command to the table section. This will reboot the microcontrollers.
        """
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.REBOOT.value)
        encoder.write_UINT8(0)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))


    def send_ping(self):
        """! 
        Send a ping command to the table section.
        If the hardware is online, it should return a "Table connected" message
        """
        self.__mqtt_ping_start = perf_counter()
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.PING.value)
        encoder.write_UINT8(0)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer), qos=2)


    def send_firmware_update_command(self):
        """! 
        Forces the table section to update its firmware.
        This affects both the Boss and Helper EPS32 microcontrollers.
        """
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.FIRMWARE_UPDATE.value)
        encoder.write_UINT8(0)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer), qos=2)


    def send_config_update_command(self):
        """! 
        Forces the table section to update its config file.
        This affects both the Boss and Helper EPS32 microcontrollers.
        """
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.CONFIG_UPDATE.value)
        encoder.write_UINT8(0)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer), qos=2)


    def mqtt_connect(self):
        """! 
        Let the MQTT client connect to the broker.
        """
        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message
        if (self.__mqtt_connected == False):
            self.__mqtt_client.username_pw_set(None, None)
            if (self.__mqtt_config.get_auth_mode() == True):
                self.__mqtt_client.username_pw_set(self.__mqtt_config.get_auth_user(), self.__mqtt_config.get_auth_password())
            self.__mqtt_client.connect(self.__mqtt_config.get_address(), self.__mqtt_config.get_port())
            self.__mqtt_client.loop_start()


    def mqtt_disconnect(self):
        """! 
        Disconnect the MQTT connection with the broker.
        """
        print(self.name + ": Closing MQTT Client")
        if (self.__mqtt_connected == True):
            self.__mqtt_client.loop_stop()
            self.__mqtt_connected = False


    def mqtt_update_force_power_flow(self) -> None:
        """
        Force send all power flow values to the Smart Grid Table.
        """  
        # Send all power flow ledstrips.
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.LED_POWER_FLOW.value)
        encoder.write_UINT8(0)
        encoder.write_UINT8(len(self.ledstrips))
        for ledstrip in self.ledstrips:
            encoder.write_UINT8(ledstrip.id)
            encoder.write_UINT8(ledstrip.flow_color.red)
            encoder.write_UINT8(ledstrip.flow_color.green)
            encoder.write_UINT8(ledstrip.flow_color.blue)
            encoder.write_UINT8(ledstrip.flow_color.alpha)
            encoder.write_UINT8(ledstrip.flow_direction)
            encoder.write_UINT16(ledstrip.flow_speed)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))

        # Set self.__previous_ledstrips for future mqtt_update_selective_power_flow() calls.
        for i in range(len(self.ledstrips)):
            self._previous_ledstrips[i].flow_color = deepcopy(self.ledstrips[i].flow_color)
            self._previous_ledstrips[i].flow_speed = deepcopy(self.ledstrips[i].flow_speed)
            self._previous_ledstrips[i].flow_direction = deepcopy(self.ledstrips[i].flow_direction)


    def mqtt_update_selective_power_flow(self) -> None:
        """
        Send all changed power flow values to the Smart Grid Table 
        since the last mqtt_update_selective_power_flow() call.
        """
        # Create a list of changed power flow ledstrips.
        changed_ledstrips: list[LEDStrip] = []

        for i in range(len(self.ledstrips)):
            if (compare_led_power_flow(self.ledstrips[i], self._previous_ledstrips[i])):
                changed_ledstrips.append(self.ledstrips[i])

        # Don't send if there aren't any changes.
        if (len(changed_ledstrips) == 0):
            return

        # Send the changed power flow ledstrips.
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.LED_POWER_FLOW.value)
        encoder.write_UINT8(0)
        encoder.write_UINT8(len(changed_ledstrips))
        for ledstrip in changed_ledstrips:
            encoder.write_UINT8(ledstrip.id)
            encoder.write_UINT8(ledstrip.flow_color.red)
            encoder.write_UINT8(ledstrip.flow_color.green)
            encoder.write_UINT8(ledstrip.flow_color.blue)
            encoder.write_UINT8(ledstrip.flow_color.alpha)
            encoder.write_UINT8(ledstrip.flow_direction)
            encoder.write_UINT16(ledstrip.flow_speed)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))

        # Set self.__previous_ledstrips for future mqtt_update_selective_power_flow() calls.
        for i in range(len(self.ledstrips)):
            self._previous_ledstrips[i].flow_color = deepcopy(self.ledstrips[i].flow_color)
            self._previous_ledstrips[i].flow_speed = deepcopy(self.ledstrips[i].flow_speed)
            self._previous_ledstrips[i].flow_direction = deepcopy(self.ledstrips[i].flow_direction)


    def mqtt_update_force_background(self) -> None:
        """
        Force send all background values to the Smart Grid Table.
        """         
        # Send all ledstrip background values.
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.LED_BACKGROUND.value)
        encoder.write_UINT8(0)
        encoder.write_UINT8(len(self.ledstrips))
        for ledstrip in self.ledstrips:
            encoder.write_UINT8(ledstrip.id)
            encoder.write_UINT8(ledstrip.background_color.red)
            encoder.write_UINT8(ledstrip.background_color.green)
            encoder.write_UINT8(ledstrip.background_color.blue)
            encoder.write_UINT16(ledstrip.background_flashing_speed)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))

        # Set self.__previous_ledstrips for future mqtt_update_selective_background() calls.
        for i in range(len(self.ledstrips)):
            self._previous_ledstrips[i].background_color = deepcopy(self.ledstrips[i].background_color)
            self._previous_ledstrips[i].background_flashing_speed = deepcopy(self.ledstrips[i].background_flashing_speed)


    def mqtt_update_selective_background(self) -> None:
        """
        Send all changed background values to the Smart Grid Table 
        since the last mqtt_update_selective_background() call.
        """
        # Create a list of changed power flow ledstrips.
        changed_ledstrips: list[LEDStrip] = []
        for i in range(len(self.ledstrips)):
            if (compare_led_background(self.ledstrips[i], self._previous_ledstrips[i])):
                changed_ledstrips.append(self.ledstrips[i])

        # Don't send if there aren't any changes.
        if (len(changed_ledstrips) == 0):
            return
        
        # Send changed ledstrip background values.
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.LED_BACKGROUND.value)
        encoder.write_UINT8(0)
        encoder.write_UINT8(len(changed_ledstrips))
        for ledstrip in changed_ledstrips:
            encoder.write_UINT8(ledstrip.id)
            encoder.write_UINT8(ledstrip.background_color.red)
            encoder.write_UINT8(ledstrip.background_color.green)
            encoder.write_UINT8(ledstrip.background_color.blue)
            encoder.write_UINT16(ledstrip.background_flashing_speed)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))

        # Set self.__previous_ledstrips for future mqtt_update_selective_background() calls.
        for i in range(len(self.ledstrips)):
            self._previous_ledstrips[i].background_color = deepcopy(self.ledstrips[i].background_color)
            self._previous_ledstrips[i].background_flashing_speed = deepcopy(self.ledstrips[i].background_flashing_speed)


    def retrieve_modules(self):
        """! 
        Send a message to the table section to send back all placed modules.
        """
        encoder = Encoder()
        encoder.write_UINT8(OPCODE_SERVER.RFID_REQUEST.value)
        encoder.write_UINT8(0)
        self.__mqtt_client.publish(self.__mqtt_publish, bytearray(encoder.buffer))
    

    def add_to_input_buffer(self, rfid, location):
        """!
        Adds element to input buffer.
        Elements will be added once a message is received.
        rfid "0" is used when a module is removed from the table.
        """
        self.__input_buffer.append({"module_location": int(location), "module_id": rfid})
        

    def get_input_buffer(self):
        """!
        Getter function for __input_buffer
        """
        return self.__input_buffer
    
    
    def empty_input_buffer(self):
        self.__input_buffer = []


    def on_connect(self, client, userdata, flags, rc):
        """! 
        MQTT on_connect callback function.
        This method will trigger when the client has connected to the MQTT broker.
        It prints a error if no connection could be made.
        """

        # rc is the error code returned when connecting to the broker
        self.__mqtt_client.subscribe(self.__mqtt_subscribe)
        mqtt_broker = self.__mqtt_config.get_address()

        if(rc != 0):
            print(self.name + ": Error: " + str(rc))
        else:
            self.__mqtt_connected = True
            print(self.name + ": Succesfully subscribed to -> " + self.__mqtt_base_topic + " (" + mqtt_broker + ")")


    def on_message(self, client, userdata, msg):
        """! 
        MQTT on_message callback function.
        This method will trigger when a message has been recieved.
        """

        # From raw bytes to numpy array
        buffer = np.frombuffer(msg.payload, dtype=np.uint8)
        decoder = Decoder(buffer, 0)
        opcode = decoder.read_UINT8()
        version = decoder.read_UINT8()

        # Received a PONG message from the table section.
        if (opcode == OPCODE_TABLE.PONG.value):
            self.__online = True
            self.retrieve_modules()
            self.mqtt_update_force_power_flow()
            self.mqtt_update_force_background()
            if (self.__mqtt_ping_start > 0):
                self.__mqtt_ping = perf_counter() - self.__mqtt_ping_start                    
                print(f"{self.name}: online ({self.__mqtt_ping*1000:0.2f} ms)")

        # Received a ONLINE message from the table section.
        if (opcode == OPCODE_TABLE.ONLINE.value):
            self.__online = True
            self.retrieve_modules()
            self.mqtt_update_force_power_flow()
            self.mqtt_update_force_background()
            print(f"{self.name}: online")

        # Received a rfid update message from the table section
        if (opcode == OPCODE_TABLE.RFID.value):
            self.__online = True
            self.__rfid_online = True
            rfid_update_count = decoder.read_UINT8()
            for i in range(0, rfid_update_count):
                module_location = int(decoder.read_UINT8())
                rfid_tag = str(decoder.read_UINT32())
                platform = None
                for platform_loop in self.platforms:
                    if platform_loop.RFID_location == module_location:
                        platform = platform_loop
                        break

                if (platform != None):                        
                    self.add_to_input_buffer(rfid=rfid_tag, location=module_location)

                    # Module removed
                    if (rfid_tag == "0"):
                        self.__mqtt_read_lock.acquire()
                        platform.clear_module()
                        self.__mqtt_read_lock.release()
                        if (self.print_module_messages):
                            print(self.name + " - Platform " + str(module_location) + " -> Module removed")
                        for errorlines in platform.error_lines:
                            self.ledstrips[errorlines].error = False
                        self.__led_update_flag = True

                    else:
                        module = self.__scenario.get_module(rfid_tag)                            
                        if (module != None):
                            wrong_platform = True
                            for accepted_module in platform.accepted_modules:
                                for component in module.components: 
                                    if (accepted_module == module.RFID_tag):                                        
                                        wrong_platform = False
                                    if (accepted_module == component.type):
                                        wrong_platform = False

                            wrong_voltage = platform.find_voltage(module.voltage)
                            if(wrong_voltage == -1):
                                wrong_platform = True

                            if (wrong_platform):
                                if (self.print_module_messages):
                                    print("Module placed on incorrect platform")
                                    print("    Module       -> " + module.name)
                                    print("    rfid         -> " + rfid_tag)
                                for errorlines in platform.error_lines:
                                    self.ledstrips[errorlines].error = True
                                self.__led_update_flag = True

                            if (not wrong_platform):
                                self.__mqtt_read_lock.acquire()
                                platform.name_prefix = self.__prefix
                                platform.add_module(module)
                                self.__mqtt_read_lock.release()
                                if (self.print_module_messages):
                                    print(self.name + " -> Platform " + str(module_location) + " -> Module placed" )
                                    print("    Module -> " + module.name)
                                    print("    rfid   -> " + rfid_tag)
                        else:
                            if (self.print_module_messages):
                                print(self.name + " - Platform " + str(module_location) + " -> Module not found in catalog: " + rfid_tag)
