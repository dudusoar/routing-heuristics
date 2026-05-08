"""Pytest configuration and fixtures for Routing Heuristics tests."""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple

from vrp_toolkit.problems.pdptw import PDPTWInstance, PDPTWSolution
from vrp_toolkit.algorithms.alns.solver import ALNS, ALNSConfig
from vrp_toolkit.data.map import RealMap
from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator


@pytest.fixture
def simple_order_table() -> pd.DataFrame:
    """Create a simple order table for testing."""
    data = {
        'ID': [0, 1, 2, 3, 4, 5],
        'Type': ['depot', 'cp', 'cp', 'cd', 'cd', 'charging'],
        'X': [0.0, 1.0, 2.0, 1.0, 2.0, 0.5],
        'Y': [0.0, 1.0, 2.0, 1.0, 2.0, 0.5],
        'Demand': [0.0, 1.0, 1.0, -1.0, -1.0, 0.0],
        'StartTime': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'EndTime': [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        'ServiceTime': [0.0, 5.0, 5.0, 5.0, 5.0, 0.0],
        'PartnerID': [0, 3, 4, 1, 2, 0],
        'RealIndex': [0, 1, 2, 3, 4, 5],
        'RealType': ['depot', 'cp', 'cp', 'cd', 'cd', 'charging']
    }
    return pd.DataFrame(data)


@pytest.fixture
def simple_distance_matrix() -> np.ndarray:
    """Create a simple 6x6 distance matrix."""
    np.random.seed(42)
    n_nodes = 6
    distance_matrix = np.random.rand(n_nodes, n_nodes) * 10
    # Make symmetric
    distance_matrix = (distance_matrix + distance_matrix.T) / 2
    # Zero diagonal
    np.fill_diagonal(distance_matrix, 0)
    return distance_matrix


@pytest.fixture
def simple_time_matrix(simple_distance_matrix) -> np.ndarray:
    """Create time matrix from distance matrix."""
    robot_speed = 2.0
    return simple_distance_matrix / robot_speed


@pytest.fixture
def simple_pdptw_instance(simple_order_table, simple_distance_matrix, simple_time_matrix) -> PDPTWInstance:
    """Create a simple PDPTW instance for testing."""
    instance = PDPTWInstance(
        order_table=simple_order_table,
        distance_matrix=simple_distance_matrix,
        time_matrix=simple_time_matrix,
        robot_speed=2.0
    )
    return instance


@pytest.fixture
def simple_pdptw_solution(simple_pdptw_instance) -> PDPTWSolution:
    """Create a simple PDPTW solution for testing."""
    # Create simple route: depot -> pickup1 -> pickup2 -> delivery1 -> delivery2 -> depot
    routes = [[0, 1, 2, 3, 4, 0]]
    
    solution = PDPTWSolution(
        instance=simple_pdptw_instance,
        vehicle_capacity=10.0,
        battery_capacity=100.0,
        battery_consume_rate=1.0,
        routes=routes,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )
    return solution


@pytest.fixture
def alns_config() -> ALNSConfig:
    """Create ALNS configuration for testing."""
    config = ALNSConfig(
        num_removal=5,
        p=4.0,
        k=3,
        L_max=5,
        avg_remove_order=2.0,
        max_no_improve=50,
        segment_length=10,
        num_segments=5,
        r=0.1,
        sigma=(33.0, 9.0, 13.0),
        start_temp=100.0,
        cooling_rate=0.95,
        cost_ci_obj_diff_threshold=0.1,
        cost_ci_window_size=25
    )
    return config


@pytest.fixture
def synthetic_real_map() -> RealMap:
    """Create a synthetic RealMap for testing."""
    np.random.seed(42)
    # RealMap creates indices: restaurants 1..n_r, customers n_r+1..n_r+n_c
    n_r = 3  # number of restaurants
    n_c = 7  # number of customers

    # Simple uniform distribution function for coordinates
    def uniform_dist(low=0.0, high=100.0):
        return np.random.uniform(low, high)

    dist_params = {"low": 0.0, "high": 100.0}

    real_map = RealMap(
        n_r=n_r,
        n_c=n_c,
        dist_function=uniform_dist,
        dist_params=dist_params
    )
    return real_map


class TestDataFactory:
    """Factory class for creating test data."""
    
    @staticmethod
    def create_minimal_order_table(n_orders: int = 2) -> pd.DataFrame:
        """Create minimal order table with n_orders pickup-delivery pairs."""
        n_nodes = 1 + 2 * n_orders  # depot + 2 * n_orders
        
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
            
        df = pd.DataFrame(data)
        return df
    
    @staticmethod
    def create_symmetric_distance_matrix(n_nodes: int, seed: int = 42) -> np.ndarray:
        """Create symmetric distance matrix with zero diagonal."""
        np.random.seed(seed)
        matrix = np.random.rand(n_nodes, n_nodes) * 10
        matrix = (matrix + matrix.T) / 2
        np.fill_diagonal(matrix, 0)
        return matrix


# Register the factory as a fixture
@pytest.fixture
def test_data_factory() -> TestDataFactory:
    """Provide TestDataFactory as a fixture."""
    return TestDataFactory
