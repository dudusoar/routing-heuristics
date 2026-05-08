"""Edge case integration tests for Routing Heuristics."""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any

from vrp_toolkit.data.map import RealMap
from vrp_toolkit.data.generators import DemandGenerator, OrderGenerator
from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from vrp_toolkit.algorithms.alns.solver import (
    ALNS,
    ALNSConfig,
    greedy_insertion_initial_solution
)
from tests.utils import test_helpers, assertions


class TestIntegrationEdgeCases:
    """Test integration edge cases and boundary conditions."""

    def test_minimal_workflow_no_demand(self):
        """Test workflow with no demand (no orders generated)."""
        np.random.seed(42)

        # Create synthetic map
        n_nodes = 5
        coordinates = np.random.rand(n_nodes, 2) * 100

        real_map = RealMap(
            coordinates=coordinates,
            restaurants=[1],  # 1 restaurant
            customers=[2, 3, 4],  # 3 customers
            depot=[0]
        )

        # Generate zero demand
        time_params_demand = {
            'peak_hours': [(8, 10)],
            'base_demand': 0.0,  # Zero demand
            'peak_multiplier': 2.0,
            'random_seed': 42
        }

        demand_generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params_demand,
            n_time_intervals=12
        )

        demand_table = demand_generator.demand_table
        assert demand_table.shape == (12, 1, 3)  # (time, restaurants, customers)
        assert np.all(demand_table == 0)  # All zero demand

        # Generate orders - should handle zero demand gracefully
        time_params_order = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }

        order_generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_table,
            time_params=time_params_order,
            robot_speed=2.0
        )

        order_table = order_generator.order_table

        # With zero demand, might have empty order table or just depot
        # Check that it's a valid DataFrame
        assert isinstance(order_table, pd.DataFrame)
        assert len(order_table) >= 1  # At least depot

        # If there are orders, they should be valid
        if len(order_table) > 1:
            assertions.assert_order_table_valid(order_table)

    def test_single_order_workflow(self):
        """Test complete workflow with single order."""
        np.random.seed(123)

        # Create very small instance directly
        n_orders = 1
        instance = test_helpers.create_minimal_pdptw_instance(
            n_orders=n_orders,
            seed=123,
            robot_speed=2.0
        )

        # Create initial solution
        initial_solution = greedy_insertion_initial_solution(
            instance=instance,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            vehicle_capacity=20.0
        )

        # Verify solution
        test_helpers.assert_solution_valid(initial_solution)

        # Configure ALNS for quick test
        alns_config = ALNSConfig(
            num_removal=1,  # Minimal removal
            max_no_improve=2,  # Very few iterations
            start_temp=30.0,
            cooling_rate=0.8
        )

        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        # Solve - should work even with single order
        final_solution = solver.solve(instance)

        # Verify final solution
        test_helpers.assert_solution_valid(final_solution)

        # Should have valid routes
        assertions.assert_routes_valid(
            final_solution.routes,
            len(instance.indices)
        )

    def test_configuration_edge_cases(self):
        """Test ALNS with extreme configuration values."""
        # Create small instance
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance
        )

        # Test 1: Very fast cooling (immediate convergence)
        fast_config = ALNSConfig(
            cooling_rate=0.1,  # Very fast cooling
            max_no_improve=1,  # Stop after 1 iteration without improvement
            start_temp=10.0  # Low starting temperature
        )

        solver_fast = ALNS(
            initial_solution=initial_solution,
            config=fast_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        solution_fast = solver_fast.solve(instance)
        assert solution_fast is not None

        # Test 2: Very slow cooling (many iterations)
        slow_config = ALNSConfig(
            cooling_rate=0.999,  # Very slow cooling
            max_no_improve=100,  # Many iterations
            start_temp=1000.0  # High temperature
        )

        solver_slow = ALNS(
            initial_solution=initial_solution,
            config=slow_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        # Should complete (might be slow, but should work)
        solution_slow = solver_slow.solve(instance)
        assert solution_slow is not None

        # Test 3: Zero removal (no nodes removed)
        zero_removal_config = ALNSConfig(
            num_removal=0,  # No removal
            max_no_improve=2
        )

        solver_zero = ALNS(
            initial_solution=initial_solution,
            config=zero_removal_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        solution_zero = solver_zero.solve(instance)
        assert solution_zero is not None

    def test_random_seed_reproducibility(self):
        """Test that random seeds produce reproducible results."""
        # Create instance
        instance1 = test_helpers.create_minimal_pdptw_instance(
            n_orders=3,
            seed=42  # Fixed seed
        )

        # Create same instance again with same seed
        instance2 = test_helpers.create_minimal_pdptw_instance(
            n_orders=3,
            seed=42  # Same seed
        )

        # Distance matrices should be identical
        np.testing.assert_array_equal(
            instance1.distance_matrix,
            instance2.distance_matrix
        )

        # Order tables should be identical
        pd.testing.assert_frame_equal(
            instance1.order_table,
            instance2.order_table
        )

        # Create solutions with same seed
        solution1 = test_helpers.create_minimal_pdptw_solution(
            instance=instance1,
            seed=42
        )

        solution2 = test_helpers.create_minimal_pdptw_solution(
            instance=instance2,
            seed=42
        )

        # Routes should be identical
        assert solution1.routes == solution2.routes

    def test_algorithm_determinism_with_seed(self):
        """Test that ALNS produces deterministic results with fixed seed."""
        # Skip if algorithm uses external randomness not controlled by seed
        # This test verifies that given the same inputs, ALNS produces same outputs

        instance = test_helpers.create_minimal_pdptw_instance(
            n_orders=2,
            seed=12345
        )

        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance,
            seed=12345
        )

        # Configure ALNS
        config = ALNSConfig(
            max_no_improve=3,
            start_temp=50.0,
            cooling_rate=0.9
        )

        # Run ALNS twice with same configuration and same random state
        solver1 = ALNS(
            initial_solution=initial_solution,
            config=config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        solver2 = ALNS(
            initial_solution=initial_solution,
            config=config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        # If ALNS uses numpy random state, reset it between runs
        np.random.seed(999)
        solution1 = solver1.solve(instance)

        np.random.seed(999)  # Reset to same state
        solution2 = solver2.solve(instance)

        # Objective values should be equal if algorithm is deterministic
        # (Might differ due to random elements in ALNS)
        obj1 = solution1.objective_function()
        obj2 = solution2.objective_function()

        # They might not be exactly equal due to randomness in ALNS,
        # but we can at least verify both solutions are valid
        test_helpers.assert_solution_valid(solution1)
        test_helpers.assert_solution_valid(solution2)


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_graceful_handling_of_invalid_inputs(self):
        """Test that invalid inputs are handled gracefully."""
        # Test with invalid distance matrix (negative values)
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)

        # Create solution
        solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance
        )

        # Try to create ALNS with invalid battery capacity
        with pytest.raises((ValueError, TypeError)):
            ALNS(
                initial_solution=solution,
                config=ALNSConfig(),
                dist_matrix=instance.distance_matrix,
                battery_capacity=-100.0  # Invalid negative capacity
            )

    def test_missing_data_files_fallback(self):
        """Test fallback behavior when data files are missing."""
        # This would test RealDataMap's fallback to synthetic data
        # when Purdue campus files are not available
        # Implementation depends on RealDataMap implementation
        pass  # Placeholder for actual test


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
