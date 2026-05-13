from __future__ import annotations

from dataclasses import dataclass, field

from vrp_heuristics.constraints import (
    BatteryConstraint,
    CapacityConstraint,
    ConstraintContext,
    ConstraintSet,
    PickupDeliveryConstraint,
    RouteEvaluator,
    TimeWindowConstraint,
)
from vrp_heuristics.core import ProblemInstance, ProblemSnapshot, RoutePlan, RouteStop, Solution
from vrp_heuristics.objectives import DistanceObjective


@dataclass
class GreedyInsertionSolver:
    """Cheapest feasible pickup-delivery insertion solver."""

    constraint_set: ConstraintSet = field(
        default_factory=lambda: ConstraintSet(
            [
                PickupDeliveryConstraint(),
                CapacityConstraint(),
                TimeWindowConstraint(),
                BatteryConstraint(),
            ]
        )
    )
    objective: DistanceObjective = field(default_factory=DistanceObjective)
    evaluator: RouteEvaluator = field(default_factory=RouteEvaluator)

    def solve(
        self,
        problem: ProblemInstance,
        snapshot: ProblemSnapshot | None = None,
    ) -> Solution:
        snapshot = snapshot or ProblemSnapshot.from_instance(problem)
        context = ConstraintContext(problem=problem, snapshot=snapshot)
        solution = Solution(
            routes={
                vehicle_id: RoutePlan(
                    vehicle_id=vehicle_id,
                    locked_stop_count=snapshot.vehicle_states[vehicle_id].locked_stop_count,
                )
                for vehicle_id in problem.vehicles
            }
        )

        served = set()
        ordered_request_ids = sorted(
            snapshot.visible_request_ids,
            key=lambda request_id: (
                problem.requests[request_id].release_time,
                request_id,
            ),
        )
        for request_id in ordered_request_ids:
            if request_id in served:
                continue
            insertion = self._best_insertion(
                request_id=request_id,
                solution=solution,
                context=context,
            )
            if insertion is None:
                continue
            route = solution.routes[insertion.vehicle_id]
            route.stops = insertion.stops
            served.add(request_id)

        return solution

    def _best_insertion(
        self,
        *,
        request_id: str,
        solution: Solution,
        context: ConstraintContext,
    ) -> "_Insertion | None":
        request = context.problem.requests[request_id]
        pickup_stop = RouteStop(
            request_id=request_id,
            stop_type="pickup",
            node_id=request.pickup_node,
        )
        dropoff_stop = RouteStop(
            request_id=request_id,
            stop_type="dropoff",
            node_id=request.dropoff_node,
        )

        best: _Insertion | None = None
        for vehicle_id, route in solution.routes.items():
            locked_prefix = min(len(route.stops), max(0, route.locked_stop_count))
            for pickup_index in range(locked_prefix, len(route.stops) + 1):
                with_pickup = list(route.stops)
                with_pickup.insert(pickup_index, pickup_stop)
                for dropoff_index in range(pickup_index + 1, len(with_pickup) + 1):
                    candidate_stops = list(with_pickup)
                    candidate_stops.insert(dropoff_index, dropoff_stop)
                    candidate_route = RoutePlan(
                        vehicle_id=vehicle_id,
                        stops=candidate_stops,
                        locked_stop_count=route.locked_stop_count,
                    )
                    profile = self.evaluator.evaluate_route(
                        route=candidate_route,
                        context=context,
                    )
                    report = self.constraint_set.evaluate_route(
                        route=candidate_route,
                        context=context,
                        profile=profile,
                    )
                    if not report.feasible:
                        continue
                    cost = self.objective.route_cost(profile)
                    candidate = _Insertion(
                        cost=cost,
                        vehicle_id=vehicle_id,
                        pickup_index=pickup_index,
                        dropoff_index=dropoff_index,
                        stops=candidate_stops,
                    )
                    if best is None or candidate.sort_key() < best.sort_key():
                        best = candidate
        return best


@dataclass(frozen=True)
class _Insertion:
    cost: float
    vehicle_id: str
    pickup_index: int
    dropoff_index: int
    stops: list[RouteStop]

    def sort_key(self) -> tuple[float, str, int, int]:
        return (
            self.cost,
            self.vehicle_id,
            self.pickup_index,
            self.dropoff_index,
        )
