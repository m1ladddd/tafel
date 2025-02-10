##
# @file Ledstrip.py
#
# @brief Class which represents a ledstrip on a table section.
# This class contains the led flow speed, color, direction and state.
#
# @section libraries_Ledstrip Libraries/Modules
# - 
#
# @section todo_Ledstrip TODO
# - None
#
# @section author_Ledstrip Author(s)
# - Created by Jop Merz, Thijs van Elsacker on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

from src.led.LEDDatatype import RBGAColor
from src.led.LEDDatatype import RBGColor

class LEDStrip:
    """! 
    Class which represents a ledstrip on a table section.
    This class contains the led flow speed, color, direction and state.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Red flow color (red, green, blue, alpha).
        self.flow_color: RBGAColor = RBGAColor(0x00, 0x00, 0x00, 0x00)

        ## Direction of powerflow animation (0 = foreward, 1 = reverse).
        self.flow_direction: int = 0

        ## Time for one animation cycle to finish in seconds
        self.flow_speed: int = 200

        ## Flow blinking speed in seconds
        self.flow_flashing_speed: int = 0

        ## Red background color (red, green, blue).
        self.background_color: RBGColor = RBGColor(0x00, 0x00, 0x00)

        ## Background blinking speed in seconds
        self.background_flashing_speed: int = 0

        ## Error state of the ledstrip (True = error, False = no error).
        ## If true, ignores all other parameters
        self.error: bool = False

        ## Avtive state of the ledstrip (True = turned on, False = ledstrip will be turned off).
        self.active: bool = True

        ## Line to which the ledstip is connected to.
        self.line: str = ""

        ## LED strip indentifier on the table
        self.id: int = 0


    def set_ledstrip_id(self, id: int) -> None:
        # uint8 range is 0 to 255.
        self.id = int(max(0, min(255, id)))


    def set_flow_color(self, color: RBGAColor):
        """! 
        Set flow color in RGB format
        @param color: RBGAColor Color dataclass containing red, green, blue and alpha channels
        """
        # uint8 range is 0 to 255.
        self.flow_color.red = int(max(0, min(255, color.red)))
        self.flow_color.green = int(max(0, min(255, color.green)))
        self.flow_color.blue = int(max(0, min(255, color.blue)))
        self.flow_color.alpha = int(max(0, min(255, color.alpha)))


    def set_flow_transparency(self, alpha: int):
        """! 
        Set flow color transparency.
        @param alpha: int Color transparency of the power flow color
        """
        # uint8 range is 0 to 255.
        self.flow_color.alpha = int(max(0, min(255, alpha)))


    def set_flow_speed(self, speed: int) -> None:
        """! 
        Set flow animation speed
        @param alpha: int Animation speed in ms
        """
        # uint16 range is 0 to 65535.
        self.flow_speed = int(max(0, min(65535, speed)))


    def set_background_color(self, color: RBGColor):
        """! 
        Set background color in RGB format
        @param color: RBGAColor Color dataclass containing red, green, blue and alpha channels
        """
        # uint8 range is 0 to 255.
        self.background_color.red = int(max(0, min(255, color.red)))
        self.background_color.green = int(max(0, min(255, color.green)))
        self.background_color.blue = int(max(0, min(255, color.blue)))


    def set_background_flashing_time(self, time: int):
        """! 
        Set the background blinking time in seconds
        @param 
        """
        # uint16 range is 0 to 65535.
        self.background_flashing_speed = int(max(0, min(65535, time)))


def compare_led_power_flow(ledstrip_1: LEDStrip, ledstrip_2: LEDStrip) -> bool:
    if (ledstrip_1.flow_color != ledstrip_2.flow_color or
        ledstrip_1.flow_speed != ledstrip_2.flow_speed or
        ledstrip_1.flow_direction != ledstrip_2.flow_direction):
        return True
    return False


def compare_led_background(ledstrip_1: LEDStrip, ledstrip_2: LEDStrip) -> bool:
    if (ledstrip_1.background_color != ledstrip_2.background_color or
        ledstrip_1.background_flashing_speed != ledstrip_2.background_flashing_speed):
        return True
    return False