##
# @file TransformerLink.py
#
# @brief A special link between table sections and has a connection with a Platform
# This way we can shut this link down if no transformer is present on the transfomer Platform
#
# @section libraries_TransformerLink Libraries/Modules
# - time
#
# @section todo_TransformerLink TODO
# - Switch to real transformer PyPSA component
#
# @section author_TransformerLink Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

class TransformerLink:
    """! A special link between table sections and has a connection with a Platform
    This way we can shut this link down if no transformer is present on the transfomer Platform
    """

    def __init__(self,RFID_table, RFID_location, table0, bus0, table1, bus1):
        """! Object constructor
        """

        ## Table section that has the transformer platform.
        self.RFID_table = RFID_table

        ## RFID location of the transformer platform.
        self.RFID  = RFID_location

        ## Table of the first connection point.
        self.table0 = table0

        ## Connection point 1
        self.bus0 = table0 + "_" + bus0

        ## Table of the second connection point.
        self.table1 = table1

        ## Connection point 1
        self.bus1 = table1 + "_" + bus1

        ## Unique name of the transformer
        self.name = "Dynamic_" + self.bus0 + "__" + self.bus1
        
        