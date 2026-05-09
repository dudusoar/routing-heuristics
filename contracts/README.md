# Contract Tests

Contract tests verify that playground-visible behavior matches the actual package behavior.
They are not a replacement for unit tests; they protect the promises made to users through
the Streamlit app and tutorials.

## Contracts To Protect

- Reproducibility: same seed and same config should produce the same result.
- Feasibility: a displayed feasible/infeasible claim should match the solution object.
- Objective value: displayed costs should match the package calculation.
- Validation: invalid inputs should fail with useful errors.

## Run

From the repository root:

```bash
pytest contracts/ -v
```

Run one file:

```bash
pytest contracts/test_reproducibility.py -v
```

## Current Files

```text
contracts/
|-- README.md
`-- test_reproducibility.py
```

Add more contract files as playground-visible behavior stabilizes.

## Writing A Contract

Start with the user-facing promise:

- "Fixed seed reproduces a run."
- "The cost shown in the UI equals the solution objective."
- "A feasible badge means `solution.is_feasible()` is true."

Then write the smallest test that compares the displayed or adapter-level value to the
underlying package value.

Useful patterns:

```python
def test_same_seed_same_result():
    result_1 = run_solver(seed=42)
    result_2 = run_solver(seed=42)

    assert result_1.objective_value == result_2.objective_value
    assert result_1.routes == result_2.routes
```

```python
def test_displayed_cost_matches_solution(solution):
    displayed_cost = format_cost_for_ui(solution)

    assert displayed_cost == solution.objective_function()
```

## Maintenance Guidelines

- Keep contract instances small so tests stay fast.
- Seed every random operation used by a contract.
- If a contract fails after a behavior change, decide whether the code broke the promise or the promise changed.
- If the promise changed, update the playground copy, tests, and relevant docs together.

Related docs:

- `../playground/README.md`
- `../DEVELOPMENT.md`

**Status:** initial contract suite.
