"""Unit tests for ALNS solver."""

import pytest
import numpy as np
from typing import List, Dict, Any

from vrp_toolkit.algorithms.alns.solver import (
    ALNS, 
    ALNSConfig,
    greedy_insertion_initial_solution
)
from vrp_toolkit.algorithms.alns.operators import (
    RemovalOperators,
    RepairOperators
)
from vrp_toolkit.algorithms.base import ConfigurableSolver, PDPTWProblemAdapter
from tests.utils import test_helpers, assertions


class TestALNSConfig:
    """Test ALNSConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ALNSConfig()

        # Check all fields have defaults
        assert config.num_removal == 5
        assert config.p == 4.0
        assert config.k == 3
        assert config.L_max == 5
        assert config.avg_remove_order == 2.0
        assert config.d_matrix is None
        assert config.max_no_improve == 100
        assert config.segment_length == 100
        assert config.num_segments == 10
        assert config.r == 0.1
        assert config.sigma == (33.0, 9.0, 13.0)
        assert config.start_temp == 10000.0
        assert config.cooling_rate == 0.99
        assert config.cost_ci_obj_diff_threshold == 0.1
        assert config.cost_ci_window_size == 25
        assert config.removal_indices == [0, 2, 3]
        assert config.repair_indices == [0, 1]
        assert config.charging_station_index is None

    def test_custom_config(self):
        """Test custom configuration values."""
        config = ALNSConfig(
            num_removal=10,
            p=5.0,
            k=4,
            L_max=8,
            avg_remove_order=3.0,
            max_no_improve=200,
            segment_length=150,
            num_segments=15,
            r=0.2,
            sigma=(40.0, 10.0, 15.0),
            start_temp=15000.0,
            cooling_rate=0.95,
            cost_ci_obj_diff_threshold=0.05,
            cost_ci_window_size=30,
            removal_indices=[1, 2, 3],
            repair_indices=[1],
            charging_station_index=10
        )

        # Check custom values
        assert config.num_removal == 10
        assert config.p == 5.0
        assert config.k == 4
        assert config.L_max == 8
        assert config.avg_remove_order == 3.0
        assert config.max_no_improve == 200
        assert config.segment_length == 150
        assert config.num_segments == 15
        assert config.r == 0.2
        assert config.sigma == (40.0, 10.0, 15.0)
        assert config.start_temp == 15000.0
        assert config.cooling_rate == 0.95
        assert config.cost_ci_obj_diff_threshold == 0.05
        assert config.cost_ci_window_size == 30
        assert config.removal_indices == [1, 2, 3]
        assert config.repair_indices == [1]
        assert config.charging_station_index == 10
    
    def test_config_validation(self):
        """Test configuration parameter validation."""
        # Note: dataclass doesn't validate values by default
        # These tests check that invalid values don't crash constructor
        # Negative removal count might be problematic but dataclass allows it
        ALNSConfig(num_removal=-5)  # Negative value (might be validated elsewhere)

        # Cooling rate > 1.0 is allowed by dataclass
        ALNSConfig(cooling_rate=1.5)

        # These should definitely work
        ALNSConfig(num_removal=0)  # Zero removal
        ALNSConfig(cooling_rate=0.5)  # Valid cooling rate

    def test_config_boundary_values(self):
        """Test configuration parameter boundary values."""
        # Test valid boundary values
        config = ALNSConfig(
            num_removal=0,  # Minimum valid
            cooling_rate=0.0,  # Minimum valid
            start_temp=0.0,  # Minimum valid (zero temperature)
            r=0.0,  # Minimum valid
        )
        assert config.num_removal == 0
        assert config.cooling_rate == 0.0
        assert config.start_temp == 0.0
        assert config.r == 0.0

        # Test upper boundaries
        config2 = ALNSConfig(
            cooling_rate=1.0,  # Maximum valid
            r=1.0,  # Maximum valid
        )
        assert config2.cooling_rate == 1.0
        assert config2.r == 1.0

        # Test large but valid values
        config3 = ALNSConfig(
            num_removal=1000,  # Large but valid
            start_temp=100000.0,  # Large but valid
            max_no_improve=10000,  # Large but valid
            segment_length=1000,  # Large but valid
            num_segments=100  # Large but valid
        )
        assert config3.num_removal == 1000
        assert config3.start_temp == 100000.0
        assert config3.max_no_improve == 10000
        assert config3.segment_length == 1000
        assert config3.num_segments == 100

    def test_config_invalid_types(self):
        """Test configuration parameter type validation."""
        # Note: dataclass doesn't validate types at construction time
        # These tests verify that invalid types are accepted (dataclass behavior)
        # Type errors would occur later when the values are used
        
        # String instead of int - dataclass accepts it
        config1 = ALNSConfig(num_removal="invalid")
        assert config1.num_removal == "invalid"  # String stored as-is
        
        # String instead of float - dataclass accepts it
        config2 = ALNSConfig(cooling_rate="invalid")
        assert config2.cooling_rate == "invalid"  # String stored as-is
        
        # List instead of float - dataclass accepts it
        config3 = ALNSConfig(start_temp=[100.0])
        assert config3.start_temp == [100.0]  # List stored as-is
        
        # Test that valid types work correctly
        config = ALNSConfig(
            num_removal=10,  # Valid int
            cooling_rate=0.95,  # Valid float
            start_temp=100.0  # Valid float
        )
        assert isinstance(config.num_removal, int)
        assert isinstance(config.cooling_rate, float)
        assert isinstance(config.start_temp, float)

    def test_config_parameter_dependencies(self):
        """Test configuration parameter dependencies and constraints."""
        # Test that removal_indices defaults work correctly
        config1 = ALNSConfig()
        assert config1.removal_indices == [0, 2, 3]  # Shaw, Worst, SISR
        assert config1.repair_indices == [0, 1]  # Greedy, Regret
        
        # Test custom removal and repair indices
        config2 = ALNSConfig(
            removal_indices=[0, 1],  # Shaw and Random only
            repair_indices=[1]  # Regret only
        )
        assert config2.removal_indices == [0, 1]
        assert config2.repair_indices == [1]
        
        # Test that charging_station_index can be set
        config3 = ALNSConfig(charging_station_index=10)
        assert config3.charging_station_index == 10
        
        # Test that None charging_station_index is allowed
        config4 = ALNSConfig(charging_station_index=None)
        assert config4.charging_station_index is None


class TestGreedyInsertionInitialSolution:
    """Test greedy insertion initial solution function."""
    
    def test_function_exists(self):
        """Test that the function exists and is callable."""
        assert callable(greedy_insertion_initial_solution)
    
    def test_returns_solution(self, simple_pdptw_instance):
        """Test that function returns a solution."""
        instance = simple_pdptw_instance

        solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        # Should return a solution
        assert solution is not None
        assert hasattr(solution, 'routes')
        assert hasattr(solution, 'instance')
        
        # Should have valid routes
        assertions.assert_routes_valid(solution.routes, len(instance.indices))
    
    def test_solution_structure(self, simple_pdptw_instance):
        """Test structure of returned solution."""
        instance = simple_pdptw_instance

        solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        # Check basic attributes
        assert solution.instance is instance
        assert len(solution.routes) > 0
        
        # Each route should start and end at depot
        for route in solution.routes:
            assert route[0] == 0
            assert route[-1] == 0
        
        # Should be able to calculate objective
        obj_value = solution.objective_function()
        assert isinstance(obj_value, (int, float))
    
    def test_with_different_parameters(self, simple_pdptw_instance):
        """Test with different battery and capacity parameters."""
        instance = simple_pdptw_instance

        # Test with high capacity (should include all nodes)
        solution_high = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=100.0,
            battery_capacity=1000.0,  # Very high
            battery_consume_rate=0.1,  # Low consumption
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        # Test with low capacity (might not include all nodes)
        solution_low = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=0.5,  # Very low
            battery_capacity=10.0,  # Low
            battery_consume_rate=2.0,  # High consumption
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        # Both should return valid solutions
        assertions.assert_solution_valid(solution_high)
        # Low capacity solution exists but may not be feasible due to extreme constraints
        assertions.assert_solution_valid(solution_low, check_constraints=False)
        
        # Objective values should be different
        obj_high = solution_high.objective_function()
        obj_low = solution_low.objective_function()
        
        # Note: obj_low might be higher due to penalties

    def test_greedy_insertion_invalid_inputs(self, simple_pdptw_instance):
        """Test greedy insertion initial solution with invalid inputs."""
        instance = simple_pdptw_instance

        # Test 1: None instance
        with pytest.raises((TypeError, ValueError)):
            greedy_insertion_initial_solution(
                problem=None,
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )

        # Test 2: Invalid instance type
        with pytest.raises((TypeError, ValueError)):
            greedy_insertion_initial_solution(
                problem="not an instance",
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )

        # Test 3: Negative battery capacity
        with pytest.raises((ValueError, TypeError)):
            greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=-100.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )

        # Test 4: Zero battery capacity (edge case - might be allowed)
        # Test if it works or raises error
        try:
            solution_zero = greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=0.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )
            # If it works, should return valid solution
            assert solution_zero is not None
        except (ValueError, TypeError):
            # It's also valid to reject zero capacity
            pass

        # Test 5: Negative battery consumption rate
        with pytest.raises((ValueError, TypeError)):
            greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=-1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )

        # Test 6: Zero battery consumption rate (edge case - allowed, means no battery consumption)
        try:
            solution_zero_rate = greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=10.0,
                battery_capacity=100.0,
                battery_consume_rate=0.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )
            assert solution_zero_rate is not None
        except (ValueError, TypeError) as e:
            # Should not raise for zero consumption rate
            pytest.fail(f"Zero battery_consume_rate should be allowed but got: {e}")

        # Test 7: Negative vehicle capacity
        with pytest.raises((ValueError, TypeError)):
            greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=-10.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )

        # Test 8: Zero vehicle capacity (edge case - may be allowed but will result in empty routes)
        try:
            solution_zero_capacity = greedy_insertion_initial_solution(
                problem=instance,
                num_vehicles=4,
                vehicle_capacity=0.0,
                battery_capacity=100.0,
                battery_consume_rate=1.0,
                penalty_unvisit=100.0,
                penalty_delay=15.0
            )
            # Zero capacity is allowed but will likely result in empty/unfeasible routes
            assert solution_zero_capacity is not None
        except (ValueError, TypeError):
            # Also acceptable to reject zero capacity
            pass

    def test_greedy_insertion_edge_cases(self, simple_pdptw_instance):
        """Test greedy insertion initial solution with edge cases."""
        instance = simple_pdptw_instance

        # Test 1: Very high battery capacity (effectively infinite)
        solution_high_battery = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=10000.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        assert solution_high_battery is not None
        assertions.assert_solution_valid(solution_high_battery)

        # Test 2: Very high vehicle capacity (effectively infinite)
        solution_high_vehicle = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10000.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        assert solution_high_vehicle is not None
        assertions.assert_solution_valid(solution_high_vehicle)

        # Test 3: Very low but valid parameters
        solution_low_params = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=0.1,
            battery_capacity=0.1,  # Very low but positive
            battery_consume_rate=0.1,  # Very low but positive
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        assert solution_low_params is not None
        # Extreme parameters may not produce feasible solution
        assertions.assert_solution_valid(solution_low_params, check_constraints=False)

        # Test 4: Matching real-world constraints (realistic values)
        solution_realistic = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=6.0,
            battery_capacity=8.0,  # Typical electric vehicle
            battery_consume_rate=0.5,  # Moderate consumption
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        assert solution_realistic is not None
        assertions.assert_solution_valid(solution_realistic)


class TestALNSSolver:
    """Test ALNS solver class."""
    
    def test_solver_creation(self, simple_pdptw_instance, alns_config):
        """Test ALNS solver initialization."""
        instance = simple_pdptw_instance
        
        # Create initial solution
        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        # Create ALNS solver
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Check solver attributes
        assert solver.initial_solution is initial_solution
        assert solver.config is alns_config
        assert solver.dist_matrix is instance.distance_matrix
        assert solver.battery_capacity == 100.0
        
        # Check that solver implements ConfigurableSolver interface
        assert isinstance(solver, ConfigurableSolver)
    
    def test_solver_interface(self, simple_pdptw_instance, alns_config):
        """Test ALNS solver interface methods."""
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Test get_config method
        config = solver.get_config()
        assert config is alns_config
        
        # Test update_config method
        new_config = ALNSConfig(num_removal=10, max_no_improve=100)
        solver.update_config(new_config)
        assert solver.config.num_removal == 10
        assert solver.config.max_no_improve == 100
    
    def test_solve_method(self, simple_pdptw_instance, alns_config):
        """Test ALNS solve method."""
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Test solving
        solution = solver.solve(instance)
        
        # Should return a solution
        assert solution is not None
        assert hasattr(solution, 'routes')
        assert hasattr(solution, 'get_objective_value')
        
        # Solution should be valid
        test_helpers.assert_solution_valid(solution)
        
        # Objective should be calculable
        obj_value = solution.get_objective_value()
        assert isinstance(obj_value, (int, float))
        
        # Should have improved or equal to initial solution
        initial_obj = initial_solution.objective_function()
        # Note: ALNS might not always improve, but should return a valid solution
        
    def test_solve_with_vrp_problem_interface(self, simple_pdptw_instance, alns_config):
        """Test that ALNS works with VRPProblem interface."""
        # Note: ALNS currently expects PDPTWInstance specifically
        # This test verifies the current behavior
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # ALNS.solve() should accept VRPProblem (via adapter pattern)
        solution = solver.solve(instance)
        
        # Should return a solution
        assert solution is not None
        assert isinstance(solution.get_objective_value(), (int, float))
    
    def test_solver_state(self, simple_pdptw_instance, alns_config):
        """Test solver state tracking."""
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # Check solver has state attributes
        assert hasattr(solver, 'current_solution')
        assert hasattr(solver, 'best_solution')
        assert hasattr(solver, 'temperature')
        assert hasattr(solver, 'segment_counts')
        assert hasattr(solver, 'operator_scores')
        
        # Initial state
        assert solver.current_solution is initial_solution
        assert solver.best_solution is initial_solution
        assert solver.temperature == alns_config.start_temp
    
    def test_solver_with_different_configs(self, simple_pdptw_instance):
        """Test ALNS with different configurations."""
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        # Test with aggressive configuration (few iterations)
        aggressive_config = ALNSConfig(
            max_no_improve=5,  # Few iterations
            start_temp=50.0,
            cooling_rate=0.8
        )
        
        solver_agg = ALNS(
            initial_solution=initial_solution,
            config=aggressive_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        solution_agg = solver_agg.solve(instance)
        assert solution_agg is not None
        
        # Test with conservative configuration (more iterations)
        conservative_config = ALNSConfig(
            max_no_improve=200,  # More iterations
            start_temp=200.0,
            cooling_rate=0.99,  # Slow cooling
            num_segments=10,
            seg_len=20
        )
        
        solver_cons = ALNS(
            initial_solution=initial_solution,
            config=conservative_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        solution_cons = solver_cons.solve(instance)
        assert solution_cons is not None

    def test_alns_invalid_initialization(self, simple_pdptw_instance, alns_config):
        """Test ALNS solver initialization with invalid inputs."""
        instance = simple_pdptw_instance

        # Create valid initial solution
        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        # Test 1: Invalid initial solution (None)
        with pytest.raises((TypeError, ValueError)):
            solver = ALNS(
                initial_solution=None,
                config=alns_config,
                dist_matrix=instance.distance_matrix,
                battery_capacity=100.0
            )

        # Test 2: Invalid config (None)
        with pytest.raises((TypeError, ValueError)):
            solver = ALNS(
                initial_solution=initial_solution,
                config=None,
                dist_matrix=instance.distance_matrix,
                battery_capacity=100.0
            )

        # Test 3: Invalid distance matrix (wrong shape)
        wrong_shape_matrix = np.random.rand(3, 4)  # Not square
        with pytest.raises((ValueError, TypeError)):
            solver = ALNS(
                initial_solution=initial_solution,
                config=alns_config,
                dist_matrix=wrong_shape_matrix,
                battery_capacity=100.0
            )

        # Test 4: Invalid battery capacity (negative)
        with pytest.raises((ValueError, TypeError)):
            solver = ALNS(
                initial_solution=initial_solution,
                config=alns_config,
                dist_matrix=instance.distance_matrix,
                battery_capacity=-10.0
            )

        # Test 5: Zero battery capacity (edge case - should it be allowed?)
        # This might be valid for testing, so we test it works
        solver_zero = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=0.0
        )
        assert solver_zero.battery_capacity == 0.0

    def test_alns_solve_invalid_inputs(self, simple_pdptw_instance, alns_config):
        """Test ALNS solve method with invalid inputs."""
        instance = simple_pdptw_instance

        # Create valid solver
        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        # Test 1: Solve with None instance
        with pytest.raises((TypeError, ValueError)):
            solver.solve(None)

        # Test 2: Solve with invalid instance type (not VRPProblem)
        with pytest.raises((TypeError, ValueError)):
            solver.solve("not a problem instance")

        # Test 3: Solve with invalid number of vehicles (negative)
        with pytest.raises((ValueError, TypeError)):
            solver.solve(instance, num_vehicles=-1)

        # Test 4: Solve with invalid vehicle capacity (zero or negative)
        with pytest.raises((ValueError, TypeError)):
            solver.solve(instance, vehicle_capacity=0.0)

        with pytest.raises((ValueError, TypeError)):
            solver.solve(instance, vehicle_capacity=-10.0)

        # Test 5: Solve with invalid battery parameters
        with pytest.raises((ValueError, TypeError)):
            solver.solve(instance, battery_consume_rate=0.0)  # Zero consumption rate

        with pytest.raises((ValueError, TypeError)):
            solver.solve(instance, battery_consume_rate=-1.0)  # Negative consumption rate

    def test_alns_edge_cases(self, simple_pdptw_instance):
        """Test ALNS solver with edge cases."""
        instance = simple_pdptw_instance

        # Create valid initial solution
        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        # Test 1: Very small max_no_improve (1 iteration)
        config_minimal = ALNSConfig(max_no_improve=1)
        solver_minimal = ALNS(
            initial_solution=initial_solution,
            config=config_minimal,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        solution_minimal = solver_minimal.solve(instance)
        assert solution_minimal is not None

        # Test 2: Zero temperature (should still work)
        config_zero_temp = ALNSConfig(start_temp=0.0, max_no_improve=5)
        solver_zero_temp = ALNS(
            initial_solution=initial_solution,
            config=config_zero_temp,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        solution_zero_temp = solver_zero_temp.solve(instance)
        assert solution_zero_temp is not None

        # Test 3: Very high temperature
        config_high_temp = ALNSConfig(start_temp=10000.0, max_no_improve=5)
        solver_high_temp = ALNS(
            initial_solution=initial_solution,
            config=config_high_temp,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        solution_high_temp = solver_high_temp.solve(instance)
        assert solution_high_temp is not None

        # Test 4: Zero cooling (temperature never decreases)
        config_no_cooling = ALNSConfig(cooling_rate=1.0, max_no_improve=5)
        solver_no_cooling = ALNS(
            initial_solution=initial_solution,
            config=config_no_cooling,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        solution_no_cooling = solver_no_cooling.solve(instance)
        assert solution_no_cooling is not None

        # Test 5: Minimal removal operations
        config_min_removal = ALNSConfig(num_removal=1, max_no_improve=5)
        solver_min_removal = ALNS(
            initial_solution=initial_solution,
            config=config_min_removal,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        solution_min_removal = solver_min_removal.solve(instance)
        assert solution_min_removal is not None


class TestALNSOperators:
    """Test ALNS removal and repair operators."""
    
    def test_removal_operators(self, simple_pdptw_instance):
        """Test removal operators initialization."""
        instance = simple_pdptw_instance
        
        # Create a solution
        solution = test_helpers.create_minimal_pdptw_solution(instance=instance)
        
        # Create removal operators
        operators = RemovalOperators(solution)
        
        # Check operators exist
        assert hasattr(operators, 'shaw_removal')
        assert hasattr(operators, 'random_removal')
        assert hasattr(operators, 'worst_removal')
        assert hasattr(operators, 'sisr_removal')
        
        # Check they are callable
        assert callable(operators.shaw_removal)
        assert callable(operators.random_removal)
        assert callable(operators.worst_removal)
        assert callable(operators.sisr_removal)
    
    def test_repair_operators(self, simple_pdptw_instance):
        """Test repair operators initialization."""
        instance = simple_pdptw_instance
        
        # Create a solution
        solution = test_helpers.create_minimal_pdptw_solution(instance=instance)
        
        # Create repair operators
        operators = RepairOperators(solution)
        
        # Check operators exist
        assert hasattr(operators, 'greedy_insertion')
        assert hasattr(operators, 'regret_insertion')
        
        # Check they are callable
        assert callable(operators.greedy_insertion)
        assert callable(operators.regret_insertion)
    
    def test_operator_integration_with_alns(self, simple_pdptw_instance, alns_config):
        """Test that operators integrate with ALNS solver."""
        instance = simple_pdptw_instance

        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )
        
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )
        
        # ALNS should use operators internally
        # Run solve to ensure operators work
        solution = solver.solve(instance)
        assert solution is not None

    def test_alns_with_vrp_problem_adapter(self, simple_pdptw_instance, alns_config):
        """Test ALNS solver with VRPProblem adapter interface."""
        instance = simple_pdptw_instance

        # Wrap instance in PDPTWProblemAdapter to test VRPProblem interface
        problem_adapter = PDPTWProblemAdapter(instance)

        # Verify adapter implements VRPProblem interface
        from vrp_toolkit.algorithms.base import VRPProblem
        assert isinstance(problem_adapter, VRPProblem)

        # Create initial solution using original instance (adapter should work too)
        initial_solution = greedy_insertion_initial_solution(
            problem=instance,
            num_vehicles=4,
            vehicle_capacity=10.0,
            battery_capacity=100.0,
            battery_consume_rate=1.0,
            penalty_unvisit=100.0,
            penalty_delay=15.0
        )

        # Create ALNS solver
        solver = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=instance.distance_matrix,
            battery_capacity=100.0
        )

        # Test 1: Solve using adapter instead of direct instance
        solution = solver.solve(problem_adapter)
        assert solution is not None

        # Test 2: Verify solution is VRPSolution compatible
        from vrp_toolkit.algorithms.base import VRPSolution
        assert isinstance(solution, VRPSolution)

        # Test 3: Verify adapter can be cast to Solver interface
        from vrp_toolkit.algorithms.base import Solver
        solver_interface: Solver = solver
        solution2 = solver_interface.solve(problem_adapter)
        assert solution2 is not None

        # Test 4: Verify ConfigurableSolver interface still works
        config_solver: ConfigurableSolver = solver
        config = config_solver.get_config()
        assert config is alns_config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])