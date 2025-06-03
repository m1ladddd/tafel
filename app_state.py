# app_state.py
"""
Module for managing the global application state.
This replaces the scattered global variables in the original Application.py
"""

class AppState:
    """Manages the global state of the Smart Grid Table application."""
    
    def __init__(self):
        self.force_update: bool = True  # Start with an initial update
        self.current_mode: str = "optimize"  # Default calculation mode
        self.console_input_buffer: str = ""
        self.is_running: bool = True
        self.simulation_mode: bool = False
        self.local_broker_ip: str = "127.0.0.1"
        self.refresh_rate: float = 0.01
        
    def set_mode(self, new_mode: str):
        """Set the calculation mode and trigger an update."""
        # Handle None and non-string inputs
        if new_mode is None or not isinstance(new_mode, str):
            return False
            
        valid_modes = ["optimize", "lopf", "lpf", "pf"]
        if new_mode.lower() in valid_modes:
            self.current_mode = new_mode.lower()
            self.force_update = True
            return True
        return False
    
    def request_shutdown(self):
        """Request application shutdown."""
        self.is_running = False
        
    def request_update(self):
        """Request a forced recalculation."""
        self.force_update = True
        
    def consume_force_update(self) -> bool:
        """Check and reset the force_update flag."""
        if self.force_update:
            self.force_update = False
            return True
        return False 