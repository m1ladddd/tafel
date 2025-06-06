"""
MQTT utility functions and helpers.
Contains common functions used by various MQTT clients.
"""

import json
import time
import socket
from typing import Dict, List, Any, Optional, Union
from datetime import datetime


def validate_mqtt_message(message: Union[str, Dict[str, Any]]) -> bool:
    """
    Validate if a message is a proper MQTT message format.
    
    Args:
        message: The message to validate (string or dict)
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if isinstance(message, str):
            # Try to parse as JSON
            parsed = json.loads(message)
            return isinstance(parsed, dict)
        elif isinstance(message, dict):
            return True
        else:
            return False
    except (json.JSONDecodeError, TypeError):
        return False


def format_gui_message(message_type: str, payload: Dict[str, Any]) -> str:
    """
    Format a message for the GUI MQTT client.
    
    Args:
        message_type: The type of message (e.g., 'SCENARIO_JSON', 'LINE_UPDATE')
        payload: The message payload
        
    Returns:
        str: JSON-formatted message string
    """
    message = {
        'type': message_type,
        'payload': payload,
        'timestamp': datetime.now().isoformat()
    }
    return json.dumps(message)


def format_jupyter_message(data: Any) -> str:
    """
    Format a message for the Jupyter MQTT client.
    
    Args:
        data: The data to send (will be JSON-serialized)
        
    Returns:
        str: JSON-formatted message string
    """
    try:
        if hasattr(data, 'to_json'):
            # Handle pandas DataFrames
            return data.to_json()
        else:
            return json.dumps(data)
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable data
        return json.dumps({"error": f"Could not serialize data: {str(e)}"})


def format_prototype_message(direction: str, module_id: str) -> Dict[str, Any]:
    """
    Format a message for the Prototype MQTT client.
    
    Args:
        direction: The direction (e.g., 'South', 'East', 'West', 'None')
        module_id: The module identifier
        
    Returns:
        dict: Formatted message dictionary
    """
    return {
        'direction': direction,
        'module': module_id,
        'timestamp': datetime.now().isoformat()
    }


def parse_console_command(command_str: str) -> tuple:
    """
    Parse a console command string into command and arguments.
    
    Args:
        command_str: The command string to parse
        
    Returns:
        tuple: (command, args_list)
    """
    parts = command_str.strip().split()
    if not parts:
        return "", []
    
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    return command, args


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.
    
    Returns:
        str: Local IP address or '127.0.0.1' if unable to determine
    """
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def create_udp_broadcast_message(protocol_version: str, opcode: str, ip_address: str) -> bytes:
    """
    Create a UDP broadcast message for table discovery.
    
    Args:
        protocol_version: Protocol version (4 chars)
        opcode: Operation code (4 chars)
        ip_address: IP address to broadcast
        
    Returns:
        bytes: Encoded message with NULL terminator
    """
    message = protocol_version + opcode + ip_address
    
    # Add NULL terminator for ESP32 compatibility
    string_length = len(message)
    message = message[:string_length] + '\0' + message[string_length + 1:]
    
    return message.encode('UTF-8')


def validate_scenario_message(message: Dict[str, Any]) -> bool:
    """
    Validate a scenario-related MQTT message.
    
    Args:
        message: The message dictionary to validate
        
    Returns:
        bool: True if valid scenario message, False otherwise
    """
    required_fields = ['type']
    
    if not all(field in message for field in required_fields):
        return False
    
    message_type = message.get('type')
    
    # Validate based on message type
    if message_type == 'CHANGE_SCENARIO':
        required_payload_fields = ['scenario_name', 'is_static']
        payload = message.get('payload', {})
        return all(field in payload for field in required_payload_fields)
    
    elif message_type == 'CHANGE_MODULE_PARAMETER':
        return 'payload' in message and isinstance(message['payload'], dict)
    
    elif message_type == 'CHANGE_LINE':
        required_payload_fields = ['table', 'line', 'active']
        payload = message.get('payload', {})
        return all(field in payload for field in required_payload_fields)
    
    return True


def format_line_update_message(table: int, line: int, active: bool) -> str:
    """
    Format a line update message for GUI.
    
    Args:
        table: Table number
        line: Line number  
        active: Whether line is active
        
    Returns:
        str: JSON-formatted line update message
    """
    message = {
        "type": "LINE_UPDATE",
        "payload": [{
            "table": table,
            "line": line,
            "active": active
        }]
    }
    return json.dumps(message)


def format_module_update_message(table_section: str, module_data: Dict[str, Any]) -> str:
    """
    Format a module update message for GUI.
    
    Args:
        table_section: The table section identifier
        module_data: Module data dictionary
        
    Returns:
        str: JSON-formatted module update message
    """
    message = {
        "type": "MODULE_UPDATE", 
        "payload": {
            "table_section": table_section,
            **module_data
        }
    }
    return json.dumps(message)


def sanitize_mqtt_topic(topic: str) -> str:
    """
    Sanitize an MQTT topic name to ensure it's valid.
    
    Args:
        topic: The topic name to sanitize
        
    Returns:
        str: Sanitized topic name
    """
    # Remove invalid characters for MQTT topics
    invalid_chars = ['+', '#', '\0']
    sanitized = topic
    
    for char in invalid_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Ensure topic doesn't start or end with '/'
    sanitized = sanitized.strip('/')
    
    return sanitized


def is_valid_broker_address(address: str) -> bool:
    """
    Validate if a broker address is valid.
    
    Args:
        address: The broker address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not address:
        return False
    
    # Check if it's a valid IP address
    try:
        socket.inet_aton(address)
        return True
    except socket.error:
        pass
    
    # Check if it's a valid hostname (basic check)
    if all(c.isalnum() or c in '.-' for c in address) and len(address) <= 253:
        return True
    
    return False


def create_error_response(error_message: str, error_code: Optional[int] = None) -> str:
    """
    Create a standardized error response message.
    
    Args:
        error_message: The error message
        error_code: Optional error code
        
    Returns:
        str: JSON-formatted error response
    """
    response = {
        "type": "ERROR",
        "payload": {
            "message": error_message,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    if error_code is not None:
        response["payload"]["code"] = error_code
    
    return json.dumps(response) 