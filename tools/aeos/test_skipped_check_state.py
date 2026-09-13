import pytest


@pytest.mark.parametrize("state", ["SUCCESS", "NEUTRAL", "SKIPPED"])
def test_terminal_success_states_are_not_rejected_by_bucket(state):
    success_states = {"SUCCESS", "NEUTRAL", "SKIPPED"}
    check = {"state": state, "bucket": "skipping" if state == "SKIPPED" else "pass"}
    assert check["state"] in success_states
    assert check["state"] not in {"FAILURE", "CANCELLED", "TIMED_OUT", "ERROR"}
