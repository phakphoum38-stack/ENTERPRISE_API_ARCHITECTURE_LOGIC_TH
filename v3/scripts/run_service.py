from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import (
    DataLayout,
    MockProvider,
    OpenAICompatibleProvider,
    ProviderRegistry,
    UnifiedMasterOrchestrator,
    V3LocalService,
    default_secret_source,
)


def build_orchestrator() -> UnifiedMasterOrchestrator:
    secret_source = default_secret_source()
    credential_names = (
        "RESEARCH_OS_OPENAI_API_KEY",
        "OPENAI_API_KEY",
    )
    credential_name = next(
        (name for name in credential_names if secret_source.get(name)),
        credential_names[0],
    )
    openai = OpenAICompatibleProvider(
        base_url=os.environ.get(
            "RESEARCH_OS_OPENAI_ENDPOINT",
            "https://api.openai.com/v1",
        ),
        model=os.environ.get("RESEARCH_OS_OPENAI_MODEL", "gpt-5"),
        api_key_env=credential_name,
        secret_source=secret_source,
        timeout=float(os.environ.get("RESEARCH_OS_PROVIDER_TIMEOUT", "30")),
    )
    # Prefer the real provider when its credential exists. Mock remains a safe
    # offline fallback so the local service and GUI can still boot deterministically.
    providers = ProviderRegistry([openai, MockProvider()])
    return UnifiedMasterOrchestrator(providers=providers)


def main() -> int:
    host = os.environ.get("RESEARCH_OS_V3_HOST", "127.0.0.1")
    port = int(os.environ.get("RESEARCH_OS_V3_PORT", "8788"))
    layout = DataLayout.from_environment().ensure()
    audit_path = layout.logs / "http-audit.jsonl"
    service = V3LocalService(
        host=host,
        port=port,
        audit_path=audit_path,
        orchestrator=build_orchestrator(),
    )
    print(
        json.dumps(
            {
                "service": "research-os-v3-full-10x10",
                "host": host,
                "port": port,
                "contract": "unified-master-orchestrator-v3-full",
                "data_root": str(layout.root),
                "http_audit": str(audit_path),
                "provider_policy": "existing-key-first-with-mock-fallback",
                "maximum_scale": "10^10",
                "maximum_logical_capacity": 10_000_000_000,
            },
            sort_keys=True,
        ),
        flush=True,
    )
    try:
        service.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        service.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
