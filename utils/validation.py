"""
Input validation and error handling utilities.
Provides centralized validation functions for improved security and robustness.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_table_section_name(section_name: str) -> bool:
    """
    Validate a table section name.
    
    Args:
        section_name: The section name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(section_name, str):
        return False
    
    # Allow table names like "Table1", "table_2", "section-3"
    pattern = r'^[a-zA-Z][a-zA-Z0-9_-]*$'
    return bool(re.match(pattern, section_name)) and len(section_name) <= 50


def validate_module_id(module_id: Union[str, int]) -> bool:
    """
    Validate a module ID.
    
    Args:
        module_id: The module ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if isinstance(module_id, int):
        return 0 <= module_id <= 999999  # Reasonable range
    
    if isinstance(module_id, str):
        # Allow alphanumeric module IDs
        pattern = r'^[a-zA-Z0-9_-]{1,20}$'
        return bool(re.match(pattern, module_id))
    
    return False


def validate_calculation_mode(mode: str) -> bool:
    """
    Validate a calculation mode.
    
    Args:
        mode: The calculation mode to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(mode, str):
        return False
    
    valid_modes = {"pf", "lpf", "lopf", "optimize"}
    return mode.lower() in valid_modes


def validate_direction(direction: str) -> bool:
    """
    Validate a direction parameter (for photovoltaic panels).
    
    Args:
        direction: The direction to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(direction, str):
        return False
    
    valid_directions = {"south", "east", "west", "north", "none", ""}
    return direction.lower() in valid_directions


def validate_voltage_level(voltage_level: str) -> bool:
    """
    Validate a voltage level parameter.
    
    Args:
        voltage_level: The voltage level to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(voltage_level, str):
        return False
    
    valid_levels = {"lv", "mv", "hv", "low", "medium", "high"}
    return voltage_level.lower() in valid_levels


def validate_scenario_name(scenario_name: str) -> bool:
    """
    Validate a scenario name.
    
    Args:
        scenario_name: The scenario name to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(scenario_name, str):
        return False
    
    # Allow reasonable scenario names
    pattern = r'^[a-zA-Z0-9_\-\s]{1,100}$'
    return bool(re.match(pattern, scenario_name))


def validate_file_path(file_path: str, must_exist: bool = True) -> bool:
    """
    Validate a file path.
    
    Args:
        file_path: The file path to validate
        must_exist: Whether the file must exist
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(file_path, str):
        return False
    
    try:
        path = Path(file_path)
        
        # Basic security check - no parent directory traversal
        if '..' in str(path):
            return False
        
        # Check if file exists if required
        if must_exist and not path.exists():
            return False
            
        return True
    except (ValueError, OSError):
        return False


def validate_json_data(data: str) -> Tuple[bool, Optional[Dict]]:
    """
    Validate and parse JSON data.
    
    Args:
        data: The JSON string to validate
        
    Returns:
        tuple: (is_valid, parsed_data_or_None)
    """
    if not isinstance(data, str):
        return False, None
    
    try:
        parsed = json.loads(data)
        return True, parsed
    except json.JSONDecodeError:
        return False, None


def validate_numeric_parameter(value: Any, min_val: Optional[float] = None, 
                             max_val: Optional[float] = None) -> bool:
    """
    Validate a numeric parameter.
    
    Args:
        value: The value to validate
        min_val: Minimum allowed value (inclusive)
        max_val: Maximum allowed value (inclusive)
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        num_value = float(value)
        
        if min_val is not None and num_value < min_val:
            return False
        
        if max_val is not None and num_value > max_val:
            return False
            
        return True
    except (ValueError, TypeError):
        return False


def validate_line_coordinates(table: int, line: int) -> bool:
    """
    Validate line coordinates.
    
    Args:
        table: Table number
        line: Line number
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(table, int) or not isinstance(line, int):
        return False
    
    # Assume reasonable limits
    return 1 <= table <= 6 and 0 <= line <= 100


def validate_command_arguments(command: str, args: List[str], 
                             expected_count: Optional[int] = None) -> bool:
    """
    Validate command arguments.
    
    Args:
        command: The command name
        args: List of arguments
        expected_count: Expected number of arguments (if any)
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(command, str) or not isinstance(args, list):
        return False
    
    # Basic command name validation
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', command):
        return False
    
    # Validate argument count if specified
    if expected_count is not None and len(args) != expected_count:
        return False
    
    # Validate individual arguments don't contain dangerous characters
    for arg in args:
        if not isinstance(arg, str):
            return False
        
        # Prevent shell injection attempts
        dangerous_chars = [';', '|', '&', '`', '$', '(', ')', '<', '>']
        if any(char in arg for char in dangerous_chars):
            return False
    
    return True


def sanitize_user_input(user_input: str, max_length: int = 1000) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        user_input: The input to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized input
    """
    if not isinstance(user_input, str):
        return ""
    
    # Truncate to max length
    sanitized = user_input[:max_length]
    
    # Remove or escape dangerous characters
    sanitized = re.sub(r'[<>&"\'\\]', '', sanitized)
    
    # Remove control characters except normal whitespace
    sanitized = ''.join(char for char in sanitized 
                       if ord(char) >= 32 or char in '\t\n\r')
    
    return sanitized.strip()


def validate_mqtt_message_type(message_type: str) -> bool:
    """
    Validate an MQTT message type.
    
    Args:
        message_type: The message type to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not isinstance(message_type, str):
        return False
    
    # Define allowed message types
    valid_types = {
        'SEND_SCENARIO_JSON', 'SEND_RESTRICTIONS', 'CHANGE_MODULE_PARAMETER',
        'SEND_ACTIVE_MODULES', 'SEND_SCENARIO_LIST', 'CHANGE_SCENARIO',
        'CHANGE_RESTRICTIONS', 'SEND_SNAPSHOTS', 'SEND_LINE_STATUSES',
        'CHANGE_LINE', 'PLACE_MODULE', 'REMOVE_MODULE', 'LOAD_SCENARIO',
        'MODULE_UPDATE', 'LINE_UPDATE', 'SCENARIO_UPDATE', 'ERROR'
    }
    
    return message_type in valid_types


class InputValidator:
    """Class-based validator for complex validation scenarios."""
    
    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode
        self.errors: List[str] = []
    
    def validate_scenario_change_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate a scenario change payload."""
        self.errors.clear()
        
        required_fields = ['scenario_name', 'is_static']
        for field in required_fields:
            if field not in payload:
                self.errors.append(f"Missing required field: {field}")
        
        if 'scenario_name' in payload:
            if not validate_scenario_name(payload['scenario_name']):
                self.errors.append("Invalid scenario name")
        
        if 'is_static' in payload:
            if not isinstance(payload['is_static'], bool):
                self.errors.append("is_static must be boolean")
        
        return len(self.errors) == 0
    
    def validate_line_change_payload(self, payload: Dict[str, Any]) -> bool:
        """Validate a line change payload."""
        self.errors.clear()
        
        required_fields = ['table', 'line', 'active']
        for field in required_fields:
            if field not in payload:
                self.errors.append(f"Missing required field: {field}")
        
        if 'table' in payload and 'line' in payload:
            try:
                table = int(payload['table'])
                line = int(payload['line'])
                if not validate_line_coordinates(table, line):
                    self.errors.append("Invalid table or line coordinates")
            except (ValueError, TypeError):
                self.errors.append("Table and line must be integers")
        
        if 'active' in payload:
            if not isinstance(payload['active'], bool):
                self.errors.append("active must be boolean")
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Get the list of validation errors."""
        return self.errors.copy()
    
    def clear_errors(self):
        """Clear the error list."""
        self.errors.clear() 