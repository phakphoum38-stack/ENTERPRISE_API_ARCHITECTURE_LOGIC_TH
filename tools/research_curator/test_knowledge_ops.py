import tempfile
import unittest
from pathlib import Path

import knowledge_ops


ARTIFACT = """---
artifact_id: \"{artifact_id}\"
title: \"{title}\"
status: \"observed\"
relationships: [{relationships}]
---

# {artifact_id} — {title}

## Discoveries

{discoveries}

## Hypotheses

- ยังไม่มีรายการ

## Open Questions

- ยังไม่มีรายการ

## Decisions

- ยังไม่มีรายการ

## Next Actions

- ยังไม่มีรายการ

## Evidence

- ยังไม่มีรายการ

## Relationships

{relationship_lines}
"""


class KnowledgeOpsTests(unittest.TestCase):
    def write_artifact(self, root: Path, artifact_id: str, discoveries: list[str], relationships=None) -> Path:
        relationships = relationships or []
        path = root / f"{artifact_id}.md"
        path.write_text(
            ARTIFACT.format(
                artifact_id=artifact_id,
                title=artifact_id,
                relationships=", ".join(f'\"{kind}:{target}\"' for kind, target in relationships),
                discoveries="\n".join(f"- {item}" for item in discoveries),
                relationship_lines="\n".join(f"- `{kind}` → `{target}`" for kind, target in relationships) or "- ยังไม่มีรายการ",
            ),
            encoding="utf-8",
        )
        return path

    def test_diff_detects_added_and_removed_items(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = knowledge_ops.load_artifact(self.write_artifact(root, "RES-OLD", ["A", "B"]))
            new = knowledge_ops.load_artifact(self.write_artifact(root, "RES-NEW", ["B", "C"]))
            report = knowledge_ops.render_diff(old, new)
            self.assertIn("- C", report)
            self.assertIn("- A", report)
            self.assertIn("Total added: 1", report)
            self.assertIn("Total removed: 1", report)

    def test_graph_exports_relationship(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_artifact(root, "RES-A", ["A"], [("supports", "RES-B")])
            self.write_artifact(root, "RES-B", ["B"])
            payload = knowledge_ops.graph_payload(knowledge_ops.load_all(root))
            self.assertEqual(2, len(payload["nodes"]))
            self.assertEqual("supports", payload["edges"][0]["relation"])
            self.assertEqual([], payload["external_targets"])

    def test_graph_marks_and_renders_external_targets(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.write_artifact(root, "RES-A", ["A"], [("relates_to", "EXT-001")])
            payload = knowledge_ops.graph_payload(knowledge_ops.load_all(root))
            diagram = knowledge_ops.render_mermaid(payload)
            self.assertEqual(["EXT-001"], payload["external_targets"])
            self.assertIn("N_EXT_001", diagram)
            self.assertIn("relates_to", diagram)


if __name__ == "__main__":
    unittest.main()
