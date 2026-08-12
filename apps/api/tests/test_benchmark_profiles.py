import unittest

from benchmarks.benchmark_profiles import (
    ABLATION_PROFILES,
    SCALE_PROFILES,
    experiment_manifest,
)


class BenchmarkProfilesTest(unittest.TestCase):
    def test_defines_required_scale_and_ablation_matrix(self) -> None:
        self.assertEqual(set(SCALE_PROFILES), {"S", "M", "L", "XL"})
        self.assertEqual(
            set(ABLATION_PROFILES),
            {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "G0", "G1", "G2", "G3"},
        )

    def test_manifest_enforces_shared_experimental_controls(self) -> None:
        manifest = experiment_manifest("S", ("A0", "A3", "A6"))
        controls = manifest["sharedControls"]
        self.assertTrue(controls["corpusParityRequired"])
        self.assertTrue(controls["queryParityRequired"])
        self.assertTrue(controls["modelParityRequired"])
        self.assertEqual(len(manifest["ablations"]), 3)

    def test_rejects_unknown_or_invalid_profiles(self) -> None:
        with self.assertRaises(ValueError):
            experiment_manifest("unknown", ("A0",))
        with self.assertRaises(ValueError):
            experiment_manifest("S", ("unknown",))
        with self.assertRaises(ValueError):
            experiment_manifest("S", ("A0",), cache_mode="sometimes")


if __name__ == "__main__":
    unittest.main()
