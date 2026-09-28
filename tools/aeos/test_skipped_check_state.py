SUCCESS_STATES = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def test_skipped_is_terminal_success_even_with_skipping_bucket():
    check = {"state": "SKIPPED", "bucket": "skipping"}
    assert check["state"] in SUCCESS_STATES
    assert check["state"] not in {"FAILURE", "CANCELLED", "TIMED_OUT", "ERROR"}
