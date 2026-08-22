from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class DurableAssignment:
    job_id: str
    runner_id: str
    assignment_id: UUID
    fencing_token: int


class PostgresAssignmentStore:
    """PostgreSQL adapter contract for transactional assignment/fencing.

    The adapter expects a DB-API connection. SQL is intentionally kept here so
    transaction ownership remains with the caller/application boundary.
    """

    def reserve(self, conn, job_id: str, runner_id: str, lease_expires_at) -> DurableAssignment:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO runner_assignments
                    (job_id, runner_id, assignment_id, fencing_token,
                     lease_expires_at, status)
                VALUES (%s, %s, gen_random_uuid(), 1, %s, 'ACTIVE')
                ON CONFLICT (job_id) DO UPDATE
                SET runner_id = EXCLUDED.runner_id,
                    assignment_id = EXCLUDED.assignment_id,
                    fencing_token = runner_assignments.fencing_token + 1,
                    lease_expires_at = EXCLUDED.lease_expires_at,
                    status = 'ACTIVE',
                    updated_at = now()
                WHERE runner_assignments.status <> 'ACTIVE'
                   OR runner_assignments.lease_expires_at <= now()
                RETURNING job_id, runner_id, assignment_id, fencing_token
                """,
                (job_id, runner_id, lease_expires_at),
            )
            row = cur.fetchone()
            if row is None:
                raise RuntimeError("job already has an active, unexpired assignment")
            return DurableAssignment(*row)

    def complete(self, conn, job_id: str, fencing_token: int) -> bool:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE runner_assignments
                   SET status = 'COMPLETED', updated_at = now()
                 WHERE job_id = %s
                   AND fencing_token = %s
                   AND status = 'ACTIVE'
                """,
                (job_id, fencing_token),
            )
            return cur.rowcount == 1
