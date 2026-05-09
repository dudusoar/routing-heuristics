# routing-heuristics

A reusable research framework for vehicle-routing heuristics. The current package focuses on
PDPTW instances, ALNS, synthetic data generation, real-map support, tutorial notebooks, and an
interactive Streamlit playground.

## Install

```bash
uv venv
uv pip install -e ".[dev]"
```

Optional real-world map support:

```bash
uv pip install -e ".[osmnx]"
```

## Repository Layout

```text
routing-heuristics/
|-- vrp_toolkit/      # Main Python package
|   |-- problems/     # Problem definitions such as PDPTW
|   |-- algorithms/   # Solver implementations, currently ALNS
|   |-- data/         # Synthetic and map-based data helpers
|   |-- visualization/# Plotting utilities
|   `-- utils/        # Shared helpers
|-- tutorials/        # Notebook examples
|-- playground/       # Streamlit learning interface
|-- contracts/        # Behavior contracts for playground-facing code
|-- tests/            # Unit and integration tests
|-- pyproject.toml    # Package metadata
`-- DEVELOPMENT.md    # Roadmap and maintenance notes
```

Generated data, map caches, and playground experiment outputs are intentionally ignored by Git.

## Core Concepts

Problem layer:

- `PDPTWInstance` represents pickup-delivery problems with time windows.
- `PDPTWSolution` represents routes, objective values, and feasibility checks.

Algorithm layer:

- `ALNSSolver` exposes the unified solver interface.
- `ALNS` and `ALNSConfig` expose the lower-level adaptive large neighborhood search runner.

Data layer:

- `RealMap` builds synthetic coordinate maps for examples.
- `DemandGenerator` and `OrderGenerator` produce PDPTW order tables.
- OSMnx extras support real street-network workflows.

## Tutorials

The tutorial notebooks cover:

1. Basic quickstart workflow.
2. Real-world maps with OSMnx.
3. Custom PDPTW problems.
4. Problem variants.
5. Parameter sensitivity analysis.
6. Custom algorithms.
7. Synthetic data generation.

Tutorial tests live under `tests/tutorials/`.

## Playground

Run the interactive app with:

```bash
streamlit run playground/app.py
```

The app currently supports synthetic PDPTW generation, ALNS configuration, route visualization,
problem-variant presets, and local experiment export. See `playground/README.md`.

## Testing

```bash
pytest tests/
pytest contracts/ -v
```

Notebook execution tests require Jupyter and nbconvert:

```bash
python tests/tutorials/test_notebooks.py
```

## Development

Common maintenance commands:

```bash
black vrp_toolkit tests contracts playground
ruff check vrp_toolkit tests contracts playground
python -m compileall -q vrp_toolkit playground contracts tests run_tests.py
```

See `DEVELOPMENT.md` for roadmap and repository hygiene notes.

## License

MIT. See `pyproject.toml` and the repository license file when present.
