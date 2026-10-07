import unittest
from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from berrybrain_api.config import Settings
from berrybrain_api.database import Base
from berrybrain_api.models import ServiceTokenRecord
from berrybrain_api.security import (
    issue_service_token,
    rotate_service_token,
    verify_service_token,
)


class ServiceTokenLifecycleTest(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        self.addCleanup(engine.dispose)
        Base.metadata.create_all(engine)
        self.session = Session(engine)
        self.addCleanup(self.session.close)
        self.settings = Settings(
            _env_file=None,
            api_token="bootstrap-fixture",
            session_secret="fixture-session-secret-for-token-tests",
        )

    def test_global_rotation_never_revives_expired_credentials(self):
        raw, record = issue_service_token(
            self.session, self.settings, name="Old integration"
        )
        record.expires_at = datetime.now(UTC) - timedelta(days=1)
        self.session.commit()
        replacement, _ = rotate_service_token(self.session, self.settings)
        self.assertFalse(verify_service_token(self.session, self.settings, raw))
        self.assertTrue(verify_service_token(self.session, self.settings, replacement))
        self.assertTrue(
            verify_service_token(self.session, self.settings, self.settings.api_token)
        )

    def test_multiple_integrations_preserve_one_bootstrap_credential(self):
        tokens = [
            issue_service_token(self.session, self.settings, name=f"Application {n}")[0]
            for n in range(4)
        ]
        records = list(self.session.scalars(select(ServiceTokenRecord)))
        self.assertEqual(len(records), 5)
        self.assertEqual(sum(r.name == "legacy-environment-token" for r in records), 1)
        for token in [*tokens, self.settings.api_token]:
            self.assertTrue(verify_service_token(self.session, self.settings, token))
