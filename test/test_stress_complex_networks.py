# test/test_stress_complex_networks.py

import pytest
import time
import os
from unittest.mock import patch

# Probeer psutil te importeren voor geheugenmeting, maar maak het optioneel
try:
    import psutil
except ImportError:
    psutil = None

# Imports van jouw project
from main_controller import MainApplicationController
from src.model.Model import Model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load
from src.Scenario import Scenario # Nodig voor het mocken van het scenario
import pandas as pd # Nodig voor snapshots

def laad_of_genereer_complex_netwerk(aantal_nodes: int):
    """
    Hulpfunctie om een complex netwerk te genereren voor stresstests.
    Dit model moet componenten bevatten die relevant zijn voor Pandapower berekeningen.
    """
    print(f"Genereren van complex netwerk met {aantal_nodes} nodes.")
    model = Model()
    # De naam van het model zelf is niet direct cruciaal voor de berekening,
    # maar kan handig zijn voor debugging.
    # model.name = f"complex_network_{aantal_nodes}_nodes"

    if aantal_nodes <= 0:
        return model

    # Voeg bussen toe
    for i in range(aantal_nodes):
        model.add_bus(Bus(name=f"bus_stress_{i}", v_nom=10.0))

    # Voeg lijnen toe (bijv. een ring of meshed structuur voor complexiteit)
    for i in range(aantal_nodes):
        bus_from_name = f"bus_stress_{i}"
        bus_to_name = f"bus_stress_{(i + 1) % aantal_nodes}" # Ring structuur
        # Gebruik realistische placeholder waarden voor lijnparameters
        model.add_line(Line(name=f"line_stress_{i}", bus0=bus_from_name, bus1=bus_to_name,
                            x=0.05, r=0.005, s_nom=500, type="NAYY 4x150 SE", length=0.5))

    # Voeg een externe grid/slack generator toe (essentieel voor Pandapower)
    # Dit is de hoofdbron van het netwerk.
    slack_generator = Generator()
    slack_generator.name = "slack_gen_stress"
    slack_generator.bus0 = model.buses[0].name # Koppel aan de eerste bus
    slack_generator.p_set = 0 # p_set voor slack wordt vaak overschreven of is niet relevant
    # Belangrijk: In Pandapower wordt een ext_grid gebruikt voor slack.
    # Je PandapowerNetworkBuilder moet een Generator (of een specifieke component)
    # kunnen vertalen naar een ext_grid, of de calculator voegt het toe.
    # Voor nu voegen we het als een gewone generator toe, en vertrouwen op de
    # emergency slack bus logic in PandapowerCalculatorPF als die niet goed wordt opgepakt.
    # Beter is om in je Model een 'is_slack' flag te hebben of een ExtGrid component type.
    # Om het explicieter te maken voor Pandapower, zou je een generator met zeer hoge p_nom kunnen toevoegen.
    slack_generator.p_nom = 10000 # MW, een grote waarde
    model.add_generator(slack_generator)


    # Voeg enkele loads en andere generatoren verspreid over het netwerk toe
    for i in range(1, aantal_nodes, max(1, aantal_nodes // 10)): # Ongeveer 10 loads/gens
        load = Load()
        load.name = f"load_stress_{i}"
        load.bus0 = model.buses[i].name
        load.p_set = float(i % 5 + 1) * 0.5 # MW, variërende kleine loads
        model.add_load(load)

        if i % 2 == 0 and i != 0: # Niet op de slack bus
            gen = Generator()
            gen.name = f"gen_stress_{i}"
            gen.bus0 = model.buses[i].name
            gen.p_set = float(i % 3 + 1) * 1.0 # MW
            gen.p_nom = gen.p_set * 1.2
            model.add_generator(gen)

    print(f"Netwerk met {len(model.buses)} bussen, {len(model.lines)} lijnen, "
          f"{len(model.generators)} generatoren, {len(model.loads)} loads gegenereerd.")
    return model

@pytest.mark.parametrize("aantal_nodes", [100, 150]) # Begin met kleinere aantallen, verhoog later
def test_stabiliteit_simulatie_complex_netwerk(aantal_nodes: int, capsys):
    """
    Test de stabiliteit van de simulatie met een complex netwerk.
    De primaire check is of de simulatie succesvol runt zonder te crashen.
    """
    print(f"\nStart test_stabiliteit_simulatie_complex_netwerk voor {aantal_nodes} nodes.")

    app_controller = MainApplicationController()
    app_controller.app_state.simulation_mode = True # Essentieel voor standalone tests

    test_model = laad_of_genereer_complex_netwerk(aantal_nodes)

    # Maak een mock Scenario object om de test_model te injecteren
    mock_scenario = Scenario()
    mock_scenario.name = f"test_scenario_complex_{aantal_nodes}"
    mock_scenario.static = True
    mock_scenario.index = ["now"] # Voor een static power flow is dit voldoende
    # De catalogus hoeft niet gevuld te worden als we get_model patchen

    process = psutil.Process(os.getpid()) if psutil else None
    mem_voor = process.memory_info().rss / (1024 * 1024) if process else -1
    start_tijd = time.perf_counter()
    simulatie_succesvol = False

    try:
        # Patch SmartGridTable's methode om ons testmodel te gebruiken
        # en zorg ervoor dat het huidige scenario onze mock is voor snapshot informatie.
        with patch.object(app_controller.table, 'get_model', return_value=test_model), \
             patch.object(app_controller.table, '_SmartGridTable__current_scenario', mock_scenario):

            print(f"Starten van berekening voor {aantal_nodes} nodes...")
            app_controller.table.force_calculate()
            simulatie_succesvol = app_controller.table.get_simulation_succes()

    except Exception as e:
        simulatie_succesvol = False
        pytest.fail(f"Simulatie crashte met {aantal_nodes} nodes: {e}", pytrace=True)
    finally:
        duur = time.perf_counter() - start_tijd
        mem_na = process.memory_info().rss / (1024 * 1024) if process else -1
        mem_gebruikt = mem_na - mem_voor if process else -1

        # Gebruik capsys.disabled() om ervoor te zorgen dat print output altijd getoond wordt
        with capsys.disabled():
            print(f"Berekening voor {aantal_nodes} nodes voltooid in {duur:.2f} seconden.")
            if psutil:
                print(f"  Geheugengebruik (RSS): Start={mem_voor:.2f}MB, Eind={mem_na:.2f}MB, Delta={mem_gebruikt:.2f}MB")
            print(f"  Simulatie succesvol: {simulatie_succesvol}")

    assert simulatie_succesvol, f"Simulatie voor {aantal_nodes} nodes is niet succesvol voltooid."