# test/test_pandapower_network.py

import pandapower as pp
import pandas as pd
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder
from src.model.Model import Model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.model.components.Transformer import Transformer

# Helper function to handle potential power flow errors
def run_pandapower_flow(net):
    """Runs pandapower power flow and handles convergence errors."""
    try:
        pp.runpp(net)
        print("Power flow succesvol uitgevoerd!")
        return True
    except pp.LoadflowNotConverged:
        print("Power flow did not converge.")
        return False
    except Exception as e:
        print(f"An error occurred during power flow: {e}")
        return False

def test_basic_network():
    """Basistest voor de PandapowerNetworkBuilder."""
    print("\n----- Test 1: Basistest -----")
    # Stap 1: Maak een generiek Model
    model = Model()

    # Stap 2: Voeg componenten toe aan het Model
    bus_comp_1 = Bus(name="Bus 1", v_nom=10.0) # Geef een nominale spanning op
    bus_comp_2 = Bus(name="Bus 2", v_nom=10.0)
    gen_comp_1 = Generator()
    gen_comp_1.name = "Gen 1"
    gen_comp_1.bus0 = "Bus 1"
    gen_comp_1.p_set = [100.0] # p_set is a list in your component
    gen_comp_1.active = True # Zorg dat componenten actief zijn
    line_comp_1 = Line(name="Line 1-2", bus0="Bus 1", bus1="Bus 2", x=0.1, r=0.01, s_nom=1000, type="NAYY 4x50 SE", length=1)
    line_comp_1.active = True # Zorg dat componenten actief zijn
    bus_comp_1.active = True
    bus_comp_2.active = True

    model.add_bus(bus_comp_1)
    model.add_bus(bus_comp_2)
    model.add_generator(gen_comp_1)
    model.add_line(line_comp_1)

    # Stap 3: Maak de builder en bouw het pandapower netwerk
    net_builder = PandapowerNetworkBuilder()
    net_builder.set_input_model(model)
    net_builder.build_model() # Deze methode vult net_builder._pandapower_model

    # Stap 4: Voeg een externe grid toe (nodig voor power flow)
    # Zoek de index van de bus waar de generator aan zit
    bus1_idx = net_builder._pandapower_model.bus.index[net_builder._pandapower_model.bus['name'] == "Bus 1"].tolist()
    if not bus1_idx:
         raise ValueError("Bus 'Bus 1' niet gevonden in pandapower model")
    bus1_idx = bus1_idx[0] # Neem de eerste gevonden index

    # Voeg externe grid toe
    pp.create_ext_grid(net_builder._pandapower_model, bus=bus1_idx, vm_pu=1.0, name="Grid Connection")

    # Verwijder de static generator (sgen), want de ext_grid neemt die rol over
    # ** HIER WAS DE FOUT - NU GECORRIGEERD NAAR 'sgen' **
    sgen1_indices = net_builder._pandapower_model.sgen.index[net_builder._pandapower_model.sgen['name'] == "Gen 1"].tolist()
    if sgen1_indices:
        sgen1_idx_to_drop = sgen1_indices[0] # Neem de eerste gevonden index
        # Drop from the 'sgen' DataFrame using the index found
        net_builder._pandapower_model.sgen.drop(index=sgen1_idx_to_drop, inplace=True)
        print(f"Info: Removed sgen 'Gen 1' at index {sgen1_idx_to_drop}")
    else:
        print("Warning: sgen 'Gen 1' not found to remove.") # Should not happen if added correctly

    # Stap 5: Voer de power flow uit op het interne pandapower model
    print("Netwerk voor power flow:\n", net_builder._pandapower_model)
    success = run_pandapower_flow(net_builder._pandapower_model)

    # Controleer of de power flow is geslaagd
    assert success, "Power flow berekening moet slagen!"

    # Haal resultaten op uit het interne pandapower model
    bus_results = net_builder._pandapower_model.res_bus
    print("Bus resultaten:\n", bus_results)

    # Controleer resultaten
    assert bus_results is not None, "Resultaten moeten bestaan!"
    assert not bus_results.empty, "Bus resultaten mogen niet leeg zijn!"
    assert "vm_pu" in bus_results.columns, "Spanning (vm_pu) moet in bus resultaten zitten!"

    print("✅ Basistest geslaagd!")


def test_complex_network():
    """Test met een vereenvoudigd complex netwerk (met realistischere waarden)."""
    print("\n----- Test 2: Complex netwerk test -----")
    # Stap 1: Maak een generiek Model
    model = Model()

    # Stap 2: Voeg componenten toe aan het Model
    hs_bus_comp = Bus(name="HS Bus", v_nom=110.0); hs_bus_comp.active = True
    ms_bus_comp = Bus(name="MS Bus", v_nom=20.0); ms_bus_comp.active = True
    ls_bus_comp = Bus(name="LS Bus", v_nom=0.4); ls_bus_comp.active = True

    trafo_hs_ms_comp = Transformer()
    trafo_hs_ms_comp.name = "T1 HS-MS"
    trafo_hs_ms_comp.bus0 = "HS Bus" # Hoogspanning bus naam
    trafo_hs_ms_comp.bus1 = "MS Bus" # Laagspanning bus naam
    trafo_hs_ms_comp.capacity = 25 # Stel capaciteit in MVA in
    trafo_hs_ms_comp.active = True
    # Geef een type op dat pandapower kent, of laat __add_transformers fallback gebruiken
    trafo_hs_ms_comp.model = "63 MVA 110/20 kV" # Geef een std_type op

    trafo_ms_ls_comp = Transformer()
    trafo_ms_ls_comp.name = "T2 MS-LS"
    trafo_ms_ls_comp.bus0 = "MS Bus" # Hoogspanning bus naam
    trafo_ms_ls_comp.bus1 = "LS Bus" # Laagspanning bus naam
    trafo_ms_ls_comp.capacity = 0.4 # Stel capaciteit in MVA in
    trafo_ms_ls_comp.active = True
    trafo_ms_ls_comp.model = "0.4 MVA 20/0.4 kV" # Geef een std_type op

    gen_comp = Generator()
    gen_comp.name = "Gen HS"
    gen_comp.bus0 = "HS Bus"
    gen_comp.p_set = [20.0] # p_set is a list
    gen_comp.active = True

    load_ms_comp = Load()
    load_ms_comp.name = "Load MS"
    load_ms_comp.bus0 = "MS Bus"
    load_ms_comp.p_set = [10.0] # p_set is a list
    load_ms_comp.q_set = 2.0 # Voorbeeld reactief vermogen
    load_ms_comp.active = True

    load_ls_comp = Load()
    load_ls_comp.name = "Load LS"
    load_ls_comp.bus0 = "LS Bus"
    load_ls_comp.p_set = [0.3] # p_set is a list
    load_ls_comp.q_set = 0.05 # Voorbeeld reactief vermogen
    load_ls_comp.active = True

    model.add_bus(hs_bus_comp)
    model.add_bus(ms_bus_comp)
    model.add_bus(ls_bus_comp)
    model.add_transformer(trafo_hs_ms_comp)
    model.add_transformer(trafo_ms_ls_comp)
    model.add_generator(gen_comp) # Wordt sgen in pandapower
    model.add_load(load_ms_comp)
    model.add_load(load_ls_comp)

    # Stap 3: Maak de builder en bouw het pandapower netwerk
    net_builder = PandapowerNetworkBuilder()
    net_builder.set_input_model(model)
    net_builder.build_model() # Vult net_builder._pandapower_model

    # Stap 4: Voeg externe grid toe aan HS bus en verwijder generator (sgen)
    hs_bus_indices = net_builder._pandapower_model.bus.index[net_builder._pandapower_model.bus['name'] == "HS Bus"].tolist()
    if not hs_bus_indices:
         raise ValueError("Bus 'HS Bus' niet gevonden in pandapower model")
    hs_bus_idx = hs_bus_indices[0]
    pp.create_ext_grid(net_builder._pandapower_model, bus=hs_bus_idx, vm_pu=1.0, name="Grid Connection")

    sgen_indices = net_builder._pandapower_model.sgen.index[net_builder._pandapower_model.sgen['name'] == "Gen HS"].tolist()
    if sgen_indices:
        sgen_idx_to_drop = sgen_indices[0]
        net_builder._pandapower_model.sgen.drop(index=sgen_idx_to_drop, inplace=True)
        print(f"Info: Removed sgen 'Gen HS' at index {sgen_idx_to_drop}")
    else:
        print("Warning: sgen 'Gen HS' not found to remove.")

    # Print informatie over het pandapower netwerk
    print("Gebouwd Pandapower Netwerk:\n", net_builder._pandapower_model)
    print("Bus tabel:\n", net_builder._pandapower_model.bus)
    print("Trafo tabel:\n", net_builder._pandapower_model.trafo)
    print("Load tabel:\n", net_builder._pandapower_model.load)
    print("Ext Grid tabel:\n", net_builder._pandapower_model.ext_grid)

    # Stap 5: Run power flow
    success = run_pandapower_flow(net_builder._pandapower_model)
    assert success, "Power flow berekening moet slagen!"

    # Haal resultaten op
    bus_results = net_builder._pandapower_model.res_bus
    print("Bus resultaten kolommen:", list(bus_results.columns))
    print("\nComplex netwerk resultaten:")
    print("Bus resultaten:\n", bus_results)

    # Controleer spanning
    assert "vm_pu" in bus_results.columns, "Spanning (vm_pu) moet aanwezig zijn in resultaten!"
    assert not bus_results.empty, "Bus resultaten mogen niet leeg zijn na succesvolle power flow!"
    assert (bus_results["vm_pu"] >= 0.9).all() and (bus_results["vm_pu"] <= 1.1).all(), \
        f"Niet alle busspanningen liggen tussen 0.9 en 1.1 pu:\n{bus_results['vm_pu']}"

    print("✅ Complexe netwerk test geslaagd!")


def test_known_example():
    """Test met een eenvoudig netwerk waarvan de resultaten bekend zijn."""
    print("\n----- Test 3: Bekende waarden test -----")
    # Stap 1: Maak een generiek Model
    model = Model()

    # Stap 2: Voeg componenten toe aan het Model
    slack_bus_comp = Bus(name="Slack", v_nom=110.0); slack_bus_comp.active = True
    load_bus_comp = Bus(name="LoadBus", v_nom=110.0); load_bus_comp.active = True # Andere naam dan Load component

    load_comp = Load()
    load_comp.name = "Load 100MW"
    load_comp.bus0 = "LoadBus" # Koppel aan LoadBus
    load_comp.p_set = [100.0] # 100 MW load
    load_comp.q_set = 10.0 # Voorbeeld 10 MVAr
    load_comp.active = True

    # Gebruik een standaard pandapower type voor voorspelbare resultaten
    line_comp = Line(name="Line Slack-Load", bus0="Slack", bus1="LoadBus", x=5.0, r=0.5, s_nom=500, type="N2XS(FL)2Y 1x185/25 64/110 kV", length=10)
    line_comp.active = True

    model.add_bus(slack_bus_comp)
    model.add_bus(load_bus_comp)
    model.add_load(load_comp)
    model.add_line(line_comp)

    # Stap 3: Maak de builder en bouw het pandapower netwerk
    net_builder = PandapowerNetworkBuilder()
    net_builder.set_input_model(model)
    net_builder.build_model() # Vult net_builder._pandapower_model

    # Stap 4: Voeg externe grid toe aan Slack bus
    slack_bus_indices = net_builder._pandapower_model.bus.index[net_builder._pandapower_model.bus['name'] == "Slack"].tolist()
    if not slack_bus_indices:
         raise ValueError("Bus 'Slack' niet gevonden in pandapower model")
    slack_bus_idx = slack_bus_indices[0]
    pp.create_ext_grid(net_builder._pandapower_model, bus=slack_bus_idx, vm_pu=1.0, name="Grid Connection")

    # Stap 5: Voer power flow uit
    print("Netwerk voor power flow:\n", net_builder._pandapower_model)
    print("Lijn tabel:\n", net_builder._pandapower_model.line)
    success = run_pandapower_flow(net_builder._pandapower_model)
    assert success, "Power flow berekening moet slagen!"

    # Haal resultaten op
    bus_results = net_builder._pandapower_model.res_bus
    line_results = net_builder._pandapower_model.res_line

    print("Lijn resultaten kolommen:", list(line_results.columns))
    print("\nBekend voorbeeld resultaten:")
    print("Bus resultaten:\n", bus_results)
    print("Lijn resultaten:\n", line_results)

    # Controleer lijnvermogen
    assert "p_from_mw" in line_results.columns, "p_from_mw moet aanwezig zijn in lijn resultaten!"
    assert not line_results.empty, "Lijn resultaten mogen niet leeg zijn!"

    # Zoek de lijn op naam in de resultaten (index komt overeen met creatie volgorde)
    lijn_index = net_builder._pandapower_model.line.index[net_builder._pandapower_model.line['name'] == "Line Slack-Load"].tolist()
    if not lijn_index:
         raise ValueError("Lijn 'Line Slack-Load' niet gevonden in pandapower model")
    lijn_index = lijn_index[0] # Neem de eerste index

    lijn_vermogen = abs(line_results.loc[lijn_index, "p_from_mw"])
    print(f"Vermogen door de lijn: {lijn_vermogen:.2f} MW")

    # Verwachting: Vermogen is iets hoger dan 100 MW vanwege lijnverliezen
    verwacht_minimum = 100.0
    verwacht_maximum = 110.0 # Ruime marge voor verliezen
    assert verwacht_minimum <= lijn_vermogen <= verwacht_maximum, \
        f"Lijn moet ~{verwacht_minimum}-{verwacht_maximum} MW transporteren (incl. verliezen), maar transporteert {lijn_vermogen:.2f} MW"

    print("Bekende waarden test geslaagd!")


# Run alle tests wanneer dit script direct wordt uitgevoerd
if __name__ == "__main__":
    print("Uitvoeren van tests voor PandapowerNetworkBuilder:")
    test_basic_network()
    test_complex_network()
    test_known_example()
    print("\nAlle tests geslaagd!")