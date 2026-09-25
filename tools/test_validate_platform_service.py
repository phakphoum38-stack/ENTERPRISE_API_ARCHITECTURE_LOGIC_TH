import unittest

from tools.validate_platform_service import validate


class PlatformServiceContractTests(unittest.TestCase):
    def test_platform_composition_is_complete(self):
        self.assertEqual(validate(), [])


if __name__ == "__main__":
    unittest.main()
