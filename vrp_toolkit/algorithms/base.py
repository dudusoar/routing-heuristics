"""Base classes for VRP solving algorithms.

This module defines abstract base classes for VRP solvers, problems, and solutions
to enable a clean separation between problem definition and algorithm implementation.

Key concepts:
1. Solver: Algorithm that solves a VRP problem instance
2. Problem: VRP problem instance with data and constraints
3. Solution: Candidate solution to a VRP problem

Design principle: Solvers should work with any VRP problem that implements the
Problem interface, and produce solutions that implement the Solution interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class VRPProblem(ABC):
    """Abstract base class for VRP problem instances.

    This class defines the minimal interface that a VRP problem must implement
    to be solvable by generic VRP algorithms.
    """

    @abstractmethod
    def get_distance(self, i: int, j: int) -> float:
        """Get distance between nodes i and j.

        Args:
            i: Source node index
            j: Destination node index

        Returns:
            Distance between nodes i and j
        """
        pass

    @abstractmethod
    def get_time(self, i: int, j: int) -> float:
        """Get travel time between nodes i and j.

        Args:
            i: Source node index
            j: Destination node index

        Returns:
            Travel time between nodes i and j
        """
        pass

    @abstractmethod
    def get_demand(self, node_id: int) -> float:
        """Get demand for a node.

        Args:
            node_id: Node index

        Returns:
            Demand at node (positive for pickup, negative for delivery, 0 for depot)
        """
        pass

    @abstractmethod
    def get_time_window(self, node_id: int) -> Tuple[float, float]:
        """Get time window for a node.

        Args:
            node_id: Node index

        Returns:
            Tuple of (start_time, end_time) for the node's time window
        """
        pass

    @abstractmethod
    def get_service_time(self, node_id: int) -> float:
        """Get service time for a node.

        Args:
            node_id: Node index

        Returns:
            Service time required at node
        """
        pass

    @property
    @abstractmethod
    def num_nodes(self) -> int:
        """Number of nodes in the problem."""
        pass

    @property
    @abstractmethod
    def num_orders(self) -> int:
        """Number of orders/requests in the problem."""
        pass

    @property
    @abstractmethod
    def depot_index(self) -> int:
        """Index of the depot node."""
        pass

    # Optional bulk matrix access methods for algorithm efficiency
    def get_distance_matrix(self) -> Optional[np.ndarray]:
        """Get full distance matrix if available.

        Returns:
            Distance matrix as numpy array, or None if not available
        """
        return None

    def get_time_matrix(self) -> Optional[np.ndarray]:
        """Get full time matrix if available.

        Returns:
            Time matrix as numpy array, or None if not available
        """
        return None


class VRPSolution(ABC):
    """Abstract base class for VRP solutions.

    This class defines the minimal interface that a VRP solution must implement
    to be evaluated and manipulated by generic VRP algorithms.
    """

    @abstractmethod
    def objective_value(self) -> float:
        """Calculate objective function value.

        Returns:
            Objective function value (lower is better)
        """
        pass

    @abstractmethod
    def is_feasible(self) -> bool:
        """Check solution feasibility.

        Returns:
            True if solution satisfies all constraints, False otherwise
        """
        pass

    @property
    @abstractmethod
    def routes(self) -> List[List[int]]:
        """List of vehicle routes.

        Returns:
            List where each element is a list of node indices representing a vehicle route
        """
        pass

    @routes.setter
    @abstractmethod
    def routes(self, value: List[List[int]]) -> None:
        """Set vehicle routes.

        Args:
            value: New routes to set
        """
        pass

    @property
    @abstractmethod
    def problem(self) -> VRPProblem:
        """Problem instance this solution belongs to.

        Returns:
            VRPProblem instance
        """
        pass

    def update(self) -> None:
        """Update internal state after route changes.

        This method should be called after routes are modified to ensure
        consistency of derived attributes (arrival times, battery levels, etc.).
        """
        pass


class Solver(ABC):
    """Abstract base class for VRP solvers.

    This class defines the interface that all VRP solving algorithms should implement.
    """

    @abstractmethod
    def solve(self, problem: VRPProblem, **kwargs) -> VRPSolution:
        """Solve a VRP problem instance.

        Args:
            problem: VRP problem instance to solve
            **kwargs: Algorithm-specific parameters

        Returns:
            Best solution found
        """
        pass

    @abstractmethod
    def get_solution_history(self) -> List[Tuple[VRPSolution, float]]:
        """Get history of solutions explored during search.

        Returns:
            List of (solution, objective_value) pairs representing the search history
        """
        pass


class ConfigurableSolver(Solver):
    """Base class for solvers with configuration management.

    This class extends Solver with configuration management capabilities.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize solver with configuration.

        Args:
            config: Dictionary of configuration parameters
        """
        self.config = config or {}

    def configure(self, **kwargs) -> None:
        """Update solver configuration.

        Args:
            **kwargs: Configuration parameters to update
        """
        self.config.update(kwargs)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration.

        Returns:
            Copy of current configuration dictionary
        """
        return self.config.copy()


# Type checking imports (for forward references)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution


# Concrete implementations for backward compatibility
class PDPTWProblemAdapter(VRPProblem):
    """Adapter for PDPTWInstance to implement VRPProblem interface."""

    def __init__(self, pdptw_instance: 'PDPTWInstance'):
        """Initialize adapter.

        Args:
            pdptw_instance: PDPTWInstance to adapt
        """
        self._instance = pdptw_instance

    def get_distance(self, i: int, j: int) -> float:
        return self._instance.get_distance(i, j)

    def get_time(self, i: int, j: int) -> float:
        return self._instance.get_time(i, j)

    def get_demand(self, node_id: int) -> float:
        return self._instance.get_demand(node_id)

    def get_time_window(self, node_id: int) -> Tuple[float, float]:
        return self._instance.get_time_window(node_id)

    def get_service_time(self, node_id: int) -> float:
        return self._instance.get_service_time(node_id)

    @property
    def num_nodes(self) -> int:
        return self._instance.num_nodes

    @property
    def num_orders(self) -> int:
        return self._instance.num_orders

    @property
    def depot_index(self) -> int:
        return self._instance.depot_index

    # Bulk matrix access methods
    def get_distance_matrix(self) -> Optional[np.ndarray]:
        """Get full distance matrix if available."""
        if hasattr(self._instance, 'get_distance_matrix'):
            return self._instance.get_distance_matrix()
        return None

    def get_time_matrix(self) -> Optional[np.ndarray]:
        """Get full time matrix if available."""
        if hasattr(self._instance, 'get_time_matrix'):
            return self._instance.get_time_matrix()
        return None

    @property
    def original_instance(self) -> 'PDPTWInstance':
        """Get the original PDPTWInstance for advanced operations."""
        return self._instance


class PDPTWSolutionAdapter(VRPSolution):
    """Adapter for PDPTWSolution to implement VRPSolution interface."""

    def __init__(self, pdptw_solution: 'PDPTWSolution'):
        """Initialize adapter.

        Args:
            pdptw_solution: PDPTWSolution to adapt
        """
        self._solution = pdptw_solution

    def objective_value(self) -> float:
        return self._solution.objective_function()

    def objective_function(self) -> float:
        """Backward compatibility alias for objective_value."""
        return self._solution.objective_function()

    def get_objective_value(self) -> float:
        """Get objective value (alias for objective_value)."""
        return self.objective_value()

    def is_feasible(self) -> bool:
        return self._solution.is_feasible()

    @property
    def routes(self) -> List[List[int]]:
        return self._solution.routes

    @routes.setter
    def routes(self, value: List[List[int]]) -> None:
        self._solution.routes = value
        self._solution.update_all()

    @property
    def problem(self) -> VRPProblem:
        return PDPTWProblemAdapter(self._solution.instance)

    @property
    def instance(self) -> 'PDPTWInstance':
        """Get the underlying PDPTWInstance for backward compatibility."""
        return self._solution.instance

    def update(self) -> None:
        self._solution.update_all()

    @property
    def original_solution(self) -> 'PDPTWSolution':
        """Get the original PDPTWSolution for advanced operations."""
        return self._solution

    @property
    def visited_requests(self) -> List[int]:
        """Get list of visited pickup nodes (requests)."""
        return self._solution.visited_requests

    @property
    def unvisited_requests(self) -> List[int]:
        """Get list of unvisited pickup nodes (requests)."""
        return self._solution.unvisited_requests

    @property
    def unvisited_pairs(self) -> List[Tuple[int, int]]:
        """Get list of unvisited (pickup, delivery) pairs."""
        return self._solution.unvisited_pairs

    @property
    def route_arrival_times(self) -> List[List[float]]:
        """Get arrival times for each route."""
        return self._solution.route_arrival_times

    @property
    def battery_capacity(self) -> float:
        """Get battery capacity."""
        return self._solution.battery_capacity

    @battery_capacity.setter
    def battery_capacity(self, value: float) -> None:
        """Set battery capacity."""
        self._solution.battery_capacity = value

    def update_all(self) -> None:
        """Update all solution attributes."""
        self._solution.update_all()