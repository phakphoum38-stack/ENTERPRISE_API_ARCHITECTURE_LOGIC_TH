import unittest
from v3.research_os_v3.authority_packet import AuthorityPacketBuilder,AuthorityPacketError
class AuthorityPacketTests(unittest.TestCase):
 def test_requires_owner_authority(self):
  x=AuthorityPacketBuilder().build({"target_sha":"a"*40},{"status":"PASS"},{"status":"PASS"}); self.assertTrue(x["owner_authority_required"]); self.assertFalse(x["merge_authorized"])
 def test_review_hold(self):
  with self.assertRaises(AuthorityPacketError): AuthorityPacketBuilder().build({"target_sha":"a"*40},{"status":"HOLD"},{"status":"PASS"})
if __name__=="__main__": unittest.main()
