from datetime import datetime, timedelta, timezone

from reference.jobstore import InMemoryJobStore, LeaseConflict


class LeaseManager:
    """Reference heartbeat/lease-renewal service."""

    def __init__(self, store: InMemoryJobStore, lease_seconds: int = 60):
        self.store = store
        self.lease_seconds = lease_seconds

    def renew(self, job_id: str, lease_id: str):
        return self.store.heartbeat(job_id, lease_id, self.lease_seconds)

    @staticmethod
    def is_expired(expires_at: datetime | None) -> bool:
        if expires_at is None:
            return True
        return expires_at <= datetime.now(timezone.utc)
