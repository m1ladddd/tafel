# src/networking/Decoder.py

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
        # Ensure buffer is a numpy array
        if not isinstance(buffer, np.ndarray):
            # Try converting if it's list-like, otherwise raise error
            try:
                 self.buffer: np.ndarray = np.array(buffer, dtype=np.uint8)
            except Exception as e:
                 raise TypeError(f"Input buffer must be a NumPy array or convertible. Error: {e}")
        else:
            self.buffer: np.ndarray = buffer

        ## Read index.
        self.index: int = start_index


    def read_UINT8(self) -> np.uint8:
        """!
        Read a unsigned 8-bit integer from the byte stream.
        @return np.uint8
        """
        # Ensure index is within bounds before reading
        if self.index >= len(self.buffer):
            raise IndexError(f"Read index {self.index} out of bounds for buffer size {len(self.buffer)}")
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
            raise IndexError(f"Read index {self.index+1} out of bounds for buffer size {len(self.buffer)}")
        value = np.uint16(0)
        # Cast bytes to prevent potential overflow issues during shift if using Python ints
        byte0 = np.uint16(self.buffer[self.index+0]) # MSB
        byte1 = np.uint16(self.buffer[self.index+1]) # LSB
        value = np.bitwise_or(value, np.left_shift(byte0, 8))
        value = np.bitwise_or(value, byte1)
        self.index += 2
        return value


    def read_UINT32(self) -> np.uint32:
        """!
        Read a unsigned 32-bit integer from the byte stream.
        @return np.uint32
        """
         # Ensure index is within bounds before reading
        if self.index + 3 >= len(self.buffer):
            raise IndexError(f"Read index {self.index+3} out of bounds for buffer size {len(self.buffer)}")
        value = np.uint32(0)
        byte0 = np.uint32(self.buffer[self.index+0]) # MSB
        byte1 = np.uint32(self.buffer[self.index+1])
        byte2 = np.uint32(self.buffer[self.index+2])
        byte3 = np.uint32(self.buffer[self.index+3]) # LSB
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
        # CORRECTION: Use .view() for robust unsigned-to-signed conversion
        value: np.int8 = u_value.view(np.int8)
        return value


    def read_INT16(self) -> np.int16:
        """!
        Read a signed 16-bit integer from the byte stream.
        @return np.int16
        """
        u_value: np.uint16 = self.read_UINT16()
        # CORRECTION: Use .view() for robust unsigned-to-signed conversion
        value: np.int16 = u_value.view(np.int16)
        return value


    def read_INT32(self) -> np.int32:
        """!
        Read a signed 32-bit integer from the byte stream.
        @return np.int32
        """
        u_value: np.uint32 = self.read_UINT32()
        # CORRECTION: Use .view() for robust unsigned-to-signed conversion
        value: np.int32 = u_value.view(np.int32)
        return value