"""Tests for VRP base interfaces (VRPProblem, VRPSolution, Solver)."""

import pytest
import numpy as np
from abc import ABC
from typing import List, Tuple

from vrp_toolkit.algorithms.base import (
    VRPProblem, 
    VRPSolution, 
    Solver,
    ConfigurableSolver
)
from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from tests.utils import test_helpers


class TestVRPProblemInterface:
    """Test VRPProblem abstract base class interface."""
    
    def test_abstract_methods(self):
        """Test that VRPProblem defines required abstract methods."""
        # Check abstract methods exist
        assert hasattr(VRPProblem, 'get_distance')
        assert hasattr(VRPProblem, 'get_time')
        assert hasattr(VRPProblem, 'get_num_nodes')
        assert hasattr(VRPProblem, 'get_num_vehicles')
        assert hasattr(VRPProblem, 'get_distance_matrix')
        assert hasattr(VRPProblem, 'get_time_windows')
        assert hasattr(VRPProblem, 'get_demands')
        assert hasattr(VRPProblem, 'get_service_times')
        
        # Check they are abstract
        assert getattr(VRPProblem.get_distance, '__isabstractmethod__', False)
        assert getattr(VRPProblem.get_time, '__isabstractmethod__', False)
        assert getattr(VRPProblem.get_num_nodes, '__isabstractmethod__', False)
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that VRPProblem cannot be instantiated directly."""
        with pytest.raises(TypeError):
            problem = VRPProblem()  # Should fail - abstract class
    
    def test_pdptw_instance_implements_interface(self, simple_pdptw_instance):
        """Test that PDPTWInstance implements VRPProblem interface."""
        instance = simple_pdptw_instance
        
        # Check instance is a VRPProblem
        assert isinstance(instance, VRPProblem)
        
        # Test all abstract methods
        n_nodes = instance.get_num_nodes()
        assert n_nodes == 5
        
        n_vehicles = instance.get_num_vehicles()
        assert isinstance(n_vehicles, int)
        
        # Test distance methods
        dist_matrix = instance.get_distance_matrix()
        assert dist_matrix.shape == (n_nodes, n_nodes)
        
        # Test get_distance for specific nodes
        for i in range(n_nodes):
            for j in range(n_nodes):
                distance = instance.get_distance(i, j)
                assert isinstance(distance, (int, float))
                assert distance >= 0
                # Should match matrix value
                assert distance == dist_matrix[i, j]
        
        # Test get_time for specific nodes
        time_matrix = instance.get_time_matrix()
        for i in range(n_nodes):
            for j in range(n_nodes):
                travel_time = instance.get_time(i, j)
                assert isinstance(travel_time, (int, float))
                assert travel_time >= 0
                # Should match matrix value
                assert travel_time == time_matrix[i, j]
        
        # Test other methods
        time_windows = instance.get_time_windows()
        assert len(time_windows) == n_nodes
        for start, end in time_windows:
            assert isinstance(start, (int, float))
            assert isinstance(end, (int, float))
            assert start <= end
        
        demands = instance.get_demands()
        assert len(demands) == n_nodes
        
        service_times = instance.get_service_times()
        assert len(service_times) == n_nodes


class TestVRPSolutionInterface:
    """Test VRPSolution abstract base class interface."""
    
    def test_abstract_methods(self):
        """Test that VRPSolution defines required abstract methods."""
        # Check abstract methods exist
        assert hasattr(VRPSolution, 'get_routes')
        assert hasattr(VRPSolution, 'get_objective_value')
        assert hasattr(VRPSolution, 'is_feasible')
        
        # Check they are abstract
        assert getattr(VRPSolution.get_routes, '__isabstractmethod__', False)
        assert getattr(VRPSolution.get_objective_value, '__isabstractmethod__', False)
        assert getattr(VRPSolution.is_feasible, '__isabstractmethod__', False)
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that VRPSolution cannot be instantiated directly."""
        with pytest.raises(TypeError):
            solution = VRPSolution()  # Should fail - abstract class
    
    def test_pdptw_solution_implements_interface(self, simple_pdptw_solution):
        """Test that PDPTWSolution implements VRPSolution interface."""
        solution = simple_pdptw_solution
        
        # Check solution is a VRPSolution
        assert isinstance(solution, VRPSolution)
        
        # Test all abstract methods
        routes = solution.get_routes()
        assert isinstance(routes, list)
        assert len(routes) > 0
        for route in routes:
            assert isinstance(route, list)
            assert len(route) >= 2
        
        obj_value = solution.get_objective_value()
        assert isinstance(obj_value, (int, float))
        
        feasible = solution.is_feasible()
        assert isinstance(feasible, bool)


class TestSolverInterface:
    """Test Solver abstract base class interface."""
    
    def test_abstract_methods(self):
        """Test that Solver defines required abstract methods."""
        # Check abstract methods exist
        assert hasattr(Solver, 'solve')
        
        # Check it is abstract
        assert getattr(Solver.solve, '__isabstractmethod__', False)
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that Solver cannot be instantiated directly."""
        with pytest.raises(TypeError):
            solver = Solver()  # Should fail - abstract class


class TestConfigurableSolverInterface:
    """Test ConfigurableSolver abstract base class interface."""
    
    def test_abstract_methods(self):
        """Test that ConfigurableSolver defines required abstract methods."""
        # Check abstract methods exist
        assert hasattr(ConfigurableSolver, 'solve')
        assert hasattr(ConfigurableSolver, 'get_config')
        assert hasattr(ConfigurableSolver, 'update_config')
        
        # Check they are abstract
        assert getattr(ConfigurableSolver.solve, '__isabstractmethod__', False)
        assert getattr(ConfigurableSolver.get_config, '__isabstractmethod__', False)
        assert getattr(ConfigurableSolver.update_config, '__isabstractmethod__', False)
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that ConfigurableSolver cannot be instantiated directly."""
        with pytest.raises(TypeError):
            solver = ConfigurableSolver()  # Should fail - abstract class


class TestInterfaceCompatibility:
    """Test compatibility between interfaces."""
    
    def test_problem_solution_compatibility(self, simple_pdptw_instance, simple_pdptw_solution):
        """Test that problem and solution interfaces are compatible."""
        problem = simple_pdptw_instance
        solution = simple_pdptw_solution
        
        # Both should implement their respective interfaces
        assert isinstance(problem, VRPProblem)
        assert isinstance(solution, VRPSolution)
        
        # Solution should reference the problem
        assert solution.instance is problem
        
        # Problem dimensions should match solution assumptions
        n_nodes = problem.get_num_nodes()
        routes = solution.get_routes()
        
        # Check all nodes in routes are valid
        for route in routes:
            for node in route:
                assert 0 <= node < n_nodes
    
    def test_adapter_pattern_compatibility(self):
        """Test that adapter pattern works with interfaces."""
        # Create a simple PDPTW instance
        instance = test_helpers.create_minimal_pdptw_instance(n_orders=2)
        
        # Create a solution
        solution = test_helpers.create_minimal_pdptw_solution(instance=instance)
        
        # Both should work through their interfaces
        problem_interface: VRPProblem = instance
        solution_interface: VRPSolution = solution
        
        # Can call interface methods
        n_nodes = problem_interface.get_num_nodes()
        routes = solution_interface.get_routes()
        obj_value = solution_interface.get_objective_value()
        feasible = solution_interface.is_feasible()
        
        # All should work without errors
        assert n_nodes > 0
        assert len(routes) > 0
        assert isinstance(obj_value, (int, float))
        assert isinstance(feasible, bool)


class TestCustomProblemImplementation:
    """Test creating custom VRPProblem implementations."""
    
    class SimpleVRPProblem(VRPProblem):
        """Simple implementation of VRPProblem for testing."""
        
        def __init__(self, n_nodes: int = 5):
            self._n_nodes = n_nodes
            self._distance_matrix = np.random.rand(n_nodes, n_nodes) * 10
            np.fill_diagonal(self._distance_matrix, 0)
            self._time_matrix = self._distance_matrix / 2.0
            self._time_windows = [(0, 100) for _ in range(n_nodes)]
            self._demands = [0.0] + [1.0] * (n_nodes - 1)
            self._service_times = [0.0] + [5.0] * (n_nodes - 1)
            self._n_vehicles = 3
        
        def get_distance(self, i: int, j: int) -> float:
            return self._distance_matrix[i, j]
        
        def get_time(self, i: int, j: int) -> float:
            return self._time_matrix[i, j]
        
        def get_num_nodes(self) -> int:
            return self._n_nodes
        
        def get_num_vehicles(self) -> int:
            return self._n_vehicles
        
        def get_distance_matrix(self) -> np.ndarray:
            return self._distance_matrix
        
        def get_time_windows(self) -> List[Tuple[float, float]]:
            return self._time_windows
        
        def get_demands(self) -> List[float]:
            return self._demands
        
        def get_service_times(self) -> List[float]:
            return self._service_times
    
    def test_custom_problem_implementation(self):
        """Test that custom VRPProblem implementation works."""
        problem = self.SimpleVRPProblem(n_nodes=5)
        
        # Should be instantiable
        assert isinstance(problem, VRPProblem)
        
        # Should implement all abstract methods
        n_nodes = problem.get_num_nodes()
        assert n_nodes == 5
        
        n_vehicles = problem.get_num_vehicles()
        assert n_vehicles == 3
        
        dist_matrix = problem.get_distance_matrix()
        assert dist_matrix.shape == (5, 5)
        
        # Test distance and time methods
        for i in range(n_nodes):
            for j in range(n_nodes):
                distance = problem.get_distance(i, j)
                assert distance == dist_matrix[i, j]
                
                time = problem.get_time(i, j)
                assert time == problem._time_matrix[i, j]
        
        # Test other methods
        time_windows = problem.get_time_windows()
        assert len(time_windows) == n_nodes
        
        demands = problem.get_demands()
        assert len(demands) == n_nodes
        
        service_times = problem.get_service_times()
        assert len(service_times) == n_nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])