##
# @file Encoder.py
# @author Jop Merz
#
# @brief  Simple binary encoder
#
# @version 0.1
# @date 24-02-2022
##

# External imports
import numpy as np

class Encoder:
    """!
    Class which encodes the folowing valuetypes:
    8-bit, 16-bit, 32-bit and 64-bit unsigned integers.
    8-bit, 16-bit, 32-bit and 64-bit signed integers.
    """

    def __init__(self) -> None:
        """!
        Constructor.
        """

        ## Byte buffer.
        self.buffer: np.array = np.empty([0], dtype=np.uint8)

        ## Write index, used to determine where to write the next data entry.
        self.__index: int = 0


    def clear_buffer(self):
        """!
        Empties all previous encoded values.
        """
        self.buffer = np.empty([0], dtype=np.uint8)  
        self.__index = 0


    def write_UINT8(self, value: np.uint8) -> None:
        """!
        Write a unsigned 8-bit integer.
        @param value np.uint8
        """
        self.buffer = np.resize(self.buffer, self.__index + 1)
        self.buffer[self.__index] = value
        self.__index += 1


    def write_UINT16(self, value: np.uint16) -> None:
        """!
        Write a unsigned 16-bit integer.
        @param value np.uint16
        """
        self.buffer = np.resize(self.buffer, self.__index + 2)
        self.buffer[self.__index+0] = np.right_shift(value, 8)
        self.buffer[self.__index+1] = np.right_shift(value, 0)
        self.__index += 2


    def write_UINT32(self, value: np.uint32) -> None:
        """!
        Write a unsigned 32-bit integer.
        @param value np.uint32
        """
        self.buffer = np.resize(self.buffer, self.__index + 4)
        self.buffer[self.__index+0] = np.right_shift(value, 24)
        self.buffer[self.__index+1] = np.right_shift(value, 16)
        self.buffer[self.__index+2] = np.right_shift(value, 8)
        self.buffer[self.__index+3] = np.right_shift(value, 0)
        self.__index += 4


    def write_INT8(self, value: np.int8) -> None:
        """!
        Write a signed 8-bit integer.
        @param value np.int8
        """
        u_value: np.uint8 = value + 128
        self.write_UINT8(u_value)


    def write_INT16(self, value: np.int16) -> None:
        """!
        Write a signed 16-bit integer.
        @param value np.int16
        """
        u_value: np.uint16 = value + 32768
        self.write_UINT16(u_value)


    def write_INT32(self, value: np.int32) -> None:
        """!
        Write a signed 32-bit integer.
        @param value np.int32
        """
        u_value: np.uint32 = value + 2147483648
        self.write_UINT32(u_value)


    def get_size(self) -> int:
        """!
        Return the current encoded payload size.
        @return int
        """
        return len(self.buffer)
