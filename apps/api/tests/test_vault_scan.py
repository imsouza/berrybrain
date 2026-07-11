import json
import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import JobRecord, NoteRecord
from berrybrain_api.vault_scan import scan_vault


class VaultScanTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "vault"
        (self.vault_path / "inbox").mkdir(parents=True)

    def tearDown(self) -> None:
        self.session.close()
        self.temp_dir.cleanup()

    def test_scan_vault_syncs_new_changed_and_deleted_notes(self) -> None:
        note_path = self.vault_path / "inbox" / "a.md"
        note_path.write_text("# A\n\nInicial.", encoding="utf-8")

        first = scan_vault(self.session, self.vault_path)
        second = scan_vault(self.session, self.vault_path)
        note_path.write_text("# A\n\nAlterada com [[B]].", encoding="utf-8")
        third = scan_vault(self.session, self.vault_path)
        note_path.unlink()
        fourth = scan_vault(self.session, self.vault_path)

        self.assertEqual(first["created"], 1)
        self.assertEqual(first["jobs_created"], 14)
        self.assertEqual(second["unchanged"], 1)
        self.assertEqual(second["jobs_created"], 0)
        self.assertEqual(third["updated"], 1)
        self.assertEqual(third["jobs_created"], 14)
        self.assertEqual(fourth["deleted"], 1)
        self.assertEqual(fourth["jobs_created"], 0)

        remaining_notes = self.session.execute(select(NoteRecord)).scalars().all()
        jobs = (
            self.session.execute(select(JobRecord).order_by(JobRecord.id))
            .scalars()
            .all()
        )
        payloads = [json.loads(job.payload) for job in jobs]

        self.assertEqual(remaining_notes, [])
        event_types = [payload["event_type"] for payload in payloads]
        self.assertEqual(event_types.count("NOTE_CREATED"), 14)
        self.assertEqual(event_types.count("NOTE_UPDATED"), 14)
        self.assertEqual(event_types.count("NOTE_DELETED"), 0)


if __name__ == "__main__":
    unittest.main()
