from __future__ import annotations

from dataclasses import dataclass

from .approval import ApprovalState
from .models import FriendRequest
from .orchestrator import FriendOrchestrator


@dataclass(frozen=True)
class AgentsSdkToolContract:
    name: str
    description: str
    approval_required: bool
    approval_state: str


@dataclass(frozen=True)
class AgentsSdkContract:
    agent_name: str
    instructions: str
    tools: tuple[AgentsSdkToolContract, ...]
    owner_id: str
    profile_id: str
    session_id: str


class AgentsSdkAdapter:
    """Compatibility boundary for a future OpenAI Agents SDK runner.

    This phase builds a deterministic contract only. It does not call the API,
    import the SDK at runtime, or execute tools. Approval remains local.
    """

    def __init__(self, orchestrator: FriendOrchestrator, *, agent_name: str = "research-os-friend") -> None:
        self.orchestrator = orchestrator
        self.agent_name = agent_name

    def build_contract(self, request: FriendRequest) -> AgentsSdkContract:
        self.orchestrator.policy.authorize_request(self.orchestrator.owner, request)
        contracts: list[AgentsSdkToolContract] = []
        for tool_name in request.requested_tools:
            tool = self.orchestrator.tools.resolve((tool_name,))[0]
            approval = self.orchestrator.approval_gate.inspect(
                self.orchestrator.owner,
                request,
                tool_name,
            )
            contracts.append(
                AgentsSdkToolContract(
                    name=tool.name,
                    description=tool.description,
                    approval_required=approval.state is not ApprovalState.NOT_REQUIRED,
                    approval_state=approval.state.value,
                )
            )
        return AgentsSdkContract(
            agent_name=self.agent_name,
            instructions=(
                "Preserve FriendOrchestrator as the execution authority. "
                "Use only explicitly requested tools and honor ApprovalGate before side effects."
            ),
            tools=tuple(contracts),
            owner_id=request.owner_id,
            profile_id=request.profile_id,
            session_id=request.session_id,
        )

    def sdk_dependency_status(self) -> dict[str, object]:
        """Describe the adapter boundary without importing or requiring the SDK."""
        return {
            "adapter": "ready",
            "provider": "OpenAI Agents SDK",
            "runtime_import": False,
            "api_calls": False,
            "credential_required_for_this_phase": False,
            "execution_authority": "FriendOrchestrator",
            "approval_authority": "ApprovalGate",
        }
