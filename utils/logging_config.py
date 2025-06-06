"""
Logging configuration for the Smart Grid Table application.
Provides centralized logging setup and utilities.
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_application_logging(
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True,
    log_directory: str = "logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up application-wide logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console
        log_directory: Directory for log files
        max_file_size: Maximum size of log files before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        logging.Logger: Configured root logger
    """
    # Create log directory if it doesn't exist
    if log_to_file:
        Path(log_directory).mkdir(exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_to_file:
        log_file = os.path.join(log_directory, "smart_grid_table.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.info("Smart Grid Table logging initialized")
    root_logger.info(f"Log level: {log_level}")
    root_logger.info(f"Log to file: {log_to_file}")
    root_logger.info(f"Log to console: {log_to_console}")
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)


def setup_mqtt_logging(log_level: str = "WARNING") -> logging.Logger:
    """
    Set up specific logging for MQTT components.
    
    Args:
        log_level: Logging level for MQTT components
        
    Returns:
        logging.Logger: MQTT logger
    """
    mqtt_logger = logging.getLogger("MQTT")
    mqtt_logger.setLevel(getattr(logging, log_level.upper(), logging.WARNING))
    
    # Create MQTT-specific formatter
    formatter = logging.Formatter(
        '%(asctime)s - MQTT.%(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for MQTT logs
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    mqtt_file_handler = logging.handlers.RotatingFileHandler(
        "logs/mqtt.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    mqtt_file_handler.setLevel(getattr(logging, log_level.upper(), logging.WARNING))
    mqtt_file_handler.setFormatter(formatter)
    
    mqtt_logger.addHandler(mqtt_file_handler)
    
    return mqtt_logger


def setup_simulation_logging(log_level: str = "DEBUG") -> logging.Logger:
    """
    Set up specific logging for simulation components.
    
    Args:
        log_level: Logging level for simulation components
        
    Returns:
        logging.Logger: Simulation logger
    """
    sim_logger = logging.getLogger("Simulation")
    sim_logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    
    # Create simulation-specific formatter
    formatter = logging.Formatter(
        '%(asctime)s - SIM.%(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler for simulation logs
    if not os.path.exists("logs"):
        os.makedirs("logs")
        
    sim_file_handler = logging.handlers.RotatingFileHandler(
        "logs/simulation.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=5
    )
    sim_file_handler.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))
    sim_file_handler.setFormatter(formatter)
    
    sim_logger.addHandler(sim_file_handler)
    
    return sim_logger


def log_performance_metric(logger: logging.Logger, operation: str, 
                          duration: float, details: Optional[str] = None):
    """
    Log a performance metric.
    
    Args:
        logger: Logger to use
        operation: Name of the operation
        duration: Duration in seconds
        details: Optional additional details
    """
    message = f"PERFORMANCE: {operation} took {duration:.3f}s"
    if details:
        message += f" - {details}"
    
    logger.info(message)


def log_security_event(logger: logging.Logger, event_type: str, 
                      details: str, severity: str = "WARNING"):
    """
    Log a security-related event.
    
    Args:
        logger: Logger to use
        event_type: Type of security event
        details: Event details
        severity: Log severity level
    """
    message = f"SECURITY: {event_type} - {details}"
    
    log_level = getattr(logging, severity.upper(), logging.WARNING)
    logger.log(log_level, message)


def log_mqtt_message(logger: logging.Logger, direction: str, topic: str, 
                     message_type: str, success: bool = True):
    """
    Log an MQTT message event.
    
    Args:
        logger: Logger to use
        direction: 'SEND' or 'RECEIVE'
        topic: MQTT topic
        message_type: Type of message
        success: Whether the operation was successful
    """
    status = "SUCCESS" if success else "FAILED"
    message = f"MQTT {direction}: {topic} - {message_type} - {status}"
    
    if success:
        logger.debug(message)
    else:
        logger.warning(message)


class PerformanceLogger:
    """Context manager for logging performance metrics."""
    
    def __init__(self, logger: logging.Logger, operation: str, details: Optional[str] = None):
        self.logger = logger
        self.operation = operation
        self.details = details
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            log_performance_metric(self.logger, self.operation, duration, self.details)


# Pre-configured loggers for common use cases
def get_main_logger() -> logging.Logger:
    """Get the main application logger."""
    return get_logger("SmartGridTable.Main")


def get_mqtt_logger() -> logging.Logger:
    """Get the MQTT logger."""
    return get_logger("SmartGridTable.MQTT")


def get_simulation_logger() -> logging.Logger:
    """Get the simulation logger."""
    return get_logger("SmartGridTable.Simulation")


def get_command_logger() -> logging.Logger:
    """Get the command processing logger."""
    return get_logger("SmartGridTable.Commands")


def get_validation_logger() -> logging.Logger:
    """Get the validation logger."""
    return get_logger("SmartGridTable.Validation") 