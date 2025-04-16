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
            # We don't rely on pp.elements here for compatibility
            if 'bus' not in self._pandapower_model or not isinstance(self._pandapower_model['bus'], pd.DataFrame):
                 self._pandapower_model['bus'] = pd.DataFrame()
            if 'line' not in self._pandapower_model or not isinstance(self._pandapower_model['line'], pd.DataFrame):
                 self._pandapower_model['line'] = pd.DataFrame()
            # Add similar checks/creations for other core tables if needed for robustness
            # e.g., load, sgen, ext_grid, trafo

        except Exception as e:
            # Fallback: If create_empty_network fails, manually create a minimal structure
            # This avoids pp.elements and pp.toolbox.create_empty_network_from_dict
            print(f"Error creating empty pandapower network: {e}. Attempting basic fallback.")
            # Basic fallback: create an empty dict and let element creation add tables/columns
            self._pandapower_model = {
                'bus': pd.DataFrame(),
                'line': pd.DataFrame(),
                'trafo': pd.DataFrame(),
                'gen': pd.DataFrame(),
                'sgen': pd.DataFrame(),
                'load': pd.DataFrame(),
                'ext_grid': pd.DataFrame(),
                'storage': pd.DataFrame(),
                '_ppc': None, # Placeholder for internal pandapower structure
                'version': getattr(pp, '__version__', 'unknown'), # Get version safely
                'converged': False,
                'name': 'Fallback Initialized Network'
            }

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
        # Check for basic result tables, but don't require them to be non-empty initially
        # if not hasattr(self._pandapower_model, 'res_bus'):
        #     print("Warning: No bus results available in PandaPower model.")
            # return # Optionally return if bus results are essential

        # Retrieve results tables safely using .get() with default empty DataFrame
        res_load = self._pandapower_model.get('res_load', pd.DataFrame())
        res_gen = self._pandapower_model.get('res_gen', pd.DataFrame())
        res_sgen = self._pandapower_model.get('res_sgen', pd.DataFrame())
        res_line = self._pandapower_model.get('res_line', pd.DataFrame())
        res_trafo = self._pandapower_model.get('res_trafo', pd.DataFrame())
        res_storage = self._pandapower_model.get('res_storage', pd.DataFrame())

        # Structure tables (ensure they exist using .get())
        load_table = self._pandapower_model.get('load', pd.DataFrame())
        gen_table = self._pandapower_model.get('gen', pd.DataFrame())
        sgen_table = self._pandapower_model.get('sgen', pd.DataFrame())
        line_table = self._pandapower_model.get('line', pd.DataFrame())
        trafo_table = self._pandapower_model.get('trafo', pd.DataFrame())
        storage_table = self._pandapower_model.get('storage', pd.DataFrame())

        snapshot_count = 1 # Pandapower standard runpp results are for one snapshot

        # --- Update Input Model Components ---
        if self._input_model is None:
             print("Warning: Input model not set, cannot update results.")
             return

        # Update Loads
        for load_comp in getattr(self._input_model, 'loads', []):
            if load_comp.active and not load_table.empty and load_comp.name in load_table.index:
                 load_idx = load_table.index.get_loc(load_comp.name)
                 # Check if result table and column exist and index is valid
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
        for gen_comp in getattr(self._input_model, 'generators', []):
             if gen_comp.active:
                 p_mw = 0
                 output_val = False

                 # Check conventional generators (gen)
                 if not gen_table.empty and gen_comp.name in gen_table.index:
                     gen_idx = gen_table.index.get_loc(gen_comp.name)
                     if not res_gen.empty and 'p_mw' in res_gen.columns and 0 <= gen_idx < len(res_gen):
                         p_mw = res_gen.p_mw.iloc[gen_idx]
                         output_val = True

                 # Check static generators (sgen)
                 elif not sgen_table.empty and gen_comp.name in sgen_table.index:
                     sgen_idx = sgen_table.index.get_loc(gen_comp.name)
                     if not res_sgen.empty and 'p_mw' in res_sgen.columns and 0 <= sgen_idx < len(res_sgen):
                         p_mw = res_sgen.p_mw.iloc[sgen_idx]
                         output_val = True

                 gen_comp.active_power = [p_mw] * snapshot_count
                 gen_comp.output = [output_val] * snapshot_count
             else:
                 gen_comp.active_power = [0.0] * snapshot_count
                 gen_comp.output = [False] * snapshot_count


        # Update Lines
        for line_comp in getattr(self._input_model, 'lines', []):
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
        for trafo_comp in getattr(self._input_model, 'transformers', []):
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
        for storage_comp in getattr(self._input_model, 'storage_units', []):
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


    def __check_or_create_table(self, table_name: str) -> None:
        """Checks if a table exists in the pandapower model, creates it if not."""
        # Ensure model is a dict
        if not isinstance(self._pandapower_model, dict):
             # Attempt to re-initialize if model structure is lost
             print(f"Warning: pandapower_model is not a dict in __check_or_create_table for '{table_name}'. Re-initializing.")
             self.__init__() # This will run the try/except logic again
             # Check again after re-init
             if not isinstance(self._pandapower_model, dict):
                 print(f"Fatal Error: Could not recover pandapower_model structure.")
                 return # Cannot proceed

        # Check if table exists and is a DataFrame
        if table_name not in self._pandapower_model or not isinstance(self._pandapower_model.get(table_name), pd.DataFrame):
             # Create an empty DataFrame without specifying columns from pp.elements
             self._pandapower_model[table_name] = pd.DataFrame()
             print(f"Info: Created empty DataFrame for table '{table_name}'.")


    def __add_buses(self, bus_list: list[Bus]) -> None:
        """Add buses to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return # Safety check
        self.__check_or_create_table('bus') # Ensure bus table exists
        bus_table = self._pandapower_model.get('bus', pd.DataFrame()) # Get safely

        for bus in bus_list:
            # Check if bus already exists by name (pandapower uses index names)
            bus_name_exists = not bus_table.empty and bus.name in bus_table.index

            if bus.active and not bus_name_exists:
                vn_kv = bus.v_nom
                try:
                    pp.create_bus(self._pandapower_model, name=bus.name, vn_kv=vn_kv)
                except Exception as e:
                    # Catch potential exceptions during creation (e.g., invalid name format)
                    print(f"Error adding bus {bus.name}: {e}")


    def __add_lines(self, line_list: list[Line]) -> None:
        """Add lines to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return # Safety check
        self.__check_or_create_table('line') # Ensure line table exists
        self.__check_or_create_table('bus')  # Ensure bus table exists
        line_table = self._pandapower_model.get('line', pd.DataFrame())
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())

        for line in line_list:
            line_name_exists = not line_table.empty and line.name in line_table.index
            if line.active and not line_name_exists:
                # Check if buses exist before trying to get index
                if bus_table.empty or line.bus0 not in bus_table.index or line.bus1 not in bus_table.index:
                     print(f"Warning: Can't add line {line.name} - bus {line.bus0} or {line.bus1} doesn't exist in the model.")
                     continue

                # Get bus indices safely
                try:
                     from_bus_idx = bus_table.index.get_loc(line.bus0)
                     to_bus_idx = bus_table.index.get_loc(line.bus1)
                except KeyError:
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
                             # Estimate max_i_ka based on bus voltage and default Snom if line.s_nom not available
                             vn_kv = bus_table.vn_kv.iloc[from_bus_idx] if 'vn_kv' in bus_table.columns else 1.0
                             s_nom_mva = line.s_nom if getattr(line, 's_nom', None) else 1.0 # Default 1 MVA if s_nom missing
                             max_i_ka = s_nom_mva / (vn_kv * 1.732) if vn_kv > 0 else 1.0

                             pp.create_line_from_parameters(
                                 self._pandapower_model,
                                 from_bus=from_bus_idx,
                                 to_bus=to_bus_idx,
                                 length_km=length_km,
                                 r_ohm_per_km=line.r if getattr(line, 'r', None) is not None else 0.1,
                                 x_ohm_per_km=line.x if getattr(line, 'x', None) is not None else 0.1,
                                 c_nf_per_km=10, # Default capacitance
                                 max_i_ka=max_i_ka,
                                 name=line.name
                             )
                         except Exception as e_param:
                              print(f"Error adding line {line.name} with parameters: {e_param}")
                else:
                    # Create line from parameters
                    try:
                        vn_kv = bus_table.vn_kv.iloc[from_bus_idx] if 'vn_kv' in bus_table.columns else 1.0
                        s_nom_mva = line.s_nom if getattr(line, 's_nom', None) else 1.0 # Default 1 MVA if s_nom missing
                        max_i_ka = s_nom_mva / (vn_kv * 1.732) if vn_kv > 0 else 1.0

                        pp.create_line_from_parameters(
                            self._pandapower_model,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=length_km,
                            r_ohm_per_km=line.r if getattr(line, 'r', None) is not None else 0.1,
                            x_ohm_per_km=line.x if getattr(line, 'x', None) is not None else 0.1,
                            c_nf_per_km=10, # Default capacitance
                            max_i_ka=max_i_ka,
                            name=line.name
                        )
                    except Exception as e_param:
                         print(f"Error adding line {line.name} with parameters: {e_param}")


    def __add_generators(self, generator_list: list[Generator]) -> None:
        """Add generators to the PandaPower model (as sgen)."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('sgen')
        self.__check_or_create_table('bus')
        sgen_table = self._pandapower_model.get('sgen', pd.DataFrame())
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())

        for gen in generator_list:
            gen_name_exists = not sgen_table.empty and gen.name in sgen_table.index
            if gen.active and not gen_name_exists:
                if bus_table.empty or gen.bus0 not in bus_table.index:
                     print(f"Warning: Can't add generator {gen.name} - bus {gen.bus0} doesn't exist.")
                     continue
                try:
                     bus_idx = bus_table.index.get_loc(gen.bus0)
                except KeyError:
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
        self.__check_or_create_table('load')
        self.__check_or_create_table('bus')
        load_table = self._pandapower_model.get('load', pd.DataFrame())
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())

        for load in load_list:
            load_name_exists = not load_table.empty and load.name in load_table.index
            if load.active and not load_name_exists:
                if bus_table.empty or load.bus0 not in bus_table.index:
                     print(f"Warning: Can't add load {load.name} - bus {load.bus0} doesn't exist.")
                     continue
                try:
                     bus_idx = bus_table.index.get_loc(load.bus0)
                except KeyError:
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
        self.__check_or_create_table('storage')
        self.__check_or_create_table('bus')
        storage_table = self._pandapower_model.get('storage', pd.DataFrame())
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())

        for storage in storage_unit_list:
            storage_name_exists = not storage_table.empty and storage.name in storage_table.index
            if storage.active and not storage_name_exists:
                 if bus_table.empty or storage.bus0 not in bus_table.index:
                     print(f"Warning: Can't add storage {storage.name} - bus {storage.bus0} doesn't exist.")
                     continue
                 try:
                     bus_idx = bus_table.index.get_loc(storage.bus0)
                 except KeyError:
                     print(f"Warning: Could not find index for bus {storage.bus0} for storage {storage.name}")
                     continue

                 # Use getattr for safe access to attributes, provide defaults
                 p_nom_mw = getattr(storage, 'p_nom', 0.1)
                 max_e_mwh = p_nom_mw * 1 # Default 1 hour capacity
                 soc_init = getattr(storage, 'state_of_charge_initial', 0.5) # Default 50%

                 try:
                     pp.create_storage(
                         self._pandapower_model,
                         bus=bus_idx,
                         p_mw=p_nom_mw if p_nom_mw > 0 else 0.1, # Ensure not zero
                         max_e_mwh=max_e_mwh if max_e_mwh > 0 else 0.1, # Ensure not zero
                         q_mvar=0,  # No reactive power for now
                         soc_percent=soc_init * 100 if soc_init else 50,  # SOC in %
                         name=storage.name
                     )
                 except Exception as e:
                      print(f"Error adding storage {storage.name}: {e}")


    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """Add transformers to the PandaPower model."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('trafo')
        self.__check_or_create_table('bus')
        trafo_table = self._pandapower_model.get('trafo', pd.DataFrame())
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())

        for trafo in transformer_list:
            trafo_name_exists = not trafo_table.empty and trafo.name in trafo_table.index
            if trafo.active and not trafo_name_exists:
                 if bus_table.empty or trafo.bus0 not in bus_table.index or trafo.bus1 not in bus_table.index:
                     print(f"Warning: Can't add transformer {trafo.name} - bus {trafo.bus0} or {trafo.bus1} doesn't exist.")
                     continue
                 try:
                     hv_bus_idx = bus_table.index.get_loc(trafo.bus0)
                     lv_bus_idx = bus_table.index.get_loc(trafo.bus1)
                 except KeyError:
                      print(f"Warning: Could not find index for buses {trafo.bus0} or {trafo.bus1} for transformer {trafo.name}")
                      continue

                 # Try to use standard type
                 std_type = getattr(trafo, 'model', None) # Use 'model' attribute for std_type
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
                            hv_vn_kv = bus_table.vn_kv.iloc[hv_bus_idx] if 'vn_kv' in bus_table.columns else 110.0 # Default HV
                            lv_vn_kv = bus_table.vn_kv.iloc[lv_bus_idx] if 'vn_kv' in bus_table.columns else 20.0  # Default MV
                            pp.create_transformer_from_parameters(
                                self._pandapower_model,
                                hv_bus=hv_bus_idx,
                                lv_bus=lv_bus_idx,
                                sn_mva= getattr(trafo, 's_nom', 1.0), # Use s_nom if available, else 1.0 MVA
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
                    print(f"Warning: No std_type (model attribute) defined for transformer {trafo.name}. Using parameters.")
                    # Fallback with parameters
                    try:
                         hv_vn_kv = bus_table.vn_kv.iloc[hv_bus_idx] if 'vn_kv' in bus_table.columns else 110.0 # Default HV
                         lv_vn_kv = bus_table.vn_kv.iloc[lv_bus_idx] if 'vn_kv' in bus_table.columns else 20.0  # Default MV
                         pp.create_transformer_from_parameters(
                             self._pandapower_model,
                             hv_bus=hv_bus_idx,
                             lv_bus=lv_bus_idx,
                             sn_mva= getattr(trafo, 's_nom', 1.0), # Use s_nom if available, else 1.0 MVA
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
             # print(f"Info: Table '{table_name}' not found for removal.")
             return

         current_table = self._pandapower_model.get(table_name)
         if not isinstance(current_table, pd.DataFrame) or current_table.empty:
             # print(f"Info: Table '{table_name}' is empty or not a DataFrame.")
             return

         # Find indices of names to remove that actually exist in the table
         indices_to_drop = current_table[current_table.index.isin(name_list)].index

         if not indices_to_drop.empty:
             try:
                 # Use the specific drop function if available (preferred)
                 drop_func_name = f"drop_{table_name}s" # e.g., drop_buses, drop_lines
                 if hasattr(pp, drop_func_name):
                     drop_func = getattr(pp, drop_func_name)
                     # Pandapower drop functions expect indices (integers), not names directly
                     drop_func(self._pandapower_model, indices_to_drop.tolist())
                 else:
                      # Generic DataFrame drop (less safe as it doesn't handle pandapower internals)
                      self._pandapower_model[table_name] = current_table.drop(index=indices_to_drop)
                      print(f"Warning: Used generic DataFrame drop for table '{table_name}'.")
             except Exception as e:
                 print(f"Error removing elements from {table_name} table: {e}")
         # else:
             # print(f"Info: No elements from the list found in table '{table_name}' for removal.")


    def __remove_buses(self, bus_list: list[Bus]) -> None:
         self.__remove_elements("bus", [bus.name for bus in bus_list if getattr(bus, 'active', True)])

    def __remove_lines(self, line_list: list[Line]) -> None:
         self.__remove_elements("line", [line.name for line in line_list if getattr(line, 'active', True)])

    def __remove_generators(self, generator_list: list[Generator]) -> None:
        # Generators can be in 'gen' or 'sgen' table
        active_gen_names = [gen.name for gen in generator_list if getattr(gen, 'active', True)]
        self.__remove_elements("sgen", active_gen_names)
        self.__remove_elements("gen", active_gen_names)

    def __remove_loads(self, load_list: list[Load]) -> None:
        self.__remove_elements("load", [load.name for load in load_list if getattr(load, 'active', True)])

    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        self.__remove_elements("storage", [storage.name for storage in storage_unit_list if getattr(storage, 'active', True)])

    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:
        self.__remove_elements("trafo", [trafo.name for trafo in transformers_list if getattr(trafo, 'active', True)])


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

        # A slack is required: either ext_grid or a gen defined as slack
        is_slack_gen = not gen_table.empty and 'slack' in gen_table.columns and gen_table['slack'].any()
        if ext_grid_table.empty and not is_slack_gen :
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no slack bus defined (no ext_grid or slack gen)"
            print("Error: No slack bus defined in PandaPower model.")
            return False

        success = True
        try:
            # Run standard power flow
            pp.runpp(self._pandapower_model, algorithm='nr', calculate_voltage_angles=True, numba=False) # Disable numba for broader compatibility
            self._status = "ok"
            self._condition = "converged" # Assumption: runpp success means convergence
            self.retrieve_results()
        except pp.LoadflowNotConverged as e:
            # Try a different solver as fallback? (e.g., 'gs' - Gauss-Seidel)
            # print(f"NR Loadflow failed: {e}. Trying Gauss-Seidel.")
            # try:
            #     pp.runpp(self._pandapower_model, algorithm='gs', numba=False)
            #     self._status = "ok (gs)"
            #     self._condition = "converged (gs)"
            #     self.retrieve_results()
            # except pp.LoadflowNotConverged as e_gs:
            #     self._status = "failed"
            #     self._condition = "loadflow not converged (nr and gs)"
            #     print(f"Error: PandaPower loadflow did not converge with NR or GS: {e_gs}")
            #     success = False
            # except Exception as e_gs_other:
            #      self._status = "failed"
            #      self._condition = f"exception during gs: {e_gs_other}"
            #      print(f"Error during PandaPower GS calculation: {e_gs_other}")
            #      success = False
            # else: # Original NR exception
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
            # print(f"Successfully exported PandaPower results to {export_filepath}")
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
        # PandaPower standard runpp doesn't use snapshots directly like PyPSA LOPF.
        # Store for interface consistency.
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
            # Re-initialize the pandapower model safely using the __init__ logic
            self.__init__()

            # Check if model is usable after init/fallback
            if not isinstance(self._pandapower_model, dict):
                 raise ValueError("Pandapower model could not be initialized.")

            build_success = self.force_build()  # Build everything anew
            if not build_success:
                 print("Warning: force_build indicated potential issues.")

            # Save a copy for potential future selective builds (if implemented)
            # Ensure deepcopy handles the structure correctly
            try:
                self._previous_model = deepcopy(self._input_model)
            except Exception as copy_e:
                print(f"Warning: Could not deepcopy input model: {copy_e}")
                self._previous_model = None


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
             # Add ext_grid early if specified by is_ref on bus component
             self.__add_initial_ext_grids(getattr(self._input_model, 'buses', []))

             self.__add_lines(getattr(self._input_model, 'lines', []))
             self.__add_generators(getattr(self._input_model, 'generators', []))
             self.__add_loads(getattr(self._input_model, 'loads', []))
             self.__add_storage_units(getattr(self._input_model, 'storage_units', []))
             self.__add_transformers(getattr(self._input_model, 'transformers', []))
        else:
            print("Warning: No input model set for force_build.")
            return False # Indicate failure

        # Final check for slack bus if none were added initially
        self.__ensure_slack_bus_exists()

        return True # Indicate success


    def __add_initial_ext_grids(self, bus_list: list[Bus]) -> None:
        """Adds external grids based on is_ref flag during initial bus addition."""
        if not isinstance(self._pandapower_model, dict): return
        self.__check_or_create_table('ext_grid')
        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())

        for bus_comp in bus_list:
             if getattr(bus_comp, 'is_ref', False):
                 if not bus_table.empty and bus_comp.name in bus_table.index:
                      try:
                           bus_idx = bus_table.index.get_loc(bus_comp.name)
                           # Check if an ext_grid already exists for this bus_idx
                           if ext_grid_table.empty or not (ext_grid_table['bus'] == bus_idx).any():
                                pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name=f"ExtGrid_{bus_comp.name}")
                                print(f"Info: Added external grid to reference bus '{bus_comp.name}'.")
                           # else:
                           #      print(f"Info: External grid already exists for bus index {bus_idx} ({bus_comp.name}).")
                      except KeyError:
                           print(f"Warning: Could not find index for supposedly existing bus {bus_comp.name} when adding ext_grid.")
                      except Exception as e:
                           print(f"Error adding initial external grid for bus {bus_comp.name}: {e}")
                 # else:
                 #      print(f"Warning: Cannot add initial ext_grid, bus {bus_comp.name} not found in table.")


    def __ensure_slack_bus_exists(self) -> None:
         """Ensures at least one slack bus (ext_grid or gen slack=True) exists."""
         if not isinstance(self._pandapower_model, dict): return

         bus_table = self._pandapower_model.get('bus', pd.DataFrame())
         gen_table = self._pandapower_model.get('gen', pd.DataFrame())
         ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())

         has_ext_grid = not ext_grid_table.empty
         has_slack_gen = not gen_table.empty and 'slack' in gen_table.columns and gen_table['slack'].any()

         if not has_ext_grid and not has_slack_gen:
              if not bus_table.empty:
                   # Add ext_grid to the first bus as a last resort
                   target_bus_name = bus_table.index[0]
                   try:
                        bus_idx = bus_table.index.get_loc(target_bus_name)
                        pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name="Fallback ExtGrid")
                        print(f"Warning: No external grid or slack gen found. Added fallback ext_grid to first bus '{target_bus_name}'.")
                   except KeyError:
                         print(f"Error: Could not find index for fallback slack bus '{target_bus_name}'.")
                   except Exception as e:
                         print(f"Error adding fallback external grid: {e}")
              else:
                   print("Warning: Cannot ensure slack bus exists because no buses are defined.")


    def selective_build(self):
        """
        Selective building (complex in PandaPower). Calls force_build for now.
        """
        print("Info: Selective building requested, performing full rebuild for robustness.")
        self.force_build()


    def set_calculation_method(self, method: str) -> None:
        # Kept for interface compatibility. runpp is used in calculate().
        print(f"Info: PandaPower builder received set_calculation_method('{method}'). Standard runpp will be used by default calculate().")
        pass


    # --- Test Helper Methods ---
    # These methods interact directly with the _pandapower_model and are used by tests.
    # They need to be robust against the model being partially formed, especially during errors.

    def add_bus(self, name, voltage=110, is_ref=False):
        """ Adds a bus for testing. """
        if not isinstance(self._pandapower_model, dict):
             print("Error: Cannot add bus (test), model not initialized.")
             return None
        self.__check_or_create_table('bus') # Ensure table exists first
        bus_table = self._pandapower_model.get('bus') # Get safely
        bus_idx = None
        # Avoid adding if exists
        if not bus_table.empty and name in bus_table.index:
             print(f"Info: Bus '{name}' already exists.")
             bus_idx = bus_table.index.get_loc(name)
        else:
            try:
                bus_idx = pp.create_bus(self._pandapower_model, name=name, vn_kv=voltage)
            except Exception as e:
                print(f"Error adding bus {name} for testing: {e}")
                return None

        if is_ref and bus_idx is not None:
            self.__check_or_create_table('ext_grid')
            ext_grid_table = self._pandapower_model.get('ext_grid')
            # Ensure no ext_grid already exists for this bus
            if ext_grid_table.empty or 'bus' not in ext_grid_table.columns or not (ext_grid_table['bus'] == bus_idx).any():
                try:
                    pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name=f"ExtGrid_{name}")
                except Exception as e:
                    print(f"Error adding ext_grid for test bus {name}: {e}")
            # else:
                # print(f"Info: Ext grid already exists for test bus {name}")
        return bus_idx


    def add_generator(self, bus, p_mw, name=None):
        """ Adds a generator (as sgen) for testing. """
        if not isinstance(self._pandapower_model, dict) or bus is None:
             print("Error: Cannot add generator (test), model or bus index invalid.")
             return None
        self.__check_or_create_table('sgen')
        gen_name = name if name else f"Test_SGen_Bus{bus}"
        gen_idx = None
        try:
            # Check if gen with this name already exists
            sgen_table = self._pandapower_model.get('sgen')
            if sgen_table.empty or gen_name not in sgen_table.index:
                 gen_idx = pp.create_sgen(self._pandapower_model, bus=bus, p_mw=p_mw, name=gen_name)
            else:
                 print(f"Info: Generator '{gen_name}' already exists.")
                 gen_idx = sgen_table.index.get_loc(gen_name)
        except Exception as e:
             print(f"Error adding generator to bus {bus} for testing: {e}")
             return None
        return gen_idx


    def add_load(self, bus, p_mw, name=None):
        """ Adds a load for testing. """
        if not isinstance(self._pandapower_model, dict) or bus is None:
             print("Error: Cannot add load (test), model or bus index invalid.")
             return None
        self.__check_or_create_table('load')
        load_name = name if name else f"Test_Load_Bus{bus}"
        load_idx = None
        try:
             load_table = self._pandapower_model.get('load')
             if load_table.empty or load_name not in load_table.index:
                 load_idx = pp.create_load(self._pandapower_model, bus=bus, p_mw=p_mw, name=load_name)
             else:
                 print(f"Info: Load '{load_name}' already exists.")
                 load_idx = load_table.index.get_loc(load_name)
        except Exception as e:
             print(f"Error adding load to bus {bus} for testing: {e}")
             return None
        return load_idx


    def add_line(self, from_bus, to_bus, length_km=1.0, std_type="NAYY 4x50 SE", name=None):
        """ Adds a line for testing. """
        if not isinstance(self._pandapower_model, dict) or from_bus is None or to_bus is None:
             print("Error: Cannot add line (test), model or bus indices invalid.")
             return None
        self.__check_or_create_table('line')
        line_name = name if name else f"Test_Line_{from_bus}-{to_bus}"
        line_idx = None
        try:
             line_table = self._pandapower_model.get('line')
             if line_table.empty or line_name not in line_table.index:
                 try:
                     line_idx = pp.create_line(self._pandapower_model, from_bus=from_bus, to_bus=to_bus,
                                              length_km=length_km, std_type=std_type, name=line_name)
                 except Exception as e_type: # Catch error if std_type unknown
                     print(f"Warning: std_type '{std_type}' not found for test line {line_name}. Using parameters. Error: {e_type}")
                     line_idx = pp.create_line_from_parameters(self._pandapower_model, from_bus=from_bus,
                                                              to_bus=to_bus, length_km=length_km,
                                                              r_ohm_per_km=0.1, x_ohm_per_km=0.1,
                                                              c_nf_per_km=10, max_i_ka=1.0, name=line_name) # Use float for max_i_ka
             else:
                  print(f"Info: Line '{line_name}' already exists.")
                  line_idx = line_table.index.get_loc(line_name)

        except Exception as e:
             print(f"Error adding line {line_name}: {e}")
             return None
        return line_idx


    def add_transformer(self, hv_bus, lv_bus, std_type="25 MVA 110/20 kV", name=None):
        """ Adds a transformer for testing. """
        if not isinstance(self._pandapower_model, dict) or hv_bus is None or lv_bus is None:
             print("Error: Cannot add transformer (test), model or bus indices invalid.")
             return None
        self.__check_or_create_table('trafo')
        self.__check_or_create_table('bus') # Ensure bus table exists for voltage lookup
        trafo_name = name if name else f"Test_Trafo_{hv_bus}-{lv_bus}"
        trafo_idx = None

        try:
            trafo_table = self._pandapower_model.get('trafo')
            if trafo_table.empty or trafo_name not in trafo_table.index:
                try:
                    trafo_idx = pp.create_transformer(self._pandapower_model, hv_bus=hv_bus, lv_bus=lv_bus, std_type=std_type, name=trafo_name)
                except Exception as e_type: # Catch error if std_type unknown
                    print(f"Warning: std_type '{std_type}' not found for test transformer {trafo_name}. Using parameters. Error: {e_type}")
                    bus_table = self._pandapower_model.get('bus')
                    # Ensure voltages can be looked up
                    if not bus_table.empty and 'vn_kv' in bus_table.columns and hv_bus in bus_table.index and lv_bus in bus_table.index:
                         hv_vn_kv = bus_table.vn_kv[hv_bus]
                         lv_vn_kv = bus_table.vn_kv[lv_bus]
                         trafo_idx = pp.create_transformer_from_parameters(
                             self._pandapower_model,
                             hv_bus=hv_bus,
                             lv_bus=lv_bus,
                             sn_mva=25.0,  # Default rating
                             vn_hv_kv=hv_vn_kv,
                             vn_lv_kv=lv_vn_kv,
                             vkr_percent=0.5, vk_percent=6.0, pfe_kw=5.0, i0_percent=0.1, shift_degree=0.0, name=trafo_name
                         )
                    else:
                         print(f"Error: Could not find bus voltages for test transformer {trafo_name} fallback.")
                         return None
            else:
                print(f"Info: Transformer '{trafo_name}' already exists.")
                trafo_idx = trafo_table.index.get_loc(trafo_name)

        except Exception as e:
             print(f"Error adding transformer {trafo_name}: {e}")
             return None
        return trafo_idx


    def run_power_flow(self):
        """ Runs power flow for testing. """
        return self.calculate() # Use the main calculate method


    def get_results(self):
        """ Gets results for testing. """
        if not isinstance(self._pandapower_model, dict): return None

        res_bus = self._pandapower_model.get('res_bus', pd.DataFrame())
        res_line = self._pandapower_model.get('res_line', pd.DataFrame())
        res_trafo = self._pandapower_model.get('res_trafo', pd.DataFrame())

        # Basic check if results were populated
        # if res_bus.empty:
        #      print("Warning: Bus results are empty in get_results.")
             # return None # Optionally return None

        results = {
            'bus_results': res_bus.copy() if not res_bus.empty else pd.DataFrame(),
            'line_results': res_line.copy() if not res_line.empty else pd.DataFrame(),
            'trafo_results': res_trafo.copy() if not res_trafo.empty else pd.DataFrame(),
        }
        return results


    def print_network_info(self):
        """ Prints network info for testing. """
        if not isinstance(self._pandapower_model, dict):
             print("Network model not initialized.")
             return

        print("\n--- Network Info ---")
        print(f"Buses: {len(self._pandapower_model.get('bus', pd.DataFrame()))}")
        print(f"Lines: {len(self._pandapower_model.get('line', pd.DataFrame()))}")
        print(f"Transformers: {len(self._pandapower_model.get('trafo', pd.DataFrame()))}")
        print(f"SGen: {len(self._pandapower_model.get('sgen', pd.DataFrame()))}")
        print(f"Loads: {len(self._pandapower_model.get('load', pd.DataFrame()))}")
        print(f"Ext Grids: {len(self._pandapower_model.get('ext_grid', pd.DataFrame()))}")
        print(f"Storage: {len(self._pandapower_model.get('storage', pd.DataFrame()))}")

        bus_table = self._pandapower_model.get('bus', pd.DataFrame())
        if not bus_table.empty and 'vn_kv' in bus_table.columns:
            voltage_levels = sorted(bus_table.vn_kv.unique())
            print(f"Voltage levels (kV): {voltage_levels}")

        ext_grid_table = self._pandapower_model.get('ext_grid', pd.DataFrame())
        if not ext_grid_table.empty and 'bus' in ext_grid_table.columns:
             print("External grids (slack) at bus indices:", ext_grid_table.bus.tolist())
        print("--------------------")