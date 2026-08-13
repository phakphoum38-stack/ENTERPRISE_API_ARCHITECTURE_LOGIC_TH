from __future__ import annotations

import argparse
import re
from pathlib import Path

# Generated UI uses deliberately simple single-line control flow. Repair only
# standalone `if (...) statement;` lines. Conditions in the generated template
# do not contain nested parentheses, so stop at the first closing parenthesis.
# This is intentionally stricter than a greedy regex because bodies such as
# `setState(() => ...)` contain their own parentheses.
SINGLE_LINE_IF = re.compile(
    r"^(?P<indent>\s*)if\s*\((?P<condition>[^)]*)\)\s+(?P<body>.+;)\s*$"
)

# The generated morning dashboard metric card was four pixels too short under
# Flutter 3.47 text metrics (inner height 76px). Keep this repair deliberately
# exact so it cannot resize unrelated widgets.
METRIC_CARD_OLD = "return SizedBox(width: 180, height: 104, child: Card("
METRIC_CARD_NEW = "return SizedBox(width: 180, height: 116, child: Card("


def repair(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    output: list[str] = []
    changed = 0
    for line in text.splitlines():
        match = SINGLE_LINE_IF.match(line)
        if match is None:
            output.append(line)
            continue
        body = match.group("body").strip()
        if body.startswith(("else ", "case ")):
            output.append(line)
            continue
        indent = match.group("indent")
        condition = match.group("condition").strip()
        if not condition:
            raise ValueError(f"empty generated if condition in {path}")
        output.extend(
            [
                f"{indent}if ({condition}) {{",
                f"{indent}  {body}",
                f"{indent}}}",
            ]
        )
        changed += 1

    repaired = "\n".join(output) + "\n"
    metric_count = repaired.count(METRIC_CARD_OLD)
    if metric_count != 1:
        raise ValueError(
            f"expected exactly one generated metric-card geometry marker; found {metric_count}"
        )
    repaired = repaired.replace(METRIC_CARD_OLD, METRIC_CARD_NEW, 1)
    changed += 1

    path.write_text(repaired, encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Strictly repair generated Research OS Dart style and layout")
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    path = Path(args.file).resolve()
    if not path.is_file():
        raise SystemExit(f"generated Dart file missing: {path}")
    changed = repair(path)
    print(f"self-repair generated Dart changes: {changed}")
    if changed < 2:
        raise SystemExit("expected generated control-flow and layout repairs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
