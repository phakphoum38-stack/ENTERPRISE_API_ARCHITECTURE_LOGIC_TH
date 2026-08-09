from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from v2_observability import (
    diagnostics_bundle,
    readiness_snapshot,
    redact,
    structured_event,
    write_diagnostics_bundle,
)


class V2ObservabilityTests(unittest.TestCase):
    def test_redaction_removes_nested_secret_values(self) -> None:
        payload = redact(
            {
                "api_key": "secret-value",
                "nested": {"Authorization": "Bearer hidden", "safe": "visible"},
                "items": [{"token": "hidden", "status": "ok"}],
            }
        )
        self.assertEqual(payload["api_key"], "[REDACTED]")
        self.assertEqual(payload["nested"]["Authorization"], "[REDACTED]")
        self.assertEqual(payload["nested"]["safe"], "visible")
        self.assertEqual(payload["items"][0]["token"], "[REDACTED]")

    def test_structured_event_contains_correlation_run_and_task_ids(self) -> None:
        event = structured_event(
            "orchestration.test",
            correlation="corr-123",
            run_id="run-1",
            task_id="task-1",
            detail={"status": "ok"},
        )
        self.assertEqual(event["correlation_id"], "corr-123")
        self.assertEqual(event["run_id"], "run-1")
        self.assertEqual(event["task_id"], "task-1")
        self.assertEqual(event["detail"]["status"], "ok")

    def test_readiness_and_bundle_are_secret_safe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "RESEARCH_OS_DATA_DIR": tmp,
                "RESEARCH_OS_PROVIDER": "mock",
                "RESEARCH_OS_FAKE_TOKEN": "must-not-leak",
            },
            clear=False,
        ):
            readiness = readiness_snapshot(tmp)
            self.assertTrue(readiness["ready"])
            self.assertTrue(readiness["storage"]["writable"])
            self.assertEqual(readiness["provider"]["provider"], "mock")

            bundle = diagnostics_bundle(tmp)
            self.assertEqual(bundle["environment"]["RESEARCH_OS_FAKE_TOKEN"], "[REDACTED]")
            serialized = json.dumps(bundle)
            self.assertNotIn("must-not-leak", serialized)

            target = Path(tmp) / "diagnostics" / "bundle.json"
            written = write_diagnostics_bundle(target, tmp)
            self.assertEqual(written, target)
            self.assertTrue(target.exists())
            self.assertNotIn("must-not-leak", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
