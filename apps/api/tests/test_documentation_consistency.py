import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.documentation_consistency import check_documentation_consistency


class DocumentationConsistencyTest(unittest.TestCase):
    def test_detects_current_and_stale_documentation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.json"
            report.write_text(
                json.dumps(
                    {
                        "generatedAt": "2026-08-12T13:07:12+00:00",
                        "profile": "S",
                        "graphOnDisk": {
                            "node_count": 500,
                            "edge_count": 1000,
                            "latency_p95_ms": 197.74,
                        },
                        "workerQueue": {"drain_rate_jobs_per_second": 12.0},
                        "httpLoad": {"requests": 100, "latency_p95_ms": 429.57},
                        "maturity": {
                            "readiness": "incomplete-evidence",
                            "minimum_level": 0,
                            "median_level": 2,
                        },
                    }
                ),
                encoding="utf-8",
            )
            current = root / "current.md"
            current.write_text(
                "12 August 2026 S 500 1,000 197.74 12.00 100 429.57 "
                "incomplete-evidence 0 2",
                encoding="utf-8",
            )
            self.assertEqual(check_documentation_consistency(report, (current,)), [])
            stale = root / "stale.md"
            stale.write_text("outdated", encoding="utf-8")
            self.assertTrue(check_documentation_consistency(report, (stale,)))


if __name__ == "__main__":
    unittest.main()
