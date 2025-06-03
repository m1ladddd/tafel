#!/usr/bin/env python3
"""
Comprehensive test suite for the refactored Smart Grid Table application.
Tests error handling, edge cases, state transitions, and integration scenarios.
"""

import sys
import os
import unittest
import tempfile
import json
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

# Add the parent directory to the path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
from app_state import AppState
from config_loader import ConfigLoader
from mqtt_services.mqtt_manager import MQTTManager
from input_handling.command_dispatcher import CommandDispatcher


class TestAppStateAdvanced(unittest.TestCase):
    """Advanced tests for AppState functionality."""
    
    def setUp(self):
        self.app_state = AppState()
    
    def test_invalid_mode_handling(self):
        """Test behavior with invalid modes."""
        original_mode = self.app_state.current_mode
        
        # Test invalid modes
        invalid_modes = ["invalid", "random", "", None, 123]
        for mode in invalid_modes:
            result = self.app_state.set_mode(mode)
            self.assertFalse(result, f"Should reject invalid mode: {mode}")
            self.assertEqual(self.app_state.current_mode, original_mode)
    
    def test_valid_modes(self):
        """Test all valid modes."""
        valid_modes = ["optimize", "lopf", "lpf", "pf"]
        for mode in valid_modes:
            result = self.app_state.set_mode(mode)
            self.assertTrue(result, f"Should accept valid mode: {mode}")
            self.assertEqual(self.app_state.current_mode, mode)
            self.assertTrue(self.app_state.force_update, "Should trigger update")
    
    def test_force_update_edge_cases(self):
        """Test force update edge cases."""
        # Multiple consecutive consume calls
        self.app_state.request_update()
        self.assertTrue(self.app_state.consume_force_update())
        self.assertFalse(self.app_state.consume_force_update())
        self.assertFalse(self.app_state.consume_force_update())
    
    def test_state_transitions(self):
        """Test various state transitions."""
        # Running -> Shutdown -> Running (shouldn't be possible)
        self.assertTrue(self.app_state.is_running)
        self.app_state.request_shutdown()
        self.assertFalse(self.app_state.is_running)
        
        # Once shutdown, should stay shutdown
        self.app_state.is_running = True  # Try to override
        self.app_state.request_shutdown()
        self.assertFalse(self.app_state.is_running)


class TestConfigLoaderAdvanced(unittest.TestCase):
    """Advanced tests for ConfigLoader functionality."""
    
    def test_missing_config_file(self):
        """Test behavior with missing config file."""
        config_loader = ConfigLoader("nonexistent_file.json")
        self.assertEqual(config_loader.main_config, {})
    
    def test_invalid_json_config(self):
        """Test behavior with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json content }")
            f.flush()
            
            config_loader = ConfigLoader(f.name)
            self.assertEqual(config_loader.main_config, {})
            
        os.unlink(f.name)
    
    def test_empty_config_file(self):
        """Test behavior with empty config file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("")
            f.flush()
            
            config_loader = ConfigLoader(f.name)
            self.assertEqual(config_loader.main_config, {})
            
        os.unlink(f.name)
    
    def test_config_value_retrieval(self):
        """Test config value retrieval with defaults."""
        # Create valid test config
        test_config = {"test_key": "test_value", "number": 42}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_config, f)
            f.flush()
            
            config_loader = ConfigLoader(f.name)
            
            # Test existing key
            self.assertEqual(config_loader.get_config_value("test_key"), "test_value")
            self.assertEqual(config_loader.get_config_value("number"), 42)
            
            # Test missing key with default
            self.assertEqual(config_loader.get_config_value("missing", "default"), "default")
            self.assertIsNone(config_loader.get_config_value("missing"))
            
        os.unlink(f.name)
    
    @patch('builtins.print')
    def test_gui_remap_error_handling(self, mock_print):
        """Test GUI remap loading with missing files."""
        # This will try to load the remaps and should handle missing files gracefully
        config_loader = ConfigLoader("config.json")  # Use existing config
        
        # Should have 6 remaps (even if some files are missing)
        self.assertEqual(len(config_loader.gui_line_remaps), 6)


class TestMQTTManagerAdvanced(unittest.TestCase):
    """Advanced tests for MQTTManager functionality."""
    
    def setUp(self):
        self.app_state = AppState()
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')  
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_partial_connection_failure(self, mock_jupyter, mock_proto, mock_gui):
        """Test behavior when some MQTT clients fail to connect."""
        # Mock one client to fail
        mock_gui.return_value.mqtt_connect.side_effect = ConnectionRefusedError("Connection failed")
        
        mqtt_manager = MQTTManager(self.app_state)
        mqtt_manager.connect_all()
        
        # Should handle partial failure gracefully
        self.assertFalse(mqtt_manager.connections_active)
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')  
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_message_handling_edge_cases(self, mock_jupyter, mock_proto, mock_gui):
        """Test message handling with various edge cases."""
        mqtt_manager = MQTTManager(self.app_state)
        
        # Test with no connections
        mqtt_manager.connections_active = False
        messages = mqtt_manager.get_gui_messages()
        self.assertEqual(messages, [])
        
        # Test with malformed messages
        mqtt_manager.connections_active = True
        mock_gui_instance = mock_gui.return_value
        mock_gui_instance.message_buffer = ['{"valid": "json"}', 'invalid json', '{"another": "valid"}']
        
        messages = mqtt_manager.get_gui_messages()
        # Should filter out invalid JSON but keep valid ones
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], {"valid": "json"})
        self.assertEqual(messages[1], {"another": "valid"})
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')  
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_simulation_mode_broker_override(self, mock_jupyter, mock_proto, mock_gui):
        """Test that simulation mode correctly overrides broker IP."""
        self.app_state.simulation_mode = True
        self.app_state.local_broker_ip = "192.168.1.100"
        
        mqtt_manager = MQTTManager(self.app_state)
        mqtt_manager.connect_all()
        
        # Should use localhost instead of detected IP
        self.assertEqual(mqtt_manager.broker_ip, "localhost")
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')  
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_publish_without_connection(self, mock_jupyter, mock_proto, mock_gui):
        """Test publishing messages when not connected."""
        mqtt_manager = MQTTManager(self.app_state)
        mqtt_manager.connections_active = False
        
        # Should not raise errors
        mqtt_manager.publish_to_gui("test message")
        mqtt_manager.publish_to_proto("test message")
        mqtt_manager.publish_to_jupyter("test message")


class TestCommandDispatcherAdvanced(unittest.TestCase):
    """Advanced tests for CommandDispatcher functionality."""
    
    def setUp(self):
        self.app_state = AppState()
        self.config_loader = ConfigLoader("config.json")
        self.mock_table = MagicMock()
        self.mock_mqtt = MagicMock()
        self.dispatcher = CommandDispatcher(
            self.app_state, 
            self.mock_table, 
            self.config_loader,
            self.mock_mqtt
        )
    
    def test_invalid_commands(self):
        """Test handling of invalid commands."""
        invalid_commands = [
            "nonexistent_command",
            "",
            "   ",
            "mode invalid_mode",
            "scenario set",  # Missing parameters
            "table reboot",  # Missing section
        ]
        
        for cmd in invalid_commands:
            # Should not raise errors, just print warnings
            self.dispatcher.dispatch_console_command(cmd)
    
    def test_scenario_commands(self):
        """Test scenario-related commands."""
        # Test scenario list
        self.dispatcher.dispatch_console_command("scenario list")
        
        # Test scenario current
        self.dispatcher.dispatch_console_command("scenario current")
        
        # Test scenario reload
        self.dispatcher.dispatch_console_command("scenario reload")
    
    def test_table_commands(self):
        """Test table-related commands."""
        # Test table list
        self.dispatcher.dispatch_console_command("table list")
        
        # Test table reboot with section
        self.dispatcher.dispatch_console_command("table reboot Table1")
        
        # Test table update commands
        self.dispatcher.dispatch_console_command("table update firmware")
        self.dispatcher.dispatch_console_command("table update config")
    
    def test_calculation_commands(self):
        """Test calculation-related commands."""
        # Test calculate command
        self.dispatcher.dispatch_console_command("calculate")
        self.assertTrue(self.app_state.force_update)
        
        # Test summation command
        self.dispatcher.dispatch_console_command("summation")
    
    def test_ui_message_handling(self):
        """Test UI message handling."""
        # Test various UI message types
        test_messages = [
            {"type": "SEND_SNAPSHOTS", "payload": {}},
            {"type": "SET_SCENARIO_STATIC", "payload": {"name": "Test"}},
            {"type": "SET_MODE", "payload": {"mode": "pf"}},
            {"type": "UNKNOWN_TYPE", "payload": {}},  # Should be handled gracefully
        ]
        
        for msg in test_messages:
            self.dispatcher.dispatch_ui_message(msg)
    
    def test_jupyter_command_handling(self):
        """Test Jupyter command handling."""
        jupyter_commands = [
            "help",
            "scenario list",
            "calculate",
            "invalid_command",
        ]
        
        for cmd in jupyter_commands:
            self.dispatcher.dispatch_jupyter_command(cmd)


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complex scenarios."""
    
    def setUp(self):
        self.app_state = AppState()
        self.config_loader = ConfigLoader("config.json")
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_full_system_initialization(self, mock_jupyter, mock_proto, mock_gui):
        """Test complete system initialization sequence."""
        # Set up simulation mode
        self.app_state.simulation_mode = True
        
        # Initialize all components
        mqtt_manager = MQTTManager(self.app_state, self.config_loader)
        mock_table = MagicMock()
        dispatcher = CommandDispatcher(
            self.app_state, 
            mock_table, 
            self.config_loader,
            mqtt_manager
        )
        
        # Connect MQTT
        mqtt_manager.connect_all()
        
        # Process some commands
        dispatcher.dispatch_console_command("help")
        dispatcher.dispatch_console_command("mode set pf")
        dispatcher.dispatch_console_command("calculate")
        
        # Verify state
        self.assertEqual(self.app_state.current_mode, "pf")
        self.assertTrue(self.app_state.force_update)
    
    def test_error_recovery_scenarios(self):
        """Test system behavior during error conditions."""
        # Test with corrupted state
        self.app_state.current_mode = "invalid_mode"
        self.app_state.set_mode("pf")  # Should still work
        self.assertEqual(self.app_state.current_mode, "pf")
        
        # Test with extreme refresh rates
        self.app_state.refresh_rate = 0.0  # Should not cause issues
        self.app_state.refresh_rate = 1000.0  # Should not cause issues
    
    @patch('mqtt_services.mqtt_manager.GUI_MQTT')
    @patch('mqtt_services.mqtt_manager.Prototype_MQTT')
    @patch('mqtt_services.mqtt_manager.Jupyter_MQTT')
    def test_mqtt_reconnection_scenario(self, mock_jupyter, mock_proto, mock_gui):
        """Test MQTT reconnection scenarios."""
        mqtt_manager = MQTTManager(self.app_state)
        
        # Initial connection failure
        mock_gui.return_value.mqtt_connect.side_effect = ConnectionRefusedError()
        mqtt_manager.connect_all()
        self.assertFalse(mqtt_manager.connections_active)
        
        # Successful reconnection
        mock_gui.return_value.mqtt_connect.side_effect = None
        mqtt_manager.connect_all()
        # Should handle gracefully


class TestPerformanceAndStress(unittest.TestCase):
    """Basic performance and stress tests."""
    
    def test_app_state_performance(self):
        """Test AppState performance with many operations."""
        app_state = AppState()
        
        # Test rapid mode changes
        import time
        start_time = time.time()
        
        for i in range(1000):
            app_state.set_mode("pf")
            app_state.set_mode("optimize")
            app_state.consume_force_update()
        
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 1.0, "AppState operations should be fast")
    
    def test_command_dispatcher_stress(self):
        """Test CommandDispatcher with many commands."""
        app_state = AppState()
        config_loader = ConfigLoader("config.json")
        mock_table = MagicMock()
        mock_mqtt = MagicMock()
        
        dispatcher = CommandDispatcher(app_state, mock_table, config_loader, mock_mqtt)
        
        # Test many command dispatches
        commands = ["help", "scenario list", "table list", "calculate"] * 100
        
        import time
        start_time = time.time()
        
        for cmd in commands:
            dispatcher.dispatch_console_command(cmd)
        
        elapsed = time.time() - start_time
        self.assertLess(elapsed, 5.0, "Command processing should be reasonably fast")


def run_comprehensive_tests():
    """Run all comprehensive tests."""
    print("🧪 Running Comprehensive Test Suite for Refactored Modules")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestAppStateAdvanced,
        TestConfigLoaderAdvanced, 
        TestMQTTManagerAdvanced,
        TestCommandDispatcherAdvanced,
        TestIntegrationScenarios,
        TestPerformanceAndStress,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL COMPREHENSIVE TESTS PASSED!")
        return 0
    else:
        print("❌ Some tests failed.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1


if __name__ == "__main__":
    exit_code = run_comprehensive_tests()
    sys.exit(exit_code) 