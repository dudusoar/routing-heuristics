# Experiment Log

Index of all saved playground experiments with key metrics and configurations.

## Purpose

This file maintains a searchable record of all experiments run through the playground, making it easy to:
- Find previous experiments by date, config, or performance
- Compare experiment results
- Reproduce successful runs
- Track learning progress

## Log Format

```markdown
### YYYY-MM-DD_HH-MM-SS - [Experiment Name/Description]

**Config:**
- Algorithm: ALNS
- Max Iterations: 1000
- Start Temperature: 10.0
- Seed: 42

**Instance:**
- Type: Synthetic PDPTW
- Orders: 20
- Vehicles: 3

**Results:**
- Best Cost: 1234.56
- Feasible: ✅ Yes
- Runtime: 45.2s
- Iterations: 1000

**Notes:**
[Any observations, insights, or follow-up ideas]

**Files:**
- runs/YYYY-MM-DD_HH-MM-SS/config.json
- runs/YYYY-MM-DD_HH-MM-SS/solution.json
- runs/YYYY-MM-DD_HH-MM-SS/metrics.json
- runs/YYYY-MM-DD_HH-MM-SS/instance.csv

---
```

## Experiment Index

**Total Experiments:** 0
**Last Updated:** 2026-01-04

---

<!-- Experiments will be logged below in reverse chronological order -->

### Example Entry (Template)

**Config:**
- Algorithm: ALNS
- Max Iterations: 1000
- Start Temperature: 10.0
- Cooling Rate: 0.95
- Seed: 42

**Instance:**
- Type: Synthetic PDPTW
- Orders: 20
- Vehicles: 3
- Area: 100x100

**Results:**
- Best Cost: 1234.56
- Feasible: ✅ Yes
- Runtime: 45.2s
- Iterations Completed: 1000
- Improvement: 15.3% from initial

**Notes:**
This is a template. Actual experiments will be logged here automatically when playground save feature is implemented.

**Files:**
- runs/example/config.json
- runs/example/solution.json
- runs/example/metrics.json
- runs/example/instance.csv

---

## Search Tips

### Find experiments by parameter:
```bash
# Find all experiments with seed=42
grep "Seed: 42" runs/EXPERIMENTS_LOG.md

# Find high-cost solutions
grep "Best Cost:" runs/EXPERIMENTS_LOG.md | grep -E "[0-9]{4,}"

# Find experiments on specific date
grep "### 2026-01-05" runs/EXPERIMENTS_LOG.md
```

### Find best performing experiment:
```bash
# Extract all costs and sort
grep "Best Cost:" runs/EXPERIMENTS_LOG.md | sort -n
```

## Automated Logging

Experiments are automatically logged when using playground's "Save Experiment" feature:

1. Run experiment in playground
2. Click "Save Experiment" button
3. Entry is appended to this file
4. Experiment files saved to `runs/YYYY-MM-DD_HH-MM-SS/`

**Implementation:** See `playground/utils/export_utils.py` (to be created)

## Related Documentation

- **Playground:** `../playground/README.md` - How to run and save experiments
- **CHANGELOG_LEARNINGS:** `../.claude/CHANGELOG_LEARNINGS.md` - Bug fixes and insights

---

**Note:** This file will be populated as playground features are implemented and users begin saving experiments.
