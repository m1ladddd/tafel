##
# @file Load.py
#
# @brief # Class which represents a module (placable piece on the table, likes houses and power plants)
# Modules have RFID tag numbers attached, this number is used to load the correct values from the JSON files
# Modules consists out of one or multiple Components
#
# @section libraries_Module Libraries/Modules
# - 
#
# @section todo_Module TODO
# - None
#
# @section author_Module Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

class Module:
    """!
    Class which represents a module (placable piece on the table, likes houses and power plants).
    Modules have RFID tag numbers attached, this number is used to load the correct values from the JSON files.
    Modules consists out of one or multiple Components.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Unique RFID indentifier read from the RFID card.
        self.RFID_tag       = ""

        ## Unique name needed for PyPSA network.
        self.name           = ""

        ## Description name of the 3D object, for example "Coal power plant".
        self.module_name    = ""

        ## Voltage level of the 3D object (LV, MV or HV).
        self.voltage        = ""

        ## List of all PyPSA components in this 3D object.
        self.components = []


    def clear(self):
        """! 
        Clears all components in this 3D object.
        """

        self.components.clear()

    def add_component(self, component):
        """! 
        Add a PyPSA component to this 3D object.
        @param component Component instance to be added.
        """

        self.components.append(component)
