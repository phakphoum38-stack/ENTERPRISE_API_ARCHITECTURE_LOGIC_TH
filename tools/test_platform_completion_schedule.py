import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class PlatformScheduleCompletionTests(unittest.TestCase):
 def test_validator_passes(self):
  result=subprocess.run([sys.executable,"tools/validate_platform_completion_schedule.py"],cwd=ROOT,text=True,capture_output=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
  self.assertIn("PLATFORM_SCHEDULE_COMPLETION=PASS",result.stdout)
 def test_completion_contract_is_fail_closed(self):
  data=json.loads((ROOT/"current/RESEARCH_OS_PLATFORM_COMPLETION_SCHEDULE_CONTRACT.json").read_text(encoding="utf-8"))
  self.assertEqual(data["status"],"ACTIVE")
  self.assertEqual(data["release_authority"],"FINAL_GATE")
  for rule in ("schedule_does_not_execute","schedule_does_not_authorize","schedule_does_not_release","existing_queue_and_stateless_runner_remain_execution_path","preview_is_not_execution","unmet_requirements_are_not_success","deferred_is_not_done","unknown_is_not_pass"):
   self.assertIn(rule,data["rules"])
if __name__=="__main__": unittest.main()
