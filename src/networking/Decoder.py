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
        # Ensure index is within bounds before reading
        if self.index >= len(self.buffer):
            raise IndexError("Read index out of bounds for buffer")
        value = np.uint8(self.buffer[self.index])
        self.index += 1
        return value


    def read_UINT16(self) -> np.uint16:
        """!
        Read a unsigned 16-bit integer from the byte stream.
        @return np.uint16
        """
        # Ensure index is within bounds before reading
        if self.index + 1 >= len(self.buffer):
            raise IndexError("Read index out of bounds for buffer")
        value = np.uint16(0)
        # Cast bytes to prevent potential overflow issues during shift if using Python ints
        byte0 = np.uint16(self.buffer[self.index+0])
        byte1 = np.uint16(self.buffer[self.index+1])
        value = np.bitwise_or(value, np.left_shift(byte0, 8))
        value = np.bitwise_or(value, byte1) # No shift needed for the least significant byte
        self.index += 2
        return value


    def read_UINT32(self) -> np.uint32:
        """!
        Read a unsigned 32-bit integer from the byte stream.
        @return np.uint32
        """
         # Ensure index is within bounds before reading
        if self.index + 3 >= len(self.buffer):
            raise IndexError("Read index out of bounds for buffer")
        value = np.uint32(0)
        byte0 = np.uint32(self.buffer[self.index+0])
        byte1 = np.uint32(self.buffer[self.index+1])
        byte2 = np.uint32(self.buffer[self.index+2])
        byte3 = np.uint32(self.buffer[self.index+3])
        value = np.bitwise_or(value, np.left_shift(byte0, 24))
        value = np.bitwise_or(value, np.left_shift(byte1, 16))
        value = np.bitwise_or(value, np.left_shift(byte2, 8))
        value = np.bitwise_or(value, byte3)
        self.index += 4
        return value


    def read_INT8(self) -> np.int8:
        """!
        Read a signed 8-bit integer from the byte stream.
        @return np.int8
        """
        u_value: np.uint8 = self.read_UINT8()
        # CORRECTION: Cast u_value to the target signed type BEFORE subtracting offset
        value: np.int8 = np.int8(u_value) - np.int8(128)
        return value


    def read_INT16(self) -> np.int16:
        """!
        Read a signed 16-bit integer from the byte stream.
        @return np.int16
        """
        u_value: np.uint16 = self.read_UINT16()
        # CORRECTION: Cast u_value to the target signed type BEFORE subtracting offset
        value: np.int16 = np.int16(u_value) - np.int16(32768)
        return value


    def read_INT32(self) -> np.int32:
        """!
        Read a signed 32-bit integer from the byte stream.
        @return np.int32
        """
        u_value: np.uint32 = self.read_UINT32()
         # CORRECTION: Cast u_value to the target signed type BEFORE subtracting offset
        # Using Python's arbitrary precision int for offset is fine here
        offset = 2147483648
        # Check if u_value is large enough before casting to avoid potential issues
        if u_value >= offset:
             # Cast to signed *after* potentially subtracting offset as intermediate
             # Or ensure calculation happens in a larger type if needed
             value: np.int32 = np.int32(u_value - offset) # This works if u_value >= offset
        else:
             # If u_value < offset, the result is negative.
             # Cast u_value to signed first, then subtract offset (promotes offset too)
             value: np.int32 = np.int32(u_value) - np.int32(offset)

        # Alternative robust way using NumPy's view method (might be cleaner):
        # value = u_value.view(np.int32)

        return value