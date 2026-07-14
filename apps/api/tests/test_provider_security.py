import unittest

from berrybrain_api.provider_security import (
    provider_credential_fingerprint,
    provider_credential_matches,
)


class ProviderSecurityTests(unittest.TestCase):
    def test_fingerprint_is_deterministic_without_exposing_credential(self) -> None:
        credential = "provider-secret-value"
        fingerprint = provider_credential_fingerprint(credential)

        self.assertEqual(fingerprint, provider_credential_fingerprint(credential))
        self.assertNotEqual(fingerprint, credential)
        self.assertNotIn(credential, fingerprint)

    def test_match_rejects_changed_or_empty_credentials(self) -> None:
        fingerprint = provider_credential_fingerprint("correct-credential")

        self.assertTrue(provider_credential_matches(fingerprint, "correct-credential"))
        self.assertFalse(provider_credential_matches(fingerprint, "wrong-credential"))
        self.assertFalse(provider_credential_matches("", "correct-credential"))
        self.assertFalse(provider_credential_matches(fingerprint, ""))


if __name__ == "__main__":
    unittest.main()
