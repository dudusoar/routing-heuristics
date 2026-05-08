"""ALNS (Adaptive Large Neighborhood Search) solver for PDPTW problems.

This module implements the ALNS algorithm for solving PDPTW problems with
battery constraints, including charging station insertion.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Any
import random
import numpy as np
from copy import deepcopy
from collections import defaultdict
import time

# Local imports
from .operators import RemovalOperators, RepairOperators
from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from vrp_toolkit.algorithms.base import ConfigurableSolver, PDPTWProblemAdapter, PDPTWSolutionAdapter, VRPProblem, VRPSolution


@dataclass
class ALNSConfig:
    """Configuration parameters for ALNS algorithm."""
    
    # Operator parameters
    num_removal: int = 5
    p: float = 4.0  # Shaw removal parameter
    k: int = 3  # Regret insertion parameter
    L_max: int = 5  # SISR removal max string length
    avg_remove_order: float = 2.0  # SISR average remove order
    d_matrix: Optional[np.ndarray] = None  # Distance matrix for SISR
    
    # ALNS parameters
    max_no_improve: int = 100
    segment_length: int = 100
    num_segments: int = 10
    r: float = 0.1  # Weight update rate
    sigma: Tuple[float, float, float] = (33.0, 9.0, 13.0)  # Reward scores
    
    # Simulated annealing parameters
    start_temp: float = 10000.0
    cooling_rate: float = 0.99
    
    # Convergence criteria
    cost_ci_obj_diff_threshold: float = 0.1  # Convergence threshold
    cost_ci_window_size: int = 25  # Window size for best cost list
    
    # Operator indices (configurable)
    removal_indices: List[int] = None  # Default: [0, 2, 3] (Shaw, Worst, SISR)
    repair_indices: List[int] = None   # Default: [0, 1] (Greedy, Regret)
    
    # Charging station parameters
    charging_station_index: Optional[int] = None  # If None, assumes last index

    # Reproducibility
    seed: Optional[int] = None  # Random seed for reproducibility

    def __post_init__(self):
        """Set default values for lists and handle parameter aliases."""
        # Handle seg_len alias (backward compatibility)
        if hasattr(self, 'seg_len'):
            self.segment_length = self.seg_len
            delattr(self, 'seg_len')

        if self.removal_indices is None:
            self.removal_indices = [0, 2, 3]  # Shaw, Worst, SISR
        if self.repair_indices is None:
            self.repair_indices = [0, 1]  # Greedy, Regret

    def __init__(self, **kwargs):
        """Initialize with support for parameter aliases.

        Supports seg_len as alias for segment_length for backward compatibility.
        """
        # Handle seg_len alias before dataclass initialization
        if 'seg_len' in kwargs:
            kwargs['segment_length'] = kwargs.pop('seg_len')

        # Set default values for all fields
        for field_name in ['num_removal', 'p', 'k', 'L_max', 'avg_remove_order', 'd_matrix',
                           'max_no_improve', 'segment_length', 'num_segments', 'r', 'sigma',
                           'start_temp', 'cooling_rate', 'cost_ci_obj_diff_threshold',
                           'cost_ci_window_size', 'removal_indices', 'repair_indices',
                           'charging_station_index', 'seed']:
            # Get default from class definition
            if field_name in kwargs:
                setattr(self, field_name, kwargs[field_name])
            else:
                # Use default value from class
                import dataclasses
                field = next((f for f in dataclasses.fields(self.__class__) if f.name == field_name), None)
                if field and field.default is not dataclasses.MISSING:
                    setattr(self, field_name, field.default)
                elif field and field.default_factory is not dataclasses.MISSING:
                    setattr(self, field_name, field.default_factory())

        # Call post_init
        self.__post_init__()


def _extract_pdptw_instance_from_problem(problem: VRPProblem) -> PDPTWInstance:
    """Extract PDPTWInstance from VRPProblem (helper function).
    
    Args:
        problem: VRPProblem to extract from
        
    Returns:
        PDPTWInstance
        
    Raises:
        TypeError: If problem cannot be converted to PDPTWInstance
    """
    # If it's already a PDPTWInstance, return it
    if isinstance(problem, PDPTWInstance):
        return problem
    
    # If it's a PDPTWProblemAdapter, return the original instance
    if isinstance(problem, PDPTWProblemAdapter):
        return problem.original_instance
    
    # Try to check if it has original_instance attribute
    if hasattr(problem, 'original_instance'):
        original = problem.original_instance
        if isinstance(original, PDPTWInstance):
            return original
    
    # If all else fails, raise error
    raise TypeError(
        f"Function requires a PDPTWInstance or PDPTWProblemAdapter, "
        f"got {type(problem).__name__}"
    )

def greedy_insertion_initial_solution(
    problem: VRPProblem,
    num_vehicles: int,
    vehicle_capacity: float,
    battery_capacity: float,
    battery_consume_rate: float,
    penalty_unvisit: float,
    penalty_delay: float
) -> VRPSolution:
    """Construct initial solution using greedy insertion.

    Args:
        problem: VRP problem instance (must be convertible to PDPTWInstance)
        num_vehicles: Number of available vehicles
        vehicle_capacity: Maximum capacity per vehicle
        battery_capacity: Maximum battery capacity
        battery_consume_rate: Battery consumption rate per distance unit
        penalty_unvisit: Penalty for unvisited nodes
        penalty_delay: Penalty for time window delays

    Returns:
        Initial feasible solution (adapter-wrapped)

    Raises:
        TypeError: If problem is None or not a valid VRP problem
        ValueError: If any numerical parameter is invalid
    """
    # Input validation
    if problem is None:
        raise TypeError("problem parameter cannot be None")

    if not isinstance(problem, (VRPProblem, PDPTWInstance)):
        raise TypeError(f"problem must be VRPProblem or PDPTWInstance, got {type(problem).__name__}")

    if battery_capacity < 0:
        raise ValueError(f"battery_capacity must be non-negative, got {battery_capacity}")

    if vehicle_capacity < 0:
        raise ValueError(f"vehicle_capacity must be non-negative, got {vehicle_capacity}")

    if battery_consume_rate < 0:
        raise ValueError(f"battery_consume_rate must be non-negative, got {battery_consume_rate}")

    if num_vehicles <= 0:
        raise ValueError(f"num_vehicles must be positive, got {num_vehicles}")

    # Extract PDPTW instance from VRPProblem
    pdptw_instance = _extract_pdptw_instance_from_problem(problem)
    
    routes = []
    # Get actual pickup nodes (type 'cp') from order table
    type_col = pdptw_instance._get_column('type')
    id_col = pdptw_instance._get_column('id')
    pickup_nodes = pdptw_instance.order_table[
        pdptw_instance.order_table[type_col] == pdptw_instance.NODE_TYPE_PICKUP
    ][id_col].tolist()
    pickup_nodes.sort(key=lambda x: pdptw_instance.time_windows[x][0])  # Sort by pickup start time

    for vehicle_id in range(num_vehicles):
        route = [0, 0]

        while pickup_nodes:
            best_pickup_node = None
            best_insertion_index = None
            best_objective_value = float('inf')

            for pickup_node in pickup_nodes:
                delivery_node = pickup_node + pdptw_instance.n
                for insertion_index in range(1, len(route)):
                    new_route = route[:insertion_index] + [pickup_node, delivery_node] + route[insertion_index:]
                    temp_solution = PDPTWSolution(
                        pdptw_instance, vehicle_capacity, battery_capacity, battery_consume_rate,
                        [new_route], penalty_unvisit, penalty_delay
                    )

                    if temp_solution.is_feasible():
                        objective_value = temp_solution.objective_function()
                        if objective_value < best_objective_value:
                            best_pickup_node = pickup_node
                            best_insertion_index = insertion_index
                            best_objective_value = objective_value

            if best_pickup_node is not None:
                pickup_nodes.remove(best_pickup_node)
                route = route[:best_insertion_index] + [best_pickup_node, best_pickup_node + pdptw_instance.n] + route[best_insertion_index:]
            else:
                break

        routes.append(route)

    solution = PDPTWSolution(
        pdptw_instance, vehicle_capacity, battery_capacity, battery_consume_rate,
        routes, penalty_unvisit, penalty_delay
    )

    # Return adapter-wrapped solution
    return PDPTWSolutionAdapter(solution)


class ALNS(ConfigurableSolver):
    """Core ALNS algorithm implementation.

    This class implements the Adaptive Large Neighborhood Search algorithm
    for PDPTW problems with battery constraints and charging station insertion.
    """
    
    def __init__(
        self,
        initial_solution: PDPTWSolution,
        config: ALNSConfig,
        dist_matrix: np.ndarray,
        battery_capacity: float
    ):
        """Initialize ALNS solver.

        Args:
            initial_solution: Starting solution for ALNS
            config: Algorithm configuration parameters
            dist_matrix: Distance matrix for charging insertion calculations
            battery_capacity: Battery capacity for charging constraint

        Raises:
            TypeError: If initial_solution or config is None
            ValueError: If battery_capacity is invalid
        """
        # Input validation
        if initial_solution is None:
            raise TypeError("initial_solution cannot be None")
        if config is None:
            raise TypeError("config cannot be None")
        if dist_matrix is None:
            raise TypeError("dist_matrix cannot be None")
        if not isinstance(dist_matrix, np.ndarray):
            raise TypeError(f"dist_matrix must be a numpy array, got {type(dist_matrix)}")
        if dist_matrix.ndim != 2 or dist_matrix.shape[0] != dist_matrix.shape[1]:
            raise ValueError(f"dist_matrix must be a square 2D array, got shape {dist_matrix.shape}")
        if battery_capacity is None or battery_capacity < 0:
            raise ValueError(f"battery_capacity must be non-negative, got {battery_capacity}")

        # Solution storage
        self.initial_solution = initial_solution  # Store reference to original for backward compatibility
        # Initially, current and best solutions are the initial solution (not copies)
        # Copies will be made during the run() method when needed
        self.current_solution = initial_solution
        self.best_solution = initial_solution
        self.charging_solution = deepcopy(initial_solution)

        # Adjust charging solution battery capacity
        robot_speed = self.current_solution.instance.robot_speed
        self.charging_solution.battery_capacity = battery_capacity * 2 / robot_speed * 60

        self.best_charging_solution = None
        self.best_charging_route = []

        # Store config for backward compatibility
        self.config = config

        # Solution history tracking (for Solver interface)
        self.solution_history = []

        # Operator parameters from config
        self.num_removal = config.num_removal
        self.p = config.p
        self.k = config.k
        self.L_max = config.L_max
        self.avg_remove_order = config.avg_remove_order
        self.d_matrix = config.d_matrix
        
        self.dist_matrix = dist_matrix
        self.battery_capacity = battery_capacity

        # ALNS parameters from config
        self.max_no_improve = config.max_no_improve
        self.segment_length = config.segment_length
        self.num_segments = config.num_segments
        self.r = config.r
        self.sigma1, self.sigma2, self.sigma3 = config.sigma

        # Simulated annealing parameters
        self.start_temp = config.start_temp
        self.cooling_rate = config.cooling_rate
        self.current_temp = config.start_temp

        # Convergence criteria
        self.cost_ci_obj_diff_threshold = config.cost_ci_obj_diff_threshold
        self.cost_ci_window_size = config.cost_ci_window_size
        
        # Charging station index
        self.charging_station_index = config.charging_station_index

        # Set random seed for reproducibility
        if config.seed is not None:
            np.random.seed(config.seed)
            random.seed(config.seed)
        if self.charging_station_index is None:
            self.charging_station_index = len(self.dist_matrix) - 1

        # ======== Initialization============
        # Operator indices
        self.removal_list = config.removal_indices
        self.repair_list = config.repair_indices

        # Weights initialization
        self.removal_weights = np.zeros((self.num_segments, len(self.removal_list)))
        self.repair_weights = np.zeros((self.num_segments, len(self.repair_list)))
        
        # Initial weights (equal distribution)
        self.removal_weights[0] = np.ones(len(self.removal_list)) / len(self.removal_list)
        self.repair_weights[0] = np.ones(len(self.repair_list)) / len(self.repair_list)

        # Scores
        self.removal_scores = np.zeros((self.num_segments, len(self.removal_list)))
        self.repair_scores = np.zeros((self.num_segments, len(self.repair_list)))

        # Theta: number of times each operator is used
        self.removal_theta = np.zeros((self.num_segments, len(self.removal_list)))
        self.repair_theta = np.zeros((self.num_segments, len(self.repair_list)))

    @property
    def segment_counts(self) -> Dict[str, np.ndarray]:
        """Get operator usage counts per segment.

        Returns:
            Dictionary with 'removal' and 'repair' operator counts
        """
        return {
            'removal': self.removal_theta,
            'repair': self.repair_theta
        }

    @property
    def operator_scores(self) -> Dict[str, np.ndarray]:
        """Get operator scores per segment.

        Returns:
            Dictionary with 'removal' and 'repair' operator scores
        """
        return {
            'removal': self.removal_scores,
            'repair': self.repair_scores
        }

    def select_operator(self, weights: np.ndarray) -> int:
        """Select operator using roulette wheel selection.
        
        Args:
            weights: Weight array for operators
            
        Returns:
            Index of selected operator
        """
        total_weight = np.sum(weights)
        probabilities = weights / total_weight
        cumulative_probabilities = np.cumsum(probabilities)
        random_number = random.random()
        for i, probability in enumerate(cumulative_probabilities):
            if random_number < probability:
                return i
        return len(weights) - 1  # select the last one

    def total_distance(self, route: List[int]) -> float:
        """Calculate total distance of a route.
        
        Args:
            route: List of node indices
            
        Returns:
            Total distance of the route
        """
        dist = 0.0
        for i in range(len(route) - 1):
            dist += self.dist_matrix[route[i]][route[i + 1]]
        return dist

    def run(self) -> Tuple[PDPTWSolution, PDPTWSolution]:
        """Run the ALNS algorithm.
        
        Returns:
            Tuple of (best_solution, best_charging_solution)
        """
        num_no_improve = 0
        segment = 0
        r = self.r
        start_time = time.time()
        best_obj_diff = 100.0
        best_obj_list = []
        insert_index = self.charging_station_index

        cost_ci_best = float('inf')  # recording cost after charging insertion
        cost_ci_obj_diff = 100.0
        cost_ci_best_list = []

        while segment < self.num_segments and cost_ci_obj_diff > self.cost_ci_obj_diff_threshold:
            # (time and information)
            segment_start_time = time.time()
            print(f"Segment {segment + 1} / {self.num_segments}")

            # ================================== A new segment begins ==================================
            # Update the weights for the current segment
            if segment > 0:
                for i in range(len(self.removal_list)):
                    self.removal_weights[segment][i] = (
                        self.removal_weights[segment - 1][i] * (1 - r)
                        + r * self.removal_scores[segment - 1][i] / max(1, self.removal_theta[segment - 1][i])
                    )
                for i in range(len(self.repair_list)):
                    self.repair_weights[segment][i] = (
                        self.repair_weights[segment - 1][i] * (1 - r)
                        + r * self.repair_scores[segment - 1][i] / max(1, self.repair_theta[segment - 1][i])
                    )

            for iteration in range(self.segment_length):
                # ================================== select the operators ==================================
                ## removal 
                removal_operators = RemovalOperators(self.current_solution)
                removal_idx = self.select_operator(self.removal_weights[segment])

                if removal_idx == 0:
                    removed_solution = removal_operators.shaw_removal(self.num_removal, self.p)
                elif removal_idx == 1:
                    removed_solution = removal_operators.random_removal(self.num_removal)
                elif removal_idx == 2:
                    removed_solution = removal_operators.worst_removal(self.num_removal)
                elif removal_idx == 3:
                    removed_solution = removal_operators.SISR_removal(self.L_max, self.avg_remove_order, self.d_matrix)

                removed_solution.update_all()
                unvisited_pairs = removed_solution.unvisited_pairs

                ## repair
                repair_operators = RepairOperators(removed_solution)
                repair_idx = self.select_operator(self.repair_weights[segment])
                if repair_idx == 0:
                    repair_solution = repair_operators.greedy_insertion(unvisited_pairs)
                elif repair_idx == 1:
                    repair_solution = repair_operators.regret_insertion(unvisited_pairs, self.k)

                # ================================== update the count ==================================
                self.removal_theta[segment][removal_idx] += 1
                self.repair_theta[segment][repair_idx] += 1

                # ================================== update the scores ==================================
                repair_solution.update_all()
                new_objective = repair_solution.objective_function()

                current_objective = self.current_solution.objective_function()
                best_objective = self.best_solution.objective_function()

                if new_objective < best_objective:  # sigma1
                    self.best_solution = deepcopy(repair_solution)
                    self.current_solution = deepcopy(repair_solution)
                    num_no_improve = 0
                    self.removal_scores[segment][removal_idx] += self.sigma1
                    self.repair_scores[segment][repair_idx] += self.sigma1
                elif new_objective < current_objective:  # sigma2
                    self.current_solution = deepcopy(repair_solution)
                    num_no_improve = 0
                    self.removal_scores[segment][removal_idx] += self.sigma2
                    self.repair_scores[segment][repair_idx] += self.sigma2
                else:  # sigma3
                    acceptance_probability = np.exp(-(new_objective - current_objective) / self.current_temp)
                    if random.random() < acceptance_probability:
                        self.current_solution = deepcopy(repair_solution)
                        self.removal_scores[segment][removal_idx] += self.sigma3
                        self.repair_scores[segment][repair_idx] += self.sigma3
                    num_no_improve += 1
    
                #================================== Add charging insertion ==================================
                if segment > 0:
                    z = 0 # number of routes which does not need charge
                    routes_charge = deepcopy(repair_solution.routes)
                    
                    for route_id, route_1 in enumerate(routes_charge):
                        
                        route_best = []
                        
                        if self.total_distance(route_1) <= self.battery_capacity:
                            z += 1
                            continue
                
                        c_best = float('inf')
                        
                        for i in range(2, len(route_1) - 1):
                            route_copy = route_1[:i] + [insert_index] + route_1[i:]

                            if self.total_distance(route_copy) > 2 * self.battery_capacity:
                                continue
                            else:
                                self.charging_solution.routes[route_id] = route_copy
                                self.charging_solution.update_all()
                                # update the best objective function
                                cr_best = self.charging_solution.objective_function()
                                if cr_best < c_best:
                                    second_index = route_copy.index(insert_index)
                                    subroute_1 = route_copy[:second_index + 1]
                                    subroute_2 = route_copy[second_index:]
                                    dist_1 = self.total_distance(subroute_1)
                                    dist_2 = self.total_distance(subroute_2)
                                    if (dist_1 <= self.battery_capacity) & (dist_2 <= self.battery_capacity):
                                        c_best = cr_best
                                        route_best = deepcopy(route_copy)
                                        routes_charge[route_id] = route_best
                        if len(route_best) > 0:
                            z += 1

                    if z == len(routes_charge):
                        self.charging_solution.routes = routes_charge
                        self.charging_solution.update_all()
                        cost_ci = self.charging_solution.objective_function()
                        if cost_ci < cost_ci_best:
                            cost_ci_best = cost_ci
                            self.best_charging_solution = deepcopy(self.charging_solution)
                    cost_ci_best_list.append(cost_ci_best)

                if len(cost_ci_best_list) >= self.cost_ci_window_size:
                    cost_ci_best_list = cost_ci_best_list[-self.cost_ci_window_size:]
                    cost_ci_obj_diff = np.mean(cost_ci_best_list) - cost_ci_best
                else:
                    cost_ci_obj_diff = 100.0

            print(f"Best objective: {best_objective}, Best charging cost: {cost_ci_best}, Diff: {cost_ci_obj_diff}")

            # (time spent on this segment)
            segment_end_time = time.time()
            segment_duration = segment_end_time - segment_start_time
            print(f"Segment {segment + 1} completed in {segment_duration:.2f} seconds")

            # update the segment, temperature
            segment += 1
            self.current_temp *= self.cooling_rate

            # === End of the segment

        # (time spend on the whole process)
        end_time = time.time()
        total_duration = end_time - start_time
        print(f"ALNS run completed in {total_duration:.2f} seconds")

        return self.best_solution, self.best_charging_solution

    def solve(self, problem: Optional[PDPTWInstance] = ..., **kwargs) -> PDPTWSolution:  # Use Ellipsis as sentinel
        """Solve the problem using ALNS (alias for run).

        Args:
            problem: Optional problem instance (for API compatibility, not used as solution is already initialized)
            **kwargs: Additional parameters (for validation only, not used)

        Returns:
            Best solution found

        Raises:
            TypeError: If problem is explicitly provided but not a valid type
            ValueError: If kwargs contain invalid parameter values
        """
        # Validate problem parameter - distinguish between not passed and passed as None
        if problem is not ...:  # If explicitly provided (even as None)
            if problem is None or not hasattr(problem, 'n'):
                # Problem provided but None or invalid type
                raise TypeError(f"problem must be a VRPProblem-like object, got {type(problem)}")

        # Validate additional parameters if provided
        if 'num_vehicles' in kwargs:
            if kwargs['num_vehicles'] is not None and kwargs['num_vehicles'] < 0:
                raise ValueError(f"num_vehicles must be non-negative, got {kwargs['num_vehicles']}")

        if 'vehicle_capacity' in kwargs:
            if kwargs['vehicle_capacity'] is not None and kwargs['vehicle_capacity'] <= 0:
                raise ValueError(f"vehicle_capacity must be positive, got {kwargs['vehicle_capacity']}")

        if 'battery_capacity' in kwargs:
            if kwargs['battery_capacity'] is not None and kwargs['battery_capacity'] < 0:
                raise ValueError(f"battery_capacity must be non-negative, got {kwargs['battery_capacity']}")

        if 'battery_consume_rate' in kwargs:
            if kwargs['battery_consume_rate'] is not None and kwargs['battery_consume_rate'] <= 0:
                raise ValueError(f"battery_consume_rate must be positive, got {kwargs['battery_consume_rate']}")

        # Run the algorithm
        best_sol, best_charging_sol = self.run()
        # Return the better of the two solutions
        if best_charging_sol is not None:
            if best_charging_sol.objective_function() < best_sol.objective_function():
                return best_charging_sol
        return best_sol

    @property
    def temperature(self) -> float:
        """Get current temperature (for simulated annealing)."""
        return self.current_temp

    def get_solution_history(self) -> List[Tuple[VRPSolution, float]]:
        """Get history of solutions explored during search.

        Returns:
            List of (solution, objective_value) pairs
        """
        return self.solution_history

    def get_config(self) -> ALNSConfig:
        """Get current configuration.

        Returns:
            Current configuration object
        """
        return self.config

    def update_config(self, config: ALNSConfig) -> None:
        """Update solver configuration.

        Args:
            config: New configuration object

        Note:
            This updates the stored config but does not re-initialize internal parameters.
            Some parameters may only take effect on the next solve() call.
        """
        self.config = config
        # Update key parameters that can be changed during execution
        self.num_removal = config.num_removal
        self.p = config.p
        self.k = config.k
        self.L_max = config.L_max
        self.avg_remove_order = config.avg_remove_order
        self.d_matrix = config.d_matrix
        self.max_no_improve = config.max_no_improve
        self.segment_length = config.segment_length
        self.num_segments = config.num_segments
        self.r = config.r
        self.sigma1, self.sigma2, self.sigma3 = config.sigma
        self.start_temp = config.start_temp
        self.cooling_rate = config.cooling_rate

    # ============================================= plot ==========================================================
    def plot_scores(self):
        """Plot operator scores over segments."""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        segments = range(self.removal_scores.shape[0])

        # removal scores
        for i in range(len(self.removal_list)):
            plt.plot(segments, self.removal_scores[:, i],
                     label=f'Shaw Removal' if i == 0 else (f'Random Removal' if i == 1 else 'Worst Removal'))

        # repair scores
        for i in range(len(self.repair_list)):
            plt.plot(segments, self.repair_scores[:, i], label=f'Greedy Insertion' if i == 0 else 'Regret Insertion')

        plt.xlabel('Segment')
        plt.ylabel('Scores')
        plt.title('Scores of Operators')
        plt.xticks(segments)
        plt.legend()
        plt.grid(True)
        plt.show()

    def plot_theta(self):
        """Plot operator usage counts over segments."""
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(12, 6))
        segments = range(self.removal_theta.shape[0])

        # removal theta
        for i in range(len(self.removal_list)):
            plt.plot(segments, self.removal_theta[:, i], label=f'Shaw Removal' if i == 0 else (
                f'Worst Removal' if i == 1 else f'SISR Removal' if i == 2 else 'SISR Removal'))

        # repair theta
        for i in range(len(self.repair_list)):
            plt.plot(segments, self.repair_theta[:, i], label=f'Greedy Insertion' if i == 0 else 'Regret Insertion')

        plt.xlabel('Segment')
        plt.ylabel('Theta (Usage Count)')
        plt.title('Usage Count of Operators')
        plt.xticks(segments)
        plt.legend()
        plt.grid(True)
        plt.show()


class ALNSSolver(ConfigurableSolver):
    """ALNS solver implementing the unified Solver interface.

    This class provides a clean interface for solving PDPTW problems using ALNS,
    following the problem-algorithm separation principle.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize ALNS solver with configuration.

        Args:
            config: Configuration dictionary for ALNS algorithm
        """
        super().__init__(config)
        self.alns_instance = None
        self.solution_history = []

    def _extract_pdptw_instance(self, problem: VRPProblem) -> PDPTWInstance:
        """Extract PDPTWInstance from VRPProblem.
        
        Args:
            problem: VRPProblem to extract from
            
        Returns:
            PDPTWInstance
            
        Raises:
            TypeError: If problem cannot be converted to PDPTWInstance
        """
        # If it's already a PDPTWInstance, return it
        if isinstance(problem, PDPTWInstance):
            return problem
        
        # If it's a PDPTWProblemAdapter, return the original instance
        if isinstance(problem, PDPTWProblemAdapter):
            return problem.original_instance
        
        # Try to check if it has original_instance attribute
        if hasattr(problem, 'original_instance'):
            original = problem.original_instance
            if isinstance(original, PDPTWInstance):
                return original
        
        # If all else fails, raise error
        raise TypeError(
            f"ALNSSolver requires a PDPTWInstance or PDPTWProblemAdapter, "
            f"got {type(problem).__name__}"
        )

    def solve(
        self,
        problem: VRPProblem,
        num_vehicles: int = 4,
        vehicle_capacity: float = 6.0,
        battery_capacity: float = 8.0,
        battery_consume_rate: float = 1.0,
        penalty_unvisited: float = 100.0,
        penalty_delayed: float = 15.0,
        **kwargs
    ) -> VRPSolution:        # Extract PDPTW instance from VRPProblem
        pdptw_instance = self._extract_pdptw_instance(problem)
        
        # Generate initial solution using greedy insertion
        initial_solution = greedy_insertion_initial_solution(
            problem=problem,
            num_vehicles=num_vehicles,
            vehicle_capacity=vehicle_capacity,
            battery_capacity=battery_capacity,
            battery_consume_rate=battery_consume_rate,
            penalty_unvisit=penalty_unvisited,
            penalty_delay=penalty_delayed
        )

        # Create ALNS configuration from parameters
        alns_config = self._create_alns_config(**kwargs)

        # Create ALNS instance
        self.alns_instance = ALNS(
            initial_solution=initial_solution,
            config=alns_config,
            dist_matrix=pdptw_instance.distance_matrix,
            battery_capacity=battery_capacity
        )

        # Run ALNS algorithm
        best_solution, _ = self.alns_instance.run()

        # Record solution in history (store adapter-wrapped solution)
        solution_adapter = PDPTWSolutionAdapter(best_solution)
        self.solution_history.append((solution_adapter, solution_adapter.objective_value()))

        # Return adapter-wrapped solution
        return solution_adapter

    def _create_alns_config(self, **kwargs) -> ALNSConfig:
        """Create ALNSConfig from configuration parameters.

        Args:
            **kwargs: Configuration parameters

        Returns:
            ALNSConfig instance
        """
        # Map common parameter names to ALNSConfig fields
        param_mapping = {
            'max_iterations': 'max_no_improve',
            'segment_length': 'segment_length',
            'num_segments': 'num_segments',
            'start_temp': 'start_temp',
            'cooling_rate': 'cooling_rate',
            'num_removal': 'num_removal',
        }

        # Start with default config
        config_dict = {}

        # Update with solver configuration
        config_dict.update(self.config)

        # Update with provided kwargs (mapping names if needed)
        for key, value in kwargs.items():
            if key in param_mapping:
                config_dict[param_mapping[key]] = value
            else:
                config_dict[key] = value

        # Create ALNSConfig instance
        return ALNSConfig(**config_dict)

    def get_solution_history(self) -> List[Tuple[VRPSolution, float]]:
        """Get history of solutions explored during search.

        Returns:
            List of (solution, objective_value) pairs
        """
        return self.solution_history

    def get_alns_instance(self) -> Optional[ALNS]:
        """Get the underlying ALNS instance for advanced operations.

        Returns:
            ALNS instance if solve() has been called, None otherwise
        """
        return self.alns_instance