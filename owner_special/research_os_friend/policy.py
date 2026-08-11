from __future__ import annotations

from .identity import OwnerIdentity
from .models import FriendRequest


class OwnerPolicy:
    """Hard owner boundary for the special edition."""

    def authorize_request(self, owner: OwnerIdentity, request: FriendRequest) -> None:
        if not owner.matches(request.owner_id):
            raise PermissionError("Owner Special request does not match the configured owner")
        if not request.text.strip():
            raise ValueError("request text is required")

    def authorize_tool(self, owner: OwnerIdentity, request: FriendRequest, tool_name: str) -> None:
        self.authorize_request(owner, request)
        if tool_name not in request.requested_tools:
            raise PermissionError(f"tool was not explicitly requested: {tool_name}")
