from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .approval import ApprovalState
from .identity import OwnerIdentity
from .models import FriendRequest


class ComputerActionType(str, Enum):
    CLICK = "click"
    TYPE = "type"
    SCROLL = "scroll"
    KEY = "key"
    WAIT = "wait"
    SCREENSHOT = "screenshot"


@dataclass(frozen=True)
class ComputerActionIntent:
    action: ComputerActionType
    description: str
    requires_approval: bool = True


@dataclass(frozen=True)
class ComputerUsePlan:
    owner_id: str
    profile_id: str
    session_id: str
    goal: str
    actions: tuple[ComputerActionIntent, ...]
    approval_state: ApprovalState


class ComputerUseBoundary:
    """Safety boundary for a future Responses API computer-use runner.

    This phase plans intent only. It performs no OS input, screenshots, or API
    calls. Every computer action is treated as side-effecting unless an
    explicitly narrower policy is introduced later.
    """

    def plan(
        self,
        owner: OwnerIdentity,
        request: FriendRequest,
        *,
        actions: tuple[ComputerActionIntent, ...],
        approval_state: ApprovalState = ApprovalState.PENDING,
    ) -> ComputerUsePlan:
        if not owner.matches(request.owner_id):
            raise PermissionError("computer-use request does not match the configured owner")
        if approval_state is ApprovalState.NOT_REQUIRED:
            raise ValueError("computer-use actions cannot default to NOT_REQUIRED")
        return ComputerUsePlan(
            owner_id=request.owner_id,
            profile_id=request.profile_id,
            session_id=request.session_id,
            goal=request.text,
            actions=tuple(actions),
            approval_state=approval_state,
        )

    def execution_status(self) -> dict[str, object]:
        return {
            "planning": "ready",
            "os_input": False,
            "screenshots": False,
            "api_calls": False,
            "credential_required_for_this_phase": False,
            "approval_required_by_default": True,
            "execution_authority": "FriendOrchestrator",
            "approval_authority": "ApprovalGate",
        }
