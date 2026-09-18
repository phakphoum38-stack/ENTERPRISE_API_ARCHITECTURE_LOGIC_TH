import unittest
from v3.research_os_v3.forensic_pack import SameSHAForensicPack,ForensicPackError
class ForensicPackTests(unittest.TestCase):
 def test_deterministic(self):
  p=SameSHAForensicPack(); a=p.build("a"*40,"b"*40,["z","a"],["c","d"]); b=p.build("a"*40,"b"*40,["a","z"],["d","c"]); self.assertEqual(a["forensic_hash"],b["forensic_hash"])
 def test_bad_sha(self):
  with self.assertRaises(ForensicPackError): SameSHAForensicPack().build("bad","b"*40,["a"],["c"])
if __name__=="__main__": unittest.main()
