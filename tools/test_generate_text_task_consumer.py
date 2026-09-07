from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from generate_text_task_consumer import (
    GenerateTextTaskConsumer,
    TextTaskError,
    build_dispatch_plan,
)


SCHEMA = "research-os-generate-text-task/v1"


def write_task(root: Path, name: str, **overrides: object) -> Path:
    payload: dict[str, object] = {
        "schema": SCHEMA,
        "task_id": "task-001",
        "owner_id": "owner",
        "text": "ตรวจสอบ build identity และสร้าง evidence",
    }
    payload.update(overrides)
    path = root / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


class GenerateTextTaskConsumerTests(unittest.TestCase):
    def test_consumes_valid_task_and_builds_deferred_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = GenerateTextTaskConsumer(root).consume_file(write_task(root, "task.json"))
            plan = build_dispatch_plan(task)
            self.assertEqual(task.owner_id, "owner")
            self.assertEqual(plan["dispatch"], "deferred")
            self.assertEqual(plan["intent"]["intent"], "generate.text")
            self.assertEqual(plan["execution"], "not-run")
            self.assertTrue(task.source_sha256)

    def test_rejects_wrong_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_task(root, "task.json", schema="wrong/v9")
            with self.assertRaises(TextTaskError):
                GenerateTextTaskConsumer(root).consume_file(path)

    def test_rejects_unknown_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_task(root, "task.json", callback="execute()")
            with self.assertRaises(TextTaskError):
                GenerateTextTaskConsumer(root).consume_file(path)

    def test_rejects_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(TextTaskError):
                GenerateTextTaskConsumer(root).consume_file("../task.json")

    def test_rejects_oversized_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_task(root, "task.json", text="x" * 40000)
            with self.assertRaises(TextTaskError):
                GenerateTextTaskConsumer(root).consume_file(path)

    def test_consume_all_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_task(root, "b.json", task_id="b")
            write_task(root, "a.json", task_id="a")
            tasks = GenerateTextTaskConsumer(root).consume_all()
            self.assertEqual([task.task_id for task in tasks], ["a", "b"])

    def test_consumer_does_not_dispatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = GenerateTextTaskConsumer(root).consume_file(write_task(root, "task.json"))
            plan = build_dispatch_plan(task)
            self.assertEqual(plan["dispatch"], "deferred")
            self.assertEqual(plan["execution"], "not-run")


if __name__ == "__main__":
    unittest.main()
