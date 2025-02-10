
# External imports
from enum import Enum

## Opcodes used in mesages from the simulation program to the Smart Grid Table
class OPCODE_SERVER(Enum):
    PING = 0
    PONG = 1
    FIRMWARE_UPDATE = 2
    FIRMWARE_REQUEST = 3
    CONFIG_UPDATE = 4
    CONFIG_REQUEST = 5
    RFID_REQUEST = 6
    LED_POWER_FLOW = 7
    LED_BACKGROUND = 8
    REBOOT = 9
    ID_REQUEST = 10
    STATUS_REQUEST = 11

## Opcodes used in messages sent by the Smart Grid Table
class OPCODE_TABLE(Enum):
    PING = 0
    PONG = 1
    ONLINE = 2
    ID = 3
    RFID = 4
    VERSION = 5
    VERSION_LATEST = 6
    LATEST_VERSION = 7
    STATUS = 8
