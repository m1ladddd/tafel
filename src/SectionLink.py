##
# @file SectionLink.py
#
# @brief A connection between table sections so power can flow from one to another
#
# @section libraries_SectionLink Libraries/Modules
# - 
#
# @section todo_SectionLink TODO
# - None
#
# @section author_SectionLink Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

class SectionLink:
    """! 
    A connection between table sections so power can flow from one to another.
    """

    def __init__(self, table0, bus0, table1, bus1):
        """! 
        Constructor.
        """
        
        ## First bus of the link.
        self.bus0   = table0 + "_" + bus0

        ## Second bus of the link.
        self.bus1   = table1 + "_" + bus1

        ## Unique link name for PyPSA.
        self.name   = self.bus0 + "__" + self.bus1

        ## Line resistance
        self.r = 0.01

        ## Line reactance
        self.x = 0.1

        ## Maxium line capacity
        self.s_nom = 99999999999999
        