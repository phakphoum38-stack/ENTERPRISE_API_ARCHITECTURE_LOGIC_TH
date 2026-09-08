import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import psycopg


DSN = os.getenv("TEST_POSTGRES_DSN", "postgresql://workflow:workflow@localhost:54329/workflow")
SCHEMA = Path("adapters/postgres/schema.sql").read_text()
JOB_ID = "concurrency-stress-job"


def _setup_database():
    conn = psycopg.connect(DSN)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cur.execute(SCHEMA)
        cur.execute("DELETE FROM runner_assignments WHERE job_id = %s", (JOB_ID,))
        cur.execute("DELETE FROM workflow_jobs WHERE job_id = %s", (JOB_ID,))
        cur.execute(
            "INSERT INTO workflow_jobs(job_id, workflow_id, status) VALUES (%s, %s, 'QUEUED')",
            (JOB_ID, str(uuid4())),
        )
    conn.close()


def _reserve(runner_id):
    conn = psycopg.connect(DSN)
    try:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO runner_assignments
                        (job_id, runner_id, assignment_id, fencing_token, lease_expires_at, status)
                    VALUES (%s, %s, gen_random_uuid(), 1, %s, 'ACTIVE')
                    ON CONFLICT (job_id) DO UPDATE
                    SET runner_id = EXCLUDED.runner_id,
                        assignment_id = EXCLUDED.assignment_id,
                        fencing_token = runner_assignments.fencing_token + 1,
                        lease_expires_at = EXCLUDED.lease_expires_at,
                        status = 'ACTIVE', updated_at = now()
                    WHERE runner_assignments.status <> 'ACTIVE'
                       OR runner_assignments.lease_expires_at <= now()
                    RETURNING fencing_token
                    """,
                    (JOB_ID, runner_id, datetime.now(timezone.utc) + timedelta(minutes=5)),
                )
                row = cur.fetchone()
                return None if row is None else row[0]
    finally:
        conn.close()


def test_concurrent_reservation_allows_exactly_one_active_owner():
    _setup_database()
    runner_ids = [f"stress-runner-{i}" for i in range(32)]

    with ThreadPoolExecutor(max_workers=len(runner_ids)) as pool:
        tokens = list(pool.map(_reserve, runner_ids))

    winners = [token for token in tokens if token is not None]
    assert winners == [1]

    conn = psycopg.connect(DSN)
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT count(*), min(fencing_token), max(fencing_token) "
                "FROM runner_assignments WHERE job_id = %s AND status = 'ACTIVE'",
                (JOB_ID,),
            )
            active_count, min_token, max_token = cur.fetchone()
    finally:
        conn.close()

    assert active_count == 1
    assert min_token == max_token == 1
