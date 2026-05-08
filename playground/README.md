# Routing Heuristics Playground

Interactive Streamlit web interface for learning routing heuristics through hands-on exploration.

## Quick Start

### Installation

```bash
# From project root
cd E:\Code\Github\routing-heuristics

# Install Streamlit (if not already installed)
uv pip install streamlit

# Optional: Install playground dependencies
uv pip install plotly folium
```

### Launch Playground

```bash
# From project root
cd playground
streamlit run app.py
```

The playground will open in your browser at `http://localhost:8501`

## Features

### Current (MVP - Stage 1)
🚧 **In Development** - Coming soon!

**Planned for first release:**
- [ ] Problem definition (upload CSV or generate synthetic)
- [ ] ALNS configuration (5-10 key parameters)
- [ ] Run solver and view results
- [ ] Route visualization (2D map)
- [ ] Cost metric display

### Planned (Stage 2)
- [ ] Multi-page app (Problem | Algorithm | Experiments)
- [ ] Seed control for reproducibility
- [ ] Convergence plot (cost vs. iteration)
- [ ] Experiment saving to `runs/` directory
- [ ] Contract test suite

### Future (Stage 3)
- [ ] Learning missions ("Get feasible solution in 30s")
- [ ] Step-by-step operator visualization
- [ ] Parameter impact hints
- [ ] Achievement tracking

## Project Structure

```
playground/
├── app.py                    # Main entry point (home page)
├── pages/                    # Multi-page app sections (future)
│   ├── 1_Problem_Definition.py
│   ├── 2_Algorithm_Config.py
│   └── 3_Experiments.py
├── components/               # Reusable UI components (future)
│   ├── instance_viewer.py
│   ├── route_visualizer.py
│   ├── convergence_plot.py
│   └── metrics_dashboard.py
├── utils/                    # Helper functions (future)
│   ├── state_manager.py
│   ├── export_utils.py
│   └── validation.py
├── README.md                 # This file
├── FEATURES.md               # Feature tracking
└── VISION.md                 # Design philosophy
```

## Usage Guide

### Step 1: Define Problem

**Option A: Upload CSV**
- Click "Upload CSV" button
- Select order table CSV file
- Required columns: `id`, `type`, `x`, `y`, `demand`, `tw_start`, `tw_end`

**Option B: Generate Synthetic**
- Choose "Generate Synthetic"
- Set number of orders (2-50)
- Set random seed for reproducibility
- Click "Generate"

### Step 2: Configure Algorithm

**Basic Parameters:**
- Max Iterations: 100-10000 (default: 1000)
- Start Temperature: 0.1-100.0 (default: 10.0)
- Number of Vehicles: 1-20 (default: 3)
- Random Seed: 0-99999 (default: 42)

**Advanced Parameters** (click to expand):
- Cooling Rate: 0.90-0.99 (default: 0.95)
- Segment Length: 10-500 (default: 100)
- Removal Count: 1-20 (default: 5)
- Shaw Relatedness (p): 1.0-10.0 (default: 4.0)

### Step 3: Run & Visualize

- Click "Run ALNS" button
- Wait for solver to complete
- View results:
  - Total cost metric
  - Route visualization (2D map)
  - Convergence plot (cost over iterations)
  - Feasibility status

### Step 4: Save Experiment (Future)

- Click "Save Experiment" button
- Experiment saved to `runs/YYYY-MM-DD_HH-MM-SS/`
- Contains:
  - `config.json` - Algorithm configuration
  - `solution.json` - Solution routes
  - `metrics.json` - Performance metrics
  - `instance.csv` - Problem instance (for reproducibility)

## Learning Path

Recommended progression for new users:

1. **Explore with defaults** - Generate synthetic instance (10 orders) and run with default ALNS settings
2. **Adjust parameters** - Try different Max Iterations (100 vs. 5000) and observe impact
3. **Compare seeds** - Run same config with different seeds, notice solution variance
4. **Temperature experiments** - Try high temp (50.0) vs. low temp (1.0), understand exploration vs. exploitation
5. **Real-world data** - Upload your own CSV data or use OSMnx-generated data

## Design Philosophy

This playground follows the **"learn by playing"** philosophy:

- 🎮 **Interactive over reading** - Understand through experimentation
- 📊 **Visual over textual** - See algorithm behavior, don't just read about it
- 🔬 **Reproducible** - Same seed = same result (for science!)
- 📈 **Progressive** - Start simple, unlock complexity as you learn

See `VISION.md` for full design rationale.

## Architecture Integration

The playground connects to Routing Heuristics as follows:

```
Streamlit UI (playground/app.py)
    ↓
User Input (sliders, buttons, uploads)
    ↓
Routing Heuristics API Integration
    ├─ vrp_toolkit.problems.pdptw.PDPTWInstance
    ├─ vrp_toolkit.algorithms.alns.ALNSSolver
    ├─ vrp_toolkit.algorithms.alns.ALNSConfig
    ├─ vrp_toolkit.data.generators (OrderGenerator, DemandGenerator)
    └─ vrp_toolkit.visualization.problem.PDPTWVisualizer
    ↓
Streamlit Output (plots, metrics, tables)
```

See `.claude/ARCHITECTURE_MAP.md` for full system architecture.

## Troubleshooting

### Playground won't start
```bash
# Check Streamlit is installed
streamlit --version

# If not, install it
uv pip install streamlit

# Try running from project root
cd E:\Code\Github\routing-heuristics
streamlit run playground/app.py
```

### Import errors
```bash
# Make sure routing-heuristics is installed
cd E:\Code\Github\routing-heuristics
uv pip install -e .
```

### Port already in use
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

## Development

### Adding a New Feature

1. Read `create-playground` skill documentation (`.claude/skills/create-playground/SKILL.md`)
2. Design UI mockup (pen & paper is fine!)
3. Implement in `app.py` or create new component in `components/`
4. Add contract test in `../contracts/` if feature changes behavior
5. Update `FEATURES.md`
6. Update this README

### Code Style

- Use `st.cache_data` for expensive operations
- Manage state with `st.session_state`
- Keep functions small and focused
- Add docstrings for non-trivial functions
- Follow existing UI patterns (see `references/ui_components.md`)

## Contract Testing

Playground features are validated by contract tests in `../contracts/`:

- `test_reproducibility.py` - Same seed → same result
- `test_feasibility.py` - Claimed feasible → actually feasible
- `test_objective_value.py` - Displayed cost = actual cost

Run tests:
```bash
cd E:\Code\Github\routing-heuristics
pytest contracts/ -v
```

## Related Documentation

- **Vision:** `VISION.md` - Design philosophy and learning model
- **Features:** `FEATURES.md` - Feature tracking and roadmap
- **Skills:** `.claude/skills/create-playground/` - Development guide
- **Architecture:** `.claude/ARCHITECTURE_MAP.md` - System overview

---

**Status:** 🚧 In Development (Stage 1 MVP)
**Last Updated:** 2026-01-04
