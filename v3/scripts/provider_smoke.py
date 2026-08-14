from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import CompletionRequest, OpenAICompatibleProvider


class StaticSecretSource:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def get(self, name: str) -> str | None:
        return self.secret if name == "OPENAI_API_KEY" else None


class FakeTransport:
    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        assert url.endswith("/chat/completions")
        assert headers["Authorization"].startswith("Bearer ")
        assert payload["model"] == "candidate-model"
        assert timeout == 5.0
        return {"choices": [{"message": {"content": "provider-smoke-ok"}}]}


def main() -> int:
    secret = "provider-smoke-secret"
    provider = OpenAICompatibleProvider(
        base_url="https://provider.invalid/v1",
        model="candidate-model",
        secret_source=StaticSecretSource(secret),
        transport=FakeTransport(),
        timeout=5.0,
    )
    safe_before = provider.status().to_safe_dict()
    assert secret not in json.dumps(safe_before, sort_keys=True)
    response = provider.complete(CompletionRequest(prompt="health-check"))
    safe_after = provider.status().to_safe_dict()
    assert response.text == "provider-smoke-ok"
    assert safe_after["connected"] is True
    assert secret not in json.dumps(safe_after, sort_keys=True)
    print(json.dumps({"status": safe_after, "response": {"provider": response.provider, "model": response.model}}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
