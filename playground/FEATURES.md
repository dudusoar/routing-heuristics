# Playground Features

Feature tracking for the Routing Heuristics interactive playground.

**Last Updated:** 2026-01-05

---

## Legend

- ✅ **Stable** - Feature complete and tested
- 🚧 **Beta** - Implemented but may have issues
- 🔮 **Planned** - On roadmap, not yet implemented
- ❌ **Deprecated** - No longer supported

---

## Stage 1: MVP (Minimal Viable Playground)

**Target:** Get something playable in 1-2 evenings

### Problem Definition
- 🔮 Upload CSV file (order table) - *Planned for Stage 2*
- 🚧 Generate synthetic instance (adjustable size, seed) - *Implemented but has bug*
- ✅ View instance summary (orders, nodes, vehicles) - *Stable*
- 🔮 Select from example instances (small/medium/large) - *Planned for Stage 2*

### Algorithm Configuration
- ✅ ALNS configuration panel - *Stable*
  - Max iterations slider (100-5000)
  - Start temperature input (0.1-100.0)
  - Number of vehicles input (1-10)
  - Random seed input (0-99999)
- ✅ Advanced parameters (in expander) - *Stable*
  - Cooling rate slider (0.90-0.99)
  - Segment length input (10-500)
  - Battery capacity input (1.0-100.0)
  - *Note: Some parameters differ from original plan*

### Solver Execution
- ✅ Run button - *Stable*
- ✅ Progress indicator (spinner) - *Stable*
- 🔮 Cancel button (optional) - *Planned for Stage 2*

### Results Display
- ✅ Total cost metric (large display) - *Stable*
- ✅ Feasibility badge (✅/❌) - *Stable*
- ✅ Route count - *Stable*
- ✅ Route visualization (2D map with matplotlib) - *Stable*
- ✅ Convergence plot (cost vs iteration) - *Stable*
- ✅ Route details table - *Stable*
- 🔮 Basic metrics table (runtime, iterations) - *Planned for Stage 2*

### Documentation
- ✅ playground/README.md created
- ✅ playground/VISION.md created
- ✅ playground/FEATURES.md created (this file)

---

## Stage 2: Explainability & Quality

**Target:** Make learning actionable and reliable

### Multi-Page Structure
- 🔮 Home page (introduction)
- 🔮 Page 1: Problem Definition
- 🔮 Page 2: Algorithm Configuration
- 🔮 Page 3: Experiments & Comparison

### Reproducibility
- 🔮 Seed control for all random operations
- 🔮 "Reproduce Run" button (from saved experiment)
- 🔮 Seed displayed in results

### Visualization Enhancements
- 🔮 Convergence plot (cost vs. iteration)
- 🔮 Interactive plots (plotly instead of matplotlib)
- 🔮 Route details table (expandable)
- 🔮 Constraint violation details (if infeasible)

### Experiment Management
- 🔮 Save experiment button
  - Saves to `runs/YYYY-MM-DD_HH-MM-SS/`
  - Includes config.json, solution.json, metrics.json, instance.csv
- 🔮 Load saved experiment (from dropdown)
- 🔮 Export experiment as JSON
- 🔮 Auto-log to `runs/EXPERIMENTS_LOG.md`

### Contract Testing
- 🔮 Reproducibility test (same seed → same result)
- 🔮 Feasibility test (claim matches reality)
- 🔮 Objective value test (display matches calculation)
- 🔮 Validation test (invalid inputs rejected)

### Documentation
- 🔮 playground/ARCHITECTURE.md (technical docs)
- ✅ contracts/README.md created
- ✅ runs/EXPERIMENTS_LOG.md created

---

## Stage 3: Gamified Learning

**Target:** Self-driven learning without instructor

### Learning Missions
- 🔮 Mission system (ordered challenges)
  - Mission 1: "Get any feasible solution"
  - Mission 2: "Reduce cost below X in Y seconds"
  - Mission 3: "Improve initial solution by 10%"
  - Mission 4: "Find global optimum (known instance)"
  - Mission 5: "Design custom operator"
- 🔮 Progress tracking (missions completed)
- 🔮 Hints system ("Try adjusting temperature...")
- 🔮 Achievement unlocks

### Step-by-Step Visualization
- 🔮 Single-step mode (run one iteration at a time)
- 🔮 Operator impact visualization
  - Before/after route comparison
  - Cost delta highlighting
  - Constraint change summary
- 🔮 Animation of search process

### Parameter Impact
- 🔮 Parameter hints (contextual explanations)
- 🔮 "What if?" mode (compare two configs side-by-side)
- 🔮 Sensitivity analysis (vary one param, observe impact)

### Advanced Features
- 🔮 Custom operator workshop (define your own)
- 🔮 Algorithm comparison (ALNS vs. GA)
- 🔮 Real-time search visualization
- 🔮 Export publication-ready figures

---

## Integration Features

### OSMnx Integration
- 🔮 Load real street network (by place name)
- 🔮 Select nodes from map
- 🔮 Generate PDPTW instance from network
- 🔮 Visualize routes on actual streets

### Problem Variants
- 🔮 VRP (basic routing)
- 🔮 CVRP (capacity constraints)
- 🔮 VRPTW (time windows)
- ✅ PDPTW (pickup-delivery with time windows) - supported via backend

### Multiple Algorithms
- ✅ ALNS - supported via backend
- 🔮 Genetic Algorithm (when implemented)
- 🔮 Tabu Search (when implemented)
- 🔮 Hybrid algorithms

---

## Quality of Life Features

### UI/UX
- 🔮 Dark mode toggle
- 🔮 Keyboard shortcuts
- 🔮 Mobile-responsive layout
- 🔮 Accessibility (WCAG 2.1 AA)

### Performance
- 🔮 Cached expensive operations
- 🔮 Background solver execution
- 🔮 Progress streaming (live updates)
- 🔮 Result caching (avoid re-runs)

### Help & Documentation
- 🔮 Inline tooltips (parameter descriptions)
- 🔮 Tutorial walkthrough (first-time users)
- 🔮 FAQ section
- 🔮 Video tutorials (future)

---

## Technical Debt & Maintenance

### Code Quality
- 🔮 Type hints for all functions
- 🔮 Comprehensive docstrings
- 🔮 Code style enforcement (black, flake8)
- 🔮 Modular component structure

### Testing
- 🔮 Contract test suite (5+ tests)
- 🔮 UI component tests
- 🔮 End-to-end smoke tests
- 🔮 Performance benchmarks

### Deployment
- 🔮 Docker containerization
- 🔮 Streamlit Cloud deployment
- 🔮 CI/CD pipeline (GitHub Actions)
- 🔮 Automated testing on commits

---

## Known Limitations

*None yet - playground is in development*

**Planned limitations (to be mindful of):**
- Initial version supports only ALNS algorithm
- Limited to PDPTW problems initially
- Requires desktop browser (mobile support in Stage 2)

---

## Feature Requests

**How to request:**
1. Create GitHub issue with label `playground-feature`
2. Describe use case and expected behavior
3. Include mockup/sketch if applicable

**Current requests:**
*None yet*

---

## Related Documentation

- **README:** `README.md` - Usage guide
- **VISION:** `VISION.md` - Design philosophy
- **Skill:** `.claude/skills/create-playground/SKILL.md` - Development guide
- **Architecture:** `.claude/ARCHITECTURE_MAP.md` - System integration

---

**Maintained by:** `create-playground` skill
**Status:** 🚧 Under active development (Stage 1 MVP mostly complete, bug fixes needed)
