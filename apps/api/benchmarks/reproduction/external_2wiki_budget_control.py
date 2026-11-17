"""Candidate-budget controls on the frozen 200-question 2WikiMultiHopQA study.

Protocol: BUDGET_CONTROL_2WIKI_PROTOCOL_2026-10-30.md.

One cross-encoder pass scores the union of (a) the frozen four-route pool from
2wiki-crossencoder.checkpoint.json and (b) a recomputed Hybrid-RRF depth-40
pool. Every reranked configuration is derived from these same scores:
Hybrid top-10 + CE, nonstructural union + CE, Hybrid with matched budget N(q)
+ CE, Hybrid40 + CE and four routes + CE. No relevance label enters pool
selection or scoring.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "reproduction-src"))
sys.path.insert(0, str(ROOT))

from comparative_retrieval_benchmark import evaluate_rankings, paired_comparisons  # noqa: E402
from same_corpus_rag_benchmark import (  # noqa: E402
    Bm25Index,
    MiniLmEncoder,
    reciprocal_rank_fusion,
    sha256_file,
    top_indices,
)
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores  # noqa: E402

# Imported last: the frozen reproduction-src modules above are already cached.
from external_2wiki_retrieval import (  # noqa: E402
    CROSS_ENCODER,
    EMBED_CACHE,
    EMBEDDER,
    RRF_K,
    SCORE_CHECKPOINT,
    SOURCE_CHECKPOINT,
    TOKENIZER,
    load_data,
)

DATA = ROOT / "external-corpus"
CHECKPOINT = DATA / "2wiki-budget-control.checkpoint.json"
OUTPUT = DATA / "2wiki-budget-control-report.json"
DEPTH = 40
TOP_K = 10
SEED = 20261030
RESAMPLES = 10_000


def fingerprint() -> dict[str, object]:
    return {
        "scriptSha256": sha256_file(Path(__file__)),
        "sourceCheckpointSha256": sha256_file(SOURCE_CHECKPOINT),
        "frozenScoreCheckpointSha256": sha256_file(SCORE_CHECKPOINT),
        "embedderSha256": sha256_file(EMBEDDER / "onnx/model_qint8_arm64.onnx"),
        "crossEncoderSha256": sha256_file(CROSS_ENCODER),
        "tokenizerRevision": TOKENIZER.name,
        "hybridDepth": DEPTH,
        "crossEncoderMaxLength": 512,
        "crossEncoderBatch": 8,
        "crossEncoderThreads": 2,
    }


def hybrid_depth40(documents, queries) -> tuple[dict[str, list[str]], dict[str, float]]:
    bm25 = Bm25Index([item.searchable_text for item in documents])
    encoder = MiniLmEncoder(EMBEDDER, batch_size=16)
    vectors, _, _ = encoder.encode_cached([item.searchable_text for item in documents], EMBED_CACHE)
    query_vectors = encoder.encode([item.question for item in queries])
    encoder.close()
    doc_ids = [item.id for item in documents]
    result, timing = {}, {}
    for index, query in enumerate(queries):
        started = time.perf_counter()
        lexical_rank = top_indices(bm25.scores(query.question), len(documents))
        dense_rank = top_indices(vectors @ query_vectors[index], len(documents))
        fused = reciprocal_rank_fusion((lexical_rank, dense_rank), constant=RRF_K)
        result[query.id] = [doc_ids[int(i)] for i in top_indices(fused, DEPTH)]
        timing[query.id] = (time.perf_counter() - started) * 1000
    return result, timing


def main() -> None:
    fp = fingerprint()
    documents, queries = load_data()
    by_id = {item.id: item for item in documents}
    source_rows = json.loads(SOURCE_CHECKPOINT.read_text())["rows"]
    frozen_rows = json.loads(SCORE_CHECKPOINT.read_text())["rows"]

    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text())
        if checkpoint["fingerprint"] != fp:
            raise ValueError("checkpoint fingerprint differs")
    else:
        hybrid40, hybrid_ms = hybrid_depth40(documents, queries)
        checkpoint = {"fingerprint": fp, "hybrid40": hybrid40, "hybridSourceMs": hybrid_ms, "rows": {}}
        atomic_write(CHECKPOINT, checkpoint)
    hybrid40 = checkpoint["hybrid40"]
    rows = checkpoint["rows"]

    model = None
    pending = [q for q in queries if q.id not in rows]
    for offset in range(0, len(pending), 8):
        if model is None:
            model = OnnxCrossEncoder(
                model_path=CROSS_ENCODER, tokenizer_name=str(TOKENIZER), revision=None,
                max_length=512, intra_op_threads=2,
            )
        batch = pending[offset : offset + 8]
        pools = [list(dict.fromkeys([*frozen_rows[q.id]["pool"], *hybrid40[q.id]])) for q in batch]
        pairs = [
            (q.question, f"{by_id[d].title}\n{by_id[d].text}")
            for q, pool in zip(batch, pools, strict=True) for d in pool
        ]
        started = time.perf_counter()
        scores = model.predict(pairs, batch_size=8)
        elapsed = (time.perf_counter() - started) * 1000
        cursor = 0
        for q, pool in zip(batch, pools, strict=True):
            rows[q.id] = {"pool": pool, "scores": scores[cursor : cursor + len(pool)],
                          "modelPredictMs": elapsed * len(pool) / len(pairs)}
            cursor += len(pool)
        checkpoint["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_write(CHECKPOINT, checkpoint)
        print(f"scored {len(rows)}/{len(queries)}", flush=True)

    methods = ("hybrid", "hybrid_top10_ce", "nonstructural_ce", "hybrid_matched_ce",
               "hybrid40_ce", "four_route_ce", "four_route_ce_frozen_scores")
    rankings = {m: {} for m in methods}
    pool_sizes, matched_sizes, top10_agree, score_dev = [], [], 0, []
    for q in queries:
        src = source_rows[q.id]["rankings"]
        frozen = frozen_rows[q.id]
        score = dict(zip(rows[q.id]["pool"], rows[q.id]["scores"], strict=True))
        four = frozen["pool"]
        n_q = len(four)
        matched = hybrid40[q.id][:n_q]
        nonstructural = list(dict.fromkeys(d for m in ("bm25", "dense", "hybrid") for d in src[m]))
        top10_agree += hybrid40[q.id][:TOP_K] == src["hybrid"]
        score_dev.extend(abs(a - score[d]) for d, a in zip(four, frozen["scores"], strict=True))
        pool_sizes.append(n_q)
        matched_sizes.append(len(matched))

        def rerank(pool, table=score):
            return rank_from_scores(pool, [table[d] for d in pool], TOP_K)

        rankings["hybrid"][q.id] = src["hybrid"]
        rankings["hybrid_top10_ce"][q.id] = rerank(src["hybrid"])
        rankings["nonstructural_ce"][q.id] = rerank(nonstructural)
        rankings["hybrid_matched_ce"][q.id] = rerank(matched)
        rankings["hybrid40_ce"][q.id] = rerank(hybrid40[q.id])
        rankings["four_route_ce"][q.id] = rerank(four)
        rankings["four_route_ce_frozen_scores"][q.id] = rank_from_scores(four, frozen["scores"], TOP_K)

    observations, summaries = {}, {}
    for m in methods:
        observations[m], summaries[m] = evaluate_rankings(rankings[m], queries, {})
        for key in ("latencyMedianMs", "latencyP95Ms"):
            summaries[m].pop(key, None)

    def compare(base: str) -> dict:
        return paired_comparisons(
            {base: observations[base], "four_route_ce": observations["four_route_ce"]},
            candidate_method="four_route_ce", seed=SEED, resamples=RESAMPLES,
        )[base]

    report = {
        "classification": "post-hoc exploratory candidate-budget control on a previously observed 2Wiki sample",
        "protocol": "BUDGET_CONTROL_2WIKI_PROTOCOL_2026-10-30.md",
        "fingerprint": fp,
        "queryCount": len(queries),
        "pool": {
            "fourRouteMean": statistics.fmean(pool_sizes),
            "fourRouteMin": min(pool_sizes), "fourRouteMax": max(pool_sizes),
            "matchedMean": statistics.fmean(matched_sizes),
            "unionPairsScored": sum(len(r["pool"]) for r in rows.values()),
        },
        "checks": {
            "recomputedHybridTop10EqualsFrozen": top10_agree,
            "fourRouteScoreAbsDevMax": max(score_dev),
            "fourRouteScoreAbsDevMean": float(np.mean(score_dev)),
            "fourRouteTop10EqualsFrozenScores": sum(
                rankings["four_route_ce"][q.id] == rankings["four_route_ce_frozen_scores"][q.id] for q in queries
            ),
        },
        "modelPredictMs": {
            "median": statistics.median(r["modelPredictMs"] for r in rows.values()),
            "total": sum(r["modelPredictMs"] for r in rows.values()),
        },
        "summaries": summaries,
        "comparisons": {
            "fourMinusMatched": compare("hybrid_matched_ce"),
            "fourMinusHybrid40": compare("hybrid40_ce"),
            "fourMinusNonstructural": compare("nonstructural_ce"),
            "fourMinusHybrid": compare("hybrid"),
        },
        "rankings": rankings,
    }
    atomic_write(OUTPUT, report)
    print(json.dumps({"summaries": summaries, "checks": report["checks"],
                      "comparisons": report["comparisons"]}, indent=1), flush=True)


if __name__ == "__main__":
    main()
