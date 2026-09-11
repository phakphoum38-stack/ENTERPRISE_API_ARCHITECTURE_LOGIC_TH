import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "owner_special" / "team_center_contract.json"


def test_owner_service_contract_matches_supported_runtime_topology():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    services = contract["owner"]["services"]
    boundaries = contract["service_boundaries"]

    assert services == [8787, 8788, 8790]
    assert set(boundaries) == {"8787", "8788", "8790"}
    assert boundaries == {
        "8787": "workspace",
        "8788": "team-engineering",
        "8790": "friend-internal",
    }
    assert 8789 not in services
    assert "8789" not in boundaries


def test_known_runtime_sources_are_bound_to_declared_ports():
    v3_launcher = ROOT / "v3" / "scripts" / "run_service.py"
    friend_launcher = ROOT / "owner_special" / "scripts" / "run_friend_service.py"
    flutter_readme = ROOT / "tools" / "research_os_api" / "README.md"

    assert '"8788"' in v3_launcher.read_text(encoding="utf-8")
    assert "8790" in friend_launcher.read_text(encoding="utf-8")
    assert "127.0.0.1:8787" in flutter_readme.read_text(encoding="utf-8")
