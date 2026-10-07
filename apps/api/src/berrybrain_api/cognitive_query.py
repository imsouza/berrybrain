from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import time
import unicodedata
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
from berrybrain_api.evidence_selection import query_aware_excerpt
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


def _search_tokens(text: str) -> set[str]:
    normalized = "".join(
        ch
        for ch in unicodedata.normalize("NFKD", text)
        if not unicodedata.combining(ch)
    )
    return _tokens(normalized)


def _query_tokens(question: str) -> set[str]:
    # Output instructions are not the subject being retrieved. Keep this separate
    # from embedding tokenization; no existing vector index changes are needed.
    boilerplate = {
        "crie",
        "criar",
        "faca",
        "montar",
        "elabore",
        "explique",
        "explique-me",
        "sobre",
        "para",
        "com",
        "uma",
        "um",
        "que",
        "quais",
        "como",
        "por",
        "das",
        "dos",
        "nas",
        "nos",
        "meu",
        "meus",
        "minha",
        "minhas",
        "suas",
        "seus",
        "notas",
        "segundo",
        "contexto",
        "responda",
        "portugues",
        "guia",
        "estudo",
        "plano",
        "roteiro",
        "create",
        "make",
        "write",
        "explain",
        "about",
        "from",
        "with",
        "the",
        "and",
        "for",
        "what",
        "which",
        "how",
        "my",
        "notes",
        "please",
        "study",
        "guide",
        "plan",
        "according",
        "based",
        "context",
        "answer",
    }
    tokens = _search_tokens(question)
    return tokens - boilerplate or tokens


def _retrieval_question(question: str, conversation_context: str) -> str:
    tokens = _search_tokens(question)
    if len(tokens) > 8 or not tokens & {
        "isso",
        "isto",
        "esse",
        "essa",
        "esses",
        "essas",
        "continue",
        "continuar",
        "melhor",
        "mais",
        "it",
        "this",
        "that",
        "those",
        "more",
        "expand",
    }:
        return question
    previous_questions = re.findall(r"^user: (.+)$", conversation_context, re.MULTILINE)
    for previous in reversed(previous_questions):
        if previous.strip() != question.strip():
            return f"{previous}\n{question}"
    return question


async def answer_cognitive_query(
    session: Session, question: str, *, conversation_context: str = ""
) -> dict[str, Any]:
    facade = sys.modules.get("berrybrain_api.cognitive_layer")
    orchestrate_fn = getattr(facade, "orchestrate_retrieval", orchestrate_retrieval)
    get_config_fn = getattr(facade, "get_ai_config", get_ai_config)
    generate_fn = getattr(facade, "generate_graph_answer", generate_graph_answer)

    retrieval_question = _retrieval_question(question, conversation_context)
    orchestrated = orchestrate_fn(session, retrieval_question)
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
        "You are BerryBrain's assistant. Respond in the user's language and fulfill "
        "the user's actual request using the supplied note content and verified graph evidence. "
        "You may synthesize explanations, study guides, outlines and learning activities "
        "from that content; a ready-made answer need not exist in a note. "
        "Label proposed activities and inferred connections as suggestions, not source facts. "
        "Do not invent factual claims absent from the evidence. If only part of the request "
        "is supported, answer that part and state the limits. Inspect graph labels, types "
        "and relationships when the user asks about the graph, not for every request. "
        "Return JSON with status, answer, evidence, relatedNodes, suggestions, "
        "confidence. Use status answered when you can provide a grounded response; "
        "use insufficient_evidence only when the supplied content cannot support the request. "
        "Return evidence IDs before the answer field and keep the JSON complete."
    )
    # Optional indexes can lag behind the canonical vault. One stale result must
    # not veto current evidence from the other retrievers. Filter before bounding
    # so an invalid result cannot consume the prompt's evidence budget.
    current_evidence = [
        item
        for item in evidence
        if _evidence_source_snapshot(session, [item]) is not None
    ]
    if not current_evidence:
        return _unsupported_answer(
            question, orchestrated, "No retrieved source could be verified as current."
        )
    orchestrated = {**orchestrated, "evidence": current_evidence}
    prompt_evidence = _bounded_query_evidence(
        current_evidence, question=retrieval_question
    )
    source_snapshot = _evidence_source_snapshot(session, prompt_evidence)
    if source_snapshot is None:
        return _unsupported_answer(
            question, orchestrated, "A retrieved source is no longer current."
        )
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
            "conversationContext": conversation_context,
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
                "Cite only the supplied evidenceId values.",
                "Return evidence as a list of objects containing evidenceId. Do not invent IDs or quotes.",
                "For study guides, provide a practical ordered guide with topics and proposed exercises grounded in the notes, not just instructions to consult a map.",
                "Use complementary evidence when the question requires multiple hops.",
                "Keep the answer useful for learning and graph navigation.",
            ],
        },
        ensure_ascii=False,
    )
    max_tokens = (
        3072
        if _search_tokens(question)
        & {
            "guia",
            "plano",
            "roteiro",
            "guide",
            "plan",
            "tutorial",
            "detalhado",
            "detalhada",
            "detailed",
        }
        else 1024
    )
    started = time.monotonic()
    try:
        for attempt in range(2):
            remaining = 80 - int(time.monotonic() - started)
            if remaining <= 0:
                raise TimeoutError
            result = await generate_fn(
                config,
                prompt,
                system,
                timeout=remaining,
                max_tokens=max_tokens,
            )
            if _validated_citations(result.get("evidence"), prompt_evidence):
                break
            if attempt == 0:
                # One bounded regeneration can repair the model's citation
                # formatting. Never attach sources to an unverified draft.
                retry_prompt = json.loads(prompt)
                retry_prompt["citationValidationFeedback"] = {
                    "error": "Your response did not contain valid citations. Regenerate a complete grounded answer.",
                    "allowedEvidenceIds": [
                        item["evidenceId"] for item in prompt_evidence
                    ],
                    "format": "evidence must be a list of objects with evidenceId; omit quotes and other source fields.",
                }
                prompt = json.dumps(retry_prompt, ensure_ascii=False)
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
    returned_evidence = _validated_citations(result.get("evidence"), prompt_evidence)
    if not returned_evidence:
        return _unsupported_answer(
            question, orchestrated, "The model did not return verifiable citations."
        )
    if _evidence_source_snapshot(session, prompt_evidence) != source_snapshot:
        return _unsupported_answer(
            question,
            orchestrated,
            "Source evidence changed while the answer was being generated.",
        )
    if not answer_text:
        return _fallback_answer(
            question, orchestrated, "AI returned no answer.", config
        )
    return {
        "status": "insufficient_evidence"
        if result.get("status") == "insufficient_evidence"
        else "answered",
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


def _canonical_evidence_key(item: RetrievalEvidence) -> str:
    metadata = item.metadata
    document_id = str(metadata.get("documentId") or "").strip()
    if document_id:
        return f"document:{document_id}"
    chunk = str(metadata.get("chunk") if metadata.get("chunk") is not None else "")
    attachment_id = str(metadata.get("attachmentId") or "").strip()
    if attachment_id:
        return f"attachment:{attachment_id}:chunk:{chunk}"
    note_id = str(metadata.get("noteId") or "").strip()
    if note_id:
        return f"note:{note_id}:chunk:{chunk}"
    edge_id = str(metadata.get("edgeId") or "").strip()
    if edge_id:
        return f"edge:{edge_id}"
    node_id = str(metadata.get("nodeId") or "").strip()
    if node_id:
        return f"node:{node_id}"
    path = str(metadata.get("path") or metadata.get("notePath") or "").strip()
    if path:
        return f"path:{path}:chunk:{chunk}"
    normalized = " ".join(sorted(_tokens(f"{item.title} {item.text}")))
    return f"content:{hashlib.sha256(normalized.encode()).hexdigest()}"


def _retrieval_route(item: RetrievalEvidence) -> str:
    return str(item.metadata.get("retrieval") or item.source).strip() or "unknown"


def _rrf(*lists: list[RetrievalEvidence], k: int = 60) -> list[RetrievalEvidence]:
    if k < 1:
        raise ValueError("RRF k must be positive")
    scores: dict[str, float] = {}
    items: dict[str, RetrievalEvidence] = {}
    best_original_scores: dict[str, float] = {}
    seen_routes: set[tuple[str, str]] = set()
    for lst in lists:
        for rank, item in enumerate(lst):
            key = _canonical_evidence_key(item)
            route = _retrieval_route(item)
            if (key, route) in seen_routes:
                continue
            seen_routes.add((key, route))
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            if key not in items:
                metadata = dict(item.metadata)
                metadata["retrievalRoutes"] = [route]
                metadata["retrievalScores"] = {route: round(float(item.score), 6)}
                metadata["evidenceKey"] = key
                items[key] = RetrievalEvidence(
                    source=item.source,
                    title=item.title,
                    text=item.text,
                    score=item.score,
                    metadata=metadata,
                )
                best_original_scores[key] = float(item.score)
                continue
            merged = items[key]
            routes = list(merged.metadata.get("retrievalRoutes") or [])
            if route not in routes:
                routes.append(route)
            merged.metadata["retrievalRoutes"] = routes
            route_scores = dict(merged.metadata.get("retrievalScores") or {})
            route_scores[route] = round(float(item.score), 6)
            merged.metadata["retrievalScores"] = route_scores
            if float(item.score) > best_original_scores[key]:
                merged.source = item.source
                merged.title = item.title
                merged.text = item.text
                best_original_scores[key] = float(item.score)
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
    from berrybrain_api.vault import parse_markdown_note

    query_tokens = _query_tokens(query)
    notes = list(session.execute(select(NoteRecord)).scalars())
    results: list[RetrievalEvidence] = []
    for note in notes:
        folder_tokens = (
            _search_tokens(note.path.rsplit("/", 1)[0]) if "/" in note.path else set()
        )
        folder_match = bool(query_tokens & folder_tokens)
        # Topic-wide requests need each note's explanation, not just its YAML
        # header or a generic map paragraph. All text still comes from the note.
        chunks = (
            [query_aware_excerpt(parse_markdown_note(note.content).body, query, 1200)]
            if folder_match
            else chunk_markdown(note.content)
        )
        for index, chunk in enumerate(chunks):
            score = _token_score(query_tokens, _search_tokens(chunk + " " + note.title))
            # A folder is a user-controlled topic signal (e.g. Computacao),
            # including when the question uses accents (computação).
            if folder_match:
                score += 0.5 * len(query_tokens & folder_tokens) / len(query_tokens)
            if score <= 0:
                continue
            results.append(
                RetrievalEvidence(
                    source="knowledge_base",
                    title=note.title,
                    text=chunk[:1200],
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
                _search_tokens(chunk + " " + attachment.filename + " " + note.title),
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
    # Broad-topic requests need several notes, not every chunk of one map.
    grouped: dict[tuple[Any, Any], list[RetrievalEvidence]] = {}
    for item in results:
        key = (item.metadata.get("noteId"), item.metadata.get("attachmentId"))
        grouped.setdefault(key, []).append(item)
    diversified: list[RetrievalEvidence] = []
    depth = 0
    while len(diversified) < limit:
        layer = [items[depth] for items in grouped.values() if len(items) > depth]
        if not layer:
            break
        diversified.extend(layer[: limit - len(diversified)])
        depth += 1
    return diversified


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
            return _vector_store().validate_external_evidence(
                session, _retrieve_qdrant(cognitive, query, limit)
            )
        except Exception:
            return []
    if store == "chroma" and cognitive["chroma_url"]:
        try:
            return _vector_store().validate_external_evidence(
                session, _retrieve_chroma(cognitive, query, limit)
            )
        except Exception:
            return []
    return []


def retrieve_graph(
    session: Session, query: str, limit: int = 10
) -> tuple[list[RetrievalEvidence], list[str]]:
    query_tokens = _query_tokens(query)
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
        score = _token_score(query_tokens, _search_tokens(body))
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
        score = _token_score(query_tokens, _search_tokens(body))
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
    question: str = "",
    limit: int = 12,
    max_text_chars: int = 1200,
    max_total_chars: int = 9000,
) -> list[dict[str, Any]]:
    if limit < 1 or max_text_chars < 1 or max_total_chars < 1:
        raise ValueError("Evidence limits must be positive")

    grouped: dict[str, list[dict[str, Any]]] = {}
    group_order: list[str] = []
    seen_items: set[str] = set()
    for item in evidence:
        metadata = (
            item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        )
        source_note_ids = metadata.get("sourceNoteIds")
        if isinstance(source_note_ids, list) and source_note_ids:
            source_key = "notes:" + ",".join(
                sorted(str(value) for value in source_note_ids)
            )
        elif metadata.get("attachmentId") is not None:
            source_key = f"attachment:{metadata['attachmentId']}"
        elif metadata.get("noteId") is not None:
            source_key = f"note:{metadata['noteId']}"
        elif metadata.get("nodeId") is not None:
            source_key = f"node:{metadata['nodeId']}"
        elif metadata.get("edgeId") is not None:
            source_key = f"edge:{metadata['edgeId']}"
        else:
            source_key = str(item.get("source") or item.get("title") or "unknown")
        fingerprint = hashlib.sha256(
            json.dumps(
                {
                    "source": source_key,
                    "title": item.get("title"),
                    "text": item.get("text"),
                },
                ensure_ascii=True,
                sort_keys=True,
            ).encode()
        ).hexdigest()
        if fingerprint in seen_items:
            continue
        seen_items.add(fingerprint)
        if source_key not in grouped:
            grouped[source_key] = []
            group_order.append(source_key)
        grouped[source_key].append(item)

    diversified: list[dict[str, Any]] = []
    depth = 0
    while len(diversified) < limit:
        added = False
        for source_key in group_order:
            rows = grouped[source_key]
            if depth < len(rows):
                diversified.append(rows[depth])
                added = True
                if len(diversified) == limit:
                    break
        if not added:
            break
        depth += 1

    bounded: list[dict[str, Any]] = []
    total = 0
    question_tokens = _tokens(question)
    for item in diversified:
        text = str(item.get("text") or "").strip()
        remaining = max_total_chars - total
        if remaining <= 0:
            break
        text = query_aware_excerpt(
            text,
            question,
            min(max_text_chars, remaining),
        )
        metadata = (
            item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        )
        stable_source = str(
            metadata.get("evidenceKey")
            or metadata.get("documentId")
            or metadata.get("noteId")
            or metadata.get("nodeId")
            or metadata.get("edgeId")
            or item.get("title")
            or item.get("source")
            or len(bounded)
        )
        evidence_id = (
            "evidence-"
            + hashlib.sha256(f"{stable_source}:{text}".encode()).hexdigest()[:12]
        )
        bounded.append(
            {
                **item,
                "text": text,
                "evidenceId": evidence_id,
                "queryTokenOverlap": len(question_tokens & _tokens(text)),
            }
        )
        total += len(text)
    return bounded


def _validated_citations(
    returned: Any, supplied: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not isinstance(returned, list) or not returned:
        return []
    allowed = {item["evidenceId"]: item for item in supplied}
    resolved: list[dict[str, Any]] = []
    seen: set[str] = set()
    for citation in returned:
        identity = (
            citation
            if isinstance(citation, str)
            else citation.get("evidenceId")
            if isinstance(citation, dict)
            else None
        )
        if not isinstance(identity, str) or identity not in allowed:
            return []
        source = allowed[identity]
        if (
            isinstance(citation, dict)
            and citation.get("quote")
            and " ".join(str(citation["quote"]).split())
            not in " ".join(str(source["text"]).split())
        ):
            return []
        if identity not in seen:
            metadata = source.get("metadata") or {}
            resolved.append(
                {
                    **source,
                    "id": identity,
                    "evidenceId": identity,
                    **{
                        key: metadata[key]
                        for key in ("noteId", "nodeId", "edgeId", "path")
                        if key in metadata
                    },
                    "citationStatus": "source_verified",
                }
            )
            seen.add(identity)
    return resolved


def _evidence_source_snapshot(
    session: Session, evidence: list[dict[str, Any]]
) -> dict[str, str] | None:
    from berrybrain_api.config import get_settings
    from berrybrain_api.models import AttachmentExtractionRecord, NoteAttachmentRecord
    from berrybrain_api.vault import read_note

    snapshot: dict[str, str] = {}
    try:
        for item in evidence:
            metadata = item.get("metadata") or {}
            note_ids = list(metadata.get("sourceNoteIds") or [])
            if metadata.get("noteId") is not None:
                note_ids.append(metadata["noteId"])
            if (
                item.get("source") != "semantic_data"
                and not note_ids
                and not any(
                    metadata.get(key) is not None
                    for key in ("nodeId", "edgeId", "attachmentId")
                )
            ):
                return None
            for raw_id in note_ids:
                identity = int(raw_id)
                note = session.get(NoteRecord, identity, populate_existing=True)
                if note is None:
                    return None
                current = read_note(get_settings().vault_path, note.path)
                if current["content_hash"] != note.content_hash:
                    return None
                snapshot[f"note:{identity}"] = (
                    f"{note.stable_id}:{note.content_hash}:{note.path}"
                )
            if metadata.get("attachmentId") is not None:
                attachment_id = int(metadata["attachmentId"])
                attachment = session.get(
                    NoteAttachmentRecord, attachment_id, populate_existing=True
                )
                extraction = session.scalar(
                    select(AttachmentExtractionRecord)
                    .where(AttachmentExtractionRecord.attachment_id == attachment_id)
                    .execution_options(populate_existing=True)
                )
                if (
                    attachment is None
                    or extraction is None
                    or extraction.status != "completed"
                ):
                    return None
                root = get_settings().vault_path.resolve()
                binary = (root / attachment.stored_path).resolve()
                if root not in binary.parents or not binary.is_file():
                    return None
                with binary.open("rb") as stream:
                    if (
                        hashlib.file_digest(stream, "sha256").hexdigest()
                        != attachment.checksum
                    ):
                        return None
                snapshot[f"attachment:{attachment_id}"] = (
                    f"{attachment.checksum}:{hashlib.sha256(extraction.extracted_text.encode()).hexdigest()}"
                )
            for field, model, clause in (
                ("nodeId", GraphNodeRecord, accepted_node_clause()),
                ("edgeId", GraphEdgeRecord, accepted_edge_clause()),
            ):
                if metadata.get(field) is None:
                    continue
                identity = int(metadata[field])
                record = session.scalar(
                    select(model)
                    .where(model.id == identity, clause)
                    .execution_options(populate_existing=True)
                )
                if record is None:
                    return None
                snapshot[f"{field}:{identity}"] = str(getattr(record, "updated_at", ""))
        return snapshot
    except Exception:
        return None


def _unsupported_answer(
    question: str, orchestrated: dict[str, Any], reason: str
) -> dict[str, Any]:
    return {
        "status": "insufficient_evidence",
        "question": question,
        "answer": "There is not enough verified, current evidence to return this answer.",
        "evidence": [],
        "relatedNodes": [],
        "routes": orchestrated.get("routes", []),
        "reason": reason,
        "confidence": 0.0,
        "judge_status": "not_evaluated",
        "suggestions": ["Review the source notes and retry the question."],
    }


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
