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
# - numpy
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
# Removed numpy import here as it's not directly used and might be related to the error
# import numpy
import time
from os import path, makedirs
from copy import deepcopy

class PandapowerNetworkBuilder (CalculatorThreadInterface):
    """!
    Class responsible for building and maintaining PandaPower network models.
    """

    def __init__(self):
        """!
        Constructor.
        """
        self._pandapower_model = None
        try:
            # Attempt to create the network normally
            self._pandapower_model = pp.create_empty_network()
            # Ensure essential tables exist even if created empty
            if 'bus' not in self._pandapower_model:
                 self._pandapower_model['bus'] = pd.DataFrame(columns=pp.elements.bus.columns)
            # Add checks for other tables if needed
        except Exception as e:
            # Fallback: If create_empty_network fails, manually create a minimal structure
            # This ensures the keys exist, preventing the KeyError later.
            print(f"Error creating empty pandapower network: {e}. Attempting manual initialization.")
            try:
                 # Check if pandas is available
                 import pandas as pd_fallback
                 # Manually create the basic structure pandapower expects
                 self._pandapower_model = pp.toolbox.create_empty_network_from_dict({
                     'bus': pd_fallback.DataFrame(columns=pp.elements.bus.columns),
                     'line': pd_fallback.DataFrame(columns=pp.elements.line.columns),
                     'trafo': pd_fallback.DataFrame(columns=pp.elements.trafo.columns),
                     'gen': pd_fallback.DataFrame(columns=pp.elements.gen.columns),
                     'sgen': pd_fallback.DataFrame(columns=pp.elements.sgen.columns),
                     'load': pd_fallback.DataFrame(columns=pp.elements.load.columns),
                     'ext_grid': pd_fallback.DataFrame(columns=pp.elements.ext_grid.columns),
                     'storage': pd_fallback.DataFrame(columns=pp.elements.storage.columns),
                     # Add other necessary empty DataFrames if needed
                     '_ppc': None,
                     'version': pp.__version__,
                     'converged': False,
                     'name': 'Manually Initialized Network'
                 })
            except Exception as fallback_e:
                 print(f"Error during manual fallback initialization: {fallback_e}")
                 # Final fallback: an empty dict, though this will likely still fail later
                 self._pandapower_model = {}

        self._input_model = None
        self._previous_model = None  # Keep track of previous model for selective updates
        self._status = ""
        self._condition = ""
        self._calculation_time = 0.0
        self._network_build_time = 0.0
        self.snapshots = [0]  # Default for static run


    def reset_lines(self) -> None:
        """
        Reset the results fields in the input_model.
        """
        # Check if snapshots is a valid list or datetime index
        if hasattr(self.snapshots, '__len__') and not isinstance(self.snapshots, str):
            snapshot_count = len(self.snapshots)
        else:
            snapshot_count = 1 # Default to 1 if snapshots is not list-like

        if self._input_model and hasattr(self._input_model, 'lines'):
            for line in self._input_model.lines:
                line.active_power = [0.0] * snapshot_count
                line.output = [False] * snapshot_count
        else:
            print("Warning: Cannot reset lines, _input_model or _input_model.lines not initialized correctly.")


    def retrieve_results(self) -> None:
        """
        Retrieve results from the PandaPower model and write them back to the input_model.
        NOTE: PandaPower result names may differ from PyPSA. Snapshots are not considered here.
        """
        # Ensure the pandapower model and results exist
        if self._pandapower_model is None or not isinstance(self._pandapower_model, dict):
             print("Warning: PandaPower model is not initialized correctly. Cannot retrieve results.")
             return
        if not hasattr(self._pandapower_model, 'res_load') or self._pandapower_model.res_load is None or self._pandapower_model.res_load.empty:
            print("Warning: No load results available or results are empty in PandaPower model.")
            # Attempt to initialize empty results if missing, crucial for checks below
            if not hasattr(self._pandapower_model, 'res_load'): self._pandapower_model.res_load = pd.DataFrame()
            if not hasattr(self._pandapower_model, 'res_gen'): self._pandapower_model.res_gen = pd.DataFrame()
            if not hasattr(self._pandapower_model, 'res_sgen'): self._pandapower_model.res_sgen = pd.DataFrame()
            if not hasattr(self._pandapower_model, 'res_line'): self._pandapower_model.res_line = pd.DataFrame()
            if not hasattr(self._pandapower_model, 'res_trafo'): self._pandapower_model.res_trafo = pd.DataFrame()
            if not hasattr(self._pandapower_model, 'res_storage'): self._pandapower_model.res_storage = pd.DataFrame()
            # return # Optionally return here if no results means no update needed

        # Retrieve results tables safely
        res_load = getattr(self._pandapower_model, 'res_load', pd.DataFrame())
        res_gen = getattr(self._pandapower_model, 'res_gen', pd.DataFrame())
        res_sgen = getattr(self._pandapower_model, 'res_sgen', pd.DataFrame())
        res_line = getattr(self._pandapower_model, 'res_line', pd.DataFrame())
        res_trafo = getattr(self._pandapower_model, 'res_trafo', pd.DataFrame())
        res_storage = getattr(self._pandapower_model, 'res_storage', pd.DataFrame())

        # Structure tables (ensure they exist)
        load_table = getattr(self._pandapower_model, 'load', pd.DataFrame())
        gen_table = getattr(self._pandapower_model, 'gen', pd.DataFrame())
        sgen_table = getattr(self._pandapower_model, 'sgen', pd.DataFrame())
        line_table = getattr(self._pandapower_model, 'line', pd.DataFrame())
        trafo_table = getattr(self._pandapower_model, 'trafo', pd.DataFrame())
        storage_table = getattr(self._pandapower_model, 'storage', pd.DataFrame())

        snapshot_count = 1 # Pandapower standard runpp results are for one snapshot

        # Update Loads
        for load_comp in self._input_model.loads:
            if load_comp.active and not load_table.empty and load_comp.name in load_table.index:
                 load_idx = load_table.index.get_loc(load_comp.name)
                 if not res_load.empty and 'p_mw' in res_load.columns and 0 <= load_idx < len(res_load):
                     load_comp.active_power = [res_load.p_mw.iloc[load_idx]] * snapshot_count
                     load_comp.output = [True] * snapshot_count
                 else:
                     load_comp.active_power = [0.0] * snapshot_count
                     load_comp.output = [False] * snapshot_count
            else:
                 load_comp.active_power = [0.0] * snapshot_count
                 load_comp.output = [False] * snapshot_count


        # Update Generators (both gen and sgen)
        for gen_comp in self._input_model.generators:
             if gen_comp.active:
                 p_mw = 0
                 found = False
                 output_val = False

                 # First check conventional generators (gen)
                 if not gen_table.empty and gen_comp.name in gen_table.index:
                     gen_idx = gen_table.index.get_loc(gen_comp.name)
                     if not res_gen.empty and 'p_mw' in res_gen.columns and 0 <= gen_idx < len(res_gen):
                         p_mw = res_gen.p_mw.iloc[gen_idx]
                         found = True
                         output_val = True

                 # Then check static generators (sgen) if not found in gen
                 elif not sgen_table.empty and gen_comp.name in sgen_table.index:
                     sgen_idx = sgen_table.index.get_loc(gen_comp.name)
                     if not res_sgen.empty and 'p_mw' in res_sgen.columns and 0 <= sgen_idx < len(res_sgen):
                         p_mw = res_sgen.p_mw.iloc[sgen_idx]
                         found = True
                         output_val = True

                 gen_comp.active_power = [p_mw] * snapshot_count
                 gen_comp.output = [output_val] * snapshot_count
             else:
                 gen_comp.active_power = [0.0] * snapshot_count
                 gen_comp.output = [False] * snapshot_count


        # Update Lines
        for line_comp in self._input_model.lines:
             if line_comp.active and not line_table.empty and line_comp.name in line_table.index:
                 line_idx = line_table.index.get_loc(line_comp.name)
                 if not res_line.empty and 'p_from_mw' in res_line.columns and 0 <= line_idx < len(res_line):
                     line_comp.active_power = [res_line.p_from_mw.iloc[line_idx]] * snapshot_count
                     line_comp.output = [True] * snapshot_count
                 else:
                     line_comp.active_power = [0.0] * snapshot_count
                     line_comp.output = [False] * snapshot_count
             else:
                 line_comp.active_power = [0.0] * snapshot_count
                 line_comp.output = [False] * snapshot_count


        # Update Transformers
        for trafo_comp in self._input_model.transformers:
             if trafo_comp.active and not trafo_table.empty and trafo_comp.name in trafo_table.index:
                 trafo_idx = trafo_table.index.get_loc(trafo_comp.name)
                 # Get capacity
                 trafo_comp.capacity = trafo_table.sn_mva.iloc[trafo_idx] if 'sn_mva' in trafo_table.columns else 0.0

                 if not res_trafo.empty and 'p_hv_mw' in res_trafo.columns and 0 <= trafo_idx < len(res_trafo):
                     trafo_comp.active_power_0 = [res_trafo.p_hv_mw.iloc[trafo_idx]] * snapshot_count
                     trafo_comp.output = [True] * snapshot_count
                 else:
                     trafo_comp.active_power_0 = [0.0] * snapshot_count
                     trafo_comp.output = [False] * snapshot_count
             else:
                 trafo_comp.active_power_0 = [0.0] * snapshot_count
                 trafo_comp.capacity = 0.0
                 trafo_comp.output = [False] * snapshot_count


        # Update Storage Units
        for storage_comp in self._input_model.storage_units:
             if storage_comp.active and not storage_table.empty and storage_comp.name in storage_table.index:
                 storage_idx = storage_table.index.get_loc(storage_comp.name)
                 if not res_storage.empty and 'p_mw' in res_storage.columns and 0 <= storage_idx < len(res_storage):
                     storage_comp.active_power = [res_storage.p_mw.iloc[storage_idx]] * snapshot_count
                     storage_comp.output = [True] * snapshot_count
                 else:
                      storage_comp.active_power = [0.0] * snapshot_count
                      storage_comp.output = [False] * snapshot_count
             else:
                 storage_comp.active_power = [0.0] * snapshot_count
                 storage_comp.output = [False] * snapshot_count


    def __check_or_create_table(self, table_name: str, columns) -> None:
        """Checks if a table exists in the pandapower model, creates it if not."""
        if table_name not in self._pandapower_model or not isinstance(self._pandapower_model[table_name], pd.DataFrame):
             self._pandapower_model[table_name] = pd.DataFrame(columns=columns)


    def __add_buses(self, bus_list: list[Bus]) -> None:
        """Add buses to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return # Safety check
        self.__check_or_create_table('bus', pp.elements.bus.columns)
        for bus in bus_list:
            if bus.active and bus.name not in self._pandapower_model.bus.index:
                # PandaPower uses kV, PyPSA uses v_nom (which can also be kV, check units!)
                vn_kv = bus.v_nom
                try:
                    pp.create_bus(self._pandapower_model, name=bus.name, vn_kv=vn_kv)
                except Exception as e:
                    print(f"Error adding bus {bus.name}: {e}")


    def __add_lines(self, line_list: list[Line]) -> None:
        """Add lines to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return # Safety check
        self.__check_or_create_table('line', pp.elements.line.columns)
        bus_table = getattr(self._pandapower_model, 'bus', pd.DataFrame())

        for line in line_list:
            if line.active and line.name not in self._pandapower_model.line.index:
                # Check if buses exist before trying to get index
                if line.bus0 not in bus_table.index or line.bus1 not in bus_table.index:
                     print(f"Warning: Can't add line {line.name} - bus {line.bus0} or {line.bus1} doesn't exist in the model.")
                     continue

                from_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus0)
                to_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus1)

                # Handle case where bus index lookup fails (should not happen after check above)
                if from_bus_idx is None or to_bus_idx is None:
                     print(f"Warning: Could not find index for buses {line.bus0} or {line.bus1} for line {line.name}")
                     continue

                # Use PandaPower's line creation method
                line_type = getattr(line, 'type', None) # Use type attribute if exists
                length_km = getattr(line, 'length', 1.0) # Use length if exists

                if line_type and line_type != "":
                    try:
                        pp.create_line(
                            self._pandapower_model,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=length_km,
                            std_type=line_type,
                            name=line.name
                        )
                    except Exception as e_type: # Catch specific pandapower error if type unknown
                         print(f"Warning: Couldn't create line {line.name} with type '{line_type}'. Using parameters. Error: {e_type}")
                         try:
                             pp.create_line_from_parameters(
                                 self._pandapower_model,
                                 from_bus=from_bus_idx,
                                 to_bus=to_bus_idx,
                                 length_km=length_km,
                                 r_ohm_per_km=line.r if line.r else 0.1,
                                 x_ohm_per_km=line.x if line.x else 0.1,
                                 c_nf_per_km=10, # Default capacitance
                                 max_i_ka= line.s_nom / (pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', from_bus_idx) * 1.732) if line.s_nom else 1.0, # Estimate max current
                                 name=line.name
                             )
                         except Exception as e_param:
                              print(f"Error adding line {line.name} with parameters: {e_param}")
                else:
                    # Create line from parameters
                    try:
                        pp.create_line_from_parameters(
                            self._pandapower_model,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=length_km,
                            r_ohm_per_km=line.r if line.r else 0.1,
                            x_ohm_per_km=line.x if line.x else 0.1,
                            c_nf_per_km=10, # Default capacitance
                            max_i_ka= line.s_nom / (pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', from_bus_idx) * 1.732) if line.s_nom else 1.0, # Estimate max current
                            name=line.name
                        )
                    except Exception as e_param:
                         print(f"Error adding line {line.name} with parameters: {e_param}")


    def __add_generators(self, generator_list: list[Generator]) -> None:
        """Add generators to the PandaPower model (as sgen)."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('sgen', pp.elements.sgen.columns)
        bus_table = getattr(self._pandapower_model, 'bus', pd.DataFrame())

        for gen in generator_list:
            if gen.active and gen.name not in self._pandapower_model.sgen.index:
                if gen.bus0 not in bus_table.index:
                     print(f"Warning: Can't add generator {gen.name} - bus {gen.bus0} doesn't exist.")
                     continue

                bus_idx = pp.get_element_index(self._pandapower_model, "bus", gen.bus0)
                if bus_idx is None:
                     print(f"Warning: Could not find index for bus {gen.bus0} for generator {gen.name}")
                     continue

                # Determine p_mw correctly for static value
                p_mw_val = 0
                if isinstance(gen.p_set, (int, float)):
                    p_mw_val = gen.p_set
                # Check if p_set is list-like and not empty
                elif hasattr(gen.p_set, '__len__') and not isinstance(gen.p_set, str) and len(gen.p_set) > 0:
                    p_mw_val = gen.p_set[0]  # Take first value for static representation
                elif isinstance(gen.p_nom, (int, float)) and gen.p_nom > 0:
                     p_mw_val = gen.p_nom # Fallback to p_nom if p_set is unusable

                # Determine q_mvar
                q_mvar_val = 0
                if isinstance(gen.q_set, (int, float)):
                    q_mvar_val = gen.q_set
                elif hasattr(gen.q_set, '__len__') and not isinstance(gen.q_set, str) and len(gen.q_set) > 0:
                     q_mvar_val = gen.q_set[0] # Take first value

                # PandaPower uses sgen for simple PQ generators
                try:
                    pp.create_sgen(
                        self._pandapower_model,
                        bus=bus_idx,
                        p_mw=p_mw_val,
                        q_mvar=q_mvar_val,
                        name=gen.name,
                        scaling=1.0  # For time series, here 1.0
                    )
                except Exception as e:
                    print(f"Error adding generator {gen.name}: {e}")

    def __add_loads(self, load_list: list[Load]) -> None:
        """Add loads to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('load', pp.elements.load.columns)
        bus_table = getattr(self._pandapower_model, 'bus', pd.DataFrame())

        for load in load_list:
            if load.active and load.name not in self._pandapower_model.load.index:
                if load.bus0 not in bus_table.index:
                     print(f"Warning: Can't add load {load.name} - bus {load.bus0} doesn't exist.")
                     continue

                bus_idx = pp.get_element_index(self._pandapower_model, "bus", load.bus0)
                if bus_idx is None:
                     print(f"Warning: Could not find index for bus {load.bus0} for load {load.name}")
                     continue

                # Determine p_mw correctly
                p_mw_val = 0
                if hasattr(load.p_set, '__len__') and not isinstance(load.p_set, str):
                    if len(load.p_set) > 0:
                        p_mw_val = load.p_set[0]  # Take first value
                elif isinstance(load.p_set, (int, float)):
                    p_mw_val = load.p_set  # Use the value directly

                # Determine q_mvar
                q_mvar_val = 0
                if hasattr(load.q_set, '__len__') and not isinstance(load.q_set, str):
                    if len(load.q_set) > 0:
                        q_mvar_val = load.q_set[0]  # Take first value
                elif isinstance(load.q_set, (int, float)):
                    q_mvar_val = load.q_set  # Use the value directly

                try:
                    pp.create_load(
                        self._pandapower_model,
                        bus=bus_idx,
                        p_mw=p_mw_val,
                        q_mvar=q_mvar_val,
                        name=load.name
                    )
                except Exception as e:
                     print(f"Error adding load {load.name}: {e}")

    def __add_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        """Add storage units to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('storage', pp.elements.storage.columns)
        bus_table = getattr(self._pandapower_model, 'bus', pd.DataFrame())

        for storage in storage_unit_list:
            if storage.active and storage.name not in self._pandapower_model.storage.index:
                 if storage.bus0 not in bus_table.index:
                     print(f"Warning: Can't add storage {storage.name} - bus {storage.bus0} doesn't exist.")
                     continue

                 bus_idx = pp.get_element_index(self._pandapower_model, "bus", storage.bus0)
                 if bus_idx is None:
                     print(f"Warning: Could not find index for bus {storage.bus0} for storage {storage.name}")
                     continue

                 try:
                     pp.create_storage(
                         self._pandapower_model,
                         bus=bus_idx,
                         p_mw=storage.p_nom if storage.p_nom else 0.1, # p_nom is power in MW, ensure not zero
                         max_e_mwh=storage.p_nom * 1 if storage.p_nom else 0.1,  # Max energy, placeholder (1 hour), ensure not zero
                         q_mvar=0,  # No reactive power for now
                         soc_percent=storage.state_of_charge_initial * 100 if storage.state_of_charge_initial else 50,  # SOC in %
                         name=storage.name
                     )
                 except Exception as e:
                      print(f"Error adding storage {storage.name}: {e}")


    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """Add transformers to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('trafo', pp.elements.trafo.columns)
        bus_table = getattr(self._pandapower_model, 'bus', pd.DataFrame())

        for trafo in transformer_list:
            if trafo.active and trafo.name not in self._pandapower_model.trafo.index:
                 if trafo.bus0 not in bus_table.index or trafo.bus1 not in bus_table.index:
                     print(f"Warning: Can't add transformer {trafo.name} - bus {trafo.bus0} or {trafo.bus1} doesn't exist.")
                     continue

                 hv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus0)
                 lv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus1)

                 if hv_bus_idx is None or lv_bus_idx is None:
                      print(f"Warning: Could not find index for buses {trafo.bus0} or {trafo.bus1} for transformer {trafo.name}")
                      continue

                 # Try to use standard type
                 std_type = trafo.model if trafo.model else None  # Use type from component
                 if std_type:
                    try:
                        pp.create_transformer(
                            self._pandapower_model,
                            hv_bus=hv_bus_idx,
                            lv_bus=lv_bus_idx,
                            std_type=std_type,
                            name=trafo.name
                        )
                    except Exception as e_type: # Catch specific error if std_type is invalid
                        print(f"Warning: Couldn't create transformer {trafo.name} with std_type '{std_type}'. Using parameters. Error: {e_type}")
                        # Fallback with parameters
                        try:
                            hv_vn_kv = pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', hv_bus_idx)
                            lv_vn_kv = pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', lv_bus_idx)
                            pp.create_transformer_from_parameters(
                                self._pandapower_model,
                                hv_bus=hv_bus_idx,
                                lv_bus=lv_bus_idx,
                                sn_mva=1.0, # Default capacity
                                vn_hv_kv=hv_vn_kv,
                                vn_lv_kv=lv_vn_kv,
                                vkr_percent=1.0,
                                vk_percent=6.0,
                                pfe_kw=1.0,
                                i0_percent=1.0,
                                name=trafo.name
                            )
                        except Exception as e_param:
                             print(f"Error adding transformer {trafo.name} with parameters: {e_param}")
                 else:
                    print(f"Warning: No std_type defined for transformer {trafo.name}. Using parameters.")
                    # Fallback with parameters
                    try:
                         hv_vn_kv = pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', hv_bus_idx)
                         lv_vn_kv = pp.get_element_property(self._pandapower_model, 'bus', 'vn_kv', lv_bus_idx)
                         pp.create_transformer_from_parameters(
                             self._pandapower_model,
                             hv_bus=hv_bus_idx,
                             lv_bus=lv_bus_idx,
                             sn_mva=1.0, # Default capacity
                             vn_hv_kv=hv_vn_kv,
                             vn_lv_kv=lv_vn_kv,
                             vkr_percent=1.0,
                             vk_percent=6.0,
                             pfe_kw=1.0,
                             i0_percent=1.0,
                             name=trafo.name
                         )
                    except Exception as e_param:
                         print(f"Error adding transformer {trafo.name} with parameters: {e_param}")

    # --- Methods for removing (simplified) ---
    def __remove_elements(self, table_name: str, name_list: list[str]) -> None:
         """Removes elements from a specified table by name."""
         if not isinstance(self._pandapower_model, dict) or table_name not in self._pandapower_model:
             return

         current_table = self._pandapower_model[table_name]
         if not isinstance(current_table, pd.DataFrame) or current_table.empty:
             return

         # Find indices of names to remove
         indices_to_drop = current_table[current_table.index.isin(name_list)].index

         if not indices_to_drop.empty:
             try:
                 # Use the specific drop function if available, otherwise generic DataFrame drop
                 drop_func_name = f"drop_{table_name}s" # e.g., drop_buses, drop_lines
                 if hasattr(pp, drop_func_name):
                     drop_func = getattr(pp, drop_func_name)
                     drop_func(self._pandapower_model, indices_to_drop.tolist())
                 else:
                      # Generic fallback if no specific drop function exists (less safe)
                      self._pandapower_model[table_name] = current_table.drop(index=indices_to_drop)
                      print(f"Warning: Used generic drop for table '{table_name}'.")
             except Exception as e:
                 print(f"Error removing elements from {table_name} table: {e}")


    def __remove_buses(self, bus_list: list[Bus]) -> None:
         self.__remove_elements("bus", [bus.name for bus in bus_list if bus.active])

    def __remove_lines(self, line_list: list[Line]) -> None:
         self.__remove_elements("line", [line.name for line in line_list if line.active])

    def __remove_generators(self, generator_list: list[Generator]) -> None:
        # Generators can be in 'gen' or 'sgen' table
        active_gen_names = [gen.name for gen in generator_list if gen.active]
        self.__remove_elements("sgen", active_gen_names)
        self.__remove_elements("gen", active_gen_names)


    def __remove_loads(self, load_list: list[Load]) -> None:
        self.__remove_elements("load", [load.name for load in load_list if load.active])

    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        self.__remove_elements("storage", [storage.name for storage in storage_unit_list if storage.active])

    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:
        self.__remove_elements("trafo", [trafo.name for trafo in transformers_list if trafo.active])


    # --- Implementation of Interface Methods ---
    def calculate(self) -> bool:
        """
        Start a PandaPower Power Flow calculation (default: runpp).
        @return bool True = success, False = Error
        """
        start_time = time.perf_counter()
        self.reset_lines()  # Reset our own model results

        # Ensure the model is a pandapower network dict
        if not isinstance(self._pandapower_model, dict):
             self._calculation_time = time.perf_counter() - start_time
             self._status = "failed"
             self._condition = "model not initialized"
             print("Error: Pandapower model is not initialized.")
             return False

        # Check for essential components before running calculation
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        gen_table = self._pandapower_model.get('gen', pd.DataFrame())
        sgen_table = self._pandapower_model.get('sgen', pd.DataFrame())
        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())

        if bus_table.empty:
             self._calculation_time = time.perf_counter() - start_time
             self._status = "failed"
             self._condition = "no buses in model"
             print("Error: No buses found in the Pandapower model.")
             return False

        if gen_table.empty and sgen_table.empty and ext_grid_table.empty:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no generation source"
            print("Error: No generator, sgen, or external grid found in PandaPower model.")
            return False

        success = True
        try:
            # Run standard power flow
            pp.runpp(self._pandapower_model, algorithm='nr', calculate_voltage_angles=True, numba=False) # Disable numba for broader compatibility
            self._status = "ok"
            self._condition = "converged" # Assumption: runpp success means convergence
            self.retrieve_results()
        except pp.LoadflowNotConverged as e:
            self._status = "failed"
            self._condition = "loadflow not converged"
            print(f"Error: PandaPower loadflow did not converge: {e}")
            success = False
        except Exception as e:
            self._status = "failed"
            self._condition = f"exception: {e}"
            print(f"Error during PandaPower calculation: {e}")
            success = False

        self._calculation_time = time.perf_counter() - start_time
        return success

    def get_status(self) -> str:
        return self._status

    def get_condition(self) -> str:
        return self._condition

    def get_calculation_time(self) -> float:
        return self._calculation_time

    def get_network_build_time(self) -> float:
        return self._network_build_time

    def export_result(self, file_path: str) -> None:
        """
        Export the PandaPower model result.
        @param file_path str Directory to save results
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot export results, Pandapower model not initialized.")
             return

        # Create directory if needed
        if not path.exists(file_path):
            try:
                 makedirs(file_path)
            except OSError as e:
                 print(f"Error creating directory {file_path}: {e}")
                 return

        # Save to Excel (or other formats like pickle)
        export_filepath = path.join(file_path, "pandapower_results.xlsx")
        try:
            pp.to_excel(self._pandapower_model, export_filepath)
            print(f"Successfully exported PandaPower results to {export_filepath}")
        except Exception as e:
            print(f"Error exporting PandaPower results to {export_filepath}: {e}")


    def set_input_model(self, input_model: Model) -> None:
        """
        Set the input model.
        @param input_model Model
        """
        self._input_model = input_model

    def set_snapshots(self, snapshots: list) -> None:
        """
        Set the simulation snapshot list.
        @param snapshots list
        """
        # PandaPower handles time series differently, snapshots might be less directly relevant
        # for standard runpp. We still store them for interface consistency.
        self.snapshots = snapshots if isinstance(snapshots, list) else [0]


    def build_model(self) -> None:
        """
        Build the PandaPower model based on input_model.
        Uses a full rebuild approach for robustness.
        """
        start_time = time.perf_counter()

        # Ensure input model is set
        if self._input_model is None:
             print("Error: Input model is not set. Cannot build PandaPower model.")
             self._network_build_time = (time.perf_counter() - start_time)
             return

        # Perform a full rebuild
        try:
            # Re-initialize the pandapower model safely
            try:
                self._pandapower_model = pp.create_empty_network()
            except Exception as e_init:
                print(f"Error re-initializing empty network: {e_init}. Attempting manual init.")
                self.__init__() # Re-run constructor's fallback logic

            # Check if model is usable after init/fallback
            if not isinstance(self._pandapower_model, dict):
                 raise ValueError("Pandapower model could not be initialized.")

            self.force_build()  # Build everything anew
            # Save a copy for potential future selective builds (if implemented)
            self._previous_model = deepcopy(self._input_model)

        except Exception as e:
            print(f"Error during model build: {e}")
            # Ensure model is at least an empty dict on failure
            if not isinstance(self._pandapower_model, dict):
                 self._pandapower_model = {}

        self._network_build_time = (time.perf_counter() - start_time)


    def force_build(self):
        """Build all components anew in PandaPower."""
        # Add components
        if self._input_model:
             # Order matters: buses first
             self.__add_buses(getattr(self._input_model, 'buses', []))
             self.__add_lines(getattr(self._input_model, 'lines', []))
             self.__add_generators(getattr(self._input_model, 'generators', []))
             self.__add_loads(getattr(self._input_model, 'loads', []))
             self.__add_storage_units(getattr(self._input_model, 'storage_units', []))
             self.__add_transformers(getattr(self._input_model, 'transformers', []))
        else:
            print("Warning: No input model set for force_build.")
            return False # Indicate failure

        # Important: PandaPower often needs a 'slack bus' (external grid)
        # Add one here if it doesn't exist yet and there are buses.
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())

        if ext_grid_table.empty and not bus_table.empty:
            # Try to find a bus marked as reference in the input model
            ref_bus_name = None
            if self._input_model:
                 for bus_comp in getattr(self._input_model, 'buses', []):
                      # Assuming 'is_ref' attribute exists, add it if not
                      if getattr(bus_comp, 'is_ref', False):
                          ref_bus_name = bus_comp.name
                          break

            # Use the found reference bus or fallback to the first bus
            target_bus_name = ref_bus_name if ref_bus_name and ref_bus_name in bus_table.index else bus_table.index[0]
            bus_idx = pp.get_element_index(self._pandapower_model, "bus", target_bus_name)

            if bus_idx is not None:
                 # Check if an ext_grid already exists for this bus_idx
                 if ext_grid_table.empty or not (ext_grid_table['bus'] == bus_idx).any():
                     try:
                         pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name="External Grid")
                         print(f"Warning: No external grid found, automatically added to bus '{target_bus_name}' as slack.")
                     except Exception as e:
                          print(f"Error adding external grid to bus {target_bus_name}: {e}")
                 else:
                      print(f"Info: External grid already exists for bus index {bus_idx}.")
            else:
                 print(f"Warning: Could not find index for target slack bus '{target_bus_name}'.")

        return True # Indicate success


    def selective_build(self):
        """
        Selective building (complex in PandaPower). For now we call force_build.
        A real implementation would track differences and use pp.drop/create.
        """
        print("Info: Selective building requested, performing full rebuild for robustness.")
        self.force_build()


    def set_calculation_method(self, method: str) -> None:
        # PandaPower doesn't have direct equivalents for 'lopf', 'lpf', 'optimize' like PyPSA.
        # runpp() is the standard power flow. Optimization requires pp.runopp().
        # This method is kept for interface compatibility but doesn't change runpp behavior here.
        print(f"Info: PandaPower builder received set_calculation_method('{method}'). Standard runpp will be used by default calculate().")
        pass

    # Helper methods for tests (added from original test file)
    def add_bus(self, name, voltage=110, is_ref=False):
        """
        Add a bus to the network with given parameters.
        Added for the test interface.

        @param name str The name of the bus
        @param voltage float Nominal voltage in kV
        @param is_ref bool Whether this bus is a reference bus (slack bus)
        @return int The bus index or None if failed
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add bus, model not initialized.")
             return None
        self.__check_or_create_table('bus', pp.elements.bus.columns)
        bus_idx = None
        try:
            bus_idx = pp.create_bus(self._pandapower_model, name=name, vn_kv=voltage)

            if is_ref:
                 self.__check_or_create_table('ext_grid', pp.elements.ext_grid.columns)
                 # Ensure no ext_grid already exists for this bus
                 if self._pandapower_model['ext_grid'].empty or not (self._pandapower_model['ext_grid']['bus'] == bus_idx).any():
                     pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name=f"ExtGrid_{name}")
                 else:
                     print(f"Info: External grid already exists for bus index {bus_idx} ({name}).")

        except Exception as e:
             print(f"Error adding bus {name} for testing: {e}")
             return None
        return bus_idx

    def add_generator(self, bus, p_mw, name=None):
        """
        Add a generator (as sgen) to the network.
        Added for the test interface.

        @param bus int The bus index to connect the generator to
        @param p_mw float The active power in MW
        @param name str Optional name for the generator
        @return int The generator index or None if failed
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add generator, model not initialized.")
             return None
        self.__check_or_create_table('sgen', pp.elements.sgen.columns)
        gen_name = name if name else f"SGen_Bus{bus}"
        gen_idx = None
        try:
            gen_idx = pp.create_sgen(self._pandapower_model, bus=bus, p_mw=p_mw, name=gen_name)
        except Exception as e:
             print(f"Error adding generator to bus {bus} for testing: {e}")
             return None
        return gen_idx

    def add_load(self, bus, p_mw, name=None):
        """
        Add a load to the network.
        Added for the test interface.

        @param bus int The bus index to connect the load to
        @param p_mw float The active power in MW
        @param name str Optional name for the load
        @return int The load index or None if failed
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add load, model not initialized.")
             return None
        self.__check_or_create_table('load', pp.elements.load.columns)
        load_name = name if name else f"Load_Bus{bus}"
        load_idx = None
        try:
            load_idx = pp.create_load(self._pandapower_model, bus=bus, p_mw=p_mw, name=load_name)
        except Exception as e:
             print(f"Error adding load to bus {bus} for testing: {e}")
             return None
        return load_idx

    def add_line(self, from_bus, to_bus, length_km=1.0, std_type="NAYY 4x50 SE", name=None):
        """
        Add a line to the network.
        Added for the test interface.

        @param from_bus int The from bus index
        @param to_bus int The to bus index
        @param length_km float Line length in km
        @param std_type str The standard line type
        @param name str Optional name for the line
        @return int The line index or None if failed
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add line, model not initialized.")
             return None
        self.__check_or_create_table('line', pp.elements.line.columns)
        line_name = name if name else f"Line_{from_bus}-{to_bus}"
        line_idx = None
        try:
            line_idx = pp.create_line(self._pandapower_model, from_bus=from_bus, to_bus=to_bus,
                                     length_km=length_km, std_type=std_type, name=line_name)
        except Exception as e_type: # Catch error if std_type unknown
             print(f"Warning: std_type '{std_type}' not found for line {line_name}. Using parameters. Error: {e_type}")
             try:
                 line_idx = pp.create_line_from_parameters(self._pandapower_model, from_bus=from_bus,
                                                         to_bus=to_bus, length_km=length_km,
                                                         r_ohm_per_km=0.1, x_ohm_per_km=0.1,
                                                         c_nf_per_km=10, max_i_ka=1, name=line_name)
             except Exception as e_param:
                  print(f"Error adding line {line_name} with parameters: {e_param}")
                  return None
        return line_idx

    def add_transformer(self, hv_bus, lv_bus, std_type="25 MVA 110/20 kV", name=None):
        """
        Add a transformer to the network.
        Added for the test interface.

        @param hv_bus int The high voltage bus index
        @param lv_bus int The low voltage bus index
        @param std_type str The standard transformer type
        @param name str Optional name for the transformer
        @return int The transformer index or None if failed
        """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add transformer, model not initialized.")
             return None
        self.__check_or_create_table('trafo', pp.elements.trafo.columns)
        trafo_name = name if name else f"Trafo_{hv_bus}-{lv_bus}"
        trafo_idx = None
        try:
            trafo_idx = pp.create_transformer(self._pandapower_model, hv_bus=hv_bus, lv_bus=lv_bus, std_type=std_type, name=trafo_name)
        except Exception as e_type: # Catch error if std_type unknown
            print(f"Warning: std_type '{std_type}' not found for transformer {trafo_name}. Using parameters. Error: {e_type}")
            try:
                # Get voltages from bus table
                bus_table = self._pandapower_model.get('bus', pd.DataFrame())
                if hv_bus in bus_table.index and lv_bus in bus_table.index:
                     hv_vn_kv = bus_table.vn_kv[hv_bus]
                     lv_vn_kv = bus_table.vn_kv[lv_bus]
                     trafo_idx = pp.create_transformer_from_parameters(
                         self._pandapower_model,
                         hv_bus=hv_bus,
                         lv_bus=lv_bus,
                         sn_mva=25.0,  # Default rating
                         vn_hv_kv=hv_vn_kv,
                         vn_lv_kv=lv_vn_kv,
                         vkr_percent=0.5,  # Default resistance
                         vk_percent=6.0,   # Default impedance
                         pfe_kw=5.0,       # Default iron losses
                         i0_percent=0.1,   # Default no-load current
                         shift_degree=0.0,
                         name=trafo_name
                     )
                else:
                    print(f"Error: Could not find HV ({hv_bus}) or LV ({lv_bus}) bus index for transformer {trafo_name} fallback.")
                    return None
            except Exception as e_param:
                print(f"Error adding transformer {trafo_name} with parameters: {e_param}")
                return None
        return trafo_idx

    def run_power_flow(self):
        """
        Run a power flow calculation on the network.
        Added for the test interface.

        @return bool True if the power flow calculation was successful, False otherwise
        """
        return self.calculate() # Use the main calculate method

    def get_results(self):
        """
        Get the results of the power flow calculation.
        Added for the test interface.

        @return dict A dictionary with the results or None if failed/no results
        """
        if not isinstance(self._pandapower_model, dict): return None

        # Ensure result tables exist before accessing columns
        res_bus = getattr(self._pandapower_model, 'res_bus', pd.DataFrame())
        res_line = getattr(self._pandapower_model, 'res_line', pd.DataFrame())
        res_trafo = getattr(self._pandapower_model, 'res_trafo', pd.DataFrame())

        if res_bus.empty: # Check if essential results are missing
             print("Warning: Bus results are empty.")
             # return None # Optionally return None if bus results are essential

        results = {
            'bus_results': res_bus.copy(),
            'line_results': res_line.copy(),
            'trafo_results': res_trafo.copy(),
            # Add other result tables if needed (res_gen, res_sgen, etc.)
        }

        return results

    def print_network_info(self):
        """
        Print information about the network.
        Added for the test interface.
        """
        if not isinstance(self._pandapower_model, dict):
             print("Network model not initialized.")
             return

        print("\nNetwork Information:")
        print(f"Number of buses: {len(self._pandapower_model.get('bus', pd.DataFrame()))}")
        print(f"Number of lines: {len(self._pandapower_model.get('line', pd.DataFrame()))}")
        print(f"Number of transformers: {len(self._pandapower_model.get('trafo', pd.DataFrame()))}")
        print(f"Number of generators (gen): {len(self._pandapower_model.get('gen', pd.DataFrame()))}")
        print(f"Number of static generators (sgen): {len(self._pandapower_model.get('sgen', pd.DataFrame()))}")
        print(f"Number of loads: {len(self._pandapower_model.get('load', pd.DataFrame()))}")
        print(f"Number of storage units: {len(self._pandapower_model.get('storage', pd.DataFrame()))}")

        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        if not bus_table.empty and 'vn_kv' in bus_table.columns:
            voltage_levels = bus_table.vn_kv.unique()
            print(f"Voltage levels: {', '.join([f'{v} kV' for v in sorted(voltage_levels)])}")

        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())
        if not ext_grid_table.empty and 'bus' in ext_grid_table.columns:
             print("External grids at buses:", end=" ")
             bus_names = bus_table.get('name', pd.Series(dtype=str)) # Get names if available
             for i, idx in enumerate(ext_grid_table.bus.values):
                 # Use bus name if available, otherwise use index
                 bus_display = bus_names.get(idx, f"Index {idx}") if not bus_names.empty else f"Index {idx}"
                 print(f"{bus_display}", end=", " if i < len(ext_grid_table) - 1 else "")
             print()