##
# @file virtual_table.py
#
# @brief # Mimics the physical table message protocol and build a optimal network
# Places transformers, generators and loads on the power grid
#
# @version 0.1
# @date 15-10-2023
##

## Internal imports
from src.networking.Encoder import Encoder
from src.Opcodes import OPCODE_TABLE

## External imports
import paho.mqtt.client as mqtt
from time import sleep

# Define MQTT broker settings
broker_address = "localhost"
broker_port = 1883
topic = "SmartDemoTable2"

# Create MQTT client instance and set callback function
client = mqtt.Client()
client.connect(broker_address, broker_port)

table1_payload = Encoder()
table1_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table1_payload.write_UINT8(0)
table1_payload.write_UINT8(3) # 3 RFID tags in this message
table1_payload.write_UINT8(0)
table1_payload.write_UINT32(1071746625) # HV-MV TF1 on platform 0
table1_payload.write_UINT8(1)
table1_payload.write_UINT32(1071771887) # Coal powerplant on platform 1
table1_payload.write_UINT8(3)
table1_payload.write_UINT32(3113060275) # HV-MV TF6 (transformer) on platform 3

table2_payload = Encoder()
table2_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table2_payload.write_UINT8(0)
table2_payload.write_UINT8(0) # 0 RFID tags in this message

table3_payload = Encoder()
table3_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table3_payload.write_UINT8(0)
table3_payload.write_UINT8(3) # 3 RFID tags in this message
table3_payload.write_UINT8(0)
table3_payload.write_UINT32(1071766506) # Solar farm small 2 on platform 0
table3_payload.write_UINT8(5)
table3_payload.write_UINT32(1072066624) # Processing factory on platform 5
table3_payload.write_UINT8(8)
table3_payload.write_UINT32(2041806607) # Processing factory 4 on platform 8

table4_payload = Encoder()
table4_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table4_payload.write_UINT8(0)
table4_payload.write_UINT8(1) # 1 RFID tag in this message
table4_payload.write_UINT8(0)
table4_payload.write_UINT32(1071746557) # MV-LV TF 1 (transformer) on platform 0

table5_payload = Encoder()
table5_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table5_payload.write_UINT8(0)
table5_payload.write_UINT8(1) # 1 RFID tag in this message
table5_payload.write_UINT8(0)
table5_payload.write_UINT32(1072040213) # MV-LV TF 3 (transformer) on platform 0

table6_payload = Encoder()
table6_payload.write_UINT8(OPCODE_TABLE.RFID.value)
table6_payload.write_UINT8(0)
table6_payload.write_UINT8(5) # 5 RFID tags in this message
table6_payload.write_UINT8(0)
table6_payload.write_UINT32(1072051579) # MV-LV TF 2 (transformer) on platform 0
table6_payload.write_UINT8(2)
table6_payload.write_UINT32(3914547211) # House 5 on platform 2
table6_payload.write_UINT8(3)
table6_payload.write_UINT32(1071773816) # Storage house 1 on platform 3
table6_payload.write_UINT8(4)
table6_payload.write_UINT32(1071770985) # Appartment 1 on platform 4
table6_payload.write_UINT8(6)
table6_payload.write_UINT32(1072039450) # StorageLV1 on platform 6

table1_packet = bytearray(table1_payload.buffer)
table2_packet = bytearray(table2_payload.buffer)
table3_packet = bytearray(table3_payload.buffer)
table4_packet = bytearray(table4_payload.buffer)
table5_packet = bytearray(table5_payload.buffer)
table6_packet = bytearray(table6_payload.buffer)

client.publish(topic + "/Table1/Outgoing", table1_packet) 
client.publish(topic + "/Table2/Outgoing", table2_packet)
client.publish(topic + "/Table3/Outgoing", table3_packet)
client.publish(topic + "/Table4/Outgoing", table4_packet)
client.publish(topic + "/Table5/Outgoing", table5_packet)
client.publish(topic + "/Table6/Outgoing", table6_packet)

# Start the MQTT client loop to begin listening for messages
client.loop()

sleep(0.2)

