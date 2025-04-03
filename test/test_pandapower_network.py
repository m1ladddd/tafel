from src.model.calculation.pandapower.PandapowerNetworkBuilder import PandapowerNetworkBuilder

def test_pandapower_network():
    """Basistest voor de PandapowerNetworkBuilder."""
    # Stap 1: Maak een netwerk aan
    net_builder = PandapowerNetworkBuilder()

    # Stap 2: Voeg bussen toe
    bus1 = net_builder.add_bus("Bus 1", is_ref=True)
    bus2 = net_builder.add_bus("Bus 2")

    # Stap 3: Voeg een generator toe
    net_builder.add_generator(bus1, 100)

    # Stap 4: Voeg een lijn toe
    net_builder.add_line(bus1, bus2)

    # Stap 5: Voer de power flow uit
    success = net_builder.run_power_flow()
    
    # Controleer of de power flow is geslaagd
    assert success, "Power flow berekening moet slagen!"
    
    # Haal resultaten op
    results = net_builder.get_results()

    # Controleer resultaten
    assert results is not None, "Resultaten moeten bestaan!"
    assert "vm_pu" in results["bus_results"].columns, "Spanning (vm_pu) moet in bus resultaten zitten!"
    
    print("✅ Basistest geslaagd: Power flow resultaten correct!")


def test_complex_network():
    """Test met een vereenvoudigd complex netwerk (met realistischere waarden)."""
    # Maak een complexer netwerk met meerdere spanningsniveaus
    net_builder = PandapowerNetworkBuilder()
    
    # Hoogspanning (HS)
    hs_bus = net_builder.add_bus("HS Bus", voltage=110, is_ref=True)
    
    # Middenspanning (MS)
    ms_bus = net_builder.add_bus("MS Bus", voltage=20)
    
    # Laagspanning (LS)
    ls_bus = net_builder.add_bus("LS Bus", voltage=0.4)
    
    # Transformatoren - met realistische waarden
    net_builder.add_transformer(hs_bus, ms_bus, std_type="25 MVA 110/20 kV")
    net_builder.add_transformer(ms_bus, ls_bus, std_type="0.4 MVA 20/0.4 kV")
    
    # Generatoren en belastingen - met realistische waarden
    net_builder.add_generator(hs_bus, 20)  # 20 MW
    net_builder.add_load(ms_bus, 10)       # 10 MW
    net_builder.add_load(ls_bus, 0.3)      # 300 kW
    
    # Print informatie over het netwerk
    net_builder.print_network_info()
    
    # Run power flow
    success = net_builder.run_power_flow()
    assert success, "Power flow berekening moet slagen!"
    
    # Haal resultaten op
    results = net_builder.get_results()
    
    # Controleer of resultaten bestaan
    assert results is not None, "Resultaten moeten bestaan!"
    
    # Print de kolommen in de resultaten
    print("Bus resultaten kolommen:", list(results["bus_results"].columns))
    
    # Bekijk de resultaten
    print("\nComplex netwerk resultaten:")
    print("Bus resultaten:\n", results["bus_results"])
    
    # Controleer spanning
    assert "vm_pu" in results["bus_results"].columns, "Spanning (vm_pu) moet aanwezig zijn in resultaten!"
    
    # Controleer of de spanning binnen normale grenzen ligt
    assert (results["bus_results"]["vm_pu"] >= 0.9).all() and (results["bus_results"]["vm_pu"] <= 1.1).all(), \
        "Alle busspanningen moeten tussen 0.9 en 1.1 pu liggen"
    
    print("✅ Complexe netwerk test geslaagd: Alle spanningen binnen normale grenzen!")


def test_known_example():
    """Test met een eenvoudig netwerk waarvan de resultaten bekend zijn."""
    # Eenvoudig netwerk met bekende resultaten
    net_builder = PandapowerNetworkBuilder()
    
    # Voeg bussen toe
    slack_bus = net_builder.add_bus("Slack", voltage=110, is_ref=True)
    load_bus = net_builder.add_bus("Load", voltage=110)
    
    # Voeg een belasting van exact 100 MW toe
    net_builder.add_load(load_bus, 100)
    
    # Voeg een lijn toe met bekende parameters
    net_builder.add_line(slack_bus, load_bus, length_km=10, std_type="NAYY 4x50 SE")
    
    # Voer power flow uit
    success = net_builder.run_power_flow()
    assert success, "Power flow berekening moet slagen!"
    
    # Haal resultaten op
    results = net_builder.get_results()
    
    # Print de kolommen in de resultaten
    print("Lijn resultaten kolommen:", list(results["line_results"].columns))
    
    # Print gedetailleerde resultaten
    print("\nBekend voorbeeld resultaten:")
    print("Bus resultaten:\n", results["bus_results"])
    print("Lijn resultaten:\n", results["line_results"])
    
    # In dit geval moet de slack bus ~100 MW leveren en de lijn moet ~100 MW transporteren
    # Gebruik de juiste kolomnamen uit pandapower
    assert "p_from_mw" in results["line_results"].columns, "p_from_mw moet aanwezig zijn in lijn resultaten!"
    
    lijn_vermogen = abs(results["line_results"]["p_from_mw"][0])
    print(f"Vermogen door de lijn: {lijn_vermogen:.2f} MW")
    
    assert lijn_vermogen > 90.0, f"Lijn moet ~100 MW transporteren, maar transporteert {lijn_vermogen:.2f} MW"
    
    print("✅ Bekende waarden test geslaagd: Lijn transporteert ongeveer 100 MW!")


# Run alle tests wanneer dit script direct wordt uitgevoerd
if __name__ == "__main__":
    print("🧪 Uitvoeren van tests voor PandapowerNetworkBuilder:")
    print("\n----- Test 1: Basistest -----")
    test_pandapower_network()
    
    print("\n----- Test 2: Complex netwerk test -----")
    test_complex_network()
    
    print("\n----- Test 3: Bekende waarden test -----")
    test_known_example()
    
    print("\n✅ Alle tests geslaagd!")