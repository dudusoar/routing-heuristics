"""Solving algorithms for VRP problems.

This package contains various algorithms for solving Vehicle Routing Problems,
including ALNS (Adaptive Large Neighborhood Search).
"""

# Note: Removed direct import of alns to avoid circular imports
# from . import alns  # Causes circular import with pdptw module
from .base import (
    VRPProblem,
    VRPSolution,
    Solver,
    ConfigurableSolver,
    PDPTWProblemAdapter,
    PDPTWSolutionAdapter
)

__all__ = [
    # Note: "alns" removed to avoid circular imports - import directly from vrp_toolkit.algorithms.alns
    "VRPProblem",
    "VRPSolution",
    "Solver",
    "ConfigurableSolver",
    "PDPTWProblemAdapter",
    "PDPTWSolutionAdapter"
]