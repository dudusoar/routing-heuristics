from __future__ import annotations


class DistanceObjective:
    """Minimize route distance from the shared route profile."""

    def route_cost(self, profile) -> float:
        return profile.total_distance

    def solution_cost(self, profiles) -> float:
        return sum(profile.total_distance for profile in profiles)
