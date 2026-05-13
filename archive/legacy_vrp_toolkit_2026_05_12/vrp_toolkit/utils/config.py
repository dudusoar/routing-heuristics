"""
Configuration management for Routing Heuristics.

This module provides configuration loading, validation, and management
for the three-layer architecture (Problem, Algorithm, Data).
"""

import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class ProblemConfig:
    """Configuration for VRP problem instances."""
    
    # Problem type
    problem_type: str = "pdptw"  # "pdptw", "cvrp", "vrptw", etc.
    
    # PDPTW-specific parameters
    num_vehicles: int = 4
    vehicle_capacity: float = 6.0
    battery_capacity: float = 8.0
    battery_consume_rate: float = 1.0
    penalty_unvisited: float = 100.0
    penalty_delayed: float = 15.0
    
    # Time window parameters
    time_window_length: int = 60
    service_time: int = 5
    extra_time: int = 15
    big_time: int = 1000
    
    # Robot parameters
    robot_speed: float = 1.0  # distance units per minute
    
    def validate(self) -> List[str]:
        """Validate configuration parameters.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if self.num_vehicles <= 0:
            errors.append("num_vehicles must be positive")
        if self.vehicle_capacity <= 0:
            errors.append("vehicle_capacity must be positive")
        if self.battery_capacity <= 0:
            errors.append("battery_capacity must be positive")
        if self.battery_consume_rate <= 0:
            errors.append("battery_consume_rate must be positive")
        if self.penalty_unvisited < 0:
            errors.append("penalty_unvisited must be non-negative")
        if self.penalty_delayed < 0:
            errors.append("penalty_delayed must be non-negative")
        if self.robot_speed <= 0:
            errors.append("robot_speed must be positive")
            
        return errors


@dataclass
class ALNSAlgorithmConfig:
    """Configuration for ALNS algorithm."""
    
    # Operator parameters
    num_removal: int = 5
    p: float = 4.0  # Shaw removal parameter
    k: int = 3  # Regret insertion parameter
    L_max: int = 5  # SISR removal max string length
    avg_remove_order: float = 2.0  # SISR average remove order
    
    # ALNS parameters
    max_no_improve: int = 100
    segment_length: int = 100
    num_segments: int = 10
    r: float = 0.1  # Weight update rate
    sigma: List[float] = field(default_factory=lambda: [33.0, 9.0, 13.0])  # Reward scores
    
    # Simulated annealing parameters
    start_temp: float = 10000.0
    cooling_rate: float = 0.99
    
    # Convergence criteria
    cost_ci_obj_diff_threshold: float = 0.1
    cost_ci_window_size: int = 25
    
    # Operator indices
    removal_indices: List[int] = field(default_factory=lambda: [0, 2, 3])  # Shaw, Worst, SISR
    repair_indices: List[int] = field(default_factory=lambda: [0, 1])  # Greedy, Regret
    
    # Charging station parameters
    charging_station_index: Optional[int] = None
    
    def validate(self) -> List[str]:
        """Validate ALNS configuration parameters."""
        errors = []
        
        if self.num_removal <= 0:
            errors.append("num_removal must be positive")
        if self.max_no_improve <= 0:
            errors.append("max_no_improve must be positive")
        if self.segment_length <= 0:
            errors.append("segment_length must be positive")
        if self.num_segments <= 0:
            errors.append("num_segments must be positive")
        if not (0 < self.cooling_rate < 1):
            errors.append("cooling_rate must be between 0 and 1")
        if self.start_temp <= 0:
            errors.append("start_temp must be positive")
            
        return errors


@dataclass
class AlgorithmConfig:
    """Configuration for solving algorithms."""
    
    algorithm_type: str = "alns"  # "alns", "ga", "tabu", etc.
    alns_config: ALNSAlgorithmConfig = field(default_factory=ALNSAlgorithmConfig)
    
    # Additional algorithm configurations can be added here
    # ga_config: GAAlgorithmConfig = field(default_factory=GAAlgorithmConfig)
    
    def validate(self) -> List[str]:
        """Validate algorithm configuration."""
        errors = []
        
        if self.algorithm_type not in ["alns"]:
            errors.append(f"Unsupported algorithm type: {self.algorithm_type}")
            
        # Validate nested configs
        if self.algorithm_type == "alns":
            errors.extend(self.alns_config.validate())
            
        return errors


@dataclass
class DataConfig:
    """Configuration for data generation and loading."""
    
    # Map type: "synthetic" or "real"
    map_type: str = "synthetic"
    
    # Synthetic map parameters
    synthetic_num_nodes: int = 20
    synthetic_grid_size: float = 100.0
    
    # Real data parameters
    real_node_file: Optional[str] = None
    real_tt_matrix_file: Optional[str] = None
    real_depot_index: int = 15
    real_distance_conversion_factor: Optional[float] = 1609.34  # meters to miles
    
    # Demand generation
    num_time_intervals: int = 6
    demand_per_order: float = 1.0
    
    def validate(self) -> List[str]:
        """Validate data configuration."""
        errors = []
        
        if self.map_type not in ["synthetic", "real"]:
            errors.append(f"Unsupported map type: {self.map_type}")
            
        if self.map_type == "real":
            if not self.real_node_file:
                errors.append("real_node_file is required for real map type")
            if not self.real_tt_matrix_file:
                errors.append("real_tt_matrix_file is required for real map type")
                
        if self.synthetic_num_nodes <= 0:
            errors.append("synthetic_num_nodes must be positive")
        if self.synthetic_grid_size <= 0:
            errors.append("synthetic_grid_size must be positive")
        if self.num_time_intervals <= 0:
            errors.append("num_time_intervals must be positive")
        if self.demand_per_order <= 0:
            errors.append("demand_per_order must be positive")
            
        return errors


@dataclass
class RunConfig:
    """Configuration for experimental runs."""
    
    random_seed: int = 42
    num_runs: int = 1
    output_dir: str = "results"
    save_solutions: bool = True
    save_logs: bool = True
    verbose: bool = True
    
    def validate(self) -> List[str]:
        """Validate run configuration."""
        errors = []
        
        if self.num_runs <= 0:
            errors.append("num_runs must be positive")
            
        return errors


@dataclass
class VRPConfig:
    """Main configuration container for Routing Heuristics."""
    
    problem: ProblemConfig = field(default_factory=ProblemConfig)
    algorithm: AlgorithmConfig = field(default_factory=AlgorithmConfig)
    data: DataConfig = field(default_factory=DataConfig)
    run: RunConfig = field(default_factory=RunConfig)
    
    # Metadata
    config_path: Optional[str] = None
    description: str = "Routing Heuristics Configuration"
    
    def validate(self) -> List[str]:
        """Validate entire configuration."""
        errors = []
        
        errors.extend(self.problem.validate())
        errors.extend(self.algorithm.validate())
        errors.extend(self.data.validate())
        errors.extend(self.run.validate())
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'VRPConfig':
        """Create configuration from dictionary."""
        # Handle nested dataclasses
        problem_dict = config_dict.get('problem', {})
        algorithm_dict = config_dict.get('algorithm', {})
        data_dict = config_dict.get('data', {})
        run_dict = config_dict.get('run', {})
        
        # Extract nested ALNS config
        alns_config_dict = algorithm_dict.get('alns_config', {})
        
        return cls(
            problem=ProblemConfig(**problem_dict),
            algorithm=AlgorithmConfig(
                algorithm_type=algorithm_dict.get('algorithm_type', 'alns'),
                alns_config=ALNSAlgorithmConfig(**alns_config_dict)
            ),
            data=DataConfig(**data_dict),
            run=RunConfig(**run_dict),
            config_path=config_dict.get('config_path'),
            description=config_dict.get('description', 'Routing Heuristics Configuration')
        )


class ConfigLoader:
    """Loader for configuration files (JSON and YAML)."""
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> VRPConfig:
        """Load configuration from file.
        
        Args:
            file_path: Path to configuration file (JSON or YAML)
            
        Returns:
            VRPConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported or invalid
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        # Determine file format
        suffix = file_path.suffix.lower()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            if suffix == '.json':
                config_dict = json.load(f)
            elif suffix in ['.yaml', '.yml']:
                if not YAML_AVAILABLE:
                    raise ImportError(
                        "YAML support requires PyYAML. Install with: pip install pyyaml"
                    )
                config_dict = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported configuration file format: {suffix}")
        
        # Add config path for reference
        config_dict['config_path'] = str(file_path.absolute())
        
        # Create configuration object
        config = VRPConfig.from_dict(config_dict)
        
        # Validate
        errors = config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))
        
        return config
    
    @staticmethod
    def save(config: VRPConfig, file_path: Union[str, Path], 
             format: str = 'json') -> None:
        """Save configuration to file.
        
        Args:
            config: VRPConfig instance to save
            file_path: Path to save configuration file
            format: Output format ('json' or 'yaml')
            
        Raises:
            ValueError: If format is unsupported
        """
        file_path = Path(file_path)
        config_dict = config.to_dict()
        
        # Remove config_path from saved file to avoid absolute paths
        if 'config_path' in config_dict:
            del config_dict['config_path']
        
        if format.lower() == 'json':
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
        elif format.lower() in ['yaml', 'yml']:
            if not YAML_AVAILABLE:
                raise ImportError(
                    "YAML support requires PyYAML. Install with: pip install pyyaml"
                )
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, allow_unicode=True)
        else:
            raise ValueError(f"Unsupported output format: {format}")
    
    @staticmethod
    def create_default() -> VRPConfig:
        """Create default configuration."""
        return VRPConfig()


def load_config(file_path: Union[str, Path]) -> VRPConfig:
    """Convenience function to load configuration from file.
    
    Args:
        file_path: Path to configuration file
        
    Returns:
        VRPConfig instance
    """
    return ConfigLoader.load(file_path)


def save_config(config: VRPConfig, file_path: Union[str, Path], 
                format: str = 'json') -> None:
    """Convenience function to save configuration to file.
    
    Args:
        config: VRPConfig instance
        file_path: Path to save configuration file
        format: Output format ('json' or 'yaml')
    """
    ConfigLoader.save(config, file_path, format)


def create_default_config() -> VRPConfig:
    """Convenience function to create default configuration."""
    return ConfigLoader.create_default()
