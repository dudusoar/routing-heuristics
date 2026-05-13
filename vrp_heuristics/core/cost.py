from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class CostProvider(Protocol):
    """Routing cost interface used by evaluators and solvers."""

    def travel_distance(
        self,
        origin: int,
        destination: int,
        *,
        current_time: float | None = None,
    ) -> float:
        ...

    def travel_time(
        self,
        origin: int,
        destination: int,
        *,
        current_time: float | None = None,
    ) -> float:
        ...


@dataclass(frozen=True)
class MatrixCostProvider:
    """Dense matrix cost provider for small instances and tests."""

    distance_matrix: Sequence[Sequence[float]]
    time_matrix: Sequence[Sequence[float]] | None = None

    def travel_distance(
        self,
        origin: int,
        destination: int,
        *,
        current_time: float | None = None,
    ) -> float:
        return float(self.distance_matrix[origin][destination])

    def travel_time(
        self,
        origin: int,
        destination: int,
        *,
        current_time: float | None = None,
    ) -> float:
        matrix = self.time_matrix if self.time_matrix is not None else self.distance_matrix
        return float(matrix[origin][destination])
