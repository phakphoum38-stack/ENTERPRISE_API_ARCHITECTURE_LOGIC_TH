from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

V3_ROOT = Path(__file__).resolve().parents[1]
if str(V3_ROOT) not in sys.path:
    sys.path.insert(0, str(V3_ROOT))

from research_os_v3.durable_events import DurableWorkflowEventStore
from research_os_v3.queue import DurableTaskQueue


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish pending V3 queue outbox events.")
    parser.add_argument("--queue", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--correlation-id", required=True)
    parser.add_argument("--max-events", type=int, default=100)
    args = parser.parse_args()

    queue = DurableTaskQueue(args.queue)
    events = DurableWorkflowEventStore(args.events)
    result = queue.drain_outbox(
        events,
        workflow_id=args.workflow_id,
        correlation_id=args.correlation_id,
        max_events=args.max_events,
    )
    output = {"queue": str(args.queue), "events": str(args.events), **result, "metrics": events.metrics(args.workflow_id)}
    print(json.dumps(output, sort_keys=True))
    return 1 if result["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
