#!/usr/bin/env python3
"""
Migration Validation Test Runner
Comprehensive test suite for PyPSA to Pandapower migration validation.

Uses: pytest, timing decorators, cProfile, memory-profiler
Test Technologies: Unit tests, Integration tests, Performance tests, Equivalence tests
"""

import pytest
import sys
import os
import time
from pathlib import Path
import subprocess
import psutil

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def run_test_suite_with_timing(test_file, test_name):
    """Run a test suite and measure execution time."""
    print(f"\n{'='*60}")
    print(f"RUNNING: {test_name}")
    print(f"File: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.perf_counter()
    
    # Run pytest with verbose output
    result = pytest.main([
        test_file, 
        "-v", 
        "--tb=short",
        "--capture=no",  # Show print statements
        f"--junitxml=test_results_{Path(test_file).stem}.xml"
    ])
    
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    print(f"\n{test_name} completed in {duration:.2f} seconds")
    print(f"Exit code: {result}")
    
    return result == 0, duration

def check_system_resources():
    """Check and report system resources before testing."""
    print("System Resource Check:")
    print(f"  CPU Count: {psutil.cpu_count()}")
    
    memory = psutil.virtual_memory()
    print(f"  Total Memory: {memory.total / 1024**3:.1f} GB")
    print(f"  Available Memory: {memory.available / 1024**3:.1f} GB")
    print(f"  Memory Usage: {memory.percent}%")
    
    disk = psutil.disk_usage('.')
    print(f"  Disk Space: {disk.free / 1024**3:.1f} GB free")

def main():
    """Run comprehensive migration validation test suite."""
    print("Smart Grid Table - PyPSA to Pandapower Migration Validation")
    print("=" * 70)
    
    check_system_resources()
    
    # Test suite configuration following the test plan
    test_suites = [
        # 1. Equivalence Tests (CRITICAL for migration)
        ("test_golden_reference_equivalence.py", "Golden Reference Equivalence Tests"),
        ("test_architecture_compatibility.py", "Architecture Compatibility Tests"),
        ("test_historical_comparison.py", "Historical Comparison Tests (if data available)"),
        
        # 2. Existing Core Functionality Tests
        ("test_pandapower_implementation.py", "Pandapower Implementation Tests"),
        ("test_pandapower_calculators.py", "Pandapower Calculator Tests"), 
        ("test_pandapower_network.py", "Pandapower Network Tests"),
        
        # 3. Model Segmentation & Threading
        ("model_segmentation_test.py", "Model Segmentation Tests"),
        
        # 4. System Integration Tests
        ("test_refactored_comprehensive.py", "Comprehensive System Tests"),
        ("test_refactored_app.py", "Application Integration Tests"),
        
        # 5. Performance & Stress Tests
        ("test_performance_advanced.py", "Advanced Performance Tests"),
        ("test_stress_complex_networks.py", "Complex Network Stress Tests"),
        
        # 6. Security & Validation
        ("test_security_validation.py", "Security Validation Tests"),
    ]
    
    results = {}
    total_start_time = time.perf_counter()
    
    # Execute test suites
    for test_file, test_name in test_suites:
        test_path = Path(__file__).parent / test_file
        
        if test_path.exists():
            success, duration = run_test_suite_with_timing(str(test_path), test_name)
            results[test_name] = {'success': success, 'duration': duration}
        else:
            print(f"\nSKIPPED: {test_name} - File not found: {test_file}")
            results[test_name] = {'success': None, 'duration': 0}
    
    total_duration = time.perf_counter() - total_start_time
    
    # Generate summary report
    print("\n" + "="*70)
    print("MIGRATION VALIDATION TEST SUMMARY")
    print("="*70)
    
    passed_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    print("\nTest Results:")
    for test_name, result in results.items():
        if result['success'] is True:
            status = "PASSED"
            passed_tests += 1
        elif result['success'] is False:
            status = "FAILED"
            failed_tests += 1
        else:
            status = "SKIPPED"
            skipped_tests += 1
        
        print(f"  {status} {test_name} ({result['duration']:.2f}s)")
    
    print(f"\nSummary:")
    print(f"  Total Tests: {len(test_suites)}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Skipped: {skipped_tests}")
    print(f"  Total Duration: {total_duration:.2f} seconds")
    
    # Migration validation assessment
    print(f"\nMigration Validation Assessment:")
    critical_tests = [
        "Golden Reference Equivalence Tests",
        "Architecture Compatibility Tests", 
        "Pandapower Implementation Tests",
        "Model Segmentation Tests"
    ]
    
    critical_passed = all(
        results.get(test, {}).get('success', False) for test in critical_tests
    )
    
    if critical_passed:
        print("MIGRATION VALIDATION SUCCESSFUL")
        print("   All critical tests passed. Pandapower implementation is ready.")
    else:
        print("MIGRATION VALIDATION ISSUES DETECTED")
        print("   Critical tests failed. Review implementation before deployment.")
        
        failed_critical = [
            test for test in critical_tests 
            if not results.get(test, {}).get('success', False)
        ]
        print("   Failed critical tests:")
        for test in failed_critical:
            print(f"     - {test}")
    
    # Performance assessment
    perf_tests = [test for test in results.keys() if "Performance" in test or "Stress" in test]
    avg_perf_time = sum(results[test]['duration'] for test in perf_tests if results[test]['success']) / max(len(perf_tests), 1)
    
    print(f"\nPerformance Assessment:")
    print(f"  Average performance test time: {avg_perf_time:.2f}s")
    if avg_perf_time < 30:
        print("  Performance acceptable")
    else:
        print("  Performance needs attention")
    
    # Recommendations
    print(f"\nRecommendations:")
    if failed_tests == 0:
        print("  Excellent! All tests passed. Migration is successful.")
    elif failed_tests <= 2:
        print("  Minor issues detected. Review failed tests.")
    else:
        print("  Multiple issues detected. Comprehensive review needed.")
    
    # Exit with appropriate code
    exit_code = 0 if critical_passed and failed_tests == 0 else 1
    
    print(f"\nTest runner exiting with code: {exit_code}")
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest runner encountered an error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1) 