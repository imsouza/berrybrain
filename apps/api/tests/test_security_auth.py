import os
import tempfile
import unittest
from importlib import import_module
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

os.environ["BERRYBRAIN_VAULT_WATCHER_ENABLED"] = "false"


class SecurityAuthTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(cls.tmp_dir.name) / "security.db"
        vault_path = Path(cls.tmp_dir.name) / "vault"
        vault_path.mkdir()

        from berrybrain_api.config import get_settings
        from berrybrain_api.database import Base
        import berrybrain_api.database as db_mod
        import berrybrain_api.models  # noqa: F401

        cls.settings = get_settings()
        cls.original = {
            "database_url": cls.settings.database_url,
            "vault_path": cls.settings.vault_path,
            "vault_watcher_enabled": cls.settings.vault_watcher_enabled,
            "api_token": cls.settings.api_token,
            "session_secret": cls.settings.session_secret,
            "session_secure_cookie": cls.settings.session_secure_cookie,
            "smtp_host": cls.settings.smtp_host,
            "admin_email": cls.settings.admin_email,
            "owner_username": cls.settings.owner_username,
        }
        cls.settings.database_url = f"sqlite:///{db_path}"
        cls.settings.vault_path = vault_path
        cls.settings.vault_watcher_enabled = False
        cls.settings.api_token = ""
        cls.settings.session_secret = "test-secret"
        cls.settings.session_secure_cookie = False
        cls.settings.smtp_host = ""
        cls.settings.admin_email = "admin@example.com"
        cls.settings.owner_username = "admin"

        cls.original_engine = db_mod.engine
        cls.original_session_local = db_mod.SessionLocal
        new_engine = create_engine(
            cls.settings.database_url, connect_args={"check_same_thread": False}
        )
        cls.new_engine = new_engine
        db_mod.engine = new_engine
        db_mod.SessionLocal = sessionmaker(
            bind=new_engine, autoflush=False, autocommit=False
        )
        Base.metadata.create_all(bind=new_engine)

        cls.patched = []
        for module_name in ("berrybrain_api.main", "berrybrain_api.routers.auth"):
            module = import_module(module_name)
            if hasattr(module, "SessionLocal"):
                cls.patched.append(module)
                module.SessionLocal = db_mod.SessionLocal
        cls.client = TestClient(import_module("berrybrain_api.main").app)

    @classmethod
    def tearDownClass(cls) -> None:
        import berrybrain_api.database as db_mod

        db_mod.engine = cls.original_engine
        db_mod.SessionLocal = cls.original_session_local
        for module in cls.patched:
            module.SessionLocal = cls.original_session_local
        cls.client.close()
        cls.new_engine.dispose()
        for key, value in cls.original.items():
            setattr(cls.settings, key, value)
        cls.tmp_dir.cleanup()

    def test_security_headers_are_present(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")

    def test_signup_is_disabled_for_self_hosted_instances(self) -> None:
        response = self.client.post(
            "/api/v1/auth/signup",
            json={
                "email": "new@example.com",
                "password": "StrongPass123",
                "display_name": "New User",
            },
        )
        self.assertEqual(response.status_code, 410)

    def test_setup_creates_admin_once_and_logs_in(self) -> None:
        previous = self.settings.admin_email
        self.settings.admin_email = "setup-admin@example.com"
        try:
            status = self.client.get("/api/v1/setup/status")
            self.assertEqual(status.status_code, 200)
            self.assertTrue(status.json()["needsSetup"])
            self.assertEqual(status.json()["ownerUsername"], "admin")
            self.assertEqual(status.json()["adminEmail"], "setup-admin@example.com")

            created = self.client.post(
                "/api/v1/setup/admin",
                json={
                    "password": "StrongPass123",
                    "display_name": "Setup Admin",
                },
            )
            self.assertEqual(created.status_code, 201)
            self.assertEqual(created.json()["status"], "configured")
            self.assertIn("bb_session", created.cookies)

            configured_status = self.client.get("/api/v1/setup/status")
            self.assertFalse(configured_status.json()["needsSetup"])
            self.assertEqual(configured_status.json()["adminEmail"], "")

            duplicate = self.client.post(
                "/api/v1/setup/admin",
                json={
                    "password": "StrongPass123",
                    "display_name": "Setup Admin",
                },
            )
            self.assertEqual(duplicate.status_code, 409)
        finally:
            self.settings.admin_email = previous

    def test_login_uses_generic_error_for_missing_user(self) -> None:
        response = self.client.post(
            "/api/v1/auth/login",
            json={"email": "missing@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            response.json()["detail"], "Invalid username/email or password"
        )

    def test_owner_can_login_with_configured_username_alias(self) -> None:
        app = import_module("berrybrain_api.main").app
        self._create_user("admin@example.com")
        previous = self.settings.owner_username
        self.settings.owner_username = "brain-owner"
        try:
            client = TestClient(app)
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "brain-owner",
                    "password": "StrongPass123",
                    "remember_me": False,
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], "authenticated")
            self.assertEqual(response.json()["user"]["email"], "admin@example.com")
        finally:
            self.settings.owner_username = previous

    def test_login_respects_remember_me_cookie_lifetime(self) -> None:
        app = import_module("berrybrain_api.main").app
        self._create_user("session-only@example.com")

        session_client = TestClient(app)
        session_login = session_client.post(
            "/api/v1/auth/login",
            json={
                "email": "session-only@example.com",
                "password": "StrongPass123",
                "remember_me": False,
            },
        )
        self.assertEqual(session_login.status_code, 200)
        session_cookies = session_login.headers.get_list("set-cookie")
        self.assertTrue(any("bb_session=" in value for value in session_cookies))
        self.assertFalse(any("Max-Age=" in value for value in session_cookies))

        persistent_client = TestClient(app)
        persistent_login = persistent_client.post(
            "/api/v1/auth/login",
            json={
                "email": "session-only@example.com",
                "password": "StrongPass123",
                "remember_me": True,
            },
        )
        self.assertEqual(persistent_login.status_code, 200)
        persistent_cookies = persistent_login.headers.get_list("set-cookie")
        self.assertTrue(any("Max-Age=2592000" in value for value in persistent_cookies))

    def _create_user(
        self,
        email: str,
        password: str = "StrongPass123",
        *,
        verified: bool = True,
        two_factor: bool = False,
    ) -> None:
        from berrybrain_api.database import SessionLocal
        from berrybrain_api.models import UserRecord
        from berrybrain_api.security import hash_password, normalize_email

        email = normalize_email(email)
        with SessionLocal() as session:
            user = session.execute(
                select(UserRecord).where(UserRecord.email == email)
            ).scalar_one_or_none()
            if user is None:
                user = UserRecord(email=email, display_name=email.split("@", 1)[0])
                session.add(user)
            user.password_hash = hash_password(password, self.settings.session_secret)
            user.email_verified = verified
            user.two_factor_enabled = two_factor
            user.locked_until = None
            user.force_password_reset = False
            user.failed_login_count = 0
            session.commit()

    def test_admin_requires_session_and_configured_email(self) -> None:
        app = import_module("berrybrain_api.main").app
        unauthenticated = TestClient(app)
        denied = unauthenticated.get("/api/v1/admin/users")
        self.assertEqual(denied.status_code, 401)

        self._create_user("user@example.com")
        user_client = TestClient(app)
        login = user_client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json()["status"], "authenticated")
        forbidden = user_client.get("/api/v1/admin/users")
        self.assertEqual(forbidden.status_code, 403)

        self._create_user("admin@example.com")
        admin_client = TestClient(app)
        admin_login = admin_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(admin_login.status_code, 200)
        allowed = admin_client.get("/api/v1/admin/users")
        self.assertEqual(allowed.status_code, 200)
        self.assertIn("users", allowed.json())

    def test_admin_mutation_requires_explicit_csrf_header(self) -> None:
        app = import_module("berrybrain_api.main").app
        self._create_user("admin@example.com")
        self._create_user("target@example.com")

        admin_client = TestClient(app)
        login = admin_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(login.status_code, 200)
        csrf = login.json()["csrfToken"]

        users = admin_client.get("/api/v1/admin/users").json()["users"]
        target_id = next(
            user["id"] for user in users if user["email"] == "target@example.com"
        )

        missing_header = admin_client.post(
            f"/api/v1/admin/users/{target_id}/lock",
            json={"reason": "test"},
        )
        self.assertEqual(missing_header.status_code, 403)

        allowed = admin_client.post(
            f"/api/v1/admin/users/{target_id}/lock",
            json={"reason": "test"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(allowed.status_code, 200)

    def test_admin_profile_crud_requires_admin_and_csrf(self) -> None:
        app = import_module("berrybrain_api.main").app
        self._create_user("admin@example.com")

        unauthenticated = TestClient(app)
        denied = unauthenticated.get("/api/v1/admin/profiles")
        self.assertEqual(denied.status_code, 401)

        admin_client = TestClient(app)
        login = admin_client.post(
            "/api/v1/auth/login",
            json={"email": "admin@example.com", "password": "StrongPass123"},
        )
        self.assertEqual(login.status_code, 200)
        csrf = login.json()["csrfToken"]

        missing_csrf = admin_client.post(
            "/api/v1/admin/profiles",
            json={"name": "Research", "slug": "research", "vault_subpath": "research"},
        )
        self.assertEqual(missing_csrf.status_code, 403)

        created = admin_client.post(
            "/api/v1/admin/profiles",
            json={"name": "Research", "slug": "research", "vault_subpath": "research"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(created.status_code, 201)
        profile_id = created.json()["profile"]["id"]

        duplicate = admin_client.post(
            "/api/v1/admin/profiles",
            json={"name": "Research 2", "slug": "research", "vault_subpath": ""},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(duplicate.status_code, 409)

        archived = admin_client.post(
            f"/api/v1/admin/profiles/{profile_id}/archive",
            json={"reason": "test"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(archived.status_code, 200)
        self.assertEqual(archived.json()["profile"]["status"], "archived")


if __name__ == "__main__":
    unittest.main()
