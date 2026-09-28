import unittest

import server_auth_routes


class ServerAuthRouteTests(unittest.TestCase):
    def test_callback_requires_code_and_state(self):
        with self.assertRaises(Exception):
            server_auth_routes.auth_callback("github", "")

    def test_status_without_cookie_is_disconnected(self):
        result = server_auth_routes.auth_status(None)
        self.assertFalse(result["connected"])
        self.assertIsNone(result["account"])


if __name__ == "__main__":
    unittest.main()
