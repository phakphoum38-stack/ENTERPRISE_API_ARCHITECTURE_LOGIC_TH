"""Central runtime variables for the Research OS resource-control plane.

These values are configuration/contract primitives only. They do not own
execution, authorization, quota, budget, routing, or provider state.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class ResourceRuntimeVariables:
    """Stable resource-runtime defaults shared by governance primitives."""

    namespace: str = "/platform/v1"
    default_currency: str = "USD"
    reservation_ttl: timedelta = timedelta(minutes=5)
    api_key_prefix: str = "ro_live_"

    def __post_init__(self) -> None:
        if not self.namespace.startswith("/"):
            raise ValueError("resource namespace must be absolute")
        if len(self.default_currency) != 3 or not self.default_currency.isalpha():
            raise ValueError("default currency must be a three-letter code")
        if self.reservation_ttl <= timedelta(0):
            raise ValueError("reservation_ttl must be positive")
        if not self.api_key_prefix.endswith("_"):
            raise ValueError("api key prefix must end with '_'")
        
    @property
    def reservation_ttl_seconds(self) -> int:
        return int(self.reservation_ttl.total_seconds())


RESOURCE_RUNTIME = ResourceRuntimeVariables()
RESOURCE_NAMESPACE = RESOURCE_RUNTIME.namespace
RESOURCE_DEFAULT_CURRENCY = RESOURCE_RUNTIME.default_currency
RESOURCE_RESERVATION_TTL = RESOURCE_RUNTIME.reservation_ttl
RESOURCE_API_KEY_PREFIX = RESOURCE_RUNTIME.api_key_prefix
