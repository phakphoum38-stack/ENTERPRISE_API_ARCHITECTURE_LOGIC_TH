import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest


DSN = os.getenv("TEST_POSTGRES_DSN", "postgresql://workflow:workflow@localhost:54329/workflow")
SCHEMA = Path("adapters/postgres/schema.sql").read_text()


@pytest.fixture()
def db():
    try:
        conn = psycopg.connect(DSN)
    except Exception as exc:
        if os.getenv("CI") == "true":
            raise RuntimeError(f"PostgreSQL integration database unavailable in CI: {exc}") from exc
        pytest.skip(f"PostgreSQL integration database unavailable: {exc}")
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
        cur.execute(SCHEMA)
        cur.execute("DELETE FROM runner_assignments")
        cur.execute("DELETE FROM workflow_jobs")
        cur.execute(
            "INSERT INTO workflow_jobs(job_id, workflow_id, status) VALUES (%s, %s, 'QUEUED')",
            ("integration-job", str(uuid4())),
        )
    try:
        yield conn
    finally:
        conn.close()


def reserve(conn, runner_id, expires_at):
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
                ("integration-job", runner_id, expires_at),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return row[0]


def test_live_postgres_concurrent_reservation_and_fencing(db):
    now = datetime.now(timezone.utc)
    token_a = reserve(db, "runner-a", now + timedelta(minutes=5))
    assert token_a == 1
    assert reserve(db, "runner-b", now + timedelta(minutes=5)) is None

    with db.cursor() as cur:
        cur.execute(
            "UPDATE runner_assignments SET lease_expires_at = now() - interval '1 second' WHERE job_id = %s",
            ("integration-job",),
        )

    token_b = reserve(db, "runner-b", now + timedelta(minutes=5))
    assert token_b == 2

    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "UPDATE runner_assignments SET status='COMPLETED', updated_at=now() "
                "WHERE job_id=%s AND fencing_token=%s AND status='ACTIVE'",
                ("integration-job", token_a),
            )
            assert cur.rowcount == 0

    with db.transaction():
        with db.cursor() as cur:
            cur.execute(
                "UPDATE runner_assignments SET status='COMPLETED', updated_at=now() "
                "WHERE job_id=%s AND fencing_token=%s AND status='ACTIVE'",
                ("integration-job", token_b),
            )
            assert cur.rowcount == 1
