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
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from berrybrain_api.ai_configuration import embedding_execution_configuration
from berrybrain_api.ai_gateway import (
    GraphAIUnavailable,
    generate_query_embedding,
)
from berrybrain_api.cognitive_state import cognitive_config
from berrybrain_api.filesystem import serialized_vault
from berrybrain_api.models import (
    AttachmentExtractionRecord,
    EmbeddingRecord,
    NoteAttachmentRecord,
    NoteRecord,
    SettingRecord,
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


@serialized_vault
def index_knowledge_base(session: Session) -> dict[str, Any]:
    from berrybrain_api.vector_cleanup import drain_vector_cleanup, register_collection

    cleanup = drain_vector_cleanup(session)
    if cleanup["pending"]:
        return {
            "status": "failed",
            "reason": "pending_vector_cleanup",
            "cleanup": cleanup,
        }
    cognitive = cognitive_config(session)
    cognitive.update(embedding_execution_configuration(session))
    chunk_size = _int_setting(cognitive["kb_chunk_size"], 900, 300, 4000)
    overlap = _int_setting(
        cognitive.get("kb_chunk_overlap", "120"), 120, 0, chunk_size - 1
    )
    cognitive["kb_chunk_overlap"] = str(overlap)
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
    store = cognitive["kb_vector_store"]
    collection_key = f"internal.vector_collection.{store}"
    previous_collection = session.scalar(
        select(SettingRecord).where(SettingRecord.key == collection_key)
    )
    if (
        not chunk_records
        and previous_collection is not None
        and not cognitive.get(f"{store}_collection")
    ):
        cognitive[f"{store}_collection"] = previous_collection.value
    if store in {"qdrant", "chroma"} and cognitive.get(f"{store}_url"):
        dimension = (
            len(chunk_records[0]["vector"]) if chunk_records else VECTOR_DIMENSIONS
        )
        register_collection(
            session,
            store,
            cognitive[f"{store}_url"],
            _collection_name(cognitive, store, dimension),
        )
        # Remember partial external writes too, so a failed sync remains cleanable.
        session.commit()
    external_sync = sync_external_vector_store(cognitive, chunk_records)
    if external_sync.get("status") == "synced" and external_sync.get("collection"):
        register_collection(
            session, store, cognitive[f"{store}_url"], external_sync["collection"]
        )
        if previous_collection is None:
            session.add(
                SettingRecord(key=collection_key, value=external_sync["collection"])
            )
        else:
            previous_collection.value = external_sync["collection"]
        session.commit()
    missing_embeddings = [
        note.path for note in processable_notes if note.id not in embeddings
    ]
    skipped_empty = [note.path for note in notes if not (note.content or "").strip()]
    return {
        "status": "failed" if external_sync.get("status") == "failed" else "indexed",
        "store": cognitive["kb_vector_store"],
        "qdrant": "configured" if cognitive["qdrant_url"] else "not_configured",
        "chroma": "configured" if cognitive["chroma_url"] else "not_configured",
        "chunkSize": chunk_size,
        "chunkOverlap": overlap,
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


def chunk_markdown(content: str, max_chars: int = 900, overlap: int = 0) -> list[str]:
    if max_chars < 1 or overlap < 0 or overlap >= max_chars:
        raise ValueError(
            "Chunk size must be positive and overlap smaller than chunk size"
        )
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
            text = text[max(1, cut - min(overlap, cut - 1)) :].strip()
        if text:
            chunks.append(text)
    return chunks or ([content.strip()] if content and content.strip() else [])


def _generate_chunk_embedding(
    cognitive: dict[str, str], text: str, *, input_type: str = "passage"
) -> tuple[list[float], str]:
    try:
        vector = generate_query_embedding(
            cognitive,
            text,
            input_type=input_type,
            prompt_version=f"embedding-{input_type}.v1",
        )
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
        overlap = _int_setting(
            cognitive.get("kb_chunk_overlap", "120"), 120, 0, chunk_size - 1
        )
        for index, chunk in enumerate(
            chunk_markdown(note.content, chunk_size, overlap)
        ):
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
                        "note_stable_id": note.stable_id,
                        "content_hash": note.content_hash,
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
            chunk_markdown(
                extraction.extracted_text,
                chunk_size,
                _int_setting(
                    cognitive.get("kb_chunk_overlap", "120"), 120, 0, chunk_size - 1
                ),
            )
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
                        "note_stable_id": note.stable_id,
                        "content_hash": note.content_hash,
                        "attachment_checksum": attachment.checksum,
                        "extraction_hash": hashlib.sha256(
                            extraction.extracted_text.encode()
                        ).hexdigest(),
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
    return str(
        uuid5(NAMESPACE_URL, f"berrybrain:attachment:{attachment_id}:chunk:{index}")
    )


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
        f"{provider}:{model}:{chunk_size}:{dimension}:{cognitive.get('kb_chunk_overlap', '120')}:passage-v2".encode()
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
            f"{collection_url}/points?wait=true",
            {"points": batch},
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    live_ids = {str(item["id"]) for item in records}
    stale_ids: list[Any] = []
    offset = None
    while True:
        payload: dict[str, Any] = {
            "filter": {"must": [{"key": "source", "match": {"value": "berrybrain"}}]},
            "limit": 256,
            "with_payload": False,
            "with_vector": False,
        }
        if offset is not None:
            payload["offset"] = offset
        page = _http_json(
            "POST", f"{collection_url}/points/scroll", payload, {200}
        ).get("result", {})
        stale_ids.extend(
            point["id"]
            for point in page.get("points", [])
            if str(point["id"]) not in live_ids
        )
        next_offset = page.get("next_page_offset")
        if next_offset is None or next_offset == offset:
            break
        offset = next_offset
    for batch in _batches(stale_ids, 256):
        _http_json(
            "POST",
            f"{collection_url}/points/delete?wait=true",
            {"points": batch},
            {200},
        )
    return {
        "status": "synced",
        "store": "qdrant",
        "collection": collection,
        "chunks": upserted,
        "removedChunks": len(stale_ids),
        "vectorSize": dimension,
    }


def _chroma_collections_url(cognitive: dict[str, str]) -> str:
    from urllib.parse import quote

    base = cognitive["chroma_url"].rstrip("/")
    # Explicit /api/v1 keeps older, operator-pinned installations usable.
    if base.endswith("/api/v1"):
        return f"{base}/collections"
    base = base.removesuffix("/api/v2")
    tenant = quote(cognitive.get("chroma_tenant", "default_tenant"), safe="")
    database = quote(cognitive.get("chroma_database", "default_database"), safe="")
    return f"{base}/api/v2/tenants/{tenant}/databases/{database}/collections"


def _sync_chroma(
    cognitive: dict[str, str], records: list[dict[str, Any]]
) -> dict[str, Any]:
    dimension = (
        len(records[0]["vector"])
        if records and records[0].get("vector")
        else VECTOR_DIMENSIONS
    )
    collections_url = _chroma_collections_url(cognitive)
    collection = _collection_name(cognitive, "chroma", dimension)
    created = _http_json(
        "POST",
        collections_url,
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
            f"{collections_url}/{collection_id}/upsert",
            {
                "ids": [item["documentId"] for item in batch],
                "embeddings": [item["vector"] for item in batch],
                "metadatas": [item["metadata"] for item in batch],
                "documents": [item["text"] for item in batch],
            },
            ok_statuses={200, 201},
        )
        upserted += len(batch)
    live_ids = {item["documentId"] for item in records}
    stale_ids = []
    offset = 0
    while True:
        page = _http_json(
            "POST",
            f"{collections_url}/{collection_id}/get",
            {
                "where": {"source": "berrybrain"},
                "include": [],
                "limit": 256,
                "offset": offset,
            },
            {200},
        )
        ids = page.get("ids", [])
        stale_ids.extend(identity for identity in ids if identity not in live_ids)
        if len(ids) < 256:
            break
        offset += len(ids)
    for batch in _batches(stale_ids, 256):
        _http_json(
            "POST", f"{collections_url}/{collection_id}/delete", {"ids": batch}, {200}
        )
    return {
        "status": "synced",
        "store": "chroma",
        "collection": collection,
        "chunks": upserted,
        "removedChunks": len(stale_ids),
        "vectorSize": dimension,
    }


def _retrieve_qdrant(
    cognitive: dict[str, str], query: str, limit: int
) -> list[RetrievalEvidence]:
    vector, _ = _generate_chunk_embedding(cognitive, query, input_type="query")
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
                    "noteStableId": payload.get("note_stable_id"),
                    "contentHash": payload.get("content_hash"),
                    "attachmentId": payload.get("attachment_id"),
                    "attachmentChecksum": payload.get("attachment_checksum"),
                    "extractionHash": payload.get("extraction_hash"),
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
    vector, _ = _generate_chunk_embedding(cognitive, query, input_type="query")
    dimension = len(vector)
    collections_url = _chroma_collections_url(cognitive)
    collection = _collection_name(cognitive, "chroma", dimension)
    created = _http_json(
        "POST",
        collections_url,
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
        f"{collections_url}/{collection_id}/query",
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
                    "noteStableId": metadata.get("note_stable_id"),
                    "contentHash": metadata.get("content_hash"),
                    "attachmentId": metadata.get("attachment_id"),
                    "attachmentChecksum": metadata.get("attachment_checksum"),
                    "extractionHash": metadata.get("extraction_hash"),
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
        data=None if method == "GET" else data,
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


def validate_external_evidence(
    session: Session, items: list[RetrievalEvidence]
) -> list[RetrievalEvidence]:
    """Old/unknown index schemas fail closed until an explicit reindex.

    A vector score is never sufficient authority to resurrect a deleted or
    edited source. Check the current database identity AND canonical file.
    """
    from berrybrain_api.config import get_settings
    from berrybrain_api.vault import read_note

    valid: list[RetrievalEvidence] = []
    for item in items:
        metadata = item.metadata
        try:
            note = session.get(
                NoteRecord, int(metadata.get("noteId")), populate_existing=True
            )
            if note is None or metadata.get("noteStableId") != note.stable_id:
                continue
            if (
                not metadata.get("contentHash")
                or metadata["contentHash"] != note.content_hash
            ):
                continue
            current = read_note(get_settings().vault_path, note.path)
            if current["content_hash"] != note.content_hash:
                continue
            attachment_id = metadata.get("attachmentId")
            if attachment_id is not None:
                attachment = session.get(
                    NoteAttachmentRecord, int(attachment_id), populate_existing=True
                )
                extraction = session.scalar(
                    select(AttachmentExtractionRecord)
                    .where(
                        AttachmentExtractionRecord.attachment_id == int(attachment_id)
                    )
                    .execution_options(populate_existing=True)
                )
                if (
                    attachment is None
                    or attachment.note_id != note.id
                    or extraction is None
                    or extraction.status != "completed"
                ):
                    continue
                if metadata.get("attachmentChecksum") != attachment.checksum:
                    continue
                if (
                    metadata.get("extractionHash")
                    != hashlib.sha256(extraction.extracted_text.encode()).hexdigest()
                ):
                    continue
                if item.text not in extraction.extracted_text:
                    continue
                metadata = {
                    **metadata,
                    "path": attachment.stored_path,
                    "notePath": note.path,
                }
            else:
                if item.text not in str(current["content"]):
                    continue
                metadata = {**metadata, "path": note.path}
            valid.append(
                RetrievalEvidence(
                    item.source, item.title, item.text, item.score, metadata
                )
            )
        except (ValueError, TypeError, OSError):
            continue
        except Exception as exc:
            # Missing/malformed sources must not downgrade to trusting the index.
            logging.debug("External evidence rejected: %s", type(exc).__name__)
    return valid


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
