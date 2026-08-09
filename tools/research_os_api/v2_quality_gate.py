#!/usr/bin/env python3
"""Executable V2 performance and resilience quality probes.

The probes use only local/mock dependencies and are safe for pull-request CI.
They do not publish, release, or modify production state.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent


def _p95(samples: list[float]) -> float:
    ordered = sorted(samples)
    return ordered[max(0, int(len(ordered) * 0.95) - 1)]


def _request_json(url: str, *, data: dict | None = None) -> dict:
    body = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body is not None else {},
        method="POST" if body is not None else "GET",
    )
    with urllib.request.urlopen(request, timeout=3) as response:
        return json.load(response)


def _rss_kb(pid: int) -> int | None:
    status = Path(f"/proc/{pid}/status")
    if not status.exists():
        return None
    for line in status.read_text(encoding="utf-8").splitlines():
        if line.startswith("VmRSS:"):
            return int(line.split()[1])
    return None


def run_performance() -> dict:
    port = "18787"
    base = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env.update(
            {
                "RESEARCH_OS_PROVIDER": "mock",
                "RESEARCH_OS_API_HOST": "127.0.0.1",
                "RESEARCH_OS_API_PORT": port,
                "HOST": "127.0.0.1",
                "PORT": port,
                "RESEARCH_OS_DATA_DIR": tmp,
            }
        )
        started = time.perf_counter()
        process = subprocess.Popen(
            [sys.executable, "render_server.py"],
            cwd=HERE,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(50):
                if process.poll() is not None:
                    raise RuntimeError(f"API exited during startup with code {process.returncode}")
                try:
                    payload = _request_json(f"{base}/health")
                    if payload.get("status") == "ok":
                        break
                except Exception:
                    time.sleep(0.2)
            else:
                raise RuntimeError("API did not become healthy within 10 seconds")

            startup_ms = (time.perf_counter() - started) * 1000
            if startup_ms > 10_000:
                raise AssertionError(f"startup readiness too slow: {startup_ms:.1f} ms")

            endpoint_metrics: dict[str, dict[str, float]] = {}
            for name, url in {
                "health": f"{base}/health",
                "v2_readiness": f"{base}/v2/health/readiness",
            }.items():
                samples: list[float] = []
                for _ in range(20):
                    sample_start = time.perf_counter()
                    payload = _request_json(url)
                    elapsed = (time.perf_counter() - sample_start) * 1000
                    if name == "health":
                        assert payload.get("status") == "ok", payload
                    else:
                        assert payload.get("ready") is True, payload
                    samples.append(elapsed)
                p95 = _p95(samples)
                if p95 > 500:
                    raise AssertionError(f"{name} p95 too slow: {p95:.1f} ms")
                endpoint_metrics[name] = {
                    "avg_ms": statistics.mean(samples),
                    "p95_ms": p95,
                    "max_ms": max(samples),
                }

            orchestration_samples: list[float] = []
            for index in range(10):
                created = _request_json(
                    f"{base}/v2/orchestrations",
                    data={
                        "objective": f"quality performance baseline {index}",
                        "steps": [
                            {
                                "step_id": "research",
                                "objective": f"research performance baseline {index}",
                                "requested_agent": "research",
                            }
                        ],
                    },
                )
                run_id = created["run"]["run_id"]
                sample_start = time.perf_counter()
                completed = _request_json(
                    f"{base}/v2/orchestrations/{run_id}/execute",
                    data={},
                )
                elapsed = (time.perf_counter() - sample_start) * 1000
                assert completed["run"]["status"] == "completed", completed
                orchestration_samples.append(elapsed)

            orchestration_p95 = _p95(orchestration_samples)
            if orchestration_p95 > 1000:
                raise AssertionError(
                    f"orchestration execute p95 too slow: {orchestration_p95:.1f} ms"
                )

            rss_kb = _rss_kb(process.pid)
            if rss_kb is not None and rss_kb > 300_000:
                raise AssertionError(f"API RSS exceeds V2 baseline: {rss_kb} KB")

            return {
                "startup_ready_ms": round(startup_ms, 1),
                "endpoints": endpoint_metrics,
                "orchestration_execute": {
                    "avg_ms": statistics.mean(orchestration_samples),
                    "p95_ms": orchestration_p95,
                    "max_ms": max(orchestration_samples),
                },
                "api_rss_kb": rss_kb,
                "thresholds": {
                    "startup_ready_ms": 10_000,
                    "endpoint_p95_ms": 500,
                    "orchestration_p95_ms": 1000,
                    "api_rss_kb": 300_000,
                },
            }
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def run_resilience() -> dict:
    import providers
    from agent_orchestrator import AgentOrchestrator
    from agent_runtime import AgentEventBus, AgentTaskQueue, SharedContextStore
    from v2_observability import diagnostics_bundle, storage_readiness

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": true}'

    attempts = {"n": 0}

    def transient_urlopen(request, timeout=60):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "busy",
                {},
                io.BytesIO(b'{"error":"busy"}'),
            )
        return FakeResponse()

    with patch.object(providers.urllib.request, "urlopen", side_effect=transient_urlopen), patch.object(
        providers.time, "sleep", return_value=None
    ):
        payload = providers._post_json(
            "https://example.invalid",
            {"x": 1},
            {"Content-Type": "application/json"},
        )
    assert payload == {"ok": True}, payload
    assert attempts["n"] == 3, attempts

    non_retry_attempts = {"n": 0}

    def non_retryable_urlopen(request, timeout=60):
        non_retry_attempts["n"] += 1
        raise urllib.error.HTTPError(
            request.full_url,
            400,
            "bad request",
            {},
            io.BytesIO(b'{"error":"bad"}'),
        )

    try:
        with patch.object(
            providers.urllib.request, "urlopen", side_effect=non_retryable_urlopen
        ), patch.object(providers.time, "sleep", return_value=None):
            providers._post_json("https://example.invalid", {"x": 1}, {})
    except providers.ProviderError:
        pass
    else:
        raise AssertionError("expected ProviderError for non-retryable 400")
    assert non_retry_attempts["n"] == 1, non_retry_attempts

    with patch.object(Path, "mkdir", side_effect=PermissionError("injected storage denial")):
        state = storage_readiness("/tmp/research-os-injected-denial")
    assert state["ready"] is False, state
    assert state["writable"] is False, state
    assert state["error"] == "PermissionError", state

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        state_path = root / "agents" / "orchestrations.json"
        runtime = AgentTaskQueue(
            event_bus=AgentEventBus(),
            context_store=SharedContextStore(tmp),
        )
        orchestrator = AgentOrchestrator(runtime=runtime, storage_path=state_path)
        run = orchestrator.create_run(
            "runtime interruption injection",
            [
                {
                    "step_id": "research",
                    "objective": "research runtime interruption evidence",
                    "requested_agent": "research",
                }
            ],
        )
        run_id = run["run_id"]
        persisted = json.loads(state_path.read_text(encoding="utf-8"))
        persisted["runs"][0]["status"] = "running"
        persisted["runs"][0]["steps"][0]["status"] = "running"
        persisted["runs"][0]["steps"][0]["task_id"] = "injected-stale-task"
        state_path.write_text(json.dumps(persisted), encoding="utf-8")

        recovered = AgentOrchestrator(
            runtime=AgentTaskQueue(
                event_bus=AgentEventBus(),
                context_store=SharedContextStore(tmp),
            ),
            storage_path=state_path,
        )
        interrupted = recovered.get(run_id)
        assert interrupted["status"] == "interrupted", interrupted
        assert interrupted["steps"][0]["status"] == "planned", interrupted
        completed = recovered.execute(run_id)
        assert completed["run_id"] == run_id, completed
        assert completed["status"] == "completed", completed

    old_secret = os.environ.get("RESEARCH_OS_TEST_TOKEN")
    os.environ["RESEARCH_OS_TEST_TOKEN"] = "never-print-this-value"
    try:
        diagnostics = json.dumps(diagnostics_bundle(), sort_keys=True)
    finally:
        if old_secret is None:
            os.environ.pop("RESEARCH_OS_TEST_TOKEN", None)
        else:
            os.environ["RESEARCH_OS_TEST_TOKEN"] = old_secret
    assert "never-print-this-value" not in diagnostics
    assert "[REDACTED]" in diagnostics

    provider_source = (HERE / "providers.py").read_text(encoding="utf-8")
    assert "max_attempts = 4" in provider_source
    assert "min(delay, 8.0)" in provider_source

    return {
        "provider_transient_503_attempts": attempts["n"],
        "provider_non_retryable_400_attempts": non_retry_attempts["n"],
        "storage_failure_injection": "passed",
        "runtime_interruption_resume": "passed",
        "diagnostics_redaction": "passed",
        "retry_bounds": "passed",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=("performance", "resilience", "all"))
    args = parser.parse_args()

    output: dict[str, dict] = {}
    if args.gate in {"performance", "all"}:
        output["performance"] = run_performance()
    if args.gate in {"resilience", "all"}:
        output["resilience"] = run_resilience()
    print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
