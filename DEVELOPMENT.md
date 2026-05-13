# Development Notes

## Current Direction

This repository is being rebuilt as a clean routing-heuristics toolkit. The old
`vrp_toolkit` package remains archived for reference, but new work should target
`vrp_heuristics/`.

## Architecture

```text
core          -> solver-independent problem and snapshot schema
constraints   -> shared route-profile evaluator plus feasibility rules
objectives    -> scoring over profiles / solutions
solvers       -> candidate generators and metaheuristics
adapters      -> future external-system bridges, e.g. sdr-sidewalk-sim
```

Key design rules:

- Problem definitions must not depend on a specific heuristic.
- Depot and route-terminal semantics belong to `VehicleSpec` /
  `TerminalPolicy`, not to a solver.
- Dynamic execution state belongs to `ProblemSnapshot`, not to
  `ProblemInstance`.
- Constraints should read a shared `RouteProfile`; they should not each rebuild
  route timing, load, and battery state independently.
- Solvers should enumerate candidates and call `ConstraintSet`, not branch on
  individual constraint types.

## Archive

`archive/legacy_vrp_toolkit_2026_05_12/` contains the previous package for
reference during migration:

- `problems/pdptw.py`: legacy PDPTW instance, solution, feasibility, objective
- `algorithms/alns/`: legacy ALNS solver and operators
- `data/`, `visualization/`, `utils/`: legacy support modules

Do not add new features to the archive. Port concepts into the new package.
