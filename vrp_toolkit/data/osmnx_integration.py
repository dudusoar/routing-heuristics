"""
OSMnx integration for real-world street network VRP instances.

This module provides utilities to integrate OpenStreetMap street networks
into VRP problem instances using OSMnx. It allows creating PDPTW instances
based on real-world geographic data with network-based distances.

Key features:
- Load street networks by place name or bounding box
- Map coordinates to network nodes
- Compute network-based distance and time matrices
- Create PDPTW instances from real locations
- Visualize routes on actual street maps
"""

import osmnx as ox
import networkx as nx
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import List, Tuple, Dict, Optional, Union
import pickle
import os


class OSMnxNetworkLoader:
    """
    Load and manage OpenStreetMap street networks for VRP problems.

    This class handles downloading, caching, and processing street networks
    from OpenStreetMap using OSMnx.

    Attributes:
        G: NetworkX graph representing the street network
        place_name: Name of the place (if loaded by name)
        bbox: Bounding box coordinates (if loaded by bbox)
        network_type: Type of network ('drive', 'walk', 'bike', or 'all')
    """

    def __init__(self):
        """Initialize the network loader."""
        self.G = None
        self.place_name = None
        self.bbox = None
        self.network_type = None

    def load_by_place(
        self,
        place_name: str,
        network_type: str = 'drive',
        simplify: bool = True,
        cache_file: Optional[str] = None
    ) -> nx.MultiDiGraph:
        """
        Load street network by place name.

        Args:
            place_name: Name of the place (e.g., "Purdue University, West Lafayette, IN, USA")
            network_type: Type of network - 'drive', 'walk', 'bike', or 'all'
            simplify: Whether to simplify the graph topology
            cache_file: Optional path to cache file (loads from cache if exists, saves if not)

        Returns:
            NetworkX MultiDiGraph representing the street network

        Example:
            >>> loader = OSMnxNetworkLoader()
            >>> G = loader.load_by_place(
            ...     "Purdue University, West Lafayette, IN, USA",
            ...     cache_file="data/purdue_network.graphml"
            ... )
            >>> print(f"Loaded {len(G.nodes)} nodes and {len(G.edges)} edges")
        """
        # Try to load from cache first
        if cache_file and os.path.exists(cache_file):
            print(f"Loading network from cache: {cache_file}")
            self.G = ox.load_graphml(cache_file)
            print(f"Loaded {len(self.G.nodes)} nodes and {len(self.G.edges)} edges from cache")
        else:
            print(f"Downloading network for: {place_name}")
            self.G = ox.graph_from_place(
                place_name,
                network_type=network_type,
                simplify=simplify
            )
            print(f"Downloaded {len(self.G.nodes)} nodes and {len(self.G.edges)} edges")

            # Save to cache if specified
            if cache_file:
                os.makedirs(os.path.dirname(cache_file) if os.path.dirname(cache_file) else '.', exist_ok=True)
                ox.save_graphml(self.G, cache_file)
                print(f"Saved network to cache: {cache_file}")

        self.place_name = place_name
        self.network_type = network_type
        return self.G

    def load_by_bbox(
        self,
        north: float,
        south: float,
        east: float,
        west: float,
        network_type: str = 'drive',
        simplify: bool = True
    ) -> nx.MultiDiGraph:
        """
        Load street network by bounding box.

        Args:
            north: Northern latitude boundary
            south: Southern latitude boundary
            east: Eastern longitude boundary
            west: Western longitude boundary
            network_type: Type of network - 'drive', 'walk', 'bike', or 'all'
            simplify: Whether to simplify the graph topology

        Returns:
            NetworkX MultiDiGraph representing the street network

        Example:
            >>> loader = OSMnxNetworkLoader()
            >>> G = loader.load_by_bbox(
            ...     north=40.4300, south=40.4200,
            ...     east=-86.9100, west=-86.9250
            ... )
        """
        print(f"Downloading network for bbox: N={north}, S={south}, E={east}, W={west}")
        # OSMnx 2.0+ expects bbox as (left, bottom, right, top) = (west, south, east, north)
        bbox = (west, south, east, north)
        self.G = ox.graph_from_bbox(
            bbox,
            network_type=network_type,
            simplify=simplify
        )
        print(f"Downloaded {len(self.G.nodes)} nodes and {len(self.G.edges)} edges")

        self.bbox = (north, south, east, west)
        self.network_type = network_type
        return self.G

    def ensure_connectivity(self) -> nx.MultiDiGraph:
        """
        Ensure graph connectivity by keeping only the largest connected component.

        Returns:
            Connected graph (largest weakly connected component)
        """
        if not nx.is_weakly_connected(self.G):
            print("Warning: Graph has multiple disconnected components")
            largest_component = max(nx.weakly_connected_components(self.G), key=len)
            self.G = self.G.subgraph(largest_component).copy()
            print(f"Using largest component with {len(self.G.nodes)} nodes")
        return self.G


def map_locations_to_nodes(
    G: nx.MultiDiGraph,
    locations: List[Tuple[float, float]]
) -> List[int]:
    """
    Map geographic coordinates to nearest network nodes.

    IMPORTANT: Input coordinates should be (latitude, longitude) pairs.
    OSMnx nearest_nodes expects (X=longitude, Y=latitude).

    Args:
        G: NetworkX graph from OSMnx
        locations: List of (latitude, longitude) tuples

    Returns:
        List of OSM node IDs (integers)

    Example:
        >>> locations = [(40.4237, -86.9212), (40.4280, -86.9145)]  # (lat, lon)
        >>> nodes = map_locations_to_nodes(G, locations)
        >>> print(f"Mapped {len(locations)} locations to {len(nodes)} nodes")
    """
    nodes = []
    for lat, lon in locations:
        # OSMnx nearest_nodes expects (X=lon, Y=lat)
        node = ox.distance.nearest_nodes(G, lon, lat)
        nodes.append(node)

    print(f"Mapped {len(locations)} locations to {len(nodes)} network nodes")
    return nodes


def compute_distance_matrix(
    G: nx.MultiDiGraph,
    nodes: List[int],
    weight: str = 'length'
) -> np.ndarray:
    """
    Compute shortest path distance matrix between nodes.

    Args:
        G: NetworkX graph from OSMnx
        nodes: List of OSM node IDs
        weight: Edge attribute to use for distance (default: 'length' in meters)

    Returns:
        Distance matrix (n x n numpy array)

    Example:
        >>> distance_matrix = compute_distance_matrix(G, nodes)
        >>> print(f"Distance matrix shape: {distance_matrix.shape}")
        >>> print(f"Average distance: {distance_matrix[distance_matrix > 0].mean():.2f} meters")
    """
    n = len(nodes)
    distance_matrix = np.zeros((n, n))

    print(f"Computing distance matrix for {n} nodes...")

    for i, origin in enumerate(nodes):
        # Compute shortest paths from origin to all destinations
        try:
            lengths = nx.single_source_dijkstra_path_length(G, origin, weight=weight)

            for j, dest in enumerate(nodes):
                if i != j:
                    if dest in lengths:
                        distance_matrix[i, j] = lengths[dest]
                    else:
                        # Node unreachable - use large penalty
                        distance_matrix[i, j] = 999999.0
                        print(f"Warning: Node {dest} unreachable from {origin}")
        except nx.NodeNotFound:
            print(f"Warning: Node {origin} not found in graph")
            distance_matrix[i, :] = 999999.0

    print(f"Distance matrix computed (units: {weight})")
    return distance_matrix


def compute_time_matrix(
    distance_matrix: np.ndarray,
    average_speed_kmh: float = 30.0
) -> np.ndarray:
    """
    Convert distance matrix (meters) to time matrix (minutes).

    Args:
        distance_matrix: Distance matrix in meters
        average_speed_kmh: Average travel speed in km/h

    Returns:
        Time matrix in minutes

    Example:
        >>> time_matrix = compute_time_matrix(distance_matrix, average_speed_kmh=30)
        >>> print(f"Average travel time: {time_matrix[time_matrix > 0].mean():.2f} minutes")
    """
    # Convert km/h to m/min
    speed_m_per_min = (average_speed_kmh * 1000) / 60

    # time (min) = distance (m) / speed (m/min)
    time_matrix = distance_matrix / speed_m_per_min

    return time_matrix


def create_pdptw_order_table_from_locations(
    depot_node: int,
    pickup_nodes: List[int],
    delivery_nodes: List[int],
    G: nx.MultiDiGraph,
    charging_node: Optional[int] = None,
    demand: float = 10.0,
    time_window: Tuple[float, float] = (0.0, 480.0),
    service_time: float = 5.0
) -> pd.DataFrame:
    """
    Create PDPTW order table from OSM nodes.

    Args:
        depot_node: OSM node ID for depot
        pickup_nodes: List of OSM node IDs for pickups
        delivery_nodes: List of OSM node IDs for deliveries (must match pickups)
        G: NetworkX graph from OSMnx
        charging_node: Optional OSM node ID for charging station
        demand: Demand quantity for each order
        time_window: Time window (start, end) in minutes
        service_time: Service time at each node in minutes

    Returns:
        DataFrame in PDPTWInstance format

    Example:
        >>> order_table = create_pdptw_order_table_from_locations(
        ...     depot_node=123456,
        ...     pickup_nodes=[234567, 345678],
        ...     delivery_nodes=[456789, 567890],
        ...     G=G
        ... )
    """
    if len(pickup_nodes) != len(delivery_nodes):
        raise ValueError("Number of pickup and delivery nodes must match")

    n_orders = len(pickup_nodes)

    # Build order table
    rows = []

    # Depot (ID=0)
    depot_data = G.nodes[depot_node]
    rows.append({
        'ID': 0,
        'Type': 'depot',
        'X': depot_data['x'],
        'Y': depot_data['y'],
        'Demand': 0.0,
        'StartTime': time_window[0],
        'EndTime': time_window[1],
        'ServiceTime': 0.0,
        'PartnerID': 0,
        'RealIndex': 0,  # Position index, not OSM node ID
        'RealType': 'depot'
    })

    # Pickup-delivery pairs
    for i, (p_node, d_node) in enumerate(zip(pickup_nodes, delivery_nodes), 1):
        pickup_id = i
        delivery_id = i + n_orders

        # Pickup node
        p_data = G.nodes[p_node]
        rows.append({
            'ID': pickup_id,
            'Type': 'cp',  # customer pickup
            'X': p_data['x'],
            'Y': p_data['y'],
            'Demand': demand,
            'StartTime': time_window[0],
            'EndTime': time_window[1],
            'ServiceTime': service_time,
            'PartnerID': delivery_id,
            'RealIndex': pickup_id,  # Position index, not OSM node ID
            'RealType': 'cp'
        })

        # Delivery node
        d_data = G.nodes[d_node]
        rows.append({
            'ID': delivery_id,
            'Type': 'cd',  # customer delivery
            'X': d_data['x'],
            'Y': d_data['y'],
            'Demand': -demand,
            'StartTime': time_window[0],
            'EndTime': time_window[1],
            'ServiceTime': service_time,
            'PartnerID': pickup_id,
            'RealIndex': delivery_id,  # Position index, not OSM node ID
            'RealType': 'cd'
        })

    # Charging station (if provided)
    if charging_node is not None:
        charging_id = len(rows)
        charging_data = G.nodes[charging_node]
        rows.append({
            'ID': charging_id,
            'Type': 'charging',
            'X': charging_data['x'],
            'Y': charging_data['y'],
            'Demand': 0.0,
            'StartTime': time_window[0],
            'EndTime': time_window[1],
            'ServiceTime': 0.0,
            'PartnerID': 0,
            'RealIndex': charging_id,  # Position index, not OSM node ID
            'RealType': 'charging'
        })

    order_table = pd.DataFrame(rows)
    return order_table


def visualize_routes_on_network(
    G: nx.MultiDiGraph,
    routes: List[List[int]],
    node_mapping: Dict[int, int],
    title: str = "VRP Solution on Street Network",
    save_path: Optional[str] = None
) -> None:
    """
    Visualize VRP routes overlaid on the street network.

    Args:
        G: NetworkX graph from OSMnx
        routes: List of routes (each route is list of VRP node IDs)
        node_mapping: Dictionary mapping VRP node IDs to OSM node IDs
        title: Plot title
        save_path: Optional path to save figure

    Example:
        >>> node_mapping = {0: depot_node, 1: pickup_nodes[0], ...}
        >>> visualize_routes_on_network(G, solution.routes, node_mapping)
    """
    # Plot base network
    fig, ax = ox.plot_graph(
        G,
        bgcolor='white',
        node_size=0,
        edge_color='gray',
        edge_linewidth=0.5,
        show=False,
        close=False
    )

    # Define colors for different routes
    colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'cyan']

    # Plot each route
    for route_idx, route in enumerate(routes):
        # Map VRP node IDs to OSM node IDs
        osm_route = [node_mapping[node_id] for node_id in route if node_id in node_mapping]

        # Get coordinates
        xs = [G.nodes[node]['x'] for node in osm_route]
        ys = [G.nodes[node]['y'] for node in osm_route]

        # Plot route
        ax.plot(
            xs, ys,
            color=colors[route_idx % len(colors)],
            linewidth=3,
            alpha=0.7,
            marker='o',
            markersize=8,
            label=f'Route {route_idx + 1}'
        )

    ax.legend()
    ax.set_title(title)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to: {save_path}")

    plt.show()


# Convenience function for complete workflow
def create_pdptw_from_osm(
    place_name: str,
    depot_location: Tuple[float, float],
    pickup_locations: List[Tuple[float, float]],
    delivery_locations: List[Tuple[float, float]],
    charging_location: Optional[Tuple[float, float]] = None,
    cache_file: Optional[str] = None,
    **kwargs
) -> Tuple[pd.DataFrame, np.ndarray, np.ndarray, nx.MultiDiGraph, Dict[int, int]]:
    """
    Complete workflow to create PDPTW instance from OpenStreetMap.

    This is a convenience function that combines all steps:
    1. Load street network
    2. Map locations to nodes
    3. Compute distance and time matrices
    4. Create order table

    Args:
        place_name: Name of place for OSM query
        depot_location: (latitude, longitude) of depot
        pickup_locations: List of (latitude, longitude) for pickups
        delivery_locations: List of (latitude, longitude) for deliveries
        charging_location: Optional (latitude, longitude) for charging station
        cache_file: Optional path to cache network
        **kwargs: Additional arguments for create_pdptw_order_table_from_locations

    Returns:
        Tuple of (order_table, distance_matrix, time_matrix, graph, node_mapping)

    Example:
        >>> order_table, dist_matrix, time_matrix, G, node_map = create_pdptw_from_osm(
        ...     place_name="Purdue University, West Lafayette, IN, USA",
        ...     depot_location=(40.4237, -86.9212),
        ...     pickup_locations=[(40.4280, -86.9145), (40.4200, -86.9180)],
        ...     delivery_locations=[(40.4250, -86.9100), (40.4210, -86.9220)],
        ...     cache_file="data/purdue_network.graphml"
        ... )
    """
    # Step 1: Load network
    loader = OSMnxNetworkLoader()
    G = loader.load_by_place(place_name, cache_file=cache_file)
    G = loader.ensure_connectivity()

    # Step 2: Map locations to nodes
    all_locations = [depot_location] + pickup_locations + delivery_locations
    if charging_location:
        all_locations.append(charging_location)

    all_nodes = map_locations_to_nodes(G, all_locations)

    depot_node = all_nodes[0]
    n_orders = len(pickup_locations)
    pickup_nodes = all_nodes[1:1+n_orders]
    delivery_nodes = all_nodes[1+n_orders:1+2*n_orders]
    charging_node = all_nodes[-1] if charging_location else None

    # Step 3: Compute matrices
    distance_matrix = compute_distance_matrix(G, all_nodes[:1+2*n_orders+(1 if charging_node else 0)])
    time_matrix = compute_time_matrix(distance_matrix)

    # Create node mapping (VRP ID -> OSM node ID) before creating order table
    node_mapping = {0: depot_node}  # Depot
    for i, p_node in enumerate(pickup_nodes, 1):
        node_mapping[i] = p_node  # Pickup
    for i, d_node in enumerate(delivery_nodes, 1):
        node_mapping[i + n_orders] = d_node  # Delivery
    if charging_node:
        node_mapping[1 + 2*n_orders] = charging_node  # Charging station

    # Step 4: Create order table
    order_table = create_pdptw_order_table_from_locations(
        depot_node=depot_node,
        pickup_nodes=pickup_nodes,
        delivery_nodes=delivery_nodes,
        G=G,
        charging_node=charging_node,
        **kwargs
    )

    print(f"\nPDPTW instance created successfully!")
    print(f"- Nodes: {len(order_table)}")
    print(f"- Orders: {n_orders}")
    print(f"- Distance matrix: {distance_matrix.shape}")

    return order_table, distance_matrix, time_matrix, G, node_mapping
