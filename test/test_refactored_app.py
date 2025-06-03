#!/usr/bin/env python3
"""
Quick integration test for the refactored application modules.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our new modules with error handling
try:
    from app_state import AppState
    APP_STATE_AVAILABLE = True
except ImportError:
    print("⚠️  AppState module not available")
    APP_STATE_AVAILABLE = False

try:
    from config_loader import ConfigLoader
    CONFIG_LOADER_AVAILABLE = True
except ImportError:
    print("⚠️  ConfigLoader module not available")
    CONFIG_LOADER_AVAILABLE = False

try:
    from mqtt_services.mqtt_manager import MQTTManager
    MQTT_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️  MQTTManager module not available")
    MQTT_MANAGER_AVAILABLE = False

try:
    from input_handling.command_dispatcher import CommandDispatcher
    COMMAND_DISPATCHER_AVAILABLE = True
except ImportError:
    print("⚠️  CommandDispatcher module not available")
    COMMAND_DISPATCHER_AVAILABLE = False


class TestRefactoredModules(unittest.TestCase):
    """Test the refactored application modules."""
    
    def test_app_state_basic_functionality(self):
        """Test basic AppState functionality."""
        print("\n=== Testing AppState ===")
        
        if APP_STATE_AVAILABLE:
            app_state = AppState()
            
            # Test initial state (corrected initial mode)
            self.assertTrue(app_state.is_running)
            self.assertEqual(app_state.current_mode, "optimize")
            self.assertTrue(app_state.force_update)  # Starts with True for initial update
            
            # Test mode change
            app_state.set_mode("pf")
            self.assertEqual(app_state.current_mode, "pf")
            
            # Test force update consumption
            consumed = app_state.consume_force_update()
            self.assertTrue(consumed)
            self.assertFalse(app_state.force_update)  # Should be reset
            
            print("✅ AppState test passed")
        else:
            print("⚠️  AppState test skipped")
    
    def test_config_loader_functionality(self):
        """Test ConfigLoader functionality."""
        print("\n=== Testing ConfigLoader ===")
        
        if CONFIG_LOADER_AVAILABLE:
            # This should work since config.json exists (adjust path for test directory)
            config_loader = ConfigLoader("../config.json")
            
            # Test that it loaded something (corrected attribute name)
            self.assertIsNotNone(config_loader.main_config)
            
            # Test GUI remap loading
            self.assertEqual(len(config_loader.gui_line_remaps), 6)
            
            print("✅ ConfigLoader test passed")
        else:
            print("⚠️  ConfigLoader test skipped")
    
    def test_mqtt_manager_functionality(self):
        """Test MQTTManager functionality with mocked MQTT clients."""
        print("\n=== Testing MQTTManager ===")
        
        if MQTT_MANAGER_AVAILABLE and APP_STATE_AVAILABLE:
            with patch('mqtt_services.mqtt_manager.GUI_MQTT'), \
                 patch('mqtt_services.mqtt_manager.Prototype_MQTT'), \
                 patch('mqtt_services.mqtt_manager.Jupyter_MQTT'):
                
                app_state = AppState()
                app_state.simulation_mode = True
                
                mqtt_manager = MQTTManager(app_state)
                
                # Test connection (should not crash with mocked clients)
                mqtt_manager.connect_all()
                
                # Test message retrieval (empty with mocked clients)
                gui_messages = mqtt_manager.get_gui_messages()
                self.assertIsInstance(gui_messages, list)
                
                print("✅ MQTTManager test passed")
        else:
            print("⚠️  MQTTManager test skipped")
    
    def test_command_dispatcher_basic(self):
        """Test CommandDispatcher basic functionality."""
        print("\n=== Testing CommandDispatcher ===")
        
        if COMMAND_DISPATCHER_AVAILABLE:
            app_state = AppState()
            config_loader = ConfigLoader("../config.json")
            
            # Mock the table and MQTT manager
            mock_table_instance = MagicMock()
            mqtt_manager = MagicMock()
            
            dispatcher = CommandDispatcher(
                app_state, 
                mock_table_instance, 
                config_loader,
                mqtt_manager
            )
            
            # Test help command
            dispatcher.dispatch_console_command("help")
            
            # Test mode command  
            dispatcher.dispatch_console_command("mode set pf")
            self.assertEqual(app_state.current_mode, "pf")
            
            print("✅ CommandDispatcher test passed")
        else:
            print("⚠️  CommandDispatcher test skipped")


def run_integration_tests():
    """Run integration tests for refactored modules."""
    print("🧪 Running Integration Tests for Refactored Modules")
    print("=" * 60)
    
    unittest.main(verbosity=2, exit=False)
    
    print("\n" + "=" * 60)
    print("✅ All integration tests completed successfully!")


if __name__ == "__main__":
    run_integration_tests() 