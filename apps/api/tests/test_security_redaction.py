import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.database import Base
from berrybrain_api.jobs import fail_job
from berrybrain_api.models import JobRecord
from berrybrain_api.redaction import redact_text, redact_value


class SecurityRedactionTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_redacts_known_tokens_and_sensitive_keys_recursively(self) -> None:
        value = redact_value(
            {
                "api_key": "nvapi-secret-value-123456789",
                "nested": ["Bearer abcdefghijklmnop", "ghp_1234567890abcdefghijkl"],
            }
        )
        self.assertEqual(value["api_key"], "[REDACTED]")
        self.assertNotIn("abcdefghijklmnop", json.dumps(value))
        self.assertNotIn(
            "super-secret", redact_text("password=super-secret request failed")
        )

    def test_job_errors_and_automation_logs_do_not_persist_secrets(self) -> None:
        job = JobRecord(type="TEST", payload="{}", max_attempts=1, attempts=1)
        self.session.add(job)
        self.session.commit()

        failed = fail_job(
            self.session,
            job.id,
            "Provider rejected Bearer abcdefghijklmnop",
        )
        self.assertNotIn("abcdefghijklmnop", failed.error_message)
        log = create_automation_log(
            self.session,
            action_type="SETTING_CHANGED",
            target_type="setting",
            target_id="provider",
            description="api_key=secret-value-123456",
            before_state={"token": "secret-value-123456"},
            after_state={"authorization": "Bearer abcdefghijklmnop"},
            reversible=False,
        )
        persisted = f"{log.description}{log.before_state}{log.after_state}"
        self.assertNotIn("secret-value", persisted)
        self.assertNotIn("abcdefghijklmnop", persisted)


if __name__ == "__main__":
    unittest.main()
