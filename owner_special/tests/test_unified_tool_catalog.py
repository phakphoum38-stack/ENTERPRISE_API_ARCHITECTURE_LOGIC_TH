from research_os_friend.unified_tool_catalog import ToolState, UnifiedToolCatalog


def test_catalog_exposes_expected_states() -> None:
    catalog = UnifiedToolCatalog()

    assert {item.name for item in catalog.by_state(ToolState.READY)} >= {
        "echo",
        "summarize",
        "schedule.generate",
        "yaml-validator",
        "python-validator",
        "git-branch",
        "pr-gate",
    }
    assert {item.name for item in catalog.by_state(ToolState.IMPLEMENTED_UNREGISTERED)} >= {
        "web",
        "github",
        "file",
        "python",
        "shell",
    }
    assert "google-workspace" in {
        item.name for item in catalog.by_state(ToolState.NEEDS_CONNECTION)
    }


def test_health_matrix_uses_actual_registry_membership() -> None:
    catalog = UnifiedToolCatalog()
    rows = {row["name"]: row for row in catalog.health_matrix(
        friend_tools=("echo", "summarize", "schedule.generate", "calendar.health", "calendar.sync", "calendar.sync.status"),
        v3_tools=("web", "github", "file", "python", "shell"),
    )}

    assert rows["echo"]["state"] == "ready"
    assert rows["web"]["state"] == "implemented_unregistered"
    assert rows["google-workspace"]["state"] == "needs_connection"


def test_catalog_rejects_duplicate_names() -> None:
    from research_os_friend.unified_tool_catalog import ToolDescriptor

    descriptor = ToolDescriptor("duplicate", "test.capability", "test", ToolState.READY)
    try:
        UnifiedToolCatalog((descriptor, descriptor))
    except ValueError as exc:
        assert str(exc) == "duplicate tool catalog entry"
    else:
        raise AssertionError("expected duplicate catalog entry to fail")
