from __future__ import annotations

import json
import re
import time
from uuid import uuid4

from .skill_runtime_types import SkillRuntimeContext


class LegacyOpsSkillHandlers:
    def _cloud_conversation_sync(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        root = context.user_data_root / "cloud-sync"
        root.mkdir(parents=True, exist_ok=True)
        action = str(args.get("action", "status")).strip().lower()
        if action == "status":
            items = sorted(path.name for path in root.glob("*.json"))
            return {"queued": len(items), "items": items[-20:], "external_upload": False}
        if action != "enqueue":
            raise ValueError("unsupported cloud sync action")
        self._require_approval(context, "cloud-sync:enqueue")
        payload = {"id": uuid4().hex, "text": str(args.get("text", text)), "user_id": context.user_id, "profile_id": context.profile_id}
        self._atomic_json(root / f"{payload['id']}.json", payload)
        return {"queued": True, "id": payload["id"], "external_upload": False}

    @staticmethod
    def _orchestration_observability(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        root = context.user_data_root / "orchestration"
        runs: list[dict[str, object]] = []
        if root.exists():
            for path in sorted(root.glob("*.json"))[-50:]:
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    runs.append({"run_id": raw.get("run_id"), "status": raw.get("status"), "attempt": raw.get("attempt", 1)})
                except (OSError, json.JSONDecodeError):
                    continue
        return {"runs": runs, "count": len(runs)}

    @staticmethod
    def _completion_crew(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        checks = args.get("checks", {})
        if not isinstance(checks, dict):
            raise ValueError("checks must be an object")
        normalized = {str(key): bool(value) for key, value in checks.items()}
        missing = sorted(key for key, value in normalized.items() if not value)
        return {"complete": bool(normalized) and not missing, "checks": normalized, "missing": missing}

    @staticmethod
    def _quality_gate(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        checks = args.get("checks", {})
        if not isinstance(checks, dict):
            raise ValueError("checks must be an object")
        normalized = {str(key): bool(value) for key, value in checks.items()}
        failed = sorted(key for key, value in normalized.items() if not value)
        return {"passed": bool(normalized) and not failed, "failed": failed, "checks": normalized}

    @staticmethod
    def _file_audit(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        raw = str(args.get("path", ".")).strip() or "."
        root = context.repository_root.resolve()
        target = (root / raw).resolve()
        if target != root and root not in target.parents:
            raise ValueError("audit path escaped repository root")
        files = [target] if target.is_file() else [path for path in target.rglob("*") if path.is_file()]
        files = files[:466]
        findings: list[dict[str, object]] = []
        for path in files:
            try:
                data = path.read_bytes()[:262144]
            except OSError:
                continue
            text_data = data.decode("utf-8", errors="ignore")
            if re.search(r"(?i)(password\s*=|api[_-]?key\s*=|secret\s*=)", text_data):
                findings.append({"path": path.relative_to(root).as_posix(), "kind": "possible-secret-assignment"})
        return {"files_scanned": len(files), "findings": findings, "logical_rule": "6^6", "passed": not findings}

    @staticmethod
    def _developer_identity(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        principal = str(args.get("principal", "")).strip()
        nonce = str(args.get("nonce", "")).strip()
        signature = str(args.get("signature", "")).strip()
        try:
            issued_at = int(args.get("timestamp", 0))
        except (TypeError, ValueError):
            issued_at = 0
        complete = bool(principal and nonce and signature and issued_at)
        fresh = complete and abs(int(time.time()) - issued_at) <= 300
        return {
            "principal": principal or None,
            "assertion_well_formed": complete,
            "timestamp_fresh": fresh,
            "cryptographic_verification": "developer-access-boundary",
            "credential_access": False,
        }

    @staticmethod
    def _provider_readiness(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        if context.provider_snapshot is None:
            raise RuntimeError("provider status runtime is unavailable")
        providers = context.provider_snapshot()
        return {"providers": providers, "ready_count": sum(1 for item in providers if bool(item.get("ready"))), "secret_exposed": False}

    @staticmethod
    def _owner_policy(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        claimed = str(args.get("owner_id", context.user_id)).strip()
        if claimed != context.user_id:
            raise PermissionError("owner policy rejected mismatched owner_id")
        write_requested = bool(args.get("write", False))
        if write_requested and not context.approved:
            raise PermissionError("owner policy requires approval for write")
        return {"authorized": True, "owner_id": claimed, "write": write_requested}

    def _evidence_recording(self, name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        self._require_approval(context, "evidence-recording")
        event = str(args.get("event", "skill-evidence")).strip() or "skill-evidence"
        data = args.get("data", {"text": text})
        if not isinstance(data, dict):
            raise ValueError("evidence data must be an object")
        clean = self._redact_sensitive(data)
        record = {"evidence_id": uuid4().hex, "event": event, "user_id": context.user_id, "profile_id": context.profile_id, "data": clean}
        path = context.user_data_root / "evidence" / "skill-events.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return {"evidence_id": record["evidence_id"], "recorded": True}

    @staticmethod
    def _redact_sensitive(value: object) -> object:
        if isinstance(value, dict):
            redacted: dict[str, object] = {}
            for key, item in value.items():
                normalized = str(key).lower().replace("-", "_")
                if any(token in normalized for token in ("secret", "token", "password", "api_key", "credential")):
                    redacted[str(key)] = "[REDACTED]"
                else:
                    redacted[str(key)] = LegacyOpsSkillHandlers._redact_sensitive(item)
            return redacted
        if isinstance(value, list):
            return [LegacyOpsSkillHandlers._redact_sensitive(item) for item in value]
        return value

    @staticmethod
    def _v3_bridge(name: str, text: str, args: dict[str, object], context: SkillRuntimeContext) -> dict[str, object]:
        return {
            "available": True,
            "authority": "unified-master-orchestrator-v3-full",
            "bridge_mode": "native-adapter",
            "legacy_master_started": False,
        }
