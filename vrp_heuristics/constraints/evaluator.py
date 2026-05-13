from __future__ import annotations

from dataclasses import dataclass, field

from vrp_heuristics.core import ProblemInstance, ProblemSnapshot, RoutePlan, RouteStop

from .base import ConstraintContext, ConstraintViolation


EPSILON = 1e-9


@dataclass(frozen=True)
class RouteEvaluationStep:
    request_id: str
    stop_type: str
    node_id: int
    arrival_time: float
    departure_time: float
    load_after_stop: float
    battery_after_leg: float | None
    distance_from_previous: float
    travel_time_from_previous: float


@dataclass
class RouteProfile:
    vehicle_id: str
    steps: list[RouteEvaluationStep] = field(default_factory=list)
    violations: list[ConstraintViolation] = field(default_factory=list)
    completion_times: dict[str, float] = field(default_factory=dict)
    total_distance: float = 0.0
    total_travel_time: float = 0.0
    terminal_node: int | None = None
    terminal_distance: float = 0.0
    terminal_travel_time: float = 0.0
    terminal_arrival_time: float | None = None
    terminal_battery_after_leg: float | None = None


class RouteEvaluator:
    """Build a route profile once so constraints can share timing/resource state."""

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
    ) -> RouteProfile:
        problem = context.problem
        snapshot = context.snapshot
        vehicle = problem.vehicles[route.vehicle_id]
        state = snapshot.vehicle_states[route.vehicle_id]
        profile = RouteProfile(vehicle_id=route.vehicle_id)

        current_node = state.current_node
        clock = max(snapshot.current_time, state.available_time)
        load = state.current_load_weight
        battery = state.current_battery
        carried = set(state.carried_request_ids)
        picked = set(state.carried_request_ids)

        for stop in route.stops:
            request = problem.requests.get(stop.request_id)
            if request is None:
                profile.violations.append(
                    ConstraintViolation(
                        constraint="KnownRequestConstraint",
                        vehicle_id=route.vehicle_id,
                        request_id=stop.request_id,
                        message="route references an unknown request",
                    )
                )
                continue

            distance = problem.cost_provider.travel_distance(
                current_node,
                stop.node_id,
                current_time=clock,
            )
            travel_time = problem.cost_provider.travel_time(
                current_node,
                stop.node_id,
                current_time=clock,
            )
            if distance == float("inf") or travel_time == float("inf"):
                profile.violations.append(
                    ConstraintViolation(
                        constraint="ReachabilityConstraint",
                        vehicle_id=route.vehicle_id,
                        request_id=stop.request_id,
                        message=f"no route from node {current_node} to {stop.node_id}",
                    )
                )
                break

            profile.total_distance += distance
            profile.total_travel_time += travel_time
            if battery is not None and vehicle.energy_per_distance > EPSILON:
                battery -= distance * vehicle.energy_per_distance

            arrival_time = clock + travel_time
            departure_time = arrival_time
            if stop.stop_type == "pickup":
                arrival_time = max(
                    arrival_time,
                    request.release_time,
                    request.pickup_time_window[0],
                )
                departure_time = arrival_time + request.pickup_service_time
                load += request.demand_weight
                carried.add(stop.request_id)
                picked.add(stop.request_id)
            elif stop.stop_type == "dropoff":
                arrival_time = max(arrival_time, request.dropoff_time_window[0])
                departure_time = arrival_time + request.dropoff_service_time
                if stop.request_id in carried:
                    carried.remove(stop.request_id)
                    load -= request.demand_weight
                profile.completion_times[stop.request_id] = arrival_time
            else:
                profile.violations.append(
                    ConstraintViolation(
                        constraint="StopTypeConstraint",
                        vehicle_id=route.vehicle_id,
                        request_id=stop.request_id,
                        message=f"unknown stop type {stop.stop_type!r}",
                    )
                )

            profile.steps.append(
                RouteEvaluationStep(
                    request_id=stop.request_id,
                    stop_type=stop.stop_type,
                    node_id=stop.node_id,
                    arrival_time=arrival_time,
                    departure_time=departure_time,
                    load_after_stop=load,
                    battery_after_leg=battery,
                    distance_from_previous=distance,
                    travel_time_from_previous=travel_time,
                )
            )
            current_node = stop.node_id
            clock = departure_time

        self._append_terminal_leg(
            profile=profile,
            problem=problem,
            route=route,
            current_node=current_node,
            clock=clock,
            battery=battery,
        )
        return profile

    @staticmethod
    def _append_terminal_leg(
        *,
        profile: RouteProfile,
        problem: ProblemInstance,
        route: RoutePlan,
        current_node: int,
        clock: float,
        battery: float | None,
    ) -> None:
        vehicle = problem.vehicles[route.vehicle_id]
        terminal_node = vehicle.terminal_policy.resolve_end_node(vehicle)
        profile.terminal_node = terminal_node
        if terminal_node is None:
            profile.terminal_battery_after_leg = battery
            return

        distance = problem.cost_provider.travel_distance(
            current_node,
            terminal_node,
            current_time=clock,
        )
        travel_time = problem.cost_provider.travel_time(
            current_node,
            terminal_node,
            current_time=clock,
        )
        if distance == float("inf") or travel_time == float("inf"):
            profile.violations.append(
                ConstraintViolation(
                    constraint="TerminalConstraint",
                    vehicle_id=route.vehicle_id,
                    request_id=None,
                    message=f"no route from node {current_node} to terminal {terminal_node}",
                )
            )
            return

        profile.terminal_distance = distance
        profile.terminal_travel_time = travel_time
        profile.terminal_arrival_time = clock + travel_time
        profile.total_distance += distance
        profile.total_travel_time += travel_time
        if battery is not None and vehicle.energy_per_distance > EPSILON:
            battery -= distance * vehicle.energy_per_distance
        profile.terminal_battery_after_leg = battery
