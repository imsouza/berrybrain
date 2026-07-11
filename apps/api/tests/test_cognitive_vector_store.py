import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from berrybrain_api.cognitive_layer import index_knowledge_base, retrieve_kb
from berrybrain_api.database import Base
from berrybrain_api.models import NoteRecord, SettingRecord


class FakeResponse:
    def __init__(self, status: int = 200, body: dict | None = None):
        self.status = status
        self._body = json.dumps(body or {}).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return self._body


class CognitiveVectorStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite:///:memory:", connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(bind=engine)
        self.session = sessionmaker(bind=engine)()
        self.session.add(
            NoteRecord(
                title="Docker Essentials",
                slug="docker-essentials",
                path="inbox/docker.md",
                content="# Docker\n\nContainers isolate applications and images.",
                content_hash="abc",
            )
        )
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def set_setting(self, key: str, value: str) -> None:
        self.session.add(SettingRecord(key=key, value=value))
        self.session.commit()

    def test_sqlite_fallback_indexes_chunks_without_external_call(self) -> None:
        result = index_knowledge_base(self.session)

        self.assertEqual(result["store"], "sqlite")
        self.assertEqual(result["chunks"], 1)
        self.assertEqual(result["externalVectorStore"]["status"], "skipped")
        self.assertEqual(result["externalVectorStore"]["store"], "sqlite")

    def test_qdrant_upserts_real_http_payload(self) -> None:
        self.set_setting("kb_vector_store", "qdrant")
        self.set_setting("qdrant_url", "http://qdrant.local")
        calls: list[tuple[str, str, dict]] = []

        def fake_urlopen(request, timeout=0):
            calls.append(
                (
                    request.get_method(),
                    request.full_url,
                    json.loads(request.data.decode("utf-8")),
                )
            )
            return FakeResponse()

        with patch("urllib.request.urlopen", fake_urlopen):
            result = index_knowledge_base(self.session)

        self.assertEqual(result["externalVectorStore"]["status"], "synced")
        self.assertEqual(result["externalVectorStore"]["store"], "qdrant")
        self.assertEqual(calls[0][0], "PUT")
        self.assertTrue(calls[0][1].endswith("/collections/berrybrain"))
        self.assertTrue(calls[1][1].endswith("/collections/berrybrain/points"))
        self.assertEqual(len(calls[1][2]["points"]), 1)
        self.assertEqual(len(calls[1][2]["points"][0]["vector"]), 64)

    def test_qdrant_retrieval_uses_vector_search_payload(self) -> None:
        self.set_setting("kb_vector_store", "qdrant")
        self.set_setting("qdrant_url", "http://qdrant.local")
        calls: list[tuple[str, str, dict]] = []

        def fake_urlopen(request, timeout=0):
            payload = json.loads(request.data.decode("utf-8"))
            calls.append((request.get_method(), request.full_url, payload))
            return FakeResponse(
                body={
                    "result": [
                        {
                            "score": 0.93,
                            "payload": {
                                "title": "Docker Essentials",
                                "path": "inbox/docker.md",
                                "text": "Containers isolate applications and images.",
                                "note_id": 1,
                                "chunk": 0,
                                "document_id": "note:1:chunk:0",
                            },
                        }
                    ]
                }
            )

        with patch("urllib.request.urlopen", fake_urlopen):
            results = retrieve_kb(self.session, "containers", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Docker Essentials")
        self.assertEqual(results[0].metadata["retrieval"], "qdrant_vector")
        self.assertEqual(calls[0][0], "POST")
        self.assertTrue(calls[0][1].endswith("/collections/berrybrain/points/search"))
        self.assertEqual(len(calls[0][2]["vector"]), 64)
        self.assertEqual(calls[0][2]["limit"], 3)

    def test_chroma_retrieval_uses_query_endpoint(self) -> None:
        self.set_setting("kb_vector_store", "chroma")
        self.set_setting("chroma_url", "http://chroma.local")
        calls: list[tuple[str, str, dict]] = []

        def fake_urlopen(request, timeout=0):
            payload = json.loads(request.data.decode("utf-8"))
            calls.append((request.get_method(), request.full_url, payload))
            if request.full_url.endswith("/api/v1/collections"):
                return FakeResponse(body={"id": "collection-id"})
            return FakeResponse(
                body={
                    "documents": [["Containers isolate applications and images."]],
                    "metadatas": [[{"title": "Docker Essentials", "path": "inbox/docker.md", "chunk": 0}]],
                    "distances": [[0.25]],
                }
            )

        with patch("urllib.request.urlopen", fake_urlopen):
            results = retrieve_kb(self.session, "containers", limit=2)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["retrieval"], "chroma_vector")
        self.assertTrue(calls[1][1].endswith("/api/v1/collections/collection-id/query"))
        self.assertEqual(len(calls[1][2]["query_embeddings"][0]), 64)
        self.assertEqual(calls[1][2]["n_results"], 2)

    def test_external_retrieval_failure_falls_back_to_local_notes(self) -> None:
        self.set_setting("kb_vector_store", "qdrant")
        self.set_setting("qdrant_url", "http://qdrant.local")

        def fake_urlopen(request, timeout=0):
            raise RuntimeError("qdrant unavailable")

        with patch("urllib.request.urlopen", fake_urlopen):
            results = retrieve_kb(self.session, "containers", limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].metadata["retrieval"], "lexical_plus_metadata")


if __name__ == "__main__":
    unittest.main()
