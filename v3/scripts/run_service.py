from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import DataLayout, V3LocalService


def main() -> int:
    host = os.environ.get("RESEARCH_OS_V3_HOST", "127.0.0.1")
    port = int(os.environ.get("RESEARCH_OS_V3_PORT", "8788"))
    layout = DataLayout.from_environment().ensure()
    audit_path = layout.logs / "http-audit.jsonl"
    service = V3LocalService(host=host, port=port, audit_path=audit_path)
    print(
        json.dumps(
            {
                "service": "research-os-v3-clean",
                "host": host,
                "port": port,
                "contract": "unified-master-orchestrator-v3-clean",
                "data_root": str(layout.root),
                "http_audit": str(audit_path),
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
