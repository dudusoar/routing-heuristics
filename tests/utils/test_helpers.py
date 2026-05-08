"""Test helper functions for Routing Heuristics tests."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from vrp_toolkit.algorithms.base import VRPProblem, VRPSolution


def assert_dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame, check_dtypes: bool = False) -> None:
    """Assert two DataFrames are equal with helpful error messages."""
    pd.testing.assert_frame_equal(df1, df2, check_dtype=check_dtypes)


def assert_arrays_equal(arr1: np.ndarray, arr2: np.ndarray, rtol: float = 1e-5, atol: float = 1e-8) -> None:
    """Assert two numpy arrays are equal within tolerance."""
    np.testing.assert_allclose(arr1, arr2, rtol=rtol, atol=atol)


def create_minimal_pdptw_instance(
    n_orders: int = 2,
    seed: int = 42,
    robot_speed: float = 2.0
) -> PDPTWInstance:
    """
    Create a minimal PDPTW instance for testing.
    
    Args:
        n_orders: Number of pickup-delivery pairs
        seed: Random seed for reproducibility
        robot_speed: Robot speed for time matrix calculation
    
    Returns:
        PDPTWInstance: Test instance
    """
    np.random.seed(seed)
    n_nodes = 1 + 2 * n_orders  # depot + 2 * n_orders
    
    # Create order table
    data = {
        'ID': list(range(n_nodes)),
        'Type': ['depot'] + ['cp', 'cd'] * n_orders,
        'X': np.random.rand(n_nodes).tolist(),
        'Y': np.random.rand(n_nodes).tolist(),
        'Demand': [0.0] + [1.0, -1.0] * n_orders,
        'StartTime': [0.0] * n_nodes,
        'EndTime': [100.0] * n_nodes,
        'ServiceTime': [0.0] + [5.0, 5.0] * n_orders,
        'PartnerID': [0] * n_nodes,
        'RealIndex': list(range(n_nodes)),
        'RealType': ['depot'] + ['cp', 'cd'] * n_orders
    }
    
    # Set partner IDs properly for pickup-delivery pairs
    for i in range(n_orders):
        pickup_idx = 1 + 2 * i
        delivery_idx = 2 + 2 * i
        data['PartnerID'][pickup_idx] = delivery_idx
        data['PartnerID'][delivery_idx] = pickup_idx
    
    order_table = pd.DataFrame(data)
    
    # Create distance and time matrices
    distance_matrix = np.random.rand(n_nodes, n_nodes) * 10
    distance_matrix = (distance_matrix + distance_matrix.T) / 2
    np.fill_diagonal(distance_matrix, 0)
    
    time_matrix = distance_matrix / robot_speed
    
    instance = PDPTWInstance(
        order_table=order_table,
        distance_matrix=distance_matrix,
        time_matrix=time_matrix,
        robot_speed=robot_speed
    )
    
    return instance


def create_minimal_pdptw_solution(
    instance: Optional[PDPTWInstance] = None,
    n_orders: int = 2,
    n_vehicles: int = 1,
    seed: int = 42
) -> PDPTWSolution:
    """
    Create a minimal PDPTW solution for testing.
    
    Args:
        instance: PDPTW instance (created if None)
        n_orders: Number of orders (if instance is None)
        n_vehicles: Number of vehicles
        seed: Random seed for reproducibility
    
    Returns:
        PDPTWSolution: Test solution
    """
    if instance is None:
        instance = create_minimal_pdptw_instance(n_orders=n_orders, seed=seed)
    
    # Create simple routes: each vehicle serves orders in sequence
    n_nodes = len(instance.indices)
    routes = []
    
    if n_vehicles == 1:
        # Single vehicle: depot -> all pickups -> all deliveries -> depot
        route = [0]  # Start at depot
        # Add all pickups
        for i in range(n_orders):
            route.append(1 + 2 * i)  # Pickup node
        # Add all deliveries
        for i in range(n_orders):
            route.append(2 + 2 * i)  # Delivery node
        route.append(0)  # Return to depot
        routes.append(route)
    else:
        # Multiple vehicles: distribute orders evenly
        orders_per_vehicle = max(1, n_orders // n_vehicles)
        for v in range(n_vehicles):
            route = [0]  # Start at depot
            start_order = v * orders_per_vehicle
            end_order = min(start_order + orders_per_vehicle, n_orders)
            
            for i in range(start_order, end_order):
                route.append(1 + 2 * i)  # Pickup
                route.append(2 + 2 * i)  # Delivery
            
            route.append(0)  # Return to depot
            routes.append(route)
    
    solution = PDPTWSolution(
        instance=instance,
        vehicle_capacity=10.0,
        battery_capacity=100.0,
        battery_consume_rate=1.0,
        routes=routes,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )
    
    return solution


def assert_solution_valid(solution: PDPTWSolution) -> None:
    """Assert that a solution has valid structure."""
    assert solution.instance is not None, "Solution must have an instance"
    assert hasattr(solution, 'routes'), "Solution must have routes attribute"
    assert isinstance(solution.routes, list), "Routes must be a list"
    
    for route in solution.routes:
        assert isinstance(route, list), "Each route must be a list"
        assert len(route) >= 2, "Route must have at least depot start and end"
        assert route[0] == 0, "Route must start at depot (node 0)"
        assert route[-1] == 0, "Route must end at depot (node 0)"
    
    # Check that objective function can be calculated
    obj_value = solution.objective_function()
    assert isinstance(obj_value, (int, float)), "Objective function must return numeric value"
    
    # Check feasibility can be determined
    is_feasible = solution.is_feasible()
    assert isinstance(is_feasible, bool), "is_feasible must return boolean"


def assert_instance_valid(instance: PDPTWInstance) -> None:
    """Assert that an instance has valid structure."""
    assert hasattr(instance, 'n'), "Instance must have n attribute"
    assert hasattr(instance, 'indices'), "Instance must have indices attribute"
    assert hasattr(instance, 'demands'), "Instance must have demands attribute"
    assert hasattr(instance, 'time_windows'), "Instance must have time_windows attribute"
    assert hasattr(instance, 'service_times'), "Instance must have service_times attribute"
    assert hasattr(instance, 'distance_matrix'), "Instance must have distance_matrix attribute"
    assert hasattr(instance, 'time_matrix'), "Instance must have time_matrix attribute"
    
    n_nodes = len(instance.indices)
    assert instance.distance_matrix.shape == (n_nodes, n_nodes), \
        f"Distance matrix shape mismatch: {instance.distance_matrix.shape} != ({n_nodes}, {n_nodes})"
    assert instance.time_matrix.shape == (n_nodes, n_nodes), \
        f"Time matrix shape mismatch: {instance.time_matrix.shape} != ({n_nodes}, {n_nodes})"
    
    # Check that matrices are square and have zero diagonal
    assert np.allclose(np.diag(instance.distance_matrix), 0), "Distance matrix diagonal must be zero"
    assert np.allclose(np.diag(instance.time_matrix), 0), "Time matrix diagonal must be zero"


def compare_vrp_problems(problem1: VRPProblem, problem2: VRPProblem, tolerance: float = 1e-6) -> None:
    """Compare two VRP problems for equality."""
    assert problem1.get_num_nodes() == problem2.get_num_nodes()
    assert problem1.get_num_vehicles() == problem2.get_num_vehicles()
    
    # Compare distance matrices
    dist1 = problem1.get_distance_matrix()
    dist2 = problem2.get_distance_matrix()
    assert_arrays_equal(dist1, dist2, atol=tolerance)
    
    # Compare time windows if available
    if hasattr(problem1, 'get_time_windows') and hasattr(problem2, 'get_time_windows'):
        tw1 = problem1.get_time_windows()
        tw2 = problem2.get_time_windows()
        assert len(tw1) == len(tw2)
        for i, (start1, end1) in enumerate(tw1):
            start2, end2 = tw2[i]
            assert abs(start1 - start2) < tolerance
            assert abs(end1 - end2) < tolerance


def print_test_summary(test_name: str, passed: bool, details: str = "") -> None:
    """Print formatted test summary."""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} - {test_name}")
    if details and not passed:
        print(f"  Details: {details}")
