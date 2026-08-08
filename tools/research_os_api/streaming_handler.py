#!/usr/bin/env python3
"""Streaming HTTP handler for Research OS AI responses.

Streaming v1 keeps the wire contract stable across providers. Providers that do
not yet support native token streaming use the provider-neutral chunk adapter in
``providers.AIProvider.stream``. Native provider streams can replace that
implementation later without changing Flutter clients.
"""

from __future__ import annotations

import json
from http import HTTPStatus
from urllib.parse import urlsplit

from memory import build_context, search_memory
from providers import ProviderError, build_provider
from server import ARTIFACT_DIR, ResearchOSHandler


class StreamingResearchOSHandler(ResearchOSHandler):
    """Research OS handler with an NDJSON AI streaming endpoint."""

    def do_POST(self) -> None:  # noqa: N802
        if urlsplit(self.path).path != "/v1/ai/stream":
            super().do_POST()
            return

        headers_sent = False
        try:
            body = self._read_json()
            prompt = str(body.get("prompt", body.get("question", ""))).strip()
            if not prompt:
                raise ValueError("prompt is required")

            use_memory = bool(body.get("memory", False))
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
                }
            )

            for chunk in provider.stream(
                provider_prompt,
                system=system,
                model=body.get("model"),
                chunk_size=int(body.get("chunk_size", 48)),
            ):
                if chunk.done:
                    self._write_stream_event(
                        {
                            "type": "done",
                            "provider": chunk.provider,
                            "model": chunk.model,
                            "session_id": body.get("session_id"),
                            "memory_count": len(memory_hits),
                        }
                    )
                    break
                self._write_stream_event(
                    {
                        "type": "delta",
                        "provider": chunk.provider,
                        "model": chunk.model,
                        "text": chunk.text,
                    }
                )
        except (BrokenPipeError, ConnectionResetError):
            # The Flutter client can stop generation by cancelling its stream.
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
