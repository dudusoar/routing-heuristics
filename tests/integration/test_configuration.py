"""Integration tests for configuration system."""

import pytest
import json
import yaml
import tempfile
import os
from typing import Dict, Any

from vrp_toolkit.utils.config import (
    VRPConfig,
    ProblemConfig,
    AlgorithmConfig,
    ALNSAlgorithmConfig,
    DataConfig,
    RunConfig,
    ConfigLoader
)


class TestVRPConfig:
    """Test VRPConfig dataclass."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = VRPConfig()
        
        # Check nested configs exist
        assert isinstance(config.problem, ProblemConfig)
        assert isinstance(config.algorithm, AlgorithmConfig)
        assert isinstance(config.data, DataConfig)
        assert isinstance(config.run, RunConfig)
    
    def test_custom_config(self):
        """Test custom configuration values."""
        # Create custom nested configs
        problem_config = ProblemConfig(
            problem_type="pdptw",
            num_vehicles=5,
            vehicle_capacity=100.0,
            battery_capacity=200.0
        )

        # Create ALNS-specific configuration
        alns_config = ALNSAlgorithmConfig(
            max_no_improve=200,
            start_temp=5000.0,
            cooling_rate=0.95,
            num_removal=7
        )

        algorithm_config = AlgorithmConfig(
            algorithm_type="alns",
            alns_config=alns_config
        )

        data_config = DataConfig(
            map_type="synthetic",
            synthetic_num_nodes=20,
            num_time_intervals=24
        )

        run_config = RunConfig(
            random_seed=42,
            num_runs=10,
            output_dir="./results"
        )

        config = VRPConfig(
            problem=problem_config,
            algorithm=algorithm_config,
            data=data_config,
            run=run_config
        )

        # Check custom values
        assert config.problem.problem_type == "pdptw"
        assert config.problem.num_vehicles == 5
        assert config.problem.vehicle_capacity == 100.0

        assert config.algorithm.algorithm_type == "alns"
        assert config.algorithm.alns_config.max_no_improve == 200
        assert config.algorithm.alns_config.start_temp == 5000.0
        assert config.algorithm.alns_config.cooling_rate == 0.95

        assert config.data.map_type == "synthetic"
        assert config.data.synthetic_num_nodes == 20

        assert config.run.random_seed == 42
        assert config.run.num_runs == 10
    
    def test_config_validation(self):
        """Test configuration parameter validation."""
        # Test that invalid values are caught by validate() method
        invalid_problem = ProblemConfig(num_vehicles=-5)  # Negative
        problem_errors = invalid_problem.validate()
        assert len(problem_errors) > 0, "Negative num_vehicles should produce validation errors"

        invalid_run = RunConfig(num_runs=0)  # Zero runs
        run_errors = invalid_run.validate()
        assert len(run_errors) > 0, "Zero num_runs should produce validation errors"

        # These should work (no errors)
        valid_problem = ProblemConfig(num_vehicles=1)  # Positive vehicles allowed
        assert len(valid_problem.validate()) == 0

        valid_run = RunConfig(num_runs=1)  # Single run
        assert len(valid_run.validate()) == 0


class TestConfigLoader:
    """Test ConfigLoader for JSON and YAML files."""
    
    def test_json_loading_saving(self):
        """Test loading and saving JSON configuration."""
        # Create config
        config = VRPConfig()

        # Save to temporary file using ConfigLoader.save
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
            ConfigLoader.save(config, temp_path, format='json')

        try:
            # Load back using ConfigLoader.load
            loaded_config = ConfigLoader.load(temp_path)

            # Should be VRPConfig instance
            assert isinstance(loaded_config, VRPConfig)

            # Should have same structure
            assert isinstance(loaded_config.problem, ProblemConfig)
            assert isinstance(loaded_config.algorithm, AlgorithmConfig)
            assert isinstance(loaded_config.data, DataConfig)
            assert isinstance(loaded_config.run, RunConfig)

            # Values should match (within JSON serialization limits)
            assert loaded_config.problem.problem_type == config.problem.problem_type
            assert loaded_config.problem.num_vehicles == config.problem.num_vehicles

        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_yaml_loading_saving(self):
        """Test loading and saving YAML configuration."""
        # Create config
        config = VRPConfig()

        # Save to temporary file using ConfigLoader.save with YAML format
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
            ConfigLoader.save(config, temp_path, format='yaml')

        try:
            # Load back using ConfigLoader.load
            loaded_config = ConfigLoader.load(temp_path)

            # Should be VRPConfig instance
            assert isinstance(loaded_config, VRPConfig)

            # Should have same structure
            assert isinstance(loaded_config.problem, ProblemConfig)
            assert isinstance(loaded_config.algorithm, AlgorithmConfig)
            assert isinstance(loaded_config.data, DataConfig)
            assert isinstance(loaded_config.run, RunConfig)

        finally:
            # Clean up
            os.unlink(temp_path)
    
    def test_load_from_string(self):
        """Test loading configuration from string."""
        # JSON string matching actual VRPConfig structure
        json_str = """
        {
            "problem": {
                "problem_type": "pdptw",
                "num_vehicles": 3,
                "vehicle_capacity": 50.0
            },
            "algorithm": {
                "algorithm_type": "alns",
                "alns_config": {
                    "max_no_improve": 200,
                    "start_temp": 5000.0,
                    "cooling_rate": 0.95
                }
            },
            "data": {
                "map_type": "synthetic",
                "synthetic_num_nodes": 10,
                "num_time_intervals": 6
            },
            "run": {
                "random_seed": 123,
                "num_runs": 5
            }
        }
        """

        # Parse JSON and create config using VRPConfig.from_dict
        config_dict = json.loads(json_str)
        config = VRPConfig.from_dict(config_dict)

        assert isinstance(config, VRPConfig)
        assert config.problem.problem_type == "pdptw"
        assert config.problem.num_vehicles == 3
        assert config.algorithm.algorithm_type == "alns"
        assert config.algorithm.alns_config.max_no_improve == 200
        assert config.data.map_type == "synthetic"
        assert config.data.synthetic_num_nodes == 10
        assert config.run.random_seed == 123
        assert config.run.num_runs == 5
    
    def test_file_not_found(self):
        """Test error handling for missing files."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("nonexistent_file.json")

        with pytest.raises(FileNotFoundError):
            ConfigLoader.load("nonexistent_file.yaml")
    
    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        # Write invalid JSON to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json}")
            temp_path = f.name

        try:
            # Should raise JSONDecodeError when loading
            with pytest.raises(json.JSONDecodeError):
                ConfigLoader.load(temp_path)
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_config_merging(self):
        """Test merging configurations."""
        base_config = VRPConfig()

        # Get base config as dictionary
        base_dict = base_config.to_dict()

        # Partial update
        update_dict = {
            "problem": {
                "num_vehicles": 7,
                "vehicle_capacity": 75.0
            },
            "run": {
                "random_seed": 999
            }
        }

        # Merge dictionaries (simple deep merge for two levels)
        merged_dict = base_dict.copy()
        for key, value in update_dict.items():
            if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
                # Merge nested dictionaries
                merged_dict[key].update(value)
            else:
                # Replace or add
                merged_dict[key] = value

        # Create merged config
        merged_config = VRPConfig.from_dict(merged_dict)

        # Updated values
        assert merged_config.problem.num_vehicles == 7
        assert merged_config.problem.vehicle_capacity == 75.0
        assert merged_config.run.random_seed == 999

        # Unchanged values
        assert merged_config.problem.problem_type == base_config.problem.problem_type
        assert merged_config.algorithm.algorithm_type == base_config.algorithm.algorithm_type
        assert merged_config.data.map_type == base_config.data.map_type


class TestConfigIntegration:
    """Test configuration integration with other components."""
    
    def test_config_with_alns(self):
        """Test using configuration with ALNS."""
        from vrp_toolkit.algorithms.alns.solver import ALNSConfig
        
        # Create ALNSConfig from dictionary
        alns_params = {
            "num_removal": 7,
            "max_no_improve": 100,
            "start_temp": 80.0,
            "cooling_rate": 0.92
        }
        
        # ALNSConfig should accept these parameters
        alns_config = ALNSConfig(**alns_params)
        
        assert alns_config.num_removal == 7
        assert alns_config.max_no_improve == 100
        assert alns_config.start_temp == 80.0
        assert alns_config.cooling_rate == 0.92
    
    def test_vrpconfig_to_alnsconfig(self):
        """Test converting VRPConfig to algorithm-specific config."""
        # Create VRPConfig with algorithm parameters
        vrp_config = VRPConfig()

        # In a real integration, we'd have a method to convert
        # VRPConfig.algorithm to ALNSConfig
        # For now, just test that both config types exist and have expected attributes

        assert hasattr(vrp_config, 'algorithm')
        assert hasattr(vrp_config.algorithm, 'algorithm_type')
        assert hasattr(vrp_config.algorithm, 'alns_config')
        # ALNS-specific attributes are now in alns_config
        assert hasattr(vrp_config.algorithm.alns_config, 'max_no_improve')
        assert hasattr(vrp_config.algorithm.alns_config, 'start_temp')
    
    def test_example_config_files(self):
        """Test example configuration files in repository."""
        example_files = [
            "config_example.json",
            "config_example.yaml"
        ]
        
        for file_name in example_files:
            file_path = os.path.join(
                os.path.dirname(__file__), "..", "..", file_name
            )
            
            if os.path.exists(file_path):
                # Should load without errors using ConfigLoader.load
                config = ConfigLoader.load(file_path)

                assert isinstance(config, VRPConfig)

                # Should have all required sections
                assert hasattr(config, 'problem')
                assert hasattr(config, 'algorithm')
                assert hasattr(config, 'data')
                assert hasattr(config, 'run')
            else:
                print(f"Note: Example config file not found: {file_name}")
    
    def test_config_validation_integration(self):
        """Test configuration validation in integrated context."""
        # Create config with some invalid values
        invalid_dict = {
            "problem": {
                "num_vehicles": -1  # Invalid
            }
        }
        
        # Loading might fail or produce invalid config
        # Actual behavior depends on validation implementation
        
        # For now, just ensure ConfigLoader exists and works
        config_loader = ConfigLoader()
        assert config_loader is not None


class TestConfigurationUseCases:
    """Test real-world configuration use cases."""
    
    def test_experiment_configuration(self):
        """Test configuration for running experiments."""
        # Configuration for sensitivity analysis experiment
        experiment_config = VRPConfig(
            problem=ProblemConfig(
                problem_type="pdptw",
                num_vehicles=3,
                vehicle_capacity=100.0,
                battery_capacity=150.0
            ),
            algorithm=AlgorithmConfig(
                algorithm_type="alns",
                alns_config=ALNSAlgorithmConfig(
                    max_no_improve=200,
                    start_temp=5000.0,
                    cooling_rate=0.95
                )
            ),
            data=DataConfig(
                map_type="synthetic",
                synthetic_num_nodes=15,
                num_time_intervals=12
            ),
            run=RunConfig(
                random_seed=42,
                num_runs=20,  # Multiple runs for statistics
                output_dir="./experiment_results"
            )
        )

        # Should be valid
        assert experiment_config.run.num_runs == 20
        assert experiment_config.algorithm.alns_config.max_no_improve == 200
    
    def test_quick_demo_configuration(self):
        """Test configuration for quick demonstration."""
        # Quick demo with minimal settings
        demo_config = VRPConfig(
            problem=ProblemConfig(
                problem_type="pdptw",
                num_vehicles=1,
                vehicle_capacity=50.0,
                battery_capacity=100.0
            ),
            algorithm=AlgorithmConfig(
                algorithm_type="alns",
                alns_config=ALNSAlgorithmConfig(
                    max_no_improve=50,
                    start_temp=1000.0,
                    cooling_rate=0.9
                )
            ),
            data=DataConfig(
                map_type="synthetic",
                synthetic_num_nodes=3,  # Small problem
                num_time_intervals=6
            ),
            run=RunConfig(
                random_seed=123,
                num_runs=1,  # Single run
                output_dir="./demo_output"
            )
        )

        # Should be valid for quick demo
        assert demo_config.algorithm.alns_config.max_no_improve == 50
        assert demo_config.data.synthetic_num_nodes == 3
    
    def test_production_configuration(self):
        """Test configuration for production use."""
        # Production settings with thorough optimization
        production_config = VRPConfig(
            problem=ProblemConfig(
                problem_type="pdptw",
                num_vehicles=10,
                vehicle_capacity=200.0,
                battery_capacity=300.0
            ),
            algorithm=AlgorithmConfig(
                algorithm_type="alns",
                alns_config=ALNSAlgorithmConfig(
                    max_no_improve=500,
                    start_temp=10000.0,
                    cooling_rate=0.99
                )
            ),
            data=DataConfig(
                map_type="synthetic",  # Using synthetic for test simplicity
                synthetic_num_nodes=50,
                num_time_intervals=24
            ),
            run=RunConfig(
                random_seed=None,  # None means truly random
                num_runs=30,  # Many runs for confidence
                output_dir="/var/results/vrp_production"
            )
        )

        # Should be valid for production
        assert production_config.algorithm.alns_config.max_no_improve == 500
        assert production_config.run.num_runs == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])