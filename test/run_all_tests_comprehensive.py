#!/usr/bin/env python3
"""
Comprehensive Test Runner for Smart Grid Table

This script automatically discovers and runs all test files in the test directory.
It provides comprehensive reporting and validation of the entire test suite.

Author: AI Assistant  
Date: 2024
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import time
import glob
import importlib.util
from datetime import datetime


def discover_test_files():
    """Discover all test files in the test directory."""
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = []
    
    # Find all Python files starting with 'test_' or ending with '_test.py'
    patterns = [
        os.path.join(test_dir, "test_*.py"),
        os.path.join(test_dir, "*_test.py")
    ]
    
    for pattern in patterns:
        test_files.extend(glob.glob(pattern))
    
    # Filter out this file itself and __init__.py
    current_file = os.path.abspath(__file__)
    test_files = [f for f in test_files if f != current_file and not f.endswith('__init__.py')]
    
    return sorted(test_files)


def load_test_module(test_file):
    """Load a test module from file path."""
    module_name = os.path.splitext(os.path.basename(test_file))[0]
    spec = importlib.util.spec_from_file_location(module_name, test_file)
    module = importlib.util.module_from_spec(spec)
    
    try:
        spec.loader.exec_module(module)
        return module, None
    except Exception as e:
        return None, str(e)


def run_test_file(test_file):
    """Run tests from a specific test file."""
    print(f"\n{'='*80}")
    test_name = os.path.basename(test_file)
    print(f"Running: {test_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Load the test module
        module, error = load_test_module(test_file)
        if error:
            print(f"FAILED to load {test_name}: {error}")
            return False, 0, 0
        
        # Discover tests in the module
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        # Count tests
        test_count = suite.countTestCases()
        if test_count == 0:
            print(f"WARNING: No tests found in {test_name}")
            return True, 0, 0
        
        print(f"Found {test_count} test(s)")
        
        # Run the tests
        runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
        result = runner.run(suite)
        
        duration = time.time() - start_time
        
        # Calculate results
        passed = result.testsRun - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)
        
        if result.wasSuccessful():
            print(f"PASSED {test_name} - {passed}/{result.testsRun} tests ({duration:.2f}s)")
            return True, passed, result.testsRun
        else:
            print(f"FAILED {test_name} - {passed}/{result.testsRun} tests passed, {failed} failed ({duration:.2f}s)")
            
            # Print failure details
            if result.failures:
                print(f"\nFAILURES:")
                for test, traceback in result.failures:
                    print(f"  FAILED {test}: {traceback.splitlines()[-1] if traceback.splitlines() else 'Unknown error'}")
            
            if result.errors:
                print(f"\nERRORS:")
                for test, traceback in result.errors:
                    print(f"  ERROR {test}: {traceback.splitlines()[-1] if traceback.splitlines() else 'Unknown error'}")
            
            return False, passed, result.testsRun
            
    except Exception as e:
        duration = time.time() - start_time
        print(f"ERROR {test_name}: {e} ({duration:.2f}s)")
        return False, 0, 0


def main():
    """Run all discovered test files."""
    print("Starting Comprehensive Smart Grid Table Test Discovery & Execution")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Auto-discovering ALL test files in test directory")
    
    start_time = time.time()
    
    # Discover test files
    test_files = discover_test_files()
    
    if not test_files:
        print("WARNING: No test files found!")
        return 1
    
    print(f"\nDISCOVERED {len(test_files)} TEST FILES:")
    for i, test_file in enumerate(test_files, 1):
        test_name = os.path.basename(test_file)
        print(f"  {i:2d}. {test_name}")
    
    # Run all tests
    results = []
    total_passed = 0
    total_tests = 0
    
    print(f"\n{'='*25} RUNNING ALL TESTS {'='*25}")
    
    for test_file in test_files:
        success, passed, tests = run_test_file(test_file)
        results.append((os.path.basename(test_file), success, passed, tests))
        total_passed += passed
        total_tests += tests
    
    # Final summary
    total_duration = time.time() - start_time
    successful_files = sum(1 for _, success, _, _ in results if success)
    total_files = len(results)
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE TEST EXECUTION REPORT")
    print(f"{'='*80}")
    print(f"Total Duration: {total_duration:.2f}s")
    print(f"Test Files: {successful_files}/{total_files} successful")
    print(f"Individual Tests: {total_passed}/{total_tests} passed")
    print(f"Success Rate: {(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "Success Rate: N/A")
    
    print(f"\nDETAILED FILE RESULTS:")
    for filename, success, passed, tests in results:
        status = "PASS" if success else "FAIL"
        if tests > 0:
            print(f"  {status} {filename:35} ({passed:3d}/{tests:3d} tests)")
        else:
            print(f"  {status} {filename:35} (no tests)")
    
    print(f"\nTEST CATEGORIES COVERED:")
    categories = {
        "Core Unit Tests": [f for f in test_files if any(x in os.path.basename(f) for x in ["binary_", "model_segmentation"])],
        "Pandapower Tests": [f for f in test_files if "pandapower" in os.path.basename(f)],
        "Refactored App Tests": [f for f in test_files if "refactored" in os.path.basename(f)],
        "Performance Tests": [f for f in test_files if "performance" in os.path.basename(f)],
        "Security Tests": [f for f in test_files if "security" in os.path.basename(f)],
        "Simulation Tests": [f for f in test_files if "simulation" in os.path.basename(f)],
        "Other Tests": []
    }
    
    # Categorize remaining files
    categorized = set()
    for category_files in categories.values():
        categorized.update(category_files)
    
    categories["Other Tests"] = [f for f in test_files if f not in categorized]
    
    for category, files in categories.items():
        if files:
            print(f"  {category}: {len(files)} file(s)")
            for f in files:
                print(f"    - {os.path.basename(f)}")
    
    print(f"\n{'='*80}")
    if successful_files == total_files and total_passed == total_tests:
        print("ALL TESTS PASSED! Complete test suite validation successful!")
        print("The Smart Grid Table system is fully tested and validated!")
        return 0
    else:
        print("Some tests failed. Review the detailed results above.")
        failed_files = total_files - successful_files
        failed_tests = total_tests - total_passed
        print(f"Summary: {failed_files} file(s) failed, {failed_tests} individual test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 