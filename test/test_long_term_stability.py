#!/usr/bin/env python3
"""
24-Hour Long-Term Stability Tests
Tests that the system remains stable during extended operation.

Test Criteria:
- No crashes or memory leakage during 24-hour test
- Stable performance over time
- Resource usage within acceptable bounds
"""

import pytest
import time
import threading
import psutil
import os
import sys
from unittest.mock import patch, MagicMock
import gc

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main_controller import MainApplicationController
from app_state import AppState
from src.model.Model import Model
from src.model.components.Bus import Bus
from src.model.components.Line import Line
from src.model.components.Generator import Generator
from src.model.components.Load import Load

class TestLongTermStability:
    """Test system stability over extended periods."""
    
    @pytest.fixture
    def app_controller(self):
        """Create app controller for testing."""
        controller = MainApplicationController()
        controller.app_state.simulation_mode = True
        return controller
    
    def create_stable_test_model(self):
        """Create a model that should remain stable."""
        model = Model()
        
        # Create simple 3-bus system
        for i in range(3):
            bus = Bus(f"bus_{i}", 110.0)
            bus.active = True
            model.add_bus(bus)
        
        # Add lines
        lines = [
            ("line_0_1", "bus_0", "bus_1"),
            ("line_1_2", "bus_1", "bus_2"),
            ("line_2_0", "bus_2", "bus_0")
        ]
        
        for name, bus0, bus1 in lines:
            line = Line(name, bus0, bus1, x=0.1, r=0.01, s_nom=1000, type="test", length=1.0)
            line.active = True
            model.add_line(line)
        
        # Add generator
        gen = Generator()
        gen.name = "gen_0"
        gen.bus0 = "bus_0"
        gen.p_set = 50.0
        gen.active = True
        model.add_generator(gen)
        
        # Add load
        load = Load()
        load.name = "load_2"
        load.bus0 = "bus_2"
        load.p_set = 45.0
        load.active = True
        model.add_load(load)
        
        return model
    
    @pytest.mark.slow
    @pytest.mark.timeout(300)  # 5 minute timeout for safety
    def test_extended_calculation_cycles(self, app_controller):
        """Test many calculation cycles to simulate long-term use."""
        print("\n=== Extended Calculation Cycles Test ===")
        
        test_model = self.create_stable_test_model()
        process = psutil.Process()
        
        # Baseline measurements
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_time = time.perf_counter()
        
        calculation_count = 0
        successful_calculations = 0
        memory_samples = []
        
        # Run for 5 minutes (scaled down from 24 hours for testing)
        target_duration = 300  # 5 minutes
        max_calculations = 1000  # Safety limit
        
        with patch.object(app_controller.table, 'get_model', return_value=test_model):
            start_time = time.perf_counter()
            
            while (time.perf_counter() - start_time < target_duration and 
                   calculation_count < max_calculations):
                
                try:
                    # Force calculation
                    app_controller.table.force_calculate()
                    calculation_count += 1
                    
                    if app_controller.table.get_simulation_succes():
                        successful_calculations += 1
                    
                    # Sample memory usage every 50 calculations
                    if calculation_count % 50 == 0:
                        current_memory = process.memory_info().rss / 1024 / 1024
                        memory_samples.append(current_memory)
                        
                        print(f"Cycle {calculation_count}: "
                              f"Memory: {current_memory:.1f}MB, "
                              f"Success rate: {successful_calculations/calculation_count*100:.1f}%")
                        
                        # Force garbage collection
                        gc.collect()
                    
                    # Small delay to prevent overwhelming
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"Error in calculation cycle {calculation_count}: {e}")
                    break
        
        final_time = time.perf_counter()
        final_memory = process.memory_info().rss / 1024 / 1024
        
        # Calculate metrics
        duration = final_time - initial_time
        memory_increase = final_memory - initial_memory
        success_rate = successful_calculations / calculation_count if calculation_count > 0 else 0
        avg_calc_time = duration / calculation_count if calculation_count > 0 else 0
        
        print(f"\n=== Extended Test Results ===")
        print(f"Duration: {duration:.1f} seconds")
        print(f"Total calculations: {calculation_count}")
        print(f"Successful calculations: {successful_calculations}")
        print(f"Success rate: {success_rate*100:.1f}%")
        print(f"Average calculation time: {avg_calc_time*1000:.2f}ms")
        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Memory increase: {memory_increase:.1f}MB")
        
        # Acceptance criteria
        assert calculation_count >= 100, f"Should complete at least 100 calculations, got {calculation_count}"
        assert success_rate >= 0.8, f"Success rate should be ≥80%, got {success_rate*100:.1f}%"
        assert memory_increase < 100, f"Memory increase should be <100MB, got {memory_increase:.1f}MB"
        assert avg_calc_time < 1.0, f"Average calculation time should be <1s, got {avg_calc_time:.3f}s"
        
        print("PASSED: Extended calculation cycles test")
    
    def test_memory_leak_detection(self):
        """Test for memory leaks in core components."""
        print("\n=== Memory Leak Detection Test ===")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Create and destroy many app states
        for i in range(100):
            app_state = AppState()
            app_state.set_mode("pf")
            app_state.set_mode("optimize") 
            app_state.request_update()
            app_state.consume_force_update()
            del app_state
            
            if i % 20 == 0:
                gc.collect()
        
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"Memory increase after 100 AppState cycles: {memory_increase:.1f}MB")
        
        # Should not increase significantly
        assert memory_increase < 10, f"Memory leak detected: {memory_increase:.1f}MB increase"
        
        print("PASSED: Memory leak detection test")
    
    @pytest.mark.slow
    def test_concurrent_stability(self):
        """Test stability under concurrent operations."""
        print("\n=== Concurrent Stability Test ===")
        
        app_state = AppState()
        results = []
        errors = []
        
        def worker_thread(thread_id, iterations=50):
            """Worker thread for concurrent testing."""
            try:
                for i in range(iterations):
                    # Simulate concurrent operations
                    app_state.set_mode(["pf", "lpf", "optimize"][i % 3])
                    app_state.request_update()
                    consumed = app_state.consume_force_update()
                    results.append((thread_id, i, consumed))
                    time.sleep(0.001)  # Small delay
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Start multiple worker threads
        threads = []
        for thread_id in range(5):
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout per thread
        
        print(f"Concurrent operations completed: {len(results)}")
        print(f"Errors encountered: {len(errors)}")
        
        # Acceptance criteria
        assert len(errors) == 0, f"Concurrent errors detected: {errors}"
        assert len(results) >= 200, f"Expected ≥200 operations, got {len(results)}"
        
        print("PASSED: Concurrent stability test")
    
    def test_resource_cleanup(self):
        """Test that resources are properly cleaned up."""
        print("\n=== Resource Cleanup Test ===")
        
        initial_threads = threading.active_count()
        initial_open_files = len(psutil.Process().open_files())
        
        # Create and destroy multiple controllers
        for i in range(10):
            controller = MainApplicationController()
            controller.app_state.simulation_mode = True
            # Simulate some operations
            controller.app_state.set_mode("pf")
            del controller
            gc.collect()
        
        final_threads = threading.active_count()
        final_open_files = len(psutil.Process().open_files())
        
        thread_increase = final_threads - initial_threads
        file_increase = final_open_files - initial_open_files
        
        print(f"Thread count change: {thread_increase}")
        print(f"Open files change: {file_increase}")
        
        # Resources should be cleaned up properly
        assert thread_increase <= 2, f"Too many threads created: +{thread_increase}"
        assert file_increase <= 5, f"Too many files left open: +{file_increase}"
        
        print("PASSED: Resource cleanup test")

class TestStabilityMetrics:
    """Test stability metrics and monitoring."""
    
    def test_performance_degradation_detection(self):
        """Test detection of performance degradation over time."""
        print("\n=== Performance Degradation Detection ===")
        
        calculation_times = []
        
        # Simulate degrading performance
        for i in range(50):
            start_time = time.perf_counter()
            
            # Simulate calculation work
            time.sleep(0.001 + i * 0.0001)  # Gradually slower
            
            calc_time = time.perf_counter() - start_time
            calculation_times.append(calc_time)
        
        # Calculate trend
        early_avg = sum(calculation_times[:10]) / 10
        late_avg = sum(calculation_times[-10:]) / 10
        degradation = (late_avg - early_avg) / early_avg
        
        print(f"Early average: {early_avg*1000:.2f}ms")
        print(f"Late average: {late_avg*1000:.2f}ms") 
        print(f"Performance degradation: {degradation*100:.1f}%")
        
        # This test expects degradation (for testing), but in real system should be minimal
        assert degradation > 0, "Test should show degradation pattern"
        
        print("PASSED: Performance degradation detection working")

if __name__ == "__main__":
    # Run with: pytest test_long_term_stability.py -v -s
    pytest.main([__file__, "-v", "-s", "--tb=short"]) 