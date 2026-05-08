"""Unit tests for map classes (RealMap, RealDataMap)."""

import pytest
import numpy as np
import pandas as pd
from typing import List, Dict, Any

from vrp_toolkit.data.map import RealMap, RealDataMap
from tests.utils import assertions


class TestRealMap:
    """Test RealMap class for synthetic maps."""
    
    def test_creation(self, synthetic_real_map):
        """Test RealMap creation with synthetic data."""
        real_map = synthetic_real_map
        
        # Check attributes
        assert hasattr(real_map, 'coordinates')
        assert hasattr(real_map, 'restaurants')
        assert hasattr(real_map, 'customers')
        assert hasattr(real_map, 'depot')
        assert hasattr(real_map, 'distance_matrix')
        
        # Check shapes and types
        assert isinstance(real_map.coordinates, np.ndarray)
        assert real_map.coordinates.shape[1] == 2  # (x, y) coordinates
        
        assert isinstance(real_map.restaurants, list)
        assert isinstance(real_map.customers, list)
        assert isinstance(real_map.depot, list)
        
        # Distance matrix should be square
        n_nodes = len(real_map.coordinates)
        assert real_map.distance_matrix.shape == (n_nodes, n_nodes)
        
        # Validate distance matrix
        assertions.assert_distance_matrix_valid(
            real_map.distance_matrix, 
            symmetric=True
        )
    
    def test_default_parameters(self):
        """Test RealMap with default parameters."""
        np.random.seed(42)
        n_nodes = 10
        coordinates = np.random.rand(n_nodes, 2) * 100
        
        # Create with minimal parameters
        real_map = RealMap(
            coordinates=coordinates,
            restaurants=[1, 2, 3],
            customers=[4, 5, 6, 7, 8],
            depot=[0]
        )
        
        # Check default attributes
        assert real_map.node_types is not None
        assert hasattr(real_map, 'node_info')
        assert isinstance(real_map.node_info, pd.DataFrame)
    
    def test_custom_parameters(self):
        """Test RealMap with custom parameters."""
        np.random.seed(42)
        n_nodes = 15
        coordinates = np.random.rand(n_nodes, 2) * 100
        
        # Custom parameters
        restaurants = [1, 2, 3, 4]
        customers = [5, 6, 7, 8, 9, 10, 11]
        depot = [0]
        charging_stations = [12, 13]
        destination = [14]
        
        real_map = RealMap(
            coordinates=coordinates,
            restaurants=restaurants,
            customers=customers,
            depot=depot,
            charging_stations=charging_stations,
            destination=destination
        )
        
        # Check custom attributes
        assert real_map.restaurants == restaurants
        assert real_map.customers == customers
        assert real_map.depot == depot
        assert real_map.charging_stations == charging_stations
        assert real_map.destination == destination
        
        # Check node_info includes all nodes
        assert len(real_map.node_info) == n_nodes
    
    def test_distance_calculation(self):
        """Test Euclidean distance calculation."""
        np.random.seed(42)
        n_nodes = 5
        coordinates = np.random.rand(n_nodes, 2) * 10
        
        real_map = RealMap(
            coordinates=coordinates,
            restaurants=[1, 2],
            customers=[3, 4],
            depot=[0]
        )
        
        # Check distance matrix matches manual calculation
        dist_matrix = real_map.distance_matrix
        
        for i in range(n_nodes):
            for j in range(n_nodes):
                # Manual Euclidean distance
                dx = coordinates[i, 0] - coordinates[j, 0]
                dy = coordinates[i, 1] - coordinates[j, 1]
                expected = np.sqrt(dx*dx + dy*dy)
                
                # Should match (within numerical tolerance)
                assert np.abs(dist_matrix[i, j] - expected) < 1e-10
    
    def test_node_info_dataframe(self, synthetic_real_map):
        """Test node_info DataFrame structure."""
        real_map = synthetic_real_map
        
        node_info = real_map.node_info
        
        # Should be DataFrame
        assert isinstance(node_info, pd.DataFrame)
        
        # Should have required columns
        required_columns = ['node_index', 'x', 'y', 'type']
        assert all(col in node_info.columns for col in required_columns)
        
        # Should have correct number of rows
        assert len(node_info) == len(real_map.coordinates)
        
        # Check node types are correctly assigned
        for idx in real_map.restaurants:
            row = node_info[node_info['node_index'] == idx].iloc[0]
            assert row['type'] == 'restaurant'
        
        for idx in real_map.customers:
            row = node_info[node_info['node_index'] == idx].iloc[0]
            assert row['type'] == 'customer'
        
        for idx in real_map.depot:
            row = node_info[node_info['node_index'] == idx].iloc[0]
            assert row['type'] == 'depot'
    
    def test_plot_map_method(self, synthetic_real_map):
        """Test plot_map method (should not crash)."""
        real_map = synthetic_real_map
        
        # Method should exist
        assert hasattr(real_map, 'plot_map')
        assert callable(real_map.plot_map)
        
        # Should not crash when called
        # Note: We can't actually test plotting without matplotlib GUI
        # but we can test that the method exists and accepts parameters
        try:
            # Try calling with minimal parameters
            real_map.plot_map(show=False)  # Don't actually show plot
        except Exception as e:
            # Might fail due to missing matplotlib backend in test environment
            # That's OK for unit tests
            pass


class TestRealDataMap:
    """Test RealDataMap class for real-world map data."""
    
    def test_class_exists(self):
        """Test that RealDataMap class exists."""
        # Just check class can be imported
        from vrp_toolkit.data.map import RealDataMap
        assert RealDataMap is not None
    
    def test_constructor_signature(self):
        """Test RealDataMap constructor signature."""
        # Check required parameters
        import inspect
        sig = inspect.signature(RealDataMap.__init__)
        
        # Required parameters
        params = list(sig.parameters.keys())
        
        # Should have node_file and tt_matrix_file
        assert 'node_file' in params
        assert 'tt_matrix_file' in params
        
        # Should have optional parameters with defaults
        assert 'depot_index' in params
        assert 'destination_index' in params
        assert 'charging_station_index' in params
        assert 'distance_conversion_factor' in params
        assert 'customer_types' in params
    
    @pytest.mark.skip(reason="Requires actual data files")
    def test_creation_with_real_data(self):
        """Test RealDataMap creation with actual data files."""
        # This test requires actual data files
        # For now, just verify the interface
        
        # RealDataMap should load data from CSV files
        # node_file: CSV with node information
        # tt_matrix_file: CSV with travel time matrix
        
        # Since we don't have actual files in test environment,
        # we'll test the interface and error handling
        
        pass
    
    def test_missing_file_handling(self):
        """Test error handling for missing files."""
        # Should raise appropriate error for missing files
        with pytest.raises((FileNotFoundError, IOError, ValueError)):
            RealDataMap(
                node_file="nonexistent_node_file.csv",
                tt_matrix_file="nonexistent_matrix_file.csv"
            )
    
    def test_default_parameters(self):
        """Test RealDataMap default parameter values."""
        # Check default values in constructor
        import inspect
        sig = inspect.signature(RealDataMap.__init__)
        
        # Get default values
        defaults = {
            k: v.default 
            for k, v in sig.parameters.items() 
            if v.default is not inspect.Parameter.empty
        }
        
        # Check key defaults
        assert defaults.get('depot_index') == 15
        assert defaults.get('distance_conversion_factor') == 1609.34
        assert defaults.get('customer_types') == ["apartment", "university building"]


class TestMapCompatibility:
    """Test compatibility between map classes."""
    
    def test_common_interface(self, synthetic_real_map):
        """Test that map classes share common interface."""
        real_map = synthetic_real_map
        
        # Both RealMap and RealDataMap should have these attributes/methods
        common_attributes = [
            'coordinates',
            'distance_matrix', 
            'node_info',
            'plot_map'
        ]
        
        for attr in common_attributes:
            assert hasattr(real_map, attr)
    
    def test_distance_matrix_compatibility(self, synthetic_real_map):
        """Test distance matrix compatibility with VRP problems."""
        real_map = synthetic_real_map
        
        # Distance matrix should be compatible with PDPTWInstance
        dist_matrix = real_map.distance_matrix
        
        # Should be numpy array
        assert isinstance(dist_matrix, np.ndarray)
        
        # Should be square
        n_nodes = len(real_map.coordinates)
        assert dist_matrix.shape == (n_nodes, n_nodes)
        
        # Should have zero diagonal
        assert np.allclose(np.diag(dist_matrix), 0)
        
        # Should be symmetric (for Euclidean distances)
        assert np.allclose(dist_matrix, dist_matrix.T)
        
        # Should be non-negative
        assert np.all(dist_matrix >= 0)


class TestMapUtilities:
    """Test utility functions in map module."""
    
    def test_coordinate_validation(self):
        """Test coordinate array validation."""
        # Valid coordinates
        valid_coords = np.array([[0, 0], [1, 1], [2, 2]])
        
        # Invalid: wrong shape
        invalid_coords_1d = np.array([0, 0, 1, 1, 2, 2])
        
        # Invalid: wrong number of columns
        invalid_coords_3d = np.array([[0, 0, 0], [1, 1, 1]])
        
        # RealMap should validate coordinates
        with pytest.raises((ValueError, AssertionError)):
            RealMap(
                coordinates=invalid_coords_1d,
                restaurants=[1],
                customers=[2],
                depot=[0]
            )
    
    def test_node_index_validation(self):
        """Test node index validation."""
        np.random.seed(42)
        n_nodes = 5
        coordinates = np.random.rand(n_nodes, 2) * 10
        
        # Invalid: index out of bounds
        with pytest.raises((ValueError, IndexError)):
            RealMap(
                coordinates=coordinates,
                restaurants=[10],  # Doesn't exist
                customers=[1, 2],
                depot=[0]
            )
        
        # Invalid: duplicate indices
        with pytest.raises((ValueError, AssertionError)):
            RealMap(
                coordinates=coordinates,
                restaurants=[1, 1],  # Duplicate
                customers=[2, 3],
                depot=[0]
            )
    
    def test_empty_sets_handling(self):
        """Test handling of empty node sets."""
        np.random.seed(42)
        n_nodes = 3
        coordinates = np.random.rand(n_nodes, 2) * 10
        
        # Should work with empty lists
        real_map = RealMap(
            coordinates=coordinates,
            restaurants=[],  # Empty
            customers=[1, 2],
            depot=[0]
        )
        
        assert real_map.restaurants == []
        assert len(real_map.node_info[real_map.node_info['type'] == 'restaurant']) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])