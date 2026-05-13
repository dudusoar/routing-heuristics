from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


StopType = Literal["pickup", "dropoff"]


@dataclass(frozen=True)
class RouteStop:
    request_id: str
    stop_type: StopType
    node_id: int


@dataclass
class RoutePlan:
    vehicle_id: str
    stops: list[RouteStop] = field(default_factory=list)
    locked_stop_count: int = 0

    def clone(self) -> "RoutePlan":
        return RoutePlan(
            vehicle_id=self.vehicle_id,
            stops=list(self.stops),
            locked_stop_count=self.locked_stop_count,
        )


@dataclass
class Solution:
    routes: dict[str, RoutePlan]

    def clone(self) -> "Solution":
        return Solution(
            routes={vehicle_id: route.clone() for vehicle_id, route in self.routes.items()}
        )
