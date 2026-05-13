"""
Map data representation for VRP problems.

This module provides classes for representing maps with nodes (restaurants, customers,
depots, charging stations) and distance matrices. It includes both synthetic map
generation (RealMap) and real-world data loading (RealDataMap).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List, Tuple, Callable, Optional, Any


class RealMap:
    """
    Represents a synthetic map with restaurants, customers, and other nodes.
    
    This class generates random coordinates for nodes and computes Euclidean
    distances between them, creating a complete map representation suitable
    for VRP problem instances.
    
    Attributes:
        N_R (int): Number of restaurants
        N_C (int): Number of customers  
        n (int): Total number of restaurants + customers
        DEPOT_INDEX (int): Index of depot node (always 0)
        DESTINATION_INDEX (int): Index of destination node (n + 1)
        CHARGING_STATION_INDEX (int): Index of charging station node (n + 2)
        all_nodes (List[int]): List of all node indices
        restaurants (List[int]): List of restaurant node indices
        customers (List[int]): List of customer node indices
        coordinates (Dict[int, Tuple[float, float]]): Node coordinates
        distance_matrix (np.ndarray): Distance matrix between all nodes
        node_type_dict (Dict[int, str]): Mapping of node indices to types
    """
    
    def __init__(self, n_r: int, n_c: int, dist_function: Callable, dist_params: Dict):
        """
        Initialize the RealMap instance.

        Args:
            n_r (int): Number of restaurants
            n_c (int): Number of customers
            dist_function (Callable): Distribution function for generating coordinates
            dist_params (Dict): Parameters for the distribution function
        """
        # number counts
        self.N_R = n_r
        self.N_C = n_c
        self.n = self.N_R + self.N_C

        # index list
        self.DEPOT_INDEX = 0
        self.DESTINATION_INDEX = self.n + 1
        self.CHARGING_STATION_INDEX = self.n + 2
        self.all_nodes: List[int] = [self.DEPOT_INDEX] + list(range(1, self.n + 1)) + [self.DESTINATION_INDEX, self.CHARGING_STATION_INDEX]
        self.restaurants: List[int] = list(range(1, self.N_R + 1))
        self.customers: List[int] = list(range(self.N_R + 1, self.n + 1))

        # other properties
        self.coordinates: Dict[int, Tuple[float, float]] = self._generate_coordinates(dist_function, dist_params)
        self.distance_matrix: np.ndarray = self._generate_distance_matrix()
        self.node_type_dict: Dict[int, str] = self._generate_node_type()

    def _generate_coordinates(self, dist_function: Callable, dist_params: Dict) -> Dict[int, Tuple[float, float]]:
        """
        Generate random coordinates for all nodes.

        Args:
            dist_function (Callable): Distribution function for generating coordinates
            dist_params (Dict): Parameters for the distribution function

        Returns:
            Dict[int, Tuple[float, float]]: Dictionary of node indices to coordinates
        """
        coordinates = {node: (dist_function(**dist_params), dist_function(**dist_params)) for node in self.all_nodes[:self.n + 1]}
        coordinates[self.DESTINATION_INDEX] = coordinates[self.DEPOT_INDEX]
        coordinates[self.CHARGING_STATION_INDEX] = coordinates[self.DEPOT_INDEX]
        return coordinates

    def _generate_distance_matrix(self) -> np.ndarray:
        """
        Calculate the distance matrix based on Euclidean distance between nodes.

        Returns:
            np.ndarray: Distance matrix
        """
        coords = np.array([self.coordinates[i] for i in self.all_nodes])
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        return np.sqrt(np.sum(diff**2, axis=-1))

    def _generate_node_type(self) -> Dict[int, str]:
        """
        Generate a dictionary mapping node indices to their types.

        Returns:
            Dict[int, str]: Dictionary of node indices to node types
        """
        return {
            self.DEPOT_INDEX: 'depot',
            self.DESTINATION_INDEX: 'destination',
            self.CHARGING_STATION_INDEX: 'charging_station',
            **{i: 'restaurant' for i in self.restaurants},
            **{i: 'customer' for i in self.customers}
        }

    def plot_map(self, show_index: bool = True):
        """
        Plot the map with all nodes.

        Args:
            show_index (bool): Whether to show node indices on the plot
        """
        plt.figure(figsize=(10, 10))
        colors = {'depot': 'red', 'destination': 'red', 'charging_station': 'green',
                  'restaurant': 'blue', 'customer': 'orange'}

        for node, (x, y) in self.coordinates.items():
            node_type = self.node_type_dict[node]
            plt.scatter(x, y, c=colors[node_type], s=100)
            if show_index:
                plt.annotate(str(node), (x, y), xytext=(5, 5), textcoords='offset points')

        plt.title("Real Map")
        plt.xlabel("X coordinate")
        plt.ylabel("Y coordinate")
        plt.legend(colors.keys())
        plt.grid(True)
        plt.show()


class RealDataMap:
    """
    Represents a real-world map loaded from data files.
    
    This class loads node information and travel time matrices from CSV files,
    creating a map representation with actual geographic coordinates and
    realistic travel distances.
    
    Attributes:
        node_data (pd.DataFrame): DataFrame containing node information
        tt_matrix (np.ndarray): Travel time matrix between nodes
        N_R (int): Number of restaurants
        N_C (int): Number of customers
        n (int): Total number of restaurants + customers
        DEPOT_INDEX (int): Index of depot node
        DESTINATION_INDEX (int): Index of destination node
        CHARGING_STATION_INDEX (int): Index of charging station node
        all_nodes (List[int]): List of all node indices
        restaurants (List[int]): List of restaurant node indices
        customers (List[int]): List of customer node indices
        coordinates (Dict[int, Tuple[float, float]]): Node coordinates (longitude, latitude)
        distance_matrix (np.ndarray): Distance matrix (same as tt_matrix)
        node_type_dict (Dict[int, str]): Mapping of node indices to types
    """
    
    def __init__(self, node_file: str, tt_matrix_file: str, 
                 depot_index: int = 15,
                 destination_index: Optional[int] = None,
                 charging_station_index: Optional[int] = None,
                 distance_conversion_factor: Optional[float] = 1609.34,
                 customer_types: List[str] = ["apartment", "university building"]):
        """
        Initialize the RealDataMap instance.
        
        Args:
            node_file (str): Path to CSV file containing node information
            tt_matrix_file (str): Path to CSV file containing travel time matrix
            depot_index (int, optional): Index of depot node. Defaults to 15.
            destination_index (Optional[int], optional): Index of destination node.
                If None, defaults to depot_index. Defaults to None.
            charging_station_index (Optional[int], optional): Index of charging station node.
                If None, defaults to depot_index. Defaults to None.
            distance_conversion_factor (Optional[float], optional): Conversion factor from
                input units to desired output units. For meters to miles, use 1609.34.
                If None, no conversion is applied. Defaults to 1609.34.
            customer_types (List[str], optional): List of node types considered as customers.
                Defaults to ["apartment", "university building"].
        """
        self.node_data = self._load_node_data(node_file)
        self.tt_matrix = self._load_tt_matrix(tt_matrix_file, distance_conversion_factor)
        
        self.N_R = len(self.node_data[self.node_data['type'] == 'restaurant'])
        self.N_C = len(self.node_data[self.node_data['type'].isin(customer_types)])
        self.n = self.N_R + self.N_C

        self.DEPOT_INDEX = depot_index
        self.DESTINATION_INDEX = destination_index if destination_index is not None else depot_index
        self.CHARGING_STATION_INDEX = charging_station_index if charging_station_index is not None else depot_index

        self.all_nodes = list(range(len(self.node_data)))
        self.restaurants = list(self.node_data[self.node_data['type'] == 'restaurant'].index)
        self.customers = list(self.node_data[self.node_data['type'].isin(customer_types)].index)

        self.coordinates = self._generate_coordinates()
        self.distance_matrix = self.tt_matrix  # For compatibility with RealMap interface
        self.node_type_dict = self._generate_node_type()
        
        # Store configuration
        self.customer_types = customer_types
        self.distance_conversion_factor = distance_conversion_factor

    def _load_node_data(self, file_path: str) -> pd.DataFrame:
        """
        Load node data from CSV file.
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            pd.DataFrame: DataFrame with node information, indexed by 'index'
        """
        df = pd.read_csv(file_path)
        return df.set_index('index')

    def _load_tt_matrix(self, file_path: str, conversion_factor: Optional[float]) -> np.ndarray:
        """
        Load travel time matrix from CSV file.
        
        Args:
            file_path (str): Path to CSV file
            conversion_factor (Optional[float]): Conversion factor from input units
                to desired output units. If None, no conversion is applied.
                
        Returns:
            np.ndarray: Travel time matrix in desired units
        """
        matrix_input = np.loadtxt(file_path, delimiter=',')
        if conversion_factor is not None:
            return matrix_input / conversion_factor
        return matrix_input

    def _generate_coordinates(self) -> Dict[int, Tuple[float, float]]:
        """
        Generate coordinates dictionary from node data.
        
        Returns:
            Dict[int, Tuple[float, float]]: Dictionary mapping node indices to
                (longitude, latitude) coordinates
        """
        return {index: (row['longitude'], row['latitude']) for index, row in self.node_data.iterrows()}

    def _generate_node_type(self) -> Dict[int, str]:
        """
        Generate node type dictionary from node data.
        
        Returns:
            Dict[int, str]: Dictionary mapping node indices to node types
        """
        return dict(zip(self.node_data.index, self.node_data['type']))

    def plot_map(self, show_index: bool = True, show_legend: bool = True, 
                 figsize: Tuple[int, int] = (15, 15), 
                 node_size: int = 50, 
                 font_size: int = 8,
                 highlight_depot: bool = True,
                 colors: Optional[Dict[str, str]] = None):
        """
        Plot the map with all nodes.
        
        Args:
            show_index (bool, optional): Whether to show node indices on the plot.
                Defaults to True.
            show_legend (bool, optional): Whether to show legend. Defaults to True.
            figsize (Tuple[int, int], optional): Figure size. Defaults to (15, 15).
            node_size (int, optional): Node size. Defaults to 50.
            font_size (int, optional): Font size for annotations. Defaults to 8.
            highlight_depot (bool, optional): Whether to highlight depot with special marker.
                Defaults to True.
            colors (Optional[Dict[str, str]], optional): Custom color mapping for node types.
                If None, uses default colors. Defaults to None.
        """
        if colors is None:
            colors = {
                'restaurant': 'red',
                'apartment': 'blue',
                'university building': 'green'
            }
        
        plt.figure(figsize=figsize)
        
        for node_type, group in self.node_data.groupby('type'):
            plt.scatter(group['longitude'], group['latitude'], 
                        c=colors.get(node_type, 'gray'), 
                        label=node_type, s=node_size, alpha=0.7)

        if highlight_depot:
            depot_node = self.node_data.loc[self.DEPOT_INDEX]
            plt.scatter(depot_node['longitude'], depot_node['latitude'], 
                        c='yellow', s=node_size*4, marker='*', 
                        edgecolors='black', linewidth=1, label='Depot')

        if show_index:
            for idx, row in self.node_data.iterrows():
                plt.annotate(str(idx), (row['longitude'], row['latitude']), 
                             xytext=(3, 3), textcoords='offset points', 
                             fontsize=font_size)

        plt.title("Real Data Map", fontsize=font_size*2)
        plt.xlabel("Longitude", fontsize=font_size*1.5)
        plt.ylabel("Latitude", fontsize=font_size*1.5)
        
        if show_legend:
            plt.legend(fontsize=font_size)
        
        plt.grid(True)
        plt.tight_layout()
        plt.show()


if __name__ == '__main__':
    # === test real map
    # real_map = RealMap(n_r=2, n_c=4, dist_function=np.random.uniform, dist_params={'low': -1, 'high': 1})
    # print(f"All nodes: {real_map.all_nodes}")
    # print(f"Number of coordinates: {len(real_map.coordinates)}")
    # real_map.plot_map(show_index=True)
    # print(real_map.restaurants)
    # print(real_map.customers)
    
    # === test real data map
    import os
    print("Current working directory:", os.getcwd())
    print("Files in the current directory:", os.listdir())

    # Get current script directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Build full file paths
    node_file = os.path.join(current_dir, 'data/purdue_node_info.csv')
    tt_matrix_file = os.path.join(current_dir, 'data/tt_matrix.csv')

    print(f"Attempting to load files:")
    print(f"Node file: {node_file}")
    print(f"TT matrix file: {tt_matrix_file}")

    real_data_map = RealDataMap(node_file, tt_matrix_file)
    print(f"Number of restaurants: {real_data_map.N_R}")
    print(f"Number of customers: {real_data_map.N_C}")
    print(f"Total number of nodes: {len(real_data_map.all_nodes)}")
    print(f"Number of customer nodes: {len(real_data_map.customers)}")
    print(f"Depot index: {real_data_map.DEPOT_INDEX}")
    print(f"Depot info: {real_data_map.node_data.loc[real_data_map.DEPOT_INDEX].to_dict()}")
    
    print(real_data_map.restaurants)
    print(real_data_map.customers)
    # Plot with default parameters
    real_data_map.plot_map()
