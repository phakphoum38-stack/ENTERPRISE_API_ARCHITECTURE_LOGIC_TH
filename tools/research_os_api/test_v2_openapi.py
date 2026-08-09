from __future__ import annotations

import unittest
from pathlib import Path


class V2OpenAPIContractTests(unittest.TestCase):
    def test_v2_contract_is_declared_in_single_openapi_source(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        required = (
            "/v2/health/readiness:",
            "/v2/providers:",
            "/v2/agents:",
            "/v2/agents/readiness:",
            "/v2/agents/discover:",
            "/v2/orchestrations:",
            "/v2/orchestrations/{run_id}:",
            "/v2/orchestrations/{run_id}/timeline:",
            "/v2/orchestrations/{run_id}/execute:",
            "/v2/orchestrations/{run_id}/confirm:",
            "/v2/orchestrations/{run_id}/retry:",
            "/v2/orchestrations/{run_id}/cancel:",
            "/v2/workspaces:",
            "/v2/workspaces/{workspace_id}/knowledge:",
            "/v2/intelligence:",
            "/v2/intelligence/capabilities:",
            "/v2/intelligence/agents:",
            "/v2/intelligence/skills:",
            "/v2/intelligence/tools:",
            "/v2/intelligence/permissions:",
            "/v2/intelligence/architecture:",
            "/v2/intelligence/project-state:",
            "/v2/intelligence/health:",
            "/v2/intelligence/plan:",
            "V2OrchestrationPage:",
            "V2PageMetadata:",
            "V2Workspace:",
            "V2WorkspaceList:",
            "V2KnowledgeRecord:",
            "V2KnowledgePage:",
            "V2Provenance:",
            "V2Readiness:",
            "V2IntelligencePlanRequest:",
            "V2IntelligenceEnvelope:",
            "V2ErrorEnvelope:",
            "brain-system-introspection-phase-7",
            "name: page_size",
            "name: cursor",
            "name: kinds",
            "name: workspace_id",
            "name: capability",
            "name: permission",
            "name: ready_only",
            "x-research-os-v2-status: draft",
        )
        missing = [marker for marker in required if marker not in text]
        self.assertEqual(missing, [])

    def test_workspace_contract_keeps_provenance_and_cursor_pagination(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        for marker in (
            "$ref: '#/components/schemas/V2WorkspaceList'",
            "$ref: '#/components/schemas/V2KnowledgePage'",
            "$ref: '#/components/schemas/V2Provenance'",
            "next_cursor:",
            "source_type:",
            "source_id:",
            "evidence:",
            "content_hash:",
        ):
            self.assertIn(marker, text)

    def test_intelligence_contract_is_introspection_and_plan_only(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        for marker in (
            "summary: Return the read-only Research OS AI Brain System Introspection manifest",
            "summary: Build a secret-safe read-only Brain plan without executing tools or granting permissions",
            "summary: Inspect descriptive permission requirements without granting permissions",
            "maxLength: 8000",
        ):
            self.assertIn(marker, text)
        for forbidden in (
            "/v2/intelligence/execute:",
            "/v2/intelligence/grant:",
            "/v2/intelligence/deploy:",
            "/v2/intelligence/release:",
        ):
            self.assertNotIn(forbidden, text)

    def test_v1_contract_remains_present_during_v2_migration(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        for marker in (
            "/v1/providers:",
            "/v1/agents:",
            "/v1/agents/orchestrations:",
            "/v1/agents/orchestrations/{run_id}/execute:",
        ):
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
