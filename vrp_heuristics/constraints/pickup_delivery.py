from __future__ import annotations

from vrp_heuristics.core import RoutePlan

from .base import ConstraintContext, ConstraintViolation


class PickupDeliveryConstraint:
    name = "PickupDeliveryConstraint"

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> list[ConstraintViolation]:
        carried = set(context.snapshot.vehicle_states[route.vehicle_id].carried_request_ids)
        picked = set(carried)
        violations: list[ConstraintViolation] = []

        for stop in route.stops:
            if stop.request_id not in context.problem.requests:
                continue
            if stop.stop_type == "pickup":
                if stop.request_id in picked:
                    violations.append(
                        ConstraintViolation(
                            constraint=self.name,
                            vehicle_id=route.vehicle_id,
                            request_id=stop.request_id,
                            message="request is picked up more than once",
                        )
                    )
                picked.add(stop.request_id)
                carried.add(stop.request_id)
            elif stop.stop_type == "dropoff":
                if stop.request_id not in carried:
                    violations.append(
                        ConstraintViolation(
                            constraint=self.name,
                            vehicle_id=route.vehicle_id,
                            request_id=stop.request_id,
                            message="dropoff appears before pickup",
                        )
                    )
                else:
                    carried.remove(stop.request_id)
        return violations
