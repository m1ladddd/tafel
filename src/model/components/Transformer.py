##
# @file Transformer.py
#
# @brief Not used, transformer objects are planned to replace the dynamic links
#
# @section libraries_StoragesUnit Libraries/Modules
# - time
#
# @section todo_StoragesUnit TODO
# Implement
#
# @section author_StoragesUnit Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

# Internal imports
from src.model.components.Component import Component

class Transformer (Component):
    """! TODO make this"""

    def __init__(self):
        """! 
        Constructor
        """

        Component.__init__(self)

        ## Input: Set componont type to Transformer
        self.type: str = "Transformer"

        ## Input: Switch to allow capacity s_nom to be extended in OPF.
        self.s_nom_extendable: bool = False

        ## Input: Model used for admittance matrix; can be “t” or “pi”; 
        ## since PyPSA Version 0.8.0 it defaults to “t” following physics and DIgSILENT PowerFactory; 
        ## versions of PyPSA before 0.8.0 and some other power system tools, like MATPOWER, PYPOWER, PSS/SINCAL use the less physical “pi” model.
        self.model: str = ""

        ## Input: Name of first bus (typically higher voltage) to which transformer is attached.
        self.bus0: str = ""

        ## Input: Name of second bus (typically lower voltage) to which transformer is attached.
        self.bus1: str = ""

        ## Input: Series reactance (per unit, using s_nom as base power); must be non-zero for AC branch in linear power flow.
        self.x: float = 0

        ## Input: Series resistance (per unit, using s_nom as base power); must be non-zero for DC branch in linear power flow. 
        self.r: float = 0

        ## Output: boolean indicating if this transformer has a calculated output
        self.output: list[bool] = [False]

        ## Output: Active power at bus0 (positive if branch is withdrawing power from bus0).
        self.active_power_0: list[float] = [0.0]

        ## Output: Total capacity of the transformer.
        self.capacity: float = 0.0


    def __key(self) -> tuple:
        return (self.name, self.changed)
    
    def __hash__(self) -> int:
        return hash(self.__key())

    def __eq__(self, other: object) -> bool:
        return self.__key() == other.__key()
