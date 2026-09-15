from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from providers import ProviderError, build_provider


class ProductionProviderBypassTests(unittest.TestCase):
    def test_direct_provider_route_is_disabled(self):
        with patch.dict(os.environ, {"RESEARCH_OS_AI_ROUTE": "direct-provider"}, clear=False):
            with self.assertRaisesRegex(ProviderError, "direct-provider route is disabled"):
                build_provider("mock")

    def test_friend_route_keeps_provider_factory_available(self):
        with patch.dict(os.environ, {"RESEARCH_OS_AI_ROUTE": "friend"}, clear=False):
            self.assertEqual(build_provider("mock").name, "mock")


if __name__ == "__main__":
    unittest.main()
