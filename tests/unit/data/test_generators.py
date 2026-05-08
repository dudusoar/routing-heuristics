"""Unit tests for data generators (OrderGenerator, DemandGenerator)."""

import pytest
import numpy as np
import pandas as pd
from typing import Dict, List, Any

from vrp_toolkit.data.generators import (
    OrderGenerator,
    DemandGenerator,
    DEFAULT_COLUMNS,
    NODE_TYPE_PICKUP,
    NODE_TYPE_DELIVERY,
    NODE_TYPE_DEPOT,
    COL_ID,
    COL_TYPE,
    COL_X,
    COL_Y,
    COL_DEMAND,
    COL_START_TIME,
    COL_END_TIME,
    COL_SERVICE_TIME,
    COL_PARTNER_ID,
    COL_REAL_INDEX,
    COL_REAL_TYPE
)
from tests.utils import assertions


class TestOrderGenerator:
    """Test OrderGenerator class."""
    
    def test_creation(self, synthetic_real_map):
        """Test OrderGenerator creation."""
        real_map = synthetic_real_map
        
        # Create demand table
        np.random.seed(42)
        n_time_intervals = 5
        n_restaurants = len(real_map.restaurants)
        n_customers = len(real_map.customers)
        
        demand_data = np.random.rand(n_time_intervals, n_restaurants, n_customers) * 10
        
        # Time parameters
        time_params = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        # Create generator
        generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_data,
            time_params=time_params,
            robot_speed=2.0
        )
        
        # Check attributes
        assert generator.real_map is real_map
        assert generator.demand_table is demand_data
        assert generator.time_window_length == time_params['time_window_length']
        assert generator.service_time == time_params['service_time']
        assert generator.extra_time == time_params['extra_time']
        assert generator.big_time == time_params['big_time']
        assert generator.robot_speed == 2.0
        
        # Should have order_table attribute
        assert hasattr(generator, 'order_table')
        assert isinstance(generator.order_table, pd.DataFrame)
    
    def test_order_table_structure(self, synthetic_real_map):
        """Test generated order table structure."""
        real_map = synthetic_real_map
        
        # Simple demand table
        n_time_intervals = 3
        n_restaurants = min(2, len(real_map.restaurants))
        n_customers = min(2, len(real_map.customers))
        demand_data = np.ones((n_time_intervals, n_restaurants, n_customers))
        
        time_params = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_data,
            time_params=time_params,
            robot_speed=2.0
        )
        
        order_table = generator.order_table
        
        # Check DataFrame structure
        assertions.assert_order_table_valid(order_table)
        
        # Check column order matches DEFAULT_COLUMNS
        assert list(order_table.columns) == DEFAULT_COLUMNS
        
        # Check node types
        type_counts = order_table[COL_TYPE].value_counts()
        assert NODE_TYPE_DEPOT in type_counts.index
        assert NODE_TYPE_PICKUP in type_counts.index
        assert NODE_TYPE_DELIVERY in type_counts.index
        
        # Check exactly one depot
        assert type_counts[NODE_TYPE_DEPOT] == 1
        
        # Check pickup-delivery pairs match
        pickup_mask = order_table[COL_TYPE] == NODE_TYPE_PICKUP
        delivery_mask = order_table[COL_TYPE] == NODE_TYPE_DELIVERY
        
        assert pickup_mask.sum() == delivery_mask.sum()  # Equal numbers
        
        # Check partner relationships
        for _, row in order_table.iterrows():
            if row[COL_TYPE] in [NODE_TYPE_PICKUP, NODE_TYPE_DELIVERY]:
                partner_id = row[COL_PARTNER_ID]
                partner_row = order_table[order_table[COL_ID] == partner_id].iloc[0]
                
                # Should be reciprocal
                assert partner_row[COL_PARTNER_ID] == row[COL_ID]
                
                # Should be opposite types
                if row[COL_TYPE] == NODE_TYPE_PICKUP:
                    assert partner_row[COL_TYPE] == NODE_TYPE_DELIVERY
                else:
                    assert partner_row[COL_TYPE] == NODE_TYPE_PICKUP
    
    def test_time_window_generation(self, synthetic_real_map):
        """Test time window generation logic."""
        real_map = synthetic_real_map
        
        # Single demand entry
        n_time_intervals = 1
        n_restaurants = 1
        n_customers = 1
        demand_data = np.array([[[5.0]]])  # 5 units in first time interval
        
        time_params = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_data,
            time_params=time_params,
            robot_speed=2.0
        )
        
        order_table = generator.order_table
        
        # Check time windows are generated
        for _, row in order_table.iterrows():
            start_time = row[COL_START_TIME]
            end_time = row[COL_END_TIME]
            
            assert isinstance(start_time, (int, float))
            assert isinstance(end_time, (int, float))
            assert start_time <= end_time
            
            # For depot, time window should be [0, big_time]
            if row[COL_TYPE] == NODE_TYPE_DEPOT:
                assert start_time == 0
                assert end_time == time_params['big_time']
    
    def test_demand_assignment(self, synthetic_real_map):
        """Test demand value assignment."""
        real_map = synthetic_real_map
        
        # Create demand with specific values
        demand_data = np.array([[[2.0, 3.0], [1.0, 4.0]]])  # 2x2 demand matrix
        
        time_params = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        # Need appropriate restaurant/customer counts
        n_restaurants = min(2, len(real_map.restaurants))
        n_customers = min(2, len(real_map.customers))
        
        if n_restaurants >= 2 and n_customers >= 2:
            generator = OrderGenerator(
                real_map=real_map,
                demand_table=demand_data,
                time_params=time_params,
                robot_speed=2.0
            )
            
            order_table = generator.order_table
            
            # Check demand values
            for _, row in order_table.iterrows():
                demand = row[COL_DEMAND]
                
                if row[COL_TYPE] == NODE_TYPE_DEPOT:
                    assert demand == 0
                elif row[COL_TYPE] == NODE_TYPE_PICKUP:
                    assert demand > 0  # Positive for pickups
                elif row[COL_TYPE] == NODE_TYPE_DELIVERY:
                    assert demand < 0  # Negative for deliveries
    
    def test_column_mapping(self, synthetic_real_map):
        """Test custom column name mapping."""
        real_map = synthetic_real_map
        
        # Simple demand
        demand_data = np.ones((1, 1, 1))
        
        time_params = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        # Custom column mapping
        column_mapping = {
            'ID': 'NodeID',
            'Type': 'NodeType',
            'X': 'CoordX',
            'Y': 'CoordY'
        }
        
        generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_data,
            time_params=time_params,
            robot_speed=2.0,
            column_mapping=column_mapping
        )
        
        order_table = generator.order_table
        
        # Check columns are renamed
        for old_name, new_name in column_mapping.items():
            assert new_name in order_table.columns
        
        # Original columns should not exist
        for old_name in column_mapping.keys():
            assert old_name not in order_table.columns


class TestDemandGenerator:
    """Test DemandGenerator class."""
    
    def test_creation(self, synthetic_real_map):
        """Test DemandGenerator creation."""
        real_map = synthetic_real_map
        
        # Time parameters
        time_params = {
            'peak_hours': [(8, 10), (17, 19)],
            'base_demand': 5.0,
            'peak_multiplier': 2.0,
            'random_seed': 42
        }
        
        # Create generator
        generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=24  # One per hour
        )
        
        # Check attributes
        assert generator.real_map is real_map
        assert generator.time_params == time_params
        assert generator.n_time_intervals == 24
        
        # Should have demand_table attribute
        assert hasattr(generator, 'demand_table')
        assert isinstance(generator.demand_table, np.ndarray)
    
    def test_demand_table_shape(self, synthetic_real_map):
        """Test demand table shape."""
        real_map = synthetic_real_map
        
        n_restaurants = len(real_map.restaurants)
        n_customers = len(real_map.customers)
        
        time_params = {
            'peak_hours': [(8, 10), (17, 19)],
            'base_demand': 5.0,
            'peak_multiplier': 2.0,
            'random_seed': 42
        }
        
        n_time_intervals = 12
        
        generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=n_time_intervals
        )
        
        demand_table = generator.demand_table
        
        # Check shape
        assert demand_table.shape == (n_time_intervals, n_restaurants, n_customers)
        
        # All values should be non-negative
        assert np.all(demand_table >= 0)
    
    def test_peak_hour_effect(self, synthetic_real_map):
        """Test that peak hours increase demand."""
        real_map = synthetic_real_map
        
        if len(real_map.restaurants) == 0 or len(real_map.customers) == 0:
            pytest.skip("Need restaurants and customers for this test")
        
        # Simple time params with clear peak
        time_params = {
            'peak_hours': [(2, 4)],  # Peak at intervals 2-4
            'base_demand': 1.0,
            'peak_multiplier': 5.0,  # 5x during peak
            'random_seed': 42
        }
        
        n_time_intervals = 6
        
        generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=n_time_intervals
        )
        
        demand_table = generator.demand_table
        
        # Check peak hours have higher demand
        peak_intervals = list(range(2, 4))
        off_peak_intervals = [0, 1, 5]  # Outside peak
        
        # Average demand during peak should be higher
        peak_avg = demand_table[peak_intervals, :, :].mean()
        off_peak_avg = demand_table[off_peak_intervals, :, :].mean()
        
        # With multiplier of 5.0, peak should be significantly higher
        # (allowing for randomness)
        assert peak_avg > off_peak_avg
    
    def test_random_seed_reproducibility(self, synthetic_real_map):
        """Test that random seed ensures reproducibility."""
        real_map = synthetic_real_map
        
        time_params = {
            'peak_hours': [(8, 10)],
            'base_demand': 5.0,
            'peak_multiplier': 2.0,
            'random_seed': 12345  # Fixed seed
        }
        
        # Create two generators with same seed
        generator1 = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=10
        )
        
        generator2 = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=10
        )
        
        # Should produce identical demand tables
        assert np.array_equal(generator1.demand_table, generator2.demand_table)
        
        # Different seed should produce different results
        time_params2 = time_params.copy()
        time_params2['random_seed'] = 54321
        
        generator3 = DemandGenerator(
            real_map=real_map,
            time_params=time_params2,
            n_time_intervals=10
        )
        
        # Very likely different (not guaranteed but very probable)
        assert not np.array_equal(generator1.demand_table, generator3.demand_table)
    
    def test_demand_statistics(self, synthetic_real_map):
        """Test demand statistics and bounds."""
        real_map = synthetic_real_map
        
        time_params = {
            'peak_hours': [(8, 10)],
            'base_demand': 10.0,
            'peak_multiplier': 3.0,
            'random_seed': 42
        }
        
        generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params,
            n_time_intervals=24
        )
        
        demand_table = generator.demand_table
        
        # Check basic statistics
        assert demand_table.mean() > 0
        assert demand_table.std() >= 0
        
        # Check bounds (demand should be non-negative)
        assert demand_table.min() >= 0
        
        # With base_demand of 10.0, average should be around that
        # (allowing for randomness and peak effects)
        avg_demand = demand_table.mean()
        assert 5.0 <= avg_demand <= 20.0  # Reasonable range


class TestGeneratorIntegration:
    """Integration tests for generators."""
    
    def test_order_generator_with_demand_generator(self, synthetic_real_map):
        """Test that OrderGenerator can use DemandGenerator output."""
        real_map = synthetic_real_map
        
        # Skip if no restaurants or customers
        if len(real_map.restaurants) == 0 or len(real_map.customers) == 0:
            pytest.skip("Need restaurants and customers for this test")
        
        # Create demand using DemandGenerator
        time_params_demand = {
            'peak_hours': [(8, 10), (17, 19)],
            'base_demand': 5.0,
            'peak_multiplier': 2.0,
            'random_seed': 42
        }
        
        demand_generator = DemandGenerator(
            real_map=real_map,
            time_params=time_params_demand,
            n_time_intervals=24
        )
        
        demand_table = demand_generator.demand_table
        
        # Use demand table in OrderGenerator
        time_params_order = {
            'time_window_length': 30.0,
            'service_time': 5.0,
            'extra_time': 10.0,
            'big_time': 1000.0
        }
        
        order_generator = OrderGenerator(
            real_map=real_map,
            demand_table=demand_table,
            time_params=time_params_order,
            robot_speed=2.0
        )
        
        # Should produce valid order table
        order_table = order_generator.order_table
        assertions.assert_order_table_valid(order_table)
        
        # Number of orders should relate to demand table
        n_pickups = (order_table[COL_TYPE] == NODE_TYPE_PICKUP).sum()
        n_deliveries = (order_table[COL_TYPE] == NODE_TYPE_DELIVERY).sum()
        
        # Should have matching numbers
        assert n_pickups == n_deliveries
        
        # Should have at least some orders if there's demand
        if np.any(demand_table > 0):
            assert n_pickups > 0
    
    def test_generator_constants(self):
        """Test generator module constants."""
        # Check constants are defined
        assert DEFAULT_COLUMNS is not None
        assert isinstance(DEFAULT_COLUMNS, list)
        assert len(DEFAULT_COLUMNS) > 0
        
        # Check node type constants
        assert NODE_TYPE_PICKUP == 'cp'
        assert NODE_TYPE_DELIVERY == 'cd'
        assert NODE_TYPE_DEPOT == 'depot'
        
        # Check column constants
        assert COL_ID == 'ID'
        assert COL_TYPE == 'Type'
        assert COL_X == 'X'
        assert COL_Y == 'Y'
        assert COL_DEMAND == 'Demand'
        assert COL_START_TIME == 'StartTime'
        assert COL_END_TIME == 'EndTime'
        assert COL_SERVICE_TIME == 'ServiceTime'
        assert COL_PARTNER_ID == 'PartnerID'
        assert COL_REAL_INDEX == 'RealIndex'
        assert COL_REAL_TYPE == 'RealType'
        
        # DEFAULT_COLUMNS should contain all column constants
        for const in [COL_ID, COL_TYPE, COL_X, COL_Y, COL_DEMAND, 
                     COL_START_TIME, COL_END_TIME, COL_SERVICE_TIME,
                     COL_PARTNER_ID, COL_REAL_INDEX, COL_REAL_TYPE]:
            assert const in DEFAULT_COLUMNS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])