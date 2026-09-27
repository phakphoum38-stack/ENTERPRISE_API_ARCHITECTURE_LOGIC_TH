import unittest
from tools.platform_observability import validate
class ObservabilityTest(unittest.TestCase):
    def test_complete_lineage(self):
        c={k:k for k in ("request_id","correlation_id","actor","contract_version")}
        self.assertEqual(validate(c,["request","workflow","delivery","worker","evidence","audit","gate"])["status"],"PASS")
if __name__=="__main__": unittest.main()
