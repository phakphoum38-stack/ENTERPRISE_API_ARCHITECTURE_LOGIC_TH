import unittest
from tools.validate_research_os_identity_access_convergence import main
class IdentityAccessConvergenceTest(unittest.TestCase):
    def test_contract(self):
        main()
if __name__=='__main__': unittest.main()
