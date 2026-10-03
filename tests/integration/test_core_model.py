import os
from pathlib import Path

import psycopg
import pytest

DSN = os.getenv("TEST_POSTGRES_DSN", "postgresql://workflow:workflow@localhost:54329/workflow")
BASE_SCHEMA = Path("adapters/postgres/schema.sql").read_text()
CORE_SCHEMA = Path("adapters/postgres/core_model_v0_3.sql").read_text()


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
        cur.execute(BASE_SCHEMA)
        cur.execute(CORE_SCHEMA)
        cur.execute("TRUNCATE execution_events, executions, workflow_versions, workflows, projects, organizations CASCADE")
    try:
        yield conn
    finally:
        conn.close()


def test_version_branching_and_execution_pin_are_isolated(db):
    with db.cursor() as cur:
        cur.execute("INSERT INTO organizations VALUES ('org-1', 'Org 1')")
        cur.execute("INSERT INTO projects VALUES ('project-1', 'org-1', 'Project 1', now())")
        cur.execute("INSERT INTO workflows VALUES ('wf-1', 'project-1', 'deploy', now())")
        cur.execute(
            "INSERT INTO workflow_versions "
            "(workflow_version_id, workflow_id, version_number, parent_version_id, branch_name, definition) "
            "VALUES ('v10', 'wf-1', 10, NULL, 'main', '{\"jobs\": [\"build\"]}')"
        )
        cur.execute(
            "INSERT INTO workflow_versions "
            "(workflow_version_id, workflow_id, version_number, parent_version_id, branch_name, definition) "
            "VALUES ('v11-ai', 'wf-1', 11, 'v10', 'ai-fix', '{\"jobs\": [\"build\", \"test\"]}')"
        )
        cur.execute("UPDATE workflow_versions SET status='PUBLISHED', published_at=now() WHERE workflow_version_id='v10'")
        cur.execute(
            "INSERT INTO executions "
            "(execution_id, workflow_id, workflow_version_id, trace_id, snapshot) "
            "VALUES ('exec-1', 'wf-1', 'v10', 'trace-1', '{\"jobs\": [\"build\"]}')"
        )
        cur.execute("SELECT workflow_version_id, snapshot FROM executions WHERE execution_id='exec-1'")
        version_id, snapshot = cur.fetchone()
        assert version_id == "v10"
        assert snapshot["jobs"] == ["build"]


def test_published_version_is_immutable(db):
    with db.cursor() as cur:
        cur.execute("INSERT INTO organizations VALUES ('org-2', 'Org 2')")
        cur.execute("INSERT INTO projects VALUES ('project-2', 'org-2', 'Project 2', now())")
        cur.execute("INSERT INTO workflows VALUES ('wf-2', 'project-2', 'build', now())")
        cur.execute(
            "INSERT INTO workflow_versions "
            "(workflow_version_id, workflow_id, version_number, branch_name, definition, status, published_at) "
            "VALUES ('v20', 'wf-2', 20, 'main', '{\"jobs\": [\"build\"]}', 'PUBLISHED', now())"
        )
        with pytest.raises(psycopg.errors.RaiseException):
            cur.execute(
                "UPDATE workflow_versions SET definition='{\"jobs\": [\"deploy\"]}' WHERE workflow_version_id='v20'"
            )


def test_execution_rejects_version_from_another_workflow(db):
    with db.cursor() as cur:
        cur.execute("INSERT INTO organizations VALUES ('org-3', 'Org 3')")
        cur.execute("INSERT INTO projects VALUES ('project-3', 'org-3', 'Project 3', now())")
        cur.execute("INSERT INTO workflows VALUES ('wf-3a', 'project-3', 'a', now())")
        cur.execute("INSERT INTO workflows VALUES ('wf-3b', 'project-3', 'b', now())")
        cur.execute(
            "INSERT INTO workflow_versions "
            "(workflow_version_id, workflow_id, version_number, branch_name, definition) "
            "VALUES ('v30', 'wf-3a', 30, 'main', '{}')"
        )
        with pytest.raises(psycopg.errors.RaiseException):
            cur.execute(
                "INSERT INTO executions "
                "(execution_id, workflow_id, workflow_version_id, trace_id, snapshot) "
                "VALUES ('exec-bad', 'wf-3b', 'v30', 'trace-bad', '{}')"
            )
