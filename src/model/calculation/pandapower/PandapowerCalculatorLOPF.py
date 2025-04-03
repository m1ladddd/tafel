##
# @file PandapowerCalculatorLOPF.py
#
# @brief Pandapower Linear Optimal Power Flow calculations.
#
# @section libraries_PandapowerCalculatorLOPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp

class PandapowerCalculatorLOPF(PandapowerNetworkBuilder):
    """
    Pandapower Linear Optimal Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Linear Optimal Power Flow calculation.
        @return bool True = success, False = Error
        """

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()
     
        # Blackout/failed calculation when no generators and storage units are present
        if (len(self._input_model.generators) == 0 and
            len(self._input_model.storage_units) == 0):
                self._calculation_time = time.perf_counter() - start_time
                self._status = "failed"
                self._condition = "no generation"
                return False
        
        success = True
        
        try:
            # Run DC OPF (linear optimal power flow)
            pp.rundcopp(self._pandapower_model)
            self._status = "ok"
            self._condition = "optimal"
        except pp.OPFNotConverged:
            self._status = "failed"
            self._condition = "not converged"
            success = False
        except Exception as e:
            self._status = "error"
            self._condition = str(e)
            success = False
            
        if success:
            self.retrieve_results()
        
        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        return success