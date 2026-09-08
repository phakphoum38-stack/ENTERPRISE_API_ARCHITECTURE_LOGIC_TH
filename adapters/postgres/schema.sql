CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS workflow_jobs (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workflow_jobs_status_check CHECK (
        status IN ('QUEUED', 'ASSIGNED', 'RUNNING', 'SUCCEEDED', 'FAILED', 'CANCELLED', 'TIMEOUT', 'RETRYING')
    )
);

CREATE TABLE IF NOT EXISTS runner_assignments (
    job_id TEXT PRIMARY KEY REFERENCES workflow_jobs(job_id) ON DELETE CASCADE,
    runner_id TEXT NOT NULL,
    assignment_id UUID NOT NULL DEFAULT gen_random_uuid(),
    fencing_token BIGINT NOT NULL DEFAULT 1,
    lease_expires_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT runner_assignments_token_check CHECK (fencing_token > 0),
    CONSTRAINT runner_assignments_status_check CHECK (
        status IN ('ACTIVE', 'COMPLETED', 'FAILED', 'CANCELLED', 'EXPIRED')
    )
);

CREATE INDEX IF NOT EXISTS runner_assignments_active_lease_idx
    ON runner_assignments (lease_expires_at)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS runner_assignments_runner_idx
    ON runner_assignments (runner_id);
