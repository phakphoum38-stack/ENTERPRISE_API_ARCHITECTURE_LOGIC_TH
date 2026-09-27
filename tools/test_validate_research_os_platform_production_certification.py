import unittest
from tools.validate_research_os_platform_production_certification import main
class ProductionCertificationTest(unittest.TestCase):
    def test_certification(self): self.assertEqual(main(),0)
if __name__=="__main__": unittest.main()
