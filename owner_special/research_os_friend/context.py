from __future__ import annotations

from dataclasses import dataclass

from .identity import OwnerIdentity
from .memory import MemoryItem, ScopedMemory
from .models import FriendRequest


@dataclass(frozen=True)
class FriendContext:
    owner: OwnerIdentity
    request: FriendRequest
    memories: tuple[MemoryItem, ...]

    @classmethod
    def build(cls, owner: OwnerIdentity, request: FriendRequest, memory: ScopedMemory) -> "FriendContext":
        return cls(
            owner=owner,
            request=request,
            memories=memory.recall(
                owner_id=request.owner_id,
                profile_id=request.profile_id,
                session_id=request.session_id,
            ),
        )
