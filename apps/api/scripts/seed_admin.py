from __future__ import annotations

import argparse
import os
import sys

from sqlalchemy import select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal, init_database
from berrybrain_api.models import UserRecord
from berrybrain_api.security import hash_password, normalize_email, validate_password


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="Create or reset the admin user (email verified, 2FA off)."
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("SEED_ADMIN_EMAIL", settings.admin_email),
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("SEED_ADMIN_PASSWORD"),
        help="Admin password (or set SEED_ADMIN_PASSWORD). Never hardcode in the repo.",
    )
    parser.add_argument("--display-name", default="Admin")
    parser.add_argument(
        "--enable-2fa",
        action="store_true",
        help="Keep email 2FA on (default: off, so login works without SMTP).",
    )
    args = parser.parse_args()

    if not args.password:
        print(
            "error: password required via --password or SEED_ADMIN_PASSWORD env",
            file=sys.stderr,
        )
        return 2

    email = normalize_email(args.email)
    validate_password(args.password)
    password_hash = hash_password(args.password, settings.session_secret)

    init_database()
    with SessionLocal() as session:
        user = session.execute(
            select(UserRecord).where(UserRecord.email == email)
        ).scalar_one_or_none()
        action = "updated"
        if user is None:
            user = UserRecord(email=email, display_name=args.display_name)
            session.add(user)
            action = "created"
        user.password_hash = password_hash
        user.email_verified = True
        user.two_factor_enabled = bool(args.enable_2fa)
        user.locked_until = None
        user.force_password_reset = False
        user.failed_login_count = 0
        session.commit()
        session.refresh(user)
        print(
            f"admin {action}: id={user.id} email={user.email} "
            f"verified={user.email_verified} two_factor={user.two_factor_enabled}"
        )

    if normalize_email(email) != normalize_email(settings.admin_email):
        print(
            f"warning: {email} != BERRYBRAIN_ADMIN_EMAIL ({settings.admin_email}); "
            "this user will NOT have admin access.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
