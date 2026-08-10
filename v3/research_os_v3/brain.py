from __future__ import annotations

from .models import SCALE_PROFILES, ScaleProfile, Workload


class BrainCore:
    """Select the smallest safe logical hierarchy for the workload."""

    def select_profile(self, workload: Workload) -> tuple[ScaleProfile, int, str]:
        demand = workload.normalized_demand()
        for profile in SCALE_PROFILES:
            if demand <= profile.capacity:
                return profile, demand, f"smallest profile satisfying demand={demand}"

        profile = SCALE_PROFILES[-1]
        return profile, demand, (
            f"demand={demand} exceeds logical capacity={profile.capacity}; "
            "use maximum profile with queue/backpressure"
        )
