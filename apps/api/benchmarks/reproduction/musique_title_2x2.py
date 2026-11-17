"""Cross-corpus 2x2 cell: Title-mention vs OpenIE on the 600 MuSiQue test questions.

Protocol: CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md.

Uses unmodified TitleMentionGraph (MAX_ENTITY_DF=64, GRAPH_SEEDS=20, RRF_K=60)
over the 11,656 MuSiQue passages and clean depth-40 source rankings. Scores the
deduplicated union of four_route_title(q) and hybrid_matched_title(q) in one
cross-encoder pass so four_route_title_ce, hybrid_matched_title_ce,
nonstructural_ce, and hybrid_top10_ce share identical per-pair logits, and
compares against the completed clean OpenIE rankings. Also audits unreranked
OpenIE proxy recall with HippoRAG's gpt-3.5-turbo-1106 vs gpt-4o-mini artifacts.
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
    MiniLmEncoder,
    OpenIeGraph,
    load_musique,
    reciprocal_rank_fusion,
    sha256_file,
    top_indices,
)
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores  # noqa: E402
from external_2wiki_retrieval import (  # noqa: E402
    CROSS_ENCODER,
    EMBEDDER,
    GRAPH_SEEDS,
    MAX_ENTITY_DF,
    RRF_K,
    TOKENIZER,
    TOP_K,
    TitleMentionGraph,
)

REPO = Path("/mnt/HDD_1/Antigravity/berrybrain")
CORPUS = ROOT / "artifact/inputs/musique_corpus.json"
QUESTIONS = ROOT / "artifact/inputs/musique.json"
SPLIT = ROOT / "frozen-evaluation/comparative-split-v1.json"
SOURCE40 = ROOT / "clean-rerun/musique-source-depth40.json"
FOUR_OPENIE = ROOT / "clean-rerun/four-route-ce.json"
MATCHED_OPENIE = ROOT / "clean-rerun/hybrid-matched-ce.json"
HYBRID40_CE = ROOT / "clean-rerun/hybrid40-ce.json"
OPENIE_GPT4O = ROOT / "external-corpus/openie_results_ner_gpt-4o-mini.json"
OPENIE_GPT35 = ROOT / "external-corpus/openie-legacy/openie_musique_results_ner_gpt-3.5-turbo-1106_11656.json"
EMBED_CACHE = REPO / ".benchmark-cache/musique-73157a03ce3f0b1a-minilm.npy"
PROTOCOL = ROOT / "CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md"
EXPECTED_PROTOCOL_SHA256 = "a1f602cff365a36c338558ca30cd7931fda73d5931e2753650a50952017a4151"
CHECKPOINT = ROOT / "clean-rerun/musique-title-2x2.checkpoint.json"
OUTPUT = ROOT / "clean-rerun/musique-title-2x2-report.json"
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
        "splitSha256": sha256_file(SPLIT),
        "source40Sha256": sha256_file(SOURCE40),
        "fourOpenieSha256": sha256_file(FOUR_OPENIE),
        "matchedOpenieSha256": sha256_file(MATCHED_OPENIE),
        "hybrid40CeSha256": sha256_file(HYBRID40_CE),
        "openieGpt4oSha256": sha256_file(OPENIE_GPT4O),
        "openieGpt35Sha256": sha256_file(OPENIE_GPT35),
        "embedderSha256": sha256_file(EMBEDDER / "onnx/model_qint8_arm64.onnx"),
        "crossEncoderSha256": sha256_file(CROSS_ENCODER),
        "tokenizerRevision": TOKENIZER.name,
        "sourceDepth": TOP_K,
        "rrfK": RRF_K,
        "graphSeeds": GRAPH_SEEDS,
        "maxEntityDf": MAX_ENTITY_DF,
        "crossEncoderMaxLength": 512,
        "crossEncoderBatch": 8,
        "crossEncoderThreads": 2,
    }


def compute_title_and_gpt35_sources(documents, all_queries, queries, src40_rankings) -> dict[str, object]:
    encoder = MiniLmEncoder(EMBEDDER, batch_size=24)
    vectors, _, _ = encoder.encode_cached([item.searchable_text for item in documents], EMBED_CACHE)
    all_query_vectors = encoder.encode([item.question for item in all_queries])
    encoder.close()
    qvec_by_id = {q.id: all_query_vectors[idx] for idx, q in enumerate(all_queries)}

    title_graph = TitleMentionGraph(documents)
    openie_gpt35_graph = OpenIeGraph(
        OPENIE_GPT35, documents, max_entity_document_frequency=MAX_ENTITY_DF
    )
    openie_gpt35_stats = {
        "distinctRetainedEntities": len(openie_gpt35_graph.entity_documents),
        "documentEntityPairs": sum(len(items) for items in openie_gpt35_graph.document_entities),
    }

    doc_ids = [item.id for item in documents]
    dense_agree_top40 = 0
    title_proxy_top10 = {}
    openie_gpt35_top10 = {}
    for query in queries:
        dense = vectors @ qvec_by_id[query.id]
        dense_rank = top_indices(dense, len(documents))
        dense_40_ids = [doc_ids[int(i)] for i in dense_rank[:40]]
        if dense_40_ids == src40_rankings["dense"][query.id]:
            dense_agree_top40 += 1

        t_scores = title_graph.propagate(dense)
        t_reached = np.flatnonzero(t_scores > 0)
        t_rank = t_reached[np.argsort(t_scores[t_reached], kind="stable")[::-1]]
        t_proxy = reciprocal_rank_fusion((dense_rank, t_rank), constant=RRF_K)
        title_proxy_top10[query.id] = [doc_ids[int(i)] for i in top_indices(t_proxy, TOP_K)]

        o35_scores = openie_gpt35_graph.propagate(dense, seed_count=GRAPH_SEEDS)
        o35_reached = np.flatnonzero(o35_scores > 0)
        o35_rank = o35_reached[np.argsort(o35_scores[o35_reached], kind="stable")[::-1]]
        o35_proxy = reciprocal_rank_fusion((dense_rank, o35_rank), constant=RRF_K)
        openie_gpt35_top10[query.id] = [doc_ids[int(i)] for i in top_indices(o35_proxy, TOP_K)]

    return {
        "titleGraphStats": title_graph.stats,
        "openieGpt35GraphStats": openie_gpt35_stats,
        "denseTop40EqualsCleanSource": dense_agree_top40,
        "titleProxyTop10": title_proxy_top10,
        "openieGpt35Top10": openie_gpt35_top10,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    fp = fingerprint()
    documents, all_queries = load_musique(CORPUS, QUESTIONS)
    split_ids = json.loads(SPLIT.read_text(encoding="utf-8"))["splits"]["confirmatory"]
    q_by_id = {q.id: q for q in all_queries}
    queries = [q_by_id[qid] for qid in split_ids]
    assert len(queries) == 600
    doc_text = {d.id: f"{d.title}\n{d.text}" for d in documents}
    src40 = json.loads(SOURCE40.read_text(encoding="utf-8"))["retrieval"]["rankings"]

    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if checkpoint["fingerprint"] != fp:
            raise ValueError("musique-title-2x2 checkpoint fingerprint mismatch")
    else:
        computed = compute_title_and_gpt35_sources(documents, all_queries, queries, src40)
        checkpoint = {
            "fingerprint": fp,
            "titleGraphStats": computed["titleGraphStats"],
            "openieGpt35GraphStats": computed["openieGpt35GraphStats"],
            "denseTop40EqualsCleanSource": computed["denseTop40EqualsCleanSource"],
            "titleProxyTop10": computed["titleProxyTop10"],
            "openieGpt35Top10": computed["openieGpt35Top10"],
            "rows": {},
        }
        if not args.dry_run:
            atomic_write(CHECKPOINT, checkpoint)

    title_top10 = checkpoint["titleProxyTop10"]
    openie_gpt35_top10 = checkpoint["openieGpt35Top10"]

    if args.dry_run:
        union_total = 0
        for q in queries:
            four_t = list(
                dict.fromkeys(
                    [
                        *src40["bm25"][q.id][:TOP_K],
                        *src40["dense"][q.id][:TOP_K],
                        *src40["hybrid"][q.id][:TOP_K],
                        *title_top10[q.id],
                    ]
                )
            )
            matched_t = src40["hybrid"][q.id][: len(four_t)]
            union_total += len(dict.fromkeys([*four_t, *matched_t]))
        print(
            json.dumps(
                {
                    "status": "dry_run_ok",
                    "queryCount": len(queries),
                    "denseTop40EqualsCleanSource": checkpoint["denseTop40EqualsCleanSource"],
                    "titleGraphStats": checkpoint["titleGraphStats"],
                    "openieGpt35GraphStats": checkpoint["openieGpt35GraphStats"],
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
        pools = []
        for q in batch:
            four_t = list(
                dict.fromkeys(
                    [
                        *src40["bm25"][q.id][:TOP_K],
                        *src40["dense"][q.id][:TOP_K],
                        *src40["hybrid"][q.id][:TOP_K],
                        *title_top10[q.id],
                    ]
                )
            )
            matched_t = src40["hybrid"][q.id][: len(four_t)]
            pools.append(list(dict.fromkeys([*four_t, *matched_t])))
        pairs = [
            (q.question, doc_text[d])
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
        print(f"musique-title-2x2 scored {len(rows)}/{len(queries)}", flush=True)

    four_openie_rankings = json.loads(FOUR_OPENIE.read_text(encoding="utf-8"))["rankings"]
    matched_openie_rankings = json.loads(MATCHED_OPENIE.read_text(encoding="utf-8"))["rankings"]
    hybrid40_ce_rankings = json.loads(HYBRID40_CE.read_text(encoding="utf-8"))["rankings"]

    rankings = {
        "bm25": {},
        "dense": {},
        "hybrid": {},
        "openie_graphrag_gpt4o": {},
        "openie_graphrag_gpt35": {},
        "title_graph_proxy": {},
        "hybrid_top10_ce": {},
        "nonstructural_ce": {},
        "hybrid_matched_openie_ce": matched_openie_rankings,
        "four_route_openie_ce": four_openie_rankings,
        "hybrid_matched_title_ce": {},
        "four_route_title_ce": {},
        "hybrid40_ce": hybrid40_ce_rankings,
    }
    title_sizes, openie_sizes = [], []
    for q in queries:
        bm25_10 = src40["bm25"][q.id][:TOP_K]
        dense_10 = src40["dense"][q.id][:TOP_K]
        hyb_10 = src40["hybrid"][q.id][:TOP_K]
        openie_10 = src40["openie_graphrag"][q.id][:TOP_K]
        t_10 = title_top10[q.id]
        nonstructural = list(dict.fromkeys([*bm25_10, *dense_10, *hyb_10]))
        four_t = list(dict.fromkeys([*nonstructural, *t_10]))
        four_o = list(dict.fromkeys([*nonstructural, *openie_10]))
        matched_t = src40["hybrid"][q.id][: len(four_t)]
        title_sizes.append(len(four_t))
        openie_sizes.append(len(four_o))

        score = dict(zip(rows[q.id]["pool"], rows[q.id]["scores"], strict=True))

        def rerank_pool(pool: list[str]) -> list[str]:
            return rank_from_scores(pool, [score[d] for d in pool], TOP_K)

        rankings["bm25"][q.id] = bm25_10
        rankings["dense"][q.id] = dense_10
        rankings["hybrid"][q.id] = hyb_10
        rankings["openie_graphrag_gpt4o"][q.id] = openie_10
        rankings["openie_graphrag_gpt35"][q.id] = openie_gpt35_top10[q.id]
        rankings["title_graph_proxy"][q.id] = t_10
        rankings["hybrid_top10_ce"][q.id] = rerank_pool(hyb_10)
        rankings["nonstructural_ce"][q.id] = rerank_pool(nonstructural)
        rankings["hybrid_matched_title_ce"][q.id] = rerank_pool(matched_t)
        rankings["four_route_title_ce"][q.id] = rerank_pool(four_t)

    observations, summaries = {}, {}
    for m, r in rankings.items():
        observations[m], summaries[m] = evaluate_rankings(r, queries, {})
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
        "fourTitleMinusHybrid": pair_diff("four_route_title_ce", "hybrid"),
        "titleProxyMinusOpenieGpt4oProxy": pair_diff("title_graph_proxy", "openie_graphrag_gpt4o"),
        "openieGpt4oProxyMinusGpt35Proxy": pair_diff("openie_graphrag_gpt4o", "openie_graphrag_gpt35"),
    }

    report = {
        "classification": "post-hoc exploratory 2x2 link-type comparison on 600 MuSiQue confirmatory-split questions",
        "protocol": "CROSS_CORPUS_2X2_LINK_TYPE_PROTOCOL_2026-11-08.md",
        "fingerprint": fp,
        "queryCount": len(queries),
        "documentCount": len(documents),
        "graphStats": {
            "titleMention": checkpoint["titleGraphStats"],
            "openieGpt35": checkpoint["openieGpt35GraphStats"],
        },
        "checks": {
            "denseTop40EqualsCleanSource": checkpoint["denseTop40EqualsCleanSource"],
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
