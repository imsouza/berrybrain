import json
import tempfile
import unittest
from dataclasses import asdict
from pathlib import Path

from benchmarks.evidence import (
    bootstrap_interval,
    checksum_json,
    create_manifest,
    paired_bootstrap_difference,
    percentile,
    write_evidence_bundle,
)


class BenchmarkEvidenceTest(unittest.TestCase):
    def test_statistics_are_deterministic_and_paired(self) -> None:
        self.assertEqual(percentile([1, 2, 3, 4], 0.5), 2.5)
        interval = bootstrap_interval([1, 2, 3, 4], resamples=500, seed=7)
        self.assertEqual(interval.samples, 4)
        self.assertLess(interval.lower, interval.upper)
        difference = paired_bootstrap_difference(
            [0.8, 0.9, 1.0], [0.5, 0.6, 0.7], resamples=500, seed=7
        )
        self.assertGreater(difference.lower, 0)

    def test_manifest_and_bundle_capture_reproducibility_data(self) -> None:
        dataset = {"queries": [{"id": "q1", "expected": ["n1"]}]}
        manifest = create_manifest(
            "unit-evidence",
            dataset=dataset,
            configuration={"mode": "test"},
            classification="ci-regression",
            seed=17,
        )
        self.assertEqual(manifest.dataset_checksum, checksum_json(dataset))
        self.assertEqual(manifest.random_seed, 17)
        with tempfile.TemporaryDirectory() as directory:
            run_dir = write_evidence_bundle(
                Path(directory),
                manifest,
                summary={"passed": True, "manifest": asdict(manifest)},
                observations=[{"queryId": "q1", "latencyMs": 1.2}],
            )
            self.assertTrue((run_dir / "checksums.txt").is_file())
            rows = (run_dir / "raw" / "observations.jsonl").read_text().splitlines()
            self.assertEqual(json.loads(rows[0])["queryId"], "q1")


if __name__ == "__main__":
    unittest.main()
