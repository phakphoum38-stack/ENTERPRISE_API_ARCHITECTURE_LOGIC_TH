#!/usr/bin/env python3
"""Negative assurance for the AEOS Autobot multi-wave controller."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools.aeos_autobot_evidence_manifest import SnapshotLock, evidence_id
from tools.aeos_autobot_orchestrator import Job
from tools.aeos_autobot_state_machine import Evidence, ResultState, Snapshot
from tools.aeos_autobot_wave_controller import WAVES, ControllerLimits, run_controller


SHA = "a" * 40


def make_job(iteration: str, wave: str, set_id: str, result: ResultState = ResultState.PASSED) -> Job:
    snapshot = Snapshot(iteration, SHA, set_id, wave, "python -c pass", ".")

    def runner(item: Snapshot) -> Evidence:
        return Evidence(item, result, evidence_id(item, result))

    return Job(snapshot, runner)


def wave_jobs(iteration: str, result_by_wave: dict[str, ResultState] | None = None) -> dict[str, list[Job]]:
    result_by_wave = result_by_wave or {}
    return {
        wave: [make_job(iteration, wave, f"{wave}-001", result_by_wave.get(wave, ResultState.PASSED))]
        for wave in WAVES
    }


def locks_for(iteration: str) -> dict[str, SnapshotLock]:
    return {
        wave: SnapshotLock(iteration, SHA, f"batch-{wave}", f"run-{wave}", (f"{wave}-001",), "start", "finish")
        for wave in WAVES
    }


class MultiWaveControllerTests(unittest.TestCase):
    def test_w0_pass_allows_w1(self) -> None:
        result = run_controller(iteration_id="it-1", source_sha=SHA, waves=wave_jobs("it-1"))
        self.assertEqual(result.state, ResultState.PASSED)
        self.assertEqual([item.wave_id for item in result.waves], list(WAVES))

    def test_w0_failure_blocks_later_waves(self) -> None:
        result = run_controller(
            iteration_id="it-2", source_sha=SHA,
            waves=wave_jobs("it-2", {"W0": ResultState.FAILED}),
        )
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual([item.wave_id for item in result.waves], ["W0"])

    def test_one_worker_failure_holds_current_wave(self) -> None:
        result = run_controller(
            iteration_id="it-3", source_sha=SHA,
            waves=wave_jobs("it-3", {"W2": ResultState.FAILED}),
        )
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual(result.waves[-1].result.decision, ResultState.HOLD)

    def test_incomplete_wave_holds_before_progression(self) -> None:
        waves = wave_jobs("it-4")
        del waves["W1"]
        result = run_controller(iteration_id="it-4", source_sha=SHA, waves=waves)
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual([item.wave_id for item in result.waves], ["W0"])

    def test_wrong_source_sha_is_rejected(self) -> None:
        waves = wave_jobs("it-5")
        waves["W0"] = [make_job("it-5", "W0", "W0-001")]
        result = run_controller(iteration_id="it-5", source_sha="b" * 40, waves=waves)
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual(result.waves, ())

    def test_wrong_iteration_is_rejected(self) -> None:
        waves = wave_jobs("it-6")
        waves["W1"] = [make_job("other", "W1", "W1-001")]
        with self.assertRaisesRegex(ValueError, "snapshot_lock_mismatch"):
            run_controller(iteration_id="it-6", source_sha=SHA, waves=waves)

    def test_timeout_never_passes(self) -> None:
        result = run_controller(
            iteration_id="it-7", source_sha=SHA,
            waves=wave_jobs("it-7", {"W0": ResultState.TIMED_OUT}),
        )
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertNotEqual(result.waves[0].result.decision, ResultState.PASSED)

    def test_manifest_lock_mismatch_holds(self) -> None:
        locks = locks_for("it-8")
        locks["W0"] = SnapshotLock("other", SHA, "batch-W0", "run-W0", ("W0-001",), "start", "finish")
        result = run_controller(iteration_id="it-8", source_sha=SHA, waves=wave_jobs("it-8"), locks=locks)
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual([item.wave_id for item in result.waves], ["W0"])

    def test_manifest_tamper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_controller(
                iteration_id="it-9", source_sha=SHA, waves=wave_jobs("it-9"),
                locks=locks_for("it-9"), manifest_dir=tmp,
            )
            self.assertEqual(result.state, ResultState.PASSED)
            path = Path(tmp) / "aeos_autobot_it-9_W0.json"
            path.write_text(path.read_text(encoding="utf-8").replace('"decision":"PASSED"', '"decision":"HOLD"'), encoding="utf-8")
            from tools.aeos_autobot_evidence_manifest import verify_manifest
            with self.assertRaisesRegex(ValueError, "manifest_digest_mismatch"):
                verify_manifest(path)

    def test_one_late_wave_failure_produces_global_hold(self) -> None:
        result = run_controller(
            iteration_id="it-10", source_sha=SHA,
            waves=wave_jobs("it-10", {"W7": ResultState.FAILED}),
        )
        self.assertEqual(result.state, ResultState.HOLD)
        self.assertEqual(result.waves[-1].wave_id, "W7")

    def test_all_required_waves_pass_is_not_merge_authority(self) -> None:
        result = run_controller(iteration_id="it-11", source_sha=SHA, waves=wave_jobs("it-11"))
        self.assertEqual(result.state, ResultState.PASSED)
        self.assertNotEqual(result.state, ResultState.HOLD)
        self.assertFalse(hasattr(result, "merge"))

    def test_deterministic_manifests_are_byte_stable(self) -> None:
        with tempfile.TemporaryDirectory() as left, tempfile.TemporaryDirectory() as right:
            run_controller(iteration_id="it-12", source_sha=SHA, waves=wave_jobs("it-12"), locks=locks_for("it-12"), manifest_dir=left)
            run_controller(iteration_id="it-12", source_sha=SHA, waves=wave_jobs("it-12"), locks=locks_for("it-12"), manifest_dir=right)
            for wave in WAVES:
                self.assertEqual(
                    (Path(left) / f"aeos_autobot_it-12_{wave}.json").read_bytes(),
                    (Path(right) / f"aeos_autobot_it-12_{wave}.json").read_bytes(),
                )

    def test_execution_bounds_are_fail_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid_execution_bounds"):
            run_controller(
                iteration_id="it-13", source_sha=SHA, waves=wave_jobs("it-13"),
                limits=ControllerLimits(max_iterations=0),
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
