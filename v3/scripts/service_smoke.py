from __future__ import annotations

import json
import os
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

from research_os_v3 import DataLayout, UserContext, V3LocalService


def get_json(url: str, *, user_id: str | None = None) -> dict[str, object]:
    request = urllib.request.Request(url)
    if user_id is not None:
        request.add_header("X-Research-OS-User", user_id)
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        data_layout = DataLayout(Path(tmp) / "data").ensure()
        service = V3LocalService(
            host="127.0.0.1",
            port=0,
            data_layout=data_layout,
        )
        server = service.build_server()
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"

        try:
            health = get_json(f"{base}/health")
            master = get_json(f"{base}/v3/master?tasks=217")
            providers = get_json(f"{base}/v3/providers")
            alice = get_json(f"{base}/v3/user", user_id="alice")
            bob = get_json(f"{base}/v3/user", user_id="bob")

            assert health["status"] == "ok"
            assert health["version"] == "v3-full-10x10"
            assert master["contract"] == "unified-master-orchestrator-v3-full"
            assert master["scale"] == "6^6"
            assert master["maximum_leaf_capacity"] == 46656
            assert master["system_maximum_scale"] == "10^10"
            assert master["system_maximum_logical_capacity"] == 10000000000
            provider = providers["providers"][0]
            assert provider["secret_exposed"] is False

            assert alice["isolated"] is True
            assert bob["isolated"] is True
            assert alice["scope"] == "users/alice/profiles/default"
            assert bob["scope"] == "users/bob/profiles/default"
            assert alice["scope"] != bob["scope"]

            alice_root = data_layout.for_user(UserContext("alice")).root
            bob_root = data_layout.for_user(UserContext("bob")).root
            assert alice_root != bob_root
            assert alice_root.exists() and bob_root.exists()

            try:
                get_json(f"{base}/v3/user")
            except urllib.error.HTTPError as exc:
                assert exc.code == 400
            else:
                raise AssertionError("missing user context must be rejected")

            print("SERVICE_SMOKE=PASS")
            return 0
        finally:
            service.shutdown()
            thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
