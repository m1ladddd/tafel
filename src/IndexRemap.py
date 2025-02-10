##
# @file LineRemap.py
#
# @brief Remaps a index to other indices.
#
# @section author_Bus Author(s)
# - Created by Jop Merz on 15/09/2023.
# - Modified by Jop Merz on 15/09/2023.
##

import json

class IndexRemap:
    """! 
    Remaps lines with one or more lines.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Remapping list where the list index is the origin line and the result are the destination lines.
        self.__mapping_list: list[list[int]] = []

        ## List of the state of lines.
        self.line_state: list[bool] = []


    def load(self, file_path: str):
        with open(file_path) as json_file:

            # Load the JSON file
            index_remap = json.load(json_file)
            remap_list = index_remap.get("remap_list")
            remap_list_size = len(remap_list)

            # Create the list with X size
            for i in range(remap_list_size):
                self.__mapping_list.append([])
                self.line_state.append(True)

            # Fill the array with the values from the JSON file
            for remap in remap_list:
                origin_line = remap.get("origin_line")
                destination_lines = remap.get("destination_lines")
                self.__mapping_list[origin_line] = destination_lines

        return True
    

    def clear(self) -> None:
        self.__mapping_list.clear()
        self.line_state.clear()


    def get_mapped_indices(self, index: int) -> list[int]:
        if (index >= len(self.__mapping_list)):
            return
        return self.__mapping_list[index]
        