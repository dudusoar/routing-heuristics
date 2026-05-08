"""End-to-end integration tests for Routing Heuristics."""

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


class TestEndToEndWorkflow:
    """Test complete VRP workflow from data generation to solution."""
    
    def test_minimal_workflow(self):
        """Test minimal workflow with synthetic data."""
        np.random.seed(42)
        
        # 1. Create synthetic map
        n_nodes = 11  # 1 depot + 2 restaurants + 8 customers
        coordinates = np.random.rand(n_nodes, 2) * 100
        
        real_map = RealMap(
            coordinates=coordinates,
            restaurants=[1, 2],  # 2 restaurants
            customers=list(range(3, 11)),  # 8 customers
            depot=[0]
        )
        
        # Verify map
        assertions.assert_distance_matrix_valid(real_map.distance_matrix)
        
        # 2. Generate demand
        time_params_demand = {
            'peak_hours': [(8, 10)],
            'base_demand': 5.0,
            'peak_multiplier': 2.0,
            'random_seed': 42
        }
        
        demand_generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params_demand,
            n_time_intervals=12  # 12 time intervals
        )
        
        demand_table = demand_generator.demand_table
        assert demand_table.shape == (12, 2, 8)  # (time, restaurants, customers)
        assert np.all(demand_table >= 0)
        
        # 3. Generate orders
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
        assertions.assert_order_table_valid(order_table)
        
        # Should have orders (depends on demand)
        n_pickups = (order_table['Type'] == 'cp').sum()
        n_deliveries = (order_table['Type'] == 'cd').sum()
        
        # If there's demand, should have orders
        if np.any(demand_table > 0):
            assert n_pickups > 0
            assert n_deliveries > 0
        
        # 4. Create PDPTW instance
        # Use map's distance matrix
        distance_matrix = real_map.distance_matrix
        time_matrix = distance_matrix / 2.0  # Assuming speed 2.0
        
        instance = PDPTWInstance(
            order_table=order_table,
            distance_matrix=distance_matrix,
            time_matrix=time_matrix,
            robot_speed=2.0
        )
        
        # Verify instance
        test_helpers.assert_instance_valid(instance)
        
        # 5. Create initial solution
        initial_solution = greedy_insertion_initial_solution(
            instance=instance,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            vehicle_capacity=20.0
        )
        
        # Verify solution
        test_helpers.assert_solution_valid(initial_solution)
        
        # 6. Configure and run ALNS
        alns_config = ALNSConfig(
            num_removal=3,
            max_no_improve=10,  # Small for testing
            start_temp=50.0,
            cooling_rate=0.9
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # 7. Solve
        final_solution = solver.solve(instance)
        
        # Verify final solution
        test_helpers.assert_solution_valid(final_solution)
        
        # Should have objective value
        initial_obj = initial_solution.objective_function()
        final_obj = final_solution.objective_function()
        
        assert isinstance(initial_obj, (int, float))
        assert isinstance(final_obj, (int, float))
        
        # ALNS might improve or stay the same
        # final_obj <= initial_obj is possible but not guaranteed
        # due to random elements in ALNS
        
        # 8. Check feasibility (might not be feasible due to constraints)
        # Just verify the method works
        is_feasible = final_solution.is_feasible()
        assert isinstance(is_feasible, bool)
    
    def test_workflow_with_small_instance(self):
        """Test workflow with very small instance for speed."""
        np.random.seed(123)
        
        # Create minimal instance
        n_orders = 2  # Very small
        instance = test_helpers.create_minimal_pdptw_instance(
            n_orders=n_orders,
            seed=123,
            robot_speed=2.0
        )
        
        # Create initial solution
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance,
            n_orders=n_orders,
            n_vehicles=1,
            seed=123
        )
        
        # Quick ALNS configuration
        alns_config = ALNSConfig(
            num_removal=1,
            max_no_improve=3,  # Very few iterations
            start_temp=30.0,
            cooling_rate=0.8
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Solve (should be fast)
        final_solution = solver.solve(instance)
        
        # Verify
        test_helpers.assert_solution_valid(final_solution)
        
        # Check routes are valid
        assertions.assert_routes_valid(
            final_solution.routes,
            len(instance.indices)
        )
    
    def test_workflow_multiple_vehicles(self):
        """Test workflow with multiple vehicles."""
        np.random.seed(456)
        
        # Create instance with more orders
        n_orders = 4
        instance = test_helpers.create_minimal_pdptw_instance(
            n_orders=n_orders,
            seed=456
        )
        
        # Create initial solution with 2 vehicles
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance,
            n_orders=n_orders,
            n_vehicles=2,  # Two vehicles
            seed=456
        )
        
        # Verify initial solution has 2 vehicles
        assert len(initial_solution.routes) == 2
        
        # Quick ALNS
        alns_config = ALNSConfig(
            num_removal=2,
            max_no_improve=5,
            start_temp=40.0,
            cooling_rate=0.85
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        final_solution = solver.solve(instance)
        
        # Verify
        test_helpers.assert_solution_valid(final_solution)
        
        # Could have 1 or 2 vehicles after optimization
        assert 1 <= len(final_solution.routes) <= 2


class TestConfigurationIntegration:
    """Test integration with configuration system."""
    
    def test_alns_config_integration(self):
        """Test ALNS configuration integration."""
        # Create instance
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        
        # Create initial solution
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance
        )
        
        # Test different configurations
        configs = [
            ALNSConfig(max_no_improve=5, start_temp=30.0),  # Fast
            ALNSConfig(max_no_improve=20, start_temp=100.0),  # Slower
            ALNSConfig(num_removal=1, segment_length=5, num_segments=3),  # Different params
        ]
        
        for config in configs:
            solver = ALNS(
                initial_solution=initial_solution,
                config=config,
                dist_matrix=instance.distance_matrix,
                battery_capacity=100.0
            )
            
            # Should be able to get config back
            retrieved_config = solver.get_config()
            assert retrieved_config.max_no_improve == config.max_no_improve
            assert retrieved_config.start_temp == config.start_temp
            
            # Quick solve
            solution = solver.solve(instance)
            assert solution is not None
    
    def test_config_update_during_solving(self):
        """Test updating configuration during solving."""
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance
        )
        
        # Start with fast configuration
        config = ALNSConfig(max_no_improve=3, start_temp=30.0)
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Update config before solving
        new_config = ALNSConfig(max_no_improve=5, start_temp=50.0)
        solver.update_config(new_config)
        
        # Should use new config
        assert solver.config.max_no_improve == 5
        assert solver.config.start_temp == 50.0
        
        solution = solver.solve(instance)
        assert solution is not None


class TestInterfaceIntegration:
    """Test integration through abstract interfaces."""
    
    def test_vrp_problem_solution_integration(self):
        """Test VRPProblem and VRPSolution interface integration."""
        from vrp_toolkit.algorithms.base import VRPProblem, VRPSolution
        
        # Create PDPTW instance (implements VRPProblem)
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        
        # Cast to interface
        problem: VRPProblem = instance
        
        # Use interface methods
        n_nodes = problem.get_num_nodes()
        dist_matrix = problem.get_distance_matrix()
        time_windows = problem.get_time_windows()
        
        assert n_nodes > 0
        assert dist_matrix.shape == (n_nodes, n_nodes)
        assert len(time_windows) == n_nodes
        
        # Create solution (implements VRPSolution)
        solution = test_helpers.create_minimal_pdptw_solution(instance=instance)
        solution_interface: VRPSolution = solution
        
        # Use interface methods
        routes = solution_interface.get_routes()
        obj_value = solution_interface.get_objective_value()
        feasible = solution_interface.is_feasible()
        
        assert len(routes) > 0
        assert isinstance(obj_value, (int, float))
        assert isinstance(feasible, bool)
    
    def test_solver_interface_integration(self):
        """Test Solver interface integration."""
        from vrp_toolkit.algorithms.base import Solver
        
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        initial_solution = test_helpers.create_minimal_pdptw_solution(
            instance=instance
        )
        
        config = ALNSConfig(max_no_improve=3)
        
        # Create ALNS solver (implements Solver/ConfigurableSolver)
        solver = ALNS(
            initial_solution=initial_solution,
            config=config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Cast to Solver interface
        solver_interface: Solver = solver
        
        # Use interface method
        solution = solver_interface.solve(instance)
        assert solution is not None
        
        # ALNS also implements ConfigurableSolver
        from vrp_toolkit.algorithms.base import ConfigurableSolver
        config_solver: ConfigurableSolver = solver
        
        config = config_solver.get_config()
        assert config is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
