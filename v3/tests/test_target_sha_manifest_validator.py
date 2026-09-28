import unittest
from v3.research_os_v3.target_sha_manifest_validator import TargetSHAManifestValidator,TargetManifestError
class TargetManifestValidatorTests(unittest.TestCase):
 def setUp(self): self.v=TargetSHAManifestValidator(); self.m={"target_sha":"a"*40,"target_identity_algorithm":"git-sha1","evidence_algorithm":"sha256","entries":[{"target_sha":"a"*40,"evidence_hash":"b"*64}]}
 def test_valid(self): self.v.validate(self.m)
 def test_mixed_target_fails(self):
  with self.assertRaises(TargetManifestError): self.v.validate({**self.m,"entries":[{"target_sha":"c"*40,"evidence_hash":"b"*64}]})
 def test_bad_evidence_fails(self):
  with self.assertRaises(TargetManifestError): self.v.validate({**self.m,"entries":[{"target_sha":"a"*40,"evidence_hash":"bad"}]})
if __name__=="__main__": unittest.main()
