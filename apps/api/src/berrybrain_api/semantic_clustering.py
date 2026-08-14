from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.confidence import ConfidenceSignal, estimate_confidence
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    GraphPaletteRecord,
    SemanticClusterAssignmentRecord,
    SemanticClusterRecord,
    SemanticProfileRecord,
    VaultVisualIdentityRecord,
)
from berrybrain_api.semantic_enrichment import SEMANTIC_PROMPT_VERSION

ALGORITHM_VERSION = 6
PENDING_COLOR_ID = "pending"
MIN_CLUSTER_COHESION = 0.12
RELATIONSHIP_SIMILARITY_WEIGHT = 0.4
TOKEN_RE = re.compile(r"[^\W_]{3,}", re.UNICODE)
STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "but",
    "concept",
    "concepts",
    "detected",
    "evidence",
    "for",
    "from",
    "graph",
    "metadata",
    "node",
    "nodes",
    "note",
    "notes",
    "the",
    "this",
    "suggested",
    "was",
    "with",
}


def build_cluster_preview(
    session: Session, node_ids: set[int] | None = None
) -> dict[str, Any]:
    requested_node_ids = set(node_ids) if node_ids is not None else None
    if node_ids:
        cluster_ids = {
            int(value)
            for value in session.execute(
                select(GraphNodeRecord.cluster_id).where(
                    GraphNodeRecord.id.in_(node_ids),
                    GraphNodeRecord.cluster_id.is_not(None),
                )
            ).scalars()
            if value is not None
        }
        if cluster_ids:
            node_ids = set(node_ids)
            node_ids.update(
                session.execute(
                    select(GraphNodeRecord.id).where(
                        GraphNodeRecord.cluster_id.in_(cluster_ids),
                        accepted_node_clause(include_provisional=True),
                    )
                ).scalars()
            )
    node_query = select(GraphNodeRecord).where(
        accepted_node_clause(include_provisional=True),
        GraphNodeRecord.type != "vault",
    )
    if node_ids is not None:
        node_query = node_query.where(GraphNodeRecord.id.in_(node_ids))
    nodes = list(session.execute(node_query.order_by(GraphNodeRecord.id)).scalars())
    selected_node_ids = {node.id for node in nodes}
    edges = list(
        session.execute(
            select(GraphEdgeRecord).where(
                accepted_edge_clause(include_provisional=True),
            )
        ).scalars()
    )
    latest_profiles: dict[int, SemanticProfileRecord] = {}
    for profile in session.execute(
        select(SemanticProfileRecord).order_by(SemanticProfileRecord.id)
    ).scalars():
        if profile.status == "completed":
            latest_profiles[profile.node_id] = profile

    neighbors: dict[int, set[int]] = defaultdict(set)
    edge_confidence: dict[tuple[int, int], float] = {}
    for edge in edges:
        if (
            edge.source_node_id not in selected_node_ids
            or edge.target_node_id not in selected_node_ids
        ):
            continue
        neighbors[edge.source_node_id].add(edge.target_node_id)
        neighbors[edge.target_node_id].add(edge.source_node_id)
        key = tuple(sorted((edge.source_node_id, edge.target_node_id)))
        edge_confidence[key] = max(edge_confidence.get(key, 0.0), edge.confidence)

    node_by_id = {node.id: node for node in nodes}
    vectors: dict[int, Counter[str]] = {}
    provisional_ids: list[int] = []
    for node in nodes:
        profile = latest_profiles.get(node.id)
        context_labels = " ".join(
            node_by_id[item].label
            for item in sorted(neighbors[node.id])
            if item in node_by_id
        )
        vectors[node.id] = _semantic_vector(node, profile, context_labels)
        if profile is None or node.semantic_state != "completed":
            provisional_ids.append(node.id)

    components, memberships = _select_clusters(vectors, edge_confidence)

    clusters: list[dict[str, Any]] = []
    claimed_cluster_ids: set[int] = set()
    for cluster_position, member_ids in enumerate(
        sorted(components, key=lambda item: min(item)), start=1
    ):
        centroid = Counter[str]()
        display_centroid = Counter[str]()
        for node_id in member_ids:
            centroid.update(vectors[node_id])
            profile = latest_profiles.get(node_id)
            if profile and profile.prompt_version == SEMANTIC_PROMPT_VERSION:
                display_centroid.update(_profile_display_tokens(profile))
        semantic_terms = [token for token, _ in centroid.most_common(5)]
        terms = [token for token, _ in display_centroid.most_common(5)]
        if not terms:
            node_types = Counter(
                _display_node_type(node_by_id[node_id].type) for node_id in member_ids
            )
            primary_type = node_types.most_common(1)[0][0]
            terms = [primary_type, f"Group {cluster_position}"]
        label = " · ".join(terms[:3])
        previous_clusters = Counter(
            int(node_by_id[node_id].cluster_id)
            for node_id in member_ids
            if node_by_id[node_id].cluster_id is not None
            and int(node_by_id[node_id].cluster_id) not in claimed_cluster_ids
        )
        reusable_cluster = None
        for cluster_id, _ in previous_clusters.most_common():
            reusable_cluster = session.get(SemanticClusterRecord, cluster_id)
            if reusable_cluster is not None:
                claimed_cluster_ids.add(cluster_id)
                break
        if reusable_cluster is not None:
            stable_key = reusable_cluster.stable_key
        else:
            member_signature = sorted(
                f"{node_by_id[node_id].type}:"
                f"{node_by_id[node_id].canonical_label or node_by_id[node_id].label.casefold()}"
                for node_id in member_ids
            )
            signature = "|".join([*semantic_terms, *member_signature])
            stable_key = (
                "semantic-" + hashlib.sha256(signature.encode("utf-8")).hexdigest()[:20]
            )
        member_confidence = {node_id: memberships[node_id] for node_id in member_ids}
        clusters.append(
            {
                "stableKey": stable_key,
                "label": label,
                "description": (
                    f"Semantic context represented by {len(member_ids)} graph "
                    f"{'node' if len(member_ids) == 1 else 'nodes'}."
                ),
                "terms": terms,
                "memberIds": member_ids,
                "memberConfidence": member_confidence,
            }
        )
    return {
        "algorithmVersion": ALGORITHM_VERSION,
        "nodeCount": len(nodes),
        "clusterCount": len(clusters),
        "unresolvedNodeIds": [],
        "provisionalNodeIds": provisional_ids,
        "clusters": clusters,
        "scoped": requested_node_ids is not None,
        "scopeNodeIds": sorted(node_ids or []),
        "requestedScopeNodeIds": sorted(requested_node_ids or []),
    }


def apply_cluster_preview(session: Session, preview: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(UTC)
    _ensure_pending_palette(session)
    scoped = bool(preview.get("scoped"))
    scope_node_ids = {
        int(value) for value in preview.get("scopeNodeIds", []) if str(value).isdigit()
    }
    previous_cluster_ids = {
        int(value)
        for value in session.execute(
            select(GraphNodeRecord.cluster_id).where(
                GraphNodeRecord.id.in_(scope_node_ids),
                GraphNodeRecord.cluster_id.is_not(None),
            )
        ).scalars()
        if value is not None
    }
    active_ids: set[int] = set()
    assignments_updated = 0
    for position, item in enumerate(preview["clusters"]):
        cluster = session.execute(
            select(SemanticClusterRecord).where(
                SemanticClusterRecord.stable_key == item["stableKey"]
            )
        ).scalar_one_or_none()
        color_id = _ensure_semantic_palette(session, item["stableKey"], position)
        if cluster is None:
            cluster = SemanticClusterRecord(
                stable_key=item["stableKey"],
                label=item["label"],
                description=item["description"],
                centroid_ref=json.dumps(item["terms"], ensure_ascii=False),
                color_id=color_id,
                version=ALGORITHM_VERSION,
            )
            session.add(cluster)
            session.flush()
        else:
            centroid_ref = json.dumps(item["terms"], ensure_ascii=False)
            cluster_changed = any(
                (
                    cluster.label != item["label"],
                    cluster.description != item["description"],
                    cluster.centroid_ref != centroid_ref,
                    cluster.color_id != color_id,
                    cluster.version != ALGORITHM_VERSION,
                    cluster.status != "active",
                )
            )
            cluster.label = item["label"]
            cluster.description = item["description"]
            cluster.centroid_ref = centroid_ref
            cluster.color_id = color_id
            cluster.version = ALGORITHM_VERSION
            cluster.status = "active"
            if cluster_changed:
                cluster.updated_at = now
        active_ids.add(cluster.id)
        for node_id in item["memberIds"]:
            confidence = float(item["memberConfidence"][node_id])
            assignments_updated += _apply_assignment(
                session,
                node_id=node_id,
                cluster=cluster,
                confidence=confidence,
                terms=item["terms"],
                now=now,
            )

    unresolved_ids = set(preview["unresolvedNodeIds"])
    if unresolved_ids:
        for node in session.execute(
            select(GraphNodeRecord).where(GraphNodeRecord.id.in_(unresolved_ids))
        ).scalars():
            node.cluster_id = None
            node.color_id = PENDING_COLOR_ID
            node.color_confidence = 0.0
            node.color_reason = "Semantic classification pending or unresolved."
            node.color_updated_at = now

    referenced_cluster_ids = {
        int(value)
        for value in session.execute(
            select(GraphNodeRecord.cluster_id).where(
                GraphNodeRecord.cluster_id.is_not(None),
                accepted_node_clause(include_provisional=True),
            )
        ).scalars()
        if value is not None
    }
    clusters_to_check = (
        session.execute(select(SemanticClusterRecord)).scalars()
        if not scoped
        else session.execute(
            select(SemanticClusterRecord).where(
                SemanticClusterRecord.id.in_(previous_cluster_ids | active_ids)
            )
        ).scalars()
    )
    for cluster in clusters_to_check:
        expected_status = (
            "active" if cluster.id in referenced_cluster_ids else "inactive"
        )
        if cluster.status != expected_status:
            cluster.status = expected_status
            cluster.updated_at = now
    synchronized_nodes = session.execute(
        select(GraphNodeRecord).where(
            GraphNodeRecord.cluster_id.is_not(None),
            accepted_node_clause(include_provisional=True),
        )
    ).scalars()
    for node in synchronized_nodes:
        cluster = session.get(SemanticClusterRecord, node.cluster_id)
        if cluster is None or node.color_id == cluster.color_id:
            continue
        node.color_id = cluster.color_id
        node.color_updated_at = now
    _ensure_vault_identities(session, now)
    session.commit()
    return {
        **preview,
        "applied": True,
        "assignmentsUpdated": assignments_updated,
    }


def serialize_clusters(session: Session) -> list[dict[str, Any]]:
    counts = dict(
        session.execute(
            select(
                GraphNodeRecord.cluster_id,
                func.count(GraphNodeRecord.id),
            )
            .where(
                GraphNodeRecord.cluster_id.is_not(None),
                accepted_node_clause(include_provisional=True),
            )
            .group_by(GraphNodeRecord.cluster_id)
        ).all()
    )
    return [
        {
            "id": cluster.id,
            "stableKey": cluster.stable_key,
            "label": cluster.label,
            "description": cluster.description,
            "colorId": cluster.color_id,
            "version": cluster.version,
            "status": cluster.status,
            "nodeCount": counts.get(cluster.id, 0),
        }
        for cluster in session.execute(
            select(SemanticClusterRecord).order_by(SemanticClusterRecord.id)
        ).scalars()
    ]


def serialize_palette(session: Session) -> dict[str, Any]:
    colors = [
        {
            "colorId": item.color_id,
            "oklch": item.oklch,
            "lightHex": item.light_hex,
            "darkHex": item.dark_hex,
            "border": item.border,
            "text": item.text,
            "namespace": item.namespace,
            "accessibility": _json_object(item.accessibility_json),
        }
        for item in session.execute(
            select(GraphPaletteRecord).order_by(
                GraphPaletteRecord.namespace, GraphPaletteRecord.id
            )
        ).scalars()
    ]
    vaults = [
        {
            "vaultId": item.vault_id,
            "colorId": item.color_id,
            "icon": item.icon,
        }
        for item in session.execute(
            select(VaultVisualIdentityRecord).order_by(VaultVisualIdentityRecord.id)
        ).scalars()
    ]
    return {"colors": colors, "vaults": vaults, "pendingColorId": PENDING_COLOR_ID}


def _semantic_vector(
    node: GraphNodeRecord,
    profile: SemanticProfileRecord | None,
    context_labels: str,
) -> Counter[str]:
    profile_data = _json_object(profile.profile_json) if profile is not None else {}
    profile_text = " ".join(
        _flatten_text(profile_data.get(key))
        for key in (
            "meaning_in_context",
            "why_it_matters_here",
            "supported_findings",
            "inferences",
        )
    )
    direct = _tokens(f"{node.label} {node.title} {node.summary} {profile_text}")
    context = _tokens(context_labels)
    vector = Counter({token: count * 3 for token, count in direct.items()})
    vector.update(context)
    if not vector:
        vector.update(_tokens(f"{node.type} {node.label}"))
    return vector


def _profile_display_tokens(profile: SemanticProfileRecord) -> Counter[str]:
    data = _json_object(profile.profile_json)
    return _tokens(
        " ".join(
            _flatten_text(data.get(key))
            for key in (
                "meaning_in_context",
                "use_in_notes",
                "why_it_matters_here",
                "supported_findings",
                "inferences",
            )
        )
    )


def _display_node_type(value: str) -> str:
    normalized = str(value or "node").replace("_", " ").strip()
    if normalized == "gap":
        normalized = "knowledge gap"
    return normalized.capitalize()


def _select_clusters(
    vectors: dict[int, Counter[str]],
    edge_confidence: dict[tuple[int, int], float],
) -> tuple[list[list[int]], dict[int, float]]:
    node_ids = sorted(vectors)
    if not node_ids:
        return [], {}
    if len(node_ids) == 1:
        return [node_ids], {node_ids[0]: 1.0}

    similarities: dict[tuple[int, int], float] = {}
    for index, left in enumerate(node_ids):
        for right in node_ids[index + 1 :]:
            lexical = _weighted_jaccard(vectors[left], vectors[right])
            relationship = edge_confidence.get((left, right), 0.0)
            similarities[(left, right)] = lexical + (
                (1 - lexical) * relationship * RELATIONSHIP_SIMILARITY_WEIGHT
            )

    max_cluster_size = max(2, math.ceil(2 * math.sqrt(len(node_ids))))
    max_k = min(len(node_ids), max(2, math.ceil(math.sqrt(len(node_ids)))))
    min_k = min(max_k, max(2, math.ceil(len(node_ids) / max_cluster_size)))
    candidates = range(min_k, max_k + 1) if len(node_ids) > 2 else range(1, 2)
    best_groups: list[list[int]] = [node_ids]
    best_score = float("-inf")
    for cluster_count in candidates:
        groups = _k_medoids(node_ids, similarities, cluster_count)
        score = _cluster_selection_score(
            groups,
            similarities,
            node_count=len(node_ids),
            max_cluster_size=max_cluster_size,
        )
        if score > best_score:
            best_score = score
            best_groups = groups

    best_groups = _enforce_cluster_capacity(
        best_groups, similarities, max_cluster_size=max_cluster_size
    )
    best_groups = _split_weakly_connected_groups(best_groups, similarities)

    memberships: dict[int, float] = {}
    medoids = [_medoid(group, similarities) for group in best_groups]
    for group, medoid in zip(best_groups, medoids, strict=True):
        for node_id in group:
            peers = [member for member in group if member != node_id]
            alternatives = [
                _similarity(node_id, other, similarities)
                for other in medoids
                if other != medoid
            ]
            alternative = max(alternatives, default=0.0)
            own = (
                sum(_similarity(node_id, peer, similarities) for peer in peers)
                / len(peers)
                if peers
                else 1 - alternative
            )
            margin = max(0.0, own - alternative)
            memberships[node_id] = round((own + margin) / 2, 6)
    return best_groups, memberships


def _split_weakly_connected_groups(
    groups: list[list[int]],
    similarities: dict[tuple[int, int], float],
) -> list[list[int]]:
    cohesive_groups: list[list[int]] = []
    for group in groups:
        remaining = set(group)
        while remaining:
            seed = min(remaining)
            component = {seed}
            frontier = [seed]
            remaining.remove(seed)
            while frontier:
                current = frontier.pop()
                connected = {
                    candidate
                    for candidate in remaining
                    if _similarity(current, candidate, similarities)
                    >= MIN_CLUSTER_COHESION
                }
                component.update(connected)
                frontier.extend(sorted(connected))
                remaining.difference_update(connected)
            cohesive_groups.append(sorted(component))
    return cohesive_groups


def _cluster_selection_score(
    groups: list[list[int]],
    similarities: dict[tuple[int, int], float],
    *,
    node_count: int,
    max_cluster_size: int,
) -> float:
    silhouette = _silhouette(groups, similarities)
    overload = sum(max(0, len(group) - max_cluster_size) for group in groups)
    concentration_penalty = overload / max(1, node_count)
    proportions = [len(group) / node_count for group in groups if group]
    entropy = -sum(value * math.log(value) for value in proportions)
    normalized_entropy = entropy / math.log(len(groups)) if len(groups) > 1 else 0.0
    return silhouette + 0.12 * normalized_entropy - 2.0 * concentration_penalty


def _enforce_cluster_capacity(
    groups: list[list[int]],
    similarities: dict[tuple[int, int], float],
    *,
    max_cluster_size: int,
) -> list[list[int]]:
    pending = list(groups)
    balanced: list[list[int]] = []
    while pending:
        group = pending.pop(0)
        if len(group) <= max_cluster_size:
            balanced.append(group)
            continue
        split_count = math.ceil(len(group) / max_cluster_size)
        splits = _k_medoids(group, similarities, split_count)
        if len(splits) <= 1 or max(map(len, splits)) == len(group):
            splits = [
                group[index : index + max_cluster_size]
                for index in range(0, len(group), max_cluster_size)
            ]
        pending.extend(splits)
    return balanced


def _k_medoids(
    node_ids: list[int], similarities: dict[tuple[int, int], float], cluster_count: int
) -> list[list[int]]:
    medoids = [node_ids[0]]
    while len(medoids) < cluster_count:
        candidate = max(
            (node_id for node_id in node_ids if node_id not in medoids),
            key=lambda node_id: (
                min(
                    1 - _similarity(node_id, medoid, similarities) for medoid in medoids
                ),
                -node_id,
            ),
        )
        medoids.append(candidate)
    for _ in range(12):
        groups = [[] for _ in medoids]
        for node_id in node_ids:
            index = max(
                range(len(medoids)),
                key=lambda item: (
                    _similarity(node_id, medoids[item], similarities),
                    -len(groups[item]),
                    -medoids[item],
                ),
            )
            groups[index].append(node_id)
        updated = [_medoid(group, similarities) for group in groups]
        if updated == medoids:
            break
        medoids = updated
    return [sorted(group) for group in groups if group]


def _medoid(group: list[int], similarities: dict[tuple[int, int], float]) -> int:
    return max(
        group,
        key=lambda node_id: (
            sum(_similarity(node_id, other, similarities) for other in group),
            -node_id,
        ),
    )


def _silhouette(
    groups: list[list[int]], similarities: dict[tuple[int, int], float]
) -> float:
    scores: list[float] = []
    for group in groups:
        for node_id in group:
            own = [
                1 - _similarity(node_id, other, similarities)
                for other in group
                if other != node_id
            ]
            if not own:
                scores.append(0.0)
                continue
            a = sum(own) / len(own)
            other_distances = [
                sum(
                    1 - _similarity(node_id, other, similarities) for other in candidate
                )
                / len(candidate)
                for candidate in groups
                if candidate is not group and candidate
            ]
            b = min(other_distances, default=a)
            scores.append((b - a) / max(a, b) if max(a, b) else 0.0)
    return sum(scores) / len(scores) if scores else 0.0


def _similarity(
    left: int, right: int, similarities: dict[tuple[int, int], float]
) -> float:
    if left == right:
        return 1.0
    return similarities.get(tuple(sorted((left, right))), 0.0)


def _apply_assignment(
    session: Session,
    *,
    node_id: int,
    cluster: SemanticClusterRecord,
    confidence: float,
    terms: list[str],
    now: datetime,
) -> int:
    node = session.get(GraphNodeRecord, node_id)
    if node is None:
        return 0
    assignment = (
        session.execute(
            select(SemanticClusterAssignmentRecord)
            .where(SemanticClusterAssignmentRecord.node_id == node_id)
            .order_by(SemanticClusterAssignmentRecord.id.desc())
        )
        .scalars()
        .first()
    )
    if assignment and assignment.pinned_by_user:
        return 0
    estimate = estimate_confidence(
        [ConfidenceSignal(confidence, "cluster-membership-v2")]
    )
    evidence = json.dumps(
        {"terms": terms, "clusterId": cluster.id},
        ensure_ascii=False,
    )
    reason = f"Semantic profile matches cluster terms: {', '.join(terms[:3])}."
    changed = assignment is None
    if assignment is None:
        assignment = SemanticClusterAssignmentRecord(
            node_id=node_id,
            cluster_id=cluster.id,
            confidence=confidence,
            margin=max(0.0, confidence),
            reason=reason,
            evidence_json=evidence,
            version=ALGORITHM_VERSION,
        )
        session.add(assignment)
    else:
        changed = changed or any(
            (
                assignment.cluster_id != cluster.id,
                not math.isclose(assignment.confidence, confidence),
                not math.isclose(assignment.margin, max(0.0, confidence)),
                assignment.reason != reason,
                assignment.evidence_json != evidence,
                assignment.version != ALGORITHM_VERSION,
                assignment.confidence_lower != estimate.lower,
                assignment.confidence_upper != estimate.upper,
                assignment.confidence_sample_size != estimate.sample_size,
                assignment.confidence_method != estimate.method,
            )
        )
        assignment.cluster_id = cluster.id
        assignment.confidence = confidence
        assignment.margin = max(0.0, confidence)
        assignment.reason = reason
        assignment.evidence_json = evidence
        assignment.version = ALGORITHM_VERSION
        if changed:
            assignment.updated_at = now
    changed = changed or any(
        (
            node.cluster_id != cluster.id,
            node.color_id != cluster.color_id,
            not math.isclose(node.color_confidence or 0.0, confidence),
            node.color_reason != reason,
        )
    )
    node.cluster_id = cluster.id
    assignment.confidence_lower = estimate.lower
    assignment.confidence_upper = estimate.upper
    assignment.confidence_sample_size = estimate.sample_size
    assignment.confidence_method = estimate.method
    node.color_id = cluster.color_id
    node.color_confidence = confidence
    node.color_reason = reason
    if changed:
        node.color_updated_at = now
    return int(changed)


def _ensure_pending_palette(session: Session) -> None:
    existing = session.execute(
        select(GraphPaletteRecord).where(
            GraphPaletteRecord.color_id == PENDING_COLOR_ID
        )
    ).scalar_one_or_none()
    if existing:
        return
    session.add(
        GraphPaletteRecord(
            color_id=PENDING_COLOR_ID,
            oklch="oklch(0.91 0.025 70)",
            light_hex="#F4E6D8",
            dark_hex="#725F4D",
            border="#B89B82",
            text="#3E3024",
            namespace="pending",
            accessibility_json=json.dumps(
                {"nonColorChannel": "dashed-border", "contrast": "AA"}
            ),
        )
    )


def _ensure_semantic_palette(session: Session, stable_key: str, position: int) -> str:
    color_id = f"semantic-{stable_key.removeprefix('semantic-')}"
    existing = session.execute(
        select(GraphPaletteRecord).where(GraphPaletteRecord.color_id == color_id)
    ).scalar_one_or_none()
    if existing:
        return color_id
    seed = int(hashlib.sha256(stable_key.encode("utf-8")).hexdigest()[:8], 16)
    hue = (seed % 360 + position * 137.508) % 360
    light_hex = _oklch_hex(0.68, 0.15, hue)
    dark_hex = _oklch_hex(0.61, 0.14, hue)
    border = _oklch_hex(0.48, 0.12, hue)
    session.add(
        GraphPaletteRecord(
            color_id=color_id,
            oklch=f"oklch(0.68 0.15 {hue:.1f})",
            light_hex=light_hex,
            dark_hex=dark_hex,
            border=border,
            text="#211A15",
            namespace="semantic",
            accessibility_json=json.dumps(
                {"nonColorChannel": "node-shape-and-border", "contrast": "AA"}
            ),
        )
    )
    return color_id


def _ensure_vault_identities(session: Session, now: datetime) -> None:
    vault_ids = {
        value
        for value in session.scalars(select(GraphNodeRecord.vault_id).distinct())
        if value
    }
    vault_ids.add("default")
    identities = {
        item.vault_id: item
        for item in session.execute(select(VaultVisualIdentityRecord)).scalars()
    }
    for vault_id in sorted(vault_ids):
        if vault_id in identities:
            continue
        digest = hashlib.sha256(vault_id.encode("utf-8")).hexdigest()
        hue = (int(digest[:8], 16) % 300) + 30
        color_id = "vault-" + digest[:16]
        if (
            session.execute(
                select(GraphPaletteRecord).where(
                    GraphPaletteRecord.color_id == color_id
                )
            ).scalar_one_or_none()
            is None
        ):
            session.add(
                GraphPaletteRecord(
                    color_id=color_id,
                    oklch=f"oklch(0.60 0.11 {hue})",
                    light_hex=_oklch_hex(0.60, 0.11, hue),
                    dark_hex=_oklch_hex(0.52, 0.10, hue),
                    border=_oklch_hex(0.40, 0.08, hue),
                    text="#FFFFFF",
                    namespace="vault",
                    accessibility_json=json.dumps(
                        {"nonColorChannel": "vault-icon", "contrast": "AA"}
                    ),
                )
            )
        identity = VaultVisualIdentityRecord(
            vault_id=vault_id,
            color_id=color_id,
            icon="vault",
        )
        session.add(identity)
        identities[vault_id] = identity

    for node in session.execute(
        select(GraphNodeRecord).where(GraphNodeRecord.type == "vault")
    ).scalars():
        identity = identities.get(node.vault_id) or identities["default"]
        node.cluster_id = None
        node.color_id = identity.color_id
        node.color_confidence = float(node.vault_id == identity.vault_id)
        node.color_reason = "Reserved visual identity for this vault."
        node.color_updated_at = now


def _weighted_jaccard(left: Counter[str], right: Counter[str]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 0.0
    intersection = sum(min(left[key], right[key]) for key in keys)
    union = sum(max(left[key], right[key]) for key in keys)
    return intersection / union if union else 0.0


def _tokens(value: str) -> Counter[str]:
    return Counter(
        token for token in TOKEN_RE.findall(value.casefold()) if token not in STOP_WORDS
    )


def _flatten_text(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    if isinstance(value, dict):
        return " ".join(_flatten_text(item) for item in value.values())
    return ""


def _json_object(value: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _oklch_hex(lightness: float, chroma: float, hue: float) -> str:
    angle = math.radians(hue)
    lab_a = chroma * math.cos(angle)
    lab_b = chroma * math.sin(angle)
    l_ = lightness + 0.3963377774 * lab_a + 0.2158037573 * lab_b
    m_ = lightness - 0.1055613458 * lab_a - 0.0638541728 * lab_b
    s_ = lightness - 0.0894841775 * lab_a - 1.291485548 * lab_b
    linear_red = 4.0767416621 * l_**3 - 3.3077115913 * m_**3 + 0.2309699292 * s_**3
    linear_green = -1.2684380046 * l_**3 + 2.6097574011 * m_**3 - 0.3413193965 * s_**3
    linear_blue = -0.0041960863 * l_**3 - 0.7034186147 * m_**3 + 1.707614701 * s_**3

    def encode(channel: float) -> int:
        channel = max(0.0, min(1.0, channel))
        srgb = (
            12.92 * channel
            if channel <= 0.0031308
            else 1.055 * channel ** (1 / 2.4) - 0.055
        )
        return round(max(0.0, min(1.0, srgb)) * 255)

    red, green, blue = (encode(linear_red), encode(linear_green), encode(linear_blue))
    return f"#{red:02X}{green:02X}{blue:02X}"
