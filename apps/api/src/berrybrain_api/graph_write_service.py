from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from collections.abc import Sequence
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.models import (
    AutomationLogRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
)


CANONICAL_NODE_TYPES = {
    "note",
    "concept",
    "entity",
    "topic",
    "source",
    "attachment",
    "insight",
    "context",
    "gap",
    "review_question",
    "study_path",
    "cluster",
}

NODE_TYPE_ALIASES = {
    "nota": "note",
    "conceito": "concept",
    "entidade": "entity",
    "topico": "topic",
    "tópico": "topic",
    "fonte": "source",
    "web_source": "source",
    "anexo": "attachment",
    "contexto": "context",
    "lacuna": "gap",
}

CANONICAL_EDGE_TYPES = {
    "explicit_link",
    "semantic_relation",
    "prerequisite",
    "example_of",
    "contrasts_with",
    "duplicates",
    "applies_to",
    "derived_from",
    "mentions",
    "supports",
    "contradicts",
}

EDGE_TYPE_ALIASES = {
    "backlink": "explicit_link",
    "semantic": "semantic_relation",
    "semantic_similarity": "semantic_relation",
    "shared_concept": "semantic_relation",
    "shared_context": "semantic_relation",
    "related": "semantic_relation",
    "duplicate": "duplicates",
    "contrast": "contrasts_with",
    "example": "example_of",
    "application": "applies_to",
    "source_supports": "supports",
    "source_contradicts": "contradicts",
    "source_expands": "derived_from",
    "insight_evidence": "derived_from",
    "insight_suggested": "derived_from",
    "attachment_related": "derived_from",
    "review_related": "derived_from",
    "topic_note": "mentions",
    "concept_note": "mentions",
}

SYMMETRIC_EDGE_TYPES = {
    "semantic_relation",
    "contrasts_with",
    "duplicates",
}

VALID_STATUSES = {"suggested", "confirmed", "ignored", "archived", "stale", "error"}
CONCEPTUAL_NODE_TYPES = {"concept", "entity", "topic", "context"}
AI_EVIDENCE_FIELDS = {
    "sourceNoteId",
    "targetNoteId",
    "sourceChunkId",
    "targetChunkId",
    "startLine",
    "endLine",
    "excerpt",
    "hash",
}


def normalize_graph_label(value: str) -> str:
    normalized = re.sub(r"[-_]+", " ", value.strip().lower())
    return re.sub(r"\s+", " ", normalized)


def canonical_node_type(value: str) -> str:
    normalized = NODE_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in CANONICAL_NODE_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Unsupported graph node type: {value}"
        )
    return normalized


def _stored_node_types(canonical_types: set[str]) -> set[str]:
    return canonical_types | {
        alias
        for alias, canonical in NODE_TYPE_ALIASES.items()
        if canonical in canonical_types
    }


def canonical_edge_type(value: str) -> str:
    normalized = EDGE_TYPE_ALIASES.get(value.strip().lower(), value.strip().lower())
    if normalized not in CANONICAL_EDGE_TYPES:
        raise HTTPException(
            status_code=422, detail=f"Unsupported graph edge type: {value}"
        )
    return normalized


def has_traceable_ai_evidence(edge: GraphEdgeRecord) -> bool:
    if edge.created_by != "ai" or edge.status in {"ignored", "archived", "stale"}:
        return True
    evidence = _json_list(edge.evidence)
    metadata = {}
    try:
        metadata = json.loads(edge.ai_notes or "{}")
    except (json.JSONDecodeError, TypeError):
        pass
    return bool(
        edge.provider
        and edge.model
        and edge.prompt_version
        and isinstance(metadata, dict)
        and metadata.get("pipeline_run_id")
        and any(
            isinstance(item, dict) and AI_EVIDENCE_FIELDS <= set(item)
            for item in evidence
        )
    )


def _json_list(raw: str | None) -> list[Any]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return value if isinstance(value, list) else []


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _node_state(node: GraphNodeRecord) -> dict[str, Any]:
    return {
        "id": node.id,
        "type": node.type,
        "label": node.label,
        "title": node.title,
        "summary": node.summary,
        "status": node.status,
        "source": node.source,
        "source_id": node.source_id,
        "source_note_ids": node.source_note_ids,
        "source_attachment_ids": node.source_attachment_ids,
        "user_notes": node.user_notes,
        "ai_summary": node.ai_summary,
        "ai_context": node.ai_context,
        "source_evidence": node.source_evidence,
        "learning_value": node.learning_value,
        "source_quality": node.source_quality,
        "provider": node.provider,
        "model": node.model,
        "prompt_version": node.prompt_version,
        "validation_status": node.validation_status,
        "graph_metadata": node.graph_metadata,
    }


def _edge_state(edge: GraphEdgeRecord) -> dict[str, Any]:
    return {
        "id": edge.id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "type": edge.type,
        "status": edge.status,
        "evidence": edge.evidence,
        "user_notes": edge.user_notes,
    }


class GraphWriteService:
    """Single mutation boundary for graph structure and user decisions."""

    def __init__(self, session: Session, autocommit: bool = True):
        self.session = session
        self.autocommit = autocommit

    def _persist(self, *records: Any) -> None:
        if self.autocommit:
            self.session.commit()
            for record in records:
                self.session.refresh(record)
        else:
            self.session.flush()

    def _record(
        self,
        action: str,
        target_type: str,
        target_id: int,
        description: str,
        before: dict[str, Any],
        after: dict[str, Any],
        reversible: bool = True,
    ) -> AutomationLogRecord:
        log = AutomationLogRecord(
            action_type=action,
            target_type=target_type,
            target_id=str(target_id),
            description=description,
            before_state=_json_dump(before),
            after_state=_json_dump(after),
            reversible=1 if reversible else 0,
        )
        self.session.add(log)
        return log

    def upsert_node(
        self,
        *,
        node_type: str,
        label: str,
        source: str = "system",
        source_id: int = 0,
        source_note_ids: list[int] | None = None,
        status: str = "suggested",
        confidence: float = 0.5,
        created_by: str = "system",
        model: str = "",
        title: str = "",
        summary: str = "",
        ai_notes: str = "",
        source_attachment_ids: list[int] | None = None,
        source_evidence: list[Any] | str | None = None,
        ai_context: str = "",
        ai_summary: str = "",
        learning_value: str = "",
        source_quality: str = "",
        validation_status: str = "unvalidated",
        provider: str = "",
        prompt_version: str = "",
        graph_metadata: dict[str, Any] | str | None = None,
    ) -> GraphNodeRecord:
        canonical_type = canonical_node_type(node_type)
        normalized_label = normalize_graph_label(label)
        if not normalized_label:
            raise HTTPException(status_code=422, detail="Graph node label is required")
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422, detail=f"Unsupported graph status: {status}"
            )

        query = select(GraphNodeRecord).where(GraphNodeRecord.type == canonical_type)
        if source_id:
            query = query.where(GraphNodeRecord.source_id == source_id)
            existing = self.session.execute(query).scalar_one_or_none()
            if existing is None and canonical_type not in {"note", "attachment"}:
                candidate_types = (
                    CONCEPTUAL_NODE_TYPES
                    if canonical_type in CONCEPTUAL_NODE_TYPES
                    else {canonical_type}
                )
                candidates = self.session.execute(
                    select(GraphNodeRecord).where(
                        GraphNodeRecord.type.in_(_stored_node_types(candidate_types))
                    )
                ).scalars()
                existing = next(
                    (
                        node
                        for node in candidates
                        if normalize_graph_label(node.label) == normalized_label
                    ),
                    None,
                )
        else:
            candidate_types = (
                CONCEPTUAL_NODE_TYPES
                if canonical_type in CONCEPTUAL_NODE_TYPES
                else {canonical_type}
            )
            candidates = self.session.execute(
                select(GraphNodeRecord).where(
                    GraphNodeRecord.type.in_(_stored_node_types(candidate_types))
                )
            ).scalars()
            existing = next(
                (
                    node
                    for node in candidates
                    if normalize_graph_label(node.label) == normalized_label
                ),
                None,
            )
        created = existing is None
        if created:
            existing = GraphNodeRecord(
                type=canonical_type,
                label=label.strip(),
                title=label.strip(),
                source=source,
                source_id=source_id,
                source_note_ids=_json_dump(sorted(set(source_note_ids or []))),
                status=status,
                confidence=max(0.0, min(1.0, confidence)),
                created_by=created_by,
                created_by_model=model,
            )
            self.session.add(existing)
            self.session.flush()
            self._record(
                "GRAPH_NODE_CREATED",
                "graph_node",
                existing.id,
                f'Graph node created: "{existing.label}"',
                {},
                _node_state(existing),
                reversible=False,
            )
        assert existing is not None
        before = {} if created else _node_state(existing)
        if not created:
            combined_ids = {
                int(value)
                for value in _json_list(existing.source_note_ids)
                + (source_note_ids or [])
                if str(value).isdigit()
            }
            existing.source_note_ids = _json_dump(sorted(combined_ids))
            existing.confidence = max(existing.confidence or 0.0, confidence)
            existing.type = canonical_type
        existing.label = label.strip()
        existing.title = title.strip() or existing.title or label.strip()
        existing.summary = summary or existing.summary
        existing.ai_notes = ai_notes or existing.ai_notes
        existing.source = source or existing.source
        existing.source_id = source_id or existing.source_id
        existing.source_attachment_ids = _json_dump(
            sorted(
                set(source_attachment_ids or _json_list(existing.source_attachment_ids))
            )
        )
        if source_evidence is not None:
            existing.source_evidence = (
                source_evidence
                if isinstance(source_evidence, str)
                else _json_dump(source_evidence)
            )
        existing.ai_context = ai_context or existing.ai_context
        existing.ai_summary = ai_summary or existing.ai_summary
        existing.learning_value = learning_value or existing.learning_value
        existing.source_quality = source_quality or existing.source_quality
        existing.validation_status = validation_status or existing.validation_status
        existing.provider = provider or existing.provider
        existing.model = model or existing.model
        existing.prompt_version = prompt_version or existing.prompt_version
        if graph_metadata is not None:
            existing.graph_metadata = (
                graph_metadata
                if isinstance(graph_metadata, str)
                else _json_dump(graph_metadata)
            )
        existing.updated_at = datetime.now(UTC)
        after = _node_state(existing)
        if not created and before != after:
            self._record(
                "GRAPH_NODE_UPSERTED",
                "graph_node",
                existing.id,
                f'Graph node updated: "{existing.label}"',
                before,
                after,
                reversible=False,
            )
        self._persist(existing)
        return existing

    def upsert_edge(
        self,
        *,
        source_node_id: int,
        target_node_id: int,
        edge_type: str,
        reason: str,
        evidence: Sequence[dict[str, Any] | str],
        confidence: float,
        source_note_ids: list[int] | None = None,
        created_by: str = "system",
        provider: str = "",
        model: str = "",
        prompt_version: str = "",
        pipeline_run_id: str = "",
        status: str = "suggested",
        label: str = "",
    ) -> GraphEdgeRecord:
        canonical_type = canonical_edge_type(edge_type)
        if source_node_id == target_node_id:
            raise HTTPException(
                status_code=422, detail="Self-referential graph edges are not allowed"
            )
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422, detail=f"Unsupported graph status: {status}"
            )
        if not reason.strip() or not evidence:
            raise HTTPException(
                status_code=422, detail="Graph edges require reason and evidence"
            )
        if (
            self.session.get(GraphNodeRecord, source_node_id) is None
            or self.session.get(GraphNodeRecord, target_node_id) is None
        ):
            raise HTTPException(
                status_code=404, detail="Graph edge endpoint node not found"
            )
        if created_by == "ai":
            self._validate_ai_evidence(
                list(evidence),
                source_note_ids or [],
                provider,
                model,
                prompt_version,
                pipeline_run_id,
            )
        if canonical_type in SYMMETRIC_EDGE_TYPES and source_node_id > target_node_id:
            source_node_id, target_node_id = target_node_id, source_node_id

        edge = self.session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.source_node_id == source_node_id,
                GraphEdgeRecord.target_node_id == target_node_id,
                GraphEdgeRecord.type == canonical_type,
            )
        ).scalar_one_or_none()
        created = edge is None
        if created:
            edge = GraphEdgeRecord(
                source_node_id=source_node_id,
                target_node_id=target_node_id,
                type=canonical_type,
            )
            self.session.add(edge)
            self.session.flush()
        assert edge is not None
        before = _edge_state(edge)
        merged_evidence = _json_list(edge.evidence) + list(evidence)
        unique_evidence = {
            _json_dump(item) if isinstance(item, dict) else str(item): item
            for item in merged_evidence
        }
        edge.label = label or edge.label or canonical_type.replace("_", " ")
        edge.reason = reason.strip()
        edge.evidence = _json_dump(list(unique_evidence.values()))
        edge.source_note_ids = _json_dump(sorted(set(source_note_ids or [])))
        edge.confidence = max(edge.confidence or 0.0, max(0.0, min(1.0, confidence)))
        edge.created_by = created_by
        edge.created_by_model = model
        edge.provider = provider
        edge.model = model
        edge.prompt_version = prompt_version
        if created or edge.status not in {"confirmed", "ignored", "archived"}:
            edge.status = status
        edge.updated_at = datetime.now(UTC)
        metadata = {"pipeline_run_id": pipeline_run_id} if pipeline_run_id else {}
        edge.ai_notes = _json_dump(metadata) if metadata else edge.ai_notes
        self._record(
            "GRAPH_EDGE_UPSERTED",
            "graph_edge",
            edge.id,
            f"Graph edge written: {edge.label}",
            before,
            _edge_state(edge),
            reversible=False,
        )
        self._persist(edge)
        return edge

    def set_node_status(self, node_id: int, status: str) -> GraphNodeRecord:
        node = self.session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422, detail=f"Unsupported graph status: {status}"
            )
        before = _node_state(node)
        node.status = status
        node.updated_at = datetime.now(UTC)
        log = self._record(
            "GRAPH_NODE_STATUS_CHANGED",
            "graph_node",
            node.id,
            f'Graph node status changed to {status}: "{node.label}"',
            before,
            _node_state(node),
        )
        self._persist(node)
        node.mutation_log_id = log.id  # type: ignore[attr-defined]
        return node

    def set_edge_status(self, edge_id: int, status: str) -> GraphEdgeRecord:
        edge = self.session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="Graph edge not found")
        if status not in VALID_STATUSES:
            raise HTTPException(
                status_code=422, detail=f"Unsupported graph status: {status}"
            )
        before = _edge_state(edge)
        edge.status = status
        edge.updated_at = datetime.now(UTC)
        log = self._record(
            "GRAPH_EDGE_STATUS_CHANGED",
            "graph_edge",
            edge.id,
            f"Graph edge status changed to {status}: {edge.label or edge.type}",
            before,
            _edge_state(edge),
        )
        self._persist(edge)
        edge.mutation_log_id = log.id  # type: ignore[attr-defined]
        return edge

    def set_node_user_notes(self, node_id: int, notes: str) -> GraphNodeRecord:
        node = self.session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        before = _node_state(node)
        node.user_notes = notes
        node.updated_at = datetime.now(UTC)
        self._record(
            "GRAPH_NODE_NOTES_CHANGED",
            "graph_node",
            node.id,
            f'User notes updated for graph node "{node.label}"',
            before,
            _node_state(node),
        )
        self._persist(node)
        return node

    def set_edge_user_notes(self, edge_id: int, notes: str) -> GraphEdgeRecord:
        edge = self.session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="Graph edge not found")
        before = _edge_state(edge)
        edge.user_notes = notes
        edge.updated_at = datetime.now(UTC)
        self._record(
            "GRAPH_EDGE_NOTES_CHANGED",
            "graph_edge",
            edge.id,
            "User notes updated for graph edge",
            before,
            _edge_state(edge),
        )
        self._persist(edge)
        return edge

    def update_node_enrichment(
        self, node_id: int, values: dict[str, Any]
    ) -> GraphNodeRecord:
        node = self.session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        allowed = {
            "ai_summary",
            "ai_context",
            "source_evidence",
            "learning_value",
            "source_quality",
            "provider",
            "model",
            "prompt_version",
        }
        changes = {
            key: value
            for key, value in values.items()
            if key in allowed and value is not None and str(value).strip()
        }
        if not changes:
            raise HTTPException(
                status_code=422, detail="Enrichment has no semantic content"
            )
        before = _node_state(node)
        for key, value in changes.items():
            setattr(node, key, value)
        node.generated_at = datetime.now(UTC)
        node.updated_at = datetime.now(UTC)
        self._record(
            "GRAPH_NODE_ENRICHED",
            "graph_node",
            node.id,
            f'Graph node enriched: "{node.label}"',
            before,
            _node_state(node),
        )
        self._persist(node)
        return node

    def delete_node(self, node_id: int) -> GraphNodeRecord:
        node = self.session.get(GraphNodeRecord, node_id)
        if node is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        if node.type == "note":
            raise HTTPException(
                status_code=409,
                detail="Vault note nodes cannot be deleted from the graph",
            )
        before = _node_state(node)
        edges = list(
            self.session.execute(
                select(GraphEdgeRecord).where(
                    (GraphEdgeRecord.source_node_id == node.id)
                    | (GraphEdgeRecord.target_node_id == node.id)
                )
            ).scalars()
        )
        edge_states = [_edge_state(edge) for edge in edges]
        for edge in edges:
            self.session.delete(edge)
        self.session.delete(node)
        self._record(
            "GRAPH_NODE_DELETED",
            "graph_node",
            node.id,
            f'Graph node deleted: "{node.label}"',
            {**before, "edges": edge_states},
            {"deleted": True},
            reversible=False,
        )
        self._persist()
        return node

    def delete_edge(self, edge_id: int, *, reason: str = "Graph edge removed") -> bool:
        edge = self.session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            return False
        before = _edge_state(edge)
        self.session.delete(edge)
        self._record(
            "GRAPH_EDGE_DELETED",
            "graph_edge",
            edge.id,
            reason,
            before,
            {"deleted": True},
            reversible=False,
        )
        self._persist()
        return True

    def deduplicate_edges(self) -> int:
        """Canonicalize and collapse duplicate edges during graph maintenance."""
        edges = list(self.session.execute(select(GraphEdgeRecord)).scalars())
        seen: dict[tuple[int, int, str], GraphEdgeRecord] = {}
        deleted = 0
        for edge in edges:
            try:
                edge.type = canonical_edge_type(edge.type)
            except HTTPException:
                edge.type = "semantic_relation"
            if (
                edge.type in SYMMETRIC_EDGE_TYPES
                and edge.source_node_id > edge.target_node_id
            ):
                edge.source_node_id, edge.target_node_id = (
                    edge.target_node_id,
                    edge.source_node_id,
                )
            if edge.source_node_id == edge.target_node_id:
                self.session.delete(edge)
                deleted += 1
                continue
            key = (edge.source_node_id, edge.target_node_id, edge.type)
            existing = seen.get(key)
            if existing is None:
                seen[key] = edge
                continue
            before = _edge_state(existing)
            evidence = _json_list(existing.evidence) + _json_list(edge.evidence)
            unique_evidence = {
                _json_dump(item) if isinstance(item, dict) else str(item): item
                for item in evidence
            }
            existing.evidence = _json_dump(list(unique_evidence.values()))
            existing.source_note_ids = _json_dump(
                sorted(
                    {
                        int(value)
                        for value in _json_list(existing.source_note_ids)
                        + _json_list(edge.source_note_ids)
                        if str(value).isdigit()
                    }
                )
            )
            existing.confidence = max(
                existing.confidence or 0.0, edge.confidence or 0.0
            )
            if not existing.reason and edge.reason:
                existing.reason = edge.reason
            if edge.status == "confirmed":
                existing.status = "confirmed"
            self.session.delete(edge)
            self._record(
                "GRAPH_EDGE_DEDUPLICATED",
                "graph_edge",
                existing.id,
                "Duplicate graph edge consolidated",
                before,
                _edge_state(existing),
                reversible=False,
            )
            deleted += 1
        if deleted:
            self._persist(*seen.values())
        return deleted

    def deduplicate_nodes(self) -> int:
        """Collapse duplicate persisted nodes and rewire their neighborhoods."""
        nodes = list(self.session.execute(select(GraphNodeRecord)).scalars())
        by_key: dict[tuple[str, str], list[GraphNodeRecord]] = {}
        for node in nodes:
            try:
                node_type = canonical_node_type(node.type)
            except HTTPException:
                node_type = node.type
            if node_type == "insight":
                continue
            identity = (
                f"source:{node.source_id}"
                if node_type == "note" and node.source_id
                else normalize_graph_label(node.label)
            )
            if identity:
                by_key.setdefault((node_type, identity), []).append(node)

        merged = 0
        for group in by_key.values():
            if len(group) < 2:
                continue
            group.sort(key=lambda item: item.confidence or 0.0, reverse=True)
            survivor = group[0]
            survivor.type = canonical_node_type(survivor.type)
            for victim in group[1:]:
                before = {
                    "survivor": _node_state(survivor),
                    "victim": _node_state(victim),
                }
                edges = list(
                    self.session.execute(
                        select(GraphEdgeRecord).where(
                            (GraphEdgeRecord.source_node_id == victim.id)
                            | (GraphEdgeRecord.target_node_id == victim.id)
                        )
                    ).scalars()
                )
                for edge in edges:
                    if edge.source_node_id == victim.id:
                        edge.source_node_id = survivor.id
                    if edge.target_node_id == victim.id:
                        edge.target_node_id = survivor.id
                survivor.source_note_ids = _json_dump(
                    sorted(
                        {
                            int(value)
                            for value in _json_list(survivor.source_note_ids)
                            + _json_list(victim.source_note_ids)
                            if str(value).isdigit()
                        }
                    )
                )
                survivor.confidence = max(
                    survivor.confidence or 0.0, victim.confidence or 0.0
                )
                self.session.delete(victim)
                self._record(
                    "GRAPH_NODE_DEDUPLICATED",
                    "graph_node",
                    survivor.id,
                    f'Duplicate graph node consolidated: "{victim.label}"',
                    before,
                    _node_state(survivor),
                    reversible=False,
                )
                merged += 1
        if merged:
            self.session.flush()
            self.deduplicate_edges()
            self._persist()
        return merged

    def update_edge_type(self, edge_id: int, edge_type: str) -> GraphEdgeRecord:
        edge = self.session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="Graph edge not found")
        canonical_type = canonical_edge_type(edge_type)
        duplicate = self.session.execute(
            select(GraphEdgeRecord).where(
                GraphEdgeRecord.id != edge.id,
                GraphEdgeRecord.source_node_id == edge.source_node_id,
                GraphEdgeRecord.target_node_id == edge.target_node_id,
                GraphEdgeRecord.type == canonical_type,
                GraphEdgeRecord.status != "archived",
            )
        ).scalar_one_or_none()
        if duplicate is not None:
            raise HTTPException(
                status_code=409,
                detail="Changing this type would create a duplicate graph edge",
            )
        before = _edge_state(edge)
        edge.type = canonical_type
        edge.updated_at = datetime.now(UTC)
        self._record(
            "GRAPH_EDGE_TYPE_CHANGED",
            "graph_edge",
            edge.id,
            f"Graph edge type changed to {edge.type}",
            before,
            _edge_state(edge),
        )
        self._persist(edge)
        return edge

    def merge_nodes(
        self, survivor_id: int, merged_node_id: int
    ) -> tuple[GraphNodeRecord, AutomationLogRecord]:
        if survivor_id == merged_node_id:
            raise HTTPException(
                status_code=422, detail="A graph node cannot merge into itself"
            )
        survivor = self.session.get(GraphNodeRecord, survivor_id)
        merged = self.session.get(GraphNodeRecord, merged_node_id)
        if survivor is None or merged is None:
            raise HTTPException(status_code=404, detail="Graph node not found")
        if survivor.type == "note" or merged.type == "note":
            raise HTTPException(
                status_code=409,
                detail="Vault note nodes cannot be merged; connect the notes instead",
            )
        if canonical_node_type(survivor.type) != canonical_node_type(merged.type):
            raise HTTPException(
                status_code=409, detail="Only nodes of the same type can merge"
            )

        affected_edges = list(
            self.session.execute(
                select(GraphEdgeRecord).where(
                    (GraphEdgeRecord.source_node_id == merged.id)
                    | (GraphEdgeRecord.target_node_id == merged.id)
                )
            ).scalars()
        )
        before = {
            "survivor": _node_state(survivor),
            "merged": _node_state(merged),
            "edges": [_edge_state(edge) for edge in affected_edges],
        }
        source_ids = {
            int(value)
            for value in _json_list(survivor.source_note_ids)
            + _json_list(merged.source_note_ids)
            if str(value).isdigit()
        }
        survivor.source_note_ids = _json_dump(sorted(source_ids))
        survivor.confidence = max(survivor.confidence or 0.0, merged.confidence or 0.0)
        survivor.updated_at = datetime.now(UTC)
        merged.status = "archived"
        merged.updated_at = datetime.now(UTC)

        for edge in affected_edges:
            if edge.source_node_id == merged.id:
                edge.source_node_id = survivor.id
            if edge.target_node_id == merged.id:
                edge.target_node_id = survivor.id
            edge.updated_at = datetime.now(UTC)
            if edge.source_node_id == edge.target_node_id:
                edge.status = "archived"
                continue
            duplicate = self.session.execute(
                select(GraphEdgeRecord).where(
                    GraphEdgeRecord.id != edge.id,
                    GraphEdgeRecord.source_node_id == edge.source_node_id,
                    GraphEdgeRecord.target_node_id == edge.target_node_id,
                    GraphEdgeRecord.type == edge.type,
                    GraphEdgeRecord.status != "archived",
                )
            ).scalar_one_or_none()
            if duplicate is not None:
                duplicate.evidence = _json_dump(
                    _json_list(duplicate.evidence) + _json_list(edge.evidence)
                )
                duplicate.confidence = max(
                    duplicate.confidence or 0.0, edge.confidence or 0.0
                )
                edge.status = "archived"

        after = {
            "survivor": _node_state(survivor),
            "merged": _node_state(merged),
            "edges": [_edge_state(edge) for edge in affected_edges],
        }
        log = self._record(
            "GRAPH_NODES_MERGED",
            "graph_node",
            survivor.id,
            f'Graph node "{merged.label}" merged into "{survivor.label}"',
            before,
            after,
        )
        self._persist(survivor, log)
        return survivor, log

    def add_manual_evidence(
        self, edge_id: int, excerpt: str, source_note_id: int | None = None
    ) -> GraphEdgeRecord:
        edge = self.session.get(GraphEdgeRecord, edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail="Graph edge not found")
        if not excerpt.strip():
            raise HTTPException(status_code=422, detail="Evidence excerpt is required")
        before = _edge_state(edge)
        evidence = _json_list(edge.evidence)
        evidence.append(
            {
                "kind": "manual",
                "sourceNoteId": source_note_id,
                "excerpt": excerpt.strip(),
                "hash": hashlib.sha256(excerpt.strip().encode()).hexdigest(),
            }
        )
        edge.evidence = _json_dump(evidence)
        edge.updated_at = datetime.now(UTC)
        self._record(
            "GRAPH_EDGE_EVIDENCE_ADDED",
            "graph_edge",
            edge.id,
            "Manual evidence added to graph edge",
            before,
            _edge_state(edge),
        )
        self._persist(edge)
        return edge

    def undo(self, mutation_log_id: int) -> AutomationLogRecord:
        log = self.session.get(AutomationLogRecord, mutation_log_id)
        if log is None:
            raise HTTPException(status_code=404, detail="Graph mutation not found")
        if not log.reversible or log.reverted_at is not None:
            raise HTTPException(
                status_code=409, detail="Graph mutation cannot be undone"
            )
        before = json.loads(log.before_state or "{}")
        target: GraphNodeRecord | GraphEdgeRecord | None
        if log.action_type == "GRAPH_NODES_MERGED":
            self._undo_node_merge(before)
            target = self.session.get(GraphNodeRecord, int(log.target_id))
        elif log.target_type == "graph_node":
            target = self.session.get(GraphNodeRecord, int(log.target_id))
        elif log.target_type == "graph_edge":
            target = self.session.get(GraphEdgeRecord, int(log.target_id))
        else:
            target = None
        if target is None:
            raise HTTPException(
                status_code=404, detail="Graph mutation target not found"
            )
        for field in (
            "type",
            "status",
            "evidence",
            "user_notes",
            "ai_summary",
            "ai_context",
            "source_evidence",
            "learning_value",
            "source_quality",
            "provider",
            "model",
            "prompt_version",
        ):
            if field in before and hasattr(target, field):
                setattr(target, field, before[field])
        target.updated_at = datetime.now(UTC)
        undo_log = self._record(
            "GRAPH_MUTATION_UNDONE",
            log.target_type,
            int(log.target_id),
            f"Graph mutation {log.id} undone",
            json.loads(log.after_state or "{}"),
            before,
            reversible=False,
        )
        self.session.flush()
        log.reverted_at = datetime.now(UTC)
        log.reverted_by_log_id = undo_log.id
        self._persist(log)
        return log

    def _undo_node_merge(self, before: dict[str, Any]) -> None:
        for key in ("survivor", "merged"):
            state = before.get(key) or {}
            node = self.session.get(GraphNodeRecord, state.get("id"))
            if node is None:
                raise HTTPException(
                    status_code=409, detail="Merged graph node no longer exists"
                )
            for field in ("type", "label", "status", "source_note_ids", "user_notes"):
                if field in state:
                    setattr(node, field, state[field])
            node.updated_at = datetime.now(UTC)
        for state in before.get("edges") or []:
            edge = self.session.get(GraphEdgeRecord, state.get("id"))
            if edge is None:
                raise HTTPException(
                    status_code=409, detail="Merged graph edge no longer exists"
                )
            for field in (
                "source_node_id",
                "target_node_id",
                "type",
                "status",
                "evidence",
                "user_notes",
            ):
                if field in state:
                    setattr(edge, field, state[field])
            edge.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate_ai_evidence(
        evidence: list[dict[str, Any] | str],
        source_note_ids: list[int],
        provider: str,
        model: str,
        prompt_version: str,
        pipeline_run_id: str,
    ) -> None:
        if not source_note_ids:
            raise HTTPException(
                status_code=422, detail="AI graph edges require source note IDs"
            )
        if not provider or not model or not prompt_version or not pipeline_run_id:
            raise HTTPException(
                status_code=422,
                detail="AI graph edges require provider, model, prompt version, and pipeline run",
            )
        if not any(
            isinstance(item, dict) and AI_EVIDENCE_FIELDS <= set(item)
            for item in evidence
        ):
            raise HTTPException(
                status_code=422,
                detail="AI graph edges require structured chunk evidence",
            )
