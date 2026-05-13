from __future__ import annotations

from vrp_heuristics.core import RoutePlan

from .base import ConstraintContext, ConstraintViolation
from .evaluator import EPSILON


class CapacityConstraint:
    name = "CapacityConstraint"

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> list[ConstraintViolation]:
        vehicle = context.problem.vehicles[route.vehicle_id]
        if vehicle.capacity_weight is None:
            return []

        violations: list[ConstraintViolation] = []
        state = context.snapshot.vehicle_states[route.vehicle_id]
        if state.current_load_weight > vehicle.capacity_weight + EPSILON:
            violations.append(
                ConstraintViolation(
                    constraint=self.name,
                    vehicle_id=route.vehicle_id,
                    request_id=None,
                    message=(
                        f"current load {state.current_load_weight:.3f} exceeds "
                        f"capacity {vehicle.capacity_weight:.3f}"
                    ),
                )
            )
        for step in profile.steps:
            if step.load_after_stop > vehicle.capacity_weight + EPSILON:
                violations.append(
                    ConstraintViolation(
                        constraint=self.name,
                        vehicle_id=route.vehicle_id,
                        request_id=step.request_id,
                        message=(
                            f"load {step.load_after_stop:.3f} exceeds "
                            f"capacity {vehicle.capacity_weight:.3f}"
                        ),
                    )
                )
            if step.load_after_stop < -EPSILON:
                violations.append(
                    ConstraintViolation(
                        constraint=self.name,
                        vehicle_id=route.vehicle_id,
                        request_id=step.request_id,
                        message=f"load became negative ({step.load_after_stop:.3f})",
                    )
                )
        return violations
