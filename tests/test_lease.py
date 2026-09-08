from datetime import datetime, timedelta, timezone

import pytest

from reference.jobstore import InMemoryJobStore, LeaseConflict
from reference.lease import LeaseManager


def test_heartbeat_renews_active_lease():
    store = InMemoryJobStore()
    job = store.create("wf-1", "idem-1", {})
    claimed = store.claim(job.job_id, "runner-a", lease_seconds=1)
    old_expiry = claimed.lease_expires_at

    renewed = LeaseManager(store, lease_seconds=60).renew(job.job_id, claimed.lease_id)

    assert renewed.lease_expires_at > old_expiry


def test_stale_heartbeat_is_rejected():
    store = InMemoryJobStore()
    job = store.create("wf-1", "idem-1", {})
    claimed = store.claim(job.job_id, "runner-a", lease_seconds=0)

    with pytest.raises(LeaseConflict):
        LeaseManager(store).renew(job.job_id, claimed.lease_id)


def test_expiry_helper():
    assert LeaseManager.is_expired(datetime.now(timezone.utc) - timedelta(seconds=1))
    assert not LeaseManager.is_expired(datetime.now(timezone.utc) + timedelta(seconds=60))
    assert LeaseManager.is_expired(None)
