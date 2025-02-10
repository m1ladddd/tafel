##
# @file Decoder.py
# @author Jop Merz
#
# @brief  Simple binary decoder
#
# @version 0.1
# @date 24-02-2022
##

# External imports
import numpy as np

class Decoder:
    """!
    Class which decodes (deserialize) the folowing valuetypes:
    8-bit, 16-bit, 32-bit and 64-bit unsigned integers.
    8-bit, 16-bit, 32-bit and 64-bit signed integers.
    """

    def __init__(self, buffer: np.array, start_index: int) -> None:
        """!
        Constructor.
        @param buffer np.array Input buffer
        @param start_index int Index form where to start decoding
        """

        ## Input byte buffer.
        self.buffer: np.array = buffer

        ## Read index.
        self.index: int = start_index


    def read_UINT8(self) -> np.uint8:
        """!
        Read a unsigned 8-bit integer from the byte stream.
        @return np.uint8
        """
        value = np.uint8(self.buffer[self.index])
        self.index += 1
        return value


    def read_UINT16(self) -> np.uint16:
        """!
        Read a unsigned 16-bit integer from the byte stream.
        @return np.uint16
        """
        value = np.uint16(0)
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+0], 8))
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+1], 0))
        self.index += 2
        return value


    def read_UINT32(self) -> np.uint32:
        """!
        Read a unsigned 32-bit integer from the byte stream.
        @return np.uint32
        """
        value = np.uint32(0)
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+0], 24))
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+1], 16))
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+2], 8))
        value = np.bitwise_or(value, np.left_shift(self.buffer[self.index+3], 0))
        self.index += 4
        return value


    def read_INT8(self) -> np.int8:
        """!
        Read a signed 8-bit integer from the byte stream.
        @return np.int8
        """
        u_value: np.uint8 = self.read_UINT8()
        value: np.int8 = u_value - 128
        return value


    def read_INT16(self) -> np.int16:
        """!
        Read a signed 16-bit integer from the byte stream.
        @return np.int16
        """
        u_value: np.uint16 = self.read_UINT16()
        value: np.int16 = u_value - 32768
        return value


    def read_INT32(self) -> np.int32:
        """!
        Read a signed 32-bit integer from the byte stream.
        @return np.int32
        """
        u_value: np.uint32 = self.read_UINT32()
        value: np.int32 = u_value - 2147483648
        return value

