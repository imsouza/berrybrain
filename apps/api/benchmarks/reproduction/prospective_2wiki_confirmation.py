"""Prospective confirmatory evaluation on 200 unseen, disjoint 2WikiMultiHopQA questions (200..399).

Protocol: PROSPECTIVE_2WIKI_CONFIRMATION_PROTOCOL_2026-11-08.md.

Strictly disjoint from the exploratory 0..199 sample under deterministic
(sha256(_id), _id) ordering. One cross-encoder pass scores the deduplicated
union of four_route_title, four_route_openie, and hybrid40 per question.
"""

from __future__ import annotations

import argparse
import hashlib
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
    CorpusDocument,
    MiniLmEncoder,
    OpenIeGraph,
    QueryCase,
    reciprocal_rank_fusion,
    sha256_file,
    stable_document_id,
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
    TOKENIZER,
    TOP_K,
    TitleMentionGraph,
)

DATA = ROOT / "external-corpus"
OPENIE_2WIKI = DATA / "openie-legacy" / "openie_2wikimultihopqa_results_ner_gpt-3.5-turbo-1106_6119.json"
EXPLORATORY_REPORT = DATA / "2wiki-retrieval-report.json"
PROTOCOL = ROOT / "PROSPECTIVE_2WIKI_CONFIRMATION_PROTOCOL_2026-11-08.md"
EXPECTED_PROTOCOL_SHA256 = "86194d3fa827bf9174e5afcf535f3d58be81fe8f6f0ea3f77b5d197acae1133c"
CHECKPOINT = DATA / "2wiki-prospective-200-399.checkpoint.json"
OUTPUT = DATA / "2wiki-prospective-200-399-report.json"
SLICE_START = 200
SLICE_END = 400
DEPTH = 40
SEED = 20261108
RESAMPLES = 10_000


def fingerprint() -> dict[str, object]:
    protocol_sha = sha256_file(PROTOCOL)
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"Prospective protocol SHA-256 mismatch: {protocol_sha}")
    return {
        "protocolSha256": protocol_sha,
        "corpusSha256": sha256_file(CORPUS),
        "questionsSha256": sha256_file(QUESTIONS),
        "openieSha256": sha256_file(OPENIE_2WIKI),
        "exploratoryReportSha256": sha256_file(EXPLORATORY_REPORT),
        "embedderSha256": sha256_file(EMBEDDER / "onnx/model_qint8_arm64.onnx"),
        "crossEncoderSha256": sha256_file(CROSS_ENCODER),
        "tokenizerRevision": TOKENIZER.name,
        "selectedSlice": f"{SLICE_START}..{SLICE_END - 1}",
        "sourceDepth": TOP_K,
        "hybridDepth": DEPTH,
        "rrfK": RRF_K,
        "graphSeeds": GRAPH_SEEDS,
        "maxEntityDf": MAX_ENTITY_DF,
        "crossEncoderMaxLength": 512,
        "crossEncoderBatch": 8,
        "crossEncoderThreads": 2,
    }


def load_prospective_data() -> tuple[list[CorpusDocument], list[QueryCase]]:
    corpus_raw = json.loads(CORPUS.read_text(encoding="utf-8"))
    questions_raw = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    exploratory_ids = set(json.loads(EXPLORATORY_REPORT.read_text(encoding="utf-8"))["queryIds"])

    documents = [
        CorpusDocument(
            id=stable_document_id(str(row["title"]), str(row["text"])),
            title=str(row["title"]),
            text=str(row["text"]),
        )
        for row in corpus_raw
    ]
    by_title = {item.title: item.id for item in documents}
    if len(by_title) != len(documents):
        raise ValueError("Corpus titles are not unique")

    ordered = sorted(
        questions_raw,
        key=lambda row: (hashlib.sha256(str(row["_id"]).encode()).hexdigest(), str(row["_id"])),
    )
    first_200_ids = {str(row["_id"]) for row in ordered[:SLICE_START]}
    if first_200_ids != exploratory_ids:
        raise ValueError("Exploratory slice 0..199 does not match frozen 2wiki-retrieval-report.json")

    chosen = ordered[SLICE_START:SLICE_END]
    prospective_ids = {str(row["_id"]) for row in chosen}
    if len(chosen) != (SLICE_END - SLICE_START) or not exploratory_ids.isdisjoint(prospective_ids):
        raise ValueError("Prospective slice is incomplete or overlaps exploratory slice")

    queries = [
        QueryCase(
            id=str(row["_id"]),
            question=str(row["question"]),
            answers=(str(row["answer"]),),
            relevant_ids=tuple(dict.fromkeys(by_title[str(item[0])] for item in row["supporting_facts"])),
            hops=max(1, len({str(item[0]) for item in row["supporting_facts"]})),
        )
        for row in chosen
    ]
    if any(not q.relevant_ids for q in queries):
        raise ValueError("Prospective question support coverage is incomplete")
    return documents, queries


def compute_sources(documents: list[CorpusDocument], queries: list[QueryCase]) -> dict[str, object]:
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
    documents, queries = load_prospective_data()
    by_id = {item.id: item for item in documents}

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry_run_ok",
                    "prospectiveQueryCount": len(queries),
                    "disjointFromExploratory": True,
                    "protocolSha256": fp["protocolSha256"],
                },
                indent=2,
            )
        )
        return

    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if checkpoint["fingerprint"] != fp:
            raise ValueError("Prospective checkpoint fingerprint mismatch")
    else:
        sources = compute_sources(documents, queries)
        checkpoint = {
            "fingerprint": fp,
            "titleGraphStats": sources["titleGraphStats"],
            "openieGraphStats": sources["openieGraphStats"],
            "sources": sources["perQuery"],
            "rows": {},
        }
        atomic_write(CHECKPOINT, checkpoint)

    src_map = checkpoint["sources"]
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
        print(f"prospective-2wiki scored {len(rows)}/{len(queries)}", flush=True)

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
        "H1_fourTitleMinusMatchedTitle": pair_diff("four_route_title_ce", "hybrid_matched_title_ce"),
        "H2_fourTitleMinusFourOpenie": pair_diff("four_route_title_ce", "four_route_openie_ce"),
        "H2_fourOpenieMinusMatchedOpenie": pair_diff("four_route_openie_ce", "hybrid_matched_openie_ce"),
        "H3_fourTitleMinusHybrid40": pair_diff("four_route_title_ce", "hybrid40_ce"),
        "H3_fourTitleMinusNonstructural": pair_diff("four_route_title_ce", "nonstructural_ce"),
        "H3_fourTitleMinusHybrid": pair_diff("four_route_title_ce", "hybrid"),
        "fourOpenieMinusHybrid40": pair_diff("four_route_openie_ce", "hybrid40_ce"),
        "fourOpenieMinusHybrid": pair_diff("four_route_openie_ce", "hybrid"),
        "titleProxyMinusOpenieProxy": pair_diff("title_graph_proxy", "openie_graph_proxy"),
    }

    h1_r10 = comparisons["H1_fourTitleMinusMatchedTitle"]["recallAt10"]
    report = {
        "classification": "preregistered prospective confirmation on 200 disjoint 2WikiMultiHopQA questions (200..399)",
        "protocol": "PROSPECTIVE_2WIKI_CONFIRMATION_PROTOCOL_2026-11-08.md",
        "fingerprint": fp,
        "queryCount": len(queries),
        "documentCount": len(documents),
        "disjointFromExploratoryVerified": True,
        "primaryHypothesisH1Confirmed": bool(h1_r10["lower95"] > 0),
        "graphStats": {
            "titleMention": checkpoint["titleGraphStats"],
            "openie": checkpoint["openieGraphStats"],
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
        "queryIds": [q.id for q in queries],
        "summaries": summaries,
        "comparisons": comparisons,
        "rankings": rankings,
    }
    atomic_write(OUTPUT, report)
    print(
        json.dumps(
            {
                "status": "complete",
                "primaryHypothesisH1Confirmed": report["primaryHypothesisH1Confirmed"],
                "pool": report["pool"],
                "summaries": summaries,
                "comparisons": comparisons,
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
