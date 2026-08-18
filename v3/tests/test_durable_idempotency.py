import os
import tempfile
import unittest

from v3.dlq.durable_idempotency import SQLiteIdempotencyRegistry


class DurableIdempotencyTests(unittest.TestCase):
    def test_claim_survives_registry_recreation(self):
        fd, path = tempfile.mkstemp(prefix="v34-idempotency-", suffix=".db")
        os.close(fd)
        try:
            first = SQLiteIdempotencyRegistry(path)
            self.assertTrue(first.claim("idem-1"))
            self.assertTrue(first.is_claimed("idem-1"))
            first.close()

            second = SQLiteIdempotencyRegistry(path)
            self.assertTrue(second.is_claimed("idem-1"))
            self.assertFalse(second.claim("idem-1"))
            second.release("idem-1")
            self.assertFalse(second.is_claimed("idem-1"))
            second.close()
        finally:
            os.unlink(path)

    def test_release_allows_recovery_after_failed_delivery(self):
        registry = SQLiteIdempotencyRegistry()
        self.assertTrue(registry.claim("idem-failed"))
        registry.release("idem-failed")
        self.assertTrue(registry.claim("idem-failed"))
        registry.close()


if __name__ == "__main__":
    unittest.main()
