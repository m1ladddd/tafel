##
# @file Line.py
#
# @brief # Data container for Line components, inherited from Component class.
# Lines are placed between Buses.
# active_power is used to drive the ledstrips, currently each ledstrip is attached to one line instance.
# x and r must be used in PyPSA simulations.
#
# @section libraries_Ledstrip Libraries/Modules
# - Component
#   - Access to Component class used for inheritance
#
# @section todo_Ledstrip TODO
# - None
#
# @section author_Ledstrip Author(s)
# - Created by Jop Merz on 31/01/2023.
# - Modified by Jop Merz on 31/01/2023.
##

# Internal imports
from src.model.components.Component import Component

class Line(Component):
    """!
    Data container for Line components, inherited from Component class.
    Lines are placed between Buses.
    active_power is used to drive the ledstrips, currently each ledstrip is attached to one line instance.
    x and r must be used in PyPSA simulations.
    """

    def __init__(self, name, bus0, bus1, x, r, s_nom, type, length):
        """!
        Constructor.
        @param name str Unique line name.
        @param bus0 str Start point of the line.
        @param bus1 str End point of the line.
        @param x float Power reactance of the line.
        @param r float Power resistance of the line,
        """

        Component.__init__(self)

        ## Input: set componont type to Line.
        self.type: str = "Line"

        ## Input: unique name identifier.
        self.name: str = name

        ## Input: start bus of the line.
        self.bus0: str = bus0

        ## Input: end bus of the line.
        self.bus1: str = bus1

        ## Name of line standard type. If this is not an empty string “”
        self.type: str = type

        ## Input: Length of line used when “type” is set, also useful for calculating the capital cost.
        self.length: int = length

        ## Input: maximum nominal amount of power
        self.s_nom: float = s_nom

        ## Input: Series resistance, must be non-zero for DC branch in linear power flow.
        self.r: float = r

        ## Input: series reactance, must be non-zero for AC branch in linear power flow.
        self.x: float = x

        ## Input: maximum nominal amount of power
        self.s_nom: float = s_nom

        ## Input: Switch to allow capacity s_nom to be extended in OPF.
        self.s_nom_extendable: bool = True

        ## Output: boolean indicating if this line has a calculated output
        self.output: list[bool] = [False]

        ## Output: current active power flowing through the line.
        self.active_power: list[float] = [0.0]


    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
