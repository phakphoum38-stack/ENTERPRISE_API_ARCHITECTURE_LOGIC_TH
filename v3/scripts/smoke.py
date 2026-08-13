from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import UnifiedMasterOrchestrator, Workload, health_contract, master_contract, providers_contract


def main() -> int:
    master = UnifiedMasterOrchestrator()
    decision, plan = master.plan(Workload(estimated_leaf_tasks=217))
    maximum, _ = master.plan(Workload(estimated_leaf_tasks=46657))
    payload = {
        "health": health_contract(),
        "master": master_contract(decision),
        "maximum": master_contract(maximum),
        "providers": providers_contract(master.providers),
        "factory_stages": list(plan.stage_order),
        "skills": [skill.name for skill in master.skills.list()],
        "tools": [tool.name for tool in master.tools.list()],
        "agents": [agent.name for agent in master.agents.list()],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    assert payload["health"]["maximum_scale"] == "10^10"
    assert payload["health"]["maximum_logical_capacity"] == 10_000_000_000
    assert payload["master"]["scale"] == "3^6"
    assert payload["master"]["maximum_leaf_capacity"] == 729
    assert payload["maximum"]["scale"] == "10^10"
    assert payload["maximum"]["maximum_leaf_capacity"] == 10_000_000_000
    assert payload["providers"]["providers"][0]["secret_exposed"] is False
    assert "chat-runtime" in payload["skills"]
    assert "echo" in payload["tools"]
    assert "architect" in payload["agents"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
