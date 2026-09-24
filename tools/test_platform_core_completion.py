"""Tests for the finite Platform Core definition of done."""
from __future__ import annotations
import unittest
from tools import platform_core_completion
from tools import project_scale_readiness

class PlatformCoreCompletionTests(unittest.TestCase):
    def test_platform_core_reconciles(self) -> None:
        self.assertEqual((), platform_core_completion.validate())
    def test_exactly_one_hundred_shared_contexts(self) -> None:
        contexts = project_scale_readiness.build_project_contexts()
        self.assertEqual(100, len(contexts))
        self.assertEqual((), project_scale_readiness.validate_project_contexts(contexts))
        self.assertEqual((), project_scale_readiness.validate_registry_scale())
        self.assertEqual((), project_scale_readiness.validate_scale_levels())
    def test_project_isolation(self) -> None:
        contexts = project_scale_readiness.build_project_contexts()
        self.assertEqual((), project_scale_readiness.validate_isolation(project_a=contexts[0], project_b=contexts[1]))
    def test_duplicate_project_id_is_rejected(self) -> None:
        contexts = list(project_scale_readiness.build_project_contexts())
        contexts[1] = contexts[0]
        self.assertIn("duplicate project identity", project_scale_readiness.validate_project_contexts(tuple(contexts)))
    def test_incomplete_idempotency_identity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            project_scale_readiness.build_idempotency_key(project_id="project-001",event_id="",source_sha="a"*40,action="execute")
    def test_cross_project_idempotency_is_distinct(self) -> None:
        key_a = project_scale_readiness.build_idempotency_key(project_id="project-001",event_id="event-1",source_sha="a"*40,action="execute")
        key_b = project_scale_readiness.build_idempotency_key(project_id="project-002",event_id="event-1",source_sha="a"*40,action="execute")
        self.assertNotEqual(key_a, key_b)

if __name__ == "__main__":
    unittest.main()
