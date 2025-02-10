##
# @file Timer.py
#
# @brief Time benchmark class.
#
# @section libraries_StoragesUnit Libraries/Modules
# - time
#
# @section todo_StoragesUnit TODO
# - None
#
# @section author_StoragesUnit Author(s)
# - Created by Jop Merz on 01/02/2023.
# - Modified by Jop Merz on 01/02/2023.
##

import time

class Timer:
    """! 
    Benchmark class.
    """

    def __init__(self):
        """! 
        Constructor.
        """

        ## Start time if the timer.
        self.__start_time   = None

        ## Elapsed time.
        self.elapsed_time = None


    def start(self):
        """! 
        Start the timer.
        """

        self.__start_time = time.perf_counter()

    def stop(self):
        """! 
        Stop the timer and calculate the elapsed time.
        """
        
        if self.__start_time is not None:
            self.elapsed_time = time.perf_counter() - self.__start_time
            self.__start_time = None
