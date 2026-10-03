-- v0.3.0 core model: tenant boundary, immutable workflow versions,
-- pinned executions, execution snapshots, and append-only event history.
-- Apply after adapters/postgres/schema.sql.

CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (organization_id, name)
);

CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, name)
);

CREATE TABLE IF NOT EXISTS workflow_versions (
    workflow_version_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id) ON DELETE CASCADE,
    version_number BIGINT NOT NULL CHECK (version_number > 0),
    parent_version_id TEXT REFERENCES workflow_versions(workflow_version_id),
    branch_name TEXT NOT NULL,
    definition JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'DRAFT',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ,
    UNIQUE (workflow_id, version_number),
    UNIQUE (workflow_version_id, workflow_id)
);

CREATE INDEX IF NOT EXISTS workflow_versions_parent_idx
    ON workflow_versions(parent_version_id);

CREATE TABLE IF NOT EXISTS executions (
    execution_id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL REFERENCES workflows(workflow_id) ON DELETE RESTRICT,
    workflow_version_id TEXT NOT NULL REFERENCES workflow_versions(workflow_version_id) ON DELETE RESTRICT,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    trace_id TEXT NOT NULL,
    snapshot JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS executions_workflow_version_idx
    ON executions(workflow_version_id, created_at);
CREATE INDEX IF NOT EXISTS executions_trace_idx
    ON executions(trace_id);

CREATE TABLE IF NOT EXISTS execution_events (
    event_id BIGSERIAL PRIMARY KEY,
    execution_id TEXT NOT NULL REFERENCES executions(execution_id) ON DELETE CASCADE,
    trace_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    schema_version INTEGER NOT NULL DEFAULT 1 CHECK (schema_version > 0),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS execution_events_execution_idx
    ON execution_events(execution_id, occurred_at, event_id);
CREATE INDEX IF NOT EXISTS execution_events_trace_idx
    ON execution_events(trace_id, occurred_at, event_id);

-- A published version is immutable. Drafts may be updated before publication,
-- but identity, parent, branch and definition cannot change after publication.
CREATE OR REPLACE FUNCTION prevent_published_workflow_version_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF OLD.status = 'PUBLISHED' THEN
        IF NEW.workflow_id IS DISTINCT FROM OLD.workflow_id
           OR NEW.version_number IS DISTINCT FROM OLD.version_number
           OR NEW.parent_version_id IS DISTINCT FROM OLD.parent_version_id
           OR NEW.branch_name IS DISTINCT FROM OLD.branch_name
           OR NEW.definition IS DISTINCT FROM OLD.definition THEN
            RAISE EXCEPTION 'published workflow version % is immutable', OLD.workflow_version_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS workflow_version_immutable ON workflow_versions;
CREATE TRIGGER workflow_version_immutable
BEFORE UPDATE ON workflow_versions
FOR EACH ROW
EXECUTE FUNCTION prevent_published_workflow_version_mutation();

-- Execution must be pinned to the version belonging to the same workflow.
CREATE OR REPLACE FUNCTION validate_execution_version_owner()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    version_workflow_id TEXT;
BEGIN
    SELECT workflow_id INTO version_workflow_id
    FROM workflow_versions
    WHERE workflow_version_id = NEW.workflow_version_id;

    IF version_workflow_id IS NULL OR version_workflow_id <> NEW.workflow_id THEN
        RAISE EXCEPTION 'execution % must reference a version belonging to workflow %',
            NEW.execution_id, NEW.workflow_id;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS execution_version_owner ON executions;
CREATE TRIGGER execution_version_owner
BEFORE INSERT OR UPDATE OF workflow_id, workflow_version_id ON executions
FOR EACH ROW
EXECUTE FUNCTION validate_execution_version_owner();
