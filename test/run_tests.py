# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import glob
import importlib.util

def discover_and_run_all_tests():
    """Discover and run all test files in the test directory."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all Python files starting with 'test_' or ending with '_test.py'
    patterns = [
        os.path.join(test_dir, "test_*.py"),
        os.path.join(test_dir, "*_test.py")
    ]
    
    test_files = []
    for pattern in patterns:
        test_files.extend(glob.glob(pattern))
    
    # Filter out this file itself
    current_file = os.path.abspath(__file__)
    test_files = [f for f in test_files if f != current_file and not f.endswith('__init__.py')]
    
    print(f"Discovered {len(test_files)} test files:")
    for test_file in sorted(test_files):
        print(f"  - {os.path.basename(test_file)}")
    
    # Create a test suite with all discovered tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    total_files = 0
    loaded_files = 0
    
    for test_file in sorted(test_files):
        total_files += 1
        try:
            # Load the test module
            module_name = os.path.splitext(os.path.basename(test_file))[0]
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Add tests from this module to the suite
            module_suite = loader.loadTestsFromModule(module)
            suite.addTest(module_suite)
            loaded_files += 1
            
        except Exception as e:
            print(f"WARNING: Failed to load {os.path.basename(test_file)}: {e}")
    
    print(f"\nSuccessfully loaded {loaded_files}/{total_files} test files")
    print(f"Total tests to run: {suite.countTestCases()}")
    
    # Run all tests
    print(f"\n{'='*60}")
    print("Running ALL discovered tests...")
    print(f"{'='*60}")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print("TEST EXECUTION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("ALL TESTS PASSED!")
    else:
        print("Some tests failed!")
    
    return result

# Legacy test suites for backwards compatibility
def encoder_suite():
    from binary_encoder_test import BinaryEncoderTest
    suite = unittest.TestSuite()
    suite.addTest(BinaryEncoderTest('test_write_uint8'))
    suite.addTest(BinaryEncoderTest('test_write_uint16'))
    suite.addTest(BinaryEncoderTest('test_write_uint32'))
    suite.addTest(BinaryEncoderTest('test_write_int8'))
    suite.addTest(BinaryEncoderTest('test_write_int16'))
    suite.addTest(BinaryEncoderTest('test_write_int32'))
    return suite

def decoder_suite():
    from binary_decoder_test import BinaryDecoderTest
    suite = unittest.TestSuite()
    suite.addTest(BinaryDecoderTest('test_read_uint8'))
    suite.addTest(BinaryDecoderTest('test_read_uint16'))
    suite.addTest(BinaryDecoderTest('test_read_uint32'))
    suite.addTest(BinaryDecoderTest('test_read_int8'))
    suite.addTest(BinaryDecoderTest('test_read_int16'))
    suite.addTest(BinaryDecoderTest('test_read_int32'))
    return suite

def model_segmentation_suite():
    from model_segmentation_test import ModelSegmentationTest
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
    # Run comprehensive test discovery by default
    discover_and_run_all_tests()
