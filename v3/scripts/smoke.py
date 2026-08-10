from __future__ import annotations

import json

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
