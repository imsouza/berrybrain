import unittest

from benchmarks.analysis_report import build_analysis_artifacts


class AnalysisReportTest(unittest.TestCase):
    def test_generates_captioned_table_and_chart_with_provenance(self) -> None:
        report = {
            "profile": "S",
            "classification": "exploratory",
            "generatedAt": "2026-08-12T13:07:12+00:00",
            "releaseGate": {
                "retrieval_ablation": {
                    "ablations": [
                        {
                            "configuration": "graph_hybrid",
                            "recall_at_10": 1.0,
                            "mean_reciprocal_rank": 1.0,
                            "ndcg_at_10": 1.0,
                            "latency_p95_ms": 20.0,
                        }
                    ]
                }
            },
            "graphOnDisk": {
                "node_count": 500,
                "edge_count": 1000,
                "latency_p95_ms": 200.0,
                "payload_bytes": 100,
                "peak_memory_bytes": 200,
            },
            "workerQueue": {
                "enqueue_rate_jobs_per_second": 10.0,
                "drain_rate_jobs_per_second": 9.0,
                "end_to_end_p95_ms": 100.0,
                "duplicate_claims": 0,
            },
            "httpLoad": None,
            "maturity": {
                "readiness": "incomplete-evidence",
                "minimum_level": 0,
                "median_level": 2,
            },
        }
        markdown, chart = build_analysis_artifacts(report)
        self.assertIn("Caption", markdown)
        self.assertIn("Provenance", markdown)
        self.assertIn("graph_hybrid", markdown)
        self.assertEqual(chart["usermeta"]["classification"], "exploratory")
        self.assertEqual(chart["data"]["values"][0]["recallAt10"], 1.0)


if __name__ == "__main__":
    unittest.main()
