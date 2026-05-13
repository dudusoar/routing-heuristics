from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .cost import CostProvider


TerminalMode = Literal[
    "open_route",
    "return_to_depot",
    "fixed_end_node",
    "return_to_nearest_charger",
]


@dataclass(frozen=True)
class TerminalPolicy:
    """Route start/end semantics for a vehicle."""

    mode: TerminalMode = "open_route"
    end_node: int | None = None

    def resolve_end_node(self, vehicle: VehicleSpec) -> int | None:
        if self.mode == "open_route":
            return None
        if self.mode == "fixed_end_node":
            return self.end_node
        if self.mode == "return_to_depot":
            return vehicle.end_depot if vehicle.end_depot is not None else vehicle.start_depot
        if self.mode == "return_to_nearest_charger":
            return self.end_node
        raise ValueError(f"Unknown terminal policy mode: {self.mode}")


@dataclass(frozen=True)
class RequestSpec:
    request_id: str
    pickup_node: int
    dropoff_node: int
    demand_weight: float = 1.0
    release_time: float = 0.0
    pickup_time_window: tuple[float, float] = (0.0, float("inf"))
    dropoff_time_window: tuple[float, float] = (0.0, float("inf"))
    pickup_service_time: float = 0.0
    dropoff_service_time: float = 0.0


@dataclass(frozen=True)
class VehicleSpec:
    vehicle_id: str
    start_depot: int | None = None
    end_depot: int | None = None
    terminal_policy: TerminalPolicy = field(default_factory=TerminalPolicy)
    capacity_weight: float | None = None
    battery_capacity: float | None = None
    energy_per_distance: float = 0.0


@dataclass(frozen=True)
class VehicleState:
    vehicle_id: str
    current_node: int
    available_time: float = 0.0
    current_load_weight: float = 0.0
    current_battery: float | None = None
    carried_request_ids: tuple[str, ...] = ()
    locked_stop_count: int = 0


@dataclass(frozen=True)
class ProblemInstance:
    """Static problem definition independent of any solver."""

    requests: dict[str, RequestSpec]
    vehicles: dict[str, VehicleSpec]
    cost_provider: CostProvider
    name: str = "routing_problem"

    def __post_init__(self) -> None:
        for request_id, request in self.requests.items():
            if request_id != request.request_id:
                raise ValueError(f"Request key {request_id!r} does not match request_id")
        for vehicle_id, vehicle in self.vehicles.items():
            if vehicle_id != vehicle.vehicle_id:
                raise ValueError(f"Vehicle key {vehicle_id!r} does not match vehicle_id")


@dataclass(frozen=True)
class ProblemSnapshot:
    """Dynamic decision-state snapshot for rolling-horizon solvers."""

    current_time: float
    vehicle_states: dict[str, VehicleState]
    visible_request_ids: tuple[str, ...]

    @classmethod
    def from_instance(
        cls,
        problem: ProblemInstance,
        *,
        current_time: float = 0.0,
    ) -> "ProblemSnapshot":
        vehicle_states = {
            vehicle_id: VehicleState(
                vehicle_id=vehicle_id,
                current_node=vehicle.start_depot if vehicle.start_depot is not None else 0,
                current_battery=vehicle.battery_capacity,
            )
            for vehicle_id, vehicle in problem.vehicles.items()
        }
        return cls(
            current_time=current_time,
            vehicle_states=vehicle_states,
            visible_request_ids=tuple(problem.requests),
        )
