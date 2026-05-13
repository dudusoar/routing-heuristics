"""
Data layer for VRP toolkit.

This module contains data generation, loading, and map representation components.
"""

from .generators import OrderGenerator, DemandGenerator
from .map import RealMap, RealDataMap

# OSMnx integration (optional - only import if osmnx is available)
try:
    from .osmnx_integration import (
        OSMnxNetworkLoader,
        map_locations_to_nodes,
        compute_distance_matrix,
        compute_time_matrix,
        create_pdptw_order_table_from_locations,
        visualize_routes_on_network,
        create_pdptw_from_osm
    )
    _OSMNX_AVAILABLE = True
except ImportError:
    _OSMNX_AVAILABLE = False

__all__ = [
    'RealMap',
    'RealDataMap',
    'OrderGenerator',
    'DemandGenerator',
]

if _OSMNX_AVAILABLE:
    __all__.extend([
        'OSMnxNetworkLoader',
        'map_locations_to_nodes',
        'compute_distance_matrix',
        'compute_time_matrix',
        'create_pdptw_order_table_from_locations',
        'visualize_routes_on_network',
        'create_pdptw_from_osm'
    ])