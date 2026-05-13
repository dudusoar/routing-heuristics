# routing-heuristics

A compact routing-heuristics toolkit for VRP / PDP / PDPTW-style research.

The current codebase is intentionally small. Legacy `vrp_toolkit` code from the
TRE paper extraction is archived under `archive/legacy_vrp_toolkit_2026_05_12/`
for reference while the new package is rebuilt around solver-independent problem
and constraint interfaces.

## Package Layout

```text
vrp_heuristics/
|-- core/          # ProblemInstance, ProblemSnapshot, vehicles, requests, routes
|-- constraints/   # Route profile evaluator and composable constraints
|-- objectives/    # Objective functions over route profiles
`-- solvers/       # Candidate generators such as greedy insertion
```

The main design boundary is:

```text
ProblemInstance + ProblemSnapshot
-> solver generates candidate routes
-> RouteEvaluator builds a shared route profile
-> ConstraintSet evaluates feasibility
-> Objective scores feasible candidates
```

Solvers do not own problem semantics such as depot, terminal policy, battery,
capacity, or time windows. Those belong to the core problem/snapshot schema and
the constraint layer.

## Minimal Example

```python
from vrp_heuristics import (
    GreedyInsertionSolver,
    MatrixCostProvider,
    ProblemInstance,
    RequestSpec,
    TerminalPolicy,
    VehicleSpec,
)

cost = MatrixCostProvider(
    distance_matrix=[
        [0, 1, 3],
        [1, 0, 2],
        [3, 2, 0],
    ]
)
problem = ProblemInstance(
    requests={
        "R1": RequestSpec("R1", pickup_node=1, dropoff_node=2),
    },
    vehicles={
        "V1": VehicleSpec(
            "V1",
            start_depot=0,
            end_depot=0,
            terminal_policy=TerminalPolicy("return_to_depot"),
            capacity_weight=1.0,
        ),
    },
    cost_provider=cost,
)
solution = GreedyInsertionSolver().solve(problem)
print(solution.routes["V1"].stops)
```

## Development

```bash
python -m compileall -q vrp_heuristics
uv run python -c "import vrp_heuristics; print(vrp_heuristics.__all__)"
```
