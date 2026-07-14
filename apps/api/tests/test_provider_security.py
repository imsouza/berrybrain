import unittest

from berrybrain_api.provider_security import (
    provider_credential_fingerprint,
    provider_credential_matches,
)

SAMPLE_VALUE_A = "sample-value-alpha"
SAMPLE_VALUE_B = "sample-value-beta"


class ProviderSecurityTests(unittest.TestCase):
    def test_fingerprint_is_deterministic_without_exposing_credential(self) -> None:
        value = SAMPLE_VALUE_A
        fingerprint = provider_credential_fingerprint(value)

        self.assertEqual(fingerprint, provider_credential_fingerprint(value))
        self.assertNotEqual(fingerprint, value)
        self.assertNotIn(value, fingerprint)

    def test_match_rejects_changed_or_empty_credentials(self) -> None:
        fingerprint = provider_credential_fingerprint(SAMPLE_VALUE_A)

        self.assertTrue(provider_credential_matches(fingerprint, SAMPLE_VALUE_A))
        self.assertFalse(provider_credential_matches(fingerprint, SAMPLE_VALUE_B))
        self.assertFalse(provider_credential_matches("", SAMPLE_VALUE_A))
        self.assertFalse(provider_credential_matches(fingerprint, ""))


if __name__ == "__main__":
    unittest.main()
