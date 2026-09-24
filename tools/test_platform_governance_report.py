import subprocess, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PlatformGovernanceReportTests(unittest.TestCase):
    def test_component_inventory_and_report_pass(self):
        r=subprocess.run([sys.executable,"tools/validate_platform_governance.py"],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        r2=subprocess.run([sys.executable,"tools/platform_governance_report.py","--json"],cwd=ROOT,text=True,capture_output=True,check=True)
        self.assertIn('"component_count": 9',r2.stdout)
    def test_report_preserves_fail_closed_semantics(self):
        r=subprocess.run([sys.executable,"tools/platform_governance_report.py"],cwd=ROOT,text=True,capture_output=True,check=True)
        self.assertIn("UNKNOWN_IS_NOT_DONE=TRUE",r.stdout)
if __name__=="__main__": unittest.main()
