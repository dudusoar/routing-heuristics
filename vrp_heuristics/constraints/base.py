from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from vrp_heuristics.core import ProblemInstance, ProblemSnapshot, RoutePlan


@dataclass(frozen=True)
class ConstraintViolation:
    constraint: str
    vehicle_id: str | None
    request_id: str | None
    message: str


@dataclass(frozen=True)
class ConstraintContext:
    problem: ProblemInstance
    snapshot: ProblemSnapshot


@dataclass
class ConstraintReport:
    feasible: bool
    violations: list[ConstraintViolation] = field(default_factory=list)

    @classmethod
    def from_violations(cls, violations: list[ConstraintViolation]) -> "ConstraintReport":
        return cls(feasible=not violations, violations=violations)

    def first_reason(self) -> str | None:
        if not self.violations:
            return None
        violation = self.violations[0]
        return f"{violation.constraint}: {violation.message}"


class Constraint(Protocol):
    name: str

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> list[ConstraintViolation]:
        ...


class ConstraintSet:
    def __init__(self, constraints: list[Constraint] | None = None):
        self.constraints = constraints or []

    def evaluate_route(
        self,
        *,
        route: RoutePlan,
        context: ConstraintContext,
        profile,
    ) -> ConstraintReport:
        violations = list(profile.violations)
        for constraint in self.constraints:
            violations.extend(
                constraint.evaluate_route(
                    route=route,
                    context=context,
                    profile=profile,
                )
            )
        return ConstraintReport.from_violations(violations)

    def evaluate_solution(
        self,
        *,
        routes: dict[str, RoutePlan],
        context: ConstraintContext,
        evaluator,
    ) -> ConstraintReport:
        violations: list[ConstraintViolation] = []
        for route in routes.values():
            profile = evaluator.evaluate_route(route=route, context=context)
            violations.extend(
                self.evaluate_route(
                    route=route,
                    context=context,
                    profile=profile,
                ).violations
            )
        return ConstraintReport.from_violations(violations)
