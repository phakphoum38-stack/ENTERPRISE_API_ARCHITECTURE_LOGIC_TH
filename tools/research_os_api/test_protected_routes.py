from protected_routes import (
    PROTECTED_GET_ROUTES,
    PROTECTED_POST_ROUTES,
    PUBLIC_GET_ROUTES,
    PUBLIC_POST_ROUTES,
    is_protected,
    is_public_bootstrap,
)


def test_public_liveness_and_bootstrap_routes_remain_public():
    assert is_public_bootstrap("GET", "/health")
    assert is_public_bootstrap("GET", "/v1/auth/google/status")
    assert is_public_bootstrap("GET", "/v1/google-workspace/oauth/callback")
    assert is_public_bootstrap("POST", "/v1/auth/google/start")
    assert is_public_bootstrap("POST", "/v1/google-workspace/oauth/start")


def test_user_data_and_ai_routes_are_protected():
    expected_get = {
        "/v1/conversations/cloud",
        "/v1/memory/search",
        "/v1/knowledge/artifacts",
        "/v1/knowledge/graph",
        "/v1/github/dashboard",
    }
    expected_post = {
        "/v1/conversations/cloud/sync",
        "/v1/conversations/cloud/delete",
        "/v1/ai/generate",
        "/v1/ai/answer-with-memory",
        "/v1/conversations/analyze",
        "/v1/memory/commit",
    }
    assert expected_get == set(PROTECTED_GET_ROUTES)
    assert expected_post == set(PROTECTED_POST_ROUTES)
    assert all(is_protected("GET", path) for path in expected_get)
    assert all(is_protected("POST", path) for path in expected_post)


def test_public_and_protected_route_sets_do_not_overlap():
    assert not (PUBLIC_GET_ROUTES & PROTECTED_GET_ROUTES)
    assert not (PUBLIC_POST_ROUTES & PROTECTED_POST_ROUTES)


def test_unknown_routes_are_not_classified_as_protected():
    assert not is_protected("GET", "/unknown")
    assert not is_protected("POST", "/unknown")
    assert not is_protected("PATCH", "/v1/ai/generate")
