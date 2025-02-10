##
# @file Platform.py
#
# @brief Class which represents a table platform, identified by location numbers [RFID 0, RFID 1 etc]
# These are used to place modules on
# Platforms must have a list of accepted modules, in the case of transformer specific platforms
# error_lines is a array of lines which are "connected" to said platform and will turn red when a wrong module is placed
#
# @section libraries_Platform Libraries/Modules
# - 
#
# @section todo_Platform TODO
# - None
#
# @section author_Platform Author(s)
# - Created by Jop Merz, Thijs van Elsacker on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

from src.model.components.Transformer import Transformer

class Platform:
    """! 
    Class which represents a table platform, identified by location numbers [RFID 0, RFID 1 etc].
    These platforms are used to place 3D modules on.
    Platforms must have a list of accepted modules, in the case of transformer specific platforms.
    error_lines is a array of lines which are "connected" to said platform and will turn red when a wrong module is placed.
    """

    def __init__(self, bus, voltage, RFID_location, error_lines, accepted_modules):
        """! 
        Constructor.
        @param bus (str) Name of the PyPSA bus connected to this platform.
        @param voltage (str) String indicating the voltage level of the platform (LV, MV or HV).
        @param RFID_location (str) Platform unique identifier (RFID 0, RFID 1, etc).
        @param error_lines (int[]) Array of line indices indicating which ledstrip should blink red if a wrong 3D object is placed.
        @param accepted_modules (str[]) Array of strings which specifies what 3D object type can be placed on this platform.
        """

        ## Name of the PyPSA bus connected to this platform.
        self.bus = bus

        ## String indicating the voltage level of the platform (LV, MV or HV).
        self.voltage = voltage

        ## Special identifier prefix
        self.name_prefix = ""

        ## Array of line indices indicating which ledstrip should blink red if a wrong 3D object is placed.
        self.error_lines = error_lines

        ## Platform unique identifier (RFID 0, RFID 1, etc).
        self.RFID_location = RFID_location

        ## RFID number of the placed 3D object (None = no module placed).
        self.RFID_tag = ""

        ## Array of strings which specifies what 3D object type can be placed on this platform.
        self.accepted_modules = []

        for module in accepted_modules:
            self.accepted_modules.append(module)

        ## 3D Module instance (None = no 3D object present).
        self.module = None

        ## List of all components from the placed 3D object.
        self.components = []

        ## Flag if a module has been placed or removed.
        self.__has_changed = False


    def add_module(self, module):
        """! 
        Place a 3D module on this platform.
        @param module (Module) Module instance to be placed.
        """

        if (module != self.module):
            self.module = module
            self.RFID_tag = module.RFID_tag

            self.components.clear()

            for buffer_component in self.module.components:
                buffer_component.name = self.name_prefix + buffer_component.name
                buffer_component.bus0 = self.name_prefix + self.bus
                self.components.append(buffer_component)

            self.__has_changed = True


    def find_voltage(self,module_voltage):
        """
        this is the function to find the voltage for the module. This function makes it so that a module can have multiple voltage
        set so that it can work on multiple tables without giving any error while still being restricted on some of the other table
         voltages.
        """
        result = module_voltage.find(self.voltage)
        return result
    

    def clear_module(self):
        """! 
        Clear the module of one his present and set has_changed flag.
        If no module is present, the has_changed flag wont be set.
        """
        if (self.module):            
            self.module = None
            self.__has_changed = True
        self.RFID_tag = "0"
        self.components.clear()
            


    def reset_changed(self):
        """! 
        Reset the has_changed flag.
        The caller must call this method after processing all changes.
        """
        self.__has_changed = False


    def has_changed(self):
        """! 
        Return if a new module has been placed or removed.
        After processing all changes, the caller must call the reset_changed() method to reset the changed flag.
        @return Bool (True = new or removed 3D module, False = no change).
        """        
        return self.__has_changed
