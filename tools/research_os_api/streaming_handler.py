#!/usr/bin/env python3
"""Streaming HTTP handler for Research OS AI responses.

The wire contract is provider-neutral. Native provider streams and fallback
transport streams both emit NDJSON events understood by Flutter clients.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from http import HTTPStatus
from urllib.parse import parse_qs, urlsplit

from memory import build_context, search_memory
from memory_engine import MemoryEngine
from provider_readiness import inspect_all
from providers import ProviderError, build_provider
from server import ARTIFACT_DIR, ResearchOSHandler


class StreamingResearchOSHandler(ResearchOSHandler):
    """Research OS handler with provider capabilities, runtime memory, and NDJSON streaming."""

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/v1/providers/capabilities":
            self._send(HTTPStatus.OK, inspect_all())
            return
        if path.startswith("/v1/runtime-memory"):
            try:
                params = parse_qs(parsed.query)
                engine = MemoryEngine()
                if path == "/v1/runtime-memory":
                    records = engine.store.list()
                    self._send(
                        HTTPStatus.OK,
                        {"count": len(records), "records": [asdict(item) for item in records]},
                    )
                    return
                if path == "/v1/runtime-memory/search":
                    query = str(params.get("q", [""])[0]).strip()
                    if not query:
                        raise ValueError("q is required")
                    hits = engine.search(
                        query,
                        limit=int(params.get("limit", ["10"])[0]),
                        type=str(params.get("type", [""])[0]).strip() or None,
                        project_id=str(params.get("project_id", [""])[0]).strip() or None,
                        session_id=str(params.get("session_id", [""])[0]).strip() or None,
                        tags=params.get("tag", []),
                    )
                    self._send(
                        HTTPStatus.OK,
                        {
                            "query": query,
                            "count": len(hits),
                            "hits": [
                                {
                                    "record": asdict(hit.record),
                                    "score": hit.score,
                                    "matched_terms": hit.matched_terms,
                                }
                                for hit in hits
                            ],
                        },
                    )
                    return
                if path == "/v1/runtime-memory/timeline":
                    records = engine.timeline(
                        project_id=str(params.get("project_id", [""])[0]).strip() or None,
                        session_id=str(params.get("session_id", [""])[0]).strip() or None,
                        limit=int(params.get("limit", ["100"])[0]),
                    )
                    self._send(
                        HTTPStatus.OK,
                        {"count": len(records), "records": [asdict(item) for item in records]},
                    )
                    return
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
            except (TypeError, ValueError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            except Exception as exc:
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})
            return
        super().do_GET()

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        prefix = "/v1/runtime-memory/"
        if not path.startswith(prefix):
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "path": path})
            return
        memory_id = path[len(prefix) :].strip()
        if not memory_id:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": "memory id is required"})
            return
        try:
            deleted = MemoryEngine().store.delete(memory_id)
            self._send(HTTPStatus.OK, {"id": memory_id, "deleted": deleted})
        except Exception as exc:
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path == "/v1/runtime-memory":
            try:
                body = self._read_json()
                record = MemoryEngine().remember(
                    type=str(body.get("type", "")),
                    content=str(body.get("content", "")),
                    title=str(body.get("title", "")),
                    source=str(body.get("source", "user")),
                    project_id=body.get("project_id"),
                    session_id=body.get("session_id"),
                    provider=body.get("provider"),
                    tags=body.get("tags", []),
                    priority=int(body.get("priority", 0)),
                    metadata=body.get("metadata") if isinstance(body.get("metadata"), dict) else {},
                )
                self._send(HTTPStatus.CREATED, {"record": asdict(record)})
            except (TypeError, ValueError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            except Exception as exc:
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})
            return

        prefix = "/v1/runtime-memory/"
        if path.startswith(prefix) and path.endswith("/update"):
            memory_id = path[len(prefix) : -len("/update")].strip("/")
            try:
                body = self._read_json()
                record = MemoryEngine().store.update(memory_id, **body)
                self._send(HTTPStatus.OK, {"record": asdict(record)})
            except KeyError:
                self._send(HTTPStatus.NOT_FOUND, {"error": "not_found", "id": memory_id})
            except (TypeError, ValueError) as exc:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
            except Exception as exc:
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})
            return

        if path != "/v1/ai/stream":
            super().do_POST()
            return

        headers_sent = False
        started = time.perf_counter()
        first_delta_at: float | None = None
        output_chars = 0
        output_parts: list[str] = []
        try:
            body = self._read_json()
            prompt = str(body.get("prompt", body.get("question", ""))).strip()
            if not prompt:
                raise ValueError("prompt is required")

            use_memory = bool(body.get("memory", False))
            capture_memory = bool(body.get("capture_memory", use_memory))
            memory_hits = []
            system = str(body.get("system", ""))
            provider_prompt = prompt
            if use_memory:
                limit = int(body.get("limit", 5))
                memory_hits = search_memory(ARTIFACT_DIR, prompt, limit)
                context = build_context(memory_hits)
                system = (
                    "Answer using the supplied Research OS memory. Distinguish stored facts from inference. "
                    "When memory is insufficient, say so. Do not invent artifact contents."
                )
                provider_prompt = f"Memory:\n{context or '(no matching memory)'}\n\nQuestion:\n{prompt}"

            provider = build_provider(body.get("provider"))
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            headers_sent = True

            self._write_stream_event(
                {
                    "type": "meta",
                    "session_id": body.get("session_id"),
                    "memory_count": len(memory_hits),
                    "memory_capture": capture_memory,
                }
            )

            for chunk in provider.stream(
                provider_prompt,
                system=system,
                model=body.get("model"),
                chunk_size=int(body.get("chunk_size", 48)),
            ):
                if chunk.done:
                    elapsed_ms = int((time.perf_counter() - started) * 1000)
                    first_token_ms = None if first_delta_at is None else int((first_delta_at - started) * 1000)
                    captured_ids: list[str] = []
                    if capture_memory and output_parts:
                        engine = MemoryEngine()
                        session_id = str(body.get("session_id") or "").strip() or None
                        user_record = engine.remember(
                            type="conversation",
                            content=prompt,
                            title="User message",
                            source="chat",
                            session_id=session_id,
                            provider=chunk.provider,
                            tags=("chat", "user"),
                            metadata={"role": "user", "model": chunk.model},
                        )
                        assistant_record = engine.remember(
                            type="conversation",
                            content="".join(output_parts),
                            title="Assistant response",
                            source="chat",
                            session_id=session_id,
                            provider=chunk.provider,
                            tags=("chat", "assistant"),
                            metadata={
                                "role": "assistant",
                                "model": chunk.model,
                                "elapsed_ms": elapsed_ms,
                            },
                        )
                        captured_ids = [user_record.id, assistant_record.id]
                    self._write_stream_event(
                        {
                            "type": "done",
                            "provider": chunk.provider,
                            "model": chunk.model,
                            "session_id": body.get("session_id"),
                            "memory_count": len(memory_hits),
                            "memory_capture": capture_memory,
                            "captured_memory_ids": captured_ids,
                            "metrics": {
                                "elapsed_ms": elapsed_ms,
                                "time_to_first_delta_ms": first_token_ms,
                                "output_chars": output_chars,
                            },
                        }
                    )
                    break
                if first_delta_at is None:
                    first_delta_at = time.perf_counter()
                output_chars += len(chunk.text)
                output_parts.append(chunk.text)
                self._write_stream_event(
                    {
                        "type": "delta",
                        "provider": chunk.provider,
                        "model": chunk.model,
                        "text": chunk.text,
                    }
                )
        except (BrokenPipeError, ConnectionResetError):
            return
        except (TypeError, ValueError) as exc:
            if headers_sent:
                self._write_stream_event({"type": "error", "detail": str(exc)})
            else:
                self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request", "detail": str(exc)})
        except ProviderError as exc:
            if headers_sent:
                self._write_stream_event({"type": "error", "detail": str(exc)})
            else:
                self._send(HTTPStatus.BAD_GATEWAY, {"error": "provider_error", "detail": str(exc)})
        except Exception as exc:
            if headers_sent:
                try:
                    self._write_stream_event({"type": "error", "detail": str(exc)})
                except (BrokenPipeError, ConnectionResetError):
                    pass
            else:
                self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error", "detail": str(exc)})

    def _write_stream_event(self, payload: dict[str, object]) -> None:
        data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        self.wfile.write(data)
        self.wfile.flush()
