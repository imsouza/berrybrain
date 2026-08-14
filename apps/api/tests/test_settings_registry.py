import unittest

from berrybrain_api.settings_registry import validate_public_setting


class SettingsRegistryTest(unittest.TestCase):
    def test_accepts_onboarding_completion_flag(self) -> None:
        self.assertEqual(
            validate_public_setting("onboarding_completed", "true"), "true"
        )

    def test_known_values_are_normalized(self) -> None:
        self.assertEqual(validate_public_setting("lang", "en"), "en")
        self.assertEqual(
            validate_public_setting("graph_min_shared_concepts", " 3 "), "3"
        )
        self.assertEqual(
            validate_public_setting("qdrant_url", "https://vector.example.test"),
            "https://vector.example.test",
        )

    def test_unknown_or_invalid_values_are_rejected(self) -> None:
        for key, value in (
            ("unregistered_key", "value"),
            ("lang", "pt"),
            ("graph_min_shared_concepts", "1"),
            ("qdrant_url", "file:///tmp/vector"),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_public_setting(key, value)


if __name__ == "__main__":
    unittest.main()
