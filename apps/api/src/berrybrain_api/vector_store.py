from __future__ import annotations

import hashlib
import json
import logging
import math
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import embedding_execution_configuration
from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_query_embedding,
)
from berrybrain_api.cognitive_layer import cognitive_config
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    EmbeddingRecord,
    NoteAttachmentRecord,
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


def index_knowledge_base(session: Session) -> dict[str, Any]:
    cognitive = cognitive_config(session)
    cognitive.update(embedding_execution_configuration(session))
    chunk_size = _int_setting(cognitive["kb_chunk_size"], 900, 300, 4000)
    notes = list(session.execute(select(NoteRecord)).scalars())
    processable_notes = [note for note in notes if (note.content or "").strip()]
    attachment_chunks = _attachment_chunks(session, chunk_size, cognitive)
    embeddings = {
        emb.note_id: emb for emb in session.execute(select(EmbeddingRecord)).scalars()
    }
    chunk_records = (
        _knowledge_chunks(processable_notes, chunk_size, cognitive) + attachment_chunks
    )
    chunk_count = len(chunk_records)
    external_sync = sync_external_vector_store(cognitive, chunk_records)
    missing_embeddings = [
        note.path for note in processable_notes if note.id not in embeddings
    ]
    skipped_empty = [note.path for note in notes if not (note.content or "").strip()]
    return {
        "status": "indexed",
        "store": cognitive["kb_vector_store"],
        "qdrant": "configured" if cognitive["qdrant_url"] else "not_configured",
        "chroma": "configured" if cognitive["chroma_url"] else "not_configured",
        "chunkSize": chunk_size,
        "chunkOverlap": _int_setting(cognitive["kb_chunk_overlap"], 120, 0, 1000),
        "embeddingProvider": cognitive["kb_embedding_provider"],
        "embeddingModel": cognitive["kb_embedding_model"],
        "notes": len(notes),
        "processableNotes": len(processable_notes),
        "skippedEmptyNotes": skipped_empty[:20],
        "chunks": chunk_count,
        "attachmentChunks": len(attachment_chunks),
        "embeddings": len(embeddings),
        "externalVectorStore": external_sync,
        "missingEmbeddings": missing_embeddings[:20],
        "updatedAt": datetime.now(UTC).isoformat(),
    }


def sync_external_vector_store(
    cognitive: dict[str, str],
    chunk_records: list[dict[str, Any]],
) -> dict[str, Any]:
    store = cognitive["kb_vector_store"]
    if store == "qdrant":
        if not cognitive["qdrant_url"]:
            return {"status": "skipped", "store": "qdrant", "reason": "missing_url"}
        try:
            return _sync_qdrant(cognitive, chunk_records)
        except Exception as exc:
            logging.warning("Qdrant sync failed: %s", exc)
            return {
                "status": "failed",
                "store": "qdrant",
                "error": "External vector store sync failed.",
            }
    if store == "chroma":
        if not cognitive["chroma_url"]:
            return {"status": "skipped", "store": "chroma", "reason": "missing_url"}
        try:
            return _sync_chroma(cognitive, chunk_records)
        except Exception as exc:
            logging.warning("Chroma sync failed: %s", exc)
            return {
                "status": "failed",
                "store": "chroma",
                "error": "External vector store sync failed.",
            }
    return {"status": "skipped", "store": "sqlite", "reason": "local_fallback"}


def chunk_markdown(content: str, max_chars: int = 900) -> list[str]:
    parts = re.split(r"\n(?=#{1,6}\s)", content or "")
    chunks: list[str] = []
    for part in parts:
        text = part.strip()
        if not text:
            continue
        while len(text) > max_chars:
            cut = text.rfind("\n", 0, max_chars)
            if cut < max_chars // 2:
                cut = max_chars
            chunks.append(text[:cut].strip())
            text = text[cut:].strip()
        if text:
            chunks.append(text)
    return chunks or ([content.strip()] if content and content.strip() else [])


def _generate_chunk_embedding(
    cognitive: dict[str, str], text: str
) -> tuple[list[float], str]:
    try:
        vector = generate_query_embedding(cognitive, text)
        provider = cognitive.get("embedding_provider") or cognitive.get("provider")
        if provider not in {"cloud", "local"}:
            raise GraphAIUnavailable("Embedding provider is not configured")
        model = (
            cognitive.get("embedding_model")
            or cognitive.get("cloud_model")
            or cognitive.get("ollama_model")
        )
        if not model:
            raise GraphAIUnavailable("Embedding model is not configured")
        return vector, f"{provider}/{model}"
    except GraphAIUnavailable:
        raise
    except Exception as exc:
        logging.exception("Embedding generation failed")
        raise GraphAIUnavailable(
            "Embedding generation failed with the configured provider"
        ) from exc


def _knowledge_chunks(
    notes: list[NoteRecord], chunk_size: int, cognitive: dict[str, str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for note in notes:
        for index, chunk in enumerate(chunk_markdown(note.content, chunk_size)):
            vector, embedding_type = _generate_chunk_embedding(
                cognitive, " ".join([note.title or "", chunk])
            )
            records.append(
                {
                    "id": _stable_chunk_id(note.id, index),
                    "documentId": f"note:{note.id}:chunk:{index}",
                    "noteId": note.id,
                    "title": note.title,
                    "path": note.path,
                    "chunkIndex": index,
                    "text": chunk,
                    "vector": vector,
                    "metadata": {
                        "source": "berrybrain",
                        "kind": "note_chunk",
                        "note_id": note.id,
                        "path": note.path,
                        "title": note.title,
                        "chunk": index,
                        "embedding_type": embedding_type,
                    },
                }
            )
    return records


def _attachment_chunks(
    session: Session, chunk_size: int, cognitive: dict[str, str]
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for attachment, extraction, note in _extracted_attachments(session):
        for index, chunk in enumerate(
            chunk_markdown(extraction.extracted_text, chunk_size)
        ):
            vector, embedding_type = _generate_chunk_embedding(
                cognitive,
                " ".join([attachment.filename or "", note.title or "", chunk]),
            )
            records.append(
                {
                    "id": _stable_attachment_chunk_id(attachment.id, index),
                    "documentId": f"attachment:{attachment.id}:chunk:{index}",
                    "noteId": note.id,
                    "attachmentId": attachment.id,
                    "title": attachment.filename,
                    "path": attachment.stored_path,
                    "chunkIndex": index,
                    "text": chunk,
                    "vector": vector,
                    "metadata": {
                        "source": "berrybrain",
                        "kind": "attachment_text",
                        "note_id": note.id,
                        "attachment_id": attachment.id,
                        "path": attachment.stored_path,
                        "note_path": note.path,
                        "title": attachment.filename,
                        "chunk": index,
                        "embedding_type": embedding_type,
                    },
                }
            )
    return records


def _extracted_attachments(
    session: Session,
) -> list[tuple[NoteAttachmentRecord, AttachmentExtractionRecord, NoteRecord]]:
    return list(
        session.execute(
            select(NoteAttachmentRecord, AttachmentExtractionRecord, NoteRecord)
            .join(
                AttachmentExtractionRecord,
                AttachmentExtractionRecord.attachment_id == NoteAttachmentRecord.id,
            )
            .join(NoteRecord, NoteRecord.id == NoteAttachmentRecord.note_id)
            .where(
                AttachmentExtractionRecord.status == "completed",
                AttachmentExtractionRecord.extracted_text != "",
            )
        ).all()
    )


def _stable_attachment_chunk_id(attachment_id: int, index: int) -> str:
    return hashlib.sha1(f"attachment:{attachment_id}:{index}".encode()).hexdigest()


def _stable_chunk_id(note_id: int, chunk_index: int) -> int:
    raw = f"note:{note_id}:chunk:{chunk_index}".encode()
    return int(hashlib.sha1(raw).hexdigest()[:15], 16)


def _hash_embedding(text: str, dimensions: int = VECTOR_DIMENSIONS) -> list[float]:
    vector = [0.0] * dimensions
    for token in _tokens(text):
        digest = hashlib.sha1(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:2], "big") % dimensions
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [round(value / norm, 6) for value in vector]


def _collection_name(cognitive: dict[str, str], prefix: str, dimension: int) -> str:
    configured = cognitive.get(f"{prefix}_collection")
    if configured:
        return configured
    provider = cognitive.get("kb_embedding_provider", "local")
    model = cognitive.get("kb_embedding_model", "hash")
    chunk_size = cognitive.get("kb_chunk_size", "900")
    fingerprint = hashlib.sha1(
        f"{provider}:{model}:{chunk_size}:{dimension}".encode()
    ).hexdigest()[:8]
    return f"berrybrain_{fingerprint}"


def _sync_qdrant(
    cognitive: dict[str, str], records: list[dict[str, Any]]
) -> dict[str, Any]:
    dimension = (
        len(records[0]["vector"])
        if records and records[0].get("vector")
        else VECTOR_DIMENSIONS
    )
    base_url = cognitive["qdrant_url"].rstrip("/")
    collection = _collection_name(cognitive, "qdrant", dimension)
    collection_url = f"{base_url}/collections/{collection}"
    _http_json(
        "PUT",
        collection_url,
        {
            "vectors": {
                "size": dimension,
                "distance": "Cosine",
            }
        },
        ok_statuses={200, 201, 409},
    )
    points = [
        {
            "id": item["id"],
            "vector": item["vector"],
            "payload": {
                **item["metadata"],
                "document_id": item["documentId"],
                "text": item["text"],
            },
        }
        for item in records
    ]
    upserted = 0
    for batch in _batches(points, 64):
        _http_json(
            "PUT",
            f"{collection_url}/points",
            {"points": batch},
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    return {
        "status": "synced",
        "store": "qdrant",
        "collection": collection,
        "chunks": upserted,
        "vectorSize": dimension,
    }


def _sync_chroma(
    cognitive: dict[str, str], records: list[dict[str, Any]]
) -> dict[str, Any]:
    dimension = (
        len(records[0]["vector"])
        if records and records[0].get("vector")
        else VECTOR_DIMENSIONS
    )
    base_url = cognitive["chroma_url"].rstrip("/")
    collection = _collection_name(cognitive, "chroma", dimension)
    created = _http_json(
        "POST",
        f"{base_url}/api/v1/collections",
        {
            "name": collection,
            "metadata": {"source": "berrybrain"},
            "get_or_create": True,
        },
        ok_statuses={200, 201, 409},
    )
    collection_id = created.get("id") or created.get("name") or collection
    upserted = 0
    for batch in _batches(records, 64):
        _http_json(
            "POST",
            f"{base_url}/api/v1/collections/{collection_id}/upsert",
            {
                "ids": [item["documentId"] for item in batch],
                "embeddings": [item["vector"] for item in batch],
                "metadatas": [item["metadata"] for item in batch],
                "documents": [item["text"] for item in batch],
            },
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    return {
        "status": "synced",
        "store": "chroma",
        "collection": collection,
        "chunks": upserted,
        "vectorSize": dimension,
    }


def _retrieve_qdrant(
    cognitive: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    vector, _ = _generate_chunk_embedding(cognitive, query)
    dimension = len(vector)
    base_url = cognitive["qdrant_url"].rstrip("/")
    collection = _collection_name(cognitive, "qdrant", dimension)
    result = _http_json(
        "POST",
        f"{base_url}/collections/{collection}/points/search",
        {
            "vector": vector,
            "limit": limit,
            "with_payload": True,
        },
        ok_statuses={200},
    )
    points = result.get("result", [])
    if not isinstance(points, list):
        return []
    evidence: list[RetrievalEvidence] = []
    for point in points:
        if not isinstance(point, dict):
            continue
        payload = point.get("payload") if isinstance(point.get("payload"), dict) else {}
        title = str(payload.get("title") or payload.get("path") or "Knowledge chunk")
        text = str(payload.get("text") or "")
        if not text.strip():
            continue
        score = _float_value(point.get("score"), 0.0)
        evidence.append(
            RetrievalEvidence(
                source="knowledge_base",
                title=title,
                text=text[:900],
                score=score,
                metadata={
                    "retrieval": "qdrant_vector",
                    "store": "qdrant",
                    "collection": collection,
                    "noteId": payload.get("note_id"),
                    "path": payload.get("path"),
                    "chunk": payload.get("chunk"),
                    "documentId": payload.get("document_id"),
                },
            )
        )
    return evidence


def _retrieve_chroma(
    cognitive: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    vector, _ = _generate_chunk_embedding(cognitive, query)
    dimension = len(vector)
    base_url = cognitive["chroma_url"].rstrip("/")
    collection = _collection_name(cognitive, "chroma", dimension)
    created = _http_json(
        "POST",
        f"{base_url}/api/v1/collections",
        {
            "name": collection,
            "metadata": {"source": "berrybrain"},
            "get_or_create": True,
        },
        ok_statuses={200, 201, 409},
    )
    collection_id = created.get("id") or created.get("name") or collection
    result = _http_json(
        "POST",
        f"{base_url}/api/v1/collections/{collection_id}/query",
        {
            "query_embeddings": [vector],
            "n_results": limit,
            "include": ["documents", "metadatas", "distances"],
        },
        ok_statuses={200},
    )
    documents = _first_nested_list(result.get("documents"))
    metadatas = _first_nested_list(result.get("metadatas"))
    distances = _first_nested_list(result.get("distances"))
    evidence: list[RetrievalEvidence] = []
    for index, document in enumerate(documents):
        text = str(document or "")
        if not text.strip():
            continue
        metadata = (
            metadatas[index]
            if index < len(metadatas) and isinstance(metadatas[index], dict)
            else {}
        )
        distance = _float_value(
            distances[index] if index < len(distances) else None, 1.0
        )
        evidence.append(
            RetrievalEvidence(
                source="knowledge_base",
                title=str(
                    metadata.get("title") or metadata.get("path") or "Knowledge chunk"
                ),
                text=text[:900],
                score=round(1 / (1 + max(distance, 0.0)), 6),
                metadata={
                    "retrieval": "chroma_vector",
                    "store": "chroma",
                    "collection": collection,
                    "noteId": metadata.get("note_id"),
                    "path": metadata.get("path"),
                    "chunk": metadata.get("chunk"),
                },
            )
        )
    return evidence


def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any],
    ok_statuses: set[int],
) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            if response.status not in ok_statuses:
                raise RuntimeError(f"HTTP {response.status}: {body[:240]}")
            return json.loads(body) if body.strip() else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in ok_statuses:
            return json.loads(body) if body.strip() else {}
        raise RuntimeError(f"HTTP {exc.code}: {body[:240]}") from exc


def _batches(items: list[Any], size: int) -> list[list[Any]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _first_nested_list(value: Any) -> list[Any]:
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    return value if isinstance(value, list) else []


def _float_value(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def _int_setting(value: str, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))
