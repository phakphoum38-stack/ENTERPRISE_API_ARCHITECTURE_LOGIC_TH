from __future__ import annotations

import json
import sys
import threading
from pathlib import Path
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3.service import V3LocalService


def get_json(url: str) -> dict[str, object]:
    with urlopen(url, timeout=5.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def main() -> int:
    service = V3LocalService(host="127.0.0.1", port=0)
    server = service.build_server()
    host, port = server.server_address[:2]
    assert host == "127.0.0.1"

    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    try:
        health = get_json(f"{base}/health")
        master = get_json(f"{base}/v3/master?tasks=217")
        providers = get_json(f"{base}/v3/providers")

        assert health["status"] == "ok"
        assert health["version"] == "v3-clean"
        assert master["contract"] == "unified-master-orchestrator-v3-clean"
        assert master["scale"] == "6^6"
        assert master["maximum_leaf_capacity"] == 46656
        provider = providers["providers"][0]
        assert provider["secret_exposed"] is False

        print(json.dumps({"health": health, "master": master, "providers": providers}, indent=2, sort_keys=True))
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5.0)


if __name__ == "__main__":
    raise SystemExit(main())
