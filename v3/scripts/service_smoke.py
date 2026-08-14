from __future__ import annotations

import json
import sys
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import DataLayout, UserContext
from research_os_v3.service import PROFILE_HEADER, USER_HEADER, V3LocalService


def get_json(
    url: str,
    *,
    user_id: str | None = None,
    profile_id: str = "default",
) -> dict[str, object]:
    request = Request(url)
    if user_id is not None:
        request.add_header(USER_HEADER, user_id)
        request.add_header(PROFILE_HEADER, profile_id)
    with urlopen(request, timeout=5.0) as response:
        payload = json.loads(response.read().decode("utf-8"))
    assert isinstance(payload, dict)
    return payload


def post_json(
    url: str,
    payload: dict[str, object],
    *,
    user_id: str,
    profile_id: str = "default",
) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            USER_HEADER: user_id,
            PROFILE_HEADER: profile_id,
        },
    )
    with urlopen(request, timeout=5.0) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    assert isinstance(decoded, dict)
    return decoded


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="research-os-v3-service-") as temporary:
        root = Path(temporary)
        audit_path = root / "http-audit.jsonl"
        data_layout = DataLayout(root / "data").ensure()
        service = V3LocalService(
            host="127.0.0.1",
            port=0,
            audit_path=audit_path,
            data_layout=data_layout,
        )
        server = service.build_server()
        host, port = server.server_address[:2]
        assert host == "127.0.0.1"

        thread = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.05},
            daemon=True,
        )
        thread.start()
        base = f"http://127.0.0.1:{port}"

        try:
            health = get_json(f"{base}/health")
            master = get_json(f"{base}/v3/master?tasks=217")
            maximum = get_json(f"{base}/v3/master?tasks=46657")
            providers = get_json(f"{base}/v3/providers")
            skills = get_json(f"{base}/v3/skills")
            tools = get_json(f"{base}/v3/tools")
            agents = get_json(f"{base}/v3/agents")
            alice = get_json(f"{base}/v3/user", user_id="alice")
            bob = get_json(f"{base}/v3/user", user_id="bob")

            assert health["status"] == "ok"
            assert health["version"] == "v3.2-unified-full-10x10"
            assert health["maximum_scale"] == "10^10"
            assert health["maximum_logical_capacity"] == 10_000_000_000
            assert health["authority_contract"] == "unified-master-orchestrator-v3-full"
            assert master["contract"] == "unified-master-orchestrator-v3-clean"
            assert master["authority_contract"] == "unified-master-orchestrator-v3-full"
            assert master["scale"] == "3^6"
            assert master["maximum_leaf_capacity"] == 729
            assert maximum["scale"] == "10^10"
            assert maximum["maximum_leaf_capacity"] == 10_000_000_000
            assert providers["providers"]
            assert providers["providers"][0]["secret_exposed"] is False
            assert skills["skills"]
            assert skills["single_authority"] == "unified-master-orchestrator-v3-full"
            assert tools["tools"]
            assert agents["agents"]

            assert alice["isolated"] is True
            assert bob["isolated"] is True
            assert alice["scope"] == "users/alice/profiles/default"
            assert bob["scope"] == "users/bob/profiles/default"
            assert alice["scope"] != bob["scope"]

            alice_root = data_layout.for_user(UserContext("alice")).root
            bob_root = data_layout.for_user(UserContext("bob")).root
            assert alice_root.is_dir()
            assert bob_root.is_dir()
            assert alice_root != bob_root

            created = post_json(
                f"{base}/v3/memory",
                {"text": "Research OS uses 10^10 logical capacity"},
                user_id="alice",
            )
            assert created["memory"]["text"] == "Research OS uses 10^10 logical capacity"
            memory = get_json(
                f"{base}/v3/memory?q={quote('logical capacity')}",
                user_id="alice",
            )
            assert len(memory["memory"]) == 1
            chat = post_json(
                f"{base}/v3/chat",
                {"message": "logical capacity"},
                user_id="alice",
            )
            assert chat["contract"] == "research-os-v3-chat-v1"
            assert chat["provider"] == "mock"
            assert chat["memory_hits"]

            try:
                get_json(f"{base}/v3/user")
            except HTTPError as exc:
                assert exc.code == 400
            else:
                raise AssertionError("/v3/user accepted a missing user context")

            try:
                get_json(f"{base}/v3/user", user_id="../bob")
            except HTTPError as exc:
                assert exc.code == 400
            else:
                raise AssertionError("/v3/user accepted an unsafe user id")

            records = [
                json.loads(line)
                for line in audit_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            assert {record["path"] for record in records} >= {
                "/health",
                "/v3/master",
                "/v3/providers",
                "/v3/skills",
                "/v3/tools",
                "/v3/agents",
                "/v3/user",
                "/v3/memory",
                "/v3/chat",
            }
            for record in records:
                assert set(record) == {"timestamp", "method", "path", "status"}
                assert record["method"] in {"GET", "POST"}
                assert "?" not in record["path"]
                assert record["status"] in {200, 201, 400}

            print(
                json.dumps(
                    {
                        "health": health,
                        "master": master,
                        "maximum": maximum,
                        "providers": providers,
                        "skills_count": len(skills["skills"]),
                        "tools_count": len(tools["tools"]),
                        "agents_count": len(agents["agents"]),
                        "cross_user_isolation": True,
                        "chat_memory_flow": True,
                        "audit_records": records,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5.0)


if __name__ == "__main__":
    raise SystemExit(main())
