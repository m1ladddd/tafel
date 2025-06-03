##
# @file PandapowerCalculatorPF.py
#
# @brief Pandapower model used for Power Flow calculations.
#
# @section libraries_PandapowerCalculatorPF Libraries/Modules
# - pandapower
##

# Internal imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

# External imports
import time
import pandapower as pp

class PandapowerCalculatorPF(PandapowerNetworkBuilder):
    """
    Pandapower Power Flow calculations.
    """

    def __init__(self):
        """! 
        Constructor.
        """
        super().__init__()


    def calculate(self) -> bool:
        """
        Start a Pandapower Power Flow calculation.
        @return bool True = success, False = Error
        """

        self._status = "ok"
        self._condition = "success"

        # Start benchmark timer
        start_time = time.perf_counter()

        # Clear previous power line values
        self.reset_lines()

        # CRITICAL: Build the Pandapower model from input_model
        if self._input_model is None:
            print("CRITICAL: No input model set! Cannot calculate.")
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no input model"
            return False
            
        print("Building Pandapower model from input Model...")
        self.build_model()

        # Blackout/failed calculation when no generators and storage units are present
        if (len(self._input_model.generators) == 0 and
            len(self._input_model.storage_units) == 0):
                self._calculation_time = time.perf_counter() - start_time
                self._status = "failed"
                self._condition = "no generation"
                return False
      
        # DETAILED DEBUG LOGGING BEFORE CALCULATION
        print("DEBUG: Pandapower Model Info:")
        print(f"   Buses: {len(self._pandapower_model.get('bus', []))}")
        print(f"   Lines: {len(self._pandapower_model.get('line', []))}")
        print(f"   Generators (gen): {len(self._pandapower_model.get('gen', []))}")
        print(f"   Static generators (sgen): {len(self._pandapower_model.get('sgen', []))}")
        print(f"   External grids (ext_grid): {len(self._pandapower_model.get('ext_grid', []))}")
        print(f"   Loads: {len(self._pandapower_model.get('load', []))}")
        print(f"   Transformers: {len(self._pandapower_model.get('trafo', []))}")
        print(f"   Storage: {len(self._pandapower_model.get('storage', []))}")
        
        # Check for critical missing components
        has_ext_grid = len(self._pandapower_model.get('ext_grid', [])) > 0
        has_generators = len(self._pandapower_model.get('gen', [])) > 0 or len(self._pandapower_model.get('sgen', [])) > 0
        has_loads = len(self._pandapower_model.get('load', [])) > 0
        
        print(f"   Has external grid (slack bus): {has_ext_grid}")
        print(f"   Has generation: {has_generators}")
        print(f"   Has loads: {has_loads}")
        
        # Critical validation
        if not has_ext_grid:
            print("CRITICAL: No external grid (slack bus) found!")
            print("   Pandapower REQUIRES at least one ext_grid for voltage reference")
            print("   Adding automatic ext_grid to first HV bus...")
            self._add_emergency_slack_bus()
        
        if not has_loads and has_generators:
            print("WARNING: Generators without loads may cause convergence issues")
        
        success = True

        try:
            # First run DC power flow as initialization
            print("Running DC power flow initialization...")
            pp.rundcpp(self._pandapower_model)
            print("DC power flow successful")
            
            # Then run full AC power flow with Newton-Raphson solver
            print("Running AC power flow calculation...")
            pp.runpp(self._pandapower_model, algorithm="nr", init="dc", max_iteration=100)
            print("AC power flow successful!")
        except pp.LoadflowNotConverged as e:
            print(f"Power flow calculation did not converge: {e}")
            print("Trying with different solver options...")
            try:
                # Second attempt with different settings
                print("   Attempting with backward-forward sweep solver...")
                pp.runpp(self._pandapower_model, algorithm="bfsw", tolerance_mva=1e-3)
                print("Second attempt successful!")
                success = True
            except Exception as e2:
                print(f"Second attempt also failed: {e2}")
                self._status = "warning"
                self._condition = f"failed: loadflow not converged - {str(e)}"
                success = False
        except Exception as e:
            print(f"Unexpected error during power flow: {e}")
            self._status = "warning"
            self._condition = f"failed: {str(e)}"
            success = False

        # Stop benchmark timer
        self._calculation_time = time.perf_counter() - start_time

        # Retrieve results if successful
        if success:
            print("Retrieving results...")
            self.retrieve_results()
            print("Results retrieved successfully!")
        else:
            print("Calculation failed - no results to retrieve")

        return success
        
    def _add_emergency_slack_bus(self):
        """Add emergency external grid to first available HV bus."""
        try:
            bus_df = self._pandapower_model.get('bus')
            if bus_df is not None and not bus_df.empty:
                # Find highest voltage bus (likely HV)
                hv_bus_idx = bus_df['vn_kv'].idxmax()
                hv_voltage = bus_df.loc[hv_bus_idx, 'vn_kv']
                
                print(f"   Adding ext_grid to bus {hv_bus_idx} ({hv_voltage} kV)")
                pp.create_ext_grid(self._pandapower_model, bus=hv_bus_idx, vm_pu=1.0, name="Emergency Grid Connection")
                print("   Emergency ext_grid added successfully")
                return True
            else:
                print("   No buses available for ext_grid")
                return False
        except Exception as e:
            print(f"   Failed to add emergency ext_grid: {e}")
            return False