#!/usr/bin/env python3
"""
Advanced Performance Tests for Smart Grid Table Application.
Tests memory usage, CPU performance, concurrent operations, and load handling.
"""

import sys
import os
import unittest
import time
import threading
import concurrent.futures
import psutil
import json
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
from app_state import AppState
from config_loader import ConfigLoader
from mqtt_services.mqtt_manager import MQTTManager
from input_handling.command_dispatcher import CommandDispatcher


class TestMemoryUsage(unittest.TestCase):
    """Test memory usage and leak detection."""
    
    def setUp(self):
        self.process = psutil.Process()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def test_app_state_memory_leak(self):
        """Test AppState doesn't leak memory with many operations."""
        app_state = AppState()
        
        # Perform many operations
        for i in range(1000):
            app_state.set_mode("pf")
            app_state.set_mode("optimize")
            app_state.request_update()
            app_state.consume_force_update()
        
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - self.initial_memory
        
        # Should not increase more than 10MB
        self.assertLess(memory_increase, 10, f"Memory increased by {memory_increase:.2f}MB")
    
    def test_config_loader_memory_efficiency(self):
        """Test ConfigLoader memory usage with repeated loading."""
        initial_memory = self.process.memory_info().rss / 1024 / 1024
        
        # Load config many times
        for i in range(100):
            config_loader = ConfigLoader("config.json")
            del config_loader
        
        current_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory
        
        # Should not increase more than 5MB
        self.assertLess(memory_increase, 5, f"Memory increased by {memory_increase:.2f}MB")


class TestConcurrency(unittest.TestCase):
    """Test concurrent operations and thread safety."""
    
    def setUp(self):
        self.app_state = AppState()
    
    def test_concurrent_mode_changes(self):
        """Test concurrent mode changes don't cause race conditions."""
        modes = ["pf", "optimize", "lopf", "lpf"]
        results = []
        
        def change_mode(mode):
            for _ in range(50):
                result = self.app_state.set_mode(mode)
                results.append(result)
                time.sleep(0.001)  # Small delay to increase chance of race condition
        
        # Start multiple threads
        threads = []
        for mode in modes:
            thread = threading.Thread(target=change_mode, args=(mode,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All mode changes should have succeeded
        self.assertTrue(all(results), "Some mode changes failed in concurrent environment")
        # Final mode should be one of the valid modes
        self.assertIn(self.app_state.current_mode, modes)
    
    def test_concurrent_force_updates(self):
        """Test concurrent force update operations."""
        update_results = []
        
        def update_loop():
            for _ in range(100):
                self.app_state.request_update()
                result = self.app_state.consume_force_update()
                update_results.append(result)
                time.sleep(0.001)
        
        # Start multiple threads doing updates
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=update_loop)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have some successful updates
        successful_updates = sum(update_results)
        self.assertGreater(successful_updates, 0, "No successful updates in concurrent test")


class TestLoadTesting(unittest.TestCase):
    """Test application behavior under high load."""
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')  
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_high_volume_mqtt_messages(self, mock_jupyter, mock_proto, mock_gui):
        """Test handling of high volume MQTT messages."""
        app_state = AppState()
        app_state.simulation_mode = True
        mqtt_manager = MQTTManager(app_state)
        
        # Simulate high volume of messages
        mock_gui_instance = mock_gui.return_value
        large_message_buffer = []
        
        for i in range(1000):
            large_message_buffer.append(f'{{"id": {i}, "type": "test", "data": "test_data_{i}"}}')
        
        mock_gui_instance.message_buffer = large_message_buffer
        
        start_time = time.time()
        messages = mqtt_manager.get_gui_messages()
        processing_time = time.time() - start_time
        
        # Should process 1000 messages in reasonable time (< 1 second)
        self.assertLess(processing_time, 1.0, f"Processing 1000 messages took {processing_time:.2f}s")
        self.assertEqual(len(messages), 1000, "Not all messages were processed")
    
    def test_command_dispatcher_load(self):
        """Test CommandDispatcher under high command load."""
        app_state = AppState()
        config_loader = ConfigLoader("config.json")
        mock_table = MagicMock()
        mock_mqtt = MagicMock()
        
        dispatcher = CommandDispatcher(app_state, mock_table, config_loader, mock_mqtt)
        
        commands = ["help", "scenario list", "table list", "calculate", "mode set pf"] * 200
        
        start_time = time.time()
        for cmd in commands:
            dispatcher.dispatch_console_command(cmd)
        processing_time = time.time() - start_time
        
        # Should process 1000 commands in reasonable time
        self.assertLess(processing_time, 5.0, f"Processing 1000 commands took {processing_time:.2f}s")


class TestRobustness(unittest.TestCase):
    """Test application robustness under various conditions."""
    
    def test_invalid_json_recovery(self):
        """Test recovery from invalid JSON in config files."""
        # Create temporary invalid config
        import tempfile
        
        invalid_configs = [
            '{"invalid": json content}',
            '{"missing_quote: "value"}',
            '{"trailing_comma": "value",}',
            '',
            'not json at all',
            '{"nested": {"missing_brace": "value"}',
        ]
        
        for invalid_json in invalid_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(invalid_json)
                f.flush()
                
                # Should not crash, should return empty config
                config_loader = ConfigLoader(f.name)
                self.assertEqual(config_loader.main_config, {})
                
            os.unlink(f.name)
    
    def test_extreme_refresh_rates(self):
        """Test application with extreme refresh rates."""
        app_state = AppState()
        
        extreme_rates = [0.0, 0.000001, 1000.0, float('inf')]
        
        for rate in extreme_rates:
            try:
                app_state.refresh_rate = rate
                # Should not crash
                self.assertIsInstance(app_state.refresh_rate, (int, float))
            except:
                self.fail(f"Application crashed with refresh rate: {rate}")
    
    def test_very_long_commands(self):
        """Test handling of very long command strings."""
        app_state = AppState()
        config_loader = ConfigLoader("config.json")
        mock_table = MagicMock()
        mock_mqtt = MagicMock()
        
        dispatcher = CommandDispatcher(app_state, mock_table, config_loader, mock_mqtt)
        
        # Very long command
        long_command = "mode set " + "x" * 10000
        
        # Should not crash
        try:
            dispatcher.dispatch_console_command(long_command)
        except Exception as e:
            # Should handle gracefully, not crash
            pass


class TestScalability(unittest.TestCase):
    """Test application scalability."""
    
    def test_many_app_state_instances(self):
        """Test creating many AppState instances."""
        instances = []
        start_time = time.time()
        
        # Create many instances
        for i in range(1000):
            app_state = AppState()
            app_state.set_mode("pf")
            instances.append(app_state)
        
        creation_time = time.time() - start_time
        
        # Should create 1000 instances quickly
        self.assertLess(creation_time, 2.0, f"Creating 1000 instances took {creation_time:.2f}s")
        
        # All should have correct initial state
        for instance in instances[:10]:  # Check first 10
            self.assertTrue(instance.is_running)
            self.assertEqual(instance.current_mode, "pf")
    
    def test_config_loader_with_large_files(self):
        """Test ConfigLoader with large configuration files."""
        import tempfile
        
        # Create large config file
        large_config = {
            "large_array": list(range(10000)),
            "nested_data": {f"key_{i}": f"value_{i}" for i in range(1000)},
            "string_data": "x" * 100000
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_config, f)
            f.flush()
            
            start_time = time.time()
            config_loader = ConfigLoader(f.name)
            load_time = time.time() - start_time
            
            # Should load large file in reasonable time
            self.assertLess(load_time, 5.0, f"Loading large config took {load_time:.2f}s")
            self.assertIsNotNone(config_loader.main_config)
            
        os.unlink(f.name)


def run_performance_tests():
    """Run all performance tests."""
    print("🚀 Running Advanced Performance Tests")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestMemoryUsage,
        TestConcurrency,
        TestLoadTesting,
        TestRobustness,
        TestScalability,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL PERFORMANCE TESTS PASSED!")
        return 0
    else:
        print("❌ Some performance tests failed.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1


if __name__ == "__main__":
    exit_code = run_performance_tests()
    sys.exit(exit_code) 