"""Post-hoc, checkpointed cross-encoder controls for the MuSiQue test split.

The nonstructural source union is scored once. Scores also rerank the Hybrid-RRF
top-10 subset, keeping the model, query, text, tokenizer and batching fixed.
This analysis was requested after the original test results were inspected;
it is exploratory rather than a new confirmatory test.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path("/mnt/HDD_1/Antigravity/berrybrain")
sys.path.insert(0, str(REPO / "apps/api/benchmarks"))

from comparative_retrieval_benchmark import (  # noqa: E402
    evaluate_rankings,
    internal_latencies,
    paired_comparisons,
)
from comparative_split_manifest import validate_manifest  # noqa: E402
from same_corpus_rag_benchmark import load_musique, sha256_file  # noqa: E402
from semantic_rerank_benchmark import (  # noqa: E402
    OnnxCrossEncoder,
    atomic_write,
    candidate_pool,
    rank_from_scores,
)

BASE = REPO / "reports/evaluation/same-corpus-rag-rrf-development-current.json"
ORIGINAL = REPO / "reports/evaluation/semantic-rerank-unreserved-onnx-int8-confirmatory.json"
CORPUS = ROOT / "artifact/inputs/musique_corpus.json"
QUERIES = ROOT / "artifact/inputs/musique.json"
SPLIT = REPO / "reports/evaluation/comparative-split-v1.json"
ONNX = REPO / ".benchmark-cache/onnx-crossencoder/model.int8.onnx"
TOKENIZER = REPO / ".benchmark-cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a"
CHECKPOINT = ROOT / "matched-rerank-control.checkpoint.json"
OUTPUT = ROOT / "matched-rerank-control.json"


def main() -> None:
    source = json.loads(BASE.read_text(encoding="utf-8"))
    original = json.loads(ORIGINAL.read_text(encoding="utf-8"))
    documents, all_queries = load_musique(CORPUS, QUERIES)
    split_data = json.loads(SPLIT.read_text(encoding="utf-8"))
    splits = validate_manifest(split_data, corpus=CORPUS, queries=QUERIES)
    query_by_id = {query.id: query for query in all_queries}
    queries = [query_by_id[query_id] for query_id in splits["confirmatory"]]
    document_by_id = {document.id: document for document in documents}
    source_rankings = source["retrieval"]["rankings"]
    fingerprint = {
        "scriptSha256": sha256_file(Path(__file__)),
        "baseSha256": sha256_file(BASE),
        "originalSha256": sha256_file(ORIGINAL),
        "corpusSha256": sha256_file(CORPUS),
        "queriesSha256": sha256_file(QUERIES),
        "splitSha256": sha256_file(SPLIT),
        "onnxSha256": sha256_file(ONNX),
        "tokenizerRevision": TOKENIZER.name,
        "maxLength": 512,
        "inferenceBatchSize": 8,
        "queryBatchSize": 8,
        "intraOpThreads": 2,
    }
    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if checkpoint["fingerprint"] != fingerprint:
            raise ValueError("Checkpoint fingerprint differs from the active protocol")
    else:
        checkpoint = {"fingerprint": fingerprint, "rows": {}}
    rows = checkpoint["rows"]
    pending = [query for query in queries if query.id not in rows]
    if pending:
        model = OnnxCrossEncoder(
            model_path=ONNX,
            tokenizer_name=str(TOKENIZER),
            revision=None,
            max_length=512,
            intra_op_threads=2,
        )
        for offset in range(0, len(pending), 8):
            batch = pending[offset : offset + 8]
            pools = [
                candidate_pool(source_rankings, query.id, ("bm25", "dense", "hybrid"))
                for query in batch
            ]
            pairs = [
                (query.question, f"{document_by_id[item].title}\n{document_by_id[item].text}")
                for query, pool in zip(batch, pools, strict=True)
                for item in pool
            ]
            started = time.perf_counter()
            scores = model.predict(pairs, batch_size=8)
            elapsed_ms = (time.perf_counter() - started) * 1000
            cursor = 0
            for query, pool in zip(batch, pools, strict=True):
                pool_scores = scores[cursor : cursor + len(pool)]
                cursor += len(pool)
                hybrid_ids = source_rankings["hybrid"][query.id]
                if not set(hybrid_ids).issubset(pool):
                    raise ValueError(f"Hybrid top-10 is outside lexical+dense pool: {query.id}")
                rows[query.id] = {
                    "pool": pool,
                    "scores": pool_scores,
                    "modelPredictMs": elapsed_ms * len(pool) / len(pairs),
                }
            atomic_write(CHECKPOINT, checkpoint)
            print(f"scored {len(rows)}/{len(queries)} questions", flush=True)

    rankings = {"hybrid_rrf": {}, "hybrid_top10_ce": {}, "nonstructural_ce": {}, "berrybrain_rerank": {}}
    latency = {}
    for query in queries:
        row = rows[query.id]
        scores = dict(zip(row["pool"], row["scores"], strict=True))
        hybrid_ids = source_rankings["hybrid"][query.id]
        rankings["hybrid_rrf"][query.id] = hybrid_ids
        rankings["hybrid_top10_ce"][query.id] = rank_from_scores(
            hybrid_ids, [scores[item] for item in hybrid_ids], 10
        )
        rankings["nonstructural_ce"][query.id] = rank_from_scores(
            row["pool"], row["scores"], 10
        )
        rankings["berrybrain_rerank"][query.id] = original["rankings"][query.id]
        latency[query.id] = float(row["modelPredictMs"])
    observations = {}
    summaries = {}
    original_latency = {
        str(row["queryId"]): float(row["latencyMs"])
        for row in original["observations"]["semantic_rerank"]
    }
    for method, method_rankings in rankings.items():
        method_latency = (
            internal_latencies(source, "hybrid")
            if method == "hybrid_rrf"
            else original_latency if method == "berrybrain_rerank" else latency
        )
        observations[method], summaries[method] = evaluate_rankings(
            method_rankings, queries, method_latency
        )
    comparisons = {
        "hybrid_top10_ce_minus_hybrid_rrf": paired_comparisons(
            {key: observations[key] for key in ("hybrid_rrf", "hybrid_top10_ce")},
            candidate_method="hybrid_top10_ce", seed=20261023, resamples=10000
        )["hybrid_rrf"],
        "nonstructural_ce_minus_hybrid_rrf": paired_comparisons(
            {key: observations[key] for key in ("hybrid_rrf", "nonstructural_ce")},
            candidate_method="nonstructural_ce", seed=20261023, resamples=10000
        )["hybrid_rrf"],
        "berrybrain_rerank_minus_nonstructural_ce": paired_comparisons(
            {key: observations[key] for key in ("nonstructural_ce", "berrybrain_rerank")},
            candidate_method="berrybrain_rerank", seed=20261023, resamples=10000
        )["nonstructural_ce"],
    }
    result = {
        "classification": "post-hoc exploratory control on previously observed test split",
        "fingerprint": fingerprint,
        "queries": len(queries),
        "pool": {
            "routes": ["bm25", "dense", "hybrid"],
            "routeDepth": 10,
            "mean": statistics.fmean(len(row["pool"]) for row in rows.values()),
            "median": statistics.median(len(row["pool"]) for row in rows.values()),
            "minimum": min(len(row["pool"]) for row in rows.values()),
            "maximum": max(len(row["pool"]) for row in rows.values()),
        },
        "summaries": summaries,
        "comparisons": comparisons,
        "rankings": rankings,
        "limitations": [
            "Post-hoc analysis on a split whose results were already observed.",
            "BM25+dense+Hybrid top-10 union is not a deeper Hybrid-RRF ranking.",
            "Hybrid top-10 reranking cannot alter Recall@10 because membership is fixed.",
            "Model-prediction timings exclude source retrieval and pool assembly.",
        ],
    }
    atomic_write(OUTPUT, result)
    print(json.dumps({"status": "completed", "summaries": summaries}), flush=True)


if __name__ == "__main__":
    main()
