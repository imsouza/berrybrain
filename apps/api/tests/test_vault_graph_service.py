import tempfile
import unittest
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import GraphNodeRecord
from berrybrain_api.vault_graph_service import (
    scan_and_refresh_graph,
    scan_response_with_graph,
)


class VaultGraphServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = Path(self.temp_dir.name) / "vault"
        self.vault_path.mkdir()

    def tearDown(self) -> None:
        self.session.close()
        self.temp_dir.cleanup()

    def test_scan_and_refresh_graph_has_explicit_contract(self) -> None:
        note_path = self.vault_path / "contract.md"
        note_path.write_text("# Contract\n\nGraph refresh contract.", encoding="utf-8")

        result = scan_and_refresh_graph(
            self.session, self.vault_path, status="scan+rebuild completed"
        )
        response = scan_response_with_graph(result)
        note_nodes = (
            self.session.execute(
                select(GraphNodeRecord).where(GraphNodeRecord.type == "note")
            )
            .scalars()
            .all()
        )

        self.assertEqual(result["status"], "scan+rebuild completed")
        self.assertEqual(result["scan"]["created"], 1)
        self.assertEqual(result["graph"]["notes"], 1)
        self.assertEqual(response["created"], 1)
        self.assertEqual(response["status"], "scan+rebuild completed")
        self.assertEqual(len(note_nodes), 1)


if __name__ == "__main__":
    unittest.main()
