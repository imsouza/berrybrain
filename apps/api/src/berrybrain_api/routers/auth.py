from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import SecurityAuditRecord, UserRecord, UserSessionRecord
from berrybrain_api.security import (
    assert_csrf,
    assert_rate_limit,
    audit_event,
    create_otp,
    create_user_session,
    hash_password,
    normalize_email,
    record_attempt,
    require_session_user,
    revoke_sessions,
    send_otp_email,
    validate_email,
    validate_password,
    verify_otp,
    verify_password,
)

router = APIRouter(prefix="/api/v1", tags=["auth"])


class SignupRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=256)
    display_name: str = Field(default="", max_length=160)


class LoginRequest(BaseModel):
    email: str
    password: str


class VerifyEmailRequest(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=12)


class VerifyTwoFactorRequest(BaseModel):
    email: str
    challenge_id: str = Field(min_length=16, max_length=160)
    code: str = Field(min_length=6, max_length=12)
    remember_me: bool = True


class ResetRequest(BaseModel):
    email: str


class ResetConfirmRequest(BaseModel):
    email: str
    code: str = Field(min_length=6, max_length=12)
    password: str = Field(min_length=12, max_length=256)


class AdminUserAction(BaseModel):
    reason: str = Field(default="", max_length=300)


class AdminUserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=256)
    display_name: str = Field(default="", max_length=160)
    email_verified: bool = True
    two_factor_enabled: bool = False


class AdminUserUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    email_verified: bool | None = None
    two_factor_enabled: bool | None = None


class AdminSetPassword(BaseModel):
    password: str = Field(min_length=12, max_length=256)


class UpdateProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=160)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class ChangeEmailRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)
    email: str = Field(min_length=3, max_length=255)


class TwoFactorRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)
    enabled: bool


class DeleteAccountConfirm(BaseModel):
    code: str = Field(min_length=6, max_length=12)


def _serialize_user(user: UserRecord) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "emailVerified": user.email_verified,
        "twoFactorEnabled": user.two_factor_enabled,
        "lockedUntil": user.locked_until.isoformat() if user.locked_until else None,
        "forcePasswordReset": user.force_password_reset,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "lastLoginAt": user.last_login_at.isoformat() if user.last_login_at else None,
    }


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _set_auth_cookies(
    response: Response, session_token: str, csrf_token: str, remember_me: bool = True
) -> None:
    settings = get_settings()
    max_age = 30 * 24 * 60 * 60 if remember_me else None
    response.set_cookie(
        settings.session_cookie_name,
        session_token,
        httponly=True,
        secure=settings.session_secure_cookie,
        samesite="lax",
        max_age=max_age,
        path="/",
    )
    response.set_cookie(
        settings.csrf_cookie_name,
        csrf_token,
        httponly=False,
        secure=settings.session_secure_cookie,
        samesite="lax",
        max_age=max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(settings.session_cookie_name, path="/")
    response.delete_cookie(settings.csrf_cookie_name, path="/")


@router.post("/auth/signup", status_code=201)
def signup(payload: SignupRequest, request: Request) -> dict:
    settings = get_settings()
    email = validate_email(payload.email)
    validate_password(payload.password)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "signup", email)
        existing = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if existing is not None:
            record_attempt(session, request, "signup", email, False, "existing")
            code, _challenge = create_otp(
                session, settings, existing, email, "email_verification"
            )
            delivery = send_otp_email(settings, email, code, "email_verification")
            session.commit()
            # Mirror the fresh-signup response exactly (no 409) so
            # signup cannot enumerate accounts. Re-issues a verification OTP to
            # the address instead of revealing that it already exists.
            return {"status": "verification_required", "delivery": delivery["status"]}
        user = UserRecord(
            email=email,
            display_name=payload.display_name.strip(),
            password_hash=hash_password(payload.password, settings.session_secret),
            email_verified=False,
            two_factor_enabled=True,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        code, _challenge = create_otp(
            session, settings, user, email, "email_verification"
        )
        delivery = send_otp_email(settings, email, code, "email_verification")
        record_attempt(session, request, "signup", email, True)
        audit_event(
            session,
            request,
            "SIGNUP_CREATED",
            user,
            "user",
            str(user.id),
            {"delivery": delivery["status"]},
        )
        return {"status": "verification_required", "delivery": delivery["status"]}


@router.post("/auth/verify-email")
def verify_email(
    payload: VerifyEmailRequest, request: Request, response: Response
) -> dict:
    settings = get_settings()
    email = validate_email(payload.email)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "verify_email", email)
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if user is None:
            record_attempt(session, request, "verify_email", email, False, "not_found")
            raise HTTPException(status_code=400, detail="Invalid or expired code")
        verify_otp(session, settings, email, "email_verification", payload.code)
        user.email_verified = True
        user.updated_at = datetime.now(UTC)
        session.commit()
        record_attempt(session, request, "verify_email", email, True)
        audit_event(session, request, "EMAIL_VERIFIED", user, "user", str(user.id))
        # ponytail: email verification already proved possession; auto-login
        # so signup does not bounce to /login for a second 2FA prompt.
        session_token, csrf_token, _session = create_user_session(
            session, settings, request, user, remember_me=True
        )
        _set_auth_cookies(response, session_token, csrf_token, remember_me=True)
        return {
            "status": "authenticated",
            "user": _serialize_user(user),
            "csrfToken": csrf_token,
        }


@router.post("/auth/login")
def login(payload: LoginRequest, request: Request, response: Response) -> dict:
    settings = get_settings()
    email = normalize_email(payload.email)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "login", email)
        generic_error = HTTPException(
            status_code=401, detail="Invalid email or password"
        )
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if user is None:
            record_attempt(session, request, "login", email, False, "not_found")
            raise generic_error
        locked_until = _as_utc(user.locked_until)
        if locked_until and locked_until > datetime.now(UTC):
            record_attempt(session, request, "login", email, False, "locked")
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        if not verify_password(
            payload.password, user.password_hash, settings.session_secret
        ):
            user.failed_login_count += 1
            if user.failed_login_count >= 5:
                user.locked_until = datetime.now(UTC) + timedelta(
                    minutes=settings.auth_lockout_minutes
                )
            session.commit()
            record_attempt(session, request, "login", email, False, "bad_password")
            raise generic_error
        if not user.email_verified:
            code, _challenge = create_otp(
                session, settings, user, email, "email_verification"
            )
            delivery = send_otp_email(settings, email, code, "email_verification")
            record_attempt(session, request, "login", email, False, "email_unverified")
            return {"status": "verification_required", "delivery": delivery["status"]}
        if user.two_factor_enabled:
            code, challenge = create_otp(session, settings, user, email, "login_2fa")
            delivery = send_otp_email(settings, email, code, "login_2fa")
            record_attempt(session, request, "login", email, True)
            audit_event(
                session,
                request,
                "LOGIN_2FA_SENT",
                user,
                "user",
                str(user.id),
                {"delivery": delivery["status"]},
            )
            return {
                "status": "2fa_required",
                "challengeId": challenge,
                "delivery": delivery["status"],
            }
        session_token, csrf_token, _session = create_user_session(
            session, settings, request, user, remember_me=True
        )
        _set_auth_cookies(response, session_token, csrf_token, remember_me=True)
        record_attempt(session, request, "login", email, True)
        audit_event(session, request, "LOGIN_COMPLETED", user, "user", str(user.id))
        return {
            "status": "authenticated",
            "user": _serialize_user(user),
            "csrfToken": csrf_token,
        }


@router.post("/auth/verify-2fa")
def verify_2fa(
    payload: VerifyTwoFactorRequest, request: Request, response: Response
) -> dict:
    settings = get_settings()
    email = validate_email(payload.email)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "verify_2fa", email)
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if user is None:
            record_attempt(session, request, "verify_2fa", email, False, "not_found")
            raise HTTPException(status_code=400, detail="Invalid or expired code")
        verify_otp(
            session, settings, email, "login_2fa", payload.code, payload.challenge_id
        )
        session_token, csrf_token, _session = create_user_session(
            session, settings, request, user, remember_me=payload.remember_me
        )
        _set_auth_cookies(
            response, session_token, csrf_token, remember_me=payload.remember_me
        )
        record_attempt(session, request, "verify_2fa", email, True)
        audit_event(session, request, "LOGIN_COMPLETED", user, "user", str(user.id))
        return {
            "status": "authenticated",
            "user": _serialize_user(user),
            "csrfToken": csrf_token,
        }


@router.get("/auth/me")
def me(request: Request) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        is_admin = normalize_email(user.email) == normalize_email(settings.admin_email)
        return {
            "user": _serialize_user(user),
            "sessionId": session_record.id,
            "isAdmin": is_admin,
        }


@router.post("/auth/logout")
def logout(request: Request, response: Response) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        result = require_session_user(session, settings, request)
        user, session_record = result
        assert_csrf(settings, request, session_record)
        session_record.revoked_at = datetime.now(UTC)
        session.commit()
        audit_event(session, request, "LOGOUT", user, "session", str(session_record.id))
    _clear_auth_cookies(response)
    return {"status": "logged_out"}


@router.post("/auth/logout-all")
def logout_all(request: Request, response: Response) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        count = revoke_sessions(session, user.id)
        audit_event(
            session,
            request,
            "LOGOUT_ALL",
            user,
            "user",
            str(user.id),
            {"revoked": count},
        )
    _clear_auth_cookies(response)
    return {"status": "logged_out", "revokedSessions": count}


@router.post("/auth/password-reset/request")
def request_password_reset(payload: ResetRequest, request: Request) -> dict:
    settings = get_settings()
    email = normalize_email(payload.email)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "password_reset", email)
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if user is not None:
            code, _challenge = create_otp(
                session, settings, user, email, "password_reset"
            )
            delivery = send_otp_email(settings, email, code, "password_reset")
            audit_event(
                session,
                request,
                "PASSWORD_RESET_REQUESTED",
                user,
                "user",
                str(user.id),
                {"delivery": delivery["status"]},
            )
        record_attempt(session, request, "password_reset", email, True)
        return {"status": "if_account_exists_email_sent"}


@router.post("/auth/password-reset/confirm")
def confirm_password_reset(payload: ResetConfirmRequest, request: Request) -> dict:
    settings = get_settings()
    email = validate_email(payload.email)
    validate_password(payload.password)
    with SessionLocal() as session:
        assert_rate_limit(session, request, settings, "password_reset_confirm", email)
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if user is None:
            record_attempt(
                session, request, "password_reset_confirm", email, False, "not_found"
            )
            raise HTTPException(status_code=400, detail="Invalid or expired code")
        verify_otp(session, settings, email, "password_reset", payload.code)
        user.password_hash = hash_password(payload.password, settings.session_secret)
        user.force_password_reset = False
        user.failed_login_count = 0
        user.locked_until = None
        user.updated_at = datetime.now(UTC)
        revoked = revoke_sessions(session, user.id)
        session.commit()
        record_attempt(session, request, "password_reset_confirm", email, True)
        audit_event(
            session,
            request,
            "PASSWORD_RESET_COMPLETED",
            user,
            "user",
            str(user.id),
            {"revokedSessions": revoked},
        )
        return {"status": "password_reset"}


@router.patch("/auth/me")
def update_own_profile(payload: UpdateProfileRequest, request: Request) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        user.display_name = payload.display_name.strip()
        user.updated_at = datetime.now(UTC)
        session.commit()
        audit_event(session, request, "PROFILE_UPDATED", user, "user", str(user.id))
        return {"user": _serialize_user(user)}


@router.post("/auth/change-password")
def change_own_password(
    payload: ChangePasswordRequest, request: Request, response: Response
) -> dict:
    settings = get_settings()
    validate_password(payload.new_password)
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        if not verify_password(
            payload.current_password, user.password_hash, settings.session_secret
        ):
            record_attempt(
                session, request, "change_password", user.email, False, "bad_password"
            )
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        user.password_hash = hash_password(
            payload.new_password, settings.session_secret
        )
        user.force_password_reset = False
        user.updated_at = datetime.now(UTC)
        revoke_sessions(session, user.id)
        session_token, csrf_token, _record = create_user_session(
            session, settings, request, user
        )
        audit_event(session, request, "PASSWORD_CHANGED", user, "user", str(user.id))
    _set_auth_cookies(response, session_token, csrf_token)
    return {"status": "password_changed", "csrfToken": csrf_token}


@router.post("/auth/change-email")
def change_own_email(
    payload: ChangeEmailRequest, request: Request, response: Response
) -> dict:
    settings = get_settings()
    new_email = validate_email(payload.email)
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        if not verify_password(
            payload.password, user.password_hash, settings.session_secret
        ):
            record_attempt(
                session, request, "change_email", user.email, False, "bad_password"
            )
            raise HTTPException(status_code=400, detail="Password is incorrect")
        if normalize_email(user.email) == normalize_email(settings.admin_email):
            raise HTTPException(
                status_code=400, detail="Cannot change the admin account email"
            )
        if new_email != user.email:
            clash = session.execute(
                select(UserRecord).where(UserRecord.email == new_email)
            ).scalar_one_or_none()
            if clash is not None:
                raise HTTPException(status_code=409, detail="Email already in use")
        user.email = new_email
        user.updated_at = datetime.now(UTC)
        revoke_sessions(session, user.id)
        session_token, csrf_token, _record = create_user_session(
            session, settings, request, user
        )
        audit_event(session, request, "EMAIL_CHANGED", user, "user", str(user.id))
    _set_auth_cookies(response, session_token, csrf_token)
    return {"status": "email_changed", "csrfToken": csrf_token}


@router.post("/auth/2fa")
def set_own_two_factor(payload: TwoFactorRequest, request: Request) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        if not verify_password(
            payload.password, user.password_hash, settings.session_secret
        ):
            raise HTTPException(status_code=400, detail="Password is incorrect")
        user.two_factor_enabled = payload.enabled
        user.updated_at = datetime.now(UTC)
        session.commit()
        audit_event(
            session,
            request,
            "TWO_FACTOR_UPDATED",
            user,
            "user",
            str(user.id),
            {"enabled": payload.enabled},
        )
        return {"user": _serialize_user(user)}


@router.post("/auth/delete-account/request")
def request_account_deletion(request: Request) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        if normalize_email(user.email) == normalize_email(settings.admin_email):
            raise HTTPException(
                status_code=400, detail="The admin account cannot be deleted"
            )
        code, _challenge = create_otp(
            session, settings, user, user.email, "account_delete"
        )
        delivery = send_otp_email(settings, user.email, code, "account_delete")
        audit_event(
            session,
            request,
            "ACCOUNT_DELETE_REQUESTED",
            user,
            "user",
            str(user.id),
            {"delivery": delivery["status"]},
        )
        return {"status": "verification_required", "delivery": delivery["status"]}


@router.post("/auth/delete-account/confirm")
def confirm_account_deletion(
    payload: DeleteAccountConfirm, request: Request, response: Response
) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        assert_csrf(settings, request, session_record)
        if normalize_email(user.email) == normalize_email(settings.admin_email):
            raise HTTPException(
                status_code=400, detail="The admin account cannot be deleted"
            )
        verify_otp(session, settings, user.email, "account_delete", payload.code)
        email = user.email
        user_id = user.id
        revoke_sessions(session, user_id)
        session.delete(user)
        session.commit()
        audit_event(
            session,
            request,
            "ACCOUNT_DELETED",
            None,
            "user",
            str(user_id),
            {"email": email},
        )
    _clear_auth_cookies(response)
    return {"status": "deleted"}


def _require_admin(session, request: Request) -> tuple[UserRecord, UserSessionRecord]:
    settings = get_settings()
    user, session_record = require_session_user(session, settings, request)
    if normalize_email(user.email) != normalize_email(settings.admin_email):
        raise HTTPException(status_code=403, detail="Admin access denied")
    return user, session_record


@router.get("/admin/users")
def admin_users(request: Request) -> dict:
    with SessionLocal() as session:
        admin, _session_record = _require_admin(session, request)
        users = list(
            session.execute(
                select(UserRecord).order_by(UserRecord.created_at.desc())
            ).scalars()
        )
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USERS_VIEWED",
                target_type="admin",
                target_id=admin.email,
            )
        )
        session.commit()
        return {"users": [_serialize_user(user) for user in users]}


@router.post("/admin/users", status_code=201)
def admin_create_user(payload: AdminUserCreate, request: Request) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        settings = get_settings()
        assert_csrf(settings, request, session_record)
        email = validate_email(payload.email)
        validate_password(payload.password)
        existing = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        if existing is not None:
            raise HTTPException(status_code=409, detail="Email already registered")
        user = UserRecord(
            email=email,
            display_name=payload.display_name.strip(),
            password_hash=hash_password(payload.password, settings.session_secret),
            email_verified=payload.email_verified,
            two_factor_enabled=payload.two_factor_enabled,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USER_CREATED",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps({"email": email}, ensure_ascii=False),
            )
        )
        session.commit()
        return {"user": _serialize_user(user)}


@router.patch("/admin/users/{user_id}")
def admin_update_user(user_id: int, payload: AdminUserUpdate, request: Request) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        settings = get_settings()
        assert_csrf(settings, request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        is_admin_account = normalize_email(user.email) == normalize_email(
            settings.admin_email
        )
        changes: dict = {}
        if payload.display_name is not None:
            user.display_name = payload.display_name.strip()
            changes["displayName"] = user.display_name
        if payload.email is not None:
            new_email = validate_email(payload.email)
            if new_email != user.email:
                # Block renaming the configured admin so the panel
                # can't orphan its own admin access.
                if is_admin_account:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot change the configured admin email",
                    )
                clash = session.execute(
                    select(UserRecord).where(UserRecord.email == new_email)
                ).scalar_one_or_none()
                if clash is not None:
                    raise HTTPException(
                        status_code=409, detail="Email already registered"
                    )
                user.email = new_email
                changes["email"] = new_email
        if payload.email_verified is not None:
            user.email_verified = payload.email_verified
            changes["emailVerified"] = payload.email_verified
        if payload.two_factor_enabled is not None:
            user.two_factor_enabled = payload.two_factor_enabled
            changes["twoFactorEnabled"] = payload.two_factor_enabled
        user.updated_at = datetime.now(UTC)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USER_UPDATED",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps(changes, ensure_ascii=False),
            )
        )
        session.commit()
        return {"user": _serialize_user(user)}


@router.post("/admin/users/{user_id}/set-password")
def admin_set_password(
    user_id: int, payload: AdminSetPassword, request: Request
) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        settings = get_settings()
        assert_csrf(settings, request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        validate_password(payload.password)
        user.password_hash = hash_password(payload.password, settings.session_secret)
        user.force_password_reset = False
        user.failed_login_count = 0
        user.locked_until = None
        user.updated_at = datetime.now(UTC)
        revoked = revoke_sessions(session, user.id)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_PASSWORD_SET",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps({"revoked": revoked}, ensure_ascii=False),
            )
        )
        session.commit()
        return {"user": _serialize_user(user), "revokedSessions": revoked}


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, request: Request) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        settings = get_settings()
        assert_csrf(settings, request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        # Never delete the acting admin or the configured admin row -
        # that would lock everyone out of /admin.
        if user.id == admin.id or normalize_email(user.email) == normalize_email(
            settings.admin_email
        ):
            raise HTTPException(
                status_code=400, detail="Cannot delete the admin account"
            )
        email = user.email
        revoke_sessions(session, user.id)
        session.delete(user)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USER_DELETED",
                target_type="user",
                target_id=str(user_id),
                audit_metadata=json.dumps({"email": email}, ensure_ascii=False),
            )
        )
        session.commit()
        return {"status": "deleted"}


@router.post("/admin/users/{user_id}/lock")
def admin_lock_user(user_id: int, payload: AdminUserAction, request: Request) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        assert_csrf(get_settings(), request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        # Do not let the admin lock the configured admin account out.
        if normalize_email(user.email) == normalize_email(get_settings().admin_email):
            raise HTTPException(status_code=400, detail="Cannot lock the admin account")
        user.locked_until = datetime.now(UTC) + timedelta(days=3650)
        user.updated_at = datetime.now(UTC)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USER_LOCKED",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps(
                    {"reason": payload.reason}, ensure_ascii=False
                ),
            )
        )
        session.commit()
        return {"user": _serialize_user(user)}


@router.post("/admin/users/{user_id}/unlock")
def admin_unlock_user(user_id: int, payload: AdminUserAction, request: Request) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        assert_csrf(get_settings(), request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.locked_until = None
        user.failed_login_count = 0
        user.updated_at = datetime.now(UTC)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_USER_UNLOCKED",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps(
                    {"reason": payload.reason}, ensure_ascii=False
                ),
            )
        )
        session.commit()
        return {"user": _serialize_user(user)}


@router.post("/admin/users/{user_id}/revoke-sessions")
def admin_revoke_sessions(
    user_id: int, payload: AdminUserAction, request: Request
) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        assert_csrf(get_settings(), request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        count = revoke_sessions(session, user.id)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_SESSIONS_REVOKED",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps(
                    {"reason": payload.reason, "revoked": count}, ensure_ascii=False
                ),
            )
        )
        session.commit()
        return {"status": "revoked", "revokedSessions": count}


@router.post("/admin/users/{user_id}/force-password-reset")
def admin_force_password_reset(
    user_id: int, payload: AdminUserAction, request: Request
) -> dict:
    with SessionLocal() as session:
        admin, session_record = _require_admin(session, request)
        assert_csrf(get_settings(), request, session_record)
        user = session.get(UserRecord, user_id)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        user.force_password_reset = True
        user.updated_at = datetime.now(UTC)
        revoked = revoke_sessions(session, user.id)
        session.add(
            SecurityAuditRecord(
                actor_user_id=admin.id,
                actor_email=admin.email,
                action="ADMIN_FORCE_PASSWORD_RESET",
                target_type="user",
                target_id=str(user.id),
                audit_metadata=json.dumps(
                    {"reason": payload.reason, "revoked": revoked}, ensure_ascii=False
                ),
            )
        )
        session.commit()
        return {"user": _serialize_user(user), "revokedSessions": revoked}


@router.get("/admin/audit-events")
def admin_audit_events(request: Request, limit: int = 100) -> dict:
    with SessionLocal() as session:
        _admin, _session_record = _require_admin(session, request)
        events = list(
            session.execute(
                select(SecurityAuditRecord)
                .order_by(SecurityAuditRecord.created_at.desc())
                .limit(max(1, min(limit, 500)))
            ).scalars()
        )
        return {
            "events": [
                {
                    "id": event.id,
                    "actorEmail": event.actor_email,
                    "action": event.action,
                    "targetType": event.target_type,
                    "targetId": event.target_id,
                    "ipAddress": event.ip_address,
                    "createdAt": event.created_at.isoformat()
                    if event.created_at
                    else None,
                }
                for event in events
            ]
        }
