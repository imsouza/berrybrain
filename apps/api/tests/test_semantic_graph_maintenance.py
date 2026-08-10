import unittest
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import GraphNodeRecord
from berrybrain_api.routers.maintenance import (
    PrepareSemanticGraphRequest,
    prepare_semantic_graph,
)


class SemanticGraphMaintenanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.factory = sessionmaker(bind=self.engine)
        with self.factory() as session:
            session.add(
                GraphNodeRecord(
                    type="note",
                    label="Pending note",
                    semantic_state="pending",
                )
            )
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_dry_run_reports_without_mutating(self) -> None:
        with patch(
            "berrybrain_api.routers.maintenance.SessionLocal",
            self.factory,
        ):
            result = prepare_semantic_graph(PrepareSemanticGraphRequest(dry_run=True))

        self.assertTrue(result["dryRun"])
        self.assertEqual(result["semanticStates"]["pending"], 1)
        self.assertEqual(result["clusterPreview"]["nodeCount"], 1)

    def test_apply_requires_confirmation_and_is_bounded(self) -> None:
        with patch(
            "berrybrain_api.routers.maintenance.SessionLocal",
            self.factory,
        ):
            with self.assertRaisesRegex(HTTPException, "confirm=true"):
                prepare_semantic_graph(PrepareSemanticGraphRequest(dry_run=False))
            result = prepare_semantic_graph(
                PrepareSemanticGraphRequest(
                    dry_run=False,
                    confirm=True,
                    batch_size=1,
                )
            )

        self.assertFalse(result["dryRun"])
        self.assertEqual(result["enrichmentQueued"], 0)
        self.assertEqual(result["enrichmentSkipped"], 1)


if __name__ == "__main__":
    unittest.main()
