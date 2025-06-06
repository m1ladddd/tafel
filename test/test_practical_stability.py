#!/usr/bin/env python3
"""
Practical Stability Tests
Tests that simulate realistic usage patterns for the Smart Grid Table.
Focus on 2-hour maximum operation time with accelerated testing.

Test Criteria:
- Simulate 2-hour usage in 2-5 minutes
- Memory leak detection over realistic periods  
- Performance degradation detection
- Resource cleanup verification
"""

import pytest
import time
import threading
import psutil
import os
import sys
import gc
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main_controller import MainApplicationController
from app_state import AppState
from src.model.Model import Model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load

class TestTableOperationStability:
    """Test stability during realistic table operation patterns."""
    
    def create_realistic_table_model(self):
        """Create a model representing typical table configuration."""
        model = Model()
        
        # Typical table setup: 4-6 buses, a few lines, some generation/load
        buses = ["HV_bus", "MV_bus", "LV_bus", "Load_bus"]
        for bus_name in buses:
            bus = Bus(bus_name, 110.0)
            bus.active = True
            model.add_bus(bus)
        
        # Typical connections
        lines = [
            ("HV_MV_line", "HV_bus", "MV_bus"),
            ("MV_LV_line", "MV_bus", "LV_bus"), 
            ("LV_Load_line", "LV_bus", "Load_bus")
        ]
        
        for name, bus0, bus1 in lines:
            line = Line(name, bus0, bus1, x=0.1, r=0.01, s_nom=1000, type="table", length=1.0)
            line.active = True
            model.add_line(line)
        
        # Add typical generation
        gen = Generator()
        gen.name = "table_gen"
        gen.bus0 = "HV_bus"
        gen.p_set = 75.0
        gen.active = True
        model.add_generator(gen)
        
        # Add typical load
        load = Load()
        load.name = "table_load"
        load.bus0 = "Load_bus"
        load.p_set = 70.0
        load.active = True
        model.add_load(load)
        
        return model
    
    @pytest.fixture
    def app_controller(self):
        """Create app controller for testing."""
        controller = MainApplicationController()
        controller.app_state.simulation_mode = True
        return controller
    
    def test_continuous_operation_simulation(self, app_controller):
        """Simulate 2 hours of continuous operation in ~2 minutes."""
        print("\n=== Continuous Operation Simulation (2 hours -> 2 minutes) ===")
        
        model = self.create_realistic_table_model()
        process = psutil.Process()
        
        # Baseline measurements
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate 2 hours = 7200 seconds
        # If we do 1 calculation per 10 seconds -> 720 calculations total
        # But we'll do this in 2 minutes -> 6 calculations per second
        target_calculations = 720
        max_test_duration = 120  # 2 minutes max
        
        calculation_count = 0
        successful_calculations = 0
        memory_samples = []
        performance_samples = []
        
        with patch.object(app_controller.table, 'get_model', return_value=model):
            start_time = time.perf_counter()
            
            while (calculation_count < target_calculations and 
                   time.perf_counter() - start_time < max_test_duration):
                
                calc_start = time.perf_counter()
                
                try:
                    # Simulate typical table operation
                    app_controller.table.force_calculate()
                    calculation_count += 1
                    
                    if app_controller.table.get_simulation_succes():
                        successful_calculations += 1
                    
                    calc_time = time.perf_counter() - calc_start
                    performance_samples.append(calc_time)
                    
                    # Sample memory every 50 calculations
                    if calculation_count % 50 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                        
                        print(f"Simulated ~{calculation_count/720*2:.1f}h operation: "
                              f"Memory: {current_memory:.1f}MB, "
                              f"Success: {successful_calculations/calculation_count*100:.1f}%, "
                              f"Avg calc time: {sum(performance_samples[-50:])/min(50,len(performance_samples))*1000:.1f}ms")
                        
                        gc.collect()
                    
                    # Minimal delay to prevent overwhelming
                    time.sleep(0.001)
                    
                except Exception as e:
                    print(f"Error in simulation cycle {calculation_count}: {e}")
                    break
        
        test_duration = time.perf_counter() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Calculate results
        memory_increase = final_memory - initial_memory
        success_rate = successful_calculations / calculation_count if calculation_count > 0 else 0
        avg_calc_time = sum(performance_samples) / len(performance_samples) if performance_samples else 0
        
        print(f"\n=== Simulation Results ===")
        print(f"Simulated operation time: ~{calculation_count/720*2:.1f} hours")
        print(f"Test duration: {test_duration:.1f} seconds")
        print(f"Calculations performed: {calculation_count}")
        print(f"Success rate: {success_rate*100:.1f}%")
        print(f"Average calculation time: {avg_calc_time*1000:.2f}ms")
        print(f"Memory increase: {memory_increase:.1f}MB")
        
        # Practical acceptance criteria for table operation
        assert calculation_count >= 100, f"Should simulate substantial operation, got {calculation_count}"
        assert success_rate >= 0.7, f"Success rate should be >=70% for table use, got {success_rate*100:.1f}%"
        assert memory_increase < 50, f"Memory increase should be <50MB for 2h operation, got {memory_increase:.1f}MB"
        assert avg_calc_time < 0.5, f"Average calculation should be <500ms, got {avg_calc_time*1000:.1f}ms"
        
        print("PASSED: Continuous operation simulation test")
    
    def test_interactive_session_patterns(self, app_controller):
        """Test patterns typical of interactive table sessions."""
        print("\n=== Interactive Session Patterns Test ===")
        
        model = self.create_realistic_table_model()
        
        # Simulate typical interactive patterns:
        # - Mode changes
        # - Calculation bursts 
        # - Idle periods
        # - Configuration updates
        
        session_actions = [
            ("mode_change", "pf"),
            ("calculation_burst", 10),    # 10 quick calculations
            ("idle_period", 0.1),         # 100ms idle
            ("mode_change", "optimize"),
            ("calculation_burst", 5),
            ("mode_change", "lpf"),
            ("calculation_burst", 8),
            ("configuration_update", None),
            ("calculation_burst", 12),
            ("idle_period", 0.2),
        ]
        
        action_results = []
        
        with patch.object(app_controller.table, 'get_model', return_value=model):
            for action_type, param in session_actions:
                action_start = time.perf_counter()
                
                if action_type == "mode_change":
                    app_controller.app_state.set_mode(param)
                    action_results.append(("mode_change", param, time.perf_counter() - action_start))
                
                elif action_type == "calculation_burst":
                    burst_successes = 0
                    for _ in range(param):
                        app_controller.table.force_calculate()
                        if app_controller.table.get_simulation_succes():
                            burst_successes += 1
                    
                    burst_time = time.perf_counter() - action_start
                    action_results.append(("calculation_burst", f"{burst_successes}/{param}", burst_time))
                
                elif action_type == "idle_period":
                    time.sleep(param)
                    action_results.append(("idle_period", f"{param}s", param))
                
                elif action_type == "configuration_update":
                    # Simulate configuration change
                    app_controller.app_state.request_update()
                    consumed = app_controller.app_state.consume_force_update()
                    action_results.append(("config_update", consumed, time.perf_counter() - action_start))
        
        # Verify interactive session completed successfully
        mode_changes = [r for r in action_results if r[0] == "mode_change"]
        calculation_bursts = [r for r in action_results if r[0] == "calculation_burst"]
        
        assert len(mode_changes) == 3, f"Should have 3 mode changes, got {len(mode_changes)}"
        assert len(calculation_bursts) == 4, f"Should have 4 calculation bursts, got {len(calculation_bursts)}"
        
        print("Interactive session actions:")
        for action_type, result, duration in action_results:
            print(f"  {action_type}: {result} ({duration*1000:.1f}ms)")
        
        print("PASSED: Interactive session patterns test")

class TestMemoryLeakDetection:
    """Practical memory leak detection for table usage."""
    
    def test_component_lifecycle_memory(self):
        """Test memory usage during component creation/destruction cycles."""
        print("\n=== Component Lifecycle Memory Test ===")
        
        process = psutil.Process()
        
        # Test different component types
        component_tests = [
            ("AppState", lambda: AppState()),
            ("Model", lambda: Model()),
            ("Bus", lambda: Bus("test", 110.0)),
            ("Line", lambda: Line("test", "bus1", "bus2", 0.1, 0.01, 1000, "test", 1.0)),
        ]
        
        memory_results = {}
        
        for component_name, create_func in component_tests:
            initial_memory = process.memory_info().rss / 1024 / 1024
            
            # Create and destroy many instances
            instances = []
            for i in range(100):
                instances.append(create_func())
                
                # Periodically clean up to simulate realistic usage
                if i % 20 == 0:
                    instances.clear()
                    gc.collect()
            
            # Final cleanup
            instances.clear()
            gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory
            
            memory_results[component_name] = memory_increase
            
            # Each component type should not leak significantly
            # Allow more memory for AppState due to Python's memory management
            max_memory = 30 if component_name == "AppState" else 10
            assert memory_increase < max_memory, f"{component_name} memory leak: {memory_increase:.1f}MB (max: {max_memory}MB)"
        
        print("Component memory test results:")
        for component, increase in memory_results.items():
            print(f"  {component}: {increase:.1f}MB increase")
        
        print("PASSED: Component lifecycle memory test")
    
    def test_calculation_cycle_memory(self):
        """Test memory usage during repeated calculation cycles."""
        print("\n=== Calculation Cycle Memory Test ===")
        
        app_controller = MainApplicationController()
        app_controller.app_state.simulation_mode = True
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Simple test model
        model = Model()
        bus1 = Bus("bus1", 110.0)
        bus2 = Bus("bus2", 110.0) 
        bus1.active = True
        bus2.active = True
        model.add_bus(bus1)
        model.add_bus(bus2)
        
        line = Line("line1", "bus1", "bus2", 0.1, 0.01, 1000, "test", 1.0)
        line.active = True
        model.add_line(line)
        
        gen = Generator()
        gen.name = "gen1"
        gen.bus0 = "bus1"
        gen.p_set = 50.0
        gen.active = True
        model.add_generator(gen)
        
        load = Load()
        load.name = "load1"
        load.bus0 = "bus2"
        load.p_set = 45.0
        load.active = True
        model.add_load(load)
        
        # Perform many calculation cycles
        with patch.object(app_controller.table, 'get_model', return_value=model):
            for i in range(200):  # Simulate ~30 minutes of use
                app_controller.table.force_calculate()
                
                if i % 50 == 0:
                    gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase after 200 calculation cycles: {memory_increase:.1f}MB")
        
        # Should not accumulate significant memory
        assert memory_increase < 20, f"Calculation cycle memory leak: {memory_increase:.1f}MB"
        
        print("PASSED: Calculation cycle memory test")

class TestPerformanceDegradation:
    """Test for performance degradation over realistic time periods."""
    
    def test_performance_consistency(self):
        """Test that performance remains consistent over table operation period."""
        print("\n=== Performance Consistency Test ===")
        
        app_controller = MainApplicationController()
        app_controller.app_state.simulation_mode = True
        
        # Create test model
        model = Model()
        bus = Bus("test_bus", 110.0)
        bus.active = True
        model.add_bus(bus)
        
        gen = Generator()
        gen.name = "test_gen"
        gen.bus0 = "test_bus"
        gen.p_set = 50.0
        gen.active = True
        model.add_generator(gen)
        
        calculation_times = []
        
        with patch.object(app_controller.table, 'get_model', return_value=model):
            # Measure calculation times over period
            for i in range(100):
                start_time = time.perf_counter()
                app_controller.table.force_calculate()
                calc_time = time.perf_counter() - start_time
                calculation_times.append(calc_time)
                
                time.sleep(0.01)  # Small delay between calculations
        
        # Analyze performance trend
        early_times = calculation_times[:20]  # First 20%
        late_times = calculation_times[-20:]  # Last 20%
        
        early_avg = sum(early_times) / len(early_times)
        late_avg = sum(late_times) / len(late_times)
        
        performance_change = (late_avg - early_avg) / early_avg
        
        print(f"Early average calculation time: {early_avg*1000:.2f}ms")
        print(f"Late average calculation time: {late_avg*1000:.2f}ms")
        print(f"Performance change: {performance_change*100:+.1f}%")
        
        # Performance should not degrade significantly
        assert abs(performance_change) < 0.5, f"Performance degraded by {performance_change*100:.1f}%"
        
        # All calculations should be reasonably fast
        max_time = max(calculation_times)
        assert max_time < 2.0, f"Slowest calculation took {max_time:.3f}s"
        
        print("PASSED: Performance consistency test")

if __name__ == "__main__":
    # Run with: pytest test_practical_stability.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"]) 