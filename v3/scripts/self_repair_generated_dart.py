from __future__ import annotations

import argparse
import re
from pathlib import Path

# Generated UI uses deliberately simple single-line control flow.  Repair only
# standalone `if (...) statement;` lines.  Collection-if elements end with a
# comma and are intentionally not touched.
SINGLE_LINE_IF = re.compile(r"^(?P<indent>\s*)if\s*\((?P<condition>.+)\)\s+(?P<body>.+;)\s*$")


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
        # Avoid transforming conditional expressions or malformed fragments.
        if body.startswith(("else ", "case ")):
            output.append(line)
            continue
        indent = match.group("indent")
        condition = match.group("condition")
        output.extend(
            [
                f"{indent}if ({condition}) {{",
                f"{indent}  {body}",
                f"{indent}}}",
            ]
        )
        changed += 1
    if changed:
        path.write_text("\n".join(output) + "\n", encoding="utf-8", newline="\n")
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Strictly repair generated Research OS Dart style")
    parser.add_argument("--file", required=True)
    args = parser.parse_args()
    path = Path(args.file).resolve()
    if not path.is_file():
        raise SystemExit(f"generated Dart file missing: {path}")
    changed = repair(path)
    print(f"self-repair control-flow changes: {changed}")
    if changed < 1:
        raise SystemExit("expected at least one generated control-flow repair")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
