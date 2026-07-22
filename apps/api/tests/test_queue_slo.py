import unittest
from datetime import UTC, datetime, timedelta

from berrybrain_api.modules.jobs.domain import (
    QueueJobSnapshot,
    QueueSloPolicy,
    evaluate_queue_slo,
)


class QueueSloDomainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
        self.policy = QueueSloPolicy(
            pending_warning_seconds=60,
            pending_breach_seconds=120,
            running_breach_seconds=180,
        )

    def test_empty_and_fresh_queues_are_healthy(self) -> None:
        self.assertEqual(
            evaluate_queue_slo([], now=self.now, policy=self.policy).status,
            "healthy",
        )
        report = evaluate_queue_slo(
            [QueueJobSnapshot("pending", self.now - timedelta(seconds=30))],
            now=self.now,
            policy=self.policy,
        )
        self.assertEqual(report.status, "healthy")
        self.assertEqual(report.oldest_pending_age_seconds, 30)

    def test_pending_age_has_warning_and_breach_states(self) -> None:
        warning = evaluate_queue_slo(
            [QueueJobSnapshot("pending", self.now - timedelta(seconds=90))],
            now=self.now,
            policy=self.policy,
        )
        self.assertEqual(warning.status, "at_risk")
        self.assertEqual(warning.violations[0].code, "pending_age_warning")

        breached = evaluate_queue_slo(
            [QueueJobSnapshot("pending", self.now - timedelta(seconds=150))],
            now=self.now,
            policy=self.policy,
        )
        self.assertEqual(breached.status, "breached")
        self.assertEqual(breached.violations[0].code, "pending_age_breached")

    def test_dead_letters_and_stale_running_jobs_are_actionable(self) -> None:
        report = evaluate_queue_slo(
            [
                QueueJobSnapshot("dead_letter", self.now),
                QueueJobSnapshot(
                    "running",
                    self.now - timedelta(minutes=10),
                    self.now - timedelta(seconds=181),
                ),
            ],
            now=self.now,
            policy=self.policy,
        )
        self.assertEqual(report.status, "breached")
        self.assertEqual(report.dead_letter_count, 1)
        self.assertEqual(report.stale_running_count, 1)
        self.assertEqual(
            {violation.code for violation in report.violations},
            {"dead_letters_present", "running_jobs_stale"},
        )

    def test_serialized_report_exposes_policy_without_job_payloads(self) -> None:
        payload = evaluate_queue_slo([], now=self.now, policy=self.policy).to_dict()
        self.assertEqual(payload["status"], "healthy")
        self.assertEqual(payload["policy"]["pendingBreachSeconds"], 120)
        self.assertNotIn("jobs", payload)


if __name__ == "__main__":
    unittest.main()
