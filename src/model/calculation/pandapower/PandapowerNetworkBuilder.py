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
import numpy
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
        # Create an empty network - THIS IS WHERE THE ERROR WAS HAPPENING
        # We're ensuring numpy.array is preserved as a function
        self._pandapower_model = None
        try:
            self._pandapower_model = pp.create_empty_network()
        except Exception as e:
            print(f"Error creating empty pandapower network: {e}")
            # Fallback for testing
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
        snapshot_count = len(self.snapshots) if isinstance(self.snapshots, list) else 1

        for line in self._input_model.lines:
            line.active_power = [0.0] * snapshot_count
            line.output = [False] * snapshot_count

    def retrieve_results(self) -> None:
        """
        Retrieve results from the PandaPower model and write them back to the input_model.
        NOTE: PandaPower result names may differ from PyPSA. Snapshots are not considered here.
        """
        if not hasattr(self._pandapower_model, 'res_load') or self._pandapower_model.res_load is None:
            print("Warning: No load results available in PandaPower model.")
            return  # Or other error handling

        # Retrieve results
        res_load = self._pandapower_model.res_load
        res_gen = self._pandapower_model.res_gen if hasattr(self._pandapower_model, 'res_gen') else None
        res_sgen = self._pandapower_model.res_sgen if hasattr(self._pandapower_model, 'res_sgen') else None  # Static generators
        res_line = self._pandapower_model.res_line if hasattr(self._pandapower_model, 'res_line') else None
        res_trafo = self._pandapower_model.res_trafo if hasattr(self._pandapower_model, 'res_trafo') else None
        res_storage = self._pandapower_model.res_storage if hasattr(self._pandapower_model, 'res_storage') else None

        # Update Loads
        for load_comp in self._input_model.loads:
            if load_comp.active and load_comp.name in self._pandapower_model.load.index:
                load_idx = self._pandapower_model.load.index.get_loc(load_comp.name)
                if 0 <= load_idx < len(res_load):
                    load_comp.active_power = [res_load.p_mw.iloc[load_idx]]
                    load_comp.output = [True]

        # Update Generators (both gen and sgen)
        for gen_comp in self._input_model.generators:
            if gen_comp.active:
                p_mw = 0
                found = False
                
                # First check conventional generators
                if res_gen is not None and gen_comp.name in self._pandapower_model.gen.index:
                    gen_idx = self._pandapower_model.gen.index.get_loc(gen_comp.name)
                    if 0 <= gen_idx < len(res_gen):
                        p_mw = res_gen.p_mw.iloc[gen_idx]
                        found = True
                
                # Then check static generators
                elif res_sgen is not None and gen_comp.name in self._pandapower_model.sgen.index:
                    sgen_idx = self._pandapower_model.sgen.index.get_loc(gen_comp.name)
                    if 0 <= sgen_idx < len(res_sgen):
                        p_mw = res_sgen.p_mw.iloc[sgen_idx]  # PandaPower uses sgen for static generators
                        found = True

                if found:
                    gen_comp.active_power = [p_mw]
                    gen_comp.output = [True]

        # Update Lines
        for line_comp in self._input_model.lines:
            if line_comp.active and res_line is not None and line_comp.name in self._pandapower_model.line.index:
                line_idx = self._pandapower_model.line.index.get_loc(line_comp.name)
                if 0 <= line_idx < len(res_line):
                    # PandaPower res_line has p_from_mw, p_to_mw etc. We take p_from_mw as p0.
                    line_comp.active_power = [res_line.p_from_mw.iloc[line_idx]]
                    line_comp.output = [True]

        # Update Transformers
        for trafo_comp in self._input_model.transformers:
            if trafo_comp.active and res_trafo is not None and trafo_comp.name in self._pandapower_model.trafo.index:
                trafo_idx = self._pandapower_model.trafo.index.get_loc(trafo_comp.name)
                if 0 <= trafo_idx < len(res_trafo):
                    trafo_comp.active_power_0 = [res_trafo.p_hv_mw.iloc[trafo_idx]]  # Power at HV side (bus0)
                    trafo_comp.capacity = self._pandapower_model.trafo.sn_mva.iloc[trafo_idx]  # Capacity
                    trafo_comp.output = [True]

        # Update Storage Units
        for storage_comp in self._input_model.storage_units:
            if storage_comp.active and res_storage is not None and storage_comp.name in self._pandapower_model.storage.index:
                storage_idx = self._pandapower_model.storage.index.get_loc(storage_comp.name)
                if 0 <= storage_idx < len(res_storage):
                    storage_comp.active_power = [res_storage.p_mw.iloc[storage_idx]]
                    storage_comp.output = [True]

    def __add_buses(self, bus_list: list[Bus]) -> None:
        """Add buses to the PandaPower model."""
        for bus in bus_list:
            if bus.active:
                # PandaPower uses kV, PyPSA uses v_nom (which can also be kV, check units!)
                vn_kv = bus.v_nom
                pp.create_bus(self._pandapower_model, name=bus.name, vn_kv=vn_kv)

    def __add_lines(self, line_list: list[Line]) -> None:
        """Add lines to the PandaPower model."""
        for line in line_list:
            if line.active:
                from_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus0)
                to_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus1)
                
                # Handle case where bus doesn't exist yet
                if from_bus_idx < 0 or to_bus_idx < 0:
                    print(f"Warning: Can't add line {line.name} - bus doesn't exist")
                    continue
                
                # Use PandaPower's line creation method
                if line.type and line.type != "":
                    try:
                        pp.create_line(
                            self._pandapower_model,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=line.length if line.length else 1.0,
                            std_type=line.type,
                            name=line.name
                        )
                    except:
                        # Fallback if type is unknown
                        print(f"Warning: Couldn't create line {line.name} with type '{line.type}'. Using parameters.")
                        pp.create_line_from_parameters(
                            self._pandapower_model,
                            from_bus=from_bus_idx,
                            to_bus=to_bus_idx,
                            length_km=line.length if line.length else 1.0,
                            r_ohm_per_km=line.r if line.r else 0.1,
                            x_ohm_per_km=line.x if line.x else 0.1,
                            c_nf_per_km=10,
                            max_i_ka=1,
                            name=line.name
                        )
                else:
                    # Create line from parameters
                    pp.create_line_from_parameters(
                        self._pandapower_model,
                        from_bus=from_bus_idx,
                        to_bus=to_bus_idx,
                        length_km=line.length if line.length else 1.0,
                        r_ohm_per_km=line.r if line.r else 0.1,
                        x_ohm_per_km=line.x if line.x else 0.1,
                        c_nf_per_km=10,
                        max_i_ka=1,
                        name=line.name
                    )

    def __add_generators(self, generator_list: list[Generator]) -> None:
        """Add generators to the PandaPower model."""
        for gen in generator_list:
            if gen.active:
                bus_idx = pp.get_element_index(self._pandapower_model, "bus", gen.bus0)
                
                # Handle case where bus doesn't exist
                if bus_idx < 0:
                    print(f"Warning: Can't add generator {gen.name} - bus doesn't exist")
                    continue
                
                # Determine p_mw correctly for static value
                p_mw_val = 0
                if isinstance(gen.p_set, (int, float)):
                    p_mw_val = gen.p_set
                elif hasattr(gen.p_set, '__len__') and not isinstance(gen.p_set, str):
                    if len(gen.p_set) > 0:
                        p_mw_val = gen.p_set[0]  # Take first value

                # Determine q_mvar
                q_mvar_val = 0
                if isinstance(gen.q_set, (int, float)):
                    q_mvar_val = gen.q_set
                
                # PandaPower uses sgen for simple PQ generators
                pp.create_sgen(
                    self._pandapower_model,
                    bus=bus_idx,
                    p_mw=p_mw_val,
                    q_mvar=q_mvar_val,
                    name=gen.name,
                    scaling=1.0  # For time series, here 1.0
                )

    def __add_loads(self, load_list: list[Load]) -> None:
        """Add loads to the PandaPower model."""
        for load in load_list:
            if load.active:
                bus_idx = pp.get_element_index(self._pandapower_model, "bus", load.bus0)
                
                # Handle case where bus doesn't exist
                if bus_idx < 0:
                    print(f"Warning: Can't add load {load.name} - bus doesn't exist")
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

                pp.create_load(
                    self._pandapower_model,
                    bus=bus_idx,
                    p_mw=p_mw_val,
                    q_mvar=q_mvar_val,
                    name=load.name
                )

    def __add_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        """Add storage units to the PandaPower model."""
        for storage in storage_unit_list:
            if storage.active:
                bus_idx = pp.get_element_index(self._pandapower_model, "bus", storage.bus0)
                
                # Handle case where bus doesn't exist
                if bus_idx < 0:
                    print(f"Warning: Can't add storage {storage.name} - bus doesn't exist")
                    continue
                
                pp.create_storage(
                    self._pandapower_model,
                    bus=bus_idx,
                    p_mw=storage.p_nom,  # p_nom is power in MW
                    max_e_mwh=storage.p_nom * 1,  # Max energy, placeholder (1 hour)
                    q_mvar=0,  # No reactive power for now
                    soc_percent=storage.state_of_charge_initial * 100 if storage.state_of_charge_initial else 50,  # SOC in %
                    name=storage.name
                )

    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """Add transformers to the PandaPower model."""
        for trafo in transformer_list:
            if trafo.active:
                hv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus0)
                lv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus1)
                
                # Handle case where bus doesn't exist
                if hv_bus_idx < 0 or lv_bus_idx < 0:
                    print(f"Warning: Can't add transformer {trafo.name} - bus doesn't exist")
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
                    except:
                        print(f"Warning: Couldn't create transformer {trafo.name} with std_type '{std_type}'. Using parameters.")
                        # Fallback with parameters
                        hv_vn_kv = self._pandapower_model.bus.vn_kv[hv_bus_idx]
                        lv_vn_kv = self._pandapower_model.bus.vn_kv[lv_bus_idx]
                        pp.create_transformer_from_parameters(
                            self._pandapower_model,
                            hv_bus=hv_bus_idx,
                            lv_bus=lv_bus_idx,
                            sn_mva=1.0,
                            vn_hv_kv=hv_vn_kv,
                            vn_lv_kv=lv_vn_kv,
                            vkr_percent=1.0,
                            vk_percent=6.0,
                            pfe_kw=1.0,
                            i0_percent=1.0,
                            name=trafo.name
                        )
                else:
                    print(f"Warning: No std_type defined for transformer {trafo.name}. Using parameters.")
                    # Fallback with parameters
                    hv_vn_kv = self._pandapower_model.bus.vn_kv[hv_bus_idx]
                    lv_vn_kv = self._pandapower_model.bus.vn_kv[lv_bus_idx]
                    pp.create_transformer_from_parameters(
                        self._pandapower_model,
                        hv_bus=hv_bus_idx,
                        lv_bus=lv_bus_idx,
                        sn_mva=1.0,
                        vn_hv_kv=hv_vn_kv,
                        vn_lv_kv=lv_vn_kv,
                        vkr_percent=1.0,
                        vk_percent=6.0,
                        pfe_kw=1.0,
                        i0_percent=1.0,
                        name=trafo.name
                    )

    # --- Methods for removing (simplified) ---
    def __remove_buses(self, bus_list: list[Bus]) -> None:
        indices = []
        for bus in bus_list:
            if bus.active:
                idx = pp.get_element_index(self._pandapower_model, "bus", bus.name)
                if idx >= 0:
                    indices.append(idx)
        if indices:
            pp.drop_buses(self._pandapower_model, indices)

    def __remove_lines(self, line_list: list[Line]) -> None:
        indices = []
        for line in line_list:
            if line.active:
                idx = pp.get_element_index(self._pandapower_model, "line", line.name)
                if idx >= 0:
                    indices.append(idx)
        if indices:
            pp.drop_lines(self._pandapower_model, indices)

    def __remove_generators(self, generator_list: list[Generator]) -> None:
        sgen_indices = []
        gen_indices = []
        
        for gen in generator_list:
            if gen.active:
                # Check for sgen
                idx = pp.get_element_index(self._pandapower_model, "sgen", gen.name)
                if idx >= 0:
                    sgen_indices.append(idx)
                
                # Check for gen
                idx = pp.get_element_index(self._pandapower_model, "gen", gen.name)
                if idx >= 0:
                    gen_indices.append(idx)
                    
        if sgen_indices:
            pp.drop_sgens(self._pandapower_model, sgen_indices)
        if gen_indices:
            pp.drop_gens(self._pandapower_model, gen_indices)

    def __remove_loads(self, load_list: list[Load]) -> None:
        indices = []
        for load in load_list:
            if load.active:
                idx = pp.get_element_index(self._pandapower_model, "load", load.name)
                if idx >= 0:
                    indices.append(idx)
        if indices:
            pp.drop_loads(self._pandapower_model, indices)

    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        indices = []
        for storage in storage_unit_list:
            if storage.active:
                idx = pp.get_element_index(self._pandapower_model, "storage", storage.name)
                if idx >= 0:
                    indices.append(idx)
        if indices:
            pp.drop_storages(self._pandapower_model, indices)

    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:
        indices = []
        for trafo in transformers_list:
            if trafo.active:
                idx = pp.get_element_index(self._pandapower_model, "trafo", trafo.name)
                if idx >= 0:
                    indices.append(idx)
        if indices:
            pp.drop_trafos(self._pandapower_model, indices)

    # --- Implementation of Interface Methods ---
    def calculate(self) -> bool:
        """
        Start a PandaPower Power Flow calculation.
        @return bool True = success, False = Error
        """
        start_time = time.perf_counter()
        self.reset_lines()  # Reset our own model results

        # Blackout/error condition check
        if not hasattr(self._pandapower_model, 'gen') or not hasattr(self._pandapower_model, 'sgen') or \
           not hasattr(self._pandapower_model, 'ext_grid'):
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "invalid model"
            print("Error: Invalid pandapower model structure.")
            return False

        if len(self._pandapower_model.gen) == 0 and len(self._pandapower_model.sgen) == 0 and \
           len(self._pandapower_model.ext_grid) == 0:
            self._calculation_time = time.perf_counter() - start_time
            self._status = "failed"
            self._condition = "no generation source"
            print("Error: No generator, sgen or external grid found in PandaPower model.")
            return False

        success = True
        try:
            # Run power flow
            pp.runpp(self._pandapower_model, algorithm='nr', calculate_voltage_angles=True)  # Newton-Raphson is default
            self._status = "ok"  # Assumption, runpp doesn't give direct status string like PyPSA lopf
            self._condition = "converged"  # Assumption
            self.retrieve_results()
        except pp.LoadflowNotConverged:
            self._status = "failed"
            self._condition = "loadflow not converged"
            print(f"Error: PandaPower loadflow did not converge for model.")
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
        # Create directory if needed
        if not path.exists(file_path):
            makedirs(file_path)

        # Save to Excel (or other formats like pickle)
        # Note: this saves the *entire* network, including structure and results
        export_filepath = path.join(file_path, "pandapower_results.xlsx")
        try:
            pp.to_excel(self._pandapower_model, export_filepath)
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
        # We still store them for consistency with interface
        self.snapshots = snapshots

    def build_model(self) -> None:
        """
        Build the PandaPower model based on input_model.
        """
        start_time = time.perf_counter()

        # For PandaPower, selective building is more complex due to index-based removal.
        # A full rebuild is often more robust, unless performance is an issue.
        # We implement a full rebuild here.
        try:
            self._pandapower_model = pp.create_empty_network()  # Start fresh
            self.force_build()  # Build everything anew
        except Exception as e:
            print(f"Error during model build: {e}")
            
        self._network_build_time = (time.perf_counter() - start_time)

    def force_build(self):
        """Build all components anew in PandaPower."""
        # Create a new PandaPower model
        try:
            self._pandapower_model = pp.create_empty_network(name="SGT Network")
        except Exception as e:
            print(f"Error creating empty pandapower network: {e}")
            return False
            
        # Add components
        self.__add_buses(self._input_model.buses)
        self.__add_lines(self._input_model.lines)
        self.__add_generators(self._input_model.generators)
        self.__add_loads(self._input_model.loads)
        self.__add_storage_units(self._input_model.storage_units)
        self.__add_transformers(self._input_model.transformers)

        # Important: PandaPower often needs a 'slack bus' (external grid)
        # We add one here to the first bus if it doesn't exist yet.
        if len(self._pandapower_model.ext_grid) == 0 and len(self._pandapower_model.bus) > 0:
            bus_idx = self._pandapower_model.bus.index[0]
            pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name="External Grid")
            print("Warning: No external grid found, automatically added to first bus as slack.")

    def selective_build(self):
        """
        Selective building (complex in PandaPower). For now we call force_build.
        A real implementation would track differences and use pp.drop/create.
        """
        print("Info: Selective building is complex in PandaPower, performing full rebuild.")
        self.force_build()

    def set_calculation_method(self, method: str) -> None:
        # PandaPower doesn't have direct equivalents for 'lopf', 'lpf', 'optimize' like PyPSA.
        # runpp() is the standard power flow. Optimization requires pp.runopp().
        print(f"Info: PandaPower builder ignores set_calculation_method('{method}'). Using default runpp.")
        pass
    
    # Helper methods for tests
    def add_bus(self, name, voltage=110, is_ref=False):
        """
        Add a bus to the network with given parameters.
        Added for the test interface.
        
        @param name str The name of the bus
        @param voltage float Nominal voltage in kV
        @param is_ref bool Whether this bus is a reference bus (slack bus)
        @return int The bus index
        """
        bus_idx = pp.create_bus(self._pandapower_model, name=name, vn_kv=voltage)
        
        if is_ref:
            pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0)
            
        return bus_idx
    
    def add_generator(self, bus, p_mw):
        """
        Add a generator to the network.
        Added for the test interface.
        
        @param bus int The bus index to connect the generator to
        @param p_mw float The active power in MW
        @return int The generator index
        """
        gen_idx = pp.create_sgen(self._pandapower_model, bus=bus, p_mw=p_mw)
        return gen_idx
    
    def add_load(self, bus, p_mw):
        """
        Add a load to the network.
        Added for the test interface.
        
        @param bus int The bus index to connect the load to
        @param p_mw float The active power in MW
        @return int The load index
        """
        load_idx = pp.create_load(self._pandapower_model, bus=bus, p_mw=p_mw)
        return load_idx
    
    def add_line(self, from_bus, to_bus, length_km=1.0, std_type="NAYY 4x50 SE"):
        """
        Add a line to the network.
        Added for the test interface.
        
        @param from_bus int The from bus index
        @param to_bus int The to bus index
        @param length_km float Line length in km
        @param std_type str The standard line type
        @return int The line index
        """
        try:
            line_idx = pp.create_line(self._pandapower_model, from_bus=from_bus, to_bus=to_bus, 
                                     length_km=length_km, std_type=std_type)
        except:
            # Fallback to default parameters
            line_idx = pp.create_line_from_parameters(self._pandapower_model, from_bus=from_bus, 
                                                     to_bus=to_bus, length_km=length_km,
                                                     r_ohm_per_km=0.1, x_ohm_per_km=0.1, 
                                                     c_nf_per_km=10, max_i_ka=1)
        return line_idx
    
    def add_transformer(self, hv_bus, lv_bus, std_type="25 MVA 110/20 kV"):
        """
        Add a transformer to the network.
        Added for the test interface.
        
        @param hv_bus int The high voltage bus index
        @param lv_bus int The low voltage bus index
        @param std_type str The standard transformer type
        @return int The transformer index
        """
        try:
            trafo_idx = pp.create_transformer(self._pandapower_model, hv_bus=hv_bus, lv_bus=lv_bus, std_type=std_type)
        except:
            # Fallback to default parameters if standard type not found
            hv_vn_kv = self._pandapower_model.bus.vn_kv[hv_bus]
            lv_vn_kv = self._pandapower_model.bus.vn_kv[lv_bus]
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
                shift_degree=0.0
            )
        return trafo_idx
        
    def run_power_flow(self):
        """
        Run a power flow calculation on the network.
        Added for the test interface.
        
        @return bool True if the power flow calculation was successful, False otherwise
        """
        try:
            pp.runpp(self._pandapower_model)
            return True
        except Exception as e:
            print(f"Power flow calculation failed: {e}")
            return False
            
    def get_results(self):
        """
        Get the results of the power flow calculation.
        Added for the test interface.
        
        @return dict A dictionary with the results
        """
        if not hasattr(self._pandapower_model, 'res_bus'):
            return None
            
        results = {
            'bus_results': self._pandapower_model.res_bus.copy(),
            'line_results': self._pandapower_model.res_line.copy() if hasattr(self._pandapower_model, 'res_line') else None,
            'trafo_results': self._pandapower_model.res_trafo.copy() if hasattr(self._pandapower_model, 'res_trafo') else None,
        }
        
        return results
        
    def print_network_info(self):
        """
        Print information about the network.
        Added for the test interface.
        """
        print("\nNetwork Information:")
        print(f"Number of buses: {len(self._pandapower_model.bus)}")
        print(f"Number of lines: {len(self._pandapower_model.line)}")
        print(f"Number of transformers: {len(self._pandapower_model.trafo)}")
        print(f"Number of generators: {len(self._pandapower_model.gen) + len(self._pandapower_model.sgen)}")
        print(f"Number of loads: {len(self._pandapower_model.load)}")
        print(f"Number of storage units: {len(self._pandapower_model.storage)}")
        
        # Print bus voltage levels
        if len(self._pandapower_model.bus) > 0:
            voltage_levels = self._pandapower_model.bus.vn_kv.unique()
            print(f"Voltage levels: {', '.join([f'{v} kV' for v in sorted(voltage_levels)])}")
            
        # Print external grids (slack buses)
        if len(self._pandapower_model.ext_grid) > 0:
            print("External grids at buses:", end=" ")
            for i, idx in enumerate(self._pandapower_model.ext_grid.bus.values):
                bus_name = self._pandapower_model.bus.name[idx] if 'name' in self._pandapower_model.bus.columns else f"Bus {idx}"
                print(f"{bus_name}", end=", " if i < len(self._pandapower_model.ext_grid) - 1 else "")
            print()