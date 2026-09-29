import unittest

from scripts.export_runtime_metrics import prometheus_metrics


class RuntimeMetricsTests(unittest.TestCase):
    def test_prometheus_output_is_stable_and_safe(self) -> None:
        output = prometheus_metrics(
            {
                "event_count": 3,
                "delivery_attempts": 4,
                "delivery_completed": 2,
                "delivery_failed": 1,
            }
        )
        self.assertIn("research_os_workflow_events_total 3", output)
        self.assertIn("research_os_event_delivery_attempts_total 4", output)
        self.assertIn('research_os_event_delivery_status{status="completed"} 2', output)
        self.assertIn('research_os_event_delivery_status{status="claimed"} 0', output)
        self.assertNotIn("secret", output.casefold())


if __name__ == "__main__":
    unittest.main()
