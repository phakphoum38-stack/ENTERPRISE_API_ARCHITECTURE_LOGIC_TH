from __future__ import annotations

import ipaddress
import json
import re
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from .contracts import health_contract, master_contract, providers_contract
from .memory import MemoryStore
from .models import Workload
from .orchestrator import UnifiedMasterOrchestrator
from .skill_runtime import SkillRuntimeContext
from .storage import DataLayout
from .user_context import UserContext

USER_HEADER = "X-Research-OS-User"
PROFILE_HEADER = "X-Research-OS-Profile"
APPROVAL_HEADER = "X-Research-OS-Approval"


class V3LocalService:
    """Loopback-only HTTP service exposing the governed V3 full-system API."""

    def __init__(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 8788,
        orchestrator: UnifiedMasterOrchestrator | None = None,
        audit_path: Path | None = None,
        data_layout: DataLayout | None = None,
    ) -> None:
        address = ipaddress.ip_address(host)
        if not address.is_loopback:
            raise ValueError("V3 local service must bind to a loopback address")
        self.host = host
        self.port = port
        self.orchestrator = orchestrator or UnifiedMasterOrchestrator()
        self.audit_path = audit_path
        self.data_layout = (data_layout or DataLayout.from_environment()).ensure()
        self._server: ThreadingHTTPServer | None = None

    def build_server(self) -> ThreadingHTTPServer:
        orchestrator = self.orchestrator
        data_layout = self.data_layout
        memory = MemoryStore(data_layout)
        audit_path = self.audit_path
        audit_lock = threading.Lock()
        if audit_path is not None:
            audit_path.parent.mkdir(parents=True, exist_ok=True)

        def write_audit(method: str, path: str, status: int) -> None:
            if audit_path is None:
                return
            record = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "method": method,
                "path": path,
                "status": status,
            }
            line = json.dumps(record, sort_keys=True) + "\n"
            with audit_lock:
                with audit_path.open("a", encoding="utf-8") as stream:
                    stream.write(line)

        class Handler(BaseHTTPRequestHandler):
            server_version = "ResearchOSV3Full/1"

            def log_message(self, format: str, *args: object) -> None:
                return

            def _write_json(
                self,
                status: int,
                payload: dict[str, object],
                *,
                method: str,
            ) -> None:
                body = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                write_audit(method, urlparse(self.path).path, status)
                self.wfile.write(body)

            def _read_json(self) -> dict[str, object] | None:
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 1_048_576:
                    self._write_json(400, {"error": "invalid request body"}, method="POST")
                    return None
                try:
                    decoded = json.loads(self.rfile.read(length).decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    self._write_json(400, {"error": "invalid json"}, method="POST")
                    return None
                if not isinstance(decoded, dict):
                    self._write_json(400, {"error": "json body must be an object"}, method="POST")
                    return None
                return {str(key): value for key, value in decoded.items()}

            def _required_user_context(self, *, method: str) -> UserContext | None:
                user_id = self.headers.get(USER_HEADER)
                if not user_id:
                    self._write_json(
                        400,
                        {"error": "missing user context", "required_header": USER_HEADER},
                        method=method,
                    )
                    return None
                profile_id = self.headers.get(PROFILE_HEADER, "default")
                try:
                    return UserContext(user_id=user_id, profile_id=profile_id)
                except ValueError as exc:
                    self._write_json(
                        400,
                        {"error": "invalid user context", "detail": str(exc)},
                        method=method,
                    )
                    return None

            def _workload_from_query(self, parsed) -> Workload | None:
                query = parse_qs(parsed.query)
                try:
                    return Workload(
                        estimated_leaf_tasks=int(query.get("tasks", ["1"])[0]),
                        risk=int(query.get("risk", ["1"])[0]),
                        parallelism=int(query.get("parallelism", ["1"])[0]),
                    )
                except ValueError:
                    self._write_json(400, {"error": "invalid workload parameters"}, method="GET")
                    return None

            def _skill_context(
                self,
                context: UserContext,
                *,
                approved: bool,
            ) -> SkillRuntimeContext:
                user_layout = data_layout.for_user(context).ensure()

                def memory_search(query: str, limit: int) -> list[dict[str, object]]:
                    return [item.to_dict() for item in memory.search(context, query, limit=limit)]

                def memory_add(text: str, tags: tuple[str, ...]) -> dict[str, object]:
                    return memory.add(context, text, tags=tags).to_dict()

                def provider_complete(prompt: str, preferred: str | None) -> dict[str, object]:
                    response = orchestrator.answer(prompt, preferred_provider=preferred)
                    return {"text": response.text, "provider": response.provider, "model": response.model}

                def provider_snapshot() -> list[dict[str, object]]:
                    return [item.to_safe_dict() for item in orchestrator.providers.statuses()]

                def agent_snapshot() -> list[dict[str, object]]:
                    return [
                        {
                            "name": item.name,
                            "role": item.role,
                            "description": item.description,
                            "skills": list(item.skills),
                            "tools": list(item.tools),
                        }
                        for item in orchestrator.agents.list()
                    ]

                def agent_run(agent_name: str, prompt: str) -> dict[str, object]:
                    response = orchestrator.answer(prompt, agent_name=agent_name)
                    return {"agent": agent_name, "text": response.text, "provider": response.provider, "model": response.model}

                def tool_run(tool_name: str, arguments: dict[str, object], is_approved: bool) -> dict[str, object]:
                    return orchestrator.execute_tool(tool_name, arguments, approved=is_approved)

                def factory_plan(tasks: int) -> dict[str, object]:
                    decision, plan = orchestrator.plan(Workload(estimated_leaf_tasks=tasks))
                    return {
                        "decision": master_contract(decision),
                        "stage_order": list(plan.stage_order),
                        "scale": plan.profile.tier.value,
                        "maximum_leaf_capacity": plan.profile.capacity,
                    }

                return SkillRuntimeContext(
                    user_id=context.user_id,
                    profile_id=context.profile_id,
                    user_data_root=user_layout.root,
                    repository_root=Path(__file__).resolve().parents[2],
                    approved=approved,
                    memory_search=memory_search,
                    memory_add=memory_add,
                    provider_complete=provider_complete,
                    provider_snapshot=provider_snapshot,
                    agent_run=agent_run,
                    agent_snapshot=agent_snapshot,
                    tool_run=tool_run,
                    factory_plan=factory_plan,
                )

            def do_GET(self) -> None:  # noqa: N802 - stdlib handler contract
                parsed = urlparse(self.path)
                if parsed.path == "/health":
                    self._write_json(200, health_contract(), method="GET")
                    return
                if parsed.path == "/v3/providers":
                    self._write_json(200, providers_contract(orchestrator.providers), method="GET")
                    return
                if parsed.path == "/v3/master":
                    workload = self._workload_from_query(parsed)
                    if workload is None:
                        return
                    decision = orchestrator.decide(workload)
                    self._write_json(200, master_contract(decision), method="GET")
                    return
                if parsed.path == "/v3/factory/plan":
                    workload = self._workload_from_query(parsed)
                    if workload is None:
                        return
                    decision, plan = orchestrator.plan(workload)
                    self._write_json(
                        200,
                        {
                            "decision": master_contract(decision),
                            "stage_order": list(plan.stage_order),
                            "scale": plan.profile.tier.value,
                            "maximum_leaf_capacity": plan.profile.capacity,
                        },
                        method="GET",
                    )
                    return
                if parsed.path == "/v3/skills":
                    self._write_json(
                        200,
                        {
                            "skills": [
                                {
                                    "name": item.name,
                                    "origin": item.origin.value,
                                    "capability": item.capability,
                                    "description": item.description,
                                    "native_v3": item.native_v3,
                                    "runtime_mode": item.runtime_mode,
                                    "source": item.source,
                                    "execution_adapter": item.execution_adapter,
                                }
                                for item in orchestrator.skills.list()
                            ],
                            "count": len(orchestrator.skills.list()),
                            "native_count": sum(1 for item in orchestrator.skills.list() if item.native_v3),
                            "context_adapter_count": sum(1 for item in orchestrator.skills.list() if item.runtime_mode == "context-adapter"),
                            "origins": [origin.value for origin in orchestrator.skills.origins()],
                            "single_authority": orchestrator.contract,
                        },
                        method="GET",
                    )
                    return
                if parsed.path == "/v3/tools":
                    self._write_json(
                        200,
                        {
                            "tools": [
                                {
                                    "name": item.name,
                                    "capability": item.capability,
                                    "description": item.description,
                                    "risk": item.risk.value,
                                    "approval_required": item.approval_required,
                                }
                                for item in orchestrator.tools.list()
                            ]
                        },
                        method="GET",
                    )
                    return
                if parsed.path == "/v3/agents":
                    self._write_json(
                        200,
                        {
                            "agents": [
                                {
                                    "name": item.name,
                                    "role": item.role,
                                    "description": item.description,
                                    "skills": list(item.skills),
                                    "tools": list(item.tools),
                                }
                                for item in orchestrator.agents.list()
                            ]
                        },
                        method="GET",
                    )
                    return
                if parsed.path == "/v3/user":
                    context = self._required_user_context(method="GET")
                    if context is None:
                        return
                    user_layout = data_layout.for_user(context).ensure()
                    self._write_json(
                        200,
                        {
                            "user_id": context.user_id,
                            "profile_id": context.profile_id,
                            "scope": f"users/{context.user_id}/profiles/{context.profile_id}",
                            "isolated": True,
                            "directories": sorted(user_layout.directories()),
                        },
                        method="GET",
                    )
                    return
                if parsed.path == "/v3/memory":
                    context = self._required_user_context(method="GET")
                    if context is None:
                        return
                    query = parse_qs(parsed.query)
                    text = query.get("q", [""])[0]
                    try:
                        limit = int(query.get("limit", ["20"])[0])
                    except ValueError:
                        limit = 20
                    records = memory.search(context, text, limit=limit) if text else memory.list(context, limit=limit)
                    self._write_json(
                        200,
                        {"memory": [record.to_dict() for record in records]},
                        method="GET",
                    )
                    return
                self._write_json(404, {"error": "not found"}, method="GET")

            def do_POST(self) -> None:  # noqa: N802 - stdlib handler contract
                parsed = urlparse(self.path)
                body = self._read_json()
                if body is None:
                    return

                if parsed.path == "/v3/memory":
                    context = self._required_user_context(method="POST")
                    if context is None:
                        return
                    text = str(body.get("text", "")).strip()
                    raw_tags = body.get("tags", [])
                    tags = tuple(str(tag) for tag in raw_tags) if isinstance(raw_tags, list) else ()
                    try:
                        record = memory.add(context, text, tags=tags)
                    except ValueError as exc:
                        self._write_json(400, {"error": str(exc)}, method="POST")
                        return
                    self._write_json(201, {"memory": record.to_dict()}, method="POST")
                    return

                if parsed.path == "/v3/chat":
                    context = self._required_user_context(method="POST")
                    if context is None:
                        return
                    prompt = str(body.get("prompt", "")).strip()
                    if not prompt:
                        self._write_json(400, {"error": "prompt must not be empty"}, method="POST")
                        return
                    try:
                        memory_limit = max(0, min(int(body.get("memory_limit", 8)), 20))
                    except (TypeError, ValueError):
                        memory_limit = 8
                    hits = memory.search(context, prompt, limit=memory_limit) if memory_limit else []
                    memory_context = "\n".join(f"- {item.text}" for item in hits) or None
                    try:
                        response = orchestrator.answer(
                            prompt,
                            memory_context=memory_context,
                            preferred_provider=(str(body["preferred_provider"]) if body.get("preferred_provider") else None),
                            agent_name=(str(body["agent"]) if body.get("agent") else None),
                        )
                    except (KeyError, RuntimeError, ValueError) as exc:
                        self._write_json(503, {"error": str(exc)}, method="POST")
                        return
                    self._write_json(
                        200,
                        {
                            "text": response.text,
                            "provider": response.provider,
                            "model": response.model,
                            "memory_hits": [item.to_dict() for item in hits],
                        },
                        method="POST",
                    )
                    return

                if parsed.path == "/v3/agents/run":
                    context = self._required_user_context(method="POST")
                    if context is None:
                        return
                    name = str(body.get("name", "")).strip()
                    prompt = str(body.get("prompt", "")).strip()
                    if not name or not prompt:
                        self._write_json(400, {"error": "name and prompt are required"}, method="POST")
                        return
                    hits = memory.search(context, prompt, limit=6)
                    memory_context = "\n".join(f"- {item.text}" for item in hits) or None
                    try:
                        response = orchestrator.answer(prompt, memory_context=memory_context, agent_name=name)
                    except (KeyError, RuntimeError, ValueError) as exc:
                        self._write_json(503, {"error": str(exc)}, method="POST")
                        return
                    self._write_json(
                        200,
                        {
                            "agent": name,
                            "text": response.text,
                            "provider": response.provider,
                            "model": response.model,
                            "memory_hits": [item.to_dict() for item in hits],
                        },
                        method="POST",
                    )
                    return

                if parsed.path == "/v3/skills/execute":
                    context = self._required_user_context(method="POST")
                    if context is None:
                        return
                    name = str(body.get("name", "")).strip()
                    text = str(body.get("text", ""))
                    arguments = body.get("arguments", {})
                    if not name:
                        self._write_json(400, {"error": "skill name is required"}, method="POST")
                        return
                    if not isinstance(arguments, dict):
                        self._write_json(400, {"error": "arguments must be an object"}, method="POST")
                        return
                    approved = self.headers.get(APPROVAL_HEADER, "").strip().lower() == "granted"
                    runtime_context = self._skill_context(context, approved=approved)
                    try:
                        result = orchestrator.execute_skill(
                            name,
                            text,
                            arguments=dict(arguments),
                            context=runtime_context,
                        )
                    except KeyError:
                        self._write_json(404, {"error": f"unknown skill or resource: {name}"}, method="POST")
                        return
                    except PermissionError as exc:
                        self._write_json(403, {"error": str(exc), "approval_header": APPROVAL_HEADER}, method="POST")
                        return
                    except ValueError as exc:
                        self._write_json(400, {"error": str(exc)}, method="POST")
                        return
                    except RuntimeError as exc:
                        self._write_json(503, {"error": str(exc)}, method="POST")
                        return
                    self._write_json(200, result, method="POST")
                    return

                if parsed.path == "/v3/tools/execute":
                    context = self._required_user_context(method="POST")
                    if context is None:
                        return
                    name = str(body.get("name", "")).strip()
                    arguments = body.get("arguments", {})
                    if not isinstance(arguments, dict):
                        self._write_json(400, {"error": "arguments must be an object"}, method="POST")
                        return
                    approved = self.headers.get(APPROVAL_HEADER, "").strip().lower() == "granted"
                    try:
                        if name == "artifact-note":
                            definition = orchestrator.tools.get(name)
                            if definition is None:
                                raise KeyError(name)
                            if definition.approval_required and not approved:
                                raise PermissionError("tool requires approval: artifact-note")
                            text = str(arguments.get("text", "")).strip()
                            if not text:
                                raise ValueError("artifact note text must not be empty")
                            title = str(arguments.get("title", "note")).strip() or "note"
                            safe_title = re.sub(r"[^A-Za-z0-9._-]+", "-", title).strip("-._")[:60] or "note"
                            path = data_layout.for_user(context).ensure().artifacts / f"{safe_title}-{uuid4().hex[:8]}.txt"
                            path.write_text(text, encoding="utf-8")
                            result = {"artifact": path.name, "created": True}
                        else:
                            result = orchestrator.execute_tool(name, dict(arguments), approved=approved)
                    except KeyError:
                        self._write_json(404, {"error": f"unknown tool: {name}"}, method="POST")
                        return
                    except PermissionError as exc:
                        self._write_json(403, {"error": str(exc), "approval_header": APPROVAL_HEADER}, method="POST")
                        return
                    except (RuntimeError, ValueError) as exc:
                        self._write_json(400, {"error": str(exc)}, method="POST")
                        return
                    self._write_json(200, {"tool": name, "result": result}, method="POST")
                    return

                self._write_json(404, {"error": "not found"}, method="POST")

        server = ThreadingHTTPServer((self.host, self.port), Handler)
        self._server = server
        return server

    def serve_forever(self) -> None:
        server = self._server or self.build_server()
        server.serve_forever(poll_interval=0.1)

    def shutdown(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
