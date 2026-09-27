"""SDK generation metadata derived from the canonical runtime OpenAPI contract."""
from __future__ import annotations

from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

def build_sdk_metadata() -> dict[str, Any]:
    source = ROOT / "tools/research_os_api/openapi.yaml"
    text = source.read_text(encoding="utf-8")
    paths = []
    for line in text.splitlines():
        match = re.match(r"^  (/[^:]+):$", line)
        if match:
            paths.append(match.group(1))
    return {
        "source": "tools/research_os_api/openapi.yaml",
        "source_version": "2.0.0-rc.1",
        "languages": ["python", "typescript", "dart"],
        "paths": sorted(set(paths)),
        "generation_mode": "metadata_only",
        "second_api_definition": False,
        "authority": "NONE",
    }
