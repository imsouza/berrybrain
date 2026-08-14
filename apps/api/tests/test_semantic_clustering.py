import json
import math
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.database import Base
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    SemanticClusterAssignmentRecord,
    SemanticClusterRecord,
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
        self.assertTrue(all(item.version == 6 for item in assignments))
        self.assertEqual(first.color_id, second.color_id)
        self.assertIn("pending", {item["namespace"] for item in palette["colors"]})
        self.assertIn("vault", {item["namespace"] for item in palette["colors"]})
        self.assertEqual(palette["vaults"][0]["vaultId"], "default")

        reapplied = apply_cluster_preview(self.session, preview)
        self.assertEqual(reapplied["assignmentsUpdated"], 0)
        self.assertTrue(all(item.version == 6 for item in assignments))

    def test_algorithm_upgrade_bypasses_assignment_hysteresis(self) -> None:
        self._node("Forecasting", "Time series forecasting and prediction.")
        self._node("Prediction", "Forecasting future time series values.")
        self.session.commit()
        preview = build_cluster_preview(self.session)
        apply_cluster_preview(self.session, preview)

        assignments = list(self.session.query(SemanticClusterAssignmentRecord))
        for assignment in assignments:
            assignment.version = 3
            assignment.confidence_upper = 1.0
        self.session.commit()

        migrated = apply_cluster_preview(self.session, preview)
        self.assertEqual(migrated["assignmentsUpdated"], 2)
        self.assertTrue(all(item.version == 6 for item in assignments))

    def test_provisional_cluster_uses_neutral_label_and_singular_grammar(self) -> None:
        self.session.add(
            GraphNodeRecord(
                type="context",
                label="Temporal Forecasting",
                summary="Time series prediction",
                semantic_state="pending",
            )
        )
        self.session.commit()

        preview = build_cluster_preview(self.session)
        cluster = preview["clusters"][0]

        self.assertEqual(cluster["label"], "Context · Group 1")
        self.assertEqual(
            cluster["description"],
            "Semantic context represented by 1 graph node.",
        )

    def test_legacy_profile_terms_are_not_published_as_cluster_labels(self) -> None:
        node = self._node(
            "Legacy source phrase",
            "Legacy source prose that must never become a published cluster label.",
        )
        profile = (
            self.session.query(SemanticProfileRecord).filter_by(node_id=node.id).one()
        )
        profile.prompt_version = "enrich-node.v2"
        self.session.commit()

        preview = build_cluster_preview(self.session)

        self.assertNotIn("legacy", preview["clusters"][0]["label"].casefold())
        self.assertEqual(preview["clusters"][0]["label"], "Entity · Group 1")

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

    def test_pending_nodes_receive_provisional_context_color(self) -> None:
        node = GraphNodeRecord(
            type="concept",
            label="Time series",
            summary="Forecasting observations ordered through time.",
            semantic_state="pending",
        )
        self.session.add(node)
        self.session.commit()

        preview = build_cluster_preview(self.session)
        apply_cluster_preview(self.session, preview)

        self.assertIn(node.id, preview["provisionalNodeIds"])
        self.assertNotEqual(node.color_id, "pending")

    def test_cluster_selection_prevents_a_dominant_context_bucket(self) -> None:
        for index in range(40):
            self._node(
                f"Shared artifact {index}",
                "Shared context with intentionally equal semantic evidence.",
            )
        self.session.commit()

        preview = build_cluster_preview(self.session)
        max_cluster_size = math.ceil(2 * math.sqrt(preview["nodeCount"]))

        self.assertGreater(preview["clusterCount"], 1)
        self.assertLessEqual(
            max(len(item["memberIds"]) for item in preview["clusters"]),
            max_cluster_size,
        )

    def test_unrelated_nodes_are_not_forced_into_the_same_color_cluster(self) -> None:
        university = self._node(
            "University",
            "Academic institution, courses, students, and research programs.",
        )
        headphones = self._node(
            "Headphones",
            "Audio transducer, impedance, frequency response, and listening.",
        )
        security = self._node(
            "Security scanner",
            "Network vulnerability assessment, exploits, and defensive controls.",
        )
        self.session.commit()

        preview = build_cluster_preview(self.session)
        apply_cluster_preview(self.session, preview)

        self.assertEqual(
            len({university.cluster_id, headphones.cluster_id, security.cluster_id}),
            3,
        )

    def test_validated_edge_contributes_to_semantic_cluster_similarity(self) -> None:
        source = self._node("Alpha", "A unique source with little lexical overlap.")
        target = self._node("Omega", "A separate target using different terminology.")
        self.session.add(
            GraphEdgeRecord(
                source_node_id=source.id,
                target_node_id=target.id,
                type="related",
                confidence=0.95,
                status="confirmed",
                semantic_status="active",
            )
        )
        self.session.commit()

        apply_cluster_preview(self.session, build_cluster_preview(self.session))

        self.assertEqual(source.cluster_id, target.cluster_id)

    def test_scoped_recalculation_preserves_unaffected_cluster(self) -> None:
        first_a = self._node("Docker", "Container runtime and deployment images.")
        first_b = self._node("Containers", "Container runtime and deployment images.")
        second_a = self._node("Poetry", "Verse, meter, literary form, and rhyme.")
        second_b = self._node("Rhyme", "Verse, meter, literary form, and rhyme.")
        self.session.commit()
        apply_cluster_preview(self.session, build_cluster_preview(self.session))
        unaffected_cluster_id = second_a.cluster_id

        first_a.summary = "Container runtime, images, registries, and deployment."
        self.session.commit()
        scope = {first_a.id, first_b.id}
        preview = build_cluster_preview(self.session, node_ids=scope)
        applied = apply_cluster_preview(self.session, preview)
        self.session.refresh(second_a)
        self.session.refresh(second_b)

        self.assertTrue(applied["scoped"])
        self.assertEqual(set(applied["scopeNodeIds"]), scope)
        self.assertEqual(second_a.cluster_id, unaffected_cluster_id)
        self.assertEqual(second_b.cluster_id, unaffected_cluster_id)

    def test_scoped_recalculation_expands_to_current_cluster_members(self) -> None:
        first = self._node("Docker", "Container runtime and deployment images.")
        second = self._node("Containers", "Container runtime and deployment images.")
        self.session.commit()
        apply_cluster_preview(self.session, build_cluster_preview(self.session))

        preview = build_cluster_preview(self.session, node_ids={first.id})

        self.assertEqual(set(preview["requestedScopeNodeIds"]), {first.id})
        self.assertEqual(set(preview["scopeNodeIds"]), {first.id, second.id})

    def test_apply_repairs_pending_color_and_inactive_cluster_reference(self) -> None:
        node = self._node("Docker", "Container runtime and deployment images.")
        self.session.commit()
        preview = build_cluster_preview(self.session)
        apply_cluster_preview(self.session, preview)
        cluster = self.session.get(SemanticClusterRecord, node.cluster_id)
        node.color_id = "pending"
        cluster.status = "inactive"
        self.session.commit()

        apply_cluster_preview(self.session, build_cluster_preview(self.session))
        self.session.refresh(node)
        self.session.refresh(cluster)

        self.assertNotEqual(node.color_id, "pending")
        self.assertEqual(node.color_id, cluster.color_id)
        self.assertEqual(cluster.status, "active")


if __name__ == "__main__":
    unittest.main()
