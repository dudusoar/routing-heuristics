# Tutorial Notebook Tests

This directory contains tests that execute the tutorial notebooks and catch broken examples.

## Scope

The suite validates that the notebooks in `tutorials/` can run against the current package:

1. `01_quickstart.ipynb`
2. `02_real_world_maps.ipynb`
3. `03_custom_problems.ipynb`
4. `04_problem_variants.ipynb`
5. `05_sensitivity_analysis.ipynb`
6. `06_custom_algorithms.ipynb`
7. `07_data_generation.ipynb`

## Requirements

```bash
uv pip install -e ".[dev]"
uv pip install jupyter nbconvert
```

OSMnx-backed notebooks also need:

```bash
uv pip install -e ".[osmnx]"
```

## Run

From the repository root:

```bash
python tests/tutorials/test_notebooks.py
```

## Maintenance

When adding a tutorial:

- Add the notebook to the tutorial test list in `test_notebooks.py`.
- Keep the notebook runtime small enough for local validation.
- Update this README's tutorial list.

The test checks execution success, imports, and timeout behavior. It does not verify visual
quality or benchmark-level correctness.
