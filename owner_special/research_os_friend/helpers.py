from __future__ import annotations

import math
from dataclasses import asdict, dataclass

from .models import FriendRequest, ScaleProfile


@dataclass(frozen=True)
class HelperAllocation:
    mode: str
    requested_helpers: int
    logical_capacity: int
    planned_helpers: int
    active_workers: int
    batches: int
    bounded: bool = True

    def snapshot(self) -> dict[str, object]:
        return asdict(self)


class HelperScheduler:
    """Plans very large logical helper pools without spawning them all at once."""

    MAX_ACTIVE_WORKERS = 128
    MAX_LOGICAL_HELPERS = 1_000_000

    def allocate(self, request: FriendRequest, scale: ScaleProfile) -> HelperAllocation:
        requested = request.helper_budget if request.helper_budget > 0 else max(1, request.parallelism)
        requested = min(max(1, int(requested)), self.MAX_LOGICAL_HELPERS)
        logical_capacity = min(scale.logical_capacity, self.MAX_LOGICAL_HELPERS)
        planned = min(requested, logical_capacity)
        active = min(planned, self.MAX_ACTIVE_WORKERS)
        batches = max(1, math.ceil(planned / active))
        return HelperAllocation(
            mode="adaptive-million" if logical_capacity == self.MAX_LOGICAL_HELPERS else "adaptive",
            requested_helpers=requested,
            logical_capacity=logical_capacity,
            planned_helpers=planned,
            active_workers=active,
            batches=batches,
        )
