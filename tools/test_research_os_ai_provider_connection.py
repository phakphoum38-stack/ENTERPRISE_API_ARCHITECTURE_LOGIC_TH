import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import tools.research_os_ai_provider_connection as connection

class AIProviderConnectionTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.evidence_path=Path(self.tmp.name)/"evidence.jsonl"
  self.patch=patch.object(connection,"EVIDENCE_PATH",self.evidence_path);self.patch.start();self.addCleanup(self.patch.stop)
 def test_inspect_is_fail_closed_without_credentials(self):
  with patch.dict(os.environ,{},clear=True):result=connection.inspect()
  providers={item["id"]:item for item in result["providers"]}
  self.assertEqual(providers["openai"]["state"],"UNAVAILABLE");self.assertEqual(providers["gemini"]["state"],"UNAVAILABLE");self.assertTrue(result["secrets_excluded"])
 def test_connect_uses_api_fallback_without_exposing_secret(self):
  with patch.dict(os.environ,{"RESEARCH_OS_OPENAI_API_KEY":"test-secret","RESEARCH_OS_OPENAI_MODEL":"test-model"},clear=True),patch.object(connection,"_health_check",return_value=(True,"healthy")):result=connection.connect("openai")
  self.assertEqual(result["state"],"CONNECTED");self.assertEqual(result["route"],"PLATFORM_API_FALLBACK");self.assertEqual(result["model"],"test-model")
  encoded=self.evidence_path.read_text(encoding="utf-8");self.assertNotIn("test-secret",encoded);record=json.loads(encoded.strip());self.assertEqual(record["provider"],"openai");self.assertEqual(record["operation"],"CONNECT")
 def test_provider_error_degrades_to_api_fallback(self):
  with patch.dict(os.environ,{"RESEARCH_OS_GEMINI_API_KEY":"test-secret"},clear=True),patch.object(connection,"_health_check",return_value=(False,"provider_unreachable")):result=connection.connect("gemini")
  self.assertEqual(result["state"],"API_FALLBACK");self.assertEqual(result["route"],"PLATFORM_API_FALLBACK")
 def test_disconnect_does_not_delete_server_credential(self):
  with patch.dict(os.environ,{"RESEARCH_OS_GEMINI_API_KEY":"test-secret"},clear=True):result=connection.disconnect("gemini")
  self.assertEqual(result["state"],"NOT_CONNECTED");self.assertTrue(result["credential_configured"]);self.assertNotIn("test-secret",self.evidence_path.read_text(encoding="utf-8"))
 def test_unknown_provider_fails_closed(self):
  with self.assertRaises(connection.AIProviderConnectionError):connection.connect("unknown")
if __name__=="__main__":unittest.main()
