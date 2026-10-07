from pathlib import Path


def test_postgres_schema_has_atomic_assignment_invariants():
    schema = Path("adapters/postgres/schema.sql").read_text()
    assert "PRIMARY KEY" in schema
    assert "fencing_token BIGINT NOT NULL" in schema
    assert "lease_expires_at TIMESTAMPTZ NOT NULL" in schema
    assert "ON runner_assignments(job_id)" in schema


def test_postgres_adapter_fences_completion_by_token():
    source = Path("adapters/postgres/assignment_store.py").read_text()
    assert "WHERE job_id = %s" in source
    assert "AND fencing_token = %s" in source
    assert "AND status = 'ACTIVE'" in source
