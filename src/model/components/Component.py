##
# @file Component.py
#
# @brief Base PyPSA component.
#
# @section libraries Libraries/Modules
# - None
#
# @section todo TODO
# - None
#
# @section author Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

class Component:
    """! 
    Base PyPSA component.
    """
    
    def __init__(self):
        """! 
        Constructor.
        """

        ## Input:Unique component name.
        self.name: str = "Unknown component"

        ## Input: Attached to this PyPSA bus.
        self.bus0: str = ""

        ## Input: Component type.
        self.type: str = ""

        ## Input: Static component (True = static, False = Dynamic).
        self.static: bool = True

        ## Boolean if component is active or not
        self.active: bool = True

        ## Boolean if this component has one or more values changed
        self.changed: bool = False
