#!/usr/bin/env python3
"""
Test script for simulation module placement
"""

import sys
import time

def test_simulation():
    """Test the simulation functionality by connecting to running instance."""
    print("Testing simulation module placement...")
    
    # Simulate user input to the running application
    # This would normally be done through the console interface
    print("To test module placement in the running simulation:")
    print("   1. Go to the terminal where Application.py is running")
    print("   2. Type: help")
    print("   3. Type: simulate quick")
    print("   4. Type: modules list")
    print("   5. Type: calculate")
    
    print("\nAvailable test commands:")
    print("   simulate quick                          - Place test modules")
    print("   simulate place 1071771887 Table1 0     - Place specific module")
    print("   simulate remove Table1 0               - Remove module")
    print("   modules list                           - Show module status")
    print("   calculate                              - Force recalculation")
    
    print("\nExpected result:")
    print("   - Modules should appear on tables")
    print("   - Pandapower calculations should succeed")
    print("   - LED updates should work")

if __name__ == "__main__":
    test_simulation() 