#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from providers import ProviderResult
from unified_master_orchestrator import MASTER, UNIFIED_MASTER_CONTRACT
from v2_server import V2ResearchOSHandler


class _FakeToolSearchProvider:
    name = "fake-tool-search"

    def search(self, query: str, *, system: str = "", model: str | None = None) -> ProviderResult:
        del query, system
        payload = {
            "candidates": [
                {
                    "name": "Example API Tool",
                    "url": "https://example.com/tool",
                    "publisher": "Example Publisher",
                    "tool_type": "api",
                    "capabilities": ["api_integration", "testing"],
                    "integration_modes": ["REST API"],
                    "platforms": ["Windows"],
                    "license": "Apache-2.0",
                    "requires_credentials": False,
                    "network_required": True,
                    "evidence_urls": ["https://example.com/docs"],
                    "risk_level": "low",
                    "recommendation": "Evaluate with a read-only adapter first.",
                }
            ]
        }
        return ProviderResult(
            self.name,
            model or "fake-v1",
            json.dumps(payload),
            {"fake": True},
            ({"url": "https://example.com/docs", "title": "Docs"},),
        )


class V2MasterServerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), V2ResearchOSHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.original_search_factory = MASTER.tool_intelligence.search_provider_factory

    def tearDown(self) -> None:
        MASTER.tool_intelligence.search_provider_factory = self.original_search_factory
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def request(self, path: str, *, method: str = "GET", body=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode("utf-8"))

    def test_master_status_exposes_unified_contract_without_execution(self) -> None:
        status, payload = self.request("/v2/master")
        self.assertEqual(status, 200)
        self.assertEqual(payload["api_version"], "v2")
        master = payload["master"]
        self.assertEqual(master["contract"], UNIFIED_MASTER_CONTRACT)
        self.assertEqual(master["capacity"]["assistant_6x3_capacity"], 216)
        self.assertEqual(master["capacity"]["max_leaf_capacity"], 46656)
        self.assertFalse(master["invariants"]["all_workers_started_by_default"])
        self.assertFalse(master["invariants"]["external_tools_auto_executed"])

    def test_master_plan_routes_explicit_6x6_and_keeps_execution_off(self) -> None:
        status, payload = self.request(
            "/v2/master/plan",
            method="POST",
            body={
                "objective": "ใช้สมอง 6^6 วิเคราะห์เชิงลึกสำหรับ API",
                "context": {"required_tool_capabilities": ["api_integration", "testing"]},
                "budget_workers": 12,
                "ready_workers": 8,
            },
        )
        self.assertEqual(status, 200)
        plan = payload["master_plan"]
        self.assertEqual(plan["compound_brain"]["assistant_profile"]["mode"], "compound_6x6")
        self.assertEqual(plan["compound_brain"]["assistant_profile"]["theoretical_assistants"], 46656)
        self.assertFalse(plan["execution"]["performed"])
        self.assertFalse(plan["execution"]["approval_bypassed"])
        self.assertFalse(plan["execution"]["external_tool_installed"])
        self.assertFalse(plan["execution"]["external_tool_executed"])

    def test_master_tool_discovery_is_evidence_backed_and_planning_only(self) -> None:
        MASTER.tool_intelligence.search_provider_factory = lambda name: _FakeToolSearchProvider()
        status, payload = self.request(
            "/v2/master/plan",
            method="POST",
            body={
                "objective": "ค้นหาเครื่องมือสำหรับ API และ testing",
                "context": {"required_tool_capabilities": ["api_integration", "testing"]},
            },
        )
        self.assertEqual(status, 200)
        strategy = payload["master_plan"]["tool_intelligence"]
        discovery = strategy["external_discovery"]
        self.assertTrue(discovery["provider_ready"])
        self.assertEqual(discovery["candidates"][0]["name"], "Example API Tool")
        self.assertTrue(discovery["candidates"][0]["evidence_urls"])
        self.assertFalse(discovery["automatic_download"])
        self.assertFalse(discovery["automatic_install"])
        self.assertFalse(discovery["automatic_execution"])
        self.assertTrue(discovery["review_required"])


if __name__ == "__main__":
    unittest.main()
