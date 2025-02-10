
##
# @file binary_decoder_test.py
#
# @brief Unit test for binary decoding of data.
#
# Created by Jop Merz on 01/11/2023.
##

# Internal imports
from src.networking.Decoder import Decoder

# External imports
import unittest
import numpy as np

class BinaryDecoderTest(unittest.TestCase):
    """
    Unit test for binary decoding of data.
    """
    def setUp(self) -> None:
        """
        Create empty buffer.
        """
        self.buffer = np.array = np.empty([0], dtype=np.uint8)
    
    def test_read_uint8(self):
        """
        Test for UINT8 decoding.
        """
        self.buffer = np.resize(self.buffer, 3)
        self.buffer[0] = 0
        self.buffer[1] = 128
        self.buffer[2] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)        
        self.assertTrue(self.decoder.read_UINT8() == 0)
        self.assertTrue(self.decoder.read_UINT8() == 128)
        self.assertTrue(self.decoder.read_UINT8() == 255)
        self.assertTrue(self.decoder.index == 3)

    def test_read_uint16(self):
        """
        Test for UINT16 decoding.
        """
        self.buffer = np.resize(self.buffer, 6)
        self.buffer[0] = 0
        self.buffer[1] = 0
        self.buffer[2] = 128
        self.buffer[3] = 0
        self.buffer[4] = 255
        self.buffer[5] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)
        self.assertTrue(self.decoder.read_UINT16() == 0)
        self.assertTrue(self.decoder.read_UINT16() == 32768)
        self.assertTrue(self.decoder.read_UINT16() == 65535)
        self.assertTrue(self.decoder.index == 6)

    def test_read_uint32(self):
        """
        Test for UINT32 decoding.
        """
        self.buffer = np.resize(self.buffer, 12)
        self.buffer[0] = 0
        self.buffer[1] = 0
        self.buffer[2] = 0
        self.buffer[3] = 0
        self.buffer[4] = 128
        self.buffer[5] = 0
        self.buffer[6] = 0
        self.buffer[7] = 0
        self.buffer[8] = 255
        self.buffer[9] = 255
        self.buffer[10] = 255
        self.buffer[11] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)
        self.assertTrue(self.decoder.read_UINT32() == 0)
        self.assertTrue(self.decoder.read_UINT32() == 2147483648)
        self.assertTrue(self.decoder.read_UINT32() == 4294967295)
        self.assertTrue(self.decoder.index == 12)

    def test_read_int8(self):
        """
        Test for INT8 decoding.
        """
        self.buffer = np.resize(self.buffer, 3)
        self.buffer[0] = 128
        self.buffer[1] = 0
        self.buffer[2] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)        
        self.assertTrue(self.decoder.read_INT8() == 0)
        self.assertTrue(self.decoder.read_INT8() == -128)
        self.assertTrue(self.decoder.read_INT8() == 127)
        self.assertTrue(self.decoder.index == 3)

    def test_read_int16(self):
        """
        Test for INT16 decoding.
        """
        self.buffer = np.resize(self.buffer, 6)
        self.buffer[0] = 0
        self.buffer[1] = 0
        self.buffer[2] = 128
        self.buffer[3] = 0
        self.buffer[4] = 255
        self.buffer[5] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)
        self.assertTrue(self.decoder.read_INT16() == -32768)
        self.assertTrue(self.decoder.read_INT16() == 0)
        self.assertTrue(self.decoder.read_INT16() == 32767)
        self.assertTrue(self.decoder.index == 6)

    def test_read_int32(self):
        """
        Test for INT32 decoding.
        """
        self.buffer = np.resize(self.buffer, 12)
        self.buffer[0] = 0
        self.buffer[1] = 0
        self.buffer[2] = 0
        self.buffer[3] = 0
        self.buffer[4] = 128
        self.buffer[5] = 0
        self.buffer[6] = 0
        self.buffer[7] = 0
        self.buffer[8] = 255
        self.buffer[9] = 255
        self.buffer[10] = 255
        self.buffer[11] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)
        self.assertTrue(self.decoder.read_INT32() == -2147483648)
        self.assertTrue(self.decoder.read_INT32() == 0)
        self.assertTrue(self.decoder.read_INT32() == 2147483647)
        self.assertTrue(self.decoder.index == 12)

if __name__ == '__main__':
    unittest.main()