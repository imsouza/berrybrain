"""Post-hoc matched CE comparison with verified reuse of identical pair scores.

Historical scores are reused only for identical query/document text, model,
tokenizer and inference settings. Missing pairs are scored locally on the Pi.
The result is a retrieval-quality comparison, not a full-latency measurement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import time
from pathlib import Path

from comparative_retrieval_benchmark import evaluate_rankings, paired_comparisons
from comparative_split_manifest import validate_manifest
from same_corpus_rag_benchmark import load_musique, sha256_file
from semantic_rerank_benchmark import (
    OnnxCrossEncoder,
    atomic_write,
    candidate_pool,
    rank_from_scores,
)


FOUR_ROUTES = ("bm25", "dense", "hybrid", "openie_graphrag")
MODEL_THREADS = 2
BATCH_SIZE = 8
MAX_LENGTH = 512
TOLERANCE = 1e-5


def clean_summary(summary: dict) -> dict:
    return {k: v for k, v in summary.items() if not k.startswith("latency")}


def clean_observations(rows: list[dict]) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "latencyMs"} for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-ten", type=Path, required=True)
    parser.add_argument("--source-forty", type=Path, required=True)
    parser.add_argument("--historical-scores", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--onnx-model", type=Path, required=True)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()

    ten = json.loads(args.source_ten.read_text())
    forty = json.loads(args.source_forty.read_text())
    old = json.loads(args.historical_scores.read_text())
    documents, all_queries = load_musique(args.corpus, args.queries)
    splits = validate_manifest(
        json.loads(args.split_manifest.read_text()), corpus=args.corpus, queries=args.queries
    )
    query_by_id = {q.id: q for q in all_queries}
    queries = [query_by_id[qid] for qid in splits["confirmatory"]]
    assert len(queries) == 600
    document_by_id = {doc.id: doc for doc in documents}
    ten_rankings = ten["retrieval"]["rankings"]
    forty_rankings = forty["retrieval"]["rankings"]

    expected = {
        "sourceTenSha256": sha256_file(args.source_ten),
        "sourceFortySha256": sha256_file(args.source_forty),
        "historicalScoresSha256": sha256_file(args.historical_scores),
        "corpusSha256": sha256_file(args.corpus),
        "queriesSha256": sha256_file(args.queries),
        "splitSha256": sha256_file(args.split_manifest),
        "onnxSha256": sha256_file(args.onnx_model),
        "tokenizerRevision": args.tokenizer.name,
        "maxLength": MAX_LENGTH,
        "batchSize": BATCH_SIZE,
        "threads": MODEL_THREADS,
    }
    old_fingerprint = old["fingerprint"]
    for field in ("corpusSha256", "queriesSha256", "splitSha256", "onnxSha256", "tokenizerRevision", "maxLength", "inferenceBatchSize", "queryBatchSize", "intraOpThreads"):
        old_field = "batchSize" if field in {"inferenceBatchSize", "queryBatchSize"} else "threads" if field == "intraOpThreads" else field
        if old_fingerprint[field] != expected[old_field]:
            raise ValueError(f"Historical score cache {field} mismatch")
    if ten["git"]["dirty"] or forty["git"]["dirty"]:
        raise ValueError("Source rankings were not produced from clean commits")
    if ten["inputs"] != forty["inputs"]:
        raise ValueError("Source reports use different inputs")
    if len(old["rows"]) != len(queries):
        raise ValueError("Historical cache query coverage differs")

    pools = {}
    validation_candidates = []
    for query in queries:
        four_pool = candidate_pool(ten_rankings, query.id, FOUR_ROUTES)
        hybrid_pool = candidate_pool(forty_rankings, query.id, ("hybrid",))
        if len(hybrid_pool) != 40:
            raise ValueError(f"Expected 40 Hybrid candidates for {query.id}")
        merged = list(dict.fromkeys([*four_pool, *hybrid_pool]))
        old_row = old["rows"][query.id]
        old_scores = dict(zip(old_row["pool"], old_row["scores"], strict=True))
        pools[query.id] = (four_pool, hybrid_pool, merged, old_scores)
        validation_candidates.extend(
            (query.id, document_id)
            for document_id in merged
            if document_id in old_scores
        )

    validation_candidates.sort(
        key=lambda pair: hashlib.sha256(f"{pair[0]}\0{pair[1]}".encode()).hexdigest()
    )
    validation = validation_candidates[:32]
    if len(validation) != 32:
        raise ValueError("Too few reusable pairs for validation")
    model = OnnxCrossEncoder(
        model_path=args.onnx_model,
        tokenizer_name=str(args.tokenizer),
        revision=None,
        max_length=MAX_LENGTH,
        intra_op_threads=MODEL_THREADS,
    )

    def model_pairs(pairs: list[tuple[str, str]]) -> list[float]:
        return [
            float(value)
            for value in model.predict(pairs, batch_size=BATCH_SIZE, show_progress_bar=False)
        ]

    validation_text = [
        (
            query_by_id[qid].question,
            f"{document_by_id[document_id].title}\n{document_by_id[document_id].text}",
        )
        for qid, document_id in validation
    ]
    new_validation_scores = model_pairs(validation_text)
    validation_differences = [
        abs(score - pools[qid][3][document_id])
        for (qid, document_id), score in zip(validation, new_validation_scores, strict=True)
    ]
    max_validation_difference = max(validation_differences)
    if max_validation_difference > TOLERANCE:
        raise ValueError(
            f"Cached CE score validation failed: max difference {max_validation_difference}"
        )
    if args.validate_only:
        print(json.dumps({
            "status": "validated",
            "sampleCount": len(validation),
            "maxAbsoluteDifference": max_validation_difference,
            "tolerance": TOLERANCE,
        }))
        return

    if args.checkpoint.exists():
        checkpoint = json.loads(args.checkpoint.read_text())
        if checkpoint["fingerprint"] != expected:
            raise ValueError("Checkpoint fingerprint mismatch")
    else:
        checkpoint = {"fingerprint": expected, "rows": {}}
    checkpoint["validation"] = {
        "sampleCount": len(validation),
        "selection": "ascending SHA-256(query ID, NUL, document ID)",
        "maxAbsoluteDifference": max_validation_difference,
        "tolerance": TOLERANCE,
        "pairs": [
            {"queryId": qid, "documentId": document_id, "absoluteDifference": delta}
            for (qid, document_id), delta in zip(validation, validation_differences, strict=True)
        ],
    }
    pending = [query for query in queries if query.id not in checkpoint["rows"]]
    for offset in range(0, len(pending), BATCH_SIZE):
        batch = pending[offset : offset + BATCH_SIZE]
        missing_by_query = []
        texts = []
        for query in batch:
            missing = [doc_id for doc_id in pools[query.id][2] if doc_id not in pools[query.id][3]]
            missing_by_query.append(missing)
            texts.extend(
                (query.question, f"{document_by_id[doc_id].title}\n{document_by_id[doc_id].text}")
                for doc_id in missing
            )
        started = time.perf_counter()
        new_scores = model_pairs(texts) if texts else []
        elapsed_ms = (time.perf_counter() - started) * 1000
        cursor = 0
        for query, missing in zip(batch, missing_by_query, strict=True):
            four_pool, hybrid_pool, merged, historical_scores = pools[query.id]
            scores = {doc_id: float(historical_scores[doc_id]) for doc_id in merged if doc_id in historical_scores}
            for doc_id in missing:
                scores[doc_id] = new_scores[cursor]
                cursor += 1
            if set(scores) != set(merged):
                raise ValueError(f"Incomplete scores for {query.id}")
            checkpoint["rows"][query.id] = {
                "scores": scores,
                "reusedPairCount": len(merged) - len(missing),
                "newPairCount": len(missing),
                "newInferenceAllocatedMs": elapsed_ms * len(missing) / max(1, len(texts)),
            }
        if cursor != len(new_scores):
            raise ValueError("New-score cursor mismatch")
        atomic_write(args.checkpoint, checkpoint)
        print(f"scored {len(checkpoint['rows'])}/{len(queries)} questions", flush=True)

    four_rankings = {}
    hybrid_rankings = {}
    for query in queries:
        four_pool, hybrid_pool, _, _ = pools[query.id]
        scores = checkpoint["rows"][query.id]["scores"]
        four_rankings[query.id] = rank_from_scores(
            four_pool, [scores[doc_id] for doc_id in four_pool], 10
        )
        hybrid_rankings[query.id] = rank_from_scores(
            hybrid_pool, [scores[doc_id] for doc_id in hybrid_pool], 10
        )
    base_rankings = {query.id: ten_rankings["hybrid"][query.id] for query in queries}
    observations = {}
    summaries = {}
    for name, rankings in (
        ("four_route_ce", four_rankings),
        ("hybrid40_ce", hybrid_rankings),
        ("hybrid_rrf", base_rankings),
    ):
        rows, summary = evaluate_rankings(rankings, queries, {})
        observations[name] = clean_observations(rows)
        summaries[name] = clean_summary(summary)
    comparisons = paired_comparisons(
        observations, candidate_method="four_route_ce", seed=20261024, resamples=10000
    )
    rows = checkpoint["rows"]
    result = {
        "status": "completed",
        "classification": "post-hoc exploratory clean-source score-cache comparison",
        "claimAuthorized": False,
        "sourceCommit": forty["git"]["revision"],
        "analysisCommit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        ).stdout.strip(),
        "fingerprint": expected,
        "validation": checkpoint["validation"],
        "questions": len(queries),
        "pairCounts": {
            "fourRoutePoolMean": statistics.fmean(len(pools[q.id][0]) for q in queries),
            "fourRoutePoolMin": min(len(pools[q.id][0]) for q in queries),
            "fourRoutePoolMax": max(len(pools[q.id][0]) for q in queries),
            "hybrid40Pool": 40,
            "uniquePairs": sum(len(pools[q.id][2]) for q in queries),
            "reusedPairs": sum(row["reusedPairCount"] for row in rows.values()),
            "newPairs": sum(row["newPairCount"] for row in rows.values()),
        },
        "summaries": summaries,
        "comparisons": comparisons,
        "rankings": {"four_route_ce": four_rankings, "hybrid40_ce": hybrid_rankings, "hybrid_rrf": base_rankings},
        "observations": observations,
        "limitations": [
            "This comparison is post-hoc on a previously observed MuSiQue split.",
            "Historical per-pair scores were reused only after fingerprint and 32-pair numerical checks; missing pairs were scored locally.",
            "The Hybrid40 candidate budget differs from the four-route union; actual pool sizes are reported.",
            "The mixed score-cache execution time is not a full online latency measurement.",
            "Exact historical source-ranking replication failed despite matching input and embedding-model hashes.",
            "External provider response time is excluded.",
        ],
    }
    atomic_write(args.output, result)
    print(json.dumps({"status": "completed", "summaries": summaries, "comparisons": comparisons}))


if __name__ == "__main__":
    main()
