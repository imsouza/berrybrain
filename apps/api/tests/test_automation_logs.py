import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.automation_logs import (
    create_automation_log,
    list_automation_logs,
    serialize_automation_log,
)
from berrybrain_api.jobs import enqueue_note_changed_jobs


class AutomationLogTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()

    def tearDown(self) -> None:
        self.session.close()

    def test_create_and_list_automation_logs(self) -> None:
        log = create_automation_log(
            self.session,
            action_type="ENQUEUE_JOB",
            target_type="note",
            target_id="inbox/a.md",
            description="Criou job PARSE_NOTE",
            before_state={},
            after_state={"job_type": "PARSE_NOTE"},
            reversible=False,
        )

        logs = list_automation_logs(self.session)
        serialized = serialize_automation_log(log)

        self.assertEqual([item.id for item in logs], [log.id])
        self.assertEqual(serialized["after_state"], {"job_type": "PARSE_NOTE"})
        self.assertFalse(serialized["reversible"])

    def test_enqueue_note_changed_jobs_records_automation_log(self) -> None:
        enqueue_note_changed_jobs(
            self.session,
            note_path="inbox/a.md",
            event_type="NOTE_UPDATED",
            content_hash="abc",
        )

        logs = list_automation_logs(self.session)
        after_state = json.loads(logs[0].after_state)

        self.assertEqual(len(logs), 14)
        self.assertEqual(logs[0].action_type, "ENQUEUE_JOB")
        self.assertEqual(logs[0].target_id, "inbox/a.md")


if __name__ == "__main__":
    unittest.main()
