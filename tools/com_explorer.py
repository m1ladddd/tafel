##
# @file com_explorer.py
#
# @brief # Reads and displays the output messaging from the simualtion server
#
# @version 0.1
# @date 15-10-2023
##

## Internal imports
from src.networking.Decoder import Decoder
from src.Opcodes import OPCODE_SERVER

## External imports
import paho.mqtt.client as mqtt
import numpy as np

# Define MQTT broker settings
broker_address = "127.0.0.1"
broker_port = 1883
topic = "SmartDemoTable2"
tile = "Table3"

sub_topic = topic + "/" + tile +"/Ingoing"

print("STARTING DEBUG SESSION")
print("Topic: " + topic) 
print("Table: " + tile) 

# Create MQTT client instance and set callback function
client = mqtt.Client()

# Define callback function for handling incoming messages
def on_message(client, userdata, message):

    print("──────── START MQTT MESSAGE ────────")

    # Convert to numpy array
    buffer = np.frombuffer(message.payload, dtype=np.uint8)

    decoder = Decoder(buffer, 0)

    # Read message header
    opcode = decoder.read_UINT8()
    version = decoder.read_UINT8()

    print("Size: " + str(len(buffer)) + " bytes")
    print("Opcode: " + str(OPCODE_SERVER(opcode).name))  
    print("Protocol: " + str(version))

    # Prints LED flow update table
    if (opcode == OPCODE_SERVER.LED_POWER_FLOW.value):

        led_count = decoder.read_UINT8()
        print(f"┌───┬────┬────┬────┬────┬───────┬─────┐")
        print(f"│ID │R   │G   │B   │A   │SPEED  │DIR  │")
        print(f"├───┼────┼────┼────┼────┼───────┼─────┤")

        for i in range(0, led_count):
            id = decoder.read_UINT8()
            red = decoder.read_UINT8()
            green = decoder.read_UINT8()
            blue = decoder.read_UINT8()
            alpha = decoder.read_UINT8()
            direction = decoder.read_UINT8()
            speed = decoder.read_UINT16()
            print(f"│{id:02d} │{red:03d} │{green:03d} │{blue:03d} │{alpha:03d} │{speed:04d}   │{direction:01d}    │")

        print(f"└───┴────┴────┴────┴────┴───────┴─────┘")

    # Prints LED background color table
    if (opcode == OPCODE_SERVER.LED_BACKGROUND.value):

        led_count = decoder.read_UINT8()
        print(f"┌───┬────┬────┬────┬───────┐")
        print(f"│ID │R   │G   │B   │SPEED  │")
        print(f"├───┼────┼────┼────┼───────┤")

        for i in range(0, led_count):
            id = decoder.read_UINT8()
            red = decoder.read_UINT8()
            green = decoder.read_UINT8()
            blue = decoder.read_UINT8()
            flashing_speed = decoder.read_UINT16()

            print(f"│{id:02d} │{red:03d} │{green:03d} │{blue:03d} │{flashing_speed:04d}   │")

        print(f"└───┴────┴────┴────┴───────┘")

    print("────────────────────────────────────")

client.on_message = on_message
client.connect(broker_address, broker_port)
client.subscribe(sub_topic)

# Start the MQTT client loop to begin listening for messages
client.loop_forever()

