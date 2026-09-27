import unittest
from tools.platform_code_writer import plan
class CodeWriterTest(unittest.TestCase):
    def test_requires_canonical_pipeline(self):
        self.assertEqual(plan(["REGISTRY","RECON","DEPENDENCY_GRAPH","CONTRACT","CHANGE_BOUNDARY","CODE_WRITER","VALIDATION","EVIDENCE"])["status"],"PASS")
    def test_unknown_holds(self): self.assertEqual(plan(["AI","CODE_WRITER"])["status"],"HOLD")
if __name__=="__main__": unittest.main()
