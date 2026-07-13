from __future__ import annotations

from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session


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
    try:
        rows = session.execute(
            text(
                "SELECT n.id, n.title, n.path, n.content, rank FROM notes_fts f "
                "JOIN notes n ON n.id = f.rowid "
                "WHERE notes_fts MATCH :query "
                "ORDER BY rank LIMIT :limit"
            ),
            {"query": query, "limit": limit},
        ).fetchall()
    except Exception:
        rows = []

    tokens = [t for t in query.lower().split() if len(t) > 1]
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


def _snippet(content: str, tokens: list[str], size: int = 180) -> str:
    lowered = content.lower()
    positions = [lowered.find(token) for token in tokens if lowered.find(token) >= 0]
    if not positions:
        return content[:size].replace("\n", " ").strip()
    start = max(0, min(positions) - 60)
    end = min(len(content), start + size)
    return content[start:end].replace("\n", " ").strip()
