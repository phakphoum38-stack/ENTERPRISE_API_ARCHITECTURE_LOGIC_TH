import sys
import tempfile
import unittest

from tools.aeos_autobot_executor import ExecutionPolicy, execute
from tools.aeos_autobot_state_machine import ResultState


class TestAutobotExecutor(unittest.TestCase):
    def test_python_success(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = execute(
                [sys.executable, "-c", "print('ok')"],
                backend="python",
                cwd=cwd,
                policy=ExecutionPolicy(timeout_seconds=5),
            )
        self.assertEqual(result.state, ResultState.PASSED)
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout)

    def test_python_failure_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = execute(
                [sys.executable, "-c", "raise SystemExit(3)"],
                backend="python",
                cwd=cwd,
                policy=ExecutionPolicy(timeout_seconds=5),
            )
        self.assertEqual(result.state, ResultState.FAILED)
        self.assertEqual(result.returncode, 3)

    def test_timeout_is_not_pass(self):
        with tempfile.TemporaryDirectory() as cwd:
            result = execute(
                [sys.executable, "-c", "import time; time.sleep(1)"],
                backend="python",
                cwd=cwd,
                policy=ExecutionPolicy(timeout_seconds=0.05),
            )
        self.assertEqual(result.state, ResultState.TIMED_OUT)
        self.assertNotEqual(result.state, ResultState.PASSED)

    def test_unknown_backend_rejected(self):
        with tempfile.TemporaryDirectory() as cwd:
            with self.assertRaises(ValueError):
                execute(
                    [sys.executable, "-c", "print('no')"],
                    backend="bash",
                    cwd=cwd,
                    policy=ExecutionPolicy(),
                )

    def test_missing_cwd_rejected(self):
        with self.assertRaises(ValueError):
            execute(
                [sys.executable, "-c", "print('no')"],
                backend="python",
                cwd="/definitely/not/a/real/path",
                policy=ExecutionPolicy(),
            )


if __name__ == "__main__":
    unittest.main()
