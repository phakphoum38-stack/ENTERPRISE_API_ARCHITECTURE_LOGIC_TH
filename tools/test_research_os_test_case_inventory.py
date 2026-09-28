import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from tools.research_os_test_case_inventory import TARGET_MIN,TARGET_MAX,discover_dart_test_cases,discover_python_test_cases,discover
class TestCaseInventoryTests(unittest.TestCase):
    def test_python_cases(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"test_sample.py"; p.write_text("def test_a(): pass\nclass X:\n def test_b(self): pass\ndef helper(): pass\n",encoding="utf-8")
            self.assertEqual(discover_python_test_cases(p),2)
    def test_dart_cases(self):
        with TemporaryDirectory() as td:
            p=Path(td)/"sample_test.dart"; p.write_text("test('a', () {}); testWidgets('b', (t) async {}); not_a_test('c');",encoding="utf-8")
            self.assertEqual(discover_dart_test_cases(p),2)
    def test_band(self):
        self.assertEqual((TARGET_MIN,TARGET_MAX),(13000,14000))
    def test_real_inventory(self):
        d=discover(); self.assertRegex(d["source_sha"],r"^[0-9a-f]{40}$"); self.assertGreater(d["inventory"]["test_files"],0); self.assertGreater(d["inventory"]["discovered_test_cases"],0); self.assertIn(d["target_status"],{"IN_BAND","OUT_OF_BAND"}); self.assertEqual(d["discovery"]["execution_status"],"NOT_EXECUTED_BY_INVENTORY")
if __name__=="__main__": unittest.main()
