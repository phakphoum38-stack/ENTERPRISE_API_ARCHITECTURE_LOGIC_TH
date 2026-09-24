import unittest

from tools.research_os_api.universal_runner import (
    BootProfile,
    RunnerDescriptor,
    RunnerError,
    RunnerLifecycle,
    detect_host_resources,
)


class UniversalRunnerTests(unittest.TestCase):
    def test_boot_profile_supports_platform_specific_phases(self):
        profile = BootProfile(
            "windows-toolchain",
            "windows",
            frozenset({"python", "flutter"}),
            ("BOOT", "DISCOVER", "INITIALIZE", "PROVISION", "READY"),
        )
        runner = RunnerDescriptor(
            "runner-win-01",
            "windows",
            "x86_64",
            frozenset({"python", "flutter"}),
            profile,
        )
        self.assertEqual(runner.lifecycle, RunnerLifecycle.CREATED)
        self.assertEqual(runner.transition(RunnerLifecycle.BOOTING).lifecycle, RunnerLifecycle.BOOTING)

    def test_transition_rejects_invalid_skip_backwards(self):
        profile = BootProfile("native-host", "linux")
        runner = RunnerDescriptor("runner-01", "linux", "x86_64", frozenset({"python"}), profile)
        with self.assertRaises(RunnerError):
            runner.transition(RunnerLifecycle.READY)

    def test_failed_boot_never_becomes_ready(self):
        profile = BootProfile("native-host", "linux")
        runner = RunnerDescriptor("runner-01", "linux", "x86_64", frozenset({"python"}), profile)
        failed = runner.transition(RunnerLifecycle.BOOTING).transition(RunnerLifecycle.FAILED)
        with self.assertRaises(RunnerError):
            failed.transition(RunnerLifecycle.READY)

    def test_platform_profile_must_match_runner(self):
        with self.assertRaises(RunnerError):
            RunnerDescriptor("runner-01", "linux", "x86_64", frozenset({"python"}), BootProfile("windows", "windows"))

    def test_host_resource_detection_is_conservative(self):
        snapshot = detect_host_resources()
        self.assertIsNotNone(snapshot.cpu_architecture)
        self.assertTrue(snapshot.cpu_available)
        self.assertIn(snapshot.nvme_detected, (None, True, False))
        if snapshot.ram_total_bytes is not None:
            self.assertGreater(snapshot.ram_total_bytes, 0)
            self.assertGreaterEqual(snapshot.ram_available_bytes or 0, 0)
            self.assertLessEqual(snapshot.ram_utilization or 0, 1)


if __name__ == "__main__":
    unittest.main()
