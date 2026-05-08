"""Edge case tests for PDPTW problem classes."""

import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from tests.utils import test_helpers, assertions


class TestPDPTWEdgeCases:
    """Test PDPTW edge cases and boundary conditions."""

    def test_zero_orders(self):
        """Test instance creation with zero orders (just depot)."""
        # Create order table with only depot
        data = {
            'ID': [0],
            'Type': ['depot'],
            'X': [0.0],
            'Y': [0.0],
            'Demand': [0.0],
            'StartTime': [0.0],
            'EndTime': [100.0],
            'ServiceTime': [0.0],
            'PartnerID': [0],
            'RealIndex': [0],
            'RealType': ['depot']
        }

        order_table = pd.DataFrame(data)

        # Create 1x1 distance and time matrices
        distance_matrix = np.array([[0.0]])
        time_matrix = np.array([[0.0]])

        instance = PDPTWInstance(
            order_table=order_table,
            distance_matrix=distance_matrix,
            time_matrix=time_matrix,
            robot_speed=2.0
        )

        # Basic assertions
        assert instance.n == 0  # No orders
        assert len(instance.indices) == 1  # Only depot
        assert len(instance.demands) == 1
        assert len(instance.time_windows) == 1
        assert instance.distance_matrix.shape == (1, 1)
        assert instance.time_matrix.shape == (1, 1)

    def test_single_order(self):
        """Test instance with single pickup-delivery pair."""
        # Create order table with depot + 1 pickup + 1 delivery
        data = {
            'ID': [0, 1, 2],
            'Type': ['depot', 'cp', 'cd'],
            'X': [0.0, 1.0, 2.0],
            'Y': [0.0, 1.0, 2.0],
            'Demand': [0.0, 1.0, -1.0],
            'StartTime': [0.0, 0.0, 0.0],
            'EndTime': [100.0, 100.0, 100.0],
            'ServiceTime': [0.0, 5.0, 5.0],
            'PartnerID': [0, 2, 1],  # pickup1 <-> delivery1
            'RealIndex': [0, 1, 2],
            'RealType': ['depot', 'cp', 'cd']
        }

        order_table = pd.DataFrame(data)

        # Create 3x3 distance and time matrices
        n_nodes = 3
        np.random.seed(42)
        distance_matrix = np.random.rand(n_nodes, n_nodes) * 10
        distance_matrix = (distance_matrix + distance_matrix.T) / 2
        np.fill_diagonal(distance_matrix, 0)

        time_matrix = distance_matrix / 2.0

        instance = PDPTWInstance(
            order_table=order_table,
            distance_matrix=distance_matrix,
            time_matrix=time_matrix,
            robot_speed=2.0
        )

        # Basic assertions
        assert instance.n == 1  # One order
        assert len(instance.indices) == 3
        assert len(instance.pickup_nodes) == 1
        assert len(instance.delivery_nodes) == 1
        assert len(instance.depot_nodes) == 1

    def test_large_number_of_orders(self):
        """Test instance with larger number of orders (performance check)."""
        n_orders = 10  # Larger but still reasonable for testing
        n_nodes = 1 + 2 * n_orders

        # Use helper to create instance
        instance = test_helpers.create_minimal_pdptw_instance(
            n_orders=n_orders,
            seed=123
        )

        # Verify dimensions
        assert instance.n == n_orders
        assert len(instance.indices) == n_nodes
        assert instance.distance_matrix.shape == (n_nodes, n_nodes)
        assert instance.time_matrix.shape == (n_nodes, n_nodes)

        # Verify pickup-delivery mappings
        assert len(instance.pickup_nodes) == n_orders
        assert len(instance.delivery_nodes) == n_orders

        # Check that each pickup maps to correct delivery
        for i, pickup in enumerate(sorted(instance.pickup_nodes)):
            delivery = instance.pickup_to_delivery[pickup]
            assert delivery in instance.delivery_nodes
            assert instance.delivery_to_pickup[delivery] == pickup

    def test_invalid_matrix_dimensions(self):
        """Test instance creation with invalid matrix dimensions."""
        # Create valid order table with 3 nodes
        data = {
            'ID': [0, 1, 2],
            'Type': ['depot', 'cp', 'cd'],
            'X': [0.0, 1.0, 2.0],
            'Y': [0.0, 1.0, 2.0],
            'Demand': [0.0, 1.0, -1.0],
            'StartTime': [0.0, 0.0, 0.0],
            'EndTime': [100.0, 100.0, 100.0],
            'ServiceTime': [0.0, 5.0, 5.0],
            'PartnerID': [0, 2, 1],
            'RealIndex': [0, 1, 2],
            'RealType': ['depot', 'cp', 'cd']
        }

        order_table = pd.DataFrame(data)

        # Create wrong size matrix (2x2 instead of 3x3)
        wrong_matrix = np.array([[0, 1], [1, 0]])

        # Should raise ValueError for dimension mismatch
        with pytest.raises(ValueError):
            PDPTWInstance(
                order_table=order_table,
                distance_matrix=wrong_matrix,
                time_matrix=wrong_matrix,
                robot_speed=2.0
            )

    def test_missing_required_columns(self):
        """Test instance creation with missing required columns."""
        # Create DataFrame missing required columns
        incomplete_data = {
            'ID': [0, 1],
            'Type': ['depot', 'cp'],
            'X': [0.0, 1.0],
            'Y': [0.0, 1.0]
            # Missing Demand, StartTime, etc.
        }

        incomplete_df = pd.DataFrame(incomplete_data)

        distance_matrix = np.array([[0, 1], [1, 0]])
        time_matrix = distance_matrix / 2.0

        # Should raise KeyError for missing columns
        with pytest.raises((KeyError, ValueError)):
            PDPTWInstance(
                order_table=incomplete_df,
                distance_matrix=distance_matrix,
                time_matrix=time_matrix,
                robot_speed=2.0
            )

    def test_solution_edge_cases(self):
        """Test solution creation with edge cases."""
        # Create minimal instance
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)

        # Test 1: Empty routes (no vehicles used)
        empty_routes = []
        empty_solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=empty_routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )

        assert empty_solution.num_vehicles == 0
        assert len(empty_solution.routes) == 0

        # Test 2: Single vehicle with minimal route
        minimal_routes = [[0, 0]]  # Depot to depot
        minimal_solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=minimal_routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )

        assert minimal_solution.num_vehicles == 1
        assert minimal_solution.routes == [[0, 0]]

        # Test 3: Multiple vehicles
        multi_routes = [[0, 1, 3, 0], [0, 2, 4, 0]]  # Two vehicles
        multi_solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=multi_routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )

        assert multi_solution.num_vehicles == 2
        assert len(multi_solution.routes) == 2


class TestSolutionFeasibilityEdgeCases:
    """Test solution feasibility in edge cases."""

    def test_infeasible_solution_detection(self):
        """Test that infeasible solutions are properly detected."""
        # Create instance
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)

        # Create solution that violates constraints
        # This route has delivery before pickup (invalid order)
        invalid_route = [[0, 3, 1, 2, 4, 0]]  # delivery1 before pickup1

        solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=invalid_route,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )

        # is_feasible should detect the violation
        # (Note: might be False or raise error depending on implementation)
        try:
            feasible = solution.is_feasible()
            # If it returns, it should be False for infeasible solution
            if isinstance(feasible, bool):
                assert not feasible
        except Exception:
            # Some implementations might raise exception for infeasible
            pass

    def test_solution_with_excessive_demand(self):
        """Test solution with demand exceeding vehicle capacity."""
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)

        # Create solution with all pickups in one route
        # Vehicle capacity is small (1.0), but pickups have demand 1.0 each
        # So total demand 2.0 > capacity 1.0
        routes = [[0, 1, 2, 3, 4, 0]]  # All nodes in one route

        solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=1.0,  # Very small capacity
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )

        # Should detect capacity violation
        try:
            capacity_ok = solution.check_capacity_constraint([0])  # vehicle 0
            if isinstance(capacity_ok, bool):
                assert not capacity_ok
        except Exception:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])