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
    UnifiedMasterOrchestrator,
    V3LocalService,
    runtime_provider_registry,
)


def main() -> int:
    host = os.environ.get("RESEARCH_OS_V3_HOST", "127.0.0.1")
    port = int(os.environ.get("RESEARCH_OS_V3_PORT", "8788"))
    layout = DataLayout.from_environment().ensure()
    audit_path = layout.logs / "http-audit.jsonl"

    providers = runtime_provider_registry()
    orchestrator = UnifiedMasterOrchestrator(providers=providers)
    service = V3LocalService(
        host=host,
        port=port,
        audit_path=audit_path,
        data_layout=layout,
        orchestrator=orchestrator,
    )
    safe_provider_statuses = [status.to_safe_dict() for status in providers.statuses()]
    print(
        json.dumps(
            {
                "service": "research-os-v3-unified",
                "host": host,
                "port": port,
                "contract": orchestrator.contract,
                "maximum_scale": "10^10",
                "data_root": str(layout.root),
                "http_audit": str(audit_path),
                "provider_mode": os.environ.get("RESEARCH_OS_PROVIDER", "auto"),
                "providers": safe_provider_statuses,
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
