from __future__ import annotations

import os
import sys

from sqlalchemy import delete, select

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal, init_database
from berrybrain_api.models import (
    AuthOtpRecord,
    LoginAttemptRecord,
    SecurityAuditRecord,
    UserRecord,
    UserSessionRecord,
)
from berrybrain_api.security import normalize_email

CONFIRMATION = "DELETE_LOCAL_OWNER"


def main() -> int:
    if os.environ.get("DELETE_OWNER_CONFIRM") != CONFIRMATION:
        print(
            f"error: set DELETE_OWNER_CONFIRM={CONFIRMATION} to continue",
            file=sys.stderr,
        )
        return 2

    settings = get_settings()
    owner_email = normalize_email(settings.admin_email)
    init_database()
    with SessionLocal() as session:
        owner = session.execute(
            select(UserRecord).where(UserRecord.email == owner_email)
        ).scalar_one_or_none()
        if owner is None:
            print("owner account is already absent")
            return 0

        session.execute(
            delete(UserSessionRecord).where(UserSessionRecord.user_id == owner.id)
        )
        session.execute(delete(AuthOtpRecord).where(AuthOtpRecord.user_id == owner.id))
        session.execute(
            delete(LoginAttemptRecord).where(LoginAttemptRecord.email == owner.email)
        )
        session.execute(
            delete(SecurityAuditRecord).where(
                SecurityAuditRecord.actor_user_id == owner.id
            )
        )
        session.delete(owner)
        session.commit()

    print("local owner deleted; the one-time setup is available again")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
