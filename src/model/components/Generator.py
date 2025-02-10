##
# @file Generator.py
#
# @brief Data container for Generators, inherited from Component class.
# Most variable values are retrieved from JSON scenario files (static network that is).
# Generator instances are used in Module instances.
#
# @section libraries_main Libraries/Modules
# - Component
#   - Access to Component class used for inheritance
#
# @section todo_Bus TODO
# - None
#
# @section author_Bus Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

# Internal imports
from src.model.components.Component import Component

class Generator (Component):
    """! 
    Data container for Generators, inherited from Component class.
    Most variable values are retrieved from JSON scenario files (static network that is).
    Generator instances are used in Module instances.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        Component.__init__(self)

        ## Input: PyPSA Type = Generator.
        self.type: str = "Generator"

        ## Input: Nominal power for limits in OPF.
        self.p_nom: float = 0.0

        ## Input: active power set point (for PF).
        self.p_set: float = 0.0

        ## Input: reactive power set point (for PF)
        self.q_set: float = 0.0

        ## Input: The minimum output for each snapshot per unit of p_nom for the OPF
        ##(e.g. for variable renewable generators this can change due to weather conditions and compulsory feed-in; 
        ## for conventional generators it represents a minimal dispatch). Note that if comittable is False and p_min_pu > 0, 
        ## this represents a must-run condition.
        self.p_min_pu: float = 0.0

        ## Input: The maximum output for each snapshot per unit of p_nom for the OPF 
        ## (e.g. for variable renewable generators this can change due to weather conditions; 
        ## for conventional generators it represents a maximum dispatch).
        self.p_max_pu = 1.0

        ## Input: If p_nom is extendable in OPF, set its minimum value.
        self.p_nom_min: float = 0.0

        ## Input: If p_nom is extendable in OPF, set its maximum value (e.g. limited by technical potential).
        self.p_nom_max: float = 1000000.0

        ## Input: Marginal cost of production of 1 MWh.
        self.marginal_cost: float = 0.0

        ## Input: Switch to allow capacity p_nom to be extended in OPF.
        self.p_nom_extendable: bool = False

        ## Output: boolean indicating if this line has a calculated output
        self.output: list[bool] = [False]

        ## Output: Active power at bus (positive if net generation)
        self.active_power: list[float] = [0.0]
        

    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
