def build_model(self):
    """ Laad het model in Pandapower. """
    start_time = time.perf_counter()

    if self._input_model:
        # Create a mapping from bus names to indices
        bus_indices = {}
        for bus in self._input_model.buses:
            if bus.active:
                # Create the bus in pandapower
                vn_kv = bus.v_nom
                idx = pp.create_bus(self._pandapower_model, vn_kv=vn_kv, name=bus.name)
                bus_indices[bus.name] = idx
                
                # Check if this is a reference bus (slack bus)
                # In a real implementation, you would need specific criteria for this
                if bus.name.lower().startswith("slack") or bus.name.lower().startswith("ref"):
                    pp.create_ext_grid(self._pandapower_model, bus=idx, vm_pu=1.0)
        
        for line in self._input_model.lines:
            if line.active and line.bus0 in bus_indices and line.bus1 in bus_indices:
                # Create the line with appropriate parameters
                # AANGEPAST: Toegevoegd 'std_type' parameter
                pp.create_line(
                    self._pandapower_model,
                    from_bus=bus_indices[line.bus0],
                    to_bus=bus_indices[line.bus1],
                    length_km=line.length if hasattr(line, 'length') else 1.0,
                    r_ohm_per_km=line.r,
                    x_ohm_per_km=line.x,
                    c_nf_per_km=0,
                    max_i_ka=line.s_nom/220 if line.s_nom else 1,  # Estimate current from apparent power
                    name=line.name,
                    std_type="NAYY 4x50 SE"  # Standaardwaarde voor std_type
                )
        
        for generator in self._input_model.generators:
            if generator.active and generator.bus0 in bus_indices:
                pp.create_gen(
                    self._pandapower_model,
                    bus=bus_indices[generator.bus0],
                    p_mw=generator.p_set[0] if hasattr(generator, 'p_set') and generator.p_set and len(generator.p_set) > 0 else generator.p_nom,
                    vm_pu=1.0,  # Default voltage setpoint
                    name=generator.name
                )
        
        for load in self._input_model.loads:
            if load.active and load.bus0 in bus_indices:
                p_mw_value = 0
                if hasattr(load, 'p_set'):
                    if isinstance(load.p_set, list) and len(load.p_set) > 0:
                        p_mw_value = load.p_set[0]
                    elif not isinstance(load.p_set, list):
                        p_mw_value = load.p_set
                
                pp.create_load(
                    self._pandapower_model,
                    bus=bus_indices[load.bus0],
                    p_mw=p_mw_value,
                    q_mvar=load.q_set if hasattr(load, 'q_set') else 0,
                    name=load.name
                )
        
        for transformer in self._input_model.transformers:
            if transformer.active and transformer.bus0 in bus_indices and transformer.bus1 in bus_indices:
                # Get the voltage levels of the connected buses
                hv_bus = bus_indices[transformer.bus0]
                lv_bus = bus_indices[transformer.bus1]
                
                # Ensure proper HV/LV order based on bus voltage
                vn_hv = self._pandapower_model.bus.vn_kv[hv_bus]
                vn_lv = self._pandapower_model.bus.vn_kv[lv_bus]
                
                if vn_hv < vn_lv:
                    # Swap if HV is actually lower than LV
                    hv_bus, lv_bus = lv_bus, hv_bus
                
                # Try to create a standard transformer, or use a custom one if standard fails
                try:
                    pp.create_transformer(
                        self._pandapower_model,
                        hv_bus=hv_bus,
                        lv_bus=lv_bus,
                        std_type="160 MVA 380/110 kV" if vn_hv >= 220 else "63 MVA 110/20 kV" if vn_hv >= 60 else "0.4 MVA 20/0.4 kV",
                        name=transformer.name
                    )
                except Exception as e:
                    print(f"Fout bij maken transformator: {e}, probeer alternatieve methode")
                    # Create custom transformer with estimated values
                    pp.create_transformer_from_parameters(
                        self._pandapower_model,
                        hv_bus=hv_bus,
                        lv_bus=lv_bus,
                        sn_mva=transformer.capacity if hasattr(transformer, 'capacity') and transformer.capacity else 100,
                        vn_hv_kv=vn_hv,
                        vn_lv_kv=vn_lv,
                        vkr_percent=0.5,  # Typical value
                        vk_percent=10,    # Typical value
                        pfe_kw=20,        # Typical value
                        i0_percent=0.1,   # Typical value
                        name=transformer.name
                    )
        
        # Add storage units if supported by this version of pandapower
        for storage in self._input_model.storage_units:
            if storage.active and storage.bus0 in bus_indices and hasattr(pp, 'create_storage'):
                pp.create_storage(
                    self._pandapower_model,
                    bus=bus_indices[storage.bus0],
                    p_mw=storage.p_nom,
                    max_e_mwh=storage.p_nom * 4,  # Assume 4 hours of storage
                    soc_percent=storage.state_of_charge_initial * 100 if hasattr(storage, 'state_of_charge_initial') else 50,
                    name=storage.name
                )

    self._network_build_time = (time.perf_counter() - start_time)