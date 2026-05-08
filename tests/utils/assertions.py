"""Custom assertions for Routing Heuristics tests."""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple
from vrp_toolkit.problems.pdptw import PDPTWSolution


def assert_solution_feasible(solution: PDPTWSolution, check_constraints: bool = True) -> None:
    """
    Assert that a solution is feasible.
    
    Args:
        solution: PDPTW solution to check
        check_constraints: Whether to check individual constraints
    """
    assert solution.is_feasible(), f"Solution should be feasible but is not. Objective: {solution.objective_function()}"
    
    if check_constraints:
        # Check capacity constraints
        selected_vehicles = solution.get_selected_vehicles()
        assert solution.check_capacity_constraint(selected_vehicles), "Capacity constraint violated"
        
        # Check battery constraints
        assert solution.check_battery_constraint(selected_vehicles), "Battery constraint violated"
        
        # Check pickup-delivery order
        assert solution.check_pickup_delivery_order(selected_vehicles), "Pickup-delivery order violated"
        
        # Check time windows if the method exists
        if hasattr(solution, 'check_time_window_constraint'):
            assert solution.check_time_window_constraint(selected_vehicles), "Time window constraint violated"


def assert_solution_valid(solution: Any, check_constraints: bool = True) -> None:
    """
    Assert that a solution is valid (exists and has proper structure).

    Args:
        solution: Solution to check (can be PDPTWSolution or VRPSolution adapter)
        check_constraints: Whether to check feasibility constraints
    """
    assert solution is not None, "Solution should not be None"
    assert hasattr(solution, 'routes'), "Solution must have routes attribute"

    # If it's an adapter, extract the original solution
    if hasattr(solution, 'original_solution'):
        pdptw_solution = solution.original_solution
    else:
        pdptw_solution = solution

    # Check feasibility if requested
    if check_constraints and hasattr(pdptw_solution, 'is_feasible'):
        assert_solution_feasible(pdptw_solution, check_constraints=True)


def assert_solution_infeasible(solution: PDPTWSolution) -> None:
    """Assert that a solution is infeasible."""
    assert not solution.is_feasible(), f"Solution should be infeasible but is feasible. Objective: {solution.objective_function()}"


def assert_routes_valid(routes: List[List[int]], n_nodes: int) -> None:
    """
    Assert that routes have valid structure.
    
    Args:
        routes: List of routes, each route is list of node indices
        n_nodes: Total number of nodes in the problem
    """
    assert isinstance(routes, list), "Routes must be a list"
    
    visited_nodes = set()
    
    for i, route in enumerate(routes):
        assert isinstance(route, list), f"Route {i} must be a list"
        assert len(route) >= 2, f"Route {i} must have at least 2 nodes (depot start and end)"
        assert route[0] == 0, f"Route {i} must start at depot (node 0), got {route[0]}"
        assert route[-1] == 0, f"Route {i} must end at depot (node 0), got {route[-1]}"
        
        # Check node indices are valid
        for node in route:
            assert 0 <= node < n_nodes, f"Route {i} contains invalid node index {node} (max {n_nodes-1})"
        
        # Track visited nodes (excluding depot at start/end)
        visited_nodes.update(route[1:-1])
    
    # Check no node appears more than once (except depot)
    all_nodes = []
    for route in routes:
        all_nodes.extend(route)
    
    node_counts = {}
    for node in all_nodes:
        node_counts[node] = node_counts.get(node, 0) + 1
    
    for node, count in node_counts.items():
        if node == 0:
            # Depot can appear multiple times (start/end of each route)
            pass
        else:
            assert count == 1, f"Node {node} appears {count} times, should appear exactly once"


def assert_distance_matrix_valid(distance_matrix: np.ndarray, symmetric: bool = True) -> None:
    """
    Assert that a distance matrix is valid.
    
    Args:
        distance_matrix: Distance matrix to check
        symmetric: Whether matrix should be symmetric
    """
    assert isinstance(distance_matrix, np.ndarray), "Distance matrix must be numpy array"
    assert distance_matrix.ndim == 2, "Distance matrix must be 2D"
    assert distance_matrix.shape[0] == distance_matrix.shape[1], "Distance matrix must be square"
    
    n = distance_matrix.shape[0]
    
    # Check diagonal is zero
    assert np.allclose(np.diag(distance_matrix), 0), "Distance matrix diagonal must be zero"
    
    # Check non-negative distances
    assert np.all(distance_matrix >= 0), "Distance matrix must contain non-negative values"
    
    # Check symmetry if required
    if symmetric:
        assert np.allclose(distance_matrix, distance_matrix.T), "Distance matrix must be symmetric"


def assert_time_matrix_valid(time_matrix: np.ndarray, distance_matrix: np.ndarray = None, 
                            speed: float = None, tolerance: float = 1e-6) -> None:
    """
    Assert that a time matrix is valid.
    
    Args:
        time_matrix: Time matrix to check
        distance_matrix: Optional distance matrix to compare with
        speed: Optional speed for distance-time conversion
        tolerance: Numerical tolerance for comparisons
    """
    assert isinstance(time_matrix, np.ndarray), "Time matrix must be numpy array"
    assert time_matrix.ndim == 2, "Time matrix must be 2D"
    assert time_matrix.shape[0] == time_matrix.shape[1], "Time matrix must be square"
    
    n = time_matrix.shape[0]
    
    # Check diagonal is zero
    assert np.allclose(np.diag(time_matrix), 0, atol=tolerance), "Time matrix diagonal must be zero"
    
    # Check non-negative times
    assert np.all(time_matrix >= 0), "Time matrix must contain non-negative values"
    
    # Check symmetry
    assert np.allclose(time_matrix, time_matrix.T, atol=tolerance), "Time matrix must be symmetric"
    
    # If distance matrix and speed provided, check consistency
    if distance_matrix is not None and speed is not None:
        expected_time = distance_matrix / speed
        assert np.allclose(time_matrix, expected_time, atol=tolerance), \
            f"Time matrix doesn't match distance/speed conversion. Max diff: {np.max(np.abs(time_matrix - expected_time))}"


def assert_order_table_valid(order_table: pd.DataFrame, n_orders: int = None) -> None:
    """
    Assert that an order table has valid structure.
    
    Args:
        order_table: Order table DataFrame to check
        n_orders: Expected number of orders (optional)
    """
    required_columns = {'ID', 'Type', 'X', 'Y', 'Demand', 'StartTime', 'EndTime', 
                       'ServiceTime', 'PartnerID', 'RealIndex', 'RealType'}
    
    assert set(order_table.columns) >= required_columns, \
        f"Order table missing required columns. Missing: {required_columns - set(order_table.columns)}"
    
    # Check ID column is unique
    assert order_table['ID'].is_unique, "ID column must contain unique values"
    
    # Check Type column has valid values
    valid_types = {'depot', 'cp', 'cd'}
    invalid_types = set(order_table['Type'].unique()) - valid_types
    assert not invalid_types, f"Invalid node types found: {invalid_types}"
    
    # Check exactly one depot
    depot_count = (order_table['Type'] == 'depot').sum()
    assert depot_count == 1, f"Expected exactly 1 depot, found {depot_count}"
    
    # Check pickup-delivery pairs match
    if n_orders is not None:
        # Count pickups and deliveries
        pickup_count = (order_table['Type'] == 'cp').sum()
        delivery_count = (order_table['Type'] == 'cd').sum()
        assert pickup_count == n_orders, f"Expected {n_orders} pickups, found {pickup_count}"
        assert delivery_count == n_orders, f"Expected {n_orders} deliveries, found {delivery_count}"
    
    # Check PartnerID references are valid
    valid_ids = set(order_table['ID'])
    partner_ids = order_table['PartnerID'].unique()
    for pid in partner_ids:
        assert pid in valid_ids, f"PartnerID {pid} not found in ID column"
    
    # Check depot has itself as partner
    depot_row = order_table[order_table['Type'] == 'depot'].iloc[0]
    assert depot_row['PartnerID'] == depot_row['ID'], "Depot must have itself as partner"
    
    # Check pickup-delivery pairs are reciprocal
    for _, row in order_table.iterrows():
        if row['Type'] in {'cp', 'cd'}:
            partner_row = order_table[order_table['ID'] == row['PartnerID']].iloc[0]
            assert partner_row['PartnerID'] == row['ID'], \
                f"Partner relationship not reciprocal for node {row['ID']}"
