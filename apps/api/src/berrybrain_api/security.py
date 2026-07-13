from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import smtplib
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage
from typing import Any

from fastapi import HTTPException, Request
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from berrybrain_api.config import Settings, get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.models import (
    AuthOtpRecord,
    LoginAttemptRecord,
    SecurityAuditRecord,
    UserRecord,
    UserSessionRecord,
)

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError

    _ARGON2 = PasswordHasher(
        time_cost=2,
        memory_cost=19456,
        parallelism=2,
        hash_len=32,
        salt_len=16,
    )
except Exception:  # pragma: no cover - fallback only for unprepared local envs
    _ARGON2 = None
    VerifyMismatchError = Exception


SESSION_TTL_DAYS = 30
SENSITIVE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def validate_email(email: str) -> str:
    value = normalize_email(email)
    if "@" not in value or "." not in value.rsplit("@", 1)[-1] or len(value) > 255:
        raise HTTPException(status_code=400, detail="Invalid email address")
    return value


def validate_password(password: str) -> None:
    if len(password or "") < 12:
        raise HTTPException(
            status_code=400, detail="Password must be at least 12 characters"
        )
    if password.lower() == password or password.upper() == password:
        raise HTTPException(status_code=400, detail="Password must mix letter case")
    if not any(ch.isdigit() for ch in password):
        raise HTTPException(status_code=400, detail="Password must include a number")


def hash_password(password: str, secret: str) -> str:
    if _ARGON2 is not None:
        return "argon2id$" + _ARGON2.hash(password)
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), f"{salt}:{secret}".encode(), 600_000
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str, secret: str) -> bool:
    if stored.startswith("argon2id$") and _ARGON2 is not None:
        try:
            return _ARGON2.verify(stored.removeprefix("argon2id$"), password)
        except VerifyMismatchError:
            return False
        except Exception:
            return False
    if stored.startswith("pbkdf2_sha256$"):
        _, salt, digest = stored.split("$", 2)
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), f"{salt}:{secret}".encode(), 600_000
        ).hex()
        return hmac.compare_digest(candidate, digest)
    return False


def token_hash(token: str, secret: str) -> str:
    return hmac.new(secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def client_ip(request: Request) -> str:
    settings = get_settings()
    forwarded = request.headers.get("x-forwarded-for", "")
    if settings.trust_x_forwarded_for and forwarded:
        return forwarded.split(",", 1)[0].strip()[:80]
    return (request.client.host if request.client else "")[:80]


def user_agent(request: Request) -> str:
    return request.headers.get("user-agent", "")[:1000]


def audit_event(
    session: Session,
    request: Request,
    action: str,
    actor: UserRecord | None = None,
    target_type: str = "",
    target_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    session.add(
        SecurityAuditRecord(
            actor_user_id=actor.id if actor else None,
            actor_email=actor.email if actor else "",
            action=action,
            target_type=target_type,
            target_id=target_id,
            ip_address=client_ip(request),
            user_agent=user_agent(request),
            audit_metadata=json.dumps(metadata or {}, ensure_ascii=False),
        )
    )
    session.commit()


def record_attempt(
    session: Session,
    request: Request,
    action: str,
    email: str,
    success: bool,
    reason: str = "",
) -> None:
    session.add(
        LoginAttemptRecord(
            email=normalize_email(email),
            ip_address=client_ip(request),
            action=action,
            success=success,
            reason=reason[:120],
        )
    )
    session.commit()


def assert_rate_limit(
    session: Session,
    request: Request,
    settings: Settings,
    action: str,
    email: str = "",
) -> None:
    since = datetime.now(UTC) - timedelta(
        seconds=settings.auth_rate_limit_window_seconds
    )
    ip = client_ip(request)
    email_key = normalize_email(email)
    identity_filter = (
        or_(LoginAttemptRecord.ip_address == ip, LoginAttemptRecord.email == email_key)
        if email_key
        else LoginAttemptRecord.ip_address == ip
    )
    failures = session.execute(
        select(func.count(LoginAttemptRecord.id)).where(
            LoginAttemptRecord.action == action,
            LoginAttemptRecord.success == False,  # noqa: E712
            LoginAttemptRecord.created_at >= since,
            identity_filter,
        )
    ).scalar_one()
    if failures >= settings.auth_rate_limit_max_attempts:
        raise HTTPException(
            status_code=429, detail="Too many attempts. Try again later."
        )


def create_otp(
    session: Session,
    settings: Settings,
    user: UserRecord | None,
    email: str,
    purpose: str,
) -> tuple[str, str]:
    now = datetime.now(UTC)
    recent = session.execute(
        select(AuthOtpRecord).where(
            AuthOtpRecord.email == email,
            AuthOtpRecord.purpose == purpose,
            AuthOtpRecord.sent_at
            >= now - timedelta(seconds=settings.auth_otp_resend_cooldown_seconds),
            AuthOtpRecord.used_at.is_(None),
        )
    ).scalar_one_or_none()
    if recent is not None:
        raise HTTPException(
            status_code=429, detail="Wait before requesting another code."
        )

    code = f"{secrets.randbelow(1_000_000):06d}"
    challenge = secrets.token_urlsafe(32)
    record = AuthOtpRecord(
        user_id=user.id if user else None,
        email=email,
        purpose=purpose,
        code_hash=token_hash(code, settings.session_secret),
        challenge_token_hash=token_hash(challenge, settings.session_secret),
        expires_at=now + timedelta(minutes=settings.auth_otp_ttl_minutes),
    )
    session.add(record)
    session.commit()
    return code, challenge


def verify_otp(
    session: Session,
    settings: Settings,
    email: str,
    purpose: str,
    code: str,
    challenge: str = "",
) -> AuthOtpRecord:
    now = datetime.now(UTC)
    query = select(AuthOtpRecord).where(
        AuthOtpRecord.email == email,
        AuthOtpRecord.purpose == purpose,
        AuthOtpRecord.used_at.is_(None),
        AuthOtpRecord.expires_at >= now,
    )
    if challenge:
        query = query.where(
            AuthOtpRecord.challenge_token_hash
            == token_hash(challenge, settings.session_secret)
        )
    record = (
        session.execute(query.order_by(AuthOtpRecord.sent_at.desc())).scalars().first()
    )
    if record is None:
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    if record.attempts >= record.max_attempts:
        raise HTTPException(status_code=429, detail="Too many code attempts")
    record.attempts += 1
    if not hmac.compare_digest(
        record.code_hash, token_hash(code, settings.session_secret)
    ):
        session.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired code")
    record.used_at = now
    session.commit()
    return record


def send_otp_email(
    settings: Settings, email: str, code: str, purpose: str
) -> dict[str, str]:
    if not settings.smtp_host or not settings.smtp_user or not settings.smtp_password:
        return {"status": "skipped", "reason": "smtp_not_configured"}
    msg = EmailMessage()
    msg["Subject"] = "Your BerryBrain security code"
    msg["From"] = settings.smtp_from
    msg["To"] = email
    msg.set_content(
        "Your BerryBrain security code is valid for "
        f"{settings.auth_otp_ttl_minutes} minutes.\n\nCode: {code}\n\n"
        f"Purpose: {purpose}\nSupport: contato@optlabs.com.br"
    )
    try:
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as smtp:
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(
                settings.smtp_host, settings.smtp_port, timeout=10
            ) as smtp:
                smtp.starttls()
                smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.send_message(msg)
    except (smtplib.SMTPException, OSError) as exc:
        return {"status": "error", "reason": str(exc)}
    return {"status": "sent"}


def create_user_session(
    session: Session,
    settings: Settings,
    request: Request,
    user: UserRecord,
    remember_me: bool = True,
) -> tuple[str, str, UserSessionRecord]:
    raw_session = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    record = UserSessionRecord(
        user_id=user.id,
        session_hash=token_hash(raw_session, settings.session_secret),
        csrf_token_hash=token_hash(csrf, settings.session_secret),
        ip_address=client_ip(request),
        user_agent=user_agent(request),
        expires_at=datetime.now(UTC)
        + (timedelta(days=SESSION_TTL_DAYS) if remember_me else timedelta(hours=12)),
    )
    session.add(record)
    user.last_login_at = datetime.now(UTC)
    user.failed_login_count = 0
    user.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(record)
    return raw_session, csrf, record


def get_session_user(
    session: Session, settings: Settings, request: Request
) -> tuple[UserRecord, UserSessionRecord] | None:
    raw_session = request.cookies.get(settings.session_cookie_name, "")
    if not raw_session:
        return None
    record = session.execute(
        select(UserSessionRecord).where(
            UserSessionRecord.session_hash
            == token_hash(raw_session, settings.session_secret),
            UserSessionRecord.revoked_at.is_(None),
            UserSessionRecord.expires_at >= datetime.now(UTC),
        )
    ).scalar_one_or_none()
    if record is None:
        return None
    user = session.get(UserRecord, record.user_id)
    if user is None:
        return None
    record.last_seen_at = datetime.now(UTC)
    session.commit()
    return user, record


def require_session_user(
    session: Session, settings: Settings, request: Request
) -> tuple[UserRecord, UserSessionRecord]:
    result = get_session_user(session, settings, request)
    if result is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return result


def require_admin(request: Request) -> UserRecord:
    settings = get_settings()
    with SessionLocal() as session:
        user, _record = require_session_user(session, settings, request)
        if normalize_email(user.email) != normalize_email(settings.admin_email):
            raise HTTPException(status_code=403, detail="Admin access required")
        return user


def assert_csrf(
    settings: Settings, request: Request, session_record: UserSessionRecord
) -> None:
    if request.method not in SENSITIVE_METHODS:
        return
    header = request.headers.get("x-csrf-token", "")
    cookie = request.cookies.get(settings.csrf_cookie_name, "")
    if not header or not cookie:
        raise HTTPException(status_code=403, detail="CSRF token required")
    if not hmac.compare_digest(header, cookie):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    if not hmac.compare_digest(
        session_record.csrf_token_hash, token_hash(header, settings.session_secret)
    ):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


def revoke_sessions(session: Session, user_id: int) -> int:
    now = datetime.now(UTC)
    rows = list(
        session.execute(
            select(UserSessionRecord).where(
                UserSessionRecord.user_id == user_id,
                UserSessionRecord.revoked_at.is_(None),
            )
        ).scalars()
    )
    for row in rows:
        row.revoked_at = now
    session.commit()
    return len(rows)


def secure_compare_env(value: str, expected: str) -> bool:
    return hmac.compare_digest(
        (value or "").strip().lower(), (expected or "").strip().lower()
    )
