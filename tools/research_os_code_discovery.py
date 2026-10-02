from __future__ import annotations
from pathlib import Path
from tools.research_os_code_identity import extract_python_identities

CODE_SUFFIXES = frozenset({
    ".py", ".ps1", ".sh", ".dart", ".js", ".ts", ".cs", ".cpp", ".h"
})

def discover_code(root: Path) -> list[str]:
    return sorted(
        p.relative_to(root).as_posix()
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix.lower() in CODE_SUFFIXES
        and ".git" not in p.parts
    )

def inspect_python(root: Path, paths: list[str]) -> list[dict]:
    result = []
    for relative in paths:
        path = root / relative
        if path.suffix.lower() == ".py":
            result.append(
                extract_python_identities(
                    relative,
                    path.read_text(encoding="utf-8"),
                )
            )
    return result
