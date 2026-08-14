import json
import unittest
import urllib.error
from email.message import Message
from io import BytesIO

import providers


class ProviderRetryTests(unittest.TestCase):
    def test_extracts_retry_delay_from_gemini_error_message(self):
        body = json.dumps(
            {
                "error": {
                    "code": 429,
                    "status": "RESOURCE_EXHAUSTED",
                    "message": "Quota exceeded. Please retry in 30.702847117s.",
                }
            }
        )
        self.assertAlmostEqual(providers._retry_delay_from_body(body), 30.702847117)

    def test_extracts_retry_info_delay(self):
        body = json.dumps(
            {
                "error": {
                    "details": [
                        {
                            "@type": "type.googleapis.com/google.rpc.RetryInfo",
                            "retryDelay": "12.5s",
                        }
                    ]
                }
            }
        )
        self.assertEqual(providers._retry_delay_from_body(body), 12.5)

    def test_retry_after_header_has_priority(self):
        headers = Message()
        headers["Retry-After"] = "17"
        exc = urllib.error.HTTPError(
            "https://example.invalid",
            429,
            "Too Many Requests",
            headers,
            BytesIO(b"{}"),
        )
        self.assertEqual(providers._retry_delay_seconds(exc, "{}", 1), 17.0)

    def test_body_delay_gets_small_reset_cushion(self):
        headers = Message()
        body = json.dumps({"error": {"message": "Please retry in 4.25s."}})
        exc = urllib.error.HTTPError(
            "https://example.invalid",
            429,
            "Too Many Requests",
            headers,
            BytesIO(body.encode("utf-8")),
        )
        self.assertAlmostEqual(providers._retry_delay_seconds(exc, body, 1), 4.75)


if __name__ == "__main__":
    unittest.main()
