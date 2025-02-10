##
# @file GUI_MQTT.py
#
# @brief MQTT client for GUI app communication.
#
# @section libraries_main Libraries/Modules
# - paho.mqtt.client (https://www.eclipse.org/paho/index.php?page=clients/python/docs/index.php)
#  - Access to the mqtt.Client class and its methods
# - json (https://docs.python.org/3/library/json.html)
#  - Access to dumps and loads functions
#
# @section todo_Bus TODO
# - None
#
# @section author_Bus Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

import paho.mqtt.client as mqtt
import json

class GUI_MQTT:
    """! 
    Provides access to the connected MQTT broker sensor.
    This connection manages the communication between this program and the GUI apps.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Client instance from paho.mqtt.client.
        self.__mqtt_client = mqtt.Client()

        ## MQTT broker adres.
        self.__mqtt_broker = None

        ## MQTT base topic.
        self.__mqtt_topic = "SmartDemoTable2/GUI"

        ## Port to use (1883 = default).
        self.__mqtt_port = 1883

        ## MQTT subscribe topic.
        self.__mqtt_subscribe = self.__mqtt_topic + "/Outgoing"

        ## MQTT publish topic.
        self.__mqtt_publish = self.__mqtt_topic + "/Ingoing"

        ## Bool if client is connected (False = not connected, True = connected).
        self.__mqtt_connected = False

        ## Revieved messages, user must manually empty if read.
        self.message_buffer = []



    def mqtt_set_broker(self, broker):
        """! 
        Set the broker of the MQTT connection.
        @param broker (str) IP address or web address.
        """

        self.__mqtt_broker = broker


    def mqtt_set_topic(self, topic):
        """! 
        Set the base topic of the MQTT connection.
        @param topic (str) Root topic.
        """

        self.__mqtt_topic = topic


    def mqtt_set_port(self, port):
        """! 
        Set the port of the MQTT broker.
        @param port (int) Port number.
        """

        self.__mqtt_port = port


    def mqtt_connect(self):
        """! 
        Connect to the MQTT broker.
        """

        self.__mqtt_client.on_connect = self.on_connect
        self.__mqtt_client.on_message = self.on_message

        if (self.__mqtt_connected == False):
            self.__mqtt_client.connect(self.__mqtt_broker, self.__mqtt_port)
            self.__mqtt_client.loop_start()
    


    def mqtt_disconnect(self):
        """! 
        Disconnect the connection.
        """

        if (self.__mqtt_connected == True):
            self.__mqtt_client.loop_stop()
            self.__mqtt_connected = False



    def mqtt_publish(self, message):
        """! 
        Publish a message to the broker and earlier given topic.
        @param message (str) Messages to be published.
        """

        self.__mqtt_client.publish(self.__mqtt_publish, message)


    def publish_snapshot(self, snapshot):
        """! 
        Publish the current snapshot of the PyPSA simulation.
        @param snapshot (int) Current index of the PyPSA simulation.
        """

        raw = {"current_snapshot": str(snapshot)}
        message = json.dumps(raw)
        self.mqtt_publish(message)


    def publish_dataframe(self, dataframe):
        """! 
        Convert a dataframe to JSON format and publish the result.
        @param dataframe Datasframe to be published.
        """

        result = dataframe.to_json()
        parsed = json.loads(result)
        json_string = json.dumps(parsed, indent=4) 
        self.mqtt_publish(json_string)


    def on_connect(self, client, userdata, flags, rc):
        """! 
        MQTT on_connect callback function.
        This method will trigger when the client has connected to the MQTT broker.
        It prints a error if no connection could be made.
        """

        self.__mqtt_client.subscribe(self.__mqtt_subscribe)

        if(rc != 0):
            print("GUI: Error: " + str(rc))
        else:
            self.__mqtt_connected = True
            print("GUI: Succesfully started GUI MQTT client")


    def on_message(self, client, userdata, msg):
        """! 
        MQTT on_message callback function.
        This method will trigger when a message has been recieved.
        The message will be converted to JSON format and appended to self.message_buffer.
        """
        
        message = str(msg.payload.decode("utf-8"))  #removes b'' in string

        try:
            json_message        = json.loads(message)
        except:
            return

        if (json_message):
            self.message_buffer.append(json_message)

