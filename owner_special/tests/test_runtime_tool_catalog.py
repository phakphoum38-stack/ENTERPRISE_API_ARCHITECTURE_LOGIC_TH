from research_os_friend.runtime import FriendRuntime
from research_os_friend.unified_tool_catalog import ToolState


def test_runtime_architecture_exposes_unified_tool_catalog(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )

    architecture = runtime.architecture()
    rows = {row["name"]: row for row in architecture["tool_catalog"]}

    assert rows["echo"]["state"] == ToolState.READY.value
    assert rows["summarize"]["state"] == ToolState.READY.value
    assert rows["calendar.health"]["state"] == ToolState.READY.value
    assert rows["calendar.health"]["optional"] is True
    assert rows["calendar.health"]["dependency"] == "phakphum-calendar"


def test_runtime_does_not_promote_v3_tools_without_registry_registration(tmp_path) -> None:
    runtime = FriendRuntime.create_owner_special(
        "owner-test",
        data_root=tmp_path,
        repository_root=tmp_path,
    )

    rows = {row["name"]: row for row in runtime.tool_catalog()}

    for name in ("web", "github", "file", "python", "shell"):
        assert rows[name]["state"] == ToolState.IMPLEMENTED_UNREGISTERED.value
