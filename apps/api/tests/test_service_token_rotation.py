import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import ServiceTokenRecord
from berrybrain_api.security import (
    revoke_service_token,
    rotate_service_token,
    verify_service_token,
)


class ServiceTokenRotationTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()
        self.settings = SimpleNamespace(
            api_token="legacy-worker-token",
            session_secret="test-session-secret-with-enough-entropy",
        )

    def tearDown(self) -> None:
        self.session.close()

    def test_rotation_hashes_tokens_and_expires_legacy_grace_token(self) -> None:
        self.assertTrue(
            verify_service_token(self.session, self.settings, "legacy-worker-token")
        )
        raw_token, active = rotate_service_token(
            self.session, self.settings, name="worker", grace_seconds=60
        )
        self.assertTrue(raw_token.startswith("bbt_"))
        self.assertNotEqual(active.token_hash, raw_token)
        self.assertTrue(verify_service_token(self.session, self.settings, raw_token))
        self.assertTrue(
            verify_service_token(self.session, self.settings, "legacy-worker-token")
        )

        legacy = self.session.execute(
            select(ServiceTokenRecord).where(
                ServiceTokenRecord.name == "legacy-environment-token"
            )
        ).scalar_one()
        legacy.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        self.session.commit()
        self.assertFalse(
            verify_service_token(self.session, self.settings, "legacy-worker-token")
        )

        revoked = revoke_service_token(self.session, active.id)
        self.assertEqual(revoked.status, "revoked")
        self.assertFalse(verify_service_token(self.session, self.settings, raw_token))


if __name__ == "__main__":
    unittest.main()
