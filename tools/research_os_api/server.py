#!/usr/bin/env python3
"""Dependency-free Research OS HTTP API.

Endpoints:
- GET  /health
- GET  /v1/providers
- POST /v1/ai/generate
- POST /v1/conversations/analyze
- GET  /v1/knowledge/artifacts
- GET  /v1/knowledge/graph

The API is intentionally thin: Research Curator and knowledge tools remain the
canonical implementation, while this module exposes stable transport contracts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from providers import ProviderError, build_provider


ROOT = Path(__file__).resolve().parents[2]
CURATOR_PATH = ROOT / "tools" / "research_curator" / "curator.py"
KNOWLEDGE_OPS_PATH = ROOT / "tools" / "research_curator" / "knowledge_ops.py"
ARTIFACT_DIR = ROOT / "research" / "artifacts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")


class ResearchOSHandler(BaseHTTPRequestHandler):
    server_version = "ResearchOSAPI/0.1"

    def _send(self, status: int, payload: Any) -> None:
        body = _json_bytes(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"invalid JSON: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError("JSON body must be an object")
        return value

    def do_GET(self) -> None:  # noqa: N802
        try:
            if self.path == "/health":
                self._send(HTTPStatus.OK, {"status": "ok", "service": "research-os-api", "version": "0.1.0"})
                return
            if self.path == "/v1/providers":
                self._send(HTTPStatus.OK, {
                    "providers": ["mock", "openai-compatible", "local", "anthropic", "gemini"],
                    "active": os.getenv("RESEARCH_OS_PROVIDER", "mock"),
                })
                return
            if self.path == "/v1/knowledge/artifacts":
                self._send(HTTPStatus.OK, {"artifacts": self._artifact_index()})
                return
            if self.path == "/v1/knowledge/graph":
                knowledge_ops = _load_module("research_os_knowledge_ops", KNOWLEDGE_OPS_PATH)
                artifacts = knowledge_ops.load_all(ARTIFACT_DIR)
                self._send(HTTPStatus.OK, knowledge_ops.graph_payload(artifacts))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})
        except Exception as exc:  # boundary guard
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            body = self._read_json()
            if self.path == "/v1/ai/generate":
                prompt = str(body.get("prompt", "")).strip()
                if not prompt:
                    raise ValueError("prompt is required")
                provider = build_provider(body.get("provider"))
                result = provider.generate(
                    prompt,
                    system=str(body.get("system", "")),
                    model=body.get("model"),
                )
                self._send(HTTPStatus.OK, {
                    "provider": result.provider,
                    "model": result.model,
                    "text": result.text,
                })
                return
            if self.path == "/v1/conversations/analyze":
                self._send(HTTPStatus.OK, self._analyze_conversation(body))
                return
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": self.path})
        except ValueError as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except ProviderError as exc:
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "provider_error", "detail": str(exc)})
        except Exception as exc:  # boundary guard
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def _analyze_conversation(self, body: dict[str, Any]) -> dict[str, Any]:
        conversation = body.get("conversation")
        if isinstance(conversation, list):
            source = json.dumps(conversation, ensure_ascii=False)
        elif isinstance(conversation, str):
            source = conversation
        else:
            raise ValueError("conversation must be a string or message array")

        curator = _load_module("research_os_curator", CURATOR_PATH)
        normalized = curator._normalize_source(source)
        relationships = [curator._parse_relationship(item) for item in body.get("relationships", [])]
        artifact = curator._deterministic_extract(
            normalized,
            str(body.get("title", "Research Session")),
            str(body.get("status", "hypothesis")),
            [str(x) for x in body.get("tags", [])],
            [str(x) for x in body.get("evidence", [])],
            relationships,
            ARTIFACT_DIR,
        )
        return {
            "artifact": curator.asdict(artifact),
            "accepted": artifact.quality_score >= int(body.get("min_quality", 20)),
            "persisted": False,
            "note": "API analysis is preview-only; persistence requires explicit Git workflow.",
        }

    @staticmethod
    def _artifact_index() -> list[dict[str, str]]:
        results: list[dict[str, str]] = []
        if not ARTIFACT_DIR.exists():
            return results
        for path in sorted(ARTIFACT_DIR.glob("RES-*.md")):
            text = path.read_text(encoding="utf-8")
            metadata: dict[str, str] = {}
            if text.startswith("---\n"):
                end = text.find("\n---", 4)
                if end > 0:
                    for line in text[4:end].splitlines():
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip().strip('"')
            results.append({
                "artifact_id": metadata.get("artifact_id", path.stem),
                "title": metadata.get("title", ""),
                "status": metadata.get("status", ""),
                "path": str(path.relative_to(ROOT)),
            })
        return results

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[research-os-api] " + (fmt % args) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Research OS provider-agnostic HTTP API")
    parser.add_argument("--host", default=os.getenv("RESEARCH_OS_API_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("RESEARCH_OS_API_PORT", "8787")))
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ResearchOSHandler)
    print(f"Research OS API listening on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
