# Development Roadmap

> **Current Status**: routing-heuristics framework split out from TRE paper code | API cleanup pending

This document outlines the ongoing development plan for transforming the research code into a reusable VRP framework.

---

## 🎯 Project Goals

### Completed ✅
- **Phase 1: Migration** (Dec 2025)
  - All 9 files migrated from research code to framework
  - Package installable via `pip install -e .`
  - Basic tutorials operational

- **Phase 2: Refactoring** (Jan 2026)
  - Three-layer architecture (Problem/Algorithm/Data)
  - Unified Solver interface for algorithm extensibility
  - Comprehensive test suite (40/40 ALNS tests passing)
  - OSMnx integration for real-world street networks
  - 7 progressive tutorials covering all features
  - Automated validation (paper-code: 4/4 tests passing)

### In Progress 🚧
- **Phase 3: Extension** (Q1 2026 - 75% complete)
  - ✅ OSMnx real-world map integration
  - ✅ Interactive Streamlit playground (Stage 1 MVP)
  - ✅ Tutorial system (7 notebooks)
  - ✅ Playground Tab 2: Problem variants explorer
  - 🔄 Additional algorithm implementations (GA, Tabu Search)
  - 🔄 Benchmark dataset integration (Solomon, Li & Lim)

---

## 📋 Upcoming Work

### Short-term (Next 3-6 months)

**1. Algorithm Extensions**
- Genetic Algorithm (GA) implementation
- Tabu Search for PDPTW
- Algorithm comparison framework
- Performance benchmarking tools

**2. Playground Enhancement (Stage 2)**
- Operator performance visualization
- Solution evolution animation
- Parameter sensitivity charts
- Algorithm comparison mode

**3. Benchmark Integration**
- Solomon VRPTW instances
- Li & Lim PDPTW instances
- Standardized evaluation metrics
- Leaderboard system

**4. Documentation & Publishing**
- API reference documentation
- Architecture decision records
- PyPI package publishing
- Project website/landing page

### Long-term (6-12 months)

**5. Advanced Features**
- Dynamic/online routing variants
- Multi-objective optimization
- Uncertainty handling extensions
- Real-time visualization dashboard

**6. Community & Education**
- Video tutorial series
- Course materials for VRP education
- Contribution guidelines
- Academic collaboration framework

**7. Additional VRP Variants**
- Capacitated VRP (CVRP)
- VRP with Time Windows (VRPTW)
- Multi-depot VRP (MDVRP)
- Rich VRP problem configurations

---

## 🏗️ Architecture Vision

The framework follows a three-layer design enabling modularity and extensibility:

```
Problem Layer    → Define instances (PDPTW, CVRP, etc.)
     ↓
Algorithm Layer  → Solve instances (ALNS, GA, Tabu, etc.)
     ↓
Data Layer      → Generate/load data (synthetic, OSMnx, benchmarks)
```

**Key Principles:**
- ✅ Problem definitions independent of algorithms
- ✅ Algorithms work with any VRPProblem interface
- ✅ Easy to add new variants without modifying existing code
- ✅ Tutorial-first documentation approach

---

## 🧪 Testing Strategy

**Current Coverage:**
- Unit tests: 40+ tests for ALNS implementation
- Integration tests: End-to-end workflow validation
- Paper-code validation: 4/4 component tests passing
- Tutorial execution: All 7 notebooks validated
- Playground features: 6/6 functional tests passing

**Planned Additions:**
- Benchmark regression tests
- Cross-algorithm comparison tests
- Performance profiling suite
- Continuous integration (GitHub Actions)

---

## 📦 Package Structure

```
routing-heuristics/
├── vrp_toolkit/           # Core package
│   ├── problems/          # Problem definitions
│   ├── algorithms/        # Solving algorithms
│   │   ├── alns/         # ✅ Implemented
│   │   ├── ga/           # 🔄 Planned
│   │   └── tabu/         # 🔄 Planned
│   ├── data/             # Data generation & loading
│   ├── visualization/     # Plotting tools
│   └── utils/            # Common utilities
├── tutorials/             # ✅ 7 Jupyter notebooks
├── playground/            # ✅ Interactive Streamlit app
├── tests/                # ✅ Comprehensive test suite
└── benchmarks/           # 🔄 Standard problem instances
```

---

## 🤝 Contribution Areas

We welcome contributions in:

1. **Algorithm Implementations**
   - New metaheuristics (Simulated Annealing, Ant Colony, etc.)
   - Exact methods (Branch-and-bound, Column generation)
   - Hybrid approaches

2. **Problem Variants**
   - Additional VRP problem types
   - Domain-specific extensions
   - Multi-objective formulations

3. **Data & Visualization**
   - Real-world case studies
   - Enhanced plotting capabilities
   - Interactive dashboards

4. **Documentation & Education**
   - Tutorial improvements
   - Code examples
   - Teaching materials

---

## 🔬 Research Integration

This framework enables:

- **Rapid prototyping** for new VRP research
- **Fair algorithm comparison** with standardized interfaces
- **Reproducible experiments** with version-controlled configurations
- **Educational use** in optimization courses

Researchers can contribute their algorithms while maintaining clean separation from problem definitions, enabling easy benchmarking and comparison.

---

## 📅 Development Status

| Component | Status | Priority |
|-----------|--------|----------|
| Paper Code Validation | ✅ Complete | Completed |
| ALNS Implementation | ✅ Complete | Completed |
| OSMnx Integration | ✅ Complete | Completed |
| Tutorial System | ✅ Complete | Completed |
| Interactive Playground | 🔄 Stage 1 MVP | High |
| Genetic Algorithm | 📋 Planned | High |
| Tabu Search | 📋 Planned | Medium |
| Benchmark Suite | 📋 Planned | Medium |
| PyPI Publishing | 📋 Planned | Medium |
| Project Website | 📋 Planned | Low |

---

## 💻 Development Workflow

The project uses **11 custom Claude Code skills** for automated workflows:

- `build-session-context` - Session startup with project status
- `migrate-module` - Code migration guidance
- `update-task-board` - Progress tracking
- `integrate-road-network` - OSMnx integration helper
- `create-tutorial` - Tutorial generation assistant
- `manage-python-env` - UV package manager reference
- And 5+ more for debugging, testing, and documentation

See [`.claude/SKILLS.md`](.claude/SKILLS.md) for complete documentation.

---

## 📞 Contact & Collaboration

This is an **active research project** transforming academic code into production-quality tools.

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Share ideas and ask questions in GitHub Discussions
- **Contributions**: See individual directory READMEs for contribution guidelines
- **Research Collaboration**: Open to academic partnerships and extensions

---

**Last Updated**: 2026-01-12
**Framework Status**: 95% complete (Phase 3 in progress)
**Paper Code Status**: ✅ Validated and published
