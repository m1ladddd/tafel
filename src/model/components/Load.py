##
# @file Load.py
#
# @brief Data container for Loads, inherited from Component class
# p_set and q_set are retrieved from JSON scenario files (static network that is)
# Load instances are part of a Module instance
#
# @section libraries_Load Libraries/Modules
# - Component
#   - Access to Component class used for inheritance
#
# @section todo_Load TODO
# - None
#
# @section author_Load Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

# Internal imports
from src.model.components.Component import Component

class Load (Component):
    """!
    Data container for Loads, inherited from Component class.
    p_set and q_set are retrieved from JSON scenario files (static network that is).
    Load instances are part of a Module instances.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        
        Component.__init__(self)
        
        ## Input: Set componont type to Load
        self.type: str = "Load"

        ## Input: Energy carrier: can be “AC” or “DC” for electrical buses, or “heat” or “gas”.
        self.carrier: str = "AC"

        ## Input: Active power consumption (positive if the load is consuming power).
        self.p_set: float = 0.0

        ## Input: Reactive power consumption (positive if the load is inductive).
        self.q_set: float = 0.0

        ## Output: boolean indicating if this load has a calculated output
        self.output: list[bool] = [False]

        ## Output: Active power at bus (positive if net load)
        self.active_power: list[float] = [0.0]


    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
