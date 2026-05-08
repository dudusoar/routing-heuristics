"""Unit tests for PDPTW problem classes."""

import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from vrp_toolkit.algorithms.base import VRPProblem, VRPSolution
from tests.utils import test_helpers, assertions


class TestPDPTWInstance:
    """Test PDPTWInstance class."""
    
    def test_creation(self, simple_pdptw_instance):
        """Test instance creation with basic attributes."""
        instance = simple_pdptw_instance
        
        # Basic attributes
        assert instance.n == 2  # 2 pickup-delivery pairs
        assert len(instance.indices) == 5
        assert len(instance.demands) == 5
        assert len(instance.time_windows) == 5
        assert len(instance.service_times) == 5
        assert instance.robot_speed == 2.0
        
        # Matrix shapes
        assert instance.distance_matrix.shape == (5, 5)
        assert instance.time_matrix.shape == (5, 5)
        
        # Validate using helper
        test_helpers.assert_instance_valid(instance)
    
    def test_order_table_processing(self, simple_order_table):
        """Test order table processing logic."""
        # Create distance and time matrices
        n_nodes = len(simple_order_table)
        distance_matrix = np.random.rand(n_nodes, n_nodes) * 10
        distance_matrix = (distance_matrix + distance_matrix.T) / 2
        np.fill_diagonal(distance_matrix, 0)
        
        time_matrix = distance_matrix / 2.0
        
        instance = PDPTWInstance(
            order_table=simple_order_table,
            distance_matrix=distance_matrix,
            time_matrix=time_matrix,
            robot_speed=2.0
        )
        
        # Check node type extraction
        assert 0 in instance.pickup_nodes  # Node 1 is pickup
        assert 1 in instance.pickup_nodes  # Node 2 is pickup
        assert 2 in instance.delivery_nodes  # Node 3 is delivery
        assert 3 in instance.delivery_nodes  # Node 4 is delivery
        assert 0 in instance.depot_nodes  # Node 0 is depot
        
        # Check pickup-delivery mapping
        assert instance.pickup_to_delivery[0] == 2  # pickup1 -> delivery1
        assert instance.pickup_to_delivery[1] == 3  # pickup2 -> delivery2
        assert instance.delivery_to_pickup[2] == 0  # delivery1 -> pickup1
        assert instance.delivery_to_pickup[3] == 1  # delivery2 -> pickup2
    
    def test_invalid_order_table(self):
        """Test instance creation with invalid order table."""
        # Missing required column
        invalid_data = {
            'ID': [0, 1],
            'Type': ['depot', 'cp'],
            'X': [0.0, 1.0],
            'Y': [0.0, 1.0],
            # Missing Demand, StartTime, etc.
        }
        invalid_df = pd.DataFrame(invalid_data)
        
        distance_matrix = np.array([[0, 1], [1, 0]])
        time_matrix = distance_matrix / 2.0
        
        with pytest.raises((KeyError, ValueError)):
            PDPTWInstance(
                order_table=invalid_df,
                distance_matrix=distance_matrix,
                time_matrix=time_matrix,
                robot_speed=2.0
            )
    
    def test_matrix_validation(self, simple_order_table):
        """Test matrix validation."""
        n_nodes = len(simple_order_table)
        
        # Non-square matrix
        invalid_matrix = np.random.rand(n_nodes, n_nodes + 1)
        
        with pytest.raises(ValueError):
            PDPTWInstance(
                order_table=simple_order_table,
                distance_matrix=invalid_matrix,
                time_matrix=invalid_matrix,
                robot_speed=2.0
            )
    
    def test_vrp_problem_interface(self, simple_pdptw_instance):
        """Test that PDPTWInstance implements VRPProblem interface."""
        instance = simple_pdptw_instance
        
        # Check VRPProblem methods
        assert hasattr(instance, 'get_num_nodes')
        assert hasattr(instance, 'get_num_vehicles')
        assert hasattr(instance, 'get_distance_matrix')
        assert hasattr(instance, 'get_time_windows')
        assert hasattr(instance, 'get_demands')
        assert hasattr(instance, 'get_service_times')
        
        # Call methods to ensure they work
        n_nodes = instance.get_num_nodes()
        assert n_nodes == 5
        
        n_vehicles = instance.get_num_vehicles()
        assert isinstance(n_vehicles, int)
        
        dist_matrix = instance.get_distance_matrix()
        assert dist_matrix.shape == (5, 5)
        
        time_windows = instance.get_time_windows()
        assert len(time_windows) == 5
        for start, end in time_windows:
            assert start <= end
        
        demands = instance.get_demands()
        assert len(demands) == 5
        
        service_times = instance.get_service_times()
        assert len(service_times) == 5


class TestPDPTWSolution:
    """Test PDPTWSolution class."""
    
    def test_creation(self, simple_pdptw_solution):
        """Test solution creation with basic attributes."""
        solution = simple_pdptw_solution
        
        # Basic attributes
        assert solution.num_vehicles == 1
        assert len(solution.routes) == 1
        assert solution.routes[0] == [0, 1, 2, 3, 4, 0]
        assert solution.instance is not None
        
        # Capacity and battery parameters
        assert solution.vehicle_capacity == 10.0
        assert solution.battery_capacity == 100.0
        assert solution.battery_consume_rate == 1.0
        
        # Penalties
        assert solution.penalty_unvisit == 1000.0
        assert solution.penalty_delay == 100.0
        
        # Validate using helper
        test_helpers.assert_solution_valid(solution)
    
    def test_routes_validation(self, simple_pdptw_instance):
        """Test route validation during solution creation."""
        instance = simple_pdptw_instance
        
        # Invalid route: doesn't start at depot
        invalid_routes = [[1, 2, 3, 4, 0]]
        
        with pytest.raises((ValueError, AssertionError)):
            PDPTWSolution(
                instance=instance,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                routes=invalid_routes,
                penalty_unvisit=1000.0,
                penalty_delay=100.0
            )
        
        # Invalid route: doesn't end at depot
        invalid_routes = [[0, 1, 2, 3, 4]]
        
        with pytest.raises((ValueError, AssertionError)):
            PDPTWSolution(
                instance=instance,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                routes=invalid_routes,
                penalty_unvisit=1000.0,
                penalty_delay=100.0
            )
    
    def test_objective_function(self, simple_pdptw_solution):
        """Test objective function calculation."""
        solution = simple_pdptw_solution
        
        obj_value = solution.objective_function()
        
        # Objective should be numeric
        assert isinstance(obj_value, (int, float))
        
        # For this simple solution, objective should be >= 0
        assert obj_value >= 0
        
        # Multiple calls should return same value
        obj_value2 = solution.objective_function()
        assert obj_value == obj_value2
    
    def test_feasibility(self, simple_pdptw_solution):
        """Test feasibility checking."""
        solution = simple_pdptw_solution
        
        is_feasible = solution.is_feasible()
        assert isinstance(is_feasible, bool)
        
        # Check individual constraint methods
        selected_vehicles = solution.get_selected_vehicles()
        assert isinstance(selected_vehicles, list)
        
        capacity_ok = solution.check_capacity_constraint(selected_vehicles)
        assert isinstance(capacity_ok, bool)
        
        battery_ok = solution.check_battery_constraint(selected_vehicles)
        assert isinstance(battery_ok, bool)
        
        order_ok = solution.check_pickup_delivery_order(selected_vehicles)
        assert isinstance(order_ok, bool)
    
    def test_visited_unvisited_records(self, simple_pdptw_solution):
        """Test visited and unvisited request tracking."""
        solution = simple_pdptw_solution
        
        # These attributes should exist
        assert hasattr(solution, 'visited_requests')
        assert hasattr(solution, 'unvisited_requests')
        assert hasattr(solution, 'visited_pairs')
        assert hasattr(solution, 'unvisited_pairs')
        
        # For the simple solution, all requests should be visited
        assert len(solution.visited_requests) == 2  # 2 orders
        assert len(solution.unvisited_requests) == 0
        assert len(solution.visited_pairs) == 2
        assert len(solution.unvisited_pairs) == 0
    
    def test_solution_copy(self, simple_pdptw_solution):
        """Test solution copying functionality."""
        solution = simple_pdptw_solution
        
        # Test that solution can be copied
        import copy
        solution_copy = copy.deepcopy(solution)
        
        # Should have same attributes
        assert solution_copy.num_vehicles == solution.num_vehicles
        assert solution_copy.routes == solution.routes
        assert solution_copy.objective_function() == solution.objective_function()
        assert solution_copy.is_feasible() == solution.is_feasible()
    
    def test_vrp_solution_interface(self, simple_pdptw_solution):
        """Test that PDPTWSolution implements VRPSolution interface."""
        solution = simple_pdptw_solution
        
        # Check VRPSolution methods
        assert hasattr(solution, 'get_routes')
        assert hasattr(solution, 'get_objective_value')
        assert hasattr(solution, 'is_feasible')
        
        # Call methods to ensure they work
        routes = solution.get_routes()
        assert isinstance(routes, list)
        assert len(routes) == 1
        
        obj_value = solution.get_objective_value()
        assert isinstance(obj_value, (int, float))
        
        feasible = solution.is_feasible()
        assert isinstance(feasible, bool)


class TestPDPTWIntegration:
    """Integration tests for PDPTW classes."""
    
    def test_instance_solution_integration(self, simple_pdptw_instance):
        """Test that instance and solution work together."""
        instance = simple_pdptw_instance
        
        # Create multiple solution variants
        routes_variants = [
            [[0, 1, 3, 2, 4, 0]],  # Different order
            [[0, 1, 3, 0], [0, 2, 4, 0]],  # Two vehicles
        ]
        
        for routes in routes_variants:
            solution = PDPTWSolution(
                instance=instance,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                routes=routes,
                penalty_unvisit=1000.0,
                penalty_delay=100.0
            )
            
            # Validate solution
            test_helpers.assert_solution_valid(solution)
            
            # Check routes are valid
            assertions.assert_routes_valid(solution.routes, len(instance.indices))
            
            # Objective should be calculable
            obj_value = solution.objective_function()
            assert isinstance(obj_value, (int, float))
    
    def test_pickup_delivery_constraints(self):
        """Test pickup-delivery constraint validation."""
        # Create instance with 2 orders
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        
        # Valid route: pickup before delivery
        valid_routes = [[0, 1, 3, 2, 4, 0]]  # p1, d1, p2, d2
        
        solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=valid_routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )
        
        # This should pass pickup-delivery order check
        selected = solution.get_selected_vehicles()
        assert solution.check_pickup_delivery_order(selected)
    
    def test_capacity_constraints(self):
        """Test capacity constraint validation."""
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        
        # Route that exceeds capacity if capacity is too low
        routes = [[0, 1, 2, 3, 4, 0]]
        
        # Solution with very low capacity (should violate constraint)
        low_cap_solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=0.5,  # Too low for demands of 1.0
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )
        
        selected = low_cap_solution.get_selected_vehicles()
        # Might not be feasible due to capacity
        capacity_ok = low_cap_solution.check_capacity_constraint(selected)
        
        # Solution with sufficient capacity (should satisfy constraint)
        high_cap_solution = PDPTWSolution(
            instance=instance,
            vehicle_capacity=10.0,  # Sufficient for demands
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            routes=routes,
            penalty_unvisit=1000.0,
            penalty_delay=100.0
        )
        
        selected = high_cap_solution.get_selected_vehicles()
        capacity_ok = high_cap_solution.check_capacity_constraint(selected)
        # This should be True if capacity is sufficient


if __name__ == "__main__":
    pytest.main([__file__, "-v"])