import json
import tempfile
import unittest
from pathlib import Path

from benchmarks.external_retrieval_baseline import run_external_baseline


class ExternalRetrievalBaselineTest(unittest.TestCase):
    def _write(self, path: Path, rows: list[dict]) -> None:
        path.write_text(
            "".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8"
        )

    def test_executes_bm25_dense_and_hybrid_against_qrels(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus.jsonl"
            queries = root / "queries.jsonl"
            qrels = root / "qrels.jsonl"
            self._write(
                corpus,
                [
                    {
                        "id": "d1",
                        "text": "time series forecast",
                        "embedding": [1.0, 0.0],
                    },
                    {"id": "d2", "text": "graph ontology", "embedding": [0.0, 1.0]},
                ],
            )
            self._write(
                queries,
                [{"id": "q1", "text": "time series", "embedding": [1.0, 0.0]}],
            )
            self._write(
                qrels,
                [{"query_id": "q1", "document_id": "d1", "relevance": 2}],
            )
            for method in ("bm25", "dense", "hybrid"):
                metrics, observations = run_external_baseline(
                    corpus, queries, qrels, method=method
                )
                self.assertEqual(metrics.recall_at_10, 1.0)
                self.assertEqual(metrics.mean_reciprocal_rank, 1.0)
                self.assertEqual(len(observations), 1)

    def test_dense_requires_real_embeddings(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus.jsonl"
            queries = root / "queries.jsonl"
            qrels = root / "qrels.jsonl"
            self._write(corpus, [{"id": "d1", "text": "evidence"}])
            self._write(queries, [{"id": "q1", "text": "evidence"}])
            self._write(
                qrels, [{"query_id": "q1", "document_id": "d1", "relevance": 1}]
            )
            with self.assertRaises(ValueError):
                run_external_baseline(corpus, queries, qrels, method="dense")


if __name__ == "__main__":
    unittest.main()
