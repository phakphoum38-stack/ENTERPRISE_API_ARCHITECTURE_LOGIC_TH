from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import UnifiedMasterOrchestrator, Workload, master_contract, providers_contract


def main() -> int:
    master = UnifiedMasterOrchestrator()
    decision, plan = master.plan(Workload(estimated_leaf_tasks=217))
    payload = {
        "master": master_contract(decision),
        "providers": providers_contract(master.providers),
        "factory_stages": [stage.name for stage in plan.stages],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))

    assert payload["master"]["scale"] == "6^6"
    assert payload["master"]["maximum_leaf_capacity"] == 46656
    assert payload["providers"]["providers"][0]["secret_exposed"] is False
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
