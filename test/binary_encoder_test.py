##
# @file binary_encoder_test.py
#
# @brief Unit test for binary encoding of data.
#
# Created by Jop Merz on 01/11/2023.
##

# Internal imports
from src.networking.Encoder import Encoder

# External imports
import unittest


class BinaryEncoderTest(unittest.TestCase):
    """
    Unit test for binary encoding of data.
    """
    def setUp(self) -> None:
        """
        Create encoder instance.
        """
        self.encoder: Encoder = Encoder()
    
    def test_write_uint8(self):
        """
        Test for UINT8 encoding.
        """
        self.encoder.write_UINT8(0)
        self.encoder.write_UINT8(128)
        self.encoder.write_UINT8(255)
        self.assertTrue(self.encoder.get_size() == 3)
        self.assertTrue(self.encoder.buffer[0] == 0)
        self.assertTrue(self.encoder.buffer[1] == 128)
        self.assertTrue(self.encoder.buffer[2] == 255)

    def test_write_uint16(self):
        """
        Test for UINT16 encoding.
        """
        self.encoder: Encoder = Encoder()
        self.encoder.write_UINT16(0)
        self.encoder.write_UINT16(32768)
        self.encoder.write_UINT16(65535)
        self.assertTrue(self.encoder.get_size() == 6)
        self.assertTrue(self.encoder.buffer[0] == 0 and self.encoder.buffer[1] == 0)
        self.assertTrue(self.encoder.buffer[2] == 128 and self.encoder.buffer[3] == 0)
        self.assertTrue(self.encoder.buffer[4] == 255 and self.encoder.buffer[5] == 255)

    def test_write_uint32(self):
        """
        Test for UINT32 encoding.
        """
        self.encoder: Encoder = Encoder()
        self.encoder.write_UINT32(0)
        self.encoder.write_UINT32(2147483648)
        self.encoder.write_UINT32(4294967295)
        self.assertTrue(self.encoder.get_size() == 12)
        self.assertTrue(self.encoder.buffer[0] == 0 and self.encoder.buffer[1] == 0 and
                        self.encoder.buffer[2] == 0 and self.encoder.buffer[3] == 0)
        self.assertTrue(self.encoder.buffer[4] == 128 and self.encoder.buffer[5] == 0 and
                        self.encoder.buffer[6] == 0 and self.encoder.buffer[7] == 0)
        self.assertTrue(self.encoder.buffer[8] == 255 and self.encoder.buffer[9] == 255 and
                        self.encoder.buffer[10] == 255 and self.encoder.buffer[11] == 255)

    def test_write_int8(self):
        """
        Test for INT8 encoding.
        """
        self.encoder.write_INT8(0)
        self.encoder.write_INT8(-128)
        self.encoder.write_INT8(127)
        self.assertTrue(self.encoder.get_size() == 3)
        self.assertTrue(self.encoder.buffer[0] == 128)
        self.assertTrue(self.encoder.buffer[1] == 0)
        self.assertTrue(self.encoder.buffer[2] == 255)

    def test_write_int16(self):
        """
        Test for INT16 encoding.
        """
        self.encoder: Encoder = Encoder()
        self.encoder.write_INT16(0)
        self.encoder.write_INT16(-32768)
        self.encoder.write_INT16(32767)
        self.assertTrue(self.encoder.get_size() == 6)
        self.assertTrue(self.encoder.buffer[0] == 128 and self.encoder.buffer[1] == 0)
        self.assertTrue(self.encoder.buffer[2] == 0 and self.encoder.buffer[3] == 0)
        self.assertTrue(self.encoder.buffer[4] == 255 and self.encoder.buffer[5] == 255)

    def test_write_int32(self):
        """
        Test for INT32 encoding.
        """
        self.encoder: Encoder = Encoder()
        self.encoder.write_INT32(0)
        self.encoder.write_INT32(-2147483648)
        self.encoder.write_INT32(2147483647)
        self.assertTrue(self.encoder.get_size() == 12)
        self.assertTrue(self.encoder.buffer[0] == 128 and self.encoder.buffer[1] == 0 and
                        self.encoder.buffer[2] == 0 and self.encoder.buffer[3] == 0)
        self.assertTrue(self.encoder.buffer[4] == 0 and self.encoder.buffer[5] == 0 and
                        self.encoder.buffer[6] == 0 and self.encoder.buffer[7] == 0)
        self.assertTrue(self.encoder.buffer[8] == 255 and self.encoder.buffer[9] == 255 and
                        self.encoder.buffer[10] == 255 and self.encoder.buffer[11] == 255)

if __name__ == '__main__':
    unittest.main()