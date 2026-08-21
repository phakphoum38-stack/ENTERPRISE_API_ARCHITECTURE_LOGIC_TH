from __future__ import annotations

import ast
from dataclasses import replace

from .models import CodeArtifact


class CodeFactory:
    """Deterministic code artifact builder with syntax validation before handoff."""

    def build_python(self, path: str, source: str, purpose: str) -> CodeArtifact:
        if not path.endswith(".py"):
            raise ValueError("Python artifact path must end with .py")
        if not source.strip():
            raise ValueError("source cannot be empty")
        ast.parse(source, filename=path)
        return CodeArtifact(path=path, content=source, language="python", purpose=purpose)

    def add_header(self, artifact: CodeArtifact, header: str) -> CodeArtifact:
        if not header.strip():
            raise ValueError("header cannot be empty")
        content = f"{header.rstrip()}\n\n{artifact.content}"
        if artifact.language == "python":
            ast.parse(content, filename=artifact.path)
        return replace(artifact, content=content)
