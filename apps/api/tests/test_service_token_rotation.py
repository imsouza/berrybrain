import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import ServiceTokenRecord
from berrybrain_api.security import (
    revoke_service_token,
    rotate_service_token,
    verify_service_token,
)
from berrybrain_api.routers.security_tokens import (
    RotateServiceTokenRequest,
    _require_owner,
    _serialize_token,
    list_service_tokens,
    revoke_token,
    rotate_token,
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

    def test_serialization_reports_expired_grace_without_mutating_record(self) -> None:
        now = datetime.now(UTC)
        record = ServiceTokenRecord(
            id=9,
            name="worker",
            token_hash="hash",
            status="grace",
            expires_at=(now - timedelta(seconds=1)).replace(tzinfo=None),
            last_used_at=now,
            created_at=now,
        )
        result = _serialize_token(record)
        self.assertEqual(result["status"], "expired")
        self.assertEqual(record.status, "grace")
        self.assertIsNotNone(result["expiresAt"])
        self.assertIsNotNone(result["lastUsedAt"])
        self.assertIsNotNone(result["createdAt"])

        active = ServiceTokenRecord(
            id=10, name="worker", token_hash="hash", status="active"
        )
        active_result = _serialize_token(active)
        self.assertEqual(active_result["status"], "active")
        self.assertIsNone(active_result["expiresAt"])

    @patch("berrybrain_api.routers.security_tokens.assert_csrf")
    @patch("berrybrain_api.routers.security_tokens.require_session_user")
    @patch("berrybrain_api.routers.security_tokens.get_settings")
    def test_owner_guard_enforces_owner_and_optional_csrf(
        self,
        get_settings: MagicMock,
        require_user: MagicMock,
        assert_csrf: MagicMock,
    ) -> None:
        settings = SimpleNamespace(admin_email="owner@example.com")
        get_settings.return_value = settings
        request = MagicMock()
        owner = SimpleNamespace(email="OWNER@example.com")
        session_record = MagicMock()
        require_user.return_value = (owner, session_record)

        self.assertIs(_require_owner(MagicMock(), request, require_csrf=True), owner)
        assert_csrf.assert_called_once_with(settings, request, session_record)

        assert_csrf.reset_mock()
        _require_owner(MagicMock(), request, require_csrf=False)
        assert_csrf.assert_not_called()

        require_user.return_value = (
            SimpleNamespace(email="other@example.com"),
            session_record,
        )
        with self.assertRaises(HTTPException) as denied:
            _require_owner(MagicMock(), request, require_csrf=False)
        self.assertEqual(denied.exception.status_code, 403)

    @patch("berrybrain_api.routers.security_tokens._require_owner")
    @patch("berrybrain_api.routers.security_tokens.SessionLocal")
    def test_list_route_serializes_persisted_tokens(
        self, session_local: MagicMock, require_owner: MagicMock
    ) -> None:
        record = ServiceTokenRecord(
            id=1, name="worker", token_hash="hash", status="active"
        )
        session = session_local.return_value.__enter__.return_value
        session.execute.return_value.scalars.return_value = [record]

        result = list_service_tokens(MagicMock())

        self.assertEqual(result["tokens"][0]["name"], "worker")
        require_owner.assert_called_once_with(
            session, unittest.mock.ANY, require_csrf=False
        )

    @patch("berrybrain_api.routers.security_tokens.audit_event")
    @patch("berrybrain_api.routers.security_tokens.rotate_service_token")
    @patch("berrybrain_api.routers.security_tokens._require_owner")
    @patch("berrybrain_api.routers.security_tokens.SessionLocal")
    def test_rotate_route_returns_secret_once_and_audits(
        self,
        session_local: MagicMock,
        require_owner: MagicMock,
        rotate: MagicMock,
        audit: MagicMock,
    ) -> None:
        owner = MagicMock(id=1)
        require_owner.return_value = owner
        record = ServiceTokenRecord(
            id=2, name="worker", token_hash="hash", status="active"
        )
        rotate.return_value = ("bbt_secret", record)

        result = rotate_token(
            RotateServiceTokenRequest(name="worker", grace_seconds=120), MagicMock()
        )

        self.assertEqual(result["token"], "bbt_secret")
        self.assertIn("shown once", result["warning"])
        rotate.assert_called_once()
        audit.assert_called_once()

    @patch("berrybrain_api.routers.security_tokens.audit_event")
    @patch("berrybrain_api.routers.security_tokens.revoke_service_token")
    @patch("berrybrain_api.routers.security_tokens._require_owner")
    @patch("berrybrain_api.routers.security_tokens.SessionLocal")
    def test_revoke_route_blocks_missing_and_last_active_token(
        self,
        session_local: MagicMock,
        require_owner: MagicMock,
        revoke: MagicMock,
        audit: MagicMock,
    ) -> None:
        session = session_local.return_value.__enter__.return_value
        session.get.return_value = None
        with self.assertRaises(HTTPException) as missing:
            revoke_token(7, MagicMock())
        self.assertEqual(missing.exception.status_code, 404)

        active = ServiceTokenRecord(
            id=7, name="worker", token_hash="hash", status="active"
        )
        session.get.return_value = active
        session.execute.return_value.scalars.return_value = [active]
        with self.assertRaises(HTTPException) as last_active:
            revoke_token(7, MagicMock())
        self.assertEqual(last_active.exception.status_code, 409)

        grace = ServiceTokenRecord(id=8, name="old", token_hash="old", status="grace")
        session.get.return_value = grace
        revoked = ServiceTokenRecord(
            id=8, name="old", token_hash="old", status="revoked"
        )
        revoke.return_value = revoked
        result = revoke_token(8, MagicMock())
        self.assertEqual(result["token"]["status"], "revoked")
        audit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
