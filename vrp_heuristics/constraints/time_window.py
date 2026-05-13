from __future__ import annotations

from vrp_heuristics.core import RoutePlan

from .base import ConstraintContext, ConstraintViolation
from .evaluator import EPSILON


class TimeWindowConstraint:
    name = "TimeWindowConstraint"

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> list[ConstraintViolation]:
        violations: list[ConstraintViolation] = []
        for step in profile.steps:
            request = context.problem.requests.get(step.request_id)
            if request is None:
                continue
            if step.stop_type == "pickup":
                window_end = request.pickup_time_window[1]
            else:
                window_end = request.dropoff_time_window[1]
            if step.arrival_time > window_end + EPSILON:
                violations.append(
                    ConstraintViolation(
                        constraint=self.name,
                        vehicle_id=route.vehicle_id,
                        request_id=step.request_id,
                        message=(
                            f"{step.stop_type} time {step.arrival_time:.3f} "
                            f"exceeds window end {window_end:.3f}"
                        ),
                    )
                )
        return violations
