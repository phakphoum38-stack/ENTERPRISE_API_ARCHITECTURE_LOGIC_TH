from __future__ import annotations
import ast
from pathlib import Path
from typing import Any

def extract_python_identities(path: str, text: str) -> dict[str, Any]:
    tree = ast.parse(text, filename=path)
    constants = {}
    symbols = []
    calls = []
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    constants[target.id] = node.value.value
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")

    return {
        "path": Path(path).as_posix(),
        "constants": constants,
        "symbols": sorted(set(symbols)),
        "calls": sorted(set(calls)),
        "imports": sorted(set(imports)),
    }
