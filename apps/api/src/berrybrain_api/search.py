from __future__ import annotations

from pathlib import Path
import re

from sqlalchemy import select
from sqlalchemy import text
from sqlalchemy.orm import Session

from berrybrain_api.models import ChunkRecord, ConnectionRecord, NoteRecord
from berrybrain_api.services import find_similar_chunks_by_vector


SEARCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "by",
    "de",
    "do",
    "da",
    "das",
    "dos",
    "e",
    "em",
    "for",
    "from",
    "in",
    "of",
    "o",
    "os",
    "para",
    "por",
    "the",
    "to",
    "um",
    "uma",
    "with",
}


def query_tokens(query: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[\w-]+", query.lower(), flags=re.UNICODE)
        if len(token) > 1 and token not in SEARCH_STOPWORDS
    ]


def init_fts(session: Session) -> None:
    session.execute(
        text("CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(title, content)")
    )
    session.execute(
        text(
            "CREATE TRIGGER IF NOT EXISTS notes_fts_insert AFTER INSERT ON notes BEGIN "
            "INSERT INTO notes_fts(rowid, title, content) VALUES (new.id, new.title, new.content); END"
        )
    )
    session.execute(
        text(
            "CREATE TRIGGER IF NOT EXISTS notes_fts_update AFTER UPDATE ON notes BEGIN "
            "UPDATE notes_fts SET title = new.title, content = new.content WHERE rowid = new.id; END"
        )
    )
    session.execute(
        text(
            "CREATE TRIGGER IF NOT EXISTS notes_fts_delete AFTER DELETE ON notes BEGIN "
            "DELETE FROM notes_fts WHERE rowid = old.id; END"
        )
    )
    session.commit()


def text_search(
    session: Session,
    query: str,
    limit: int = 20,
    vault_path: Path | None = None,
) -> list[dict]:
    results: dict[int, dict] = {}
    tokens = query_tokens(query)
    if not tokens:
        return []
    fts_query = " OR ".join(f'"{token.replace(chr(34), "")}"' for token in tokens)
    try:
        rows = session.execute(
            text(
                "SELECT n.id, n.title, n.path, n.content, rank FROM notes_fts f "
                "JOIN notes n ON n.id = f.rowid "
                "WHERE notes_fts MATCH :query "
                "ORDER BY rank LIMIT :limit"
            ),
            {"query": fts_query, "limit": limit},
        ).fetchall()
    except Exception:
        rows = []

    for r in rows:
        rid = int(r[0])
        title = r[1]
        path = r[2]
        content = r[3] or ""
        score = round(abs(r[4]), 4)
        # Detect source: title match gets higher base score indicating title hit,
        # content match gets lower base. rank already factors this.
        title_match = any(t in title.lower() for t in tokens) if tokens else True
        snippet = _snippet(content, tokens) if content else ""
        existing = results.get(rid)
        if existing is None or score < existing["score"]:
            results[rid] = {
                "id": rid,
                "title": title,
                "path": path,
                "score": score,
                "source": "title" if title_match else "body",
                "snippet": snippet,
            }

    return sorted(results.values(), key=lambda item: item["score"])[:limit]


def chunk_search(session: Session, query: str, limit: int = 20) -> list[dict]:
    tokens = query_tokens(query)
    if not tokens:
        return []

    rows = session.execute(
        select(ChunkRecord, NoteRecord)
        .join(NoteRecord, NoteRecord.id == ChunkRecord.note_id)
        .where(ChunkRecord.content_hash == NoteRecord.content_hash)
        .order_by(ChunkRecord.updated_at.desc())
        .limit(500)
    ).all()
    scored: list[dict] = []
    for chunk, note in rows:
        haystack = f"{note.title} {chunk.heading_path} {chunk.text}".lower()
        hits = sum(1 for token in tokens if token in haystack)
        if hits == 0:
            continue
        score = hits / max(1, len(tokens))
        scored.append(
            {
                "id": note.id,
                "title": note.title,
                "path": note.path,
                "score": round(1 - score, 4),
                "source": "chunk",
                "snippet": _snippet(chunk.text, tokens),
                "evidence": {
                    "chunkIndex": chunk.chunk_index,
                    "contentHash": chunk.content_hash,
                    "noteVersion": chunk.note_version,
                    "headingPath": chunk.heading_path,
                    "startLine": chunk.start_line,
                    "endLine": chunk.end_line,
                    "text": _snippet(chunk.text, tokens, size=240),
                },
            }
        )

    scored.sort(key=lambda item: item["score"])
    return scored[:limit]


def hybrid_search(
    session: Session,
    query: str,
    limit: int = 10,
    query_vector: list[float] | None = None,
) -> list[dict]:
    """Search notes using lexical, chunk, vector, and graph signals."""
    candidate_limit = max(limit, 50)
    text_results = text_search(session, query, limit=candidate_limit)
    chunk_results = chunk_search(session, query, limit=candidate_limit)
    vector_results = (
        find_similar_chunks_by_vector(
            session,
            query_vector,
            limit=candidate_limit,
        )
        if query_vector
        else []
    )

    seed_ids = {item["id"] for item in vector_results + text_results + chunk_results}
    graph_results: list[dict] = []
    if seed_ids:
        graph_rows = (
            session.query(ConnectionRecord, NoteRecord)
            .join(
                NoteRecord,
                (
                    (
                        ConnectionRecord.source_note_id.in_(seed_ids)
                        & (NoteRecord.id == ConnectionRecord.target_note_id)
                    )
                    | (
                        ConnectionRecord.target_note_id.in_(seed_ids)
                        & (NoteRecord.id == ConnectionRecord.source_note_id)
                    )
                ),
            )
            .filter(ConnectionRecord.status != "ignored")
            .limit(50)
            .all()
        )
        for connection, note in graph_rows:
            if note.id in seed_ids:
                continue
            graph_results.append(
                {
                    "id": note.id,
                    "title": note.title,
                    "path": note.path,
                    "score": 0.5,
                    "source": "graph",
                    "snippet": connection.reason[:240],
                    "evidence": {
                        "connectionType": connection.connection_type,
                        "text": connection.reason,
                    },
                }
            )

    weights = {
        "vector_chunk": 0.55,
        "title": 0.25,
        "body": 0.25,
        "chunk": 0.20,
        "graph": 0.10,
    }
    merged: dict[int, dict] = {}
    for item in vector_results + text_results + chunk_results + graph_results:
        note_id = item["id"]
        source = str(item.get("source") or "body")
        relevance = float(item.get("similarity") or max(0.0, 1 - item["score"]))
        weighted_relevance = relevance * weights.get(source, 0.15)
        current = merged.get(note_id)
        if current is None:
            merged[note_id] = {**item, "evidence": [], "_hybrid_score": 0.0}
            current = merged[note_id]
        current["_hybrid_score"] += weighted_relevance
        if weighted_relevance > current.get("_best_signal", -1):
            current.update(
                {
                    "title": item["title"],
                    "path": item["path"],
                    "snippet": item.get("snippet", ""),
                    "source": source,
                    "_best_signal": weighted_relevance,
                }
            )
        if item.get("evidence"):
            current["evidence"].append(item["evidence"])

    for item in merged.values():
        item["_hybrid_score"] = min(1.0, item["_hybrid_score"])
        item["score"] = round(1 - item["_hybrid_score"], 4)
    results = sorted(
        merged.values(), key=lambda item: item["_hybrid_score"], reverse=True
    )[:limit]

    note_ids = [result["id"] for result in results]
    backlinks: dict[int, list[dict]] = {}
    if note_ids:
        rows = (
            session.query(
                ConnectionRecord.source_note_id,
                ConnectionRecord.target_note_id,
                ConnectionRecord.connection_type,
                ConnectionRecord.reason,
                NoteRecord.path.label("source_path"),
                NoteRecord.title.label("source_title"),
            )
            .join(NoteRecord, ConnectionRecord.source_note_id == NoteRecord.id)
            .filter(ConnectionRecord.target_note_id.in_(note_ids))
            .all()
        )
        for row in rows:
            backlinks.setdefault(row.target_note_id, []).append(
                {
                    "note_path": row.source_path,
                    "note_title": row.source_title,
                    "connection_type": row.connection_type,
                    "reason": row.reason,
                }
            )

    return [
        {
            "id": result["id"],
            "title": result["title"],
            "path": result["path"],
            "score": result["score"],
            "snippet": result.get("snippet", ""),
            "source": result.get("source", ""),
            "evidence": result.get("evidence", [])[:3],
            "backlinks": backlinks.get(result["id"], []),
        }
        for result in results
    ]


def _snippet(content: str, tokens: list[str], size: int = 180) -> str:
    lowered = content.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    if not positions:
        return content[:size].replace("\n", " ").strip()
    start = max(0, min(positions) - 60)
    end = min(len(content), start + size)
    return content[start:end].replace("\n", " ").strip()
