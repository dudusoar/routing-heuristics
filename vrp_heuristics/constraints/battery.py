from __future__ import annotations

from vrp_heuristics.core import RoutePlan

from .base import ConstraintContext, ConstraintViolation
from .evaluator import EPSILON


class BatteryConstraint:
    name = "BatteryConstraint"

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> list[ConstraintViolation]:
        vehicle = context.problem.vehicles[route.vehicle_id]
        state = context.snapshot.vehicle_states[route.vehicle_id]
        if vehicle.battery_capacity is None or state.current_battery is None:
            return []

        violations: list[ConstraintViolation] = []
        if state.current_battery > vehicle.battery_capacity + EPSILON:
            violations.append(
                ConstraintViolation(
                    constraint=self.name,
                    vehicle_id=route.vehicle_id,
                    request_id=None,
                    message=(
                        f"current battery {state.current_battery:.3f} exceeds "
                        f"capacity {vehicle.battery_capacity:.3f}"
                    ),
                )
            )
        for step in profile.steps:
            if step.battery_after_leg is not None and step.battery_after_leg < -EPSILON:
                violations.append(
                    ConstraintViolation(
                        constraint=self.name,
                        vehicle_id=route.vehicle_id,
                        request_id=step.request_id,
                        message=f"battery drops below zero ({step.battery_after_leg:.3f})",
                    )
                )
        if (
            profile.terminal_battery_after_leg is not None
            and profile.terminal_battery_after_leg < -EPSILON
        ):
            violations.append(
                ConstraintViolation(
                    constraint=self.name,
                    vehicle_id=route.vehicle_id,
                    request_id=None,
                    message=(
                        "battery drops below zero on terminal leg "
                        f"({profile.terminal_battery_after_leg:.3f})"
                    ),
                )
            )
        return violations
