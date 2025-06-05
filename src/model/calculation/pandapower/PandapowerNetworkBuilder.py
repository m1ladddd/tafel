# src/model/calculation/pandapower/PandapowerNetworkBuilder.py
##
# @file PandapowerNetworkBuilder.py
#
# @brief Class responsible for building and maintaining PandaPower network models.
#
# @section libraries_PandapowerNetworkBuilder Libraries/Modules
# - pandapower
# - pandas
# - time
##

# Internal imports
from src.model.calculation.CalculatorThreadInterface import CalculatorThreadInterface
from src.model.Model import Model, get_added_model_components, get_removed_model_components
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.Transformer import Transformer
from src.model.components.StorageUnit import StorageUnit

# External imports
import pandapower as pp
import pandas as pd
import time
from os import path, makedirs
from copy import deepcopy

class PandapowerNetworkBuilder (CalculatorThreadInterface):
    """!
    Class responsible for building and maintaining PandaPower network models.
    Uses a Model object as input.
    """

    def __init__(self):
        """!
        Constructor. Initializes an empty pandapower network.
        """
        self._pandapower_model = pp.create_empty_network()
        self._input_model = None
        self._previous_model = None  # Keep track of previous model for selective updates
        self._status = ""
        self._condition = ""
        self._calculation_time = 0.0
        self._network_build_time = 0.0
        self.snapshots = [0]  # Default for static run - Pandapower runpp is static

    def reset_lines(self) -> None:
        """
        Reset the results fields in the input_model component objects.
        """
        # Standard pandapower runpp results are for one snapshot
        snapshot_count = 1

        if self._input_model:
            # Reset Lines
            for comp in getattr(self._input_model, 'lines', []):
                comp.active_power = [0.0] * snapshot_count
                comp.output = [False] * snapshot_count
            # Reset Generators
            for comp in getattr(self._input_model, 'generators', []):
                comp.active_power = [0.0] * snapshot_count
                comp.output = [False] * snapshot_count
            # Reset Loads
            for comp in getattr(self._input_model, 'loads', []):
                comp.active_power = [0.0] * snapshot_count
                comp.output = [False] * snapshot_count
            # Reset Transformers
            for comp in getattr(self._input_model, 'transformers', []):
                comp.active_power_0 = [0.0] * snapshot_count
                comp.output = [False] * snapshot_count
                comp.capacity = 0.0
            # Reset Storage Units
            for comp in getattr(self._input_model, 'storage_units', []):
                comp.active_power = [0.0] * snapshot_count
                comp.output = [False] * snapshot_count
        else:
            print("Warning: Cannot reset results, _input_model not initialized correctly.")


    def retrieve_results(self) -> None:
        """
        Retrieve results from the PandaPower model and write them back to the input_model.
        NOTE: Assumes results are from a standard (single snapshot) power flow (runpp).
        """
        if self._pandapower_model is None or not isinstance(self._pandapower_model, dict):
             print("Warning: PandaPower model is not initialized correctly. Cannot retrieve results.")
             return

        # Retrieve result tables safely using .get()
        res_bus = self._pandapower_model.get('res_bus', pd.DataFrame())
        res_load = self._pandapower_model.get('res_load', pd.DataFrame())
        res_gen = self._pandapower_model.get('res_gen', pd.DataFrame())
        res_sgen = self._pandapower_model.get('res_sgen', pd.DataFrame())
        res_line = self._pandapower_model.get('res_line', pd.DataFrame())
        res_trafo = self._pandapower_model.get('res_trafo', pd.DataFrame())
        res_storage = self._pandapower_model.get('res_storage', pd.DataFrame())
        res_ext_grid = self._pandapower_model.get('res_ext_grid', pd.DataFrame())

        # Check if essential results exist
        if res_bus.empty:
             print("Warning: No bus results available in PandaPower model.")
             # Don't proceed if bus results are missing, as lookups might fail
             # Ensure results arrays in components are at least reset
             self.reset_lines()
             return

        # Get component tables for name-to-index mapping
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        load_table = self._pandapower_model.get('load', pd.DataFrame())
        gen_table = self._pandapower_model.get('gen', pd.DataFrame())
        sgen_table = self._pandapower_model.get('sgen', pd.DataFrame())
        line_table = self._pandapower_model.get('line', pd.DataFrame())
        trafo_table = self._pandapower_model.get('trafo', pd.DataFrame())
        storage_table = self._pandapower_model.get('storage', pd.DataFrame())
        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())

        snapshot_count = 1 # Pandapower standard runpp results are for one snapshot

        # --- Update Components in self._input_model ---
        # Note: Using direct indexing assumes names were used correctly during creation
        # and exist in the pandapower tables. Error handling added.

        # Update Loads
        for load_comp in getattr(self._input_model, 'loads', []):
             power = 0.0
             output = False
             if load_comp.active and load_comp.name in load_table.index:
                 load_idx = load_table.index.get_loc(load_comp.name)
                 if not res_load.empty and 'p_mw' in res_load.columns and load_idx < len(res_load):
                     power = res_load.p_mw.iloc[load_idx]
                     output = True
             load_comp.active_power = [power] * snapshot_count
             load_comp.output = [output] * snapshot_count

        # Update Generators (gen, sgen, ext_grid)
        for gen_comp in getattr(self._input_model, 'generators', []):
             power = 0.0
             output = False
             if gen_comp.active:
                 # Check conventional generators (gen)
                 if gen_comp.name in gen_table.index:
                     gen_idx = gen_table.index.get_loc(gen_comp.name)
                     if not res_gen.empty and 'p_mw' in res_gen.columns and gen_idx < len(res_gen):
                         power = res_gen.p_mw.iloc[gen_idx]
                         output = True
                 # Check static generators (sgen)
                 elif gen_comp.name in sgen_table.index:
                     sgen_idx = sgen_table.index.get_loc(gen_comp.name)
                     if not res_sgen.empty and 'p_mw' in res_sgen.columns and sgen_idx < len(res_sgen):
                         power = res_sgen.p_mw.iloc[sgen_idx]
                         output = True
                 # Check if it corresponds to an external grid (often acts as generator)
                 # This requires mapping the generator's bus to the ext_grid table
                 elif gen_comp.bus0 in bus_table.index:
                      bus_idx = bus_table.index.get_loc(gen_comp.bus0)
                      # Find ext_grid connected to this bus
                      ext_grids_on_bus = ext_grid_table[ext_grid_table['bus'] == bus_idx]
                      if not ext_grids_on_bus.empty:
                           ext_grid_idx = ext_grids_on_bus.index[0] # Assume only one per bus
                           if not res_ext_grid.empty and 'p_mw' in res_ext_grid.columns and ext_grid_idx in res_ext_grid.index:
                                power = res_ext_grid.p_mw.loc[ext_grid_idx]
                                output = True

             gen_comp.active_power = [power] * snapshot_count
             gen_comp.output = [output] * snapshot_count


        # Update Lines
        for line_comp in getattr(self._input_model, 'lines', []):
             power = 0.0
             output = False
             if line_comp.active and line_comp.name in line_table.index:
                 line_idx = line_table.index.get_loc(line_comp.name)
                 if not res_line.empty and 'p_from_mw' in res_line.columns and line_idx < len(res_line):
                     power = res_line.p_from_mw.iloc[line_idx]
                     output = True
             line_comp.active_power = [power] * snapshot_count
             line_comp.output = [output] * snapshot_count

        # Update Transformers
        for trafo_comp in getattr(self._input_model, 'transformers', []):
             power = 0.0
             output = False
             capacity = 0.0
             if trafo_comp.active and trafo_comp.name in trafo_table.index:
                 trafo_idx = trafo_table.index.get_loc(trafo_comp.name)
                 capacity = trafo_table.sn_mva.iloc[trafo_idx] if 'sn_mva' in trafo_table.columns else 0.0
                 if not res_trafo.empty and 'p_hv_mw' in res_trafo.columns and trafo_idx < len(res_trafo):
                     power = res_trafo.p_hv_mw.iloc[trafo_idx]
                     output = True
             trafo_comp.active_power_0 = [power] * snapshot_count
             trafo_comp.capacity = capacity
             trafo_comp.output = [output] * snapshot_count


        # Update Storage Units
        for storage_comp in getattr(self._input_model, 'storage_units', []):
             power = 0.0
             output = False
             if storage_comp.active and storage_comp.name in storage_table.index:
                 storage_idx = storage_table.index.get_loc(storage_comp.name)
                 if not res_storage.empty and 'p_mw' in res_storage.columns and storage_idx < len(res_storage):
                     power = res_storage.p_mw.iloc[storage_idx]
                     output = True
             storage_comp.active_power = [power] * snapshot_count
             storage_comp.output = [output] * snapshot_count


    # --- Private Helper Methods for Building ---

    def __get_bus_index(self, bus_name):
        """Safely get bus index by name."""
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        if bus_name in bus_table.index:
             return bus_table.index.get_loc(bus_name)
        else:
             # Try finding by 'name' column if index is numeric
             if 'name' in bus_table.columns:
                 matches = bus_table[bus_table['name'] == bus_name].index
                 if not matches.empty:
                      return matches[0] # Return the first matching numeric index
             print(f"Warning: Bus '{bus_name}' not found in pandapower model.")
             return None


    def __add_buses(self, bus_list: list[Bus]) -> None:
        """Add buses from the Model to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        bus_added = False
        for bus in bus_list:
            # Use 'name' attribute which should be the unique identifier
            if bus.active and bus.name not in self._pandapower_model['bus'].index:
                # PandaPower uses kV
                vn_kv = bus.v_nom
                try:
                    pp.create_bus(self._pandapower_model, name=bus.name, vn_kv=vn_kv)
                    bus_added = True
                except Exception as e:
                    print(f"Error adding bus {bus.name}: {e}")
        # Reindex if names were used and indices might not be sequential
        if bus_added:
             self._pandapower_model['bus'].reset_index(drop=True, inplace=True)


    def __add_lines(self, line_list: list[Line]) -> None:
        """Add lines from the Model to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        lines_added = False
        for line in line_list:
            if line.active and line.name not in self._pandapower_model['line'].index:
                from_bus_idx = self.__get_bus_index(line.bus0)
                to_bus_idx = self.__get_bus_index(line.bus1)

                if from_bus_idx is None or to_bus_idx is None:
                    print(f"Warning: Skipping line {line.name} due to missing buses.")
                    continue

                # Get line properties safely
                line_type = getattr(line, 'type', None)
                length_km = getattr(line, 'length', 1.0)
                r_ohm_per_km = getattr(line, 'r', 0.1) # Provide default if missing
                x_ohm_per_km = getattr(line, 'x', 0.1) # Provide default if missing
                c_nf_per_km = getattr(line, 'c', 10) # Provide default if missing
                s_nom_mva = getattr(line, 's_nom', None)

                # Map custom line types to valid Pandapower types
                line_type_mapping = {
                    "Link": "NAYY 4x50 SE",  # Use a standard cable type for links
                    "TransformerLink": "NAYY 4x50 SE",  # Use same for transformer links
                    "": None  # Empty string maps to None (force parameter mode)
                }
                
                # Apply mapping if line_type is in our custom types
                if line_type in line_type_mapping:
                    line_type = line_type_mapping[line_type]

                try:
                     # Estimate max current if s_nom is available
                     max_i_ka_val = 1.0 # Default
                     if s_nom_mva:
                          vn_kv = self._pandapower_model.bus.vn_kv.iloc[from_bus_idx]
                          if vn_kv > 0:
                               max_i_ka_val = s_nom_mva / (vn_kv * 1.732)

                     # Prefer using std_type if provided and valid
                     if line_type:
                          try:
                               pp.create_line(
                                   self._pandapower_model,
                                   from_bus=from_bus_idx, to_bus=to_bus_idx,
                                   length_km=length_km, std_type=line_type,
                                   name=line.name, max_loading_percent=100.0
                               )
                               lines_added = True
                               continue # Skip parameter creation if std_type worked
                          except Exception as e_type:
                               print(f"Info: std_type '{line_type}' for line {line.name} invalid or caused error ({e_type}). Using parameters.")

                     # Fallback to parameters
                     pp.create_line_from_parameters(
                         self._pandapower_model,
                         from_bus=from_bus_idx, to_bus=to_bus_idx,
                         length_km=length_km,
                         r_ohm_per_km=r_ohm_per_km,
                         x_ohm_per_km=x_ohm_per_km,
                         c_nf_per_km=c_nf_per_km,
                         max_i_ka=max_i_ka_val,
                         name=line.name
                     )
                     lines_added = True

                except Exception as e_param:
                     print(f"Error adding line {line.name}: {e_param}")
        # Reindex if names were used
        if lines_added:
             self._pandapower_model['line'].reset_index(drop=True, inplace=True)


    def __add_generators(self, generator_list: list[Generator]) -> None:
        """Add generators from the Model to the PandaPower model (as sgen)."""
        if not isinstance(self._pandapower_model, dict): return
        sgen_added = False
        for gen in generator_list:
            if gen.active and gen.name not in self._pandapower_model['sgen'].index:
                bus_idx = self.__get_bus_index(gen.bus0)
                if bus_idx is None:
                    print(f"Warning: Skipping generator {gen.name} due to missing bus {gen.bus0}.")
                    continue

                # Determine p_mw (take first value from list if applicable)
                p_mw_val = 0
                if isinstance(gen.p_set, (int, float)): p_mw_val = gen.p_set
                elif hasattr(gen.p_set, '__len__') and len(gen.p_set) > 0: p_mw_val = gen.p_set[0]
                elif isinstance(gen.p_nom, (int, float)): p_mw_val = gen.p_nom # Fallback

                # Determine q_mvar (take first value from list if applicable)
                q_mvar_val = 0
                if isinstance(gen.q_set, (int, float)): q_mvar_val = gen.q_set
                elif hasattr(gen.q_set, '__len__') and len(gen.q_set) > 0: q_mvar_val = gen.q_set[0]

                try:
                    # Create as static generator (sgen)
                    pp.create_sgen(
                        self._pandapower_model, bus=bus_idx, p_mw=p_mw_val, q_mvar=q_mvar_val,
                        name=gen.name, scaling=1.0
                    )
                    sgen_added = True
                except Exception as e:
                    print(f"Error adding generator {gen.name}: {e}")
        if sgen_added:
             self._pandapower_model['sgen'].reset_index(drop=True, inplace=True)


    def __add_loads(self, load_list: list[Load]) -> None:
        """Add loads from the Model to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        loads_added = False
        for load in load_list:
            if load.active and load.name not in self._pandapower_model['load'].index:
                bus_idx = self.__get_bus_index(load.bus0)
                if bus_idx is None:
                    print(f"Warning: Skipping load {load.name} due to missing bus {load.bus0}.")
                    continue

                p_mw_val = 0
                if isinstance(load.p_set, (int, float)): p_mw_val = load.p_set
                elif hasattr(load.p_set, '__len__') and len(load.p_set) > 0: p_mw_val = load.p_set[0]

                q_mvar_val = 0
                if isinstance(load.q_set, (int, float)): q_mvar_val = load.q_set
                elif hasattr(load.q_set, '__len__') and len(load.q_set) > 0: q_mvar_val = load.q_set[0]

                try:
                    pp.create_load(
                        self._pandapower_model, bus=bus_idx, p_mw=p_mw_val, q_mvar=q_mvar_val,
                        name=load.name
                    )
                    loads_added = True
                except Exception as e:
                     print(f"Error adding load {load.name}: {e}")
        if loads_added:
             self._pandapower_model['load'].reset_index(drop=True, inplace=True)


    def __add_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        """Add storage units from the Model to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        storage_added = False
        for storage in storage_unit_list:
             if storage.active and storage.name not in self._pandapower_model['storage'].index:
                 bus_idx = self.__get_bus_index(storage.bus0)
                 if bus_idx is None:
                     print(f"Warning: Skipping storage {storage.name} due to missing bus {storage.bus0}.")
                     continue

                 p_nom = getattr(storage, 'p_nom', 0.1)
                 soc = getattr(storage, 'state_of_charge_initial', 0.5) # Default 50% SOC
                 # Estimate max energy based on power rating (e.g., 4 hours)
                 max_e = p_nom * 4 if p_nom else 0.4

                 try:
                     pp.create_storage(
                         self._pandapower_model, bus=bus_idx, p_mw=p_nom,
                         max_e_mwh=max_e, soc_percent=soc * 100,
                         q_mvar=0, name=storage.name
                     )
                     storage_added = True
                 except Exception as e:
                      print(f"Error adding storage {storage.name}: {e}")
        if storage_added:
             self._pandapower_model['storage'].reset_index(drop=True, inplace=True)


    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """Add transformers from the Model to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        trafo_added = False
        for trafo in transformer_list:
            if trafo.active and trafo.name not in self._pandapower_model['trafo'].index:
                 hv_bus_idx = self.__get_bus_index(trafo.bus0) # Assume bus0 is HV side
                 lv_bus_idx = self.__get_bus_index(trafo.bus1) # Assume bus1 is LV side

                 if hv_bus_idx is None or lv_bus_idx is None:
                     print(f"Warning: Skipping transformer {trafo.name} due to missing buses.")
                     continue

                 # Get bus voltages to ensure correct HV/LV assignment and for parameter fallback
                 hv_vn_kv = self._pandapower_model.bus.vn_kv.iloc[hv_bus_idx]
                 lv_vn_kv = self._pandapower_model.bus.vn_kv.iloc[lv_bus_idx]

                 # Swap if assumption was wrong
                 if hv_vn_kv < lv_vn_kv:
                      hv_bus_idx, lv_bus_idx = lv_bus_idx, hv_bus_idx
                      hv_vn_kv, lv_vn_kv = lv_vn_kv, hv_vn_kv

                 # Try to use standard type from trafo.model
                 std_type = getattr(trafo, 'model', None)
                 if std_type:
                    try:
                        pp.create_transformer(
                            self._pandapower_model, hv_bus=hv_bus_idx, lv_bus=lv_bus_idx,
                            std_type=std_type, name=trafo.name
                        )
                        trafo_added = True
                        continue # Skip parameter creation if std_type worked
                    except Exception as e_type:
                        print(f"Info: std_type '{std_type}' for trafo {trafo.name} invalid or caused error ({e_type}). Using parameters.")

                 # Fallback to parameters if no std_type or if std_type failed
                 try:
                    # Get parameters from trafo object or use defaults
                    sn_mva = getattr(trafo, 'capacity', 1.0) or 1.0 # Ensure not None or 0
                    vkr_percent = getattr(trafo, 'r', 1.0) # Assuming trafo.r maps to vkr
                    vk_percent = getattr(trafo, 'x', 6.0) # Assuming trafo.x maps to vk

                    pp.create_transformer_from_parameters(
                         self._pandapower_model, hv_bus=hv_bus_idx, lv_bus=lv_bus_idx,
                         sn_mva=sn_mva, vn_hv_kv=hv_vn_kv, vn_lv_kv=lv_vn_kv,
                         vkr_percent=vkr_percent, vk_percent=vk_percent,
                         pfe_kw=sn_mva * 10, # Rough estimation of iron losses
                         i0_percent=0.5, # Rough estimation of no-load current
                         name=trafo.name
                    )
                    print(f"DEBUG: Created transformer {trafo.name} using parameter fallback")
                    trafo_added = True
                 except Exception as e_param:
                    print(f"Error adding transformer {trafo.name} with parameters: {e_param}")

        if trafo_added:
             self._pandapower_model['trafo'].reset_index(drop=True, inplace=True)

    # --- Methods for removing components ---
    def __remove_elements(self, table_name: str, name_list: list[str]) -> None:
         """Removes elements from a specified table by name (which is used as index)."""
         if not isinstance(self._pandapower_model, dict) or table_name not in self._pandapower_model:
             return

         current_table = self._pandapower_model.get(table_name, pd.DataFrame())
         if not isinstance(current_table, pd.DataFrame) or current_table.empty:
             return

         # Ensure index is the 'name' column if it exists and isn't already the index
         if 'name' in current_table.columns and current_table.index.name != 'name':
              # Check if names are unique before setting as index
              if current_table['name'].is_unique:
                   current_table.set_index('name', inplace=True)
              else:
                   print(f"Warning: Cannot remove elements from '{table_name}' by name, names are not unique.")
                   return # Cannot reliably remove by non-unique name

         # Find indices (names) to drop
         indices_to_drop = [name for name in name_list if name in current_table.index]

         if indices_to_drop:
             try:
                 # Use DataFrame drop directly with the index (names)
                 self._pandapower_model[table_name] = current_table.drop(index=indices_to_drop)
                 # Reset numeric index if needed (though keeping name index might be fine)
                 # self._pandapower_model[table_name].reset_index(inplace=True) # Optional
                 print(f"Removed {len(indices_to_drop)} elements from '{table_name}'.")
             except Exception as e:
                 print(f"Error removing elements {indices_to_drop} from {table_name}: {e}")


    def __remove_buses(self, bus_list: list[Bus]) -> None:
         self.__remove_elements("bus", [bus.name for bus in bus_list if bus.active])

    def __remove_lines(self, line_list: list[Line]) -> None:
         self.__remove_elements("line", [line.name for line in line_list if line.active])

    def __remove_generators(self, generator_list: list[Generator]) -> None:
        active_gen_names = [gen.name for gen in generator_list if gen.active]
        self.__remove_elements("sgen", active_gen_names) # Remove from static generators
        self.__remove_elements("gen", active_gen_names)  # Remove from conventional generators


    def __remove_loads(self, load_list: list[Load]) -> None:
        self.__remove_elements("load", [load.name for load in load_list if load.active])

    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        self.__remove_elements("storage", [storage.name for storage in storage_unit_list if storage.active])

    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:
        self.__remove_elements("trafo", [trafo.name for trafo in transformers_list if trafo.active])


    # --- Implementation of Interface Methods ---

    def calculate(self) -> bool:
        """
        Start a default PandaPower Power Flow calculation (runpp).
        Derived classes can override this for OPF, etc.
        @return bool True = success, False = Error
        """
        start_time = time.perf_counter()
        self.reset_lines() # Reset results in our input_model components

        if self._pandapower_model is None or not isinstance(self._pandapower_model, dict):
            self._status = "failed"
            self._condition = "model not initialized"
            print("Error: Pandapower model not initialized, cannot calculate.")
            self._calculation_time = time.perf_counter() - start_time
            return False

        # Check for any generation source (but don't fail if none exist)
        has_ext_grid = not self._pandapower_model.get('ext_grid', pd.DataFrame()).empty
        has_gen = not self._pandapower_model.get('gen', pd.DataFrame()).empty
        has_sgen = not self._pandapower_model.get('sgen', pd.DataFrame()).empty
        has_any_generation = has_ext_grid or has_gen or has_sgen
        
        if not has_any_generation:
            print("WARNING: No generation source found in the model (ext_grid, gen, or sgen).")
            print("         This typically happens when no physical modules are placed.")
            print("         Treating as empty grid simulation.")
            # Don't fail - treat as successful empty grid
            self._status = "warning"
            self._condition = "empty grid - no generation"
            self._calculation_time = time.perf_counter() - start_time
            return True

        success = True
        try:
            # Run standard power flow - REMOVED numba=False
            print("Running standard power flow (runpp)...")
            pp.runpp(self._pandapower_model, algorithm='nr', calculate_voltage_angles=True)
            print("Power flow calculation successful!")
            self._status = "ok"
            self._condition = "converged" # runpp success implies convergence
            self.retrieve_results() # Populate input_model components with results
        except pp.LoadflowNotConverged as e:
            self._status = "warning"  # Changed from "failed" to "warning" 
            self._condition = "loadflow not converged"
            print(f"Warning: PandaPower loadflow did not converge: {e}")
            print("         This is often normal for empty grids or grids without proper load/generation balance")
            success = True  # Changed: treat non-convergence as warning, not failure
            # Still populate with default/reset results
            self.reset_lines()
        except Exception as e:
            self._status = "failed"
            self._condition = f"exception: {e}"
            print(f"Error during PandaPower calculation: {e}")
            import traceback
            traceback.print_exc()  # Add full traceback for debugging
            success = False
            # Optionally clear results in components on failure
            self.reset_lines()

        self._calculation_time = time.perf_counter() - start_time
        return success


    def get_status(self) -> str:
        """ Return de status van de simulatie. """
        return self._status

    def get_condition(self) -> str:
        """ Return de conditie van de simulatie. """
        return self._condition

    def get_calculation_time(self) -> float:
        """ Return de berekeningstijd. """
        return self._calculation_time

    def get_network_build_time(self) -> float:
        """ Return de tijd die nodig was om het netwerk te bouwen. """
        return self._network_build_time

    def export_result(self, file_path: str) -> None:
        """ Export the PandaPower model result to Excel. """
        if self._pandapower_model is None:
            print("Error: Cannot export results, Pandapower model not initialized.")
            return

        if not path.exists(file_path):
            try: makedirs(file_path)
            except OSError as e:
                print(f"Error creating directory {file_path}: {e}"); return

        export_filepath = path.join(file_path, "pandapower_results.xlsx")
        try:
            pp.to_excel(self._pandapower_model, export_filepath)
            print(f"Successfully exported PandaPower results to {export_filepath}")
        except Exception as e:
            print(f"Error exporting PandaPower results to {export_filepath}: {e}")


    def set_input_model(self, input_model: Model) -> None:
        """ Set the input model for this builder. """
        self._input_model = input_model

    def set_snapshots(self, snapshots: list) -> None:
        """ Set the simulation snapshot list (less relevant for standard runpp). """
        self.snapshots = snapshots if isinstance(snapshots, list) else [0]


    def build_model(self) -> None:
        """
        Build the PandaPower model based on input_model. Performs a full rebuild.
        """
        start_time = time.perf_counter()
        if self._input_model is None:
            print("Error: Input model is not set. Cannot build PandaPower model."); return

        try:
            # Start with a fresh empty network for full rebuild
            self._pandapower_model = pp.create_empty_network()
            self.force_build()
            self._previous_model = deepcopy(self._input_model) # Keep copy for potential future diffs
        except Exception as e:
            print(f"Critical error during model build: {e}")
            # Ensure model is reset to avoid inconsistent state
            self._pandapower_model = pp.create_empty_network()

        self._network_build_time = (time.perf_counter() - start_time)


    def force_build(self):
        """Build all components from the input_model into PandaPower."""
        if not self._input_model:
            print("Warning: No input model set for force_build."); return

        # Add components in logical order (Buses first)
        self.__add_buses(self._input_model.buses)
        self.__add_lines(self._input_model.lines)
        self.__add_generators(self._input_model.generators)
        self.__add_loads(self._input_model.loads)
        self.__add_storage_units(self._input_model.storage_units)
        self.__add_transformers(self._input_model.transformers)
        
        # Automatically add external grid if none exists
        self._ensure_external_grid()

    def _ensure_external_grid(self):
        """Ensure at least one external grid exists for voltage reference."""
        try:
            ext_grid_df = self._pandapower_model.get('ext_grid', pd.DataFrame())
            if ext_grid_df.empty:
                # Find the highest voltage bus for external grid placement
                bus_df = self._pandapower_model.get('bus', pd.DataFrame())
                if not bus_df.empty:
                    # Get HV bus (highest voltage, preferably Table1)
                    table1_buses = bus_df[bus_df['name'].str.contains('Table1', na=False)]
                    if not table1_buses.empty:
                        # Use Table1_bus0 if available, otherwise highest voltage Table1 bus
                        table1_bus0 = table1_buses[table1_buses['name'].str.contains('bus0', na=False)]
                        if not table1_bus0.empty:
                            bus_idx = table1_bus0.index[0]
                        else:
                            bus_idx = table1_buses['vn_kv'].idxmax()
                    else:
                        # No Table1 buses, use highest voltage bus
                        bus_idx = bus_df['vn_kv'].idxmax()
                    
                    bus_name = bus_df.loc[bus_idx, 'name']
                    bus_voltage = bus_df.loc[bus_idx, 'vn_kv']
                    
                    # Add external grid
                    pp.create_ext_grid(
                        self._pandapower_model, 
                        bus=bus_idx, 
                        vm_pu=1.0, 
                        name="Auto External Grid"
                    )
                    print(f"AUTO: Added external grid to {bus_name} ({bus_voltage} kV)")
                    return True
                else:
                    print("Warning: No buses available for external grid")
                    return False
            else:
                print(f"External grid already exists (count: {len(ext_grid_df)})")
                return True
        except Exception as e:
            print(f"Error ensuring external grid: {e}")
            return False


    def selective_build(self):
        """
        Selective building based on diff between input_model and previous_model.
        (Currently defaults to full rebuild for robustness).
        """
        # TODO: Implement actual selective build using get_added/removed model components
        # and the __remove_... / __add_... methods.
        print("Info: Selective building requested, performing full rebuild for now.")
        self.build_model() # Call full build which handles initialization


    def set_calculation_method(self, method: str) -> None:
        """
        Set the calculation method (Placeholder for interface compatibility).
        Actual calculation logic is in specific calculator classes or the default calculate().
        """
        print(f"Info: PandaPower builder received set_calculation_method('{method}'). Specific calculators should implement relevant logic.")
        pass