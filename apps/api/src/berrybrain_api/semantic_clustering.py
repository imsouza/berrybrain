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

from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    GraphPaletteRecord,
    SemanticClusterAssignmentRecord,
    SemanticClusterRecord,
    SemanticProfileRecord,
    VaultVisualIdentityRecord,
)

ALGORITHM_VERSION = 1
MIN_ASSIGNMENT_CONFIDENCE = 0.35
MERGE_SIMILARITY = 0.28
HYSTERESIS_MARGIN = 0.12
PENDING_COLOR_ID = "pending"
TOKEN_RE = re.compile(r"[^\W_]{3,}", re.UNICODE)
STOP_WORDS = {
    "about",
    "after",
    "also",
    "como",
    "com",
    "das",
    "dos",
    "for",
    "from",
    "mais",
    "para",
    "por",
    "que",
    "the",
    "this",
    "uma",
    "with",
}


class _UnionFind:
    def __init__(self, node_ids: list[int]) -> None:
        self.parent = {node_id: node_id for node_id in node_ids}

    def find(self, node_id: int) -> int:
        parent = self.parent[node_id]
        if parent != node_id:
            self.parent[node_id] = self.find(parent)
        return self.parent[node_id]

    def union(self, left: int, right: int) -> None:
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root != right_root:
            self.parent[max(left_root, right_root)] = min(left_root, right_root)


def build_cluster_preview(session: Session) -> dict[str, Any]:
    nodes = list(
        session.execute(
            select(GraphNodeRecord)
            .where(
                GraphNodeRecord.status != "ignored",
                GraphNodeRecord.type != "vault",
            )
            .order_by(GraphNodeRecord.id)
        ).scalars()
    )
    edges = list(session.execute(select(GraphEdgeRecord)).scalars())
    latest_profiles: dict[int, SemanticProfileRecord] = {}
    for profile in session.execute(
        select(SemanticProfileRecord).order_by(SemanticProfileRecord.id)
    ).scalars():
        if profile.status == "completed":
            latest_profiles[profile.node_id] = profile

    neighbors: dict[int, set[int]] = defaultdict(set)
    edge_confidence: dict[tuple[int, int], float] = {}
    for edge in edges:
        neighbors[edge.source_node_id].add(edge.target_node_id)
        neighbors[edge.target_node_id].add(edge.source_node_id)
        key = tuple(sorted((edge.source_node_id, edge.target_node_id)))
        edge_confidence[key] = max(edge_confidence.get(key, 0.0), edge.confidence)

    node_by_id = {node.id: node for node in nodes}
    vectors: dict[int, Counter[str]] = {}
    unresolved: list[int] = []
    for node in nodes:
        profile = latest_profiles.get(node.id)
        if profile is None or node.semantic_state != "completed":
            unresolved.append(node.id)
            continue
        context_labels = " ".join(
            node_by_id[item].label
            for item in sorted(neighbors[node.id])
            if item in node_by_id
        )
        vectors[node.id] = _semantic_vector(node, profile, context_labels)

    eligible_ids = sorted(vectors)
    groups = _UnionFind(eligible_ids)
    candidate_pairs = set(edge_confidence)
    buckets: dict[str, list[int]] = defaultdict(list)
    for node_id, vector in vectors.items():
        for token, _ in vector.most_common(4):
            buckets[token].append(node_id)
    for bucket in buckets.values():
        for index, left in enumerate(bucket):
            for right in bucket[index + 1 :]:
                candidate_pairs.add(tuple(sorted((left, right))))

    for left, right in sorted(candidate_pairs):
        if left not in vectors or right not in vectors:
            continue
        similarity = _weighted_jaccard(vectors[left], vectors[right])
        relationship = edge_confidence.get((left, right), 0.0)
        if similarity >= MERGE_SIMILARITY or (
            relationship >= 0.8 and similarity >= 0.12
        ):
            groups.union(left, right)

    components: dict[int, list[int]] = defaultdict(list)
    for node_id in eligible_ids:
        components[groups.find(node_id)].append(node_id)

    clusters: list[dict[str, Any]] = []
    for member_ids in sorted(components.values(), key=lambda item: min(item)):
        centroid = Counter[str]()
        for node_id in member_ids:
            centroid.update(vectors[node_id])
        terms = [token for token, _ in centroid.most_common(5)]
        label = " · ".join(terms[:3]) or "Unresolved"
        stable_key = (
            "semantic-"
            + hashlib.sha256("|".join(terms).encode("utf-8")).hexdigest()[:20]
        )
        member_confidence = {
            node_id: round(_weighted_jaccard(vectors[node_id], centroid), 4)
            for node_id in member_ids
        }
        clusters.append(
            {
                "stableKey": stable_key,
                "label": label,
                "description": f"Semantic context shared by {len(member_ids)} graph nodes.",
                "terms": terms,
                "memberIds": member_ids,
                "memberConfidence": member_confidence,
            }
        )
    return {
        "algorithmVersion": ALGORITHM_VERSION,
        "nodeCount": len(nodes),
        "clusterCount": len(clusters),
        "unresolvedNodeIds": unresolved,
        "clusters": clusters,
    }


def apply_cluster_preview(session: Session, preview: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(UTC)
    _ensure_pending_palette(session)
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
            cluster.label = item["label"]
            cluster.description = item["description"]
            cluster.centroid_ref = json.dumps(item["terms"], ensure_ascii=False)
            cluster.color_id = color_id
            cluster.version += 1
            cluster.status = "active"
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

    for cluster in session.execute(select(SemanticClusterRecord)).scalars():
        if cluster.id not in active_ids:
            cluster.status = "inactive"
            cluster.updated_at = now
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
                SemanticClusterAssignmentRecord.cluster_id,
                func.count(SemanticClusterAssignmentRecord.id),
            ).group_by(SemanticClusterAssignmentRecord.cluster_id)
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
    profile: SemanticProfileRecord,
    context_labels: str,
) -> Counter[str]:
    profile_data = _json_object(profile.profile_json)
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
    return vector


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
    if (
        assignment
        and assignment.cluster_id != cluster.id
        and confidence < assignment.confidence + HYSTERESIS_MARGIN
    ):
        return 0
    previous_cluster_id = assignment.cluster_id if assignment else None
    evidence = json.dumps(
        {"terms": terms, "previousClusterId": previous_cluster_id},
        ensure_ascii=False,
    )
    reason = f"Semantic profile matches cluster terms: {', '.join(terms[:3])}."
    if assignment is None:
        assignment = SemanticClusterAssignmentRecord(
            node_id=node_id,
            cluster_id=cluster.id,
            confidence=confidence,
            margin=max(0.0, confidence - MIN_ASSIGNMENT_CONFIDENCE),
            reason=reason,
            evidence_json=evidence,
            version=ALGORITHM_VERSION,
        )
        session.add(assignment)
    else:
        assignment.cluster_id = cluster.id
        assignment.confidence = confidence
        assignment.margin = max(0.0, confidence - MIN_ASSIGNMENT_CONFIDENCE)
        assignment.reason = reason
        assignment.evidence_json = evidence
        assignment.version += 1
        assignment.updated_at = now
    node.cluster_id = cluster.id
    node.color_id = (
        cluster.color_id
        if confidence >= MIN_ASSIGNMENT_CONFIDENCE
        else PENDING_COLOR_ID
    )
    node.color_confidence = confidence
    node.color_reason = reason
    node.color_updated_at = now
    return 1


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
        node.color_confidence = 1.0
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
