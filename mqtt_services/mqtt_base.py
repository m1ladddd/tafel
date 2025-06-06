"""
Base MQTT client class providing common functionality.
This serves as a foundation for GUI, Prototype, and Jupyter MQTT clients.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from threading import Lock
import logging


class MQTTClientBase(ABC):
    """Abstract base class for MQTT clients."""
    
    def __init__(self, client_name: str):
        self.client_name = client_name
        self.broker_ip = "localhost"
        self.broker_port = 1883
        self.is_connected = False
        self.connection_lock = Lock()
        
        # Message handling
        self.message_buffer = []
        self.message_handlers: Dict[str, Callable] = {}
        
        # Logging
        self.logger = logging.getLogger(f"MQTT_{client_name}")
        
    @abstractmethod
    def get_topic_subscribe(self) -> str:
        """Get the topic this client should subscribe to."""
        pass
    
    @abstractmethod
    def get_topic_publish(self) -> str:
        """Get the topic this client should publish to."""
        pass
    
    def mqtt_set_broker(self, broker_ip: str, broker_port: int = 1883):
        """Set the MQTT broker connection details."""
        self.broker_ip = broker_ip
        self.broker_port = broker_port
        self.logger.info(f"Broker set to {broker_ip}:{broker_port}")
    
    def mqtt_connect(self) -> bool:
        """Connect to the MQTT broker."""
        with self.connection_lock:
            try:
                # This would be implemented by concrete classes
                # using their specific MQTT library (paho-mqtt, etc.)
                self._perform_connection()
                self.is_connected = True
                self.logger.info(f"{self.client_name} MQTT client connected")
                return True
            except Exception as e:
                self.logger.error(f"Failed to connect {self.client_name} MQTT client: {e}")
                self.is_connected = False
                return False
    
    def mqtt_disconnect(self):
        """Disconnect from the MQTT broker."""
        with self.connection_lock:
            try:
                self._perform_disconnection()
                self.is_connected = False
                self.logger.info(f"{self.client_name} MQTT client disconnected")
            except Exception as e:
                self.logger.error(f"Failed to disconnect {self.client_name} MQTT client: {e}")
    
    def mqtt_publish(self, message: str) -> bool:
        """Publish a message to the MQTT topic."""
        if not self.is_connected:
            self.logger.warning(f"Cannot publish - {self.client_name} not connected")
            return False
            
        try:
            topic = self.get_topic_publish()
            self._perform_publish(topic, message)
            self.logger.debug(f"Published message to {topic}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to publish message: {e}")
            return False
    
    def mqtt_is_connected(self) -> bool:
        """Check if the MQTT client is connected."""
        return self.is_connected
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add a message handler for a specific message type."""
        self.message_handlers[message_type] = handler
    
    def process_received_message(self, raw_message: str):
        """Process a received MQTT message."""
        try:
            # Try to parse as JSON
            message = json.loads(raw_message)
            
            # Add to message buffer
            self.message_buffer.append(message)
            
            # If there's a type-specific handler, call it
            if isinstance(message, dict) and 'type' in message:
                message_type = message['type']
                if message_type in self.message_handlers:
                    self.message_handlers[message_type](message)
                    
        except json.JSONDecodeError:
            # Handle non-JSON messages (like simple strings)
            self.message_buffer.append(raw_message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    def clear_message_buffer(self):
        """Clear the message buffer."""
        self.message_buffer.clear()
    
    def get_pending_messages(self) -> List[Any]:
        """Get all pending messages and clear the buffer."""
        messages = self.message_buffer.copy()
        self.message_buffer.clear()
        return messages
    
    # Abstract methods that concrete classes must implement
    @abstractmethod
    def _perform_connection(self):
        """Perform the actual MQTT connection."""
        pass
    
    @abstractmethod
    def _perform_disconnection(self):
        """Perform the actual MQTT disconnection."""
        pass
    
    @abstractmethod
    def _perform_publish(self, topic: str, message: str):
        """Perform the actual MQTT publish."""
        pass


class MQTTConnectionError(Exception):
    """Exception raised when MQTT connection fails."""
    pass


class MQTTPublishError(Exception):
    """Exception raised when MQTT publish fails."""
    pass 