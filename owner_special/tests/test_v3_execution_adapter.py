from __future__ import annotations

import pytest

from research_os_friend.models import FriendRequest
from research_os_friend.runtime import FriendRuntime
from v3.research_os_v3.research_tools import ToolResult


def test_v3_adapter_registers_local_and_network_tools(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )

    assert runtime.v3.names() == ("file", "github", "python", "shell", "web")
    rows = {row["name"]: row for row in runtime.tool_catalog()}
    for name in ("web", "github", "file", "python", "shell"):
        assert rows[name]["state"] == "ready"


def test_v3_adapter_executes_python_without_network(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )
    request = FriendRequest(
        owner_id="owner-test",
        text="analyze python",
        requested_tools=("python",),
    )

    result = runtime.execute_v3(
        request,
        capability="python.analyze",
        input={"source": "import json\nvalue = 1"},
    )

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.output["imports"] == ["json"]


def test_v3_adapter_rejects_unrequested_capability(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )
    request = FriendRequest(owner_id="owner-test", text="run", requested_tools=())

    with pytest.raises(PermissionError, match="explicitly requested"):
        runtime.execute_v3(
            request,
            capability="python.analyze",
            input={"source": "value = 1"},
        )


def test_v3_adapter_rejects_wrong_owner(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )
    request = FriendRequest(
        owner_id="other-owner",
        text="analyze python",
        requested_tools=("python",),
    )

    with pytest.raises(PermissionError, match="Owner Special request"):
        runtime.execute_v3(
            request,
            capability="python.analyze",
            input={"source": "value = 1"},
        )
