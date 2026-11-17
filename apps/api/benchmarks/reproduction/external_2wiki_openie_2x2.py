"""Cross-corpus 2x2 cell: OpenIE vs Title-mention on the 200 exploratory 2Wiki questions.

Protocol: CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md.

One cross-encoder pass scores the deduplicated union of four_route_title,
four_route_openie, and hybrid40 for each of the 200 exploratory 2WikiMultiHopQA
questions (indices 0..199 by SHA-256(_id)), so every reranked arm shares
identical per-pair logits.
"""

from __future__ import annotations

import argparse
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
    OpenIeGraph,
    reciprocal_rank_fusion,
    sha256_file,
    top_indices,
)
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores  # noqa: E402
from external_2wiki_retrieval import (  # noqa: E402
    CORPUS,
    CROSS_ENCODER,
    EMBED_CACHE,
    EMBEDDER,
    GRAPH_SEEDS,
    MAX_ENTITY_DF,
    QUESTIONS,
    RRF_K,
    SOURCE_CHECKPOINT,
    TOKENIZER,
    TOP_K,
    TitleMentionGraph,
    load_data,
)

DATA = ROOT / "external-corpus"
OPENIE_2WIKI = DATA / "openie-legacy" / "openie_2wikimultihopqa_results_ner_gpt-3.5-turbo-1106_6119.json"
PROTOCOL = ROOT / "CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md"
EXPECTED_PROTOCOL_SHA256 = "a1f602cff365a36c338558ca30cd7931fda73d5931e2753650a50952017a4151"
CHECKPOINT = DATA / "2wiki-2x2-openie.checkpoint.json"
OUTPUT = DATA / "2wiki-2x2-openie-report.json"
DEPTH = 40
SEED = 20261108
RESAMPLES = 10_000


def fingerprint() -> dict[str, object]:
    protocol_sha = sha256_file(PROTOCOL)
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"Protocol SHA-256 mismatch: {protocol_sha}")
    return {
        "protocolSha256": protocol_sha,
        "corpusSha256": sha256_file(CORPUS),
        "questionsSha256": sha256_file(QUESTIONS),
        "openieSha256": sha256_file(OPENIE_2WIKI),
        "embedderSha256": sha256_file(EMBEDDER / "onnx/model_qint8_arm64.onnx"),
        "crossEncoderSha256": sha256_file(CROSS_ENCODER),
        "tokenizerRevision": TOKENIZER.name,
        "selectedSlice": "0..199",
        "sourceDepth": TOP_K,
        "hybridDepth": DEPTH,
        "rrfK": RRF_K,
        "graphSeeds": GRAPH_SEEDS,
        "maxEntityDf": MAX_ENTITY_DF,
        "crossEncoderMaxLength": 512,
        "crossEncoderBatch": 8,
        "crossEncoderThreads": 2,
    }


def compute_sources(documents, queries) -> dict[str, object]:
    bm25 = Bm25Index([item.searchable_text for item in documents])
    encoder = MiniLmEncoder(EMBEDDER, batch_size=16)
    vectors, _, _ = encoder.encode_cached([item.searchable_text for item in documents], EMBED_CACHE)
    query_vectors = encoder.encode([item.question for item in queries])
    encoder.close()

    title_graph = TitleMentionGraph(documents)
    openie_graph = OpenIeGraph(
        OPENIE_2WIKI, documents, max_entity_document_frequency=MAX_ENTITY_DF
    )
    openie_stats = {
        "distinctRetainedEntities": len(openie_graph.entity_documents),
        "documentEntityPairs": sum(len(items) for items in openie_graph.document_entities),
    }

    doc_ids = [item.id for item in documents]
    per_query = {}
    for index, query in enumerate(queries):
        lexical_rank = top_indices(bm25.scores(query.question), len(documents))
        dense = vectors @ query_vectors[index]
        dense_rank = top_indices(dense, len(documents))
        hybrid = reciprocal_rank_fusion((lexical_rank, dense_rank), constant=RRF_K)

        t_scores = title_graph.propagate(dense)
        t_reached = np.flatnonzero(t_scores > 0)
        t_rank = t_reached[np.argsort(t_scores[t_reached], kind="stable")[::-1]]
        t_proxy = reciprocal_rank_fusion((dense_rank, t_rank), constant=RRF_K)

        o_scores = openie_graph.propagate(dense, seed_count=GRAPH_SEEDS)
        o_reached = np.flatnonzero(o_scores > 0)
        o_rank = o_reached[np.argsort(o_scores[o_reached], kind="stable")[::-1]]
        o_proxy = reciprocal_rank_fusion((dense_rank, o_rank), constant=RRF_K)

        per_query[query.id] = {
            "bm25": [doc_ids[int(i)] for i in lexical_rank[:TOP_K]],
            "dense": [doc_ids[int(i)] for i in dense_rank[:TOP_K]],
            "hybrid": [doc_ids[int(i)] for i in top_indices(hybrid, TOP_K)],
            "hybrid40": [doc_ids[int(i)] for i in top_indices(hybrid, DEPTH)],
            "title_graph_proxy": [doc_ids[int(i)] for i in top_indices(t_proxy, TOP_K)],
            "openie_graph_proxy": [doc_ids[int(i)] for i in top_indices(o_proxy, TOP_K)],
        }
    return {
        "titleGraphStats": title_graph.stats,
        "openieGraphStats": openie_stats,
        "perQuery": per_query,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fp = fingerprint()
    documents, queries = load_data()
    by_id = {item.id: item for item in documents}
    frozen_src = json.loads(SOURCE_CHECKPOINT.read_text(encoding="utf-8"))["rows"]

    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if checkpoint["fingerprint"] != fp:
            raise ValueError("2wiki-2x2-openie checkpoint fingerprint mismatch")
    else:
        sources = compute_sources(documents, queries)
        checkpoint = {
            "fingerprint": fp,
            "titleGraphStats": sources["titleGraphStats"],
            "openieGraphStats": sources["openieGraphStats"],
            "sources": sources["perQuery"],
            "rows": {},
        }
        if not args.dry_run:
            atomic_write(CHECKPOINT, checkpoint)

    src_map = checkpoint["sources"]
    title_agree = sum(
        src_map[q.id]["title_graph_proxy"] == frozen_src[q.id]["rankings"]["graph_proxy"]
        for q in queries
    )
    bm25_agree = sum(
        src_map[q.id]["bm25"] == frozen_src[q.id]["rankings"]["bm25"]
        for q in queries
    )
    if args.dry_run:
        union_total = sum(
            len(
                dict.fromkeys(
                    [
                        *src_map[q.id]["bm25"],
                        *src_map[q.id]["dense"],
                        *src_map[q.id]["hybrid"],
                        *src_map[q.id]["title_graph_proxy"],
                        *src_map[q.id]["openie_graph_proxy"],
                        *src_map[q.id]["hybrid40"],
                    ]
                )
            )
            for q in queries
        )
        print(
            json.dumps(
                {
                    "status": "dry_run_ok",
                    "queryCount": len(queries),
                    "bm25EqualsFrozen": bm25_agree,
                    "titleProxyEqualsFrozen": title_agree,
                    "titleGraphStats": checkpoint["titleGraphStats"],
                    "openieGraphStats": checkpoint["openieGraphStats"],
                    "unionPairs": union_total,
                },
                indent=2,
            )
        )
        return

    rows = checkpoint["rows"]
    pending = [q for q in queries if q.id not in rows]
    model = None
    for offset in range(0, len(pending), 8):
        if model is None:
            model = OnnxCrossEncoder(
                model_path=CROSS_ENCODER,
                tokenizer_name=str(TOKENIZER),
                revision=None,
                max_length=512,
                intra_op_threads=2,
            )
        batch = pending[offset : offset + 8]
        pools = [
            list(
                dict.fromkeys(
                    [
                        *src_map[q.id]["bm25"],
                        *src_map[q.id]["dense"],
                        *src_map[q.id]["hybrid"],
                        *src_map[q.id]["title_graph_proxy"],
                        *src_map[q.id]["openie_graph_proxy"],
                        *src_map[q.id]["hybrid40"],
                    ]
                )
            )
            for q in batch
        ]
        pairs = [
            (q.question, f"{by_id[d].title}\n{by_id[d].text}")
            for q, pool in zip(batch, pools, strict=True)
            for d in pool
        ]
        started = time.perf_counter()
        scores = model.predict(pairs, batch_size=8)
        elapsed_ms = (time.perf_counter() - started) * 1000
        cursor = 0
        for q, pool in zip(batch, pools, strict=True):
            rows[q.id] = {
                "pool": pool,
                "scores": scores[cursor : cursor + len(pool)],
                "modelPredictMs": elapsed_ms * len(pool) / len(pairs),
            }
            cursor += len(pool)
        checkpoint["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_write(CHECKPOINT, checkpoint)
        print(f"2wiki-2x2 scored {len(rows)}/{len(queries)}", flush=True)

    methods = (
        "bm25",
        "dense",
        "hybrid",
        "title_graph_proxy",
        "openie_graph_proxy",
        "hybrid_top10_ce",
        "nonstructural_ce",
        "hybrid_matched_openie_ce",
        "four_route_openie_ce",
        "hybrid_matched_title_ce",
        "four_route_title_ce",
        "hybrid40_ce",
    )
    rankings = {m: {} for m in methods}
    title_sizes, openie_sizes = [], []
    for q in queries:
        s = src_map[q.id]
        score = dict(zip(rows[q.id]["pool"], rows[q.id]["scores"], strict=True))
        nonstructural = list(dict.fromkeys([*s["bm25"], *s["dense"], *s["hybrid"]]))
        four_title = list(dict.fromkeys([*nonstructural, *s["title_graph_proxy"]]))
        four_openie = list(dict.fromkeys([*nonstructural, *s["openie_graph_proxy"]]))
        matched_title = s["hybrid40"][: len(four_title)]
        matched_openie = s["hybrid40"][: len(four_openie)]
        title_sizes.append(len(four_title))
        openie_sizes.append(len(four_openie))

        def rerank_pool(pool: list[str]) -> list[str]:
            return rank_from_scores(pool, [score[d] for d in pool], TOP_K)

        for m in ("bm25", "dense", "hybrid", "title_graph_proxy", "openie_graph_proxy"):
            rankings[m][q.id] = s[m]
        rankings["hybrid_top10_ce"][q.id] = rerank_pool(s["hybrid"])
        rankings["nonstructural_ce"][q.id] = rerank_pool(nonstructural)
        rankings["hybrid_matched_openie_ce"][q.id] = rerank_pool(matched_openie)
        rankings["four_route_openie_ce"][q.id] = rerank_pool(four_openie)
        rankings["hybrid_matched_title_ce"][q.id] = rerank_pool(matched_title)
        rankings["four_route_title_ce"][q.id] = rerank_pool(four_title)
        rankings["hybrid40_ce"][q.id] = rerank_pool(s["hybrid40"])

    observations, summaries = {}, {}
    for m in methods:
        observations[m], summaries[m] = evaluate_rankings(rankings[m], queries, {})
        for key in ("latencyMedianMs", "latencyP95Ms"):
            summaries[m].pop(key, None)

    def pair_diff(cand: str, base: str) -> dict:
        return paired_comparisons(
            {base: observations[base], cand: observations[cand]},
            candidate_method=cand,
            seed=SEED,
            resamples=RESAMPLES,
        )[base]

    comparisons = {
        "fourTitleMinusMatchedTitle": pair_diff("four_route_title_ce", "hybrid_matched_title_ce"),
        "fourOpenieMinusMatchedOpenie": pair_diff("four_route_openie_ce", "hybrid_matched_openie_ce"),
        "fourTitleMinusFourOpenie": pair_diff("four_route_title_ce", "four_route_openie_ce"),
        "fourTitleMinusHybrid40": pair_diff("four_route_title_ce", "hybrid40_ce"),
        "fourOpenieMinusHybrid40": pair_diff("four_route_openie_ce", "hybrid40_ce"),
        "fourTitleMinusNonstructural": pair_diff("four_route_title_ce", "nonstructural_ce"),
        "fourOpenieMinusNonstructural": pair_diff("four_route_openie_ce", "nonstructural_ce"),
        "fourTitleMinusHybrid": pair_diff("four_route_title_ce", "hybrid"),
        "fourOpenieMinusHybrid": pair_diff("four_route_openie_ce", "hybrid"),
        "titleProxyMinusOpenieProxy": pair_diff("title_graph_proxy", "openie_graph_proxy"),
    }

    report = {
        "classification": "post-hoc exploratory 2x2 link-type comparison on 200 2WikiMultiHopQA questions (0..199)",
        "protocol": "CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md",
        "fingerprint": fp,
        "queryCount": len(queries),
        "documentCount": len(documents),
        "graphStats": {
            "titleMention": checkpoint["titleGraphStats"],
            "openie": checkpoint["openieGraphStats"],
        },
        "checks": {
            "bm25EqualsFrozen": bm25_agree,
            "titleProxyEqualsFrozen": title_agree,
        },
        "pool": {
            "fourTitleMean": statistics.fmean(title_sizes),
            "fourTitleMin": min(title_sizes),
            "fourTitleMax": max(title_sizes),
            "fourOpenieMean": statistics.fmean(openie_sizes),
            "fourOpenieMin": min(openie_sizes),
            "fourOpenieMax": max(openie_sizes),
            "unionPairsScored": sum(len(r["pool"]) for r in rows.values()),
        },
        "modelPredictMs": {
            "median": statistics.median(r["modelPredictMs"] for r in rows.values()),
            "total": sum(r["modelPredictMs"] for r in rows.values()),
        },
        "summaries": summaries,
        "comparisons": comparisons,
        "rankings": rankings,
    }
    atomic_write(OUTPUT, report)
    print(
        json.dumps(
            {
                "status": "complete",
                "pool": report["pool"],
                "checks": report["checks"],
                "summaries": summaries,
                "comparisons": comparisons,
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
