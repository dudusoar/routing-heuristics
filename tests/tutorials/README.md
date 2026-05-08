# Tutorial Notebooks Test Suite

This directory contains tests for validating that all Routing Heuristics tutorial notebooks can execute successfully.

## 📁 Structure

```
tests/tutorials/
├── README.md              # This file
└── test_notebooks.py      # Main test script for all tutorials
```

## 🎯 Purpose

Validate that all 7 tutorial notebooks in `routing-heuristics/tutorials/` can:
- Execute without errors
- Complete within reasonable time limits
- Work with the current routing-heuristics codebase

## 📚 Tested Tutorials

1. **01_quickstart.ipynb** - Basic usage and quickstart guide
2. **02_real_world_maps.ipynb** - Using real-world maps with OSMnx
3. **03_custom_problems.ipynb** - Creating custom PDPTW instances
4. **04_problem_variants.ipynb** - VRP, CVRP, PDP, PDPTW variants
5. **05_sensitivity_analysis.ipynb** - Parameter sensitivity analysis
6. **06_custom_algorithms.ipynb** - Implementing custom heuristics
7. **07_data_generation.ipynb** - Synthetic data generation

## 🚀 Usage

### Prerequisites

Install required dependencies:
```bash
# Install routing-heuristics in development mode
cd routing-heuristics
pip install -e .

# Install notebook testing dependencies
pip install jupyter nbconvert
```

### Run All Tests

```bash
cd routing-heuristics/tests/tutorials
python test_notebooks.py
```

### Expected Output

```
================================================================================
VRP-TOOLKIT TUTORIAL NOTEBOOKS TEST SUITE
================================================================================

Checking dependencies...
  [OK] jupyter installed
  [OK] nbconvert installed
  [OK] vrp_toolkit importable

================================================================================
Testing: Quickstart Tutorial
File: 01_quickstart.ipynb
================================================================================
[OK] Quickstart Tutorial executed successfully
  Duration: 12.3s

... (continues for all tutorials)

================================================================================
TEST SUMMARY
================================================================================

[PASS]   - Quickstart Tutorial                      (12.3s)
[PASS]   - Real World Maps Tutorial                 (25.1s)
[PASS]   - Custom Problems Tutorial                 (15.8s)
[PASS]   - Problem Variants Tutorial                (18.2s)
[PASS]   - Sensitivity Analysis Tutorial            (45.3s)
[PASS]   - Custom Algorithms Tutorial               (22.7s)
[PASS]   - Data Generation Tutorial                 (19.4s)

================================================================================
Total: 7/7 notebooks passed
Total time: 158.8s
================================================================================

*** ALL TUTORIALS PASSED! ***
```

## ⏱️ Performance Notes

- **Timeout**: Each notebook has a 300-second (5-minute) timeout
- **Expected Duration**: Most tutorials complete in 10-30 seconds
- **Long-running**: Tutorial 05 (sensitivity analysis) may take 40-60 seconds
- **Total Time**: All 7 tutorials typically complete in 2-3 minutes

## 🐛 Troubleshooting

### ImportError: No module named 'vrp_toolkit'

**Solution**: Install routing-heuristics in development mode:
```bash
cd routing-heuristics
pip install -e .
```

### ImportError: No module named 'jupyter' or 'nbconvert'

**Solution**: Install notebook dependencies:
```bash
pip install jupyter nbconvert
```

### Notebook execution timeout

**Cause**: Tutorial is taking too long (> 5 minutes)
**Solution**:
- Check if the notebook has computationally expensive cells
- Increase timeout in `test_notebooks.py` if needed
- Run the notebook manually to identify slow cells

### Missing OSMnx for Tutorial 02

**Solution**: Install OSMnx:
```bash
pip install osmnx
```

## 📝 Test Details

### How It Works

1. **Dependency Check**: Verifies jupyter, nbconvert, and vrp_toolkit are installed
2. **Notebook Execution**: Uses `jupyter nbconvert --execute` to run each notebook
3. **Error Detection**: Captures execution errors and timeouts
4. **Cleanup**: Removes temporary executed notebook files
5. **Summary**: Reports pass/fail status for each tutorial

### What Gets Tested

- ✅ All code cells execute without exceptions
- ✅ Imports work correctly
- ✅ Data generation produces valid results
- ✅ Solver executes successfully
- ✅ Visualizations render without errors

### What Doesn't Get Tested

- ❌ Output correctness (only checks for execution errors)
- ❌ Performance benchmarks
- ❌ Visual output quality
- ❌ Interactive features (notebooks run in batch mode)

## 🔧 Maintenance

### Adding New Tutorials

When adding a new tutorial to `routing-heuristics/tutorials/`:

1. Add the notebook to the `TUTORIALS` list in `test_notebooks.py`:
   ```python
   TUTORIALS = [
       # ... existing tutorials ...
       ("08_new_tutorial.ipynb", "New Tutorial Description"),
   ]
   ```

2. Run tests to verify it executes correctly

3. Update this README with the new tutorial in the "Tested Tutorials" section

### Modifying Timeout

If tutorials consistently need more time:

1. Edit `test_notebooks.py`
2. Change the `timeout` parameter in the `test_notebook()` call
3. Default is 300 seconds (5 minutes)

### CI/CD Integration

To integrate with continuous integration:

```yaml
# Example GitHub Actions workflow
- name: Test Tutorial Notebooks
  run: |
    cd routing-heuristics
    pip install -e .
    pip install jupyter nbconvert
    python tests/tutorials/test_notebooks.py
```

## 📊 Success Criteria

Tests pass if:
- ✅ All 7 notebooks execute without errors
- ✅ Each notebook completes within timeout (300s)
- ✅ No Python exceptions raised
- ✅ Exit code 0 returned

Tests fail if:
- ❌ Any notebook raises an exception
- ❌ Any notebook times out
- ❌ Dependencies are missing
- ❌ Tutorial files not found

---

**Last Updated**: 2026-01-09
**Total Tutorials**: 7
**Test Coverage**: 100%
