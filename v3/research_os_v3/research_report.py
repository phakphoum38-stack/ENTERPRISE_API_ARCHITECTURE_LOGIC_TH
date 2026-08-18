from __future__ import annotations

from dataclasses import dataclass

from .research_checkpoint import ResearchCheckpoint


@dataclass(frozen=True)
class ReportFinding:
    claim: str
    evidence_ids: tuple[str, ...] = ()
    source_uris: tuple[str, ...] = ()
    confidence: float = 0.0


@dataclass(frozen=True)
class ResearchReport:
    title: str
    question: str
    findings: tuple[ReportFinding, ...]
    conclusion: str

    def to_markdown(self) -> str:
        lines = [f"# {self.title}", "", f"**Research question:** {self.question}", "", "## Findings", ""]
        for index, finding in enumerate(self.findings, start=1):
            citations = " ".join(
                f"[{i}]({uri})" for i, uri in enumerate(finding.source_uris, start=1)
            )
            suffix = f" {citations}" if citations else ""
            lines.append(f"{index}. {finding.claim} (confidence={finding.confidence:.2f}).{suffix}")
        lines.extend(["", "## Conclusion", "", self.conclusion, ""])
        return "\n".join(lines)


class ResearchReportBuilder:
    def build(
        self,
        *,
        question: str,
        findings: tuple[ReportFinding, ...],
        conclusion: str,
        title: str = "Research Report",
    ) -> ResearchReport:
        if not question.strip():
            raise ValueError("question must not be empty")
        if not conclusion.strip():
            raise ValueError("conclusion must not be empty")
        for finding in findings:
            if not 0.0 <= finding.confidence <= 1.0:
                raise ValueError("finding confidence must be between 0 and 1")
            if len(finding.evidence_ids) != len(set(finding.evidence_ids)):
                raise ValueError("evidence ids must be unique per finding")
        return ResearchReport(title, question.strip(), findings, conclusion.strip())

    def from_checkpoint(
        self,
        checkpoint: ResearchCheckpoint,
        *,
        conclusion: str,
        title: str = "Research Report",
    ) -> ResearchReport:
        finding = ReportFinding(
            claim=f"Research completed {len(checkpoint.completed_tasks)} task(s).",
            evidence_ids=checkpoint.evidence_ids,
            confidence=1.0 if not checkpoint.failed_tasks else 0.5,
        )
        return self.build(
            question=checkpoint.plan_question,
            findings=(finding,),
            conclusion=conclusion,
            title=title,
        )
