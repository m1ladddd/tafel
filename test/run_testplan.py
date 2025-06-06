#!/usr/bin/env python3
"""
Smart Grid Table Testplan Runner

This script implements the testplan execution according to the sprints defined
in the testplan document.

Sprint 3: Unit tests voor PandapowerNetworkBuilder en basisberekeningsfunctionaliteit
Sprint 4: Integratietests voor calculatoren en modelsegmentatie  
Sprint 5: Performancetests
Sprint 6: Systeemtests voor tafelsecties en MQTT-communicatie
Sprint 7: Energieverbruikstests en microgrid-functionaliteit
Sprint 8: End-to-end tests en stabiliteitsvalidatie
"""

import sys
import os
import logging
import argparse
import subprocess
import time
from datetime import datetime
from typing import List, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'testplan_execution_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)
logger = logging.getLogger(__name__)

class TestplanRunner:
    """
    Main runner class for executing the Smart Grid Table testplan
    """
    
    def __init__(self):
        self.test_results = {}
        self.current_sprint = None
        
    def run_sprint_3_unit_tests(self):
        """
        Sprint 3: Unit tests voor PandapowerNetworkBuilder en basisberekeningsfunctionaliteit
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 3: Unit Tests for PandapowerNetworkBuilder")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 3"
        
        test_files = [
            "test_pandapower_network.py",
            "test_pandapower_calculators.py",
            "test_pandapower_implementation.py"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def run_sprint_4_integration_tests(self):
        """
        Sprint 4: Integratietests voor calculatoren en modelsegmentatie
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 4: Integration Tests for Calculators and Model Segmentation")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 4"
        
        test_files = [
            "model_segmentation_test.py",
            "test_smart_grid_table_testplan.py::TestFunctionalityPandapowerComponents::test_pandapower_calculators_functionality",
            "test_smart_grid_table_testplan.py::TestFunctionalityPandapowerComponents::test_model_segmentation",
            "test_smart_grid_table_testplan.py::TestFunctionalityPandapowerComponents::test_thread_management"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def run_sprint_5_performance_tests(self):
        """
        Sprint 5: Performancetests
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 5: Performance Tests")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 5"
        
        test_files = [
            "test_performance_advanced.py",
            "test_smart_grid_table_testplan.py::TestNonFunctionalRequirements::test_performance_efficiency",
            "test_smart_grid_table_testplan.py::TestNonFunctionalRequirements::test_scalability_large_networks"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def run_sprint_6_system_tests(self):
        """
        Sprint 6: Systeemtests voor tafelsecties en MQTT-communicatie
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 6: System Tests for Table Sections and MQTT")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 6"
        
        test_files = [
            "test_mqtt_communication.py",
            "test_smart_grid_table_testplan.py::TestIntegrationEndToEnd::test_mqtt_communication_mock",
            "test_smart_grid_table_testplan.py::TestIntegrationEndToEnd::test_led_visualization_mock",
            "test_smart_grid_table_testplan.py::TestNonFunctionalRequirements::test_synchronization_multiple_sections"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def run_sprint_7_microgrid_tests(self):
        """
        Sprint 7: Energieverbruikstests en microgrid-functionaliteit
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 7: Energy Usage and Microgrid Functionality Tests")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 7"
        
        test_files = [
            "test_microgrid_functionality.py",
            "test_smart_grid_table_testplan.py::TestIntegrationEndToEnd::test_standalone_mode_functionality"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def run_sprint_8_stability_tests(self):
        """
        Sprint 8: End-to-end tests en stabiliteitsvalidatie
        """
        logger.info("="*60)
        logger.info("EXECUTING SPRINT 8: End-to-End and Stability Tests")
        logger.info("="*60)
        
        self.current_sprint = "Sprint 8"
        
        test_files = [
            "test_long_term_stability.py",
            "test_practical_stability.py",
            "test_smart_grid_table_testplan.py::TestNonFunctionalRequirements::test_reliability_stress",
            "test_refactored_comprehensive.py"
        ]
        
        results = self._run_test_files(test_files)
        self.test_results[self.current_sprint] = results
        
        return all(results.values())
    
    def _run_test_files(self, test_files: List[str]) -> Dict[str, bool]:
        """
        Run specified test files and return results
        """
        results = {}
        
        for test_file in test_files:
            logger.info(f"Running test: {test_file}")
            
            try:
                # Change to test directory
                test_dir = os.path.join(os.path.dirname(__file__))
                
                # Construct pytest command
                if "::" in test_file:
                    # Specific test method
                    cmd = ["python", "-m", "pytest", test_file, "-v", "-s"]
                else:
                    # Entire test file
                    test_path = os.path.join(test_dir, test_file)
                    if os.path.exists(test_path):
                        cmd = ["python", "-m", "pytest", test_path, "-v", "-s"]
                    else:
                        logger.warning(f"Test file not found: {test_path}")
                        results[test_file] = False
                        continue
                
                # Run the test
                start_time = time.time()
                result = subprocess.run(
                    cmd,
                    cwd=os.path.dirname(os.path.dirname(__file__)),  # Project root
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per test
                )
                execution_time = time.time() - start_time
                
                success = result.returncode == 0
                results[test_file] = success
                
                logger.info(f"Test {test_file}: {'PASSED' if success else 'FAILED'} "
                           f"(took {execution_time:.2f}s)")
                
                if not success:
                    logger.error(f"Test output for {test_file}:")
                    logger.error(result.stdout)
                    logger.error(result.stderr)
                
            except subprocess.TimeoutExpired:
                logger.error(f"Test {test_file} timed out after 5 minutes")
                results[test_file] = False
            except Exception as e:
                logger.error(f"Error running test {test_file}: {e}")
                results[test_file] = False
        
        return results
    
    def run_all_sprints(self):
        """
        Run all sprints in order
        """
        logger.info("STARTING COMPLETE TESTPLAN EXECUTION")
        logger.info("Following the sprint schedule from the testplan document")
        
        sprints = [
            self.run_sprint_3_unit_tests,
            self.run_sprint_4_integration_tests,
            self.run_sprint_5_performance_tests,
            self.run_sprint_6_system_tests,
            self.run_sprint_7_microgrid_tests,
            self.run_sprint_8_stability_tests
        ]
        
        overall_success = True
        
        for i, sprint_func in enumerate(sprints, 3):
            logger.info(f"\n{'='*20} SPRINT {i} {'='*20}")
            
            try:
                sprint_success = sprint_func()
                if not sprint_success:
                    overall_success = False
                    logger.error(f"Sprint {i} had failing tests")
                else:
                    logger.info(f"Sprint {i} completed successfully")
                    
            except Exception as e:
                logger.error(f"Sprint {i} failed with exception: {e}")
                overall_success = False
            
            # Short break between sprints
            time.sleep(2)
        
        self._generate_final_report(overall_success)
        
        return overall_success
    
    def _generate_final_report(self, overall_success: bool):
        """
        Generate final testplan execution report
        """
        logger.info("\n" + "="*60)
        logger.info("TESTPLAN EXECUTION FINAL REPORT")
        logger.info("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for sprint, results in self.test_results.items():
            sprint_total = len(results)
            sprint_passed = sum(1 for success in results.values() if success)
            
            total_tests += sprint_total
            passed_tests += sprint_passed
            
            logger.info(f"{sprint}: {sprint_passed}/{sprint_total} tests passed")
            
            for test_name, success in results.items():
                status = "✓ PASS" if success else "✗ FAIL"
                logger.info(f"  {status}: {test_name}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\nOVERALL RESULTS:")
        logger.info(f"Total tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {total_tests - passed_tests}")
        logger.info(f"Success rate: {success_rate:.1f}%")
        
        if overall_success and success_rate >= 80:
            logger.info("\n🎉 TESTPLAN EXECUTION SUCCESSFUL!")
            logger.info("The Pandapower implementation meets the testplan criteria.")
        else:
            logger.error("\n❌ TESTPLAN EXECUTION FAILED!")
            logger.error("Some tests failed or success rate below 80%.")
            logger.error("Review the failed tests and address issues before deployment.")
        
        # Testplan success criteria check
        logger.info("\nTESTPLAN CRITERIA EVALUATION:")
        logger.info("✓ Functional equivalence testing completed")
        logger.info("✓ Performance testing completed")
        logger.info("✓ Stability testing completed")
        logger.info("✓ MQTT communication testing completed")
        logger.info("✓ Microgrid functionality testing completed")
        
        return overall_success

def main():
    """
    Main entry point for testplan execution
    """
    parser = argparse.ArgumentParser(description="Smart Grid Table Testplan Runner")
    parser.add_argument(
        "--sprint", 
        type=int, 
        choices=[3, 4, 5, 6, 7, 8], 
        help="Run specific sprint (3-8)"
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Run all sprints in sequence"
    )
    
    args = parser.parse_args()
    
    runner = TestplanRunner()
    
    if args.sprint:
        sprint_methods = {
            3: runner.run_sprint_3_unit_tests,
            4: runner.run_sprint_4_integration_tests,
            5: runner.run_sprint_5_performance_tests,
            6: runner.run_sprint_6_system_tests,
            7: runner.run_sprint_7_microgrid_tests,
            8: runner.run_sprint_8_stability_tests
        }
        
        success = sprint_methods[args.sprint]()
        sys.exit(0 if success else 1)
    
    elif args.all or True:  # Default to running all
        success = runner.run_all_sprints()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main() 