CREATE TABLE IF NOT EXISTS workflow_jobs (
    job_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS runner_assignments (
    job_id TEXT PRIMARY KEY REFERENCES workflow_jobs(job_id) ON DELETE CASCADE,
    runner_id TEXT NOT NULL,
    assignment_id UUID NOT NULL UNIQUE,
    fencing_token BIGINT NOT NULL,
    lease_expires_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS runner_assignments_active_job_idx
    ON runner_assignments(job_id)
    WHERE status = 'ACTIVE';

CREATE INDEX IF NOT EXISTS runner_assignments_runner_idx
    ON runner_assignments(runner_id, status);
