import hashlib
import json
import logging
import threading
from collections import Counter
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from berrybrain_api.ai_gateway import generate_graph_answer, get_ai_config
from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.ask_flow import (
    append_ask_turn,
    cancel_ask_session,
    close_ask_session,
    create_ask_session,
    create_insight_from_flow_session,
    get_ask_session_payload,
    serialize_ask_session,
    serialize_ask_turn,
)
from berrybrain_api.database import SessionLocal
from berrybrain_api.learning import record_learning_event
from berrybrain_api.models import (
    AskTurnRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    SemanticClusterRecord,
    SettingRecord,
)

router = APIRouter(prefix="/api/v1/ask", tags=["ask"])
logger = logging.getLogger(__name__)
ASK_SUGGESTIONS_CACHE_KEY = "ask_ai_suggestions_v1"
_suggestion_refresh_lock = threading.Lock()
_suggestion_refreshes: set[str] = set()


class CreateAskSessionRequest(BaseModel):
    mode: str = "flow"
    title: str = ""
    inference_id: int | None = None


class CreateAskTurnRequest(BaseModel):
    content: str


class AskTurnFeedbackRequest(BaseModel):
    action: str = Field(pattern="^(upvoted|downvoted|corrected)$")
    correction: str = Field(default="", max_length=8000)


def _suggestion_id(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]


def _question(
    prompt: str,
    *,
    topic: str,
    source: str,
    node_ids: list[int] | None = None,
) -> dict:
    return {
        "id": _suggestion_id(prompt),
        "prompt": prompt,
        "topic": topic,
        "source": source,
        "nodeIds": node_ids or [],
    }


def _graph_fingerprint(
    nodes: list[GraphNodeRecord],
    edges: list[GraphEdgeRecord],
    clusters: list[SemanticClusterRecord],
) -> str:
    payload = {
        "nodes": [(node.id, node.updated_at.isoformat()) for node in nodes],
        "edges": [(edge.id, edge.updated_at.isoformat()) for edge in edges],
        "clusters": [
            (cluster.id, cluster.updated_at.isoformat()) for cluster in clusters
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_suggestion_cache(session, fingerprint: str) -> dict | None:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == ASK_SUGGESTIONS_CACHE_KEY)
    ).scalar_one_or_none()
    if row is None:
        return None
    try:
        payload = json.loads(row.value)
    except (TypeError, ValueError):
        return None
    if payload.get("graphFingerprint") != fingerprint:
        return None
    if not isinstance(payload.get("questions"), list):
        return None
    return payload


def _write_suggestion_cache(session, fingerprint: str, payload: dict) -> None:
    row = session.execute(
        select(SettingRecord).where(SettingRecord.key == ASK_SUGGESTIONS_CACHE_KEY)
    ).scalar_one_or_none()
    value = json.dumps(
        {
            "graphFingerprint": fingerprint,
            "questions": payload["questions"],
            "topics": payload["topics"],
            "generatedAt": datetime.now(UTC).isoformat(),
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if row is None:
        session.add(SettingRecord(key=ASK_SUGGESTIONS_CACHE_KEY, value=value))
    else:
        row.value = value
        row.updated_at = datetime.now(UTC)
    session.commit()


def _validate_ai_suggestions(
    raw: dict[str, Any],
    nodes: list[GraphNodeRecord],
    clusters: list[SemanticClusterRecord],
    limit: int,
) -> dict:
    node_by_id = {node.id: node for node in nodes}
    allowed_topics = {
        item.label.strip().casefold(): item.label.strip()
        for item in [*nodes, *clusters]
        if item.label.strip()
    }
    questions: list[dict] = []
    seen_prompts: set[str] = set()
    for item in raw.get("questions", []):
        if not isinstance(item, dict):
            continue
        prompt = " ".join(str(item.get("prompt") or "").split()).strip()
        if len(prompt) < 12 or len(prompt) > 240 or "?" not in prompt:
            continue
        node_ids: list[int] = []
        for raw_id in item.get("node_ids", []):
            try:
                node_id = int(raw_id)
            except (TypeError, ValueError):
                continue
            if node_id in node_by_id and node_id not in node_ids:
                node_ids.append(node_id)
        if not node_ids:
            continue
        normalized = prompt.casefold()
        if normalized in seen_prompts:
            continue
        seen_prompts.add(normalized)
        requested_topic = str(item.get("topic") or "").strip()
        topic = allowed_topics.get(requested_topic.casefold())
        if topic is None:
            topic = node_by_id[node_ids[0]].label.strip()
        intent = str(item.get("intent") or "graph_content").strip().casefold()
        if intent not in {
            "graph_content",
            "graph_structure",
            "ontology",
            "gap",
            "insight",
        }:
            intent = "graph_content"
        questions.append(
            _question(
                prompt,
                topic=topic,
                source=f"ai_{intent}",
                node_ids=node_ids[:12],
            )
        )
        if len(questions) >= limit:
            break
    topics: list[str] = []
    for value in raw.get("topics", []):
        topic = allowed_topics.get(str(value or "").strip().casefold())
        if topic and topic not in topics:
            topics.append(topic)
    for item in questions:
        if item["topic"] not in topics:
            topics.append(item["topic"])
    return {"questions": questions, "topics": topics[:16]}


def _graph_context_suggestions(
    nodes: list[GraphNodeRecord],
    edges: list[GraphEdgeRecord],
    clusters: list[SemanticClusterRecord],
    degree: Counter[int],
    limit: int,
) -> dict:
    """Build grounded recovery prompts from live graph semantics only."""

    def display_label(value: str) -> str:
        compact = " ".join(value.split()).strip()
        return compact if len(compact) <= 80 else f"{compact[:77].rstrip()}..."

    node_by_id = {node.id: node for node in nodes}
    ranked_nodes = sorted(
        nodes,
        key=lambda node: (
            node.type not in {"insight", "gap"},
            -degree[node.id],
            -node.id,
        ),
    )
    questions: list[dict] = []
    seen: set[str] = set()

    def add(prompt: str, topic: str, node_ids: list[int]) -> bool:
        normalized = prompt.casefold()
        if not node_ids or normalized in seen or len(questions) >= limit:
            return False
        seen.add(normalized)
        questions.append(
            _question(
                prompt,
                topic=topic,
                source="graph_context",
                node_ids=node_ids[:12],
            )
        )
        return True

    edge_budget = max(2, min(5, limit // 3))
    edge_topics: Counter[str] = Counter()
    for edge in sorted(
        edges, key=lambda item: (-degree[item.source_node_id], -item.id)
    ):
        if sum(edge_topics.values()) >= edge_budget:
            break
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        if source is None or target is None:
            continue
        topic_node = target if target.type != "note" else source
        topic_key = topic_node.label.strip().casefold()
        if not topic_key or edge_topics[topic_key] >= 1:
            continue
        source_label = display_label(source.label)
        target_label = display_label(target.label)
        relationship = " ".join(edge.type.replace("_", " ").split()).strip()
        if add(
            f'What evidence explains the "{relationship}" relationship between '
            f'"{source_label}" and "{target_label}"?',
            topic_node.label,
            [source.id, target.id],
        ):
            edge_topics[topic_key] += 1

    for cluster in clusters:
        cluster_nodes = [
            node.id for node in ranked_nodes if node.cluster_id == cluster.id
        ]
        if not cluster_nodes:
            continue
        add(
            f'How do the nodes in the "{display_label(cluster.label)}" context relate to one another?',
            cluster.label,
            cluster_nodes,
        )

    type_prompts = {
        "attachment": 'What knowledge was extracted from the attachment "{label}"?',
        "concept": 'Which notes and entities provide context for the concept "{label}"?',
        "context": 'Which nodes are framed by the context "{label}"?',
        "entity": 'Where does the entity "{label}" appear, and what role does it play?',
        "gap": 'Which existing evidence could resolve the gap "{label}"?',
        "insight": 'What evidence supports or challenges the insight "{label}"?',
        "note": 'Which concepts, entities, and topics are grounded in "{label}"?',
        "source": 'Which claims in the graph depend on the source "{label}"?',
        "study_path": 'Which concepts form the study path "{label}", and in what order?',
        "topic": 'Which nodes contribute most to the topic "{label}"?',
    }
    for node in ranked_nodes:
        label = display_label(node.label)
        add(
            type_prompts.get(
                node.type,
                'What evidence and relationships define "{label}"?',
            ).format(label=label),
            node.label,
            [node.id],
        )

    for node in ranked_nodes:
        label = display_label(node.label)
        add(
            f'How does "{label}" connect to other knowledge in this graph?',
            node.label,
            [node.id],
        )

    for node in ranked_nodes:
        label = display_label(node.label)
        node_type = " ".join(node.type.replace("_", " ").split())
        add(
            f'What recorded evidence supports the graph item "{label}"?',
            node.label,
            [node.id],
        )
        add(
            f'Why is "{label}" classified as {node_type}, and does its current context support that classification?',
            node.label,
            [node.id],
        )
        add(
            f'What remains uncertain or incomplete about "{label}" in the current graph?',
            node.label,
            [node.id],
        )

    topics: list[str] = []
    for item in questions:
        if item["topic"] not in topics:
            topics.append(item["topic"])
    return {"questions": questions, "topics": topics[:16]}


def _claim_suggestion_refresh(fingerprint: str) -> bool:
    with _suggestion_refresh_lock:
        if fingerprint in _suggestion_refreshes:
            return False
        _suggestion_refreshes.add(fingerprint)
        return True


async def _refresh_ai_suggestions(
    fingerprint: str,
    context: dict,
    system: str,
    recovered: dict,
    limit: int,
) -> None:
    try:
        with SessionLocal() as session:
            generated = await generate_graph_answer(
                get_ai_config(session),
                json.dumps(context, ensure_ascii=False, separators=(",", ":")),
                system,
                timeout=45,
                max_tokens=1800,
                session=session,
                prompt_version="ask-suggestions.v1",
                correlation_id=f"ask-suggestions:{fingerprint[:16]}",
            )
            nodes = list(
                session.execute(
                    select(GraphNodeRecord)
                    .where(
                        accepted_node_clause(),
                    )
                    .order_by(
                        GraphNodeRecord.updated_at.desc(), GraphNodeRecord.id.desc()
                    )
                    .limit(200)
                ).scalars()
            )
            node_ids = [node.id for node in nodes]
            edges = list(
                session.execute(
                    select(GraphEdgeRecord).where(
                        accepted_edge_clause(),
                        GraphEdgeRecord.source_node_id.in_(node_ids),
                        GraphEdgeRecord.target_node_id.in_(node_ids),
                    )
                ).scalars()
            )
            clusters = list(
                session.execute(
                    select(SemanticClusterRecord)
                    .where(SemanticClusterRecord.status == "active")
                    .order_by(SemanticClusterRecord.updated_at.desc())
                    .limit(12)
                ).scalars()
            )
            if _graph_fingerprint(nodes, edges, clusters) != fingerprint:
                return
            validated = _validate_ai_suggestions(generated, nodes, clusters, limit)
            if not validated["questions"]:
                return
            questions = list(validated["questions"])
            seen = {item["prompt"].casefold() for item in questions}
            for item in recovered["questions"]:
                if len(questions) >= limit:
                    break
                if item["prompt"].casefold() not in seen:
                    questions.append(item)
                    seen.add(item["prompt"].casefold())
            topics = list(validated["topics"])
            for item in questions:
                if item["topic"] not in topics:
                    topics.append(item["topic"])
            _write_suggestion_cache(
                session,
                fingerprint,
                {"questions": questions, "topics": topics[:16]},
            )
    except Exception:
        logger.exception("Background Ask suggestion generation failed")
    finally:
        with _suggestion_refresh_lock:
            _suggestion_refreshes.discard(fingerprint)


@router.get("/suggestions")
async def get_suggestions(background_tasks: BackgroundTasks, limit: int = 8) -> dict:
    """Generate questions with AI, then constrain them to live graph evidence."""
    bounded_limit = max(1, min(limit, 18))
    with SessionLocal() as session:
        nodes = list(
            session.execute(
                select(GraphNodeRecord)
                .where(
                    accepted_node_clause(),
                )
                .order_by(GraphNodeRecord.updated_at.desc(), GraphNodeRecord.id.desc())
                .limit(200)
            ).scalars()
        )
        if not nodes:
            return {"questions": [], "topics": [], "graph": {"nodes": 0, "edges": 0}}

        node_by_id = {node.id: node for node in nodes}
        node_ids = list(node_by_id)
        edge_rows = list(
            session.execute(
                select(GraphEdgeRecord).where(
                    accepted_edge_clause(),
                    GraphEdgeRecord.source_node_id.in_(node_ids),
                    GraphEdgeRecord.target_node_id.in_(node_ids),
                )
            ).scalars()
        )
        degree: Counter[int] = Counter()
        for edge in edge_rows:
            degree[edge.source_node_id] += 1
            degree[edge.target_node_id] += 1

        clusters = list(
            session.execute(
                select(SemanticClusterRecord)
                .where(SemanticClusterRecord.status == "active")
                .order_by(SemanticClusterRecord.updated_at.desc())
                .limit(12)
            ).scalars()
        )
        graph = {
            "nodes": len(nodes),
            "edges": len(edge_rows),
            "suggestedInsights": sum(
                1
                for node in nodes
                if node.type == "insight" and node.status == "suggested"
            ),
            "gaps": sum(
                1 for node in nodes if node.type == "gap" and node.status != "ignored"
            ),
        }
        fingerprint = _graph_fingerprint(nodes, edge_rows, clusters)
        cached = _read_suggestion_cache(session, fingerprint)
        if cached is not None:
            return {
                "questions": cached["questions"][:bounded_limit],
                "topics": cached.get("topics", []),
                "graph": graph,
                "generation": "cached_ai",
            }

        ranked_nodes = sorted(
            nodes,
            key=lambda node: (
                node.type not in {"insight", "gap"},
                -degree[node.id],
                -node.id,
            ),
        )[:80]
        ranked_ids = {node.id for node in ranked_nodes}
        context = {
            "graph": graph,
            "requested_question_count": bounded_limit,
            "nodes": [
                {
                    "id": node.id,
                    "type": node.type,
                    "label": node.label,
                    "status": node.status,
                    "summary": (node.ai_summary or node.summary or "")[:500],
                    "cluster_id": node.cluster_id,
                }
                for node in ranked_nodes
            ],
            "relationships": [
                {
                    "source_id": edge.source_node_id,
                    "target_id": edge.target_node_id,
                    "type": edge.type,
                    "reason": edge.reason[:300],
                }
                for edge in edge_rows
                if edge.source_node_id in ranked_ids
                and edge.target_node_id in ranked_ids
            ][:120],
            "clusters": [
                {"id": cluster.id, "label": cluster.label} for cluster in clusters
            ],
            "output_contract": {
                "questions": [
                    {
                        "prompt": "English question grounded in supplied graph data",
                        "topic": "exact supplied node or cluster label",
                        "node_ids": ["one or more supplied node IDs"],
                        "intent": "graph_content | graph_structure | ontology | gap | insight",
                    }
                ],
                "topics": ["exact supplied node or cluster labels"],
            },
        }
        system = (
            "Return valid JSON only. Generate useful next questions for the owner of this "
            "knowledge graph. Every question must be answerable from the supplied graph, cite "
            "one or more supplied node IDs, and be written in English. Cover both graph "
            "structure and graph content when evidence supports them. Do not invent labels, "
            "IDs, facts, or generic suggestions. Preserve user-authored labels verbatim."
        )
        recovered = _graph_context_suggestions(
            nodes, edge_rows, clusters, degree, bounded_limit
        )
        if _claim_suggestion_refresh(fingerprint):
            background_tasks.add_task(
                _refresh_ai_suggestions,
                fingerprint,
                context,
                system,
                recovered,
                bounded_limit,
            )
        return {
            "questions": recovered["questions"],
            "topics": recovered["topics"],
            "graph": graph,
            "generation": "graph_context",
        }


@router.post("/sessions", status_code=201)
def create_session(payload: CreateAskSessionRequest) -> dict:
    with SessionLocal() as session:
        item = create_ask_session(
            session,
            mode=payload.mode,
            title=payload.title,
            inference_id=payload.inference_id,
        )
        return get_ask_session_payload(session, item.id)


@router.get("/sessions/{session_id}")
def get_session(session_id: str) -> dict:
    with SessionLocal() as session:
        return get_ask_session_payload(session, session_id)


@router.post("/sessions/{session_id}/turns")
async def create_turn(session_id: str, payload: CreateAskTurnRequest) -> dict:
    with SessionLocal() as session:
        try:
            user_turn, assistant_turn = await append_ask_turn(
                session, session_id, payload.content
            )
        except Exception as exc:
            if isinstance(exc, HTTPException):
                raise
            logger.exception("Flow turn failed", extra={"session_id": session_id})
            raise HTTPException(
                status_code=502,
                detail="Flow could not complete with the configured AI provider.",
            ) from exc
        return {
            "userTurn": serialize_ask_turn(user_turn),
            "assistantTurn": serialize_ask_turn(assistant_turn),
        }


@router.post("/sessions/{session_id}/turns/{turn_id}/feedback")
def record_turn_feedback(
    session_id: str, turn_id: int, payload: AskTurnFeedbackRequest
) -> dict[str, Any]:
    with SessionLocal() as session:
        turn = session.get(AskTurnRecord, turn_id)
        if turn is None or turn.session_id != session_id:
            raise HTTPException(status_code=404, detail="Ask turn not found")
        if turn.role != "assistant":
            raise HTTPException(
                status_code=422,
                detail="Feedback can only be recorded for an assistant answer",
            )
        if payload.action == "corrected" and not payload.correction.strip():
            raise HTTPException(
                status_code=422,
                detail="A corrected answer is required for correction feedback",
            )
        event = record_learning_event(
            session,
            event_type=f"ask.answer.{payload.action}",
            target_type="ask_answer",
            target_key=f"ask:{session_id}:turn:{turn.id}",
            action=payload.action,
            before_state={"answer": turn.content},
            after_state={"correction": payload.correction.strip()},
            actor_type="user",
            origin="ask_api",
        )
        session.commit()
        return {
            "status": "recorded",
            "eventId": event.event_id,
            "action": event.action,
        }


@router.post("/sessions/{session_id}/cancel")
def cancel_session(session_id: str) -> dict:
    with SessionLocal() as session:
        item = cancel_ask_session(session, session_id)
        return {"session": serialize_ask_session(item)}


@router.post("/sessions/{session_id}/close")
def close_session(session_id: str) -> dict:
    with SessionLocal() as session:
        item = close_ask_session(session, session_id)
        return {"session": serialize_ask_session(item)}


@router.post("/sessions/{session_id}/insight")
def create_session_insight(session_id: str) -> dict:
    with SessionLocal() as session:
        return create_insight_from_flow_session(session, session_id)
