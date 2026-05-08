# Routing Heuristics Playground - Design Vision

**Created:** 2026-01-04
**Purpose:** Document the core philosophy and design principles for the interactive playground

---

## Core Philosophy: "Learn by Playing, Not by Reading"

### Problem Statement
- No one wants to read code line-by-line, especially AI-generated code
- Traditional "read documentation → understand → use" learning path is inefficient
- Need a way to learn the system through interaction and exploration

### Solution: Interactive Playground
An executable learning environment that forces you to understand the system by:
1. **Playing with parameters** → Learn the interface layer
2. **Observing algorithm behavior** → Learn the pipeline layer
3. **Comparing experiments** → Learn the mechanism layer

### Dual Benefits
1. **For learners:** Understand architecture through interaction, not documentation
2. **For the project:** Discover bugs through usage, improve code quality iteratively

---

## Three-Layer Learning Model

### Layer 1: Interface Layer (API/Contracts)
**What you'll learn:**
- Input format: What does a valid instance look like?
- Output format: What does a solution contain?
- Error handling: What happens when things go wrong?

**Playground features:**
- Instance viewer: See instance structure
- Solution inspector: Examine solution details
- Validation feedback: Immediate error messages

### Layer 2: Pipeline Layer (Workflows)
**What you'll learn:**
- Algorithm stages: Construction → Destruction → Repair → Acceptance
- Key parameters: Which parameters affect which stage?
- Performance trade-offs: Speed vs. quality

**Playground features:**
- Stage-by-stage execution
- Parameter sliders with live impact preview
- Performance metrics dashboard

### Layer 3: Mechanism Layer (Why It Works)
**What you'll learn:**
- Operator effects: How does 2-opt improve solutions?
- Search behavior: Why does temperature affect acceptance?
- Algorithm intuition: What makes ALNS effective?

**Playground features:**
- Step-by-step operator visualization
- Move impact highlighting (before/after cost comparison)
- Search trajectory animation

---

## Three Critical Deliverables

### 1. Interactive Console (Playground)
The Streamlit web interface where users:
- Select/generate instances
- Configure algorithms
- Run experiments
- Visualize results

### 2. System Map (ARCHITECTURE_MAP.md)
Auto-generated documentation showing:
- Module structure
- Key classes and functions
- Data flow (Instance → Solver → Solution)

### 3. Contract Tests (contracts/)
Automated tests ensuring:
- Playground demonstrations match actual behavior
- Reproducibility (same seed = same result)
- Interface consistency across iterations

---

## Four Types of Interactions

### A. Problem Definition & Instance Generation
- Upload/select instances (VRP, VRPTW, PDPTW)
- View instance summary (nodes, vehicles, time windows)
- Generate small test instances (for quick learning)

### B. Algorithm Pipeline Configuration
- Stage-based UI: Construction → Improvement → Acceptance
- Key parameters exposed, advanced parameters hidden
- Single-stage execution for debugging

### C. Operator Explainability
- Operator catalog (2-opt, relocate, exchange, etc.)
- Move log: Cost change, constraint impact, trigger reason
- Step-by-step mode: Apply one move at a time

### D. Experiment Comparison & Regression
- Save multiple configurations
- Auto-generate comparison reports
- Export experiment cards (Markdown/JSON)

---

## Implementation Roadmap

### Stage 1: Minimal Viable Playground (1-2 evenings)
**Goal:** Get something running that you can play with
**Features:**
- Basic Streamlit app
- Instance selection + algorithm configuration (≤10 parameters)
- Run ALNS + visualize routes
- Display cost and convergence curve

**Deliverables:**
- playground/app.py
- playground/README.md
- ARCHITECTURE_MAP.md (rough version)

### Stage 2: Explainability & Reproducibility (quality leap)
**Goal:** Make learning actionable and reliable
**Features:**
- Fixed seed support
- Structured logs (solution + metrics + config)
- Step-by-step operator visualization
- Contract tests (parsing, feasibility, evaluation)

**Deliverables:**
- runs/ directory for experiment records
- contracts/ directory for tests
- Enhanced visualizations

### Stage 3: Gamified Learning System
**Goal:** Make learning self-driven
**Features:**
- Learning missions (e.g., "Get feasible solution in 30s")
- Achievement hints (e.g., "Try adjusting temperature decay")
- Difficulty progression

**Deliverables:**
- Mission system
- Progress tracking
- Guided learning paths

---

## Engineering Principles

### 1. Minimal Cognitive Slices
Don't try to understand everything at once. Only track:
- Entry points (where does execution start?)
- Data sources (where does instance data come from?)
- Result evaluation (how is solution quality measured?)

Everything else: learn on-demand when you hit a limitation.

### 2. AI Iteration Discipline
When AI fixes bugs through playground development:
1. Write reproduction script first
2. Add contract test covering the failure
3. Make minimal fix
4. Update CHANGELOG_LEARNINGS.md with root cause + impact

This prevents "patch fixes" that break later.

### 3. Just-in-Time Learning
Only dive into a module when:
- Playground hits a limitation (e.g., "doesn't support time windows")
- You want to customize behavior (e.g., "add a custom operator")
- You encounter a bug (e.g., "infeasible solution accepted")

Otherwise: stay at the interaction level.

---

## Success Metrics

### Short-term (Stage 1 complete)
- [ ] Can launch playground in 1 command
- [ ] Can generate instance + run ALNS + see routes in <5 minutes
- [ ] Understand what PDPTWInstance, ALNSSolver, VRPSolution are

### Medium-term (Stage 2 complete)
- [ ] Can reproduce any experiment from saved config
- [ ] Understand algorithm pipeline (construct → search → accept)
- [ ] Can explain why a parameter affects solution quality

### Long-term (Stage 3 complete)
- [ ] Can implement a custom operator through guided missions
- [ ] Can design experiments to test algorithm hypotheses
- [ ] Playground becomes the primary learning interface for others

---

## Open Source Value

A well-designed playground transforms Routing Heuristics from "yet another algorithm library" to "an interactive learning platform for routing research."

**Benefits:**
- Lower barrier to entry (play instead of read)
- Better bug discovery (usage reveals edge cases)
- Stronger teaching tool (show don't tell)
- More reproducible research (saved experiments)

**Vision:** Others don't read your code—they play with your system, understand it through interaction, and reproduce your results through saved configurations.

---

**Next Steps:** See playground/README.md for setup instructions and playground/FEATURES.md for current capabilities.
