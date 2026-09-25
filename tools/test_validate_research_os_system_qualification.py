import unittest

from validate_research_os_system_qualification import main


class SystemQualificationValidatorTests(unittest.TestCase):
    def test_system_qualification_is_bound_and_fail_closed(self) -> None:
        main()


if __name__ == "__main__":
    unittest.main()
