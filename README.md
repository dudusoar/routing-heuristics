# routing-heuristics

A reusable research framework for vehicle routing heuristics, with current focus on PDPTW, ALNS, tutorials, and solver experimentation.

> **Status**: Phase 1 Complete - Ready for installation and basic usage

## 🚀 Quick Installation

```bash
# From this repository root
uv venv
uv pip install -e ".[dev]"

# Optional real-world map support
uv pip install -e ".[osmnx]"
```

## 📦 Package Structure

```
routing-heuristics/
├── vrp_toolkit/          # Main Python package
│   ├── problems/         # Problem definitions
│   │   └── pdptw.py     # PDPTW implementation
│   ├── algorithms/       # Solving algorithms
│   │   └── alns/        # Adaptive Large Neighborhood Search
│   ├── data/            # Data generation and loading
│   │   ├── generators.py # Synthetic data
│   │   └── map.py       # Real-world map integration
│   ├── visualization/    # Plotting utilities
│   └── utils/           # Common utilities
├── tutorials/           # Educational notebooks
├── playground/          # Streamlit learning interface
├── contracts/           # Playground and reproducibility contract tests
├── runs/                # Local experiment notes
├── tests/              # Unit tests
└── pyproject.toml      # Package configuration
```

## 🎯 Quick Example

```python
from vrp_toolkit.problems.pdptw import PDPTWInstance
from vrp_toolkit.algorithms.alns.solver import ALNSSolver
from vrp_toolkit.data.generators import OrderGenerator

# Generate a sample instance
generator = OrderGenerator(num_orders=20, num_vehicles=3)
instance = generator.generate_instance()

# Solve with ALNS
solver = ALNSSolver()
solution = solver.solve(instance)

print(f"Best cost: {solution.total_cost}")
print(f"Routes: {solution.routes}")
```

## 🏗️ Core Concepts

### Problem Layer
- **`PDPTWInstance`**: Defines a PDPTW problem with nodes, time windows, and demands
- **`Solution`**: Represents a feasible solution with routes and costs
- **`Node`**: Individual location with pickup/delivery constraints

### Algorithm Layer
- **`ALNSSolver`**: Adaptive Large Neighborhood Search implementation
- **`Operator`**: Destruction and repair operators for ALNS
- Common interface: `Solver.solve(instance) -> Solution`

### Data Layer
- **`OrderGenerator`**: Synthetic order generation
- **`MapLoader`**: Real-world map integration via OSMnx
- **`DistanceMatrix`**: Pre-computed distances between locations

## 📊 Features

### Currently Implemented
- ✅ PDPTW problem definition
- ✅ ALNS algorithm with configurable operators
- ✅ Synthetic data generation
- ✅ Basic visualization
- ✅ Real-world map integration (OSMnx)
- ✅ Seven comprehensive tutorials covering all features

### Coming Soon
- Genetic Algorithm implementation
- Additional VRP variants (CVRP, VRPTW)
- Benchmark suite
- Web visualization interface

## 📚 Tutorials

Start with these interactive notebooks:

1. **`tutorials/01_quickstart.ipynb`** - Basic usage and problem solving
2. **`tutorials/02_real_world_maps.ipynb`** - Real-world street networks with OSMnx
3. **`tutorials/03_custom_problems.ipynb`** - Creating custom PDPTW problems ⭐ NEW!
4. **`tutorials/04_problem_variants.ipynb`** - VRP, CVRP, PDP, PDPTW variants ⭐ NEW!
5. **`tutorials/05_sensitivity_analysis.ipynb`** - Parameter sensitivity analysis
6. **`tutorials/06_custom_algorithms.ipynb`** - Implementing custom heuristics ⭐ NEW!
7. **`tutorials/07_data_generation.ipynb`** - Synthetic data generation ⭐ NEW!

## 🗺️ Real-World Integration

Use real street networks from OpenStreetMap:

```python
from vrp_toolkit.data import create_pdptw_from_osm

# Create PDPTW instance from real location
order_table, dist_matrix, time_matrix, G, node_map = create_pdptw_from_osm(
    place_name="Purdue University, West Lafayette, IN, USA",
    depot_location=(40.4237, -86.9212),
    pickup_locations=[(40.4280, -86.9145), (40.4200, -86.9180)],
    delivery_locations=[(40.4250, -86.9100), (40.4210, -86.9220)],
    cache_file="data/purdue_network.graphml"
)

# Solve and visualize routes on real streets!
```

## 🔧 Development

### Running Tests
```bash
pytest tests/
```

### Code Style
```bash
# Format code
black vrp_toolkit/

# Check style
ruff check vrp_toolkit/
```

### Adding New Algorithms
1. Create new solver class in `vrp_toolkit/algorithms/[name]/`
2. Implement `solve(instance) -> Solution` method
3. Add configuration options
4. Create example in `examples/`

## 📖 API Reference

### Main Classes

#### `PDPTWInstance`
```python
class PDPTWInstance:
    nodes: List[Node]          # All nodes (depot, pickups, deliveries)
    distance_matrix: np.ndarray # Distance between nodes
    vehicle_capacity: float     # Vehicle capacity constraint
    time_horizon: float        # Operating time window
```

#### `ALNSSolver`
```python
class ALNSSolver:
    def __init__(self, max_iterations=1000, ...):
        # Configuration parameters
    
    def solve(self, instance: PDPTWInstance) -> Solution:
        # Main solving method
```

#### `OrderGenerator`
```python
class OrderGenerator:
    def generate_instance(self, num_orders=20, num_vehicles=3) -> PDPTWInstance:
        # Generate synthetic instance
```

## 🤝 Contributing

1. Follow the three-layer architecture (Problem/Algorithm/Data)
2. Add type hints for public APIs
3. Include basic docstrings
4. Add integration tests for new features
5. Update relevant tutorials

## 📄 License

Intended for academic and educational use. See repository LICENSE file for details.

---

**routing-heuristics** - Transforming routing research code into reusable heuristic frameworks.
