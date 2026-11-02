"""AI connection sync cannot elevate drafts or generated statuses."""

import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import NoteRecord
from berrybrain_api.routers.connections import (
    SyncConnectionsRequest,
    sync_connections_from_ai,
)


class ConnectionSyncSafetyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(bind=self.engine)
        with self.sessions() as session:
            session.add_all(
                [
                    NoteRecord(
                        id=1, path="inbox/source.md", slug="source", title="Source"
                    ),
                    NoteRecord(
                        id=2, path="study/target.md", slug="target", title="Target"
                    ),
                    NoteRecord(
                        id=3,
                        path="study/draft.md",
                        slug="draft",
                        title="Draft",
                        evidence_status="draft",
                    ),
                ]
            )
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_generated_status_and_invalid_confidence_cannot_confirm_connection(
        self,
    ) -> None:
        with (
            patch("berrybrain_api.routers.connections.SessionLocal", self.sessions),
            patch("berrybrain_api.routers.connections.create_connection") as create,
        ):
            result = sync_connections_from_ai(
                SyncConnectionsRequest(
                    note_path="inbox/source.md",
                    connections=[
                        {"target": "inbox/source.md", "status": "confirmed"},
                        {"target": "study/draft.md", "status": "confirmed"},
                        {
                            "target": "study/target.md",
                            "status": "confirmed",
                            "confidence": float("inf"),
                        },
                    ],
                )
            )
        self.assertEqual(result["connections_created"], 1)
        self.assertEqual(create.call_args.kwargs["status"], "suggested")
        self.assertIsNone(create.call_args.args[4])

    def test_draft_source_is_not_processed(self) -> None:
        with (
            patch("berrybrain_api.routers.connections.SessionLocal", self.sessions),
            patch("berrybrain_api.routers.connections.create_connection") as create,
        ):
            result = sync_connections_from_ai(
                SyncConnectionsRequest(
                    note_path="study/draft.md",
                    connections=[{"target": "study/target.md"}],
                )
            )
        self.assertEqual(result, {"status": "skipped_draft", "connections_created": 0})
        create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
