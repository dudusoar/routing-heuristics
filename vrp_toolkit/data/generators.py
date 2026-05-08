"""Data generators for VRP problems.

This module contains classes for generating synthetic and real-world data
for Vehicle Routing Problems (VRP), including PDPTW instances.
"""

import math
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from collections import defaultdict

# Constants for PDPTW data generation
# These match the constants defined in PDPTWInstance for compatibility
NODE_TYPE_DEPOT = 'depot'
NODE_TYPE_PICKUP = 'cp'  # customer pickup
NODE_TYPE_DELIVERY = 'cd'  # customer delivery
NODE_TYPE_CHARGING = 'charging'
NODE_TYPE_DESTINATION = 'destination'

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

# Default column order for generated order table
DEFAULT_COLUMNS = [
    COL_ID, COL_TYPE, COL_X, COL_Y, COL_DEMAND,
    COL_START_TIME, COL_END_TIME, COL_SERVICE_TIME,
    COL_PARTNER_ID, COL_REAL_INDEX, COL_REAL_TYPE
]


class OrderGenerator:
    """Generate PDPTW order table from demand data and map information.
    
    This class takes demand information and real-world map data to generate
    a complete order table suitable for creating PDPTWInstance objects.
    
    Attributes:
        real_map: RealMap object containing map data (coordinates, distance matrix, etc.)
        demand_table: DataFrame with demand information per time interval
        time_window_length: Length of delivery time windows in minutes
        service_time: Service time required at each node in minutes
        extra_time: Extra buffer time added to delivery start time
        big_time: Large value representing infinity for time windows
        robot_speed: Robot speed in distance units per minute
        total_number_orders: Total number of orders generated
        time_matrix: Travel time matrix between nodes in minutes
        order_table: Generated order table DataFrame
    """
    
    # Node type mappings (use module-level constants)
    NODE_TYPE_PICKUP = NODE_TYPE_PICKUP
    NODE_TYPE_DELIVERY = NODE_TYPE_DELIVERY
    NODE_TYPE_DEPOT = NODE_TYPE_DEPOT
    NODE_TYPE_DESTINATION = NODE_TYPE_DESTINATION
    NODE_TYPE_CHARGING = NODE_TYPE_CHARGING
    
    def __init__(
        self,
        real_map,
        demand_table: pd.DataFrame,
        time_params: Dict[str, int],
        robot_speed: float,
        column_mapping: Optional[Dict[str, str]] = None
    ):
        """Initialize the OrderGenerator.
        
        Args:
            real_map: RealMap object containing map data (coordinates, distance matrix, node types)
            demand_table: DataFrame with demand information per time interval
            time_params: Dictionary containing time-related parameters:
                - time_window_length: Length of delivery time windows in minutes
                - service_time: Service time required at each node in minutes  
                - extra_time: Extra buffer time added to delivery start time
                - big_time: Large value representing infinity for time windows
            robot_speed: Robot speed in distance units per minute
            column_mapping: Optional dictionary mapping standard column names to
                          actual column names in demand_table
        """
        # Store map data
        self.real_map = real_map
        self.real_coordinates = self.real_map.coordinates
        self.distance_matrix = self.real_map.distance_matrix
        self.node_type_dict = self.real_map.node_type_dict
        
        # Store demand data
        self.demand_table = demand_table
        
        # Extract time parameters
        self.time_window_length = time_params['time_window_length']
        self.service_time = time_params['service_time']
        self.extra_time = time_params['extra_time']
        self.big_time = time_params.get('big_time', 1000)  # Default to 1000 if not specified
        
        # Store robot speed
        self.robot_speed = robot_speed
        
        # Calculate derived properties
        self.total_number_orders = self.demand_table.iloc[:, 2:].sum().sum().astype(int)
        self.time_matrix = self._generate_time_matrix()
        self.order_table = self._generate_whole_table()
        
        # Apply column mapping if provided
        if column_mapping:
            self.order_table = self.order_table.rename(columns=column_mapping)
    
    def _generate_time_matrix(self) -> np.ndarray:
        """Generate time matrix in minutes.
        
        Returns:
            Time matrix where time_matrix[i][j] = travel time from node i to j in minutes
        """
        return (self.distance_matrix / self.robot_speed) * 60
    
    def _generate_whole_table(self) -> pd.DataFrame:
        """Generate the complete order table with all required information.
        
        Returns:
            DataFrame containing pickup, delivery, depot, destination, and charging station nodes
        """
        data: List[List] = []
        count: int = 0
        
        # Iterate over time intervals (columns starting from index 2)
        for j in range(2, self.demand_table.shape[1]):
            time_start: int = int(self.demand_table.columns[j].split('-')[0])
            
            # Iterate over restaurant-customer pairs (rows)
            for i in range(self.demand_table.shape[0]):
                orders_count: int = self.demand_table.iloc[i, j]
                
                if orders_count > 0:
                    pickup_real_index: int = self.demand_table.iloc[i, 0]
                    delivery_real_index: int = self.demand_table.iloc[i, 1]
                    
                    # Create one pickup and one delivery node for each order
                    for _ in range(orders_count):
                        count += 1
                        travel_time: float = self.time_matrix[pickup_real_index][delivery_real_index]
                        delivery_start_time: float = (
                            time_start + travel_time + self.service_time + self.extra_time
                        )
                        
                        # Add pickup entry
                        data.append(self._create_pickup_entry(
                            count, pickup_real_index, time_start
                        ))
                        
                        # Add delivery entry  
                        data.append(self._create_delivery_entry(
                            count, delivery_real_index, delivery_start_time
                        ))
        
        # Add special nodes (depot, destination, charging station)
        data.extend([
            self._create_depot_entry(),
            self._create_destination_entry(),
            self._create_charging_station_entry()
        ])
        
        # Create DataFrame and sort by ID
        df = pd.DataFrame(data, columns=DEFAULT_COLUMNS)
        return df.sort_values(by=COL_ID).reset_index(drop=True)
    
    def _create_pickup_entry(self, count: int, pickup_real_index: int, time_start: int) -> List:
        """Create entry for a pickup node.
        
        Args:
            count: Order ID
            pickup_real_index: Real index of pickup location
            time_start: Start time for the pickup
            
        Returns:
            List of values for the pickup node row
        """
        return [
            count,
            self.NODE_TYPE_PICKUP,
            self.real_coordinates[pickup_real_index][0],
            self.real_coordinates[pickup_real_index][1],
            1,  # Demand: +1 for pickup
            time_start,
            self.big_time,  # End time: big time (effectively no constraint)
            self.service_time,
            count + self.total_number_orders,  # Partner ID: corresponding delivery
            pickup_real_index,
            self.node_type_dict[pickup_real_index]
        ]
    
    def _create_delivery_entry(self, count: int, delivery_real_index: int, 
                              delivery_start_time: float) -> List:
        """Create entry for a delivery node.
        
        Args:
            count: Order ID
            delivery_real_index: Real index of delivery location
            delivery_start_time: Start time for the delivery
            
        Returns:
            List of values for the delivery node row
        """
        return [
            count + self.total_number_orders,
            self.NODE_TYPE_DELIVERY,
            self.real_coordinates[delivery_real_index][0],
            self.real_coordinates[delivery_real_index][1],
            -1,  # Demand: -1 for delivery
            delivery_start_time,
            delivery_start_time + self.time_window_length,
            self.service_time,
            count,  # Partner ID: corresponding pickup
            delivery_real_index,
            self.node_type_dict[delivery_real_index]
        ]
    
    def _create_depot_entry(self) -> List:
        """Create entry for depot node.
        
        Returns:
            List of values for the depot node row
        """
        depot_real_index = self.real_map.DEPOT_INDEX
        depot_coordinates = self.real_coordinates[depot_real_index]
        return [
            0,
            self.NODE_TYPE_DEPOT,
            depot_coordinates[0],
            depot_coordinates[1],
            0,  # Demand: 0 for depot
            0,  # Start time: 0
            self.big_time,  # End time: big time
            0,  # Service time: 0
            0,  # Partner ID: 0 (self)
            depot_real_index,
            self.node_type_dict[depot_real_index]
        ]
    
    def _create_destination_entry(self) -> List:
        """Create entry for destination node.
        
        Returns:
            List of values for the destination node row
        """
        destination_real_index = self.real_map.DESTINATION_INDEX
        destination_coordinates = self.real_coordinates[destination_real_index]
        return [
            self.total_number_orders * 2 + 1,
            self.NODE_TYPE_DESTINATION,
            destination_coordinates[0],
            destination_coordinates[1],
            0,  # Demand: 0 for destination
            0,  # Start time: 0
            self.big_time,  # End time: big time
            0,  # Service time: 0
            self.total_number_orders * 2 + 1,  # Partner ID: self
            destination_real_index,
            self.node_type_dict[destination_real_index]
        ]
    
    def _create_charging_station_entry(self) -> List:
        """Create entry for charging station node.
        
        Returns:
            List of values for the charging station node row
        """
        charging_station_real_index = self.real_map.CHARGING_STATION_INDEX
        charging_station_coordinates = self.real_coordinates[charging_station_real_index]
        return [
            self.total_number_orders * 2 + 2,
            self.NODE_TYPE_CHARGING,
            charging_station_coordinates[0],
            charging_station_coordinates[1],
            0,  # Demand: 0 for charging station
            0,  # Start time: 0
            self.big_time,  # End time: big time
            0,  # Service time: 0
            self.total_number_orders * 2 + 2,  # Partner ID: self
            charging_station_real_index,
            self.node_type_dict[charging_station_real_index]
        ]
    
    def get_order_table(self) -> pd.DataFrame:
        """Get the generated order table.

        Returns:
            Generated order table DataFrame
        """
        return self.order_table.copy()

class DemandGenerator:
    """Generate demand data for VRP problems.

    This class generates synthetic demand data for restaurant-customer pairs
    across time intervals, suitable for use with OrderGenerator.

    Attributes:
        time_range: Total time range in minutes
        time_step: Step size for each time interval in minutes
        restaurants: List of restaurant indices
        customers: List of customer indices
        sample_dist: Function for sampling number of pairs per time interval
        sample_params: Parameters for sample_dist function
        demand_dist: Function for generating order quantities per pair
        demand_params: Parameters for demand_dist function
        time_intervals: List of time interval tuples (start, end)
        pairs: List of restaurant-customer pairs
        demand_table: Generated demand table DataFrame
    """

    def __init__(
        self, 
        time_range: int, 
        time_step: int, 
        restaurants: List[int], 
        customers: List[int], 
        random_params: Dict
    ):
        """Initialize the DemandGenerator instance and generate the demand table.
        
        Args:
            time_range: Total time range in minutes
            time_step: Step size for each time interval in minutes
            restaurants: List of restaurant indices
            customers: List of customer indices
            random_params: Dictionary containing random functions and their parameters:
                - sample_dist: Function for sampling number of pairs per time interval
                - sample_params: Parameters for sample_dist function
                - demand_dist: Function for generating order quantities per pair
                - demand_params: Parameters for demand_dist function
        """
        self.time_range = time_range
        self.time_step = time_step
        self.restaurants = restaurants
        self.customers = customers
        
        self.sample_dist: Callable = random_params['sample_dist']['function']
        self.sample_params: Dict = random_params['sample_dist']['params']
        self.demand_dist: Callable = random_params['demand_dist']['function']
        self.demand_params: Dict = random_params['demand_dist']['params']
        
        self.time_intervals: List[Tuple[int, int]] = self._generate_time_intervals()
        self.pairs: List[Tuple[int, int]] = self._generate_pairs()
        self.demand_table: pd.DataFrame = self._generate_demand_table()
    
    def _generate_time_intervals(self) -> List[Tuple[int, int]]:
        """Generate time intervals.
        
        Returns:
            List of (start, end) tuples for each time interval
        """
        return [
            (i, min(i + self.time_step, self.time_range)) 
            for i in range(0, self.time_range, self.time_step)
        ]
    
    def _generate_pairs(self) -> List[Tuple[int, int]]:
        """Generate all restaurant-customer pairs.
        
        Returns:
            List of (restaurant_index, customer_index) tuples
        """
        return [(r, c) for r in self.restaurants for c in self.customers]
    
    def _generate_demand_table(self) -> pd.DataFrame:
        """Generate the demand table with additional columns for pickup and delivery points.
        
        Returns:
            DataFrame with columns: Pickup, Delivery, and time interval columns
        """
        demand_dict = {
            pair: np.zeros(len(self.time_intervals), dtype=int) 
            for pair in self.pairs
        }
        
        for idx in range(len(self.time_intervals)):
            num_samples = self.sample_dist(**self.sample_params)
            sampled_pairs = np.random.choice(
                len(self.pairs), size=num_samples, replace=True
            )
            
            for sample in sampled_pairs:
                pair = self.pairs[sample]
                order_quantity = max(0, self.demand_dist(**self.demand_params))
                demand_dict[pair][idx] += order_quantity
        
        # Create DataFrame with time intervals as columns
        demand_table = pd.DataFrame(
            demand_dict, 
            index=[f"{start}-{end}" for start, end in self.time_intervals]
        ).T
        
        # Add pickup and delivery columns
        demand_table['Pickup'] = [pair[0] for pair in self.pairs]
        demand_table['Delivery'] = [pair[1] for pair in self.pairs]
        
        # Reorder columns: Pickup, Delivery, then time intervals
        cols = ['Pickup', 'Delivery'] + [
            col for col in demand_table.columns if col not in ['Pickup', 'Delivery']
        ]
        demand_table = demand_table[cols]
        
        return demand_table.reset_index(drop=True).rename_axis(None)
    
    def get_demand_table(self) -> pd.DataFrame:
        """Return the generated demand table.
        
        Returns:
            Generated demand table DataFrame
        """
        return self.demand_table.copy()
    
    def plot_demand_heatmap(self):
        """Plot a heatmap of the demand table.

        Shows demand intensity across restaurant-customer pairs and time intervals.
        """
        import matplotlib.pyplot as plt
        import seaborn as sns

        plt.figure(figsize=(12, 8))
        sns.heatmap(self.demand_table.iloc[:, 2:], cmap="YlOrRd", annot=True, fmt="d")
        plt.title("Demand Heatmap")
        plt.xlabel("Time Intervals")
        plt.ylabel("Restaurant-Customer Pairs")
        plt.show()
