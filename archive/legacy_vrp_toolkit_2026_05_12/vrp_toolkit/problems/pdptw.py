"""PDPTW (Pickup and Delivery Problem with Time Windows) problem instance.

This module defines the PDPTWInstance class for representing PDPTW problem
instances with battery constraints commonly used in delivery robot problems.
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional, Union, Any

from vrp_toolkit.algorithms.base import VRPProblem


class PDPTWInstance(VRPProblem):
    """PDPTW problem instance with battery constraints.
    
    Represents a Pickup and Delivery Problem with Time Windows instance
    suitable for delivery robot routing with charging stations.
    
    Attributes:
        order_table (pd.DataFrame): DataFrame containing node information
        robot_speed (float): Robot speed in distance units per minute
        n (int): Total number of orders
        indices (List[int]): List of node IDs
        demands (List[float]): Demand for each node (positive for pickup, negative for delivery)
        time_windows (List[Tuple[float, float]]): Time windows for each node
        service_times (List[float]): Service time required at each node
        distance_matrix (np.ndarray): Distance matrix between nodes
        time_matrix (np.ndarray): Travel time matrix between nodes
        depot (Tuple[float, float]): Depot coordinates
        pickup_points (List[Tuple[float, float]]): Pickup point coordinates
        delivery_points (List[Tuple[float, float]]): Delivery point coordinates
        charging (Tuple[float, float]): Charging station coordinates
    """
    
    # Node type constants
    NODE_TYPE_DEPOT = 'depot'
    NODE_TYPE_PICKUP = 'cp'  # customer pickup
    NODE_TYPE_DELIVERY = 'cd'  # customer delivery
    NODE_TYPE_CHARGING = 'charging'
    NODE_TYPE_DESTINATION = 'destination'
    
    # Default column names (can be overridden)
    COL_ID = 'ID'
    COL_TYPE = 'Type'
    COL_X = 'X'
    COL_Y = 'Y'
    COL_DEMAND = 'Demand'
    COL_START_TIME = 'StartTime'
    COL_END_TIME = 'EndTime'
    COL_SERVICE_TIME = 'ServiceTime'
    COL_PARTNER_ID = 'PartnerID'
    COL_REAL_INDEX = 'RealIndex'
    COL_REAL_TYPE = 'RealType'
    
    def __init__(
        self,
        order_table: pd.DataFrame,
        distance_matrix: np.ndarray,
        time_matrix: np.ndarray,
        robot_speed: float,
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """Initialize PDPTW instance from data.
        
        Args:
            order_table: DataFrame containing node information with columns for
                        ID, Type, coordinates, demand, time windows, etc.
            distance_matrix: Distance matrix between real indices
            time_matrix: Travel time matrix between real indices
            robot_speed: Robot speed in distance units per minute
            column_mapping: Optional dictionary mapping standard column names
                          to actual column names in order_table
        """
        # Set column mappings
        self._column_mapping = self._get_column_mapping(column_mapping)
        
        # Store inputs
        self.order_table = order_table.copy()
        self.robot_speed = robot_speed
        
        # Extract basic information
        self.indices = self.order_table[self._get_column('id')].tolist()
        # n = number of pickup-delivery pairs (count pickup nodes only)
        self.n = len(self.order_table[
            self.order_table[self._get_column('type')] == self.NODE_TYPE_PICKUP
        ])
        
        # Extract derived data
        self.demands = self._extract_demands()
        self.time_windows = self._extract_time_windows()
        self.service_times = self._extract_service_times()
        
        # Extract coordinates
        self.depot = self._extract_depot_coordinates()
        self.pickup_points = self._extract_pickup_coordinates()
        self.delivery_points = self._extract_delivery_coordinates()
        self.charging = self._extract_charging_coordinates()
        
        # Create mapped matrices for internal use
        self.distance_matrix = self._create_mapped_distance_matrix(distance_matrix)
        self.time_matrix = self._create_mapped_time_matrix(time_matrix)
    
    def _get_column_mapping(self, column_mapping: Optional[Dict[str, str]]) -> Dict[str, str]:
        """Get column mapping dictionary."""
        default_mapping = {
            'id': self.COL_ID,
            'type': self.COL_TYPE,
            'x': self.COL_X,
            'y': self.COL_Y,
            'demand': self.COL_DEMAND,
            'start_time': self.COL_START_TIME,
            'end_time': self.COL_END_TIME,
            'service_time': self.COL_SERVICE_TIME,
            'partner_id': self.COL_PARTNER_ID,
            'real_index': self.COL_REAL_INDEX,
            'real_type': self.COL_REAL_TYPE,
        }
        
        if column_mapping is None:
            return default_mapping
        
        # Merge with defaults
        merged = default_mapping.copy()
        for key, value in column_mapping.items():
            if key in merged:
                merged[key] = value
        return merged
    
    def _get_column(self, column_key: str) -> str:
        """Get actual column name from key."""
        return self._column_mapping.get(column_key, column_key)

    def _col(self, column_key: str) -> str:
        """Alias for _get_column for backward compatibility."""
        return self._get_column(column_key)

    @property
    def _col_mapping(self) -> Dict[str, str]:
        """Backward compatibility property."""
        # For compatibility with existing code expecting _col dictionary
        return {
            'ID': self._col('id'),
            'Type': self._col('type'),
            'X': self._col('x'),
            'Y': self._col('y'),
            'Demand': self._col('demand'),
            'StartTime': self._col('start_time'),
            'EndTime': self._col('end_time'),
            'ServiceTime': self._col('service_time'),
            'PartnerID': self._col('partner_id'),
            'RealIndex': self._col('real_index'),
            'RealType': self._col('real_type'),
        }
    
    def _extract_demands(self) -> List[float]:
        """Extract demand values for all nodes."""
        max_id = max(self.indices) if self.indices else 0
        demands = [0.0] * (max_id + 1)
        
        for _, row in self.order_table.iterrows():
            node_id = row[self._get_column('id')]
            demands[node_id] = row[self._get_column('demand')]
        
        return demands
    
    def _extract_time_windows(self) -> List[Tuple[float, float]]:
        """Extract time windows for all nodes."""
        max_id = max(self.indices) if self.indices else 0
        time_windows = [[0.0, float('inf')] for _ in range(max_id + 1)]
        
        for _, row in self.order_table.iterrows():
            node_id = row[self._get_column('id')]
            time_windows[node_id] = [
                row[self._get_column('start_time')],
                row[self._get_column('end_time')]
            ]
        
        return time_windows
    
    def _extract_service_times(self) -> List[float]:
        """Extract service times for all nodes."""
        max_id = max(self.indices) if self.indices else 0
        service_times = [0.0] * (max_id + 1)
        
        for _, row in self.order_table.iterrows():
            node_id = row[self._get_column('id')]
            service_times[node_id] = row[self._get_column('service_time')]
        
        return service_times
    
    def _create_mapped_distance_matrix(self, distance_matrix: np.ndarray) -> np.ndarray:
        """Create distance matrix mapped to internal ID space."""
        n = max(self.indices) + 1 if self.indices else 0
        mapped_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                # Get real indices from order_table
                real_i = self.order_table.loc[
                    self.order_table[self._get_column('id')] == i,
                    self._get_column('real_index')
                ].values[0]
                real_j = self.order_table.loc[
                    self.order_table[self._get_column('id')] == j,
                    self._get_column('real_index')
                ].values[0]
                
                mapped_matrix[i][j] = distance_matrix[real_i][real_j]
        
        return mapped_matrix
    
    def _create_mapped_time_matrix(self, time_matrix: np.ndarray) -> np.ndarray:
        """Create time matrix mapped to internal ID space."""
        n = max(self.indices) + 1 if self.indices else 0
        mapped_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                # Get real indices from order_table
                real_i = self.order_table.loc[
                    self.order_table[self._get_column('id')] == i,
                    self._get_column('real_index')
                ].values[0]
                real_j = self.order_table.loc[
                    self.order_table[self._get_column('id')] == j,
                    self._get_column('real_index')
                ].values[0]
                
                mapped_matrix[i][j] = time_matrix[real_i][real_j]
        
        return mapped_matrix
    
    def _extract_depot_coordinates(self) -> Tuple[float, float]:
        """Extract depot coordinates."""
        depot_row = self.order_table[
            self.order_table[self._get_column('type')] == self.NODE_TYPE_DEPOT
        ].iloc[0]
        return (depot_row[self._get_column('x')], depot_row[self._get_column('y')])
    
    def _extract_pickup_coordinates(self) -> List[Tuple[float, float]]:
        """Extract pickup point coordinates."""
        pickup_rows = self.order_table[
            self.order_table[self._col('type')] == self.NODE_TYPE_PICKUP
        ]
        return [
            (row[self._col('x')], row[self._col('y')])
            for _, row in pickup_rows.iterrows()
        ]
    
    def _extract_delivery_coordinates(self) -> List[Tuple[float, float]]:
        """Extract delivery point coordinates."""
        delivery_rows = self.order_table[
            self.order_table[self._col('type')] == self.NODE_TYPE_DELIVERY
        ]
        return [
            (row[self._col('x')], row[self._col('y')])
            for _, row in delivery_rows.iterrows()
        ]
    
    def _extract_charging_coordinates(self) -> Optional[Tuple[float, float]]:
        """Extract charging station coordinates (returns None if no charging station)."""
        charging_rows = self.order_table[
            self.order_table[self._col('type')] == self.NODE_TYPE_CHARGING
        ]
        if len(charging_rows) == 0:
            return None  # No charging station in this instance
        charging_row = charging_rows.iloc[0]
        return (charging_row[self._col('x')], charging_row[self._col('y')])
    
    # Compatibility methods for existing code
    def get_distance(self, i: int, j: int) -> float:
        """Get distance between nodes i and j."""
        return self.distance_matrix[i][j]

    def get_time(self, i: int, j: int) -> float:
        """Get travel time between nodes i and j."""
        return self.time_matrix[i][j]
    
    def get_demand(self, node_id: int) -> float:
        """Get demand for a node."""
        return self.demands[node_id] if node_id < len(self.demands) else 0.0
    
    def get_time_window(self, node_id: int) -> Tuple[float, float]:
        """Get time window for a node."""
        return self.time_windows[node_id] if node_id < len(self.time_windows) else (0.0, float('inf'))
    
    def get_service_time(self, node_id: int) -> float:
        """Get service time for a node."""
        return self.service_times[node_id] if node_id < len(self.service_times) else 0.0

    # VRPProblem interface implementation
    @property
    def num_nodes(self) -> int:
        """Number of nodes in the problem."""
        return max(self.indices) + 1 if self.indices else 0

    @property
    def num_orders(self) -> int:
        """Number of orders/requests in the problem."""
        return self.n

    @property
    def depot_index(self) -> int:
        """Index of the depot node."""
        return 0  # Assuming depot is always index 0

    # Bulk matrix access methods for algorithm efficiency
    def get_distance_matrix(self) -> np.ndarray:
        """Get full distance matrix for algorithms that need bulk access."""
        return self.distance_matrix

    def get_time_matrix(self) -> np.ndarray:
        """Get full time matrix for algorithms that need bulk access."""
        return self.time_matrix

    # Node-order mapping helper methods
    def get_pickup_node(self, order_id: int) -> int:
        """Get node index for pickup of given order.

        Assumes pickup nodes are 1-n and delivery nodes are n+1-2n.
        """
        return order_id  # Current assumption

    def get_delivery_node(self, order_id: int) -> int:
        """Get node index for delivery of given order.

        Assumes pickup nodes are 1-n and delivery nodes are n+1-2n.
        """
        return order_id + self.n  # Current assumption

    def __repr__(self) -> str:
        """String representation of the instance."""
        return f"PDPTWInstance(n={self.n}, nodes={len(self.indices)}, speed={self.robot_speed})"


class PDPTWSolution:
    """Solution for PDPTW problem with battery constraints.
    
    Represents a solution to a PDPTW instance with routes, battery constraints,
    capacity constraints, and pickup-delivery pairing constraints.
    
    Attributes:
        instance (PDPTWInstance): Problem instance
        vehicle_capacity (float): Vehicle capacity constraint
        battery_capacity (float): Battery capacity constraint
        battery_consume_rate (float): Battery consumption rate per unit time
        routes (List[List[int]]): List of routes for each vehicle
        penalty_unvisit (float): Penalty for unvisited requests
        penalty_delay (float): Penalty for delayed orders
        num_vehicles (int): Number of vehicles (length of routes)
        route_battery_levels (np.ndarray): Battery levels along routes
        route_capacity_levels (np.ndarray): Capacity levels along routes
        route_arrival_times (np.ndarray): Arrival times at nodes
        route_leave_times (np.ndarray): Leave times from nodes
        route_wait_times (np.ndarray): Wait times at nodes
        total_travel_times (np.ndarray): Total travel time per vehicle
        total_delay_times (np.ndarray): Total delay time per vehicle
        total_wait_times (np.ndarray): Total wait time per vehicle
        total_delay_orders (np.ndarray): Number of delayed orders per vehicle
        visited_requests (Set[int]): Set of visited request IDs
        unvisited_requests (Set[int]): Set of unvisited request IDs
        visited_pairs (List[Tuple[int, int]]): List of visited pickup-delivery pairs
        unvisited_pairs (List[Tuple[int, int]]): List of unvisited pickup-delivery pairs
    """
    
    def __init__(
        self,
        instance: PDPTWInstance,
        vehicle_capacity: float,
        battery_capacity: float,
        battery_consume_rate: float,
        routes: List[List[int]],
        penalty_unvisit: float = 1000.0,
        penalty_delay: float = 100.0
    ):
        """Initialize PDPTWSolution object.
        
        Args:
            instance: PDPTWInstance object
            vehicle_capacity: Vehicle capacity constraint
            battery_capacity: Battery capacity constraint
            battery_consume_rate: Battery consumption rate per unit time
            routes: List of routes for each vehicle
            penalty_unvisit: Penalty for unvisited requests (default: 1000.0)
            penalty_delay: Penalty for delayed orders (default: 100.0)
        """
        # Unchanged parameters within the same instance
        self.instance = instance
        ## penalty
        self.penalty_unvisit = penalty_unvisit
        self.penalty_delay = penalty_delay
        ## constraints
        self.vehicle_capacity = vehicle_capacity
        self.battery_capacity = battery_capacity
        self.battery_consume_rate = battery_consume_rate
        ## main data structure
        self.routes = routes
        self.num_vehicles = len(routes)

        # Need to be initialized based on the new routes
        # battery and capacity
        self.route_battery_levels = np.empty((self.num_vehicles,), dtype=object)
        self.route_capacity_levels = np.empty((self.num_vehicles,), dtype=object)
        # time
        self.route_arrival_times = np.empty((self.num_vehicles,), dtype=object)
        self.route_leave_times = np.empty((self.num_vehicles,), dtype=object)
        self.route_wait_times = np.empty((self.num_vehicles,), dtype=object)
        # evaluation
        self.total_travel_times = np.zeros((self.num_vehicles,))
        self.total_delay_times = np.zeros((self.num_vehicles,))
        self.total_wait_times = np.zeros((self.num_vehicles,))
        self.total_delay_orders = np.zeros((self.num_vehicles,))
        # visited record
        self.visited_requests = set()
        self.unvisited_requests = set()
        self.unvisited_pairs = []
        self.visited_pairs = []

        self.initialize_routes()
        self.calculate_all()
        self.update_visit_record()

    def update_all(self):
        """Update all related attributes."""
        self.initialize_routes()
        self.calculate_all()
        self.update_visit_record()

    def initialize_routes(self):
        """Initialize route-related variables."""
        for vehicle_id in range(self.num_vehicles):
            route = self.routes[vehicle_id]
            self.route_battery_levels[vehicle_id] = np.zeros((len(route),))
            self.route_capacity_levels[vehicle_id] = np.zeros((len(route),))
            self.route_arrival_times[vehicle_id] = np.zeros((len(route),))
            self.route_leave_times[vehicle_id] = np.zeros((len(route),))
            self.route_wait_times[vehicle_id] = np.zeros((len(route),))

    def calculate_all(self):
        """Calculate all state variables and objective function value."""
        for vehicle_id in range(self.num_vehicles):
            self.calculate_battery_capacity_levels(vehicle_id)
            self.calculate_arrival_leave_wait_times(vehicle_id)
            self.calculate_travel_delay_wait_times(vehicle_id)

    def update_visit_record(self):
        """Update unserved requests."""
        visited_requests = set()
        for route in self.routes:
            for node in route:
                if node != 0:  # Ignore depot
                    if node <= self.instance.n:
                        visited_requests.add(node)
                    else:
                        visited_requests.add(node - self.instance.n)
        all_requests = set(range(1, self.instance.n + 1))
        unvisited_requests = all_requests - visited_requests
        # update
        self.visited_requests = visited_requests
        self.unvisited_requests = unvisited_requests
        self.visited_pairs = [(node, node + self.instance.n) for node in visited_requests]
        self.unvisited_pairs = [(node, node + self.instance.n) for node in unvisited_requests]

    def calculate_battery_capacity_levels(self, vehicle_id: int):
        """
        Calculate battery and capacity levels for each node on the route.
        
        Args:
            vehicle_id: Vehicle ID
        """
        route = self.routes[vehicle_id]
        battery_levels = self.route_battery_levels[vehicle_id]
        capacity_levels = self.route_capacity_levels[vehicle_id]
        time_matrix = self.instance.time_matrix

        battery_levels[0] = self.battery_capacity
        capacity_levels[0] = 0

        for i in range(1, len(route)):
            prev_node = route[i - 1]
            curr_node = route[i]
            # update the battery
            time = time_matrix[prev_node][curr_node]
            if curr_node == 0 and i != len(route) - 1:
                battery_levels[i] = self.battery_capacity
            else:
                battery_levels[i] = battery_levels[i - 1] - time * self.battery_consume_rate
            # update the capacity
            capacity_levels[i] = capacity_levels[i - 1] + self.instance.demands[curr_node]

    def calculate_arrival_leave_wait_times(self, vehicle_id: int):
        """
        Calculate arrival, leave, and wait times for each node on the route.
        
        Args:
            vehicle_id: Vehicle ID
        """
        route = self.routes[vehicle_id]
        arrival_times = self.route_arrival_times[vehicle_id]
        leave_times = self.route_leave_times[vehicle_id]
        wait_times = self.route_wait_times[vehicle_id]
        time_matrix = self.instance.time_matrix

        arrival_times[0] = 0
        wait_times[0] = 0
        leave_times[0] = self.instance.service_times[route[0]]
        # leave_times[0] = 0

        for i in range(1, len(route)):
            prev_node = route[i - 1]
            curr_node = route[i]
            arrival_times[i] = leave_times[i - 1] + time_matrix[prev_node][curr_node]
            wait_times[i] = max(0, self.instance.time_windows[curr_node][0] - arrival_times[i])
            if arrival_times[i] > self.instance.time_windows[curr_node][0]:
                wait_times[i] = 0
            leave_times[i] = arrival_times[i] + wait_times[i] + self.instance.service_times[curr_node]

    def calculate_travel_delay_wait_times(self, vehicle_id: int):
        """
        Calculate total travel time, delay time, and wait time for the vehicle.
        
        Args:
            vehicle_id: Vehicle ID
        """
        route = self.routes[vehicle_id]
        leave_times = self.route_leave_times[vehicle_id]
        arrival_times = self.route_arrival_times[vehicle_id]
        wait_times = self.route_wait_times[vehicle_id]
        time_matrix = self.instance.time_matrix

        travel_time = 0
        delay_time = 0
        wait_time = 0
        delay_count = 0

        for i in range(len(route) - 1):
            curr_node = route[i]
            next_node = route[i + 1]
            travel_time += time_matrix[curr_node][next_node]

            if self.instance.time_windows[curr_node][1] != float('inf'):
                # delay_time += max(0, leave_times[i] - self.instance.time_windows[next_node][1])
                if (self.instance.time_windows[curr_node][1] - arrival_times[i]) < 0:
                    delay_count += 1
                    # if arrival_times[i] > self.instance.time_window[curr_node][1]:
            #     delay_count += 1

            wait_time += wait_times[i]

        self.total_travel_times[vehicle_id] = travel_time
        self.total_delay_times[vehicle_id] = delay_time
        self.total_wait_times[vehicle_id] = wait_time
        self.total_delay_orders[vehicle_id] = delay_count

    # ================================ objective function ================================
    def objective_function(self) -> float:
        """
        Calculate objective function value.
        
        Returns:
            Objective function value (total travel time + total delay time + penalties)
        """
        unvisited_penalty = len(self.unvisited_requests) * self.penalty_unvisit
        late_penalty = np.sum(self.total_delay_orders) * self.penalty_delay
        # return np.sum(self.total_travel_times) + np.sum(self.total_delay_times) + unvisited_penalty
        return np.sum(self.total_travel_times) / 60 * self.instance.robot_speed + late_penalty + unvisited_penalty

    # ================================ feasibility check ================================
    def is_feasible(self) -> bool:
        """
        Check solution feasibility.
        
        Returns:
            True if solution is feasible, False otherwise
        """
        selected_vehicles = self.get_selected_vehicles()
        if not selected_vehicles:
            return False
        if not self.check_capacity_constraint(selected_vehicles):
            return False
        if not self.check_battery_constraint(selected_vehicles):
            return False
        if not self.check_pickup_delivery_order(selected_vehicles):
            return False
        return True

    def get_selected_vehicles(self) -> List[int]:
        """
        Get list of selected vehicle IDs.
        
        Returns:
            List of selected vehicle IDs
        """
        selected_vehicles = []
        for vehicle_id in range(self.num_vehicles):
            if len(self.routes[vehicle_id]) > 2:
                selected_vehicles.append(vehicle_id)
        return selected_vehicles

    def check_capacity_constraint(self, selected_vehicles: List[int]) -> bool:
        """
        Check capacity constraint.
        
        Args:
            selected_vehicles: List of selected vehicle IDs
            
        Returns:
            True if capacity constraint satisfied, False otherwise
        """
        for vehicle_id in selected_vehicles:
            if np.any(self.route_capacity_levels[vehicle_id] > self.vehicle_capacity):
                return False
        return True

    def check_battery_constraint(self, selected_vehicles: List[int]) -> bool:
        """
        Check battery constraint.
        
        Args:
            selected_vehicles: List of selected vehicle IDs
            
        Returns:
            True if battery constraint satisfied, False otherwise
        """
        for vehicle_id in selected_vehicles:
            if np.any(self.route_battery_levels[vehicle_id] < 0):
                return False
        return True

    def check_pickup_delivery_order(self, selected_vehicles: List[int]) -> bool:
        """
        Check pickup-delivery order constraint.
        
        Args:
            selected_vehicles: List of selected vehicle IDs
            
        Returns:
            True if pickup-delivery order constraint satisfied, False otherwise
        """
        for vehicle_id in selected_vehicles:
            route = self.routes[vehicle_id]
            visited_pickups = set()
            for node in route:
                if 1 <= node <= self.instance.n:
                    visited_pickups.add(node)
                elif self.instance.n < node <= 2 * self.instance.n:
                    if node - self.instance.n not in visited_pickups:
                        return False
        return True

    # ================================ plot ================================
    def plot_solution(self, vehicle_ids=None):
        """
        Plot solution routes.
        
        Args:
            vehicle_ids: List of vehicle IDs to plot (optional, default: all selected vehicles)
        """
        # Import here to avoid matplotlib dependency if not plotting
        import matplotlib.pyplot as plt
        from collections import defaultdict
        
        selected_vehicles = self.get_selected_vehicles()
        if not selected_vehicles:
            print("No vehicle is selected in the solution.")
            return

        if vehicle_ids is None:
            vehicle_ids = selected_vehicles
        else:
            vehicle_ids = [vehicle_id for vehicle_id in vehicle_ids if vehicle_id in selected_vehicles]

        if not vehicle_ids:
            print("No valid vehicle IDs provided.")
            return

        plt.figure(figsize=(12, 10))

        # Create a dictionary to store all order IDs for each location
        location_orders = defaultdict(list)

        # Fill location_orders dictionary
        for order_id in range(1, self.instance.n + 1):
            pickup_coord = self.instance.pickup_points[order_id - 1]
            delivery_coord = self.instance.delivery_points[order_id - 1]
            location_orders[pickup_coord].append(f"P{order_id}")
            location_orders[delivery_coord].append(f"D{order_id}")

        # Plot nodes
        plt.scatter(self.instance.depot[0], self.instance.depot[1], c='red', marker='s', s=100, label='Depot')
        plt.scatter([p[0] for p in self.instance.pickup_points], [p[1] for p in self.instance.pickup_points], c='blue',
                    marker='o', s=100, label='Pickup')
        plt.scatter([d[0] for d in self.instance.delivery_points], [d[1] for d in self.instance.delivery_points],
                    c='green', marker='d', s=100, label='Delivery')

        if self.instance.charging != self.instance.depot:
            plt.scatter(self.instance.charging[0], self.instance.charging[1], c='purple', marker='^', s=100,
                        label='Charging Station')

        # Add labels
        plt.annotate('Depot', (self.instance.depot[0], self.instance.depot[1]), textcoords='offset points',
                     xytext=(0, 10), ha='center')

        for location, orders in location_orders.items():
            label = ', '.join(orders)
            plt.annotate(f"[{label}]", (location[0], location[1]), textcoords='offset points', xytext=(0, 5),
                         ha='center', fontsize=8)

        # Plot routes
        color_map = plt.cm.get_cmap('viridis', len(vehicle_ids))
        for i, vehicle_id in enumerate(vehicle_ids):
            route = self.routes[vehicle_id]
            color = color_map(i)

            route_points = [self.instance.depot]
            for node in route[1:-1]:
                if node <= self.instance.n:
                    route_points.append(self.instance.pickup_points[node - 1])
                elif node <= 2 * self.instance.n:
                    route_points.append(self.instance.delivery_points[node - self.instance.n - 1])
                else:
                    route_points.append(self.instance.charging)
            route_points.append(self.instance.depot)

            route_x = [point[0] for point in route_points]
            route_y = [point[1] for point in route_points]

            plt.plot(route_x, route_y, color=color, linestyle='-', linewidth=1.5, alpha=0.8,
                     label=f'Vehicle {vehicle_id + 1}')

        plt.xlabel('X coordinate')
        plt.ylabel('Y coordinate')
        plt.title('PDPTW Solution')
        plt.legend(loc='best')
        plt.grid(True)
        plt.show()
