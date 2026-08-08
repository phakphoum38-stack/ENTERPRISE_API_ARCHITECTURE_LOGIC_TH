import json
import unittest
from unittest.mock import patch

from providers import GeminiProvider, OpenAICompatibleProvider


class _FakeResponse:
    def __init__(self, lines):
        self._lines = [line.encode("utf-8") for line in lines]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        return iter(self._lines)


class ProviderStreamingTests(unittest.TestCase):
    def test_openai_compatible_streams_sse_delta_chunks(self):
        response = _FakeResponse(
            [
                'data: {"model":"test-model","choices":[{"delta":{"content":"Hello "}}]}\n',
                'data: {"model":"test-model","choices":[{"delta":{"content":"world"}}]}\n',
                'data: [DONE]\n',
            ]
        )
        captured = {}

        def fake_urlopen(request, timeout=60):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return response

        provider = OpenAICompatibleProvider(
            endpoint="http://localhost:11434/v1/chat/completions",
            api_key=None,
            default_model="test-model",
        )
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            chunks = list(provider.stream("hello"))

        self.assertEqual("http://localhost:11434/v1/chat/completions", captured["url"])
        self.assertTrue(captured["payload"]["stream"])
        self.assertEqual("Hello world", "".join(chunk.text for chunk in chunks))
        self.assertTrue(chunks[-1].done)

    def test_gemini_uses_stream_generate_content_sse(self):
        response = _FakeResponse(
            [
                'data: {"candidates":[{"content":{"parts":[{"text":"สวัสดี "}]}}]}\n',
                'data: {"candidates":[{"content":{"parts":[{"text":"ครับ"}]}}]}\n',
            ]
        )
        captured = {}

        def fake_urlopen(request, timeout=60):
            captured["url"] = request.full_url
            captured["payload"] = json.loads(request.data.decode("utf-8"))
            return response

        provider = GeminiProvider(
            endpoint_template=(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "{model}:generateContent?key={api_key}"
            ),
            api_key="test-key",
            default_model="gemini-test",
        )
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            chunks = list(provider.stream("ทดสอบ"))

        self.assertIn(":streamGenerateContent", captured["url"])
        self.assertIn("alt=sse", captured["url"])
        self.assertEqual("ทดสอบ", captured["payload"]["contents"][0]["parts"][0]["text"])
        self.assertEqual("สวัสดี ครับ", "".join(chunk.text for chunk in chunks))
        self.assertTrue(chunks[-1].done)


if __name__ == "__main__":
    unittest.main()
