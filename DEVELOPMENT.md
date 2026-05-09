# Development Roadmap

> Current status: the reusable routing-heuristics framework has been split out from the
> TRE paper code. The repository is being kept as a clean, standalone toolkit with
> package code, tutorials, tests, contracts, and a Streamlit playground.

## Project Goals

Completed:

- Migrated the reusable VRP/PDPTW code into an installable Python package.
- Established the three-layer package shape: problems, algorithms, and data.
- Added ALNS as the first implemented solver family.
- Added synthetic data generation and OSMnx-based map support.
- Added tutorial notebooks for common learning and validation workflows.
- Added a Streamlit playground for interactive experimentation.

In progress:

- Cleaning public documentation and removing local agent/project-control artifacts.
- Tightening API consistency around solver configuration and result objects.
- Expanding contract tests for playground-visible behavior.
- Preparing the project for independent maintenance as a reusable toolkit.

## Short-Term Work

1. API cleanup

- Normalize solver interfaces across algorithms.
- Make random seed handling explicit and reproducible.
- Expose cost history or iteration logs when a solver supports them.
- Keep UI-facing adapters thin and tested.

2. Playground quality

- Keep the current quickstart and problem-variants flows stable.
- Add tests for claims shown in the UI: reproducibility, feasibility, and objective values.
- Improve experiment export without tracking generated `runs/` artifacts in Git.
- Add real-map workflows only after the package API is stable enough to support them cleanly.

3. Documentation

- Keep `README.md` focused on package installation and usage.
- Keep `playground/README.md` focused on the Streamlit app.
- Keep `contracts/README.md` focused on behavior contracts.
- Avoid publishing local agent notes, stale test snapshots, and generated experiment logs.

## Longer-Term Work

Algorithm extensions:

- Genetic Algorithm implementation.
- Tabu Search implementation.
- Algorithm comparison and benchmarking helpers.

Problem and data extensions:

- Additional VRP variants such as CVRP, VRPTW, multi-depot VRP, and richer PDPTW settings.
- Benchmark instance loaders such as Solomon and Li & Lim.
- More robust real-map examples.

Research and teaching support:

- Reproducible experiment cards.
- Tutorial updates aligned with the stable API.
- Course-friendly examples and visual explanations.

## Architecture Principles

The package should preserve a simple separation:

```text
Problem layer   -> defines instances and solutions
Algorithm layer -> solves instances through consistent solver interfaces
Data layer      -> generates or loads synthetic, map-based, and benchmark data
```

Guidelines:

- Problem definitions should not depend on a specific heuristic.
- Solver classes should accept explicit configuration and return inspectable results.
- Data generators should be reproducible when given seeds.
- Playground and tutorial code should use public package APIs rather than private internals when possible.

## Testing Strategy

Current test areas:

- Unit tests for package components.
- Integration tests for end-to-end workflows.
- Tutorial execution tests for notebook examples.
- Contract tests for playground-facing behavior.

Planned improvements:

- Add regression tests around solver reproducibility.
- Add benchmark smoke tests with small instances.
- Add CI once the public API and dependency set settle.

## Repository Hygiene

Tracked files should stay focused on source, tests, tutorials, contracts, and concise documentation.

Ignored local files include:

- Python caches and test caches.
- OSMnx/cache outputs and generated `.graphml` files.
- Generated `data/` artifacts.
- Playground experiment output under `runs/`.
- Local agent context under `.claude/`.

If a generated artifact becomes important enough to preserve, promote it deliberately with a short README explaining why it belongs in the repository.

**Last updated:** 2026-05-08
