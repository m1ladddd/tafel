#!/usr/bin/env python3
"""
Vereenvoudigd testscript voor de Pandapower implementatie.
Focust alleen op de componenten die werkelijk beschikbaar zijn.
"""

import os
import sys
import time

# Voeg de hoofdmap toe aan het pad voor imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Model en component imports
from src.model.Model import Model
from src.model.components.Bus import Bus

# Pandapower calculator imports
from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder
import pandapower as pp

def explore_model_components():
    """Verken de beschikbare model componenten en hun interfaces."""
    print("\n=== Verkenning van Model Componenten ===")
    
    # Test Bus klasse
    print("\nBus klasse:")
    bus = Bus("test_bus", 110.0)
    print(f"Bus aangemaakt: {bus}")
    print(f"Bus attributen: {dir(bus)}")
    
    # Verken de Model klasse
    print("\nModel klasse:")
    model = Model()
    print(f"Model aangemaakt: {model}")
    print(f"Model attributen: {[attr for attr in dir(model) if not attr.startswith('_')]}")
    
    return model

def test_pandapower_builder():
    """Test de basis functionaliteit van PandapowerNetworkBuilder."""
    print("\n=== Test PandapowerNetworkBuilder ===")
    
    # Maak een leeg model
    model = Model()
    
    # Voeg handmatig een bus toe
    bus = Bus("testbus", 110.0)
    model.buses.append(bus)
    
    print(f"Model gemaakt met 1 bus: {model.buses[0]}")
    
    # Maak de PandapowerNetworkBuilder aan
    builder = PandapowerNetworkBuilder()
    print(f"Builder aangemaakt: {builder}")
    
    # Set input model
    builder.set_input_model(model)
    
    # Set snapshots
    builder.set_snapshots([0])
    
    try:
        # Bouw het model
        print("Model bouwen...")
        builder.build_model()
        print("Model gebouwd!")
        
        # Bekijk het resulterende pandapower model
        pp_model = builder._pandapower_model
        print(f"Pandapower model heeft {len(pp_model.bus)} bussen")
        print(f"Bus details: {pp_model.bus}")
        
    except Exception as e:
        print(f"Fout tijdens het bouwen van het model: {e}")
    
    return builder

def test_direct_pandapower():
    """Test direct pandapower functionaliteit zonder de model laag."""
    print("\n=== Test Direct Pandapower ===")
    
    try:
        # Maak een leeg pandapower netwerk
        net = pp.create_empty_network()
        
        # Voeg handmatig elementen toe
        bus1 = pp.create_bus(net, vn_kv=110, name="bus1")
        bus2 = pp.create_bus(net, vn_kv=110, name="bus2")
        
        # Voeg een lijn toe
        pp.create_line(net, from_bus=bus1, to_bus=bus2, length_km=1.0, 
                       std_type="N2XS(FL)2Y 1x185 RM/35 64/110 kV")
        
        # Voeg een externe grid (slack bus) toe
        pp.create_ext_grid(net, bus=bus1, vm_pu=1.0)
        
        # Voeg een load toe
        pp.create_load(net, bus=bus2, p_mw=100)
        
        # Voer een power flow berekening uit
        print("Power flow uitvoeren...")
        pp.runpp(net)
        print("Power flow succesvol uitgevoerd!")
        
        # Bekijk resultaten
        print(f"Bus resultaten: {net.res_bus}")
        print(f"Line resultaten: {net.res_line}")
        
        return True
    except Exception as e:
        print(f"Fout tijdens directe pandapower test: {e}")
        return False

if __name__ == "__main__":
    # Verken model componenten
    model = explore_model_components()
    
    # Test PandapowerNetworkBuilder
    builder = test_pandapower_builder()
    
    # Test direct pandapower
    success = test_direct_pandapower()
    
    if success:
        print("\n=== Alle tests voltooid! ===")
    else:
        print("\n=== Er zijn fouten opgetreden tijdens de tests! ===")