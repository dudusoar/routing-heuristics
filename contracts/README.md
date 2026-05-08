# Contract Tests

Automated tests ensuring playground demonstrations match actual code behavior.

## Purpose

Contract tests verify that the playground doesn't "lie" to users:
- ✅ Reproducibility: Same seed + same config → same result
- ✅ Feasibility: "Feasible" badge → solution actually feasible
- ✅ Evaluation: Displayed cost = actual objective value
- ✅ Validation: Invalid inputs rejected with clear messages

**Why this matters:** When users learn through the playground, they must trust that what they see reflects reality. Contract tests maintain this trust.

## Running Tests

```bash
# From project root
cd E:\Code\Github\routing-heuristics

# Run all contract tests
pytest contracts/ -v

# Run specific test file
pytest contracts/test_reproducibility.py -v

# Run with coverage
pytest contracts/ --cov=playground --cov-report=html
```

## Test Categories

### 1. Reproducibility Contracts

**File:** `test_reproducibility.py`

**Ensures:** Same seed + same config → identical results

```python
def test_same_seed_same_result():
    """Running twice with same seed must produce identical solutions."""
    config = ALNSConfig(max_iterations=100, seed=42)
    instance = generate_test_instance()

    solution1 = run_playground_solver(instance, config)
    solution2 = run_playground_solver(instance, config)

    assert solution1.objective_value == solution2.objective_value
    assert solution1.routes == solution2.routes
```

### 2. Feasibility Contracts

**File:** `test_feasibility.py`

**Ensures:** Playground claims "feasible" → solution actually feasible

```python
def test_feasibility_claim_is_accurate():
    """If playground shows green checkmark, solution must be truly feasible."""
    solution = run_playground_solver(...)

    # What playground displays
    displayed_feasible = playground_ui_shows_feasible(solution)

    # What code says
    actual_feasible = solution.is_feasible()

    assert displayed_feasible == actual_feasible
```

### 3. Objective Value Contracts

**File:** `test_objective_value.py`

**Ensures:** Displayed cost matches actual calculation

```python
def test_displayed_cost_matches_actual():
    """Cost shown in UI must match solution.objective_value."""
    solution = run_playground_solver(...)

    displayed_cost = extract_cost_from_ui(solution)
    actual_cost = solution.objective_value

    assert abs(displayed_cost - actual_cost) < 1e-6  # Floating point tolerance
```

### 4. Validation Contracts

**File:** `test_validation.py`

**Ensures:** Invalid inputs are rejected with helpful messages

```python
def test_negative_vehicles_rejected():
    """Playground must reject num_vehicles < 0."""
    with pytest.raises(ValueError, match="num_vehicles must be positive"):
        run_playground_solver(instance, num_vehicles=-1)

def test_error_message_is_helpful():
    """Error messages must guide users to fix the problem."""
    try:
        run_playground_solver(instance, num_vehicles=-1)
    except ValueError as e:
        assert "positive" in str(e).lower()
        assert "num_vehicles" in str(e)
```

## Test Structure

Each test file follows this pattern:

```python
# contracts/test_*.py
import pytest
from playground.utils.solver_runner import run_playground_solver
from vrp_toolkit.problems.pdptw import PDPTWInstance
from vrp_toolkit.algorithms.alns import ALNSConfig

@pytest.fixture
def simple_instance():
    """Fixture providing a simple test instance."""
    # Generate or load a small, known-good instance
    return generate_simple_pdptw_instance(num_orders=5, seed=42)

@pytest.fixture
def default_config():
    """Fixture providing default ALNS config."""
    return ALNSConfig(
        max_iterations=100,
        start_temp=10.0,
        cooling_rate=0.95
    )

def test_contract_name(simple_instance, default_config):
    """Test description."""
    # Arrange
    ...

    # Act
    result = run_playground_solver(simple_instance, default_config)

    # Assert
    assert ...
```

## Writing New Contract Tests

### Step 1: Identify the Contract

Ask: "What promise does the playground make to the user?"

Examples:
- "Reproducible results with fixed seed"
- "Solutions marked feasible are truly feasible"
- "Cost displayed matches actual calculation"

### Step 2: Write Test

```python
def test_your_contract(simple_instance):
    """Test that [contract] holds."""
    # Setup
    ...

    # Run playground function
    result = playground_function(...)

    # Verify contract
    assert promise == reality
```

### Step 3: Add to CI/CD (Future)

When CI/CD is set up, contract tests will run automatically on every commit.

## Common Patterns

### Pattern 1: Reproducibility Test

```python
def test_reproducibility_for_feature_X():
    config = {...}
    instance = ...

    result1 = run_feature_X(instance, config, seed=42)
    result2 = run_feature_X(instance, config, seed=42)

    assert result1 == result2  # Or use appropriate comparison
```

### Pattern 2: Consistency Test

```python
def test_ui_matches_code():
    solution = run_solver(...)

    ui_value = extract_from_ui(solution)
    code_value = solution.actual_method()

    assert ui_value == code_value
```

### Pattern 3: Validation Test

```python
def test_invalid_input_rejected():
    with pytest.raises(ExpectedError, match="helpful message"):
        run_solver(invalid_param=...)
```

## Test Data

### Fixtures

Use fixtures for common test data:

```python
@pytest.fixture
def small_instance():
    """5 orders, fits in memory, runs fast."""
    return generate_pdptw_instance(num_orders=5, seed=1)

@pytest.fixture
def medium_instance():
    """20 orders, more realistic."""
    return generate_pdptw_instance(num_orders=20, seed=2)

@pytest.fixture
def infeasible_instance():
    """Intentionally infeasible (for negative testing)."""
    return create_infeasible_instance()
```

### Test Instance Generation

```python
def generate_test_instance(num_orders, seed):
    """Generate reproducible test instance."""
    from vrp_toolkit.data.generators import OrderGenerator, DemandGenerator
    from vrp_toolkit.data.map import RealMap

    real_map = RealMap(num_customers=num_orders, num_restaurants=3, seed=seed)
    demand_gen = DemandGenerator(num_customers=num_orders, num_restaurants=3, seed=seed)
    demand_table = demand_gen.generate()

    order_gen = OrderGenerator(
        real_map=real_map,
        demand_table=demand_table,
        time_params={'time_window_length': 30, 'service_time': 5},
        robot_speed=1.0
    )
    order_table = order_gen.generate()

    return PDPTWInstance(order_table=order_table)
```

## Continuous Integration

When CI/CD is configured:

```yaml
# .github/workflows/contracts.yml
name: Contract Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run contract tests
        run: |
          pytest contracts/ -v --cov=playground
```

## Coverage Goals

Target coverage:
- ✅ Core features: 100% (reproducibility, feasibility, evaluation)
- ✅ UI components: 80% (main user flows)
- ⚠️ Edge cases: 50% (nice to have)

Check coverage:
```bash
pytest contracts/ --cov=playground --cov-report=term-missing
```

## Troubleshooting

### Test fails intermittently

**Likely cause:** Non-deterministic behavior (missing seed control)

**Solution:** Ensure all random operations use fixed seeds:
```python
np.random.seed(42)
random.seed(42)
```

### Test fails after code change

**Good!** This is working as intended. The contract test caught a breaking change.

**Action:**
1. Understand why the change broke the contract
2. Either fix the code or update the contract (if contract was wrong)
3. Document the change in CHANGELOG_LEARNINGS.md

### Test is too slow

**Guideline:** Each test should complete in <1 second

**Solutions:**
- Use smaller test instances (5-10 orders instead of 50)
- Reduce max_iterations for tests (100 instead of 5000)
- Cache expensive setup with fixtures

---

## Related Documentation

- **Playground:** `../playground/README.md` - Playground usage guide
- **create-playground skill:** `.claude/skills/create-playground/SKILL.md` - Development workflow
- **VISION:** `../playground/VISION.md` - Why contracts matter for learning

---

**Status:** 🚧 To be created (as playground features are implemented)
**Last Updated:** 2026-01-04
