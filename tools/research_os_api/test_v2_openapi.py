from __future__ import annotations

import unittest
from pathlib import Path


class V2OpenAPIContractTests(unittest.TestCase):
    def test_v2_contract_is_declared_in_single_openapi_source(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        required = (
            "/v2/health/readiness:",
            "/v2/providers:",
            "/v2/master:",
            "/v2/master/plan:",
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
            "V2OrchestrationPage:",
            "V2PageMetadata:",
            "V2Workspace:",
            "V2WorkspaceList:",
            "V2KnowledgeRecord:",
            "V2KnowledgePage:",
            "V2Provenance:",
            "V2Readiness:",
            "V2ErrorEnvelope:",
            "name: page_size",
            "name: cursor",
            "name: kinds",
            "name: workspace_id",
            "x-research-os-v2-status: draft",
        )
        missing = [marker for marker in required if marker not in text]
        self.assertEqual(missing, [])

    def test_master_contract_is_planning_only_and_bounded(self) -> None:
        text = Path(__file__).with_name("openapi.yaml").read_text(encoding="utf-8")
        for marker in (
            "Create a planning-only Unified Master plan",
            "maxItems: 1296",
            "maximum: 46656",
            "pattern: '^[A-Za-z0-9._:-]+$'",
            "required: [api_version, master_plan]",
        ):
            self.assertIn(marker, text)

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
