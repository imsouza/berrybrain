from __future__ import annotations

import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_graph_answer,
    get_ai_config,
)
from berrybrain_api.artifact_state import accepted_edge_clause, accepted_node_clause
from berrybrain_api.learning import build_learning_guidance
from berrybrain_api.models import (
    GraphEdgeRecord,
    GraphNodeRecord,
    NoteRecord,
)

TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9_-]{2,}")
VECTOR_DIMENSIONS = 64


@dataclass
class RetrievalEvidence:
    source: str
    title: str
    text: str
    score: float
    metadata: dict[str, Any]


def cognitive_config(session: Session) -> dict[str, str]:
    from berrybrain_api.cognitive_state import cognitive_config as _cognitive_config

    return _cognitive_config(session)


def semantic_data_state(session: Session) -> dict[str, Any]:
    from berrybrain_api.cognitive_state import (
        semantic_data_state as _semantic_data_state,
    )

    return _semantic_data_state(session)


def _vector_store() -> Any:
    import importlib

    return importlib.import_module("berrybrain_api.vector_store")


def _retrieve_qdrant(
    config: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    return _vector_store()._retrieve_qdrant(config, query, limit)


def _retrieve_chroma(
    config: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    return _vector_store()._retrieve_chroma(config, query, limit)


def chunk_markdown(text: str) -> list[str]:
    return _vector_store().chunk_markdown(text)


def _extracted_attachments(session: Session) -> list[tuple[Any, Any, Any]]:
    return _vector_store()._extracted_attachments(session)


def _tokens(text: str) -> set[str]:
    return _vector_store()._tokens(text)


async def answer_cognitive_query(session: Session, question: str) -> dict[str, Any]:
    facade = sys.modules.get("berrybrain_api.cognitive_layer")
    orchestrate_fn = getattr(facade, "orchestrate_retrieval", orchestrate_retrieval)
    get_config_fn = getattr(facade, "get_ai_config", get_ai_config)
    generate_fn = getattr(facade, "generate_graph_answer", generate_graph_answer)

    orchestrated = orchestrate_fn(session, question)
    evidence = orchestrated["evidence"]
    if not evidence:
        return {
            "status": "insufficient_evidence",
            "question": question,
            "answer": "There is not enough evidence in your BerryBrain data to answer this.",
            "routes": orchestrated["routes"],
            "evidence": [],
            "relatedNodes": [],
            "suggestions": ["Add or process more notes before asking again."],
        }

    config = get_config_fn(session)
    system = (
        "You are BerryBrain Cognitive Layer. Answer only from provided evidence. "
        "Return JSON with status, answer, evidence, relatedNodes, suggestions, "
        "confidence. If evidence is weak, status must be insufficient_evidence."
    )
    prompt_evidence = _bounded_query_evidence(evidence)
    source_note_ids = sorted(
        {
            int(metadata["noteId"])
            for item in prompt_evidence
            if isinstance((metadata := item.get("metadata")), dict)
            and str(metadata.get("noteId", "")).isdigit()
        }
    )
    prompt = json.dumps(
        {
            "question": question,
            "routes": orchestrated["routes"],
            "semanticState": orchestrated["semanticState"],
            "evidence": prompt_evidence,
            "learningGuidance": build_learning_guidance(
                session,
                source_note_ids=source_note_ids,
                target_type="ask_answer",
            ),
            "rules": [
                "Do not invent facts.",
                "Cite concrete note/node/edge/job evidence.",
                "Keep the answer useful for learning and graph navigation.",
            ],
        },
        ensure_ascii=False,
    )
    try:
        result = await generate_fn(
            config,
            prompt,
            system,
            timeout=80,
            max_tokens=1024,
        )
    except TimeoutError:
        return _fallback_answer(
            question,
            orchestrated,
            "The AI provider did not answer within 80 seconds. Try again shortly or choose a faster model.",
            config,
        )
    except GraphAIUnavailable as exc:
        return _fallback_answer(
            question, orchestrated, f"AI unavailable: {exc}", config
        )
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403}:
            reason = (
                "NVIDIA NIM authentication failed. Replace the API key in Settings "
                "and save again."
            )
        elif exc.code == 429:
            reason = "The AI provider rate limit was reached. Try again shortly."
        else:
            reason = f"The AI provider returned HTTP {exc.code}. Check Settings."
        return _fallback_answer(question, orchestrated, reason, config)
    except Exception:
        return _fallback_answer(
            question,
            orchestrated,
            "The AI provider request failed. Check the provider configuration in Settings.",
            config,
        )

    answer_text = str(result.get("answer") or "").strip()
    returned_evidence = result.get("evidence")
    if not isinstance(returned_evidence, list) or not returned_evidence:
        # ponytail: model answered but skipped the strict evidence list -> use retrieved evidence
        if not answer_text:
            return _fallback_answer(
                question, orchestrated, "AI returned no answer.", config
            )
        returned_evidence = orchestrated["evidence"][:8]
    if not answer_text:
        return _fallback_answer(
            question, orchestrated, "AI returned no answer.", config
        )
    return {
        "status": str(result.get("status") or "answered"),
        "question": question,
        "answer": answer_text,
        "routes": orchestrated["routes"],
        "evidence": returned_evidence,
        "relatedNodes": result.get("relatedNodes")
        if isinstance(result.get("relatedNodes"), list)
        else orchestrated["relatedNodes"],
        "suggestions": result.get("suggestions")
        if isinstance(result.get("suggestions"), list)
        else [],
        "confidence": _safe_confidence(result.get("confidence")),
        "provider": config.get("provider", ""),
        "model": config.get("cloud_model") or config.get("ollama_model") or "",
        "retrievers": orchestrated.get("retrievers", []),
        "embedding_type": orchestrated.get("embedding_type", "unknown"),
        "judge_status": "pending",
        "trace_id": f"query_{int(time.time())}",
    }


def _rrf(*lists: list[RetrievalEvidence], k: int = 60) -> list[RetrievalEvidence]:
    scores: dict[str, float] = {}
    items: dict[str, RetrievalEvidence] = {}
    for lst in lists:
        for rank, item in enumerate(lst):
            meta = item.metadata
            key = f"{item.source}:{item.title}:{meta.get('noteId')}:{meta.get('chunk')}:{meta.get('nodeId')}:{meta.get('attachmentId')}"
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in items:
                items[key] = item
    for key, score in scores.items():
        items[key].score = round(score, 6)
    return sorted(items.values(), key=lambda x: x.score, reverse=True)


def orchestrate_retrieval(session: Session, question: str) -> dict[str, Any]:
    cognitive = cognitive_config(session)
    tokens = _tokens(question)
    semantic_needed = bool(
        tokens
        & {"job", "jobs", "error", "errors", "queue", "worker", "stats", "status"}
    )
    mode = cognitive["cognitive_retrieval_mode"]
    graph_needed = mode in {"hybrid", "graph_first"}
    kb_needed = mode in {"hybrid", "kb_first"}
    routes = []

    vector_evidence: list[RetrievalEvidence] = []
    lexical_evidence: list[RetrievalEvidence] = []
    graph_evidence: list[RetrievalEvidence] = []
    related_nodes: list[str] = []

    hipporag_evidence: list[RetrievalEvidence] = []

    if kb_needed:
        routes.append("knowledge_base")
        vector_evidence = retrieve_external_kb(session, question, limit=8)
        lexical_evidence = _retrieve_lexical_kb(session, question, limit=8)

    if graph_needed or (not vector_evidence and not lexical_evidence):
        routes.append("knowledge_graph")
        graph_evidence, related_nodes = retrieve_graph(session, question)

    if cognitive.get("hipporag_enabled") == "true":
        routes.append("hipporag")
        hipporag_evidence = retrieve_hipporag(session, question, limit=5)

    fused_evidence = _rrf(
        vector_evidence, lexical_evidence, graph_evidence, hipporag_evidence
    )
    evidence = [_evidence_dict(item) for item in fused_evidence]
    semantic_state = {}
    if semantic_needed or cognitive["semantic_data_enabled"] == "true":
        routes.append("semantic_data")
        semantic_state = semantic_data_state(session)
        evidence.append(
            {
                "source": "semantic_data",
                "title": "BerryBrain system state",
                "text": json.dumps(semantic_state, ensure_ascii=False),
                "score": 1.0,
                "metadata": {"type": "system_state"},
            }
        )
    config = get_ai_config(session)
    embedding_type = f"{config.get('embedding_provider', 'local')}/{config.get('embedding_model', 'unknown')}"

    return {
        "routes": list(dict.fromkeys(routes)),
        "evidence": evidence[:20],
        "relatedNodes": related_nodes[:12],
        "semanticState": semantic_state,
        "retrievers": ["vector", "lexical", "graph"]
        if graph_needed and kb_needed
        else routes,
        "embedding_type": embedding_type,
    }


def retrieve_hipporag(
    session: Session, query: str, limit: int = 5
) -> list[RetrievalEvidence]:
    """Optional multi-hop retrieval via the HippoRAG sidecar.

    Honors ADR 002: the sidecar is opt-in and offline-tolerant. Callers
    already tolerate an empty list (RRF fusion degrades to no hipporag route),
    so we log and swallow network errors. Set `hipporag_enabled=true` in
    cognitive settings to activate the route.
    """
    from berrybrain_api.config import get_settings

    settings = get_settings()
    url = settings.hipporag_url.rstrip("/")
    try:
        import httpx

        service_token = settings.hipporag_service_token
        r = httpx.post(
            f"{url}/retrieve",
            headers=(
                {"Authorization": f"Bearer {service_token}"} if service_token else {}
            ),
            json={"vault_id": "default", "query": query, "top_k": limit},
            timeout=5,
        )
        r.raise_for_status()
        rows = r.json().get("results", [])
        return [
            RetrievalEvidence(
                source="hipporag",
                title=item.get("title", ""),
                text=item.get("text", ""),
                score=float(item.get("score", 0.0)),
                metadata=item.get("metadata", {}),
            )
            for item in rows
            if item.get("score", 0.0) > 0
        ]
    except Exception:
        # Sidecar offline: omit this route and let RRF continue with available evidence.
        return []


def _retrieve_lexical_kb(
    session: Session, query: str, limit: int = 8
) -> list[RetrievalEvidence]:
    query_tokens = _tokens(query)
    notes = list(session.execute(select(NoteRecord)).scalars())
    results: list[RetrievalEvidence] = []
    for note in notes:
        chunks = chunk_markdown(note.content)
        for index, chunk in enumerate(chunks):
            score = _token_score(query_tokens, _tokens(chunk + " " + note.title))
            if score <= 0:
                continue
            results.append(
                RetrievalEvidence(
                    source="knowledge_base",
                    title=note.title,
                    text=chunk[:900],
                    score=score,
                    metadata={
                        "noteId": note.id,
                        "path": note.path,
                        "chunk": index,
                        "retrieval": "lexical_plus_metadata",
                    },
                )
            )
    attachments = _extracted_attachments(session)
    for attachment, extraction, note in attachments:
        chunks = chunk_markdown(extraction.extracted_text)
        for index, chunk in enumerate(chunks):
            score = _token_score(
                query_tokens,
                _tokens(chunk + " " + attachment.filename + " " + note.title),
            )
            if score <= 0:
                continue
            results.append(
                RetrievalEvidence(
                    source="knowledge_base",
                    title=f"{attachment.filename} ({note.title})",
                    text=chunk[:900],
                    score=score,
                    metadata={
                        "attachmentId": attachment.id,
                        "noteId": note.id,
                        "path": attachment.stored_path,
                        "notePath": note.path,
                        "chunk": index,
                        "kind": "attachment_text",
                        "retrieval": "lexical_plus_metadata",
                    },
                )
            )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def retrieve_kb(
    session: Session, query: str, limit: int = 8
) -> list[RetrievalEvidence]:
    """Retrieve from configured vector store, falling back to local lexical KB."""
    external = retrieve_external_kb(session, query, limit=limit)
    if external:
        return external[:limit]
    return _retrieve_lexical_kb(session, query, limit=limit)


def retrieve_external_kb(
    session: Session, query: str, limit: int = 8
) -> list[RetrievalEvidence]:
    cognitive = cognitive_config(session)
    from berrybrain_api.ai_configuration import embedding_execution_configuration

    cognitive.update(embedding_execution_configuration(session))
    store = cognitive["kb_vector_store"]
    if store == "qdrant" and cognitive["qdrant_url"]:
        try:
            return _retrieve_qdrant(cognitive, query, limit)
        except Exception:
            return []
    if store == "chroma" and cognitive["chroma_url"]:
        try:
            return _retrieve_chroma(cognitive, query, limit)
        except Exception:
            return []
    return []


def retrieve_graph(
    session: Session, query: str, limit: int = 10
) -> tuple[list[RetrievalEvidence], list[str]]:
    query_tokens = _tokens(query)
    nodes = list(
        session.execute(select(GraphNodeRecord).where(accepted_node_clause())).scalars()
    )
    edges = list(
        session.execute(select(GraphEdgeRecord).where(accepted_edge_clause())).scalars()
    )
    node_by_id = {node.id: node for node in nodes}
    results: list[RetrievalEvidence] = []
    related_nodes: list[str] = []
    seed_scores: dict[int, float] = {}
    for node in nodes:
        body = " ".join(
            [
                node.label or "",
                node.summary or "",
                node.ai_summary or "",
                node.ai_context or "",
                node.source_evidence or "",
                node.ontology_class or "",
                node.aliases_json or "",
            ]
        )
        score = _token_score(query_tokens, _tokens(body))
        if score <= 0:
            continue
        confidence_floor = (
            node.confidence_lower if node.confidence_lower is not None else 0.0
        )
        score *= confidence_floor
        seed_scores[node.id] = score
        related_nodes.append(f"{node.type}_{node.id}")
        results.append(
            RetrievalEvidence(
                source="knowledge_graph",
                title=node.label,
                text=(node.ai_context or node.ai_summary or node.summary or node.label)[
                    :900
                ],
                score=score,
                metadata={
                    "nodeId": node.id,
                    "type": node.type,
                    "confidence": (
                        node.confidence if node.confidence_sample_size else None
                    ),
                    "confidenceLower": node.confidence_lower,
                    "status": node.status,
                    "ontologyClass": node.ontology_class,
                    "sourceNoteIds": _json_list(node.source_note_ids),
                    "evidence": _json_list(node.source_evidence),
                    "provider": node.provider,
                    "model": node.model,
                },
            )
        )
    for edge in edges:
        source = node_by_id.get(edge.source_node_id)
        target = node_by_id.get(edge.target_node_id)
        body = " ".join(
            [
                edge.label or "",
                edge.reason or "",
                edge.evidence or "",
                source.label if source else "",
                target.label if target else "",
            ]
        )
        score = _token_score(query_tokens, _tokens(body))
        source_seed = seed_scores.get(edge.source_node_id, 0.0)
        target_seed = seed_scores.get(edge.target_node_id, 0.0)
        confidence_floor = (
            edge.confidence_lower if edge.confidence_lower is not None else 0.0
        )
        propagated = max(source_seed, target_seed) * confidence_floor
        score = max(score * confidence_floor, propagated)
        if score <= 0:
            continue
        if source:
            related_nodes.append(f"{source.type}_{source.id}")
        if target:
            related_nodes.append(f"{target.type}_{target.id}")
        results.append(
            RetrievalEvidence(
                source="knowledge_graph",
                title=edge.label or edge.type,
                text=edge.reason[:900],
                score=score,
                metadata={
                    "edgeId": edge.id,
                    "type": edge.type,
                    "confidence": (
                        edge.confidence if edge.confidence_sample_size else None
                    ),
                    "confidenceLower": edge.confidence_lower,
                    "status": edge.status,
                    "ontologyProperty": edge.ontology_property,
                    "sourceNoteIds": _json_list(edge.source_note_ids),
                    "direction": {
                        "sourceNodeId": edge.source_node_id,
                        "targetNodeId": edge.target_node_id,
                    },
                    "evidence": _json_list(edge.evidence),
                    "provider": edge.provider,
                    "model": edge.model,
                },
            )
        )
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit], list(dict.fromkeys(related_nodes))


def _fallback_answer(
    question: str,
    orchestrated: dict[str, Any],
    reason: str,
    config: dict[str, str] | None = None,
) -> dict[str, Any]:
    evidence = orchestrated["evidence"]
    if "authentication failed" in reason.lower():
        suggestions = [
            "Replace the cloud API key in Settings and click Save.",
            "Retry the question after Settings shows Connected.",
        ]
    else:
        suggestions = [
            "Retry after the provider recovers.",
            "Review the active provider and model in Settings.",
        ]
    provider_config = config or {}
    return {
        "status": "waiting_provider",
        "question": question,
        "answer": "",
        "routes": orchestrated["routes"],
        "evidence": evidence[:8],
        "relatedNodes": orchestrated["relatedNodes"],
        "suggestions": suggestions,
        "reason": reason,
        "provider": provider_config.get("provider", ""),
        "model": provider_config.get("cloud_model")
        or provider_config.get("ollama_model")
        or "",
    }


def _bounded_query_evidence(
    evidence: list[dict[str, Any]],
    *,
    limit: int = 12,
    max_text_chars: int = 1200,
    max_total_chars: int = 9000,
) -> list[dict[str, Any]]:
    bounded: list[dict[str, Any]] = []
    total = 0
    for item in evidence[:limit]:
        text = str(item.get("text") or "").strip()
        remaining = max_total_chars - total
        if remaining <= 0:
            break
        text = text[: min(max_text_chars, remaining)]
        bounded.append({**item, "text": text})
        total += len(text)
    return bounded


def _safe_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, confidence))


def _token_score(query_tokens: set[str], body_tokens: set[str]) -> float:
    if not query_tokens or not body_tokens:
        return 0.0
    overlap = len(query_tokens & body_tokens)
    if overlap == 0:
        return 0.0
    return overlap / math.sqrt(len(query_tokens) * len(body_tokens))


def _evidence_dict(item: RetrievalEvidence) -> dict[str, Any]:
    return {
        "source": item.source,
        "title": item.title,
        "text": item.text,
        "score": round(item.score, 4),
        "metadata": item.metadata,
    }


def _json_list(raw: str) -> list[Any]:
    try:
        parsed = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return [raw] if raw else []
    return parsed if isinstance(parsed, list) else [parsed]
