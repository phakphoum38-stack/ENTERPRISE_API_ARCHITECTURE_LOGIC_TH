from __future__ import annotations

import copy
import json
import re
from typing import Any, Mapping


class MissionControlBuildIdentityError(ValueError):
    """Raised when canonical build/provenance evidence cannot be projected safely."""


class MissionControlBuildIdentityProjection:
    """Read-only projection of canonical build identity and installed provenance evidence."""

    SCHEMA = "research-os-mission-control-build-identity/v1"
    MAX_STRING = 2048
    MAX_BYTES = 16 * 1024
    BLOCKED = re.compile(
        r"(?:bearer\s+|api[_-]?key|private.?key|password|credential|secret|token|"
        r"javascript:|subprocess|os\.system|child_process|powershell|cmd\.exe|bash\s+-c)",
        re.I,
    )
    EXPOSED_FIELDS = (
        "gate",
        "passed",
        "file_name",
        "sha256",
        "product_name",
        "internal_name",
        "original_filename",
        "file_description",
        "company_name",
        "owner_edition",
        "owner_only",
        "manifest_version",
        "commit",
    )

    def snapshot(
        self,
        *,
        owner_id: str,
        build_identity: Mapping[str, Any] | None,
        installed_provenance: Mapping[str, Any] | None,
        expected_commit: str | None = None,
    ) -> dict[str, object]:
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise MissionControlBuildIdentityError("owner_id is required")
        if len(owner_id) > self.MAX_STRING or self.BLOCKED.search(owner_id):
            raise MissionControlBuildIdentityError("owner_id is unsafe")

        build = self._copy_mapping(build_identity)
        installed = self._copy_mapping(installed_provenance)
        status, reason = self._classify(build, installed, expected_commit)

        result: dict[str, object] = {
            "schema": self.SCHEMA,
            "owner_id": owner_id,
            "read_only": True,
            "source_authority": "canonical-build-identity-and-installed-provenance-gates",
            "status": status,
            "reason": reason,
            "identity": self._identity(build, installed, status),
        }
        self._validate(result)
        return copy.deepcopy(result)

    def _copy_mapping(self, value: Mapping[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return None
        if not isinstance(value, Mapping):
            raise MissionControlBuildIdentityError("canonical evidence must be an object")
        return copy.deepcopy(dict(value))

    def _classify(
        self,
        build: dict[str, Any] | None,
        installed: dict[str, Any] | None,
        expected_commit: str | None,
    ) -> tuple[str, str]:
        if build is None:
            return "PENDING", "build identity evidence is missing"
        if installed is None:
            return "PENDING", "installed release provenance evidence is missing"
        if build.get("passed") is not True:
            return "INVALID", "build identity gate is not passed"
        if installed.get("passed") is not True:
            return "INVALID", "installed provenance gate is not passed"
        if build.get("owner_edition") != "owner-special" or build.get("owner_only") is not True:
            return "CONFLICT", "build identity is not canonical owner-special evidence"
        if installed.get("owner_edition") not in (None, "owner-special"):
            return "CONFLICT", "installed provenance owner edition conflicts"

        build_commit = self._normalized_sha(build.get("commit"))
        installed_commit = self._normalized_sha(installed.get("commit"))
        expected = self._normalized_sha(expected_commit)
        if not build_commit or not installed_commit:
            return "PENDING", "canonical commit provenance is incomplete"
        if build_commit != installed_commit:
            return "CONFLICT", "build and installed commits differ"
        if expected and build_commit != expected:
            return "STALE", "canonical evidence does not match the expected source commit"

        build_sha = self._normalized_sha(build.get("sha256"))
        installed_sha = self._normalized_sha(installed.get("sha256"))
        if not build_sha or not installed_sha:
            return "PENDING", "canonical executable SHA256 provenance is incomplete"
        if build_sha != installed_sha:
            return "CONFLICT", "build and installed executable SHA256 values differ"
        if build.get("file_name") != "research_os_owner_special.exe":
            return "CONFLICT", "canonical build identity filename is unexpected"
        return "VERIFIED", "canonical build identity and installed provenance agree"

    @staticmethod
    def _normalized_sha(value: Any) -> str | None:
        if not isinstance(value, str):
            return None
        value = value.strip().lower()
        return value or None

    def _identity(
        self,
        build: dict[str, Any] | None,
        installed: dict[str, Any] | None,
        status: str,
    ) -> dict[str, object]:
        source = build or installed or {}
        identity: dict[str, object] = {"status": status}
        for field in self.EXPOSED_FIELDS:
            value = source.get(field)
            if isinstance(value, (str, bool)):
                identity[field] = value
        if installed is not None:
            installed_commit = installed.get("commit")
            if isinstance(installed_commit, str):
                identity["installed_commit"] = installed_commit
            installed_sha = installed.get("sha256")
            if isinstance(installed_sha, str):
                identity["installed_sha256"] = installed_sha
        return identity

    def _validate(self, payload: dict[str, object]) -> None:
        if payload["read_only"] is not True:
            raise MissionControlBuildIdentityError("projection must remain read-only")
        identity = payload["identity"]
        if not isinstance(identity, dict):
            raise MissionControlBuildIdentityError("identity projection must be an object")
        for value in self._walk_values(payload):
            if isinstance(value, str) and (len(value) > self.MAX_STRING or self.BLOCKED.search(value)):
                raise MissionControlBuildIdentityError("blocked or oversized identity value")
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlBuildIdentityError("build identity projection exceeds byte bound")

    def _walk_values(self, value: Any):
        if isinstance(value, Mapping):
            for item in value.values():
                yield from self._walk_values(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                yield from self._walk_values(item)
        else:
            yield value
