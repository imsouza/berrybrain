"""Sidecar functional self-checks.

Run from apps/hipporag/:
    python -m tests.test_sidecar
or use pytest. The tests use FAST API TestClient and point the DB to a
tempdir, so no Docker or external services are required.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

try:
    import pytest

    _HAS_PYTEST = True
except ImportError:
    _HAS_PYTEST = False


def _client(tmp_path: Path, monkeypatch=None):
    import importlib

    import main

    if monkeypatch is not None:
        monkeypatch.setenv("HIPPORAG_DATA_DIR", str(tmp_path))
        monkeypatch.setattr(main, "DATA_DIR", tmp_path)
        monkeypatch.setattr(main, "DB_PATH", tmp_path / "hipporag.db")
        monkeypatch.setattr(main, "LLM_URL", "")
    else:
        import os

        os.environ["HIPPORAG_DATA_DIR"] = str(tmp_path)
        main.DATA_DIR = tmp_path
        main.DB_PATH = tmp_path / "hipporag.db"
        main.LLM_URL = ""
    importlib.reload(main)
    return TestClient(main.app)


if _HAS_PYTEST:

    @pytest.fixture()
    def client(tmp_path: Path, monkeypatch):
        return _client(tmp_path, monkeypatch)


SAMPLE_NOTE = (
    "# Distributed Systems\n"
    "An [[observability]] stack helps debug latency.\n"
    "**OpenTelemetry** collects traces.\n"
    "OpenTelemetry connects to Jaeger.\n"
    "Jaeger stores traces.\n"
)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["llm"] is False


def test_index_then_retrieve(client):
    r = client.post(
        "/index",
        json={"vault_id": "v1", "doc_id": "note1", "content": SAMPLE_NOTE},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "indexed"
    assert body["triples"] > 0, "extractor produced no triples"

    r = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "observability traces Jaeger", "top_k": 10},
    )
    assert r.status_code == 200
    results = r.json()["results"]
    assert results, "retrieve returned no evidence for matching query"
    assert any(
        "OpenTelemetry" in res["title"] or "Jaeger" in res["title"] for res in results
    )
    assert all(res["score"] > 0 for res in results)


def test_retrieve_empty_when_no_match(client):
    r = client.post(
        "/index",
        json={"vault_id": "v1", "doc_id": "note1", "content": SAMPLE_NOTE},
    )
    r = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "zzz_nonexistent_topic"},
    )
    assert r.json()["results"] == []


def test_idempotent_index(client):
    """Re-indexing the same doc replaces old triples (idempotent)."""
    client.post(
        "/index",
        json={"vault_id": "v1", "doc_id": "n1", "content": "# Alpha links [[Beta]]"},
    )
    first = client.post(
        "/index",
        json={"vault_id": "v1", "doc_id": "n1", "content": "# Gamma links [[Delta]]"},
    )
    assert first.json()["status"] == "indexed"
    r = client.post("/retrieve", json={"vault_id": "v1", "query": "Delta"})
    assert r.json()["results"], "replaced index dropped valid triples"
    r = client.post("/retrieve", json={"vault_id": "v1", "query": "Beta"})
    assert r.json()["results"] == [], "old triples not replaced by idempotent index"


def test_delete_and_rebuild(client):
    client.post(
        "/index", json={"vault_id": "v1", "doc_id": "n1", "content": SAMPLE_NOTE}
    )
    r = client.delete("/index/v1/n1")
    assert r.status_code == 200
    assert r.json()["removed"] == 1

    r = client.post("/retrieve", json={"vault_id": "v1", "query": "Jaeger"})
    assert r.json()["results"] == []

    # rebuild re-injects from stored docs (none left after delete)
    r = client.post("/rebuild")
    assert r.json()["status"] == "rebuilt"
    assert r.json()["docs"] == 0


def test_explicit_ontology_triples_survive_rebuild(client):
    payload = {
        "vault_id": "v1",
        "doc_id": "ontology-note",
        "content": "# Forecasting",
        "triples": [
            {
                "subject": "Stationarity",
                "predicate": "bb:prerequisiteFor",
                "object": "Time series forecasting",
            }
        ],
    }
    indexed = client.post("/index", json=payload)
    assert indexed.status_code == 200
    result = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "Stationarity time series"},
    )
    assert any(
        item["metadata"].get("predicate") == "bb:prerequisiteFor"
        for item in result.json()["results"]
    )
    assert client.post("/rebuild").status_code == 200
    rebuilt = client.post(
        "/retrieve",
        json={"vault_id": "v1", "query": "Stationarity time series"},
    )
    assert any(
        item["metadata"].get("predicate") == "bb:prerequisiteFor"
        for item in rebuilt.json()["results"]
    )


def test_reconcile(client):
    r = client.post("/reconcile")
    assert r.status_code == 200
    assert r.json()["status"] == "reconciled"


def test_multihop_finds_neighbors_through_bfs(client):
    """Multi-hop retrieval reaches a node that has no query-token overlap
    but is reachable in 1-2 hops from a seed node."""
    content = (
        "# Kun polar explorers\n"
        "[[Amundsen]] reached [[South Pole]] first.\n"
        "South Pole contains ice.\n"
        "Ice reflects sunlight.\n"
        "Sunlight powers snowfields.\n"
    )
    client.post(
        "/index", json={"vault_id": "v1", "doc_id": "poles", "content": content}
    )
    # query mentions 'Amundsen' (seed); multi-hop should reach 'snowfields'
    r = client.post(
        "/retrieve",
        json={
            "vault_id": "v1",
            "query": "Amundsen",
            "top_k": 50,
            "max_hops": 3,
        },
    )
    all_text = " ".join(res["text"] for res in r.json()["results"])
    assert "Sunlight" in all_text, all_text


if __name__ == "__main__":
    # direct runner: pyfile-style invocation, no pytest fixture
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main = __import__("main")

    def _fresh_client():
        tmp = Path(tempfile.mkdtemp(prefix="hipporag_test_"))
        main.DATA_DIR = tmp
        main.DB_PATH = tmp / "hipporag.db"
        main.LLM_URL = ""
        # ponytail: per-test tempdir keeps tests isolated in the direct runner
        return TestClient(main.app), tmp

    c, _tmp = _fresh_client()
    test_health(c)
    c, tmp = _fresh_client()
    test_index_then_retrieve(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_retrieve_empty_when_no_match(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_idempotent_index(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_delete_and_rebuild(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_explicit_ontology_triples_survive_rebuild(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_reconcile(c)
    shutil.rmtree(tmp, ignore_errors=True)
    c, tmp = _fresh_client()
    test_multihop_finds_neighbors_through_bfs(c)
    shutil.rmtree(tmp, ignore_errors=True)
    print("OK: all sidecar tests passed")
