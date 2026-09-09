import unittest

from owner_special.research_os_friend.aeos_assurance_compiler import (
    AssuranceCompilerError,
    compile_assurance_cases,
    select_high_risk_cases,
)


class AssuranceCompilerTests(unittest.TestCase):
    def test_compilation_is_deterministic(self):
        kwargs = dict(
            domains=("reality", "governance"),
            dimensions=("integrity",),
            states=("VALID", "UNKNOWN"),
            risks=("HIGH",),
            actors=("VERIFIER", "BUILDER"),
            modes=("REPLAY",),
        )
        first = compile_assurance_cases(**kwargs)
        second = compile_assurance_cases(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 4)
        self.assertEqual(len({case.case_id for case in first}), 4)

    def test_unbounded_space_is_rejected(self):
        with self.assertRaises(AssuranceCompilerError):
            compile_assurance_cases(
                domains=("a", "b"),
                dimensions=("d", "e"),
                states=("s", "t"),
                risks=("r",),
                actors=("x", "y"),
                modes=("m", "n"),
                max_cases=10,
            )

    def test_empty_axis_is_rejected(self):
        with self.assertRaises(AssuranceCompilerError):
            compile_assurance_cases(
                domains=(),
                dimensions=("integrity",),
                states=("VALID",),
                risks=("HIGH",),
                actors=("VERIFIER",),
                modes=("REPLAY",),
            )

    def test_high_risk_selection_is_deterministic(self):
        cases = compile_assurance_cases(
            domains=("reality",),
            dimensions=("integrity",),
            states=("VALID",),
            risks=("LOW", "CRITICAL"),
            actors=("VERIFIER",),
            modes=("REPLAY",),
        )
        selected = select_high_risk_cases(cases)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].risk, "CRITICAL")


if __name__ == "__main__":
    unittest.main()
