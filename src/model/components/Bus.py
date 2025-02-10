##
# @file Bus.py
#
# @brief Class which represents a PyPSA bus.
#
# @section libraries Libraries/Modules
# - Component
#   - Access to Component class used for inheritance.
#
# @section todo TODO
# - None
#
# @section author Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

# Internal imports
from src.model.components.Component import Component

# Classes
class Bus (Component):
    """! 
    Class which represents a PyPSA bus.
    """

    def __init__(self, name, v_nom):
        """! 
        Constructor.
        @param name str Unique name of the bus.
        @param v_nom float Nominal voltage of the bus.
        """

        Component.__init__(self)

        ## Input: PyPSA type = Bus.
        self.type: str = "Bus"

        ## Input: Unique bus name.
        self.name: str = name

        ## Input: P,Q,V control strategy for PF, must be “PQ”, “PV” or “Slack”.
        self.control: str = "PQ"

        ## Input: Nominal voltage.
        self.v_nom: float = v_nom


    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
