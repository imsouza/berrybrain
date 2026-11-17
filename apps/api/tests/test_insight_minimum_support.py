"""Cross-note insights must not outlive their two-note support.

Regression for the lifecycle gap found by the MuSiQue edit-stream benchmark:
an AI-extracted concept can survive an edit or deletion with a single
supporting note, and the "Connection pattern: ... links N notes" insight built
on it used to stay active after the rebuild.
"""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.models import GraphNodeRecord, InsightRecord, NoteRecord
from berrybrain_api.second_brain import expand_knowledge_graph

CONCEPT = "Indian Ocean Trade"


class InsightMinimumSupportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _note(self, slug: str, body: str | None = None) -> NoteRecord:
        text = body or f"Historical notes on {CONCEPT} across regional archives."
        note = NoteRecord(
            title=f"Archive {slug}",
            slug=slug,
            path=f"sources/{slug}.md",
            content=f"# Archive {slug}\n\n{text}",
            content_hash=f"hash-{slug}",
        )
        self.session.add(note)
        self.session.commit()
        return note

    def _retract(self, note: NoteRecord) -> None:
        note.content = "# Retracted source\n\nThe earlier passage has been retracted."
        note.content_hash = f"retracted-{note.slug}"
        self.session.commit()
        self._set_concepts(note, [])

    def _set_concepts(self, note: NoteRecord, concepts: list[str]) -> None:
        upsert_generated_metadata(
            self.session,
            note.id,
            "concepts",
            {"concepts": concepts},
            note.content_hash,
            model_used="test-openie",
        )
        self.session.commit()

    def _concept_insight_titles(self) -> list[str]:
        needle = CONCEPT.casefold()
        return sorted(
            insight.title
            for insight in self.session.query(InsightRecord).filter(
                InsightRecord.type == "new_connection"
            )
            if needle in insight.title.casefold()
        )

    def _concept_insight_nodes(self) -> list[str]:
        needle = CONCEPT.casefold()
        return sorted(
            node.label
            for node in self.session.query(GraphNodeRecord).filter(
                GraphNodeRecord.type == "insight"
            )
            if needle in node.label.casefold()
        )

    def test_insight_is_pruned_when_support_drops_to_one_note(self) -> None:
        first, second = self._note("first"), self._note("second")
        self._set_concepts(first, [CONCEPT])
        self._set_concepts(second, [CONCEPT])
        expand_knowledge_graph(self.session)
        self.assertEqual(len(self._concept_insight_titles()), 1)
        self.assertIn("links 2 notes", self._concept_insight_titles()[0])
        self.assertEqual(len(self._concept_insight_nodes()), 1)

        # The second note is retracted: the concept keeps one supporting note.
        self._retract(second)
        expand_knowledge_graph(self.session)

        self.assertEqual(self._concept_insight_titles(), [])
        self.assertEqual(self._concept_insight_nodes(), [])
        concept_labels = {
            node.label.casefold()
            for node in self.session.query(GraphNodeRecord).filter(
                GraphNodeRecord.type == "concept"
            )
        }
        # The single-note concept itself is still valid derived state.
        self.assertIn(CONCEPT.casefold(), concept_labels)

    def test_insight_survives_while_two_notes_still_support_it(self) -> None:
        notes = [self._note(slug) for slug in ("alpha", "beta", "gamma")]
        for note in notes:
            self._set_concepts(note, [CONCEPT])
        expand_knowledge_graph(self.session)
        self.assertTrue(
            any("links 3 notes" in title for title in self._concept_insight_titles())
        )

        self._retract(notes[2])
        expand_knowledge_graph(self.session)

        titles = self._concept_insight_titles()
        self.assertTrue(any("links 2 notes" in title for title in titles), titles)


if __name__ == "__main__":
    unittest.main()
