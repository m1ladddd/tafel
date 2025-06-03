#!/usr/bin/env python3
"""
Debug script to test transformer creation and diagnose issues.
"""

import sys
import time
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Import the main controller and required components
from main_controller import MainApplicationController
from app_state import AppState

def debug_transformers():
    """Run the system, place modules, and see what happens to transformers."""
    print("=== TRANSFORMER DEBUG SESSION ===")
    
    # Initialize with simulation mode
    sys.argv = ['debug_transformers.py', '--simulation']
    
    # Create app controller
    app_controller = MainApplicationController()
    
    print("Initializing system...")
    app_controller._initialize_system()
    
    print("\nPlacing modules via simulate simple command...")
    # Dispatch the simulate simple command
    app_controller.command_dispatcher.dispatch_console_command("simulate simple")
    
    print("\nForcing calculation...")
    # Force a calculation to see transformer creation
    app_controller.table.force_calculate()
    
    if app_controller.table.get_simulation_succes():
        print("✅ Calculation successful!")
    else:
        print("❌ Calculation failed!")
    
    print("\nShutting down...")
    app_controller.app_state.request_shutdown()
    app_controller._shutdown_system()

if __name__ == "__main__":
    debug_transformers() 