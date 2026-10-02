from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.research_os_resource_change_coalescer import (
    ResourceChangeCoalescer,
)
from tools.research_os_resource_change_event import (
    ResourceChangeEvent,
)
from tools.research_os_resource_change_queue import (
    ResourceChangeQueue,
)
from tools.research_os_resource_drift import (
    compare_resource_changes,
)
from tools.research_os_resource_incremental_processor import (
    ResourceIncrementalProcessor,
)
from tools.research_os_resource_instance import (
    ResourceInstance,
)


class ResourceIncrementalPipelineTests(unittest.TestCase):

    def test_modify_burst_flows_event_to_drift_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "a.py"
            target.write_bytes(b"changed")

            baseline_instance = ResourceInstance.create(
                "R1",
                str(target),
                b"original",
            )

            queue = ResourceChangeQueue()

            queue.extend(
                [
                    ResourceChangeEvent(
                        str(target),
                        "MODIFY",
                        "flutter",
                    ),
                    ResourceChangeEvent(
                        str(target),
                        "MODIFY",
                        "flutter",
                    ),
                    ResourceChangeEvent(
                        str(target),
                        "MODIFY",
                        "flutter",
                    ),
                ]
            )

            queued = queue.drain()

            coalesced = ResourceChangeCoalescer().coalesce(
                queued
            )

            self.assertEqual(len(queued), 1)
            self.assertEqual(len(coalesced), 1)
            self.assertEqual(
                coalesced[0].operation,
                "MODIFY",
            )

            processor = ResourceIncrementalProcessor(
                {
                    str(target): "R1",
                }
            )

            changes = processor.process(coalesced)

            self.assertEqual(len(changes), 1)
            self.assertEqual(
                changes[0]["resource_id"],
                "R1",
            )

            drift = compare_resource_changes(
                {"R1": baseline_instance},
                changes,
            )

            self.assertEqual(len(drift), 1)
            self.assertEqual(
                drift[0].resource_id,
                "R1",
            )
            self.assertEqual(
                drift[0].state,
                "CONTENT_DRIFT",
            )

    def test_multiple_resources_remain_incremental(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            first = root / "a.py"
            second = root / "b.py"

            first.write_bytes(b"changed-a")
            second.write_bytes(b"changed-b")

            baseline = {
                "R1": ResourceInstance.create(
                    "R1",
                    str(first),
                    b"old-a",
                ),
                "R2": ResourceInstance.create(
                    "R2",
                    str(second),
                    b"old-b",
                ),
                "R3": ResourceInstance.create(
                    "R3",
                    str(root / "untouched.py"),
                    b"untouched",
                ),
            }

            queue = ResourceChangeQueue()

            queue.extend(
                [
                    ResourceChangeEvent(
                        str(second),
                        "MODIFY",
                        "flutter",
                    ),
                    ResourceChangeEvent(
                        str(first),
                        "MODIFY",
                        "flutter",
                    ),
                    ResourceChangeEvent(
                        str(second),
                        "MODIFY",
                        "flutter",
                    ),
                ]
            )

            coalesced = ResourceChangeCoalescer().coalesce(
                queue.drain()
            )

            self.assertEqual(len(coalesced), 2)

            processor = ResourceIncrementalProcessor(
                {
                    str(first): "R1",
                    str(second): "R2",
                    str(root / "untouched.py"): "R3",
                }
            )

            changes = processor.process(coalesced)

            drift = compare_resource_changes(
                baseline,
                changes,
            )

            self.assertEqual(
                [item.resource_id for item in drift],
                ["R1", "R2"],
            )
            self.assertEqual(
                [item.state for item in drift],
                [
                    "CONTENT_DRIFT",
                    "CONTENT_DRIFT",
                ],
            )

            self.assertNotIn(
                "R3",
                [item.resource_id for item in drift],
            )

    def test_create_modify_delete_cancels_before_processing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "new.py"

            queue = ResourceChangeQueue()

            queue.push(
                ResourceChangeEvent(
                    str(target),
                    "CREATE",
                    "flutter",
                )
            )
            queue.push(
                ResourceChangeEvent(
                    str(target),
                    "MODIFY",
                    "flutter",
                )
            )
            queue.push(
                ResourceChangeEvent(
                    str(target),
                    "DELETE",
                    "flutter",
                )
            )

            coalesced = ResourceChangeCoalescer().coalesce(
                queue.drain()
            )

            self.assertEqual(coalesced, [])

            processor = ResourceIncrementalProcessor({})

            changes = processor.process(coalesced)

            self.assertEqual(changes, [])

            drift = compare_resource_changes(
                {},
                changes,
            )

            self.assertEqual(drift, [])


if __name__ == "__main__":
    unittest.main()
