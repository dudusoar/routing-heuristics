# Playground Redesign Proposal
## Based on 7 Validated Tutorials

**Date:** 2026-01-09
**Status:** Proposal for Stage 2 Implementation
**Context:** All 7 tutorials now passing with correct APIs

---

## 🎯 Design Philosophy

**Learn by Doing** - Interactive exploration of VRP concepts
**Progressive Disclosure** - Start simple, unlock complexity
**Instant Feedback** - See results immediately
**Tutorial-Driven** - Each feature mirrors a tutorial

---

## 📚 Tutorial Mapping to Features

### Current Stage 1 MVP (Implemented)
| Feature | Tutorial | Status |
|---------|----------|--------|
| Synthetic instance generation | Tutorial 07 | ✅ Working |
| Basic ALNS configuration | Tutorial 01 | ✅ Working |
| Route visualization | Tutorial 01 | ✅ Working |
| Convergence plot | Tutorial 01 | ✅ Working |

### Proposed Stage 2 Features (Based on Tutorials)

#### Feature 1: Real-World Maps (Tutorial 02)
```
📍 Real-World Problem Creator
├── Input: Place name (e.g., "West Lafayette, Indiana, USA")
├── Pick depot/pickup/delivery locations on map
├── Load street network from OSMnx
├── Generate PDPTW instance from real map
└── Visualize routes on actual streets
```

**Why:** Most engaging feature - users see real locations!
**Complexity:** Medium (OSMnx API validated)
**Impact:** High (unique selling point)

#### Feature 2: Custom Problem Builder (Tutorial 03)
```
🎨 Manual Problem Designer
├── Canvas to click/place nodes
├── Define node types (depot, pickup, delivery)
├── Set demands and time windows
├── Upload CSV files
└── Validate and create instance
```

**Why:** Power users want full control
**Complexity:** Low (just UI + existing API)
**Impact:** Medium (advanced users)

#### Feature 3: Problem Variants Explorer (Tutorial 04)
```
🔀 Problem Type Selector
├── Radio buttons: PDPTW / PDP / CVRP / VRP
├── Auto-configure constraints
│   ├── Relaxed (wide time windows)
│   ├── Standard (normal constraints)
│   └── Strict (tight constraints)
├── Compare difficulty
└── See how problem type affects solution
```

**Why:** Teaches problem types intuitively
**Complexity:** Low (configuration presets)
**Impact:** High (educational value)

#### Feature 4: Parameter Sensitivity Dashboard (Tutorial 05)
```
📊 Sensitivity Analysis
├── Select parameter to vary (capacity, time windows, battery)
├── Define range and steps
├── Run batch experiments
├── Interactive charts:
│   ├── Objective vs Parameter
│   ├── Feasibility rate
│   └── Runtime comparison
└── Download results CSV
```

**Why:** Understand algorithm behavior
**Complexity:** High (multiple runs + visualization)
**Impact:** High (research tool)

#### Feature 5: Algorithm Playground (Tutorial 06)
```
🧪 Operator Testing Lab
├── Enable/disable operators:
│   ├── Removal: Shaw, Random, Worst, SISR
│   └── Repair: Greedy, Regret
├── Live operator performance:
│   ├── Usage count per operator
│   ├── Success rate
│   └── Average improvement
├── Compare operator combinations
└── Visualize search trajectory
```

**Why:** Understand ALNS internals
**Complexity:** Medium (operator statistics)
**Impact:** Very High (algorithm learning)

#### Feature 6: Data Generation Wizard (Tutorial 07)
```
🎲 Synthetic Data Generator
├── Step 1: Map Configuration
│   ├── Restaurants: [slider]
│   ├── Customers: [slider]
│   └── Distribution: Uniform/Normal/Clustered
├── Step 2: Demand Pattern
│   ├── Time range and intervals
│   ├── Demand distribution (Poisson λ)
│   └── Preview demand heatmap
├── Step 3: Order Generation
│   ├── Time window length
│   ├── Service time
│   └── Generate instance
└── Export to file
```

**Why:** Systematic instance creation
**Complexity:** Medium (multi-step wizard)
**Impact:** High (instance creation tool)

---

## 🎨 Proposed UI Layout

### Tab-Based Navigation (Streamlit tabs)

```
┌────────────────────────────────────────────────────────┐
│ 🚀 Routing Heuristics Playground                       │
├────────────────────────────────────────────────────────┤
│ [Quickstart] [Real Maps] [Custom] [Variants] ...      │
├────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐            │
│  │  Configuration  │  │    Results      │            │
│  │                 │  │                 │            │
│  │  [inputs]       │  │  [viz/charts]   │            │
│  │  [sliders]      │  │                 │            │
│  │  [buttons]      │  │                 │            │
│  └─────────────────┘  └─────────────────┘            │
│                                                         │
│  [🎯 Solve Button]                                     │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### Tab 1: 🎯 Quickstart (Tutorial 01)
- Current Stage 1 MVP (already working)
- Keep as simple entry point

### Tab 2: 📍 Real-World Maps (Tutorial 02)
- Place name input
- Interactive map for location selection
- Load network button
- Visualize routes on real streets

### Tab 3: 🎨 Custom Problem (Tutorial 03)
- Canvas for manual node placement
- Or CSV upload
- Node property editor

### Tab 4: 🔀 Problem Variants (Tutorial 04)
- Problem type selector
- Constraint presets
- Side-by-side comparison

### Tab 5: 📊 Sensitivity Analysis (Tutorial 05)
- Parameter selection
- Batch experiment runner
- Interactive charts

### Tab 6: 🧪 Algorithm Lab (Tutorial 06)
- Operator toggles
- Real-time statistics
- Performance comparison

### Tab 7: 🎲 Data Generator (Tutorial 07)
- Multi-step wizard
- Preview at each step
- Export functionality

---

## 🚀 Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. **Problem Variants Tab (Tutorial 04)**
   - Easiest to implement (just UI + presets)
   - High educational value
   - Uses validated Tutorial 04 code

2. **Improve Quickstart Tab**
   - Add tooltips and explanations
   - Better visualization
   - Progress indicators

### Phase 2: High-Impact Features (3-5 days)
3. **Real-World Maps Tab (Tutorial 02)**
   - Most exciting feature
   - OSMnx API validated
   - Needs folium for interactive map

4. **Algorithm Lab Tab (Tutorial 06)**
   - Exposes ALNS internals
   - Great for learning
   - Operator statistics already available

### Phase 3: Advanced Tools (5-7 days)
5. **Sensitivity Analysis Tab (Tutorial 05)**
   - Research tool
   - Batch experiments
   - Data export

6. **Custom Problem Tab (Tutorial 03)**
   - Advanced users
   - Canvas interaction needs work

7. **Data Generator Tab (Tutorial 07)**
   - Wizard interface
   - Multi-step flow

---

## 🎯 Recommended Next Steps

### Option A: Quick Win First (Recommended)
**Start with:** Problem Variants Tab (Tutorial 04)
- ✅ Easiest to implement (2-3 hours)
- ✅ High educational value
- ✅ Demonstrates tutorial → playground pipeline
- ✅ Builds confidence

### Option B: Big Impact First
**Start with:** Real-World Maps Tab (Tutorial 02)
- ✅ Most exciting feature
- ✅ Unique selling point
- ❌ Slightly more complex (folium integration)

### Option C: Learning Focus
**Start with:** Algorithm Lab Tab (Tutorial 06)
- ✅ Deep algorithm understanding
- ✅ Interactive exploration
- ❌ Needs UI for operator statistics

---

## 📋 Technical Notes

### APIs Validated (From Tutorials)
- ✅ PDPTWInstance creation (Tutorial 03)
- ✅ OSMnx integration (Tutorial 02)
- ✅ Data generation (Tutorial 07)
- ✅ ALNS configuration (All tutorials)
- ✅ Operator interfaces (Tutorial 06)
- ✅ Sensitivity analysis (Tutorial 05)

### Dependencies Needed
- **Current:** streamlit, numpy, matplotlib
- **For Real Maps:** folium, osmnx (already installed)
- **For Sensitivity:** plotly (optional, better interactive charts)
- **For Custom Canvas:** streamlit-drawable-canvas (optional)

### Session State Structure
```python
st.session_state = {
    'instance': PDPTWInstance,           # Current problem
    'solution': PDPTWSolution,           # Current solution
    'cost_history': List[float],         # Convergence
    'operator_stats': Dict,              # Operator performance
    'sensitivity_results': List[Dict],   # Batch experiments
    'current_tab': str,                  # Active tab
}
```

---

## 🎓 Educational Value

Each tab teaches specific concepts:

| Tab | Teaches |
|-----|---------|
| Quickstart | Basic VRP workflow |
| Real Maps | Real-world applications |
| Custom | Problem structure |
| Variants | Problem types & constraints |
| Sensitivity | Parameter tuning |
| Algorithm Lab | ALNS algorithm internals |
| Data Generator | Instance creation |

---

## 💡 User Flow Examples

### Beginner User
1. Quickstart → Generate instance → Solve → See results
2. Problem Variants → Try relaxed/standard/strict
3. Real Maps → See routes on actual streets

### Intermediate User
4. Algorithm Lab → Enable/disable operators
5. Sensitivity Analysis → Find best parameters
6. Data Generator → Create custom instances

### Advanced User
7. Custom Problem → Full control
8. Export data → Research use

---

## 🎬 Next Action

**Which feature should we implement first?**

A. 🔀 Problem Variants (Tutorial 04) - **Quickest win**
B. 📍 Real-World Maps (Tutorial 02) - **Biggest impact**
C. 🧪 Algorithm Lab (Tutorial 06) - **Best learning**
D. Other suggestion?

**I recommend Option A** for quick confidence boost, then B or C.

What do you think? 🤔
