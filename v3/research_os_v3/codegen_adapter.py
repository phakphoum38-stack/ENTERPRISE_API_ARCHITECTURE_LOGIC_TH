from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping

from .execution import StageEvidence, _sha256
from .models import OrchestrationDecision, Workload
from .providers import CompletionRequest, ProviderRegistry


@dataclass(frozen=True)
class CodeGenerationRequest:
    task: str
    repository: str
    base_sha: str
    constraints: Mapping[str, object]


@dataclass(frozen=True)
class CodeGenerationResult:
    status: str
    provider: str
    model: str
    output: str
    output_sha256: str
    base_sha: str

    @property
    def evidence(self) -> StageEvidence:
        return StageEvidence(
            name="codegen",
            status=self.status,
            output_sha256=self.output_sha256 if self.status == "passed" else None,
        )


class ExistingCodeGeneratorAdapter:
    """Bridge the existing provider/orchestrator stack to a governed codegen stage.

    The adapter deliberately returns generated text only. Branch creation, commits,
    PRs and release decisions remain outside the generator so generated output can
    be tested and audited before any repository mutation.
    """

    contract = "existing-code-generator-adapter-v1"

    def __init__(self, providers: ProviderRegistry | None = None) -> None:
        self.providers = providers or ProviderRegistry()

    def generate(
        self,
        request: CodeGenerationRequest,
        *,
        decision: OrchestrationDecision | None = None,
    ) -> CodeGenerationResult:
        system_prompt = (
            "You are the repository code-generation stage. Return only the proposed "
            "patch/content, never secrets. Preserve the supplied base SHA and obey "
            "the stated constraints. Do not claim tests or CI passed unless evidence "
            "was actually supplied."
        )
        prompt = (
            f"Task: {request.task}\n"
            f"Repository: {request.repository}\n"
            f"Base SHA: {request.base_sha}\n"
            f"Constraints: {dict(request.constraints)}\n"
            f"Decision: {decision}\n"
        )
        response = self.providers.complete(
            CompletionRequest(prompt=prompt, system_prompt=system_prompt),
            preferred=decision.provider if decision else None,
        )
        return CodeGenerationResult(
            status="passed",
            provider=response.provider,
            model=response.model,
            output=response.text,
            output_sha256=_sha256(response.text),
            base_sha=request.base_sha,
        )


CodegenStageHandler = Callable[[CodeGenerationRequest], CodeGenerationResult]
