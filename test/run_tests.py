
import unittest
from binary_encoder_test import BinaryEncoderTest
from binary_decoder_test import BinaryDecoderTest
from model_segmentation_test import ModelSegmentationTest

def encoder_suite():
    suite = unittest.TestSuite()
    suite.addTest(BinaryEncoderTest('test_write_uint8'))
    suite.addTest(BinaryEncoderTest('test_write_uint16'))
    suite.addTest(BinaryEncoderTest('test_write_uint32'))
    suite.addTest(BinaryEncoderTest('test_write_int8'))
    suite.addTest(BinaryEncoderTest('test_write_int16'))
    suite.addTest(BinaryEncoderTest('test_write_int32'))
    return suite

def decoder_suite():
    suite = unittest.TestSuite()
    suite.addTest(BinaryDecoderTest('test_read_uint8'))
    suite.addTest(BinaryDecoderTest('test_read_uint16'))
    suite.addTest(BinaryDecoderTest('test_read_uint32'))
    suite.addTest(BinaryDecoderTest('test_read_int8'))
    suite.addTest(BinaryDecoderTest('test_read_int16'))
    suite.addTest(BinaryDecoderTest('test_read_int32'))
    return suite

def model_segmentation_suite():
    suite = unittest.TestSuite()
    suite.addTest(ModelSegmentationTest('test_complete_network_buses'))
    suite.addTest(ModelSegmentationTest('test_complete_network_lines'))
    suite.addTest(ModelSegmentationTest('test_complete_network_generators'))
    suite.addTest(ModelSegmentationTest('test_complete_network_loads'))
    suite.addTest(ModelSegmentationTest('test_complete_network_storage_units'))
    suite.addTest(ModelSegmentationTest('test_split_network_buses'))
    suite.addTest(ModelSegmentationTest('test_split_network_lines'))
    suite.addTest(ModelSegmentationTest('test_split_network_generators'))
    suite.addTest(ModelSegmentationTest('test_split_network_loads'))
    suite.addTest(ModelSegmentationTest('test_split_network_storage_units'))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    runner.verbosity = 2
    runner.run(encoder_suite())
    runner.run(decoder_suite())
    runner.run(model_segmentation_suite())
