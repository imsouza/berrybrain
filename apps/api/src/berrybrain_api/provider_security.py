from __future__ import annotations

import hashlib
import hmac

from berrybrain_api.config import get_settings


def provider_credential_fingerprint(credential: str) -> str:
    """Return an installation-bound fingerprint without storing credential material."""
    if not credential:
        return ""
    key = get_settings().session_secret.encode("utf-8")
    return hashlib.blake2b(
        credential.encode("utf-8"), key=key, digest_size=32
    ).hexdigest()


def provider_credential_matches(fingerprint: str, credential: str) -> bool:
    if not fingerprint or not credential:
        return False
    expected = provider_credential_fingerprint(credential)
    return hmac.compare_digest(fingerprint, expected)
