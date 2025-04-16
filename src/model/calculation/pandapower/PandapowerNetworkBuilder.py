##
# @file PandapowerNetworkBuilder.py
#
# @brief Klasse verantwoordelijk voor het bouwen en onderhouden van PandaPower netwerkmodellen.
# LET OP: Dit is een gereconstrueerde versie gebaseerd op PyPSANetworkBuilder en de traceback.
#         Mogelijk wijkt het af van het originele bestand.
#
# @section libraries_PandapowerNetworkBuilder Libraries/Modules
# - pandapower
# - pandas
# - time
# - numpy
##

# Interne imports
from src.model.calculation.CalculatorThreadInterface import CalculatorThreadInterface
from src.model.Model import Model, get_added_model_components, get_removed_model_components
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.Transformer import Transformer
from src.model.components.StorageUnit import StorageUnit

# Externe imports
import pandapower as pp
import pandas as pd
import numpy as np
import time
from os import path, makedirs
from copy import deepcopy

class PandapowerNetworkBuilder (CalculatorThreadInterface):
    """!
    Klasse verantwoordelijk voor het bouwen en onderhouden van PandaPower netwerkmodellen.
    """

    def __init__(self):
        """!
        Constructor.
        """
        self._pandapower_model: pp.pandapowerNet = pp.create_empty_network()
        self._input_model: Model = None
        self._previous_model: Model = None # Houdt het vorige model bij voor selectieve updates
        self._status: str = ""
        self._condition: str = ""
        self._calculation_time: float = 0.0
        self._network_build_time: float = 0.0
        self.snapshots: list = [0] # Standaard voor statische run

    def set_input_model(self, input_model: Model) -> None:
        """!
        Stel het input model in.
        @param input_model Model
        """
        self._input_model = input_model

    def set_snapshots(self, snapshots: list) -> None:
        """!
        Stel de simulatie snapshot lijst in.
        @param snapshots list
        """
        # PandaPower behandelt tijdreeksen anders, mogelijk zijn snapshots hier minder direct relevant
        # We slaan ze wel op voor consistentie met de interface
        self.snapshots = snapshots
        # Hier zou eventueel logica kunnen komen om time series data voor te bereiden voor PandaPower controllers

    def _reset_results(self) -> None:
        """
        Reset de resultaatvelden in het input_model.
        """
        snapshot_count: int = len(self.snapshots) if isinstance(self.snapshots, list) else 1

        for component_list in [
            self._input_model.lines,
            self._input_model.generators,
            self._input_model.loads,
            self._input_model.transformers,
            self._input_model.storage_units
        ]:
            for component in component_list:
                if hasattr(component, 'active_power'):
                    component.active_power = [0.0] * snapshot_count
                if hasattr(component, 'reactive_power'): # PandaPower geeft ook Q
                    component.reactive_power = [0.0] * snapshot_count
                if hasattr(component, 'output'):
                     component.output = [False] * snapshot_count
                if hasattr(component, 'active_power_0'): # Voor transformers
                    component.active_power_0 = [0.0] * snapshot_count
                # Reset andere specifieke output velden indien nodig

    def _retrieve_results(self) -> None:
        """
        Haal resultaten op uit het PandaPower model en schrijf ze terug naar het input_model.
        LET OP: PandaPower resultaatnamen kunnen afwijken van PyPSA.
               Dit is een vereenvoudigde weergave. Snapshots worden hier niet meegenomen.
        """
        if not hasattr(self._pandapower_model, 'res_load') or self._pandapower_model.res_load is None:
             print("Waarschuwing: Geen load resultaten beschikbaar in PandaPower model.")
             return # Of andere foutafhandeling

        # Haal resultaten op (vereenvoudigd, neemt geen snapshots mee)
        res_load = self._pandapower_model.res_load
        res_gen = self._pandapower_model.res_gen if hasattr(self._pandapower_model, 'res_gen') else None
        res_sgen = self._pandapower_model.res_sgen if hasattr(self._pandapower_model, 'res_sgen') else None # Statische generatoren
        res_line = self._pandapower_model.res_line if hasattr(self._pandapower_model, 'res_line') else None
        res_trafo = self._pandapower_model.res_trafo if hasattr(self._pandapower_model, 'res_trafo') else None
        res_storage = self._pandapower_model.res_storage if hasattr(self._pandapower_model, 'res_storage') else None

        # Update Loads
        for load_comp in self._input_model.loads:
             if load_comp.active and load_comp.name in res_load.index:
                 load_comp.active_power = [res_load.p_mw[load_comp.name]]
                 # load_comp.reactive_power = [res_load.q_mvar[load_comp.name]] # Indien nodig
                 load_comp.output = [True]

        # Update Generators (combinatie van gen en sgen)
        for gen_comp in self._input_model.generators:
             if gen_comp.active:
                 p_mw = 0
                 found = False
                 if res_gen is not None and gen_comp.name in res_gen.index:
                     p_mw = res_gen.p_mw[gen_comp.name]
                     found = True
                 elif res_sgen is not None and gen_comp.name in res_sgen.index:
                     p_mw = res_sgen.p_mw[gen_comp.name] # PandaPower gebruikt sgen voor statische generatoren
                     found = True

                 if found:
                     gen_comp.active_power = [p_mw]
                     # gen_comp.reactive_power = [...] # Indien nodig
                     gen_comp.output = [True]

        # Update Lines
        for line_comp in self._input_model.lines:
            if line_comp.active and res_line is not None and line_comp.name in res_line.index:
                 # PandaPower res_line heeft p_from_mw, p_to_mw etc. We nemen p_from_mw als p0.
                 line_comp.active_power = [res_line.p_from_mw[line_comp.name]]
                 # line_comp.reactive_power = [res_line.q_from_mvar[line_comp.name]] # Indien nodig
                 line_comp.output = [True]

        # Update Transformers
        for trafo_comp in self._input_model.transformers:
             if trafo_comp.active and res_trafo is not None and trafo_comp.name in res_trafo.index:
                 trafo_comp.active_power_0 = [res_trafo.p_hv_mw[trafo_comp.name]] # Vermogen aan HV kant (bus0)
                 # trafo_comp.reactive_power_0 = [res_trafo.q_hv_mvar[trafo_comp.name]] # Indien nodig
                 # trafo_comp.capacity = self._pandapower_model.trafo.sn_mva[trafo_comp.name] # Capaciteit
                 trafo_comp.output = [True]

        # Update Storage Units
        for storage_comp in self._input_model.storage_units:
             if storage_comp.active and res_storage is not None and storage_comp.name in res_storage.index:
                 storage_comp.active_power = [res_storage.p_mw[storage_comp.name]]
                 # storage_comp.reactive_power = [res_storage.q_mvar[storage_comp.name]] # Indien nodig
                 storage_comp.output = [True]


    def __add_buses(self, bus_list: list[Bus]) -> None:
        """Voeg bussen toe aan het PandaPower model."""
        for bus in bus_list:
            if bus.active:
                # PandaPower gebruikt kV, PyPSA gebruikt v_nom (wat ook kV kan zijn, check eenheden!)
                vn_kv = bus.v_nom
                pp.create_bus(self._pandapower_model, name=bus.name, vn_kv=vn_kv)

    def __add_lines(self, line_list: list[Line]) -> None:
        """Voeg lijnen toe aan het PandaPower model."""
        for line in line_list:
             if line.active:
                 from_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus0)
                 to_bus_idx = pp.get_element_index(self._pandapower_model, "bus", line.bus1)
                 # PandaPower heeft lijnparameters per km nodig (r_ohm_per_km, x_ohm_per_km, c_nf_per_km, max_i_ka)
                 # PyPSA gebruikt r, x (pu?), s_nom (MVA?). Conversie is nodig!
                 # Dit vereist kennis van de base MVA en base kV van het PyPSA model, of standaard lijntypes.
                 # Voor nu gebruiken we een placeholder - DIT MOET WORDEN AANGEPAST!
                 if line.type: # Als een PyPSA type is gegeven, probeer PandaPower std_type
                     try:
                         pp.create_line_from_parameters(net=self._pandapower_model,
                                        from_bus=from_bus_idx,
                                        to_bus=to_bus_idx,
                                        length_km=line.length if line.length else 1.0, # Gebruik lengte uit PyPSA
                                        r_ohm_per_km=line.r if line.r else 0.01,  # Placeholder - R is pu in PyPSA?
                                        x_ohm_per_km=line.x if line.x else 0.1,   # Placeholder - X is pu in PyPSA?
                                        c_nf_per_km=10,  # Placeholder
                                        max_i_ka= (line.s_nom / (self._pandapower_model.bus.vn_kv[from_bus_idx] * np.sqrt(3))) if line.s_nom else 1, # Geschatte max stroom uit s_nom
                                        name=line.name,
                                        type=line.type) # Geef type door, hopelijk herkent PandaPower het
                     except:
                          # Fallback als type onbekend is of parameters ontbreken
                          print(f"Waarschuwing: Kon lijn {line.name} niet direct aanmaken met type '{line.type}'. Gebruik placeholders.")
                          pp.create_line_from_parameters(net=self._pandapower_model, from_bus=from_bus_idx, to_bus=to_bus_idx, length_km=1.0, r_ohm_per_km=0.1, x_ohm_per_km=0.1, c_nf_per_km=10, max_i_ka=1, name=line.name)


    def __add_generators(self, generator_list: list[Generator]) -> None:
        """Voeg generatoren toe (als sgen voor statisch)."""
        for gen in generator_list:
             if gen.active:
                 bus_idx = pp.get_element_index(self._pandapower_model, "bus", gen.bus0)
                 # Bepaal p_mw correct voor statische waarde
                 p_mw_val = 0
                 if isinstance(gen.p_set, (int, float)):
                      p_mw_val = gen.p_set
                 elif hasattr(gen.p_set, '__len__') and not isinstance(gen.p_set, str):
                     if len(gen.p_set) > 0:
                         p_mw_val = gen.p_set[0] # Neem eerste waarde

                 # PandaPower gebruikt sgen voor simpele PQ generatoren
                 pp.create_sgen(self._pandapower_model,
                                bus=bus_idx,
                                p_mw=p_mw_val, # Gebruik p_set voor sgen? Of p_nom? Hangt af van type.
                                q_mvar=gen.q_set if isinstance(gen.q_set, (int, float)) else 0, # Statische Q
                                name=gen.name,
                                scaling=1.0) # Voor tijdreeksen, hier 1.0

    def __add_loads(self, load_list: list[Load]) -> None:
        """Voeg loads toe, met correctie voor p_set en q_set."""
        for load in load_list:
            if load.active:
                bus_index = pp.get_element_index(self._pandapower_model, "bus", load.bus0)

                # --- CORRECTIE HIER ---
                p_mw_val = 0
                # Check of het een lijst-achtig type is (en geen string)
                if hasattr(load.p_set, '__len__') and not isinstance(load.p_set, str):
                    if len(load.p_set) > 0:
                        p_mw_val = load.p_set[0] # Neem de eerste waarde voor nu
                # Check of het een getal is
                elif isinstance(load.p_set, (int, float)):
                    p_mw_val = load.p_set # Gebruik het getal direct

                q_mvar_val = 0
                 # Check of het een lijst-achtig type is (en geen string)
                if hasattr(load.q_set, '__len__') and not isinstance(load.q_set, str):
                    if len(load.q_set) > 0:
                         q_mvar_val = load.q_set[0] # Neem de eerste waarde
                # Check of het een getal is
                elif isinstance(load.q_set, (int, float)):
                    q_mvar_val = load.q_set # Gebruik het getal direct
                # --- EINDE CORRECTIE ---

                pp.create_load(self._pandapower_model,
                               bus=bus_index,
                               p_mw=p_mw_val,
                               q_mvar=q_mvar_val,
                               name=load.name)

    def __add_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        """Voeg storage units toe."""
        for storage in storage_unit_list:
            if storage.active:
                bus_idx = pp.get_element_index(self._pandapower_model, "bus", storage.bus0)
                pp.create_storage(self._pandapower_model,
                                 bus=bus_idx,
                                 p_mw=storage.p_nom, # p_nom is vermogen in MW
                                 max_e_mwh=storage.p_nom * 1, # Max energie, placeholder (1 uur)
                                 q_mvar=0, # Voor nu geen reactief vermogen
                                 soc_percent=storage.state_of_charge_initial * 100 if storage.state_of_charge_initial else 50, # SOC in %
                                 name=storage.name)

    def __add_transformers(self, transformer_list: list[Transformer]) -> None:
        """Voeg transformatoren toe."""
        for trafo in transformer_list:
            if trafo.active:
                 hv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus0)
                 lv_bus_idx = pp.get_element_index(self._pandapower_model, "bus", trafo.bus1)
                 # Probeer standaard type te gebruiken
                 std_type = trafo.model if trafo.model else None # Gebruik type uit component
                 if std_type:
                      try:
                          pp.create_transformer(self._pandapower_model,
                                             hv_bus=hv_bus_idx,
                                             lv_bus=lv_bus_idx,
                                             std_type=std_type,
                                             name=trafo.name)
                      except:
                           print(f"Waarschuwing: Kon transformator {trafo.name} niet aanmaken met std_type '{std_type}'. Gebruik parameters (placeholders).")
                           # Fallback met parameters (placeholders - MOET AANGEPAST)
                           hv_vn_kv = self._pandapower_model.bus.vn_kv[hv_bus_idx]
                           lv_vn_kv = self._pandapower_model.bus.vn_kv[lv_bus_idx]
                           pp.create_transformer_from_parameters(net=self._pandapower_model, hv_bus=hv_bus_idx, lv_bus=lv_bus_idx, sn_mva=1.0, vn_hv_kv=hv_vn_kv, vn_lv_kv=lv_vn_kv, vkr_percent=1.0, vk_percent=6.0, pfe_kw=1.0, i0_percent=1.0, name=trafo.name)
                 else:
                      print(f"Waarschuwing: Geen std_type gedefinieerd voor transformator {trafo.name}. Gebruik parameters (placeholders).")
                      # Fallback met parameters (placeholders - MOET AANGEPAST)
                      hv_vn_kv = self._pandapower_model.bus.vn_kv[hv_bus_idx]
                      lv_vn_kv = self._pandapower_model.bus.vn_kv[lv_bus_idx]
                      pp.create_transformer_from_parameters(net=self._pandapower_model, hv_bus=hv_bus_idx, lv_bus=lv_bus_idx, sn_mva=1.0, vn_hv_kv=hv_vn_kv, vn_lv_kv=lv_vn_kv, vkr_percent=1.0, vk_percent=6.0, pfe_kw=1.0, i0_percent=1.0, name=trafo.name)


    # --- Methoden voor verwijderen (vereenvoudigd, PandaPower vereist indices) ---
    # PandaPower maakt verwijderen lastiger omdat het met indices werkt die kunnen verschuiven.
    # Een volledige herbouw is vaak eenvoudiger tenzij performance kritisch is.
    # Voor nu laten we deze leeg of simplistisch.

    def __remove_buses(self, bus_list: list[Bus]) -> None:
        indices = [pp.get_element_index(self._pandapower_model, "bus", bus.name) for bus in bus_list if bus.active]
        if indices: pp.drop_buses(self._pandapower_model, indices)

    def __remove_lines(self, line_list: list[Line]) -> None:
        indices = [pp.get_element_index(self._pandapower_model, "line", line.name) for line in line_list if line.active]
        if indices: pp.drop_lines(self._pandapower_model, indices)

    def __remove_generators(self, generator_list: list[Generator]) -> None:
        sgen_indices = [pp.get_element_index(self._pandapower_model, "sgen", gen.name) for gen in generator_list if gen.active and gen.name in self._pandapower_model.sgen.name.values]
        if sgen_indices: pp.drop_sgens(self._pandapower_model, sgen_indices)
        # Voeg drop_gen toe indien nodig

    def __remove_loads(self, load_list: list[Load]) -> None:
        indices = [pp.get_element_index(self._pandapower_model, "load", load.name) for load in load_list if load.active]
        if indices: pp.drop_loads(self._pandapower_model, indices)

    def __remove_storage_units(self, storage_unit_list: list[StorageUnit]) -> None:
        indices = [pp.get_element_index(self._pandapower_model, "storage", storage.name) for storage in storage_unit_list if storage.active]
        if indices: pp.drop_storages(self._pandapower_model, indices)

    def __remove_transformers(self, transformers_list: list[Transformer]) -> None:
         indices = [pp.get_element_index(self._pandapower_model, "trafo", trafo.name) for trafo in transformers_list if trafo.active]
         if indices: pp.drop_trafos(self._pandapower_model, indices)

    # --- Implementatie van Interface Methoden ---

    def calculate(self) -> bool:
        """
        Start een PandaPower Power Flow berekening.
        @return bool True = succes, False = Error
        """
        start_time: float = time.perf_counter()
        self._reset_results() # Reset onze eigen model resultaten

        # Blackout/fout conditie check
        if len(self._pandapower_model.gen) == 0 and len(self._pandapower_model.sgen) == 0 and len(self._pandapower_model.ext_grid) == 0:
             self._calculation_time = time.perf_counter() - start_time
             self._status = "failed"
             self._condition = "no generation source"
             print("Fout: Geen generator, sgen of external grid gevonden in PandaPower model.")
             return False

        succes: bool = True
        try:
            # Voer power flow uit
            pp.runpp(self._pandapower_model, algorithm='nr', calculate_voltage_angles=True) # Newton-Raphson is standaard
            self._status = "ok" # Aanname, runpp geeft geen directe status string zoals PyPSA lopf
            self._condition = "converged" # Aanname
            self._retrieve_results()
        except pp.LoadflowNotConverged:
            self._status = "failed"
            self._condition = "loadflow not converged"
            print(f"Fout: PandaPower loadflow convergeerde niet voor model.")
            succes = False
        except Exception as e:
            self._status = "failed"
            self._condition = f"exception: {e}"
            print(f"Fout tijdens PandaPower berekening: {e}")
            succes = False

        self._calculation_time = time.perf_counter() - start_time
        return succes

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
        Exporteer het PandaPower model resultaat.
        @param file_path str Directory om resultaten op te slaan
        """
        # Maak directory indien nodig
        if not path.exists(file_path):
             makedirs(file_path)

        # Sla op naar Excel (of andere formaten zoals pickle)
        # Let op: dit slaat het *hele* netwerk op, inclusief structuur en resultaten
        export_filepath = path.join(file_path, "pandapower_results.xlsx")
        try:
            pp.to_excel(self._pandapower_model, export_filepath)
        except Exception as e:
            print(f"Fout bij exporteren van PandaPower resultaten naar {export_filepath}: {e}")


    def build_model(self) -> None:
        """
        Bouw het PandaPower model op basis van het input_model.
        """
        start_time: float = time.perf_counter()

        # Voor PandaPower is selectief bouwen complexer door index-gebaseerd verwijderen.
        # Een volledige herbouw is vaak robuuster, tenzij performance een probleem is.
        # We implementeren hier een volledige herbouw.
        self._pandapower_model = pp.create_empty_network() # Begin opnieuw
        self.force_build() # Bouw alles opnieuw op

        self._network_build_time = (time.perf_counter() - start_time)

    def force_build(self):
         """Bouw alle componenten opnieuw op in PandaPower."""
         # Reset huidig PandaPower model
         self._pandapower_model = pp.create_empty_network(name="SGT Network")

         # Voeg componenten toe
         self.__add_buses(self._input_model.buses)
         self.__add_lines(self._input_model.lines)
         self.__add_generators(self._input_model.generators)
         self.__add_loads(self._input_model.loads)
         self.__add_storage_units(self._input_model.storage_units)
         self.__add_transformers(self._input_model.transformers)

         # Belangrijk: PandaPower heeft vaak een 'slack bus' nodig (external grid)
         # We voegen er hier een toe aan de eerste bus als die nog niet bestaat.
         # Dit moet mogelijk intelligenter, bv. gebaseerd op een specifiek 'external grid' component in het SGT model.
         if len(self._pandapower_model.ext_grid) == 0 and len(self._pandapower_model.bus) > 0:
             bus_idx = self._pandapower_model.bus.index[0]
             pp.create_ext_grid(self._pandapower_model, bus=bus_idx, vm_pu=1.0, name="External Grid")
             print("Waarschuwing: Geen external grid gevonden, automatisch toegevoegd aan eerste bus als slack.")


    def selective_build(self):
        """
        Selectief bouwen (complex in PandaPower). Voor nu roepen we force_build aan.
        Een echte implementatie zou de verschillen moeten bijhouden en pp.drop/create gebruiken.
        """
        print("Info: Selectief bouwen is complex in PandaPower, volledige herbouw wordt uitgevoerd.")
        self.force_build()

    # Dummy implementatie voor consistentie met interface (niet gebruikt in deze PandaPower setup)
    def set_calculation_method(self, method: str) -> None:
        # PandaPower heeft geen directe equivalenten voor 'lopf', 'lpf', 'optimize' zoals PyPSA.
        # runpp() is de standaard power flow. Optimalisatie vereist pp.runopp().
        # We negeren de methode hier, of passen 'calculate' aan op basis van 'method'.
        print(f"Info: PandaPower builder negeert set_calculation_method('{method}'). Gebruikt standaard runpp.")
        pass