from __future__ import annotations

import unittest

from research_os_v3.delay import GeneratedDelay


class GeneratedDelayTests(unittest.TestCase):
    def test_generated_value_is_slept_once_and_reused(self) -> None:
        sleeps: list[float] = []
        delay = GeneratedDelay(0.25)

        observed = delay.sleep(sleeps.append)

        self.assertEqual([0.25], sleeps)
        self.assertEqual(0.25, observed)
        self.assertEqual(0.25, delay.value())

    def test_negative_delay_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            GeneratedDelay(-0.01)

    def test_zero_delay_is_valid(self) -> None:
        sleeps: list[float] = []
        delay = GeneratedDelay(0.0)
        self.assertEqual(0.0, delay.sleep(sleeps.append))
        self.assertEqual([0.0], sleeps)


if __name__ == "__main__":
    unittest.main()
