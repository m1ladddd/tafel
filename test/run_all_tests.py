#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for Smart Grid Table Project
Runs all available unit tests, integration tests, and performance tests
"""

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import time
from contextlib import redirect_stdout, redirect_stderr
import io


def run_command(name: str, command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*80}")
    print(f"🧪 {name}")
    print(f"📝 {description}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(command, check=False, cwd=os.getcwd())
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ {name} PASSED ({duration:.2f}s)")
            return True
        else:
            print(f"❌ {name} FAILED ({duration:.2f}s)")
            return False
    except Exception as e:
        duration = time.time() - start_time
        print(f"💥 {name} ERROR: {e} ({duration:.2f}s)")
        return False


def main():
    """Run the complete local test pipeline with all test categories."""
    print("🚀 Starting Complete Smart Grid Table Test Pipeline")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Running ALL test categories for comprehensive coverage")
    
    start_time = time.time()
    tests = []
    
    print(f"\n{'🔵'*20} CORE FUNCTIONALITY TESTS {'🔵'*20}")
    
    # Test 1: Original Unit Tests
    tests.append(run_command(
        "Original Unit Tests",
        [sys.executable, "test/run_tests.py"],
        "Running original unit tests (binary encoding, model segmentation)"
    ))
    
    # Test 2: Pandapower Tests
    tests.append(run_command(
        "Pandapower Tests", 
        [sys.executable, "test/test_pandapower_implementation.py"],
        "Testing Pandapower implementation and network functionality"
    ))
    
    print(f"\n{'🟢'*20} REFACTORED MODULE TESTS {'🟢'*20}")
    
    # Test 3: Basic Integration Tests
    tests.append(run_command(
        "Refactored Module Integration Tests",
        [sys.executable, "test_refactored_app.py"],
        "Testing basic integration of refactored modules"
    ))
    
    # Test 4: Comprehensive Tests
    tests.append(run_command(
        "Comprehensive Tests",
        [sys.executable, "test/test_refactored_comprehensive.py"],
        "Running comprehensive tests (error handling, edge cases, performance)"
    ))
    
    print(f"\n{'🚀'*20} PERFORMANCE & LOAD TESTS {'🚀'*20}")
    
    # Test 5: Performance Tests
    tests.append(run_command(
        "Performance Tests",
        [sys.executable, "test/test_performance_advanced.py"],
        "Testing memory usage, concurrency, load handling, and scalability"
    ))
    
    print(f"\n{'🔒'*20} SECURITY & VALIDATION TESTS {'🔒'*20}")
    
    # Test 6: Security Tests
    tests.append(run_command(
        "Security Tests",
        [sys.executable, "test/test_security_validation.py"],
        "Testing input validation, injection prevention, and security boundaries"
    ))
    
    print(f"\n{'⚡'*20} SYSTEM INTEGRATION TESTS {'⚡'*20}")
    
    # Test 7: Application Smoke Test
    print(f"\n{'='*80}")
    print(f"🧪 Application Smoke Test")
    print(f"📝 Testing basic application startup and imports")
    print(f"{'='*80}")
    
    smoke_start = time.time()
    try:
        from main_controller import MainApplicationController
        from app_state import AppState
        
        app_state = AppState()
        app_state.simulation_mode = True
        controller = MainApplicationController()
        controller.app_state.request_shutdown()
        
        smoke_duration = time.time() - smoke_start
        print(f"✅ Application Smoke Test PASSED ({smoke_duration:.2f}s)")
        tests.append(True)
    except Exception as e:
        smoke_duration = time.time() - smoke_start
        print(f"❌ Application Smoke Test FAILED: {e} ({smoke_duration:.2f}s)")
        tests.append(False)
    
    # Test 8: PyTest Discovery
    tests.append(run_command(
        "PyTest Discovery",
        [sys.executable, "-m", "pytest", "test/", "-v", "--tb=short"],
        "Running all tests via pytest discovery"
    ))
    
    # Summary
    total_duration = time.time() - start_time
    passed = sum(tests)
    total = len(tests)
    
    print(f"\n{'='*80}")
    print(f"📊 COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    print(f"🕐 Total Duration: {total_duration:.2f}s")
    print(f"📈 Success Rate: {(passed/total*100):.1f}%")
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total-passed}/{total}")
    
    print(f"\n📋 DETAILED BREAKDOWN BY CATEGORY:")
    test_categories = [
        ("Core", "Original Unit Tests"),
        ("Core", "Pandapower Tests"), 
        ("Refactored", "Integration Tests"),
        ("Refactored", "Comprehensive Tests"),
        ("Performance", "Performance Tests"),
        ("Security", "Security Tests"),
        ("System", "Application Smoke Test"),
        ("Discovery", "PyTest Discovery")
    ]
    
    category_stats = {}
    for i, ((category, name), result) in enumerate(zip(test_categories, tests)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} [{category:12}] {name}")
        
        if category not in category_stats:
            category_stats[category] = {"passed": 0, "total": 0}
        category_stats[category]["total"] += 1
        if result:
            category_stats[category]["passed"] += 1
    
    print(f"\n📈 CATEGORY SUMMARY:")
    for category, stats in category_stats.items():
        rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"  {category:12}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
    
    print(f"\n🧪 TEST COVERAGE INCLUDES:")
    print(f"  ✅ Core Functionality (Binary encoding, Pandapower calculations)")
    print(f"  ✅ Refactored Architecture (AppState, ConfigLoader, MQTTManager, CommandDispatcher)")
    print(f"  ✅ Error Handling & Edge Cases")
    print(f"  ✅ Performance & Scalability")
    print(f"  ✅ Memory Management & Concurrency")
    print(f"  ✅ Security & Input Validation")
    print(f"  ✅ Load Testing & Resource Management")
    print(f"  ✅ System Integration & Smoke Testing")
    
    print(f"\n{'='*80}")
    if all(tests):
        print("🎉 ALL TESTS PASSED! The refactored application is FULLY VALIDATED!")
        print("🚀 Ready for production deployment with comprehensive test coverage!")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the results above.")
        print("🔍 Check specific test output for detailed failure information.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 