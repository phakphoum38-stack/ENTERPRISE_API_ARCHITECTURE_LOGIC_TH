import unittest

from policy import PolicyContext, PolicyEffect, PolicyEngine, PolicyRule
from resource_governance import QuotaDimension, QuotaError, Usage


class PolicyEngineTests(unittest.TestCase):
    def test_dimension_threshold_triggers_rule(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule("deny-heavy", PolicyEffect.DENY, {QuotaDimension.TOKENS: 100}))
        engine.add_rule(PolicyRule("allow-user", PolicyEffect.ALLOW))
        below = engine.evaluate(PolicyContext("user-1"), Usage(tokens=50))
        self.assertEqual(below.rule_id, "default")
        at_threshold = engine.evaluate(PolicyContext("user-1"), Usage(tokens=100))
        self.assertEqual(at_threshold.effect, PolicyEffect.DENY)

    def test_scope_and_principal_constraints(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule("agent-only", PolicyEffect.THROTTLE,
                                   required_scopes=frozenset({"agent:run"}),
                                   principal_types=frozenset({"agent"})))
        self.assertEqual(engine.evaluate(PolicyContext("u1", frozenset({"agent:run"}), "user"), Usage()).rule_id, "default")
        self.assertEqual(engine.evaluate(PolicyContext("a1", frozenset({"agent:run"}), "agent"), Usage()).effect, PolicyEffect.THROTTLE)

    def test_no_match_defaults_to_allow(self):
        decision = PolicyEngine().evaluate(PolicyContext("u1"), Usage())
        self.assertEqual(decision.effect, PolicyEffect.ALLOW)
        self.assertEqual(decision.rule_id, "default")

    def test_duplicate_and_invalid_rules_fail_closed(self):
        engine = PolicyEngine()
        engine.add_rule(PolicyRule("r1", PolicyEffect.ALLOW))
        with self.assertRaises(QuotaError):
            engine.add_rule(PolicyRule("r1", PolicyEffect.DENY))
        with self.assertRaises(QuotaError):
            PolicyRule("bad", PolicyEffect.DENY, {QuotaDimension.REQUESTS: -1})


if __name__ == "__main__":
    unittest.main()
