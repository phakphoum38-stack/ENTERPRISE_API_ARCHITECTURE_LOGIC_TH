from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
INVARIANTS = ROOT / "current" / "ARCHITECTURE_INVARIANTS.md"
MATRIX = ROOT / "current" / "ARCHITECTURE_ENFORCEMENT_MATRIX.yml"

ALLOWED_STATUSES = {"implemented", "partial", "not-yet-enforced"}


def main() -> None:
    assert INVARIANTS.is_file(), "canonical architecture invariant document is missing"
    assert MATRIX.is_file(), "architecture enforcement matrix is missing"

    text = INVARIANTS.read_text(encoding="utf-8")
    matrix = yaml.safe_load(MATRIX.read_text(encoding="utf-8")) or {}
    entries = matrix.get("invariants") or []
    assert len(entries) == 20, f"expected 20 invariant entries, got {len(entries)}"

    ids = [entry.get("id") for entry in entries]
    expected = [f"INV-{index:03d}" for index in range(1, 21)]
    assert ids == expected, "matrix invariant IDs must remain canonical and ordered"

    for entry in entries:
        invariant_id = entry.get("id")
        status = entry.get("status")
        mechanism = entry.get("mechanism")
        evidence = entry.get("evidence")
        assert status in ALLOWED_STATUSES, f"{invariant_id}: invalid status {status!r}"
        assert mechanism, f"{invariant_id}: enforcement mechanism is required"
        assert evidence, f"{invariant_id}: evidence reference is required"
        assert invariant_id in text, f"{invariant_id}: missing from canonical invariant document"
        if status == "not-yet-enforced":
            assert "planned" in evidence.lower(), (
                f"{invariant_id}: not-yet-enforced entries must name an explicit plan"
            )

    rules = matrix.get("rules") or []
    required_rules = {
        "every_invariant_has_one_status",
        "every_invariant_has_one_mechanism",
        "every_invariant_has_one_evidence_reference",
        "matrix_does_not_replace_runtime_or_ci_evidence",
    }
    present_rules = {next(iter(rule)) for rule in rules if isinstance(rule, dict) and len(rule) == 1}
    assert required_rules <= present_rules, "matrix governance rules are incomplete"

    print("Architecture invariant enforcement matrix validation passed: 20 invariants mapped.")


if __name__ == "__main__":
    main()
