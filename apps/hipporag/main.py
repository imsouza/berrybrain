"""BerryBrain HippoRAG sidecar.

Lightweight multi-hop knowledge graph retrieval service.

The real `hipporag` PyPI package pinned in earlier requirements is unresolvable
(no matching distribution). Instead of pulling a heavy torch/vLLM stack, this
sidecar implements the ADR's contract (002-hipporag-sidecar.md): HTTP
`/index`, `/retrieve`, `/reconcile`, `/rebuild` endpoints, per-vault isolation,
graceful offline fallback, and multi-hop graph search over a SQLite-backed
knowledge graph. Triple extraction is regex/heuristic so the sidecar runs
without an LLM; set `HIPPORAG_LLM_URL` to an Ollama-compatible endpoint for
richer OpenIE-style triples (ponytail: upgrade path, not required for MVP).

Indexed documents persist in `/data/hipporag.db` (one shared SQLite DB with a
`vault_id` column per ponytail rule — fewer files than per-vault DBs).
"""

from __future__ import annotations

import json
import math
import os
import re
import sqlite3
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(title="BerryBrain HippoRAG Sidecar")

DATA_DIR = Path(os.getenv("HIPPORAG_DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "hipporag.db"
# ponytail: optional LLM endpoint. If unset, extraction is heuristic only.
LLM_URL = os.getenv("HIPPORAG_LLM_URL", "")
SERVICE_TOKEN = os.getenv("HIPPORAG_SERVICE_TOKEN", "")
TOKEN_RE = re.compile(r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9_-]{2,}")
SENTENCE_PREDICATES = (
    "relates to",
    "relates_to",
    "depends on",
    "depends_on",
    "connects to",
    "connects_to",
    "describes",
    "defines",
    "extends",
    "contains",
    "reflects",
    "powers",
    "generates",
    "provides",
    "supports",
    "enables",
    "builds",
    "creates",
    "processes",
    "covers",
    "targets",
    "references",
    "mentions",
    "uses",
    "are",
    "is",
)


class IndexRequest(BaseModel):
    vault_id: str
    doc_id: str
    content: str


class RetrieveRequest(BaseModel):
    vault_id: str
    query: str
    top_k: int = 5
    max_hops: int = 2


def _ensure_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


@contextmanager
def _db():
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        _init_schema(conn)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS docs (
            vault_id TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at REAL NOT NULL,
            PRIMARY KEY (vault_id, doc_id)
        );
        CREATE TABLE IF NOT EXISTS triples (
            vault_id TEXT NOT NULL,
            doc_id TEXT NOT NULL,
            subject TEXT NOT NULL,
            predicate TEXT NOT NULL,
            object TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_triples_vault ON triples(vault_id);
        CREATE INDEX IF NOT EXISTS idx_triples_doc ON triples(vault_id, doc_id);
        CREATE INDEX IF NOT EXISTS idx_triples_subject ON triples(vault_id, subject);
        CREATE INDEX IF NOT EXISTS idx_triples_object ON triples(vault_id, object);
        """
    )


def _tokens(text: str) -> set[str]:
    return {m.group(0).lower() for m in TOKEN_RE.finditer(text or "")}


def _normalize_spaces(text: str) -> str:
    return " ".join(str(text or "").split())


def _strip_inline_markup(text: str) -> str:
    cleaned = str(text or "")
    for char in "[]*`#()_":
        cleaned = cleaned.replace(char, " ")
    return _normalize_spaces(cleaned)


def _wiki_targets(line: str) -> Iterable[str]:
    offset = 0
    while True:
        start = line.find("[[", offset)
        if start < 0:
            return
        end = line.find("]]", start + 2)
        if end < 0:
            return
        body = line[start + 2 : end].split("|", 1)[0].strip()
        if body:
            yield body
        offset = end + 2


def _markdown_links(line: str) -> Iterable[tuple[str, str]]:
    offset = 0
    while True:
        text_start = line.find("[", offset)
        if text_start < 0:
            return
        text_end = line.find("]", text_start + 1)
        url_start = text_end + 1
        if text_end < 0 or url_start >= len(line) or line[url_start] != "(":
            offset = text_start + 1
            continue
        url_end = line.find(")", url_start + 1)
        if url_end < 0:
            return
        text = line[text_start + 1 : text_end].strip()
        url = line[url_start + 1 : url_end].strip()
        if text and url:
            yield text, url
        offset = url_end + 1


def _bold_entities(line: str) -> Iterable[str]:
    offset = 0
    while True:
        start = line.find("**", offset)
        if start < 0:
            return
        end = line.find("**", start + 2)
        if end < 0:
            return
        value = line[start + 2 : end].strip()
        if value:
            yield value
        offset = end + 2


def _sentences(text: str) -> Iterable[str]:
    start = 0
    for index, char in enumerate(text):
        if char not in ".!?":
            continue
        sentence = text[start : index + 1].strip()
        if sentence:
            yield sentence
        start = index + 1
    tail = text[start:].strip()
    if tail:
        yield tail


def _parse_sentence_relation(sentence: str) -> tuple[str, str, str] | None:
    lowered = sentence.lower()
    for predicate in SENTENCE_PREDICATES:
        marker = f" {predicate} "
        index = lowered.find(marker)
        if index <= 0:
            continue
        subject = sentence[:index].strip()
        obj = sentence[index + len(marker) :].strip()
        if (
            1 < len(subject) <= 80
            and obj
            and subject[0].isupper()
            and all(char.isalnum() or char in "ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüý .,'-" for char in subject)
        ):
            return subject, predicate.replace(" ", "_"), obj
    return None


def _extract_triples(content: str) -> list[tuple[str, str, str]]:
    """Heuristic OpenIE-style extraction from Markdown.

    Pulls (subject, predicate, object) triples from headings, wiki-links,
    bold references, link targets and simple `A is B` sentence patterns. No
    LLM dep — set HIPPORAG_LLM_URL for richer triples.
    """
    triples: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def _add(s: str, p: str, o: str) -> None:
        s, p, o = s.strip(), p.strip(), o.strip()
        # ponytail: strip trailing sentence punctuation so object 'ice.' and subject
        # 'Ice' normalize to the same graph node — BFS adjacency depends on this
        s = s.rstrip(".,;:!?") if len(s) > 1 else s
        o = o.rstrip(".,;:!?") if len(o) > 1 else o
        if not s or not o or len(s) > 200 or len(o) > 200:
            return
        key = (s.lower(), p.lower(), o.lower())
        if key in seen:
            return
        seen.add(key)
        triples.append((s, p, o))

    current_heading = ""
    for line in content.splitlines():
        line = line.rstrip()
        stripped = line.lstrip()
        if stripped.startswith("#"):
            heading_marks = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped[heading_marks:].strip()
            if 1 <= heading_marks <= 6 and heading_text:
            # ponytail: strip wiki-link/bold/markup so the heading label is clean
                current_heading = _strip_inline_markup(heading_text)
            # ponytail: keep processing the heading line — wikilinks/bold often
            # appear inline with the heading (e.g. "# A links [[B]]"). Falling
            # through instead of `continue` lets the same-line extractors run.
        # [[wiki]] links -> (heading, links_to, target)
        for target in _wiki_targets(line):
            if current_heading:
                _add(current_heading, "links_to", target)
        # [text](url) -> (text, references, url)
        for text, url in _markdown_links(line):
            _add(text.strip(), "references", url.strip())
        # **bold** as entities -> (heading, mentions, bold)
        for bold in _bold_entities(line):
            if current_heading:
                _add(current_heading, "mentions", bold.strip())
        # sentence-level "X is/are Y", "X uses Y", "X relates_to Y"
        clean = _strip_inline_markup(line)
        if not clean:
            continue
        for sentence in _sentences(clean):
            relation = _parse_sentence_relation(sentence)
            if relation:
                _add(*relation)
            if current_heading and len(sentence) > 8:
                # ponytail: naive (heading, mentions, sentence) captures adjacency seed
                _add(current_heading, "mentions", sentence[:120])

    return triples


def _maybe_llm_triples(content: str) -> list[tuple[str, str, str]]:
    """Optional: extract richer triples via Ollama-compatible endpoint.

    Honors ADR 002 point 4 (route LLM through available endpoint). Falls back
    to heuristic extraction on any error so the sidecar stays usable offline.
    """
    if not LLM_URL:
        return _extract_triples(content)
    try:
        prompt = (
            "Extract knowledge triples (subject, predicate, object) from the note "
            'below as JSON: [{"s":"","p":"","o":""}]. Predicates must be '
            "snake_case. No commentary.\n\n" + content[:4000]
        )
        r = httpx.post(
            LLM_URL,
            json={"model": "hipporag", "prompt": prompt, "stream": False},
            timeout=20,
        )
        r.raise_for_status()
        raw = ""
        data = r.json()
        if isinstance(data, dict):
            raw = data.get("response") or data.get("output") or ""
        triples: list[tuple[str, str, str]] = []
        # tolerate free-form JSON inside the model response
        match = re.search(r"\[.*?\]", raw, re.DOTALL)
        if match:
            for item in json.loads(match.group(0)):
                s, p, o = item.get("s"), item.get("p"), item.get("o")
                if s and p and o:
                    triples.append((str(s), str(p), str(o)))
        if triples:
            return triples
        return _extract_triples(content)
    except Exception:
        # ponytail: LLM unreachable -> degrade to heuristic, never fail indexing
        return _extract_triples(content)


def _verify_token(authorization: str | None) -> None:
    if not SERVICE_TOKEN:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing service token")
    if authorization.removeprefix("Bearer ").strip() != SERVICE_TOKEN:
        raise HTTPException(status_code=403, detail="invalid service token")


def _index(conn: sqlite3.Connection, vault_id: str, doc_id: str, content: str) -> int:
    # Replace existing doc + triples (idempotent index)
    conn.execute(
        "DELETE FROM triples WHERE vault_id=? AND doc_id=?",
        (vault_id, doc_id),
    )
    conn.execute(
        "INSERT OR REPLACE INTO docs(vault_id, doc_id, content, created_at) "
        "VALUES (?, ?, ?, ?)",
        (vault_id, doc_id, content, time.time()),
    )
    triples = _maybe_llm_triples(content)
    conn.executemany(
        "INSERT INTO triples(vault_id, doc_id, subject, predicate, object) "
        "VALUES (?, ?, ?, ?, ?)",
        [(vault_id, doc_id, s, p, o) for (s, p, o) in triples],
    )
    return len(triples)


def _adjacency(conn: sqlite3.Connection, vault_id: str) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for row in conn.execute(
        "SELECT subject, object FROM triples WHERE vault_id=?", (vault_id,)
    ):
        adj[row["subject"]].add(row["object"])
        adj[row["object"]].add(row["subject"])
    return adj


def _bfs_multihop(
    adj: dict[str, set[str]], seeds: Iterable[str], max_hops: int
) -> list[tuple[str, int]]:
    """BFS over adjacency, returns (node, depth) pairs within max_hops."""
    visited: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for seed in seeds:
        if seed and seed not in visited:
            visited[seed] = 0
            queue.append((seed, 0))
    while queue:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue
        for neighbor in adj.get(node, ()):
            if neighbor not in visited:
                visited[neighbor] = depth + 1
                queue.append((neighbor, depth + 1))
    return sorted(visited.items(), key=lambda kv: kv[1])


@app.get("/health")
def health():
    # ponytail: liveness probe only; readiness is implied by successful ops
    return {"status": "ok", "service": "hipporag-sidecar", "llm": bool(LLM_URL)}


@app.post("/index")
def index_document(req: IndexRequest, authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    with _db() as conn:
        n = _index(conn, req.vault_id, req.doc_id, req.content)
    return {"status": "indexed", "doc_id": req.doc_id, "triples": n}


@app.delete("/index/{vault_id}/{doc_id}")
def delete_document(
    vault_id: str, doc_id: str, authorization: str | None = Header(default=None)
):
    _verify_token(authorization)
    with _db() as conn:
        conn.execute(
            "DELETE FROM triples WHERE vault_id=? AND doc_id=?",
            (vault_id, doc_id),
        )
        cur = conn.execute(
            "DELETE FROM docs WHERE vault_id=? AND doc_id=?", (vault_id, doc_id)
        )
        removed = cur.rowcount
    return {"status": "deleted", "doc_id": doc_id, "removed": removed}


@app.post("/retrieve")
def retrieve(req: RetrieveRequest, authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    query_tokens = _tokens(req.query)
    if not query_tokens:
        return {"results": [], "query_tokens": 0}
    with _db() as conn:
        adj = _adjacency(conn, req.vault_id)
        # seed: nodes whose name shares tokens with the query
        seeds = [node for node in adj if _token_score(query_tokens, _tokens(node)) > 0]
        if not seeds:
            return {"results": [], "query_tokens": len(query_tokens)}
        hops = _bfs_multihop(adj, seeds, max_hops=max(1, min(req.max_hops, 3)))
        depth_by_node = dict(hops)

        # pull triples touching any visited node
        visited_nodes = set(depth_by_node)
        rows = list(
            conn.execute(
                "SELECT subject, predicate, object, doc_id FROM triples "
                "WHERE vault_id=? AND (subject IN (%s) OR object IN (%s))"
                % (
                    ",".join("?" * len(visited_nodes)),
                    ",".join("?" * len(visited_nodes)),
                ),
                [req.vault_id, *visited_nodes, *visited_nodes],
            )
        )

        # score: seed-token match + inverse path depth
        results: list[dict[str, Any]] = []
        for row in rows:
            subj, pred, obj, doc_id = (
                row["subject"],
                row["predicate"],
                row["object"],
                row["doc_id"],
            )
            subj_score = _token_score(query_tokens, _tokens(subj))
            obj_score = _token_score(query_tokens, _tokens(obj))
            seed_hit = subj_score > 0 or obj_score > 0
            depth = min(
                depth_by_node.get(subj, req.max_hops + 1),
                depth_by_node.get(obj, req.max_hops + 1),
            )
            proximity = 1.0 / (1.0 + depth)
            score = round(
                (subj_score + obj_score) * 0.6 + proximity * 0.4,
                4,
            )
            if not seed_hit and depth > req.max_hops:
                continue
            if score <= 0 and not seed_hit:
                continue
            text = f"{subj} — {pred} — {obj}"
            results.append(
                {
                    "source": "hipporag",
                    "title": subj,
                    "text": text,
                    "score": score,
                    "metadata": {
                        "subject": subj,
                        "predicate": pred,
                        "object": obj,
                        "docId": doc_id,
                        "depth": depth,
                        "seedHit": seed_hit,
                    },
                }
            )
        results.sort(key=lambda r: r["score"], reverse=True)
    return {"results": results[: req.top_k], "query_tokens": len(query_tokens)}


@app.post("/reconcile")
def reconcile(authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    # ponytail: SQLite is the source of truth, adjacency is recomputed on each
    # query. Reconcile is a no-op that confirms the DB is alive.
    with _db() as conn:
        conn.execute("SELECT 1 FROM docs LIMIT 1")
    return {"status": "reconciled", "db": str(DB_PATH)}


@app.post("/rebuild")
def rebuild(authorization: str | None = Header(default=None)):
    _verify_token(authorization)
    # Drop triples + docs and re-extract from stored docs (kept in `docs` table)
    with _db() as conn:
        conn.execute("DELETE FROM triples")
        rows = list(conn.execute("SELECT vault_id, doc_id, content FROM docs"))
        total = 0
        for row in rows:
            total += _index(conn, row["vault_id"], row["doc_id"], row["content"])
    return {"status": "rebuilt", "triples": total, "docs": len(rows)}


def _token_score(query_tokens: set[str], body_tokens: set[str]) -> float:
    if not query_tokens or not body_tokens:
        return 0.0
    overlap = len(query_tokens & body_tokens)
    if overlap == 0:
        return 0.0
    return overlap / math.sqrt(len(query_tokens) * len(body_tokens))


def _demo() -> None:
    """Self-check: index→retrieve→delete→rebuild roundtrip. Run with `python main.py`."""
    import tempfile

    global DATA_DIR, DB_PATH
    tmp = Path(tempfile.mkdtemp(prefix="hipporag_test_"))
    DATA_DIR = tmp
    DB_PATH = tmp / "hipporag.db"

    from fastapi.testclient import TestClient

    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"

    content = (
        "# Distributed Systems\n"
        "An [[observability]] stack helps debug latency.\n"
        "**OpenTelemetry** collects traces.\n"
        "OpenTelemetry connects to Jaeger.\n"
        "Jaeger stores traces.\n"
    )
    r = client.post(
        "/index",
        json={"vault_id": "v1", "doc_id": "note1", "content": content},
    )
    assert r.status_code == 200, r.text
    assert r.json()["triples"] > 0, "extraction produced no triples"

    r = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "observability traces", "top_k": 5},
    )
    results = r.json()["results"]
    assert results, "retrieve returned empty for matching query"
    assert any(
        "OpenTelemetry" in res["title"] or "OpenTelemetry" in res["text"]
        for res in results
    ), results

    r = client.delete("/index/v1/note1")
    assert r.json()["removed"] == 1, r.text

    r = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "observability traces"},
    )
    assert r.json()["results"] == [], "delete did not take effect"

    # re-index then rebuild
    client.post(
        "/index", json={"vault_id": "v1", "doc_id": "note1", "content": content}
    )
    r = client.post("/rebuild")
    assert r.json()["status"] == "rebuilt"

    print(f"OK: sidecar self-check passed (db={tmp})")


if __name__ == "__main__":
    _demo()
