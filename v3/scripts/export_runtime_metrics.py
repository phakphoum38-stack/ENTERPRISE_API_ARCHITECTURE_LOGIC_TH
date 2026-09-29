from __future__ import annotations

import argparse
from pathlib import Path
import sys

V3_ROOT = Path(__file__).resolve().parents[1]
if str(V3_ROOT) not in sys.path:
    sys.path.insert(0, str(V3_ROOT))

from research_os_v3.durable_events import DurableWorkflowEventStore


def prometheus_metrics(values: dict[str, int]) -> str:
    lines = [
        "# HELP research_os_workflow_events_total Number of durable workflow events.",
        "# TYPE research_os_workflow_events_total gauge",
        f"research_os_workflow_events_total {values.get('event_count', 0)}",
        "# HELP research_os_event_delivery_attempts_total Durable event delivery attempts.",
        "# TYPE research_os_event_delivery_attempts_total counter",
        f"research_os_event_delivery_attempts_total {values.get('delivery_attempts', 0)}",
    ]
    for status in ("claimed", "completed", "failed"):
        name = f"delivery_{status}"
        lines.append(f"research_os_event_delivery_status{{status=\"{status}\"}} {values.get(name, 0)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Export durable V3 event metrics.")
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--workflow-id")
    args = parser.parse_args()
    store = DurableWorkflowEventStore(args.events)
    print(prometheus_metrics(store.metrics(args.workflow_id)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
