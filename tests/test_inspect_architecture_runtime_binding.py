from pathlib import Path

from tools.inspect_architecture_runtime_binding import inspect


def test_runtime_binding_inspector_is_fail_closed():
    result = inspect(Path(__file__).resolve().parents[1])
    assert result["mode"] == "read_only_runtime_binding_inspection"
    assert result["status"] == "FAIL"
    assert result["summary"]["unproven_or_duplicate"] > 0


def test_runtime_binding_inspector_reports_all_roots():
    result = inspect(Path(__file__).resolve().parents[1])
    assert set(result["roots"]) == {"general", "owner_special", "v3"}
    for item in result["roots"].values():
        assert "dimensions" in item
        assert "navigation" in item["dimensions"]
        assert "state" in item["dimensions"]


def test_shared_contract_exports_are_explicit():
    result = inspect(Path(__file__).resolve().parents[1])
    assert all(result["shared_contract_exports"].values())
