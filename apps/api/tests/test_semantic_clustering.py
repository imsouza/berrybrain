import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    SemanticClusterAssignmentRecord,
    SemanticProfileRecord,
)
from berrybrain_api.semantic_clustering import (
    apply_cluster_preview,
    build_cluster_preview,
    serialize_palette,
)


class SemanticClusteringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=self.engine)
        self.session = sessionmaker(bind=self.engine)()

    def tearDown(self) -> None:
        self.session.close()
        self.engine.dispose()

    def _node(self, label: str, meaning: str) -> GraphNodeRecord:
        node = GraphNodeRecord(
            type="entity",
            label=label,
            summary=meaning,
            semantic_state="completed",
        )
        self.session.add(node)
        self.session.flush()
        self.session.add(
            SemanticProfileRecord(
                node_id=node.id,
                source_fingerprint=f"source-{node.id}",
                profile_json=json.dumps(
                    {
                        "meaning_in_context": meaning,
                        "why_it_matters_here": meaning,
                        "supported_findings": [meaning],
                        "inferences": [],
                    }
                ),
                status="completed",
            )
        )
        return node

    def test_semantic_context_splits_homonyms_and_groups_related_nodes(self) -> None:
        driver = self._node(
            "Roberto Carlos",
            "Brazilian racing driver in motorsport competition and automobile events.",
        )
        race = self._node(
            "Motorsport",
            "Automobile racing competition with drivers and track events.",
        )
        singer = self._node(
            "Roberto Carlos",
            "Brazilian singer and songwriter known for romantic music albums.",
        )
        self.session.add(
            GraphEdgeRecord(
                source_node_id=driver.id,
                target_node_id=race.id,
                type="related",
                confidence=0.95,
            )
        )
        self.session.commit()

        preview = build_cluster_preview(self.session)
        member_sets = [set(item["memberIds"]) for item in preview["clusters"]]

        self.assertIn({driver.id, race.id}, member_sets)
        self.assertTrue(
            any(
                singer.id in members and driver.id not in members
                for members in member_sets
            )
        )

    def test_apply_is_stable_and_reserves_pending_and_vault_namespaces(self) -> None:
        first = self._node("Docker", "Container runtime and reproducible deployment.")
        second = self._node(
            "Containers", "Container runtime for reproducible services."
        )
        self.session.commit()
        preview = build_cluster_preview(self.session)

        applied = apply_cluster_preview(self.session, preview)
        assignments = list(self.session.query(SemanticClusterAssignmentRecord))
        palette = serialize_palette(self.session)

        self.assertTrue(applied["applied"])
        self.assertEqual(len(assignments), 2)
        self.assertEqual(first.color_id, second.color_id)
        self.assertIn("pending", {item["namespace"] for item in palette["colors"]})
        self.assertIn("vault", {item["namespace"] for item in palette["colors"]})
        self.assertEqual(palette["vaults"][0]["vaultId"], "default")

    def test_vault_nodes_do_not_join_semantic_clusters(self) -> None:
        vault = GraphNodeRecord(
            type="vault",
            label="Work",
            vault_id="work",
            semantic_state="completed",
        )
        self.session.add(vault)
        self.session.flush()
        self.session.add(
            SemanticProfileRecord(
                node_id=vault.id,
                source_fingerprint="vault-source",
                profile_json=json.dumps(
                    {
                        "meaning_in_context": "Container runtime",
                        "supported_findings": ["Docker container runtime"],
                    }
                ),
                status="completed",
            )
        )
        self.session.commit()

        preview = build_cluster_preview(self.session)
        apply_cluster_preview(self.session, preview)
        self.session.refresh(vault)

        self.assertNotIn(vault.id, preview["unresolvedNodeIds"])
        self.assertFalse(
            any(vault.id in item["memberIds"] for item in preview["clusters"])
        )
        self.assertIsNone(vault.cluster_id)
        self.assertTrue(vault.color_id.startswith("vault-"))


if __name__ == "__main__":
    unittest.main()
