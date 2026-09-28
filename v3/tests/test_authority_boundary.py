import unittest
from v3.research_os_v3.authority_boundary import AuthorityBoundary
class AuthorityBoundaryTests(unittest.TestCase):
 def test_packet_alone_cannot_authorize(self):
  x=AuthorityBoundary().evaluate({"owner_authority_required":True,"pre_authority":"PASS"},False); self.assertFalse(x["merge_authorized"])
 def test_owner_authority_is_explicit(self):
  x=AuthorityBoundary().evaluate({"owner_authority_required":True,"pre_authority":"PASS"},True); self.assertTrue(x["merge_authorized"])
if __name__=="__main__": unittest.main()
