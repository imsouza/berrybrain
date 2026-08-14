from types import SimpleNamespace

from berrybrain_api.artifact_state import (
    apply_quality_verdict,
    is_default_visible_edge,
    is_default_visible_node,
)


def artifact(**overrides):
    values = {
        "semantic_status": "active",
        "status": "suggested",
        "quality_gate_status": "pending",
        "type": "concept",
        "created_by": "ai",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_failed_quality_verdict_quarantines_semantic_artifact():
    node = artifact()

    apply_quality_verdict(node, "insufficient_evidence")

    assert node.quality_gate_status == "insufficient_evidence"
    assert node.semantic_status == "quarantined"
    assert not is_default_visible_node(node)


def test_source_notes_remain_visible_while_quality_is_pending():
    node = artifact(type="note", status="confirmed", created_by="system")

    assert is_default_visible_node(node)


def test_pending_ai_semantic_node_is_not_default_visible():
    assert not is_default_visible_node(artifact())


def test_passed_ai_semantic_node_is_default_visible():
    assert is_default_visible_node(artifact(quality_gate_status="passed"))


def test_only_deterministic_pending_system_edges_are_default_visible():
    provenance = artifact(type="derived_from", created_by="system")
    semantic = artifact(type="related", created_by="system")

    assert is_default_visible_edge(provenance)
    assert not is_default_visible_edge(semantic)


def test_rejected_deterministic_edge_is_never_visible():
    edge = artifact(
        type="derived_from",
        created_by="system",
        quality_gate_status="rejected",
    )

    assert not is_default_visible_edge(edge)
