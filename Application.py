##
# @mainpage Smart Grid Table Project
#
# @section description_main Description
# A Python program which controls the behavior of the Smart Grid Table.
#
# @section notes_main Notes
# Version 1.1 (Utilizes Pandapower for calculations)
#
# @file Application.py
#
# @brief Main entry point for the Smart Grid Table application.
#
# @section description_Application Description
# This file serves as the minimal entry point for the application.
# All logic has been moved to separate modules for better organization.
#
# @section libraries_main Libraries/Modules
# - main_controller: Main application controller
# - warnings: Standard library for warning management
#
# @section notes_Application Notes
# - Comments are Doxygen compatible.
# - Application logic has been refactored into separate modules
#
# @section author_Application Author(s)
# - Created by Jop Merz, Thijs van Elsacker on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
# - Modified by Milad Husseini from 05/02/2025 - 06-06-2025
# - Refactored into modular architecture on [current date]
##

# Imports
import warnings

# Import the main controller from the root
from main_controller import MainApplicationController

# Global configuration
warnings.simplefilter(action='ignore', category=FutureWarning)


def main():
    """Main entry point for the Smart Grid Table application."""
    print("────────────────────────────────────────────────────────────────")
    print("────────────── Smart Grid Table Application Start ──────────────")
    print("────────────────────────────────────────────────────────────────")

    # Create and run the main application controller
    app_controller = MainApplicationController()
    app_controller.run()

    print("────────────────────────────────────────────────────────────────")
    print("──────────── Smart Grid Table Application Stopped ──────────────")
    print("────────────────────────────────────────────────────────────────")


# Entry point
if __name__ == "__main__":
    main()