import unittest

from benchmarks.worker_queue_benchmark import run_worker_queue_benchmark


class WorkerQueueBenchmarkTest(unittest.TestCase):
    def test_drains_jobs_through_production_queue_functions(self) -> None:
        metrics, observations = run_worker_queue_benchmark(jobs=12)

        self.assertEqual(metrics.jobs, 12)
        self.assertEqual(metrics.completed_jobs, 12)
        self.assertEqual(metrics.remaining_jobs, 0)
        self.assertEqual(metrics.duplicate_claims, 0)
        self.assertGreater(metrics.enqueue_rate_jobs_per_second, 0)
        self.assertGreater(metrics.drain_rate_jobs_per_second, 0)
        self.assertEqual(len(observations), 12)

    def test_rejects_empty_workload(self) -> None:
        with self.assertRaises(ValueError):
            run_worker_queue_benchmark(jobs=0)


if __name__ == "__main__":
    unittest.main()
