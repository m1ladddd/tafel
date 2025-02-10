##
# @file StorageUnit.py
#
# @brief Data container for Storages, inherited from Component class
# Most values are retrieved from JSON scenario files (static network that is)
# Storage objects are part of a Module object
#
# @section libraries_StoragesUnit Libraries/Modules
# - Component
#   - Access to Component class used for inheritance
#
# @section todo_StoragesUnit TODO
# - None
#
# @section author_StoragesUnit Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.model.components.Component import Component

class StorageUnit (Component):
    """! 
    Data container for Storages, inherited from Component class.
    Most values are retrieved from JSON scenario files (static network that is).
    Storage objects are part of a Module object.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        Component.__init__(self)
        
        ## Input: Set componont type to storage
        self.type: str = "Storage"

        ## Input: Nominal power for limits in OPF.
        self.p_nom: float = 0.0

        ## Input: If p_nom is extendable in OPF, set its minimum value.
        self.p_nom_min:float = 0.0

        ## Input: If p_nom is extendable in OPF, set its maximum value (e.g. limited by potential).
        self.p_nom_max: float = 1000000.0

        ## Input: Switch to allow capacity p_nom to be extended in OPF.
        self.p_nom_extendable: bool = False

        ## Input: Marginal cost of production of 1 MWh.
        self.marginal_cost: float = 0.0

        ## Input: State of charge before the snapshots in the OPF.
        self.state_of_charge_initial: float = 0.0

        ## Output: boolean indicating if this storage unit has a calculated output
        self.output: list[bool] = [False]

        ## Output: Active power at bus (positive if net generation)
        self.active_power: list[float] = [0.0]


    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
