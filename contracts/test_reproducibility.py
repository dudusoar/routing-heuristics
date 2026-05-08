"""
Contract Tests: Reproducibility

Ensures that same seed + same config produces identical results.
This is CRITICAL for learning - users must trust that experiments are reproducible.
"""

import pytest
import numpy as np
from vrp_toolkit.problems.pdptw import PDPTWInstance
from vrp_toolkit.algorithms.alns import ALNS, ALNSConfig, greedy_insertion_initial_solution
from vrp_toolkit.algorithms.base import PDPTWProblemAdapter
from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator
from vrp_toolkit.data.map import RealMap


# ===== Test Fixtures =====

@pytest.fixture
def simple_instance():
    """Generate a simple 5-order PDPTW instance for testing."""
    # Set seed for deterministic instance generation
    np.random.seed(42)

    # Generate map
    real_map = RealMap(
        n_r=2,  # 2 restaurants
        n_c=5,  # 5 customers
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Generate demands
    demand_gen = DemandGenerator(
        time_range=240,
        time_step=30,
        restaurants=real_map.restaurants,
        customers=real_map.customers,
        random_params={
            'sample_dist': {'function': np.random.poisson, 'params': {'lam': 2}},
            'demand_dist': {'function': np.random.randint, 'params': {'low': 1, 'high': 3}}
        }
    )

    # Generate orders
    order_gen = OrderGenerator(
        real_map=real_map,
        demand_table=demand_gen.demand_table,
        time_params={
            'time_window_length': 30,
            'service_time': 5,
            'extra_time': 10,
            'big_time': 1000
        },
        robot_speed=1.0
    )

    # Create instance
    instance = PDPTWInstance(
        order_table=order_gen.order_table,
        distance_matrix=real_map.distance_matrix,
        time_matrix=order_gen.time_matrix,
        robot_speed=1.0
    )

    return instance


@pytest.fixture
def default_config():
    """Default ALNS configuration for testing."""
    return ALNSConfig(
        max_iterations=100,  # Short for fast tests
        temperature=10.0,
        cooling_rate=0.95,
        segment_length=50,
        seed=42  # CRITICAL: seed parameter
    )


# ===== Reproducibility Tests =====

def test_same_seed_same_instance():
    """
    CONTRACT: Same seed must produce identical instances.

    This test verifies that instance generation is deterministic.
    """
    # First generation
    np.random.seed(42)
    real_map1 = RealMap(
        n_r=3, n_c=10,
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Second generation with same seed
    np.random.seed(42)
    real_map2 = RealMap(
        n_r=3, n_c=10,
        dist_function=np.random.uniform,
        dist_params={'low': 0, 'high': 100}
    )

    # Distance matrices should be identical
    np.testing.assert_array_equal(
        real_map1.distance_matrix,
        real_map2.distance_matrix,
        err_msg="Same seed should produce identical distance matrices"
    )

    # Coordinates should be identical
    assert real_map1.coordinates == real_map2.coordinates, \
        "Same seed should produce identical coordinates"


def test_alns_config_has_seed_parameter():
    """
    CONTRACT: ALNSConfig must accept and store seed parameter.

    This is required for reproducible ALNS runs.
    """
    config = ALNSConfig(
        max_iterations=100,
        seed=42
    )

    # Verify seed is stored
    assert hasattr(config, 'seed'), "ALNSConfig must have 'seed' attribute"
    assert config.seed == 42, "ALNSConfig.seed should be 42"


def test_same_seed_same_initial_solution(simple_instance):
    """
    CONTRACT: Same seed must produce identical initial solutions.

    Initial solution generation should be deterministic.
    """
    problem = PDPTWProblemAdapter(simple_instance)

    # First generation
    np.random.seed(42)
    initial1 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    # Second generation with same seed
    np.random.seed(42)
    initial2 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    # Both should succeed
    assert initial1 is not None, "First initial solution generation failed"
    assert initial2 is not None, "Second initial solution generation failed"

    # Routes should be identical
    assert initial1.routes == initial2.routes, \
        "Same seed should produce identical initial solution routes"

    # Objective values should be identical
    assert abs(initial1.objective_value() - initial2.objective_value()) < 1e-6, \
        "Same seed should produce identical initial solution costs"


def test_same_seed_same_alns_solution(simple_instance, default_config):
    """
    CONTRACT: Same seed + same config must produce identical ALNS solutions.

    This is THE MOST CRITICAL contract for the playground.
    If this fails, users cannot reproduce experiments.
    """
    problem = PDPTWProblemAdapter(simple_instance)

    # First run
    np.random.seed(42)
    initial1 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    alns1 = ALNS(
        initial_solution=initial1._solution,
        config=default_config,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns1.run()
    solution1 = alns1.best_solution

    # Second run with same seed
    np.random.seed(42)
    initial2 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    alns2 = ALNS(
        initial_solution=initial2._solution,
        config=default_config,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns2.run()
    solution2 = alns2.best_solution

    # CRITICAL: Solutions must be identical
    assert solution1.routes == solution2.routes, \
        f"Same seed must produce identical routes.\nRun 1: {solution1.routes}\nRun 2: {solution2.routes}"

    assert abs(solution1.objective_function() - solution2.objective_function()) < 1e-6, \
        f"Same seed must produce identical costs.\nRun 1: {solution1.objective_function()}\nRun 2: {solution2.objective_function()}"


def test_different_seed_different_solution(simple_instance):
    """
    CONTRACT: Different seeds should produce different solutions (with high probability).

    This verifies that seed actually affects the algorithm.
    """
    problem = PDPTWProblemAdapter(simple_instance)

    config1 = ALNSConfig(max_iterations=100, seed=42)
    config2 = ALNSConfig(max_iterations=100, seed=999)

    # Run 1 with seed=42
    np.random.seed(42)
    initial1 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )
    alns1 = ALNS(
        initial_solution=initial1._solution,
        config=config1,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns1.run()

    # Run 2 with seed=999
    np.random.seed(999)
    initial2 = greedy_insertion_initial_solution(
        problem=problem,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )
    alns2 = ALNS(
        initial_solution=initial2._solution,
        config=config2,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns2.run()

    # Solutions should be different (with high probability)
    # Note: There's a tiny chance they're the same by coincidence
    assert alns1.best_solution.routes != alns2.best_solution.routes or \
           abs(alns1.best_solution.objective_function() - alns2.best_solution.objective_function()) > 1e-6, \
           "Different seeds should produce different solutions (failed with small probability)"


# ===== Playground-Specific Reproducibility Tests =====

def test_playground_workflow_reproducibility(simple_instance):
    """
    CONTRACT: Playground's complete workflow must be reproducible.

    This simulates the exact workflow in playground/app.py:
    1. User sets seed
    2. Generates instance
    3. Configures ALNS
    4. Runs solver

    Same inputs must produce same outputs.
    """
    # Workflow Run 1
    seed = 42
    np.random.seed(seed)

    problem1 = PDPTWProblemAdapter(simple_instance)
    initial1 = greedy_insertion_initial_solution(
        problem=problem1,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    config1 = ALNSConfig(
        max_iterations=100,
        temperature=10.0,
        cooling_rate=0.95,
        segment_length=50,
        seed=seed  # IMPORTANT: Must use seed
    )

    alns1 = ALNS(
        initial_solution=initial1._solution,
        config=config1,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns1.run()

    # Workflow Run 2 (identical)
    np.random.seed(seed)

    problem2 = PDPTWProblemAdapter(simple_instance)
    initial2 = greedy_insertion_initial_solution(
        problem=problem2,
        num_vehicles=2,
        vehicle_capacity=1000,
        battery_capacity=1000.0,
        battery_consume_rate=1.0,
        penalty_unvisit=1000.0,
        penalty_delay=100.0
    )

    config2 = ALNSConfig(
        max_iterations=100,
        temperature=10.0,
        cooling_rate=0.95,
        segment_length=50,
        seed=seed
    )

    alns2 = ALNS(
        initial_solution=initial2._solution,
        config=config2,
        dist_matrix=simple_instance.distance_matrix,
        battery_capacity=1000.0
    )
    alns2.run()

    # Results must match
    assert abs(alns1.best_solution.objective_function() - alns2.best_solution.objective_function()) < 1e-6, \
        "Playground workflow must be reproducible (objective value)"

    assert alns1.best_solution.routes == alns2.best_solution.routes, \
        "Playground workflow must be reproducible (routes)"
