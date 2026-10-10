"""Product regressions only: projections must preserve semantics, not audit blobs."""

import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from berrybrain_api.assimilation import note_assimilation_map
from berrybrain_api.database import Base
from berrybrain_api.jobs import calculate_pipeline_progress
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    JobRecord,
    NoteRecord,
)
from berrybrain_api.routers.graph import get_graph_edges_page
from berrybrain_api.routers.jobs import pipeline_progress_endpoint


class ReadPerformanceTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.factory = sessionmaker(bind=self.engine)

    def tearDown(self):
        self.engine.dispose()

    def test_assimilation_projection_matches_legacy_and_structured_jobs(self):
        with self.factory() as session:
            notes = [
                NoteRecord(
                    title=str(i),
                    slug=str(i),
                    path=f"{i}.md",
                    content="content",
                    content_hash=f"hash-{i}",
                )
                for i in range(6)
            ]
            session.add_all(notes)
            session.flush()
            jobs = [
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="completed",
                    payload=json.dumps({"note_path": "0.md", "content_hash": "hash-0"}),
                ),
                JobRecord(
                    type="GENERATE_EMBEDDING", status="completed", note_path="1.md"
                ),
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="completed",
                    payload=json.dumps({"note_path": "2.md", "content_hash": "hash-3"}),
                ),
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="completed",
                    payload=json.dumps({"note_path": "3.md", "content_hash": "old"}),
                ),
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="completed",
                    note_id=notes[4].id,
                    content_hash="hash-4",
                ),
                JobRecord(type="GENERATE_EMBEDDING", status="completed", payload="{"),
            ]
            session.add_all(jobs)
            session.commit()
            expected = note_assimilation_map(session, notes, jobs=jobs)
            actual = note_assimilation_map(session, notes)
            self.assertEqual(actual, expected)
            self.assertEqual(
                [actual[n.id]["assimilated"] for n in notes],
                [True, True, False, False, True, False],
            )

    def test_compact_edges_keep_topology_bounds_and_full_default(self):
        with self.factory() as session:
            nodes = [GraphNodeRecord(type="note", label=str(i)) for i in range(3)]
            session.add_all(nodes)
            session.flush()
            for i in range(2):
                session.add(
                    GraphEdgeRecord(
                        source_node_id=nodes[i].id,
                        target_node_id=nodes[i + 1].id,
                        type="related",
                        quality_gate_status="passed",
                        evidence=json.dumps([{"quote": "evidence" * 1000}]),
                        confidence_factors=json.dumps([{"reason": "factor" * 1000}]),
                        confidence=0.8,
                        confidence_lower=0.6,
                        confidence_upper=0.9,
                        confidence_sample_size=10,
                        reason="Explanation retained",
                    )
                )
            session.commit()
        statements = []
        event.listen(
            self.engine,
            "before_cursor_execute",
            lambda c, u, sql, p, x, m: statements.append(sql),
        )
        with patch("berrybrain_api.routers.graph.SessionLocal", self.factory):
            compact = get_graph_edges_page(
                cursor=0, limit=1, compact=True, include_provisional=True
            )
            reads = list(statements)
            full = get_graph_edges_page(cursor=0, limit=1, include_provisional=True)
            second = get_graph_edges_page(
                cursor=compact["nextCursor"],
                limit=1,
                compact=True,
                include_provisional=True,
            )
        self.assertIsNone(second["nextCursor"])
        self.assertEqual(compact["nextCursor"], full["nextCursor"])
        for key, value in compact["edges"][0].items():
            if key != "confidenceInterval":
                self.assertEqual(value, full["edges"][0][key])
        self.assertNotIn("evidence", compact["edges"][0])
        self.assertNotIn("factors", compact["edges"][0]["confidenceInterval"])
        self.assertTrue(full["edges"][0]["evidence"])
        self.assertEqual(compact["edges"][0]["confidenceInterval"]["lower"], 0.6)
        self.assertLess(len(json.dumps(compact)), len(json.dumps(full)) / 4)
        edge_selects = [s for s in reads if "FROM graph_edges" in s]
        self.assertFalse(any("graph_edges.evidence" in s for s in edge_selects))
        self.assertFalse(
            any("graph_edges.confidence_factors" in s for s in edge_selects)
        )

    def test_pipeline_excludes_maintenance_and_projects_legacy_identity(self):
        with self.factory() as session:
            note = NoteRecord(
                title="Study",
                slug="study",
                path="study.md",
                content="large" * 1000,
                content_hash="v1",
            )
            session.add(note)
            session.flush()
            session.add(
                JobRecord(
                    type="GENERATE_EMBEDDING",
                    status="completed",
                    payload=json.dumps(
                        {
                            "note_id": note.id,
                            "note_path": note.path,
                            "content_hash": "v1",
                            "prompt": "private" * 10000,
                        }
                    ),
                )
            )
            session.add_all(
                [
                    JobRecord(type="UPDATE_GRAPH_STATS", status="completed")
                    for _ in range(501)
                ]
            )
            # Corrupt legacy payloads must not crash the endpoint or create a
            # spurious note named "None" after SQL identity projection.
            session.add(
                JobRecord(type="GENERATE_EMBEDDING", status="failed", payload="{")
            )
            session.commit()
        with (
            patch("berrybrain_api.routers.jobs.SessionLocal", self.factory),
            patch(
                "berrybrain_api.routers.jobs.calculate_pipeline_progress",
                wraps=calculate_pipeline_progress,
            ) as calculate,
        ):
            result = pipeline_progress_endpoint()
        self.assertEqual(len(result["notes"]), 1)
        self.assertEqual(result["notes"][0]["notePath"], "study.md")
        self.assertEqual(result["notes"][0]["percent"], 100)
        rows = calculate.call_args.args[0]
        self.assertEqual(len(rows), 1)
        self.assertTrue(all(len(row.payload) < 200 for row in rows))


if __name__ == "__main__":
    unittest.main()
