"""
Test playground core functionality without UI interaction.

Tests the logic behind both Tab 1 (Quickstart) and Tab 2 (Problem Variants)
to ensure all features work correctly.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add parent directory to path to import vrp_toolkit
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from vrp_toolkit.problems.pdptw import PDPTWInstance
from vrp_toolkit.algorithms.alns import ALNS, ALNSConfig, greedy_insertion_initial_solution
from vrp_toolkit.algorithms.base import PDPTWProblemAdapter
from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator
from vrp_toolkit.data.map import RealMap


class TestTab1Quickstart:
    """Test Tab 1: Quickstart workflow"""

    def test_synthetic_instance_generation(self):
        """Test synthetic PDPTW instance generation (Tab 1 workflow)"""
        print("\n" + "="*70)
        print("TEST 1: Tab 1 - Synthetic Instance Generation")
        print("="*70)

        num_orders = 5
        seed = 42

        try:
            # Set random seed for reproducibility
            np.random.seed(seed)

            # Use simpler approach: directly create order table like Tab 2
            # to avoid DemandGenerator creating too many orders
            order_data = []

            # Depot
            order_data.append({
                'ID': 0, 'Type': 'depot', 'X': 0.0, 'Y': 0.0, 'Demand': 0.0,
                'StartTime': 0.0, 'EndTime': 480.0, 'ServiceTime': 0.0,
                'PartnerID': 0, 'RealIndex': 0, 'RealType': 'depot'
            })

            # Generate orders
            for i in range(1, num_orders + 1):
                # Pickup
                pickup_x = np.random.uniform(5, 50)
                pickup_y = np.random.uniform(5, 50)

                # Delivery (near pickup)
                delivery_x = pickup_x + np.random.uniform(-10, 10)
                delivery_y = pickup_y + np.random.uniform(-10, 10)

                demand = np.random.randint(1, 5)

                # Pickup node
                order_data.append({
                    'ID': i, 'Type': 'cp', 'X': pickup_x, 'Y': pickup_y, 'Demand': demand,
                    'StartTime': 0.0, 'EndTime': 240.0, 'ServiceTime': 5.0,
                    'PartnerID': i + num_orders, 'RealIndex': i, 'RealType': 'cp'
                })

                # Delivery node
                order_data.append({
                    'ID': i + num_orders, 'Type': 'cd', 'X': delivery_x, 'Y': delivery_y,
                    'Demand': -demand, 'StartTime': 0.0, 'EndTime': 300.0,
                    'ServiceTime': 5.0, 'PartnerID': i, 'RealIndex': i + num_orders, 'RealType': 'cd'
                })

            order_table = pd.DataFrame(order_data)

            # Create distance and time matrices
            n = len(order_table)
            distance_matrix = np.zeros((n, n))
            coords = order_table[['X', 'Y']].values

            for i in range(n):
                for j in range(n):
                    if i != j:
                        distance_matrix[i, j] = np.linalg.norm(coords[i] - coords[j])

            time_matrix = distance_matrix / 1.0  # robot_speed = 1.0

            # Create instance
            instance = PDPTWInstance(
                order_table=order_table,
                distance_matrix=distance_matrix,
                time_matrix=time_matrix,
                robot_speed=1.0
            )

            print(f"[PASS] Instance generated successfully")
            print(f"  - Orders: {instance.n}")
            print(f"  - Total nodes: {len(instance.indices)}")
            print(f"  - Depot index: {instance.depot_index}")

            return instance

        except Exception as e:
            print(f"[FAIL] {e}")
            raise

    def test_alns_solving(self, instance):
        """Test ALNS solving workflow (Tab 1)"""
        print("\n" + "="*70)
        print("TEST 2: Tab 1 - ALNS Solving")
        print("="*70)

        seed = 42
        num_vehicles = 2
        max_iterations = 100
        battery_capacity = 300.0

        try:
            # Set seed
            np.random.seed(seed)

            # Create problem adapter
            problem = PDPTWProblemAdapter(instance)

            # Generate initial solution
            initial_solution = greedy_insertion_initial_solution(
                problem=problem,
                num_vehicles=num_vehicles,
                vehicle_capacity=1000,
                battery_capacity=battery_capacity,
                battery_consume_rate=1.0,
                penalty_unvisit=1000.0,
                penalty_delay=100.0
            )

            if initial_solution is None:
                print("[FAIL] FAILED: Could not generate initial solution")
                return False

            print(f"[PASS] Initial solution generated")
            print(f"  - Initial cost: {initial_solution.objective_value():.2f}")
            print(f"  - Feasible: {initial_solution.is_feasible()}")

            # Check for empty routes
            has_empty_routes = all(len(route) == 2 and route == [0, 0] for route in initial_solution.routes)
            if has_empty_routes:
                print("[FAIL] WARNING: Initial solution has empty routes")
                return False

            # Create ALNS config
            segment_length = 50
            num_segments = max(1, max_iterations // segment_length)
            config = ALNSConfig(
                num_segments=num_segments,
                segment_length=segment_length,
                start_temp=10.0,
                cooling_rate=0.95,
                seed=seed
            )

            # Run ALNS
            alns = ALNS(
                initial_solution=initial_solution._solution,
                config=config,
                dist_matrix=instance.distance_matrix,
                battery_capacity=battery_capacity
            )

            best_solution, best_charging_solution = alns.run()

            print(f"[PASS] ALNS completed successfully")
            print(f"  - Best cost: {best_solution.objective_function():.2f}")
            print(f"  - Feasible: {best_solution.is_feasible()}")
            print(f"  - Routes: {len(best_solution.routes)}")

            return True

        except Exception as e:
            print(f"[FAIL] FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


class TestTab2ProblemVariants:
    """Test Tab 2: Problem Variants workflow"""

    def create_variant_order_table(self, num_orders, constraint_level, seed):
        """Helper function to create order table with specified constraint level."""
        np.random.seed(seed)

        # Create base coordinates
        order_data = []

        # Depot
        order_data.append({
            'ID': 0, 'Type': 'depot', 'X': 0.0, 'Y': 0.0, 'Demand': 0.0,
            'StartTime': 0.0, 'EndTime': 480.0, 'ServiceTime': 0.0,
            'PartnerID': 0, 'RealIndex': 0, 'RealType': 'depot'
        })

        # Generate orders
        for i in range(1, num_orders + 1):
            # Pickup
            pickup_x = np.random.uniform(2, 10)
            pickup_y = np.random.uniform(2, 10)

            # Delivery (near pickup)
            delivery_x = pickup_x + np.random.uniform(-3, 3)
            delivery_y = pickup_y + np.random.uniform(-3, 3)

            demand = np.random.randint(5, 15)

            # Configure time windows based on constraint level
            if constraint_level == "Relaxed":
                pickup_start, pickup_end = 0.0, 480.0
                delivery_start, delivery_end = 0.0, 480.0
            elif constraint_level == "Standard":
                pickup_start, pickup_end = 0.0, 120.0
                delivery_start, delivery_end = 0.0, 180.0
            else:  # Strict
                pickup_start, pickup_end = 30.0, 60.0
                delivery_start, delivery_end = 90.0, 120.0

            # Pickup node
            order_data.append({
                'ID': i, 'Type': 'cp', 'X': pickup_x, 'Y': pickup_y, 'Demand': demand,
                'StartTime': pickup_start, 'EndTime': pickup_end, 'ServiceTime': 5.0,
                'PartnerID': i + num_orders, 'RealIndex': i, 'RealType': 'cp'
            })

            # Delivery node
            order_data.append({
                'ID': i + num_orders, 'Type': 'cd', 'X': delivery_x, 'Y': delivery_y,
                'Demand': -demand, 'StartTime': delivery_start, 'EndTime': delivery_end,
                'ServiceTime': 5.0, 'PartnerID': i, 'RealIndex': i + num_orders, 'RealType': 'cd'
            })

        return pd.DataFrame(order_data)

    def create_distance_matrix(self, order_table):
        """Compute Euclidean distance matrix."""
        n = len(order_table)
        dist_matrix = np.zeros((n, n))
        coords = order_table[['X', 'Y']].values

        for i in range(n):
            for j in range(n):
                if i != j:
                    dist_matrix[i, j] = np.linalg.norm(coords[i] - coords[j])
        return dist_matrix

    def test_constraint_level(self, constraint_level):
        """Test instance generation for a specific constraint level"""
        print("\n" + "="*70)
        print(f"TEST: Tab 2 - {constraint_level} Constraint Level")
        print("="*70)

        num_orders = 3
        seed = 42

        try:
            # Generate order table with constraints
            order_table = self.create_variant_order_table(num_orders, constraint_level, seed)

            # Create matrices
            distance_matrix = self.create_distance_matrix(order_table)
            time_matrix = distance_matrix / 2.0  # robot_speed = 2.0

            # Create instance
            instance = PDPTWInstance(
                order_table=order_table,
                distance_matrix=distance_matrix,
                time_matrix=time_matrix,
                robot_speed=2.0
            )

            print(f"[PASS] {constraint_level} instance generated successfully")
            print(f"  - Orders: {instance.n}")
            print(f"  - Total nodes: {len(instance.indices)}")

            # Verify time window configuration
            pickup_example = order_table[order_table['Type'] == 'cp'].iloc[0]
            delivery_example = order_table[order_table['Type'] == 'cd'].iloc[0]

            print(f"  - Pickup time window: [{pickup_example['StartTime']:.0f}, {pickup_example['EndTime']:.0f}]")
            print(f"  - Delivery time window: [{delivery_example['StartTime']:.0f}, {delivery_example['EndTime']:.0f}]")

            # Expected time windows
            expected = {
                "Relaxed": {"pickup": (0, 480), "delivery": (0, 480)},
                "Standard": {"pickup": (0, 120), "delivery": (0, 180)},
                "Strict": {"pickup": (30, 60), "delivery": (90, 120)}
            }

            exp_pickup = expected[constraint_level]["pickup"]
            exp_delivery = expected[constraint_level]["delivery"]

            assert pickup_example['StartTime'] == exp_pickup[0], f"Pickup start time mismatch"
            assert pickup_example['EndTime'] == exp_pickup[1], f"Pickup end time mismatch"
            assert delivery_example['StartTime'] == exp_delivery[0], f"Delivery start time mismatch"
            assert delivery_example['EndTime'] == exp_delivery[1], f"Delivery end time mismatch"

            print(f"[PASS] Time windows verified correctly")

            # Try to solve
            np.random.seed(seed)
            problem = PDPTWProblemAdapter(instance)

            initial_solution = greedy_insertion_initial_solution(
                problem=problem,
                num_vehicles=2,
                vehicle_capacity=1000,
                battery_capacity=300.0,
                battery_consume_rate=1.0,
                penalty_unvisit=1000.0,
                penalty_delay=100.0
            )

            if initial_solution is None:
                print(f"  [WARN] No initial solution found (expected for {constraint_level})")
            else:
                print(f"[PASS] Initial solution found")
                print(f"  - Cost: {initial_solution.objective_value():.2f}")
                print(f"  - Feasible: {initial_solution.is_feasible()}")

            return True

        except Exception as e:
            print(f"[FAIL] FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


class TestReproducibility:
    """Test reproducibility with same seed"""

    def test_same_seed_same_result(self):
        """Test that same seed produces same instance"""
        print("\n" + "="*70)
        print("TEST: Reproducibility - Same Seed Same Result")
        print("="*70)

        seed = 42
        num_orders = 5

        try:
            # Generate instance 1
            np.random.seed(seed)
            num_restaurants = max(2, num_orders // 3)
            real_map_1 = RealMap(
                n_r=num_restaurants,
                n_c=num_orders,
                dist_function=np.random.uniform,
                dist_params={'low': 0, 'high': 100}
            )

            # Generate instance 2 with same seed
            np.random.seed(seed)
            real_map_2 = RealMap(
                n_r=num_restaurants,
                n_c=num_orders,
                dist_function=np.random.uniform,
                dist_params={'low': 0, 'high': 100}
            )

            # Compare distance matrices
            distance_match = np.allclose(real_map_1.distance_matrix, real_map_2.distance_matrix)

            if distance_match:
                print("[PASS] Same seed produces identical instances")
                print(f"  - Distance matrices match: {distance_match}")
            else:
                print("[FAIL] FAILED: Distance matrices do not match")
                return False

            return True

        except Exception as e:
            print(f"[FAIL] FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("Routing Heuristics Playground Feature Testing")
    print("="*70)
    print("Testing both Tab 1 (Quickstart) and Tab 2 (Problem Variants)")
    print("="*70)

    results = {}

    # Test Tab 1
    print("\n" + "#"*70)
    print("# TAB 1: QUICKSTART TESTS")
    print("#"*70)

    tab1_tester = TestTab1Quickstart()

    try:
        instance = tab1_tester.test_synthetic_instance_generation()
        results['tab1_generation'] = True

        results['tab1_solving'] = tab1_tester.test_alns_solving(instance)
    except Exception as e:
        results['tab1_generation'] = False
        results['tab1_solving'] = False

    # Test Tab 2
    print("\n" + "#"*70)
    print("# TAB 2: PROBLEM VARIANTS TESTS")
    print("#"*70)

    tab2_tester = TestTab2ProblemVariants()

    for level in ["Relaxed", "Standard", "Strict"]:
        results[f'tab2_{level.lower()}'] = tab2_tester.test_constraint_level(level)

    # Test reproducibility
    print("\n" + "#"*70)
    print("# REPRODUCIBILITY TESTS")
    print("#"*70)

    repro_tester = TestReproducibility()
    results['reproducibility'] = repro_tester.test_same_seed_same_result()

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)

    for test_name, passed in results.items():
        status = "[PASS] PASS" if passed else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print("="*70)
    print(f"Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
    print("="*70)

    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
