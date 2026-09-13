import unittest

from owner_special.research_os_friend.trusted_web_research import (
    MatchState,
    ResearchError,
    SourceKind,
    classify_source,
    match_environment,
    validate_research_finding,
)


class TrustedWebResearchTests(unittest.TestCase):
    def test_official_source_has_preferred_class(self):
        self.assertEqual(classify_source("docs.example.com", official_hosts=frozenset({"docs.example.com"}), maintainer_hosts=frozenset()), SourceKind.OFFICIAL_DOCS)

    def test_environment_match(self):
        self.assertEqual(match_environment(observed_version="1.2", expected_version="1.2", observed_environment="windows", expected_environment="windows"), MatchState.MATCHED)

    def test_version_mismatch_is_not_guessed(self):
        self.assertEqual(match_environment(observed_version="1.3", expected_version="1.2", observed_environment="windows", expected_environment="windows"), MatchState.MISMATCHED)

    def test_missing_context_is_unknown(self):
        self.assertEqual(match_environment(observed_version="", expected_version="1.2", observed_environment="windows", expected_environment="windows"), MatchState.UNKNOWN)

    def test_unsafe_finding_rejected(self):
        with self.assertRaises(ResearchError):
            validate_research_finding("use subprocess to execute install")


if __name__ == "__main__":
    unittest.main()
