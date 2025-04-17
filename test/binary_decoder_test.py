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
        # CORRECTIE: Wijs alleen toe aan self.buffer
        self.buffer = np.empty([0], dtype=np.uint8)

    def test_read_uint8(self):
        """
        Test for UINT8 decoding.
        """
        self.buffer = np.resize(self.buffer, 3)
        self.buffer[0] = 0
        self.buffer[1] = 128
        self.buffer[2] = 255
        self.decoder: Decoder = Decoder(self.buffer, 0)
        self.assertEqual(self.decoder.read_UINT8(), 0)
        self.assertEqual(self.decoder.read_UINT8(), 128)
        self.assertEqual(self.decoder.read_UINT8(), 255)
        self.assertEqual(self.decoder.index, 3)

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
        self.assertEqual(self.decoder.read_UINT16(), 0)
        self.assertEqual(self.decoder.read_UINT16(), 32768)
        self.assertEqual(self.decoder.read_UINT16(), 65535)
        self.assertEqual(self.decoder.index, 6)

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
        self.assertEqual(self.decoder.read_UINT32(), 0)
        self.assertEqual(self.decoder.read_UINT32(), 2147483648)
        self.assertEqual(self.decoder.read_UINT32(), 4294967295)
        self.assertEqual(self.decoder.index, 12)

    def test_read_int8(self):
        """
        Test for INT8 decoding.
        """
        self.buffer = np.resize(self.buffer, 3)
        self.buffer[0] = 128 # uint(128) - 128 = 0
        self.buffer[1] = 0   # uint(0) - 128 = -128
        self.buffer[2] = 255 # uint(255) - 128 = 127
        self.decoder: Decoder = Decoder(self.buffer, 0)
        # CORRECTION: Verwachte waarden voor de aftrek-methode
        self.assertEqual(self.decoder.read_INT8(), 0)
        self.assertEqual(self.decoder.read_INT8(), -128)
        self.assertEqual(self.decoder.read_INT8(), 127)
        self.assertEqual(self.decoder.index, 3)

    def test_read_int16(self):
        """
        Test for INT16 decoding.
        """
        self.buffer = np.resize(self.buffer, 6)
        self.buffer[0] = 0   # Byte 0 \ uint(0) - 32768 = -32768
        self.buffer[1] = 0   # Byte 1 /
        self.buffer[2] = 128 # Byte 2 \ uint(32768) - 32768 = 0
        self.buffer[3] = 0   # Byte 3 /
        self.buffer[4] = 255 # Byte 4 \ uint(65535) - 32768 = 32767
        self.buffer[5] = 255 # Byte 5 /
        self.decoder: Decoder = Decoder(self.buffer, 0)
        # CORRECTION: Verwachte waarden voor de aftrek-methode
        self.assertEqual(self.decoder.read_INT16(), -32768)
        self.assertEqual(self.decoder.read_INT16(), 0)
        self.assertEqual(self.decoder.read_INT16(), 32767)
        self.assertEqual(self.decoder.index, 6)

    def test_read_int32(self):
        """
        Test for INT32 decoding.
        """
        self.buffer = np.resize(self.buffer, 12)
        self.buffer[0] = 0   # Byte 0 \
        self.buffer[1] = 0   # Byte 1 | uint(0) - offset = -offset
        self.buffer[2] = 0   # Byte 2 |
        self.buffer[3] = 0   # Byte 3 /
        self.buffer[4] = 128 # Byte 4 \ uint(offset) - offset = 0
        self.buffer[5] = 0   # Byte 5 |
        self.buffer[6] = 0   # Byte 6 |
        self.buffer[7] = 0   # Byte 7 /
        self.buffer[8] = 255 # Byte 8 \ uint(max) - offset = max_signed
        self.buffer[9] = 255 # Byte 9 |
        self.buffer[10] = 255# Byte 10|
        self.buffer[11] = 255# Byte 11/
        self.decoder: Decoder = Decoder(self.buffer, 0)
        # CORRECTION: Verwachte waarden voor de aftrek-methode
        self.assertEqual(self.decoder.read_INT32(), -2147483648)
        self.assertEqual(self.decoder.read_INT32(), 0)
        self.assertEqual(self.decoder.read_INT32(), 2147483647)
        self.assertEqual(self.decoder.index, 12)

if __name__ == '__main__':
    unittest.main()