from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class GeneratedDelay:
    """One generated delay value that can be slept and reused unchanged."""

    seconds: float

    def __post_init__(self) -> None:
        if self.seconds < 0:
            raise ValueError("delay seconds must be non-negative")

    def sleep(self, sleeper: Callable[[float], None] = time.sleep) -> float:
        """Sleep once using the generated value and return that same value."""
        sleeper(self.seconds)
        return self.seconds

    def value(self) -> float:
        """Return the exact generated value for downstream steps."""
        return self.seconds
