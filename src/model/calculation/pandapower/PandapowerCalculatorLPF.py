##
# @file PandapowerCalculatorLPF.py
#
# @brief Pandapower Linear Power Flow calculations.
#
# @section libraries_PandapowerCalculatorLPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp
import pandas as pd

class PandapowerCalculatorLPF(PandapowerNetworkBuilder):
    """
    Pandapower Linear Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """        
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Linear Power Flow calculation.
        @return bool True = success, False = Error
        """

        self._status = "ok"
        self._condition = "success"

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()

        # Check if model exists
        if self._pandapower_model is None:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "model not initialized"
            print("LPF Error: Pandapower model not initialized")
            return False

        # Check for external grid (slack bus)
        ext_grid_df = self._pandapower_model.get('ext_grid', pd.DataFrame())
        if ext_grid_df.empty:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed" 
            self._condition = "no external grid"
            print("LPF Error: No external grid (slack bus) found")
            return False

        # Check for loads or generators
        gen_df = self._pandapower_model.get('gen', pd.DataFrame())
        sgen_df = self._pandapower_model.get('sgen', pd.DataFrame())
        load_df = self._pandapower_model.get('load', pd.DataFrame())
        
        total_gens = len(gen_df) + len(sgen_df)
        total_loads = len(load_df)
        
        if total_gens == 0 and total_loads == 0:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no generation or loads"
            print("LPF Error: No generators or loads present")
            return False
      
        success = True

        try:
            # Run DC power flow (linear approximation)
            print(f"LPF: Starting calculation with {total_gens} generators, {total_loads} loads")
            pp.rundcpp(self._pandapower_model)
            print("LPF: Calculation successful")
        except Exception as e:
            self._status = "warning"
            self._condition = f"failed: {str(e)}"
            print(f"LPF Error: {str(e)}")
            success = False

        if success:
            self.retrieve_results()

        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        return success