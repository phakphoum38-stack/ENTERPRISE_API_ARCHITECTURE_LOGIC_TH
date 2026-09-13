from __future__ import annotations

import json


class ResponseComposer:
    """Compose a user-facing answer while preserving verified tool evidence."""

    MAX_EVIDENCE_CHARS = 5000

    def compose(
        self,
        *,
        provider_name: str,
        answer: str,
        tool_results: dict[str, object],
    ) -> str:
        if not tool_results or provider_name != "owner-mock":
            return answer
        evidence = json.dumps(tool_results, ensure_ascii=False, indent=2, default=str)
        if len(evidence) > self.MAX_EVIDENCE_CHARS:
            evidence = evidence[: self.MAX_EVIDENCE_CHARS] + "\n... [evidence truncated]"
        return f"{answer}\n\n[Verified tool results]\n{evidence}"
