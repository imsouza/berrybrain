"""MuSiQue clean-source controls and end-to-end latency on the Raspberry Pi.

Protocol: MUSIQUE_CLEAN_TABLE_AND_LATENCY_PROTOCOL_2026-10-30.md

Mode ``nonstructural``: score the clean nonstructural union (BM25, dense and
Hybrid-RRF top ten) for the 600 test questions, giving Hybrid top-10 + CE and
nonstructural union + CE on the same clean source rankings as the other
reranked controls.

Mode ``latency``: for 100 hash-selected test questions, time each
configuration end to end (query embedding -> source rankings -> pool ->
cross-encoder -> top ten), one query at a time, in rotated order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "reproduction-src"))

from comparative_retrieval_benchmark import evaluate_rankings, paired_comparisons  # noqa: E402
from same_corpus_rag_benchmark import (  # noqa: E402
    Bm25Index,
    MiniLmEncoder,
    OpenIeGraph,
    load_musique,
    reciprocal_rank_fusion,
    sha256_file,
    top_indices,
)
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores  # noqa: E402

REPO = Path("/mnt/HDD_1/Antigravity/berrybrain")
CORPUS = ROOT / "artifact/inputs/musique_corpus.json"
QUESTIONS = ROOT / "artifact/inputs/musique.json"
OPENIE = ROOT / "external-corpus/openie_results_ner_gpt-4o-mini.json"
SPLIT = ROOT / "frozen-evaluation/comparative-split-v1.json"
EMBEDDER = REPO / ".benchmark-cache/models/all-MiniLM-L6-v2"
EMBED_CACHE = REPO / ".benchmark-cache/musique-73157a03ce3f0b1a-minilm.npy"
CROSS_ENCODER = REPO / ".benchmark-cache/onnx-crossencoder/model.int8.onnx"
TOKENIZER = REPO / ".benchmark-cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a"
SOURCE = ROOT / "clean-rerun/musique-source-depth40.json"
FOUR = ROOT / "clean-rerun/four-route-ce.json"
MATCHED = ROOT / "clean-rerun/hybrid-matched-ce.json"
H40 = ROOT / "clean-rerun/hybrid40-ce.json"
OUT = ROOT / "clean-rerun"
TOP_K = 10
SEED = 20261030


def model() -> OnnxCrossEncoder:
    return OnnxCrossEncoder(model_path=CROSS_ENCODER, tokenizer_name=str(TOKENIZER), revision=None,
                            max_length=512, intra_op_threads=2)


def test_queries():
    documents, queries = load_musique(CORPUS, QUESTIONS)
    split = json.loads(SPLIT.read_text())["splits"]["confirmatory"]
    by_id = {q.id: q for q in queries}
    return documents, [by_id[i] for i in split]


def nonstructural() -> None:
    documents, queries = test_queries()
    text = {d.id: f"{d.title}\n{d.text}" for d in documents}
    src = json.loads(SOURCE.read_text())["retrieval"]["rankings"]
    ckpt_path = OUT / "nonstructural-ce.checkpoint.json"
    fp = {"script": sha256_file(Path(__file__)), "source": sha256_file(SOURCE),
          "crossEncoder": sha256_file(CROSS_ENCODER), "tokenizer": TOKENIZER.name}
    ckpt = json.loads(ckpt_path.read_text()) if ckpt_path.exists() else {"fingerprint": fp, "rows": {}}
    if {k: v for k, v in ckpt["fingerprint"].items() if k != "script"} != {
        k: v for k, v in fp.items() if k != "script"
    }:
        raise ValueError("fingerprint differs")
    rows = ckpt["rows"]
    pending = [q for q in queries if q.id not in rows]
    ce = model() if pending else None
    for off in range(0, len(pending), 8):
        batch = pending[off: off + 8]
        pools = [list(dict.fromkeys(d for m in ("bm25", "dense", "hybrid") for d in src[m][q.id][:TOP_K]))
                 for q in batch]
        pairs = [(q.question, text[d]) for q, p in zip(batch, pools) for d in p]
        t0 = time.perf_counter()
        scores = ce.predict(pairs, batch_size=8)
        ms = (time.perf_counter() - t0) * 1000
        c = 0
        for q, p in zip(batch, pools):
            rows[q.id] = {"pool": p, "scores": scores[c: c + len(p)], "modelPredictMs": ms * len(p) / len(pairs)}
            c += len(p)
        atomic_write(ckpt_path, ckpt)
        print(f"nonstructural {len(rows)}/{len(queries)}", flush=True)

    rankings = {
        "bm25": {},
        "dense": {},
        "openie_graphrag": {},
        "hybrid": {},
        "hybrid_top10_ce": {},
        "nonstructural_ce": {},
    }
    for q in queries:
        rankings["bm25"][q.id] = src["bm25"][q.id][:TOP_K]
        rankings["dense"][q.id] = src["dense"][q.id][:TOP_K]
        rankings["openie_graphrag"][q.id] = src["openie_graphrag"][q.id][:TOP_K]
        score = dict(zip(rows[q.id]["pool"], rows[q.id]["scores"]))
        hyb = src["hybrid"][q.id][:TOP_K]
        rankings["hybrid"][q.id] = hyb
        rankings["hybrid_top10_ce"][q.id] = rank_from_scores(hyb, [score[d] for d in hyb], TOP_K)
        pool = rows[q.id]["pool"]
        rankings["nonstructural_ce"][q.id] = rank_from_scores(pool, [score[d] for d in pool], TOP_K)
    for name, path in (("four_route_ce", FOUR), ("hybrid_matched_ce", MATCHED), ("hybrid40_ce", H40)):
        rankings[name] = json.loads(path.read_text())["rankings"]
    obs, summ = {}, {}
    for m, r in rankings.items():
        obs[m], summ[m] = evaluate_rankings(r, queries, {})
        summ[m].pop("latencyMedianMs"), summ[m].pop("latencyP95Ms")
    comps = {}
    for base in (
        "bm25",
        "dense",
        "openie_graphrag",
        "hybrid",
        "hybrid_top10_ce",
        "nonstructural_ce",
        "hybrid_matched_ce",
        "hybrid40_ce",
    ):
        comps[f"fourMinus_{base}"] = paired_comparisons(
            {base: obs[base], "four_route_ce": obs["four_route_ce"]}, candidate_method="four_route_ce",
            seed=SEED, resamples=10_000)[base]
    comps["nonstructuralMinusHybrid"] = paired_comparisons(
        {"hybrid": obs["hybrid"], "nonstructural_ce": obs["nonstructural_ce"]},
        candidate_method="nonstructural_ce", seed=SEED, resamples=10_000)["hybrid"]
    comps["matchedMinusHybrid"] = paired_comparisons(
        {"hybrid": obs["hybrid"], "hybrid_matched_ce": obs["hybrid_matched_ce"]},
        candidate_method="hybrid_matched_ce", seed=SEED, resamples=10_000)["hybrid"]
    comps["hybrid40MinusHybrid"] = paired_comparisons(
        {"hybrid": obs["hybrid"], "hybrid40_ce": obs["hybrid40_ce"]},
        candidate_method="hybrid40_ce", seed=SEED, resamples=10_000)["hybrid"]
    sizes = [len(rows[q.id]["pool"]) for q in queries]
    report = {"classification": "post-hoc exploratory clean-source consolidation", "fingerprint": fp,
              "checkpointFingerprint": ckpt["fingerprint"],
              "poolMean": statistics.fmean(sizes), "poolMedian": statistics.median(sizes),
              "poolMin": min(sizes), "poolMax": max(sizes), "totalPairs": sum(sizes),
              "summaries": summ, "comparisons": comps, "rankings": rankings}
    atomic_write(OUT / "clean-consolidated-report.json", report)
    print(json.dumps({"poolMean": report["poolMean"], "totalPairs": report["totalPairs"],
                      "summaries": summ, "comparisons": comps}, indent=1))


def latency(n: int) -> None:
    documents, queries = test_queries()
    chosen = sorted(queries, key=lambda q: hashlib.sha256(q.id.encode()).hexdigest())[:n]
    doc_ids = [d.id for d in documents]
    text = [f"{d.title}\n{d.text}" for d in documents]
    four_ref = json.loads(FOUR.read_text())["rankings"]
    src40 = json.loads(SOURCE.read_text())["retrieval"]["rankings"]
    n_q = {q.id: len(dict.fromkeys(d for m in ("bm25", "dense", "hybrid", "openie_graphrag")
                                   for d in src40[m][q.id][:TOP_K])) for q in chosen}
    setup = {}
    t0 = time.perf_counter(); bm25 = Bm25Index([d.searchable_text for d in documents]); setup["bm25IndexS"] = time.perf_counter() - t0
    t0 = time.perf_counter(); enc = MiniLmEncoder(EMBEDDER, batch_size=1)
    vectors, _, _ = enc.encode_cached([d.searchable_text for d in documents], EMBED_CACHE); setup["denseLoadS"] = time.perf_counter() - t0
    t0 = time.perf_counter(); graph = OpenIeGraph(OPENIE, documents, max_entity_document_frequency=64); setup["graphIndexS"] = time.perf_counter() - t0
    t0 = time.perf_counter(); ce = model(); setup["crossEncoderLoadS"] = time.perf_counter() - t0
    enc.encode(["warm up"]); ce.predict([("warm up", "warm up")], batch_size=8)

    def hybrid_stage(q):
        t_e0 = time.perf_counter()
        qv = enc.encode([q.question])[0]
        t_e1 = time.perf_counter()
        lex = top_indices(bm25.scores(q.question), len(documents))
        t_l1 = time.perf_counter()
        dense_scores = vectors @ qv
        den = top_indices(dense_scores, len(documents))
        t_d1 = time.perf_counter()
        hyb = reciprocal_rank_fusion((lex, den))
        return lex, den, dense_scores, hyb, {
            "queryEmbedMs": (t_e1 - t_e0) * 1000,
            "bm25E2eMs": (t_l1 - t_e1) * 1000,
            "denseE2eMs": ((t_e1 - t_e0) + (t_d1 - t_l1)) * 1000,
        }

    def rerank(q, idx):
        pool = list(dict.fromkeys(int(i) for i in idx))
        scores = ce.predict([(q.question, text[i]) for i in pool], batch_size=8)
        return rank_from_scores([doc_ids[i] for i in pool], scores, TOP_K), len(pool)

    def run(cfg, q):
        t0 = time.perf_counter()
        lex, den, dense_scores, hyb, sub = hybrid_stage(q)
        t_src = time.perf_counter()
        if cfg == "hybrid":
            top = [doc_ids[int(i)] for i in top_indices(hyb, TOP_K)]; pool = 0
        elif cfg == "four_route_ce":
            gs = graph.propagate(dense_scores, seed_count=20)
            reached = np.flatnonzero(gs > 0)
            grank = reached[np.argsort(gs[reached], kind="stable")[::-1]]
            proxy = reciprocal_rank_fusion((den, grank))
            t_src = time.perf_counter()
            idx = [*lex[:TOP_K], *den[:TOP_K], *top_indices(hyb, TOP_K), *top_indices(proxy, TOP_K)]
            top, pool = rerank(q, idx)
        elif cfg == "hybrid_matched_ce":
            top, pool = rerank(q, top_indices(hyb, n_q[q.id]))
        else:
            top, pool = rerank(q, top_indices(hyb, 40))
        t1 = time.perf_counter()
        return {"totalMs": (t1 - t0) * 1000, "sourceMs": (t_src - t0) * 1000,
                "rerankMs": (t1 - t_src) * 1000, "pool": pool, "top10": top, **sub}

    cfgs = ["hybrid", "four_route_ce", "hybrid_matched_ce", "hybrid40_ce"]
    ckpt_path = OUT / f"e2e-latency-{n}.checkpoint.json"
    if ckpt_path.exists():
        saved = json.loads(ckpt_path.read_text())
        rows = saved["rows"]
        load = saved["load"]
    else:
        rows = {}
        load = []
    for k, q in enumerate(chosen):
        if q.id in rows:
            continue
        order = cfgs[k % 4:] + cfgs[: k % 4]
        rows[q.id] = {c: run(c, q) for c in order}
        load.append(os.getloadavg()[0])
        if (k + 1) % 5 == 0 or (k + 1) == n:
            atomic_write(ckpt_path, {"rows": rows, "load": load})
        if (k + 1) % 10 == 0 or (k + 1) == n:
            print(f"latency {k + 1}/{n}", flush=True)
    summary = {}
    for c in cfgs:
        tot = [rows[q][c]["totalMs"] for q in rows]
        summary[c] = {"medianMs": statistics.median(tot), "p95Ms": float(np.percentile(tot, 95)),
                      "meanMs": statistics.fmean(tot),
                      "sourceMedianMs": statistics.median(rows[q][c]["sourceMs"] for q in rows),
                      "rerankMedianMs": statistics.median(rows[q][c]["rerankMs"] for q in rows),
                      "meanPool": statistics.fmean(rows[q][c]["pool"] for q in rows)}
    for sub_key, out_name in (("bm25E2eMs", "bm25_from_hybrid"), ("denseE2eMs", "dense_from_hybrid"), ("queryEmbedMs", "query_embed")):
        vals = [rows[q]["hybrid"][sub_key] for q in rows]
        summary[out_name] = {
            "medianMs": statistics.median(vals),
            "p95Ms": float(np.percentile(vals, 95)),
            "meanMs": statistics.fmean(vals),
        }
    agree4 = sum(rows[q.id]["four_route_ce"]["top10"] == four_ref[q.id] for q in chosen)
    report = {"classification": "end-to-end local latency, Raspberry Pi 4", "n": n,
              "selection": f"{n} smallest SHA-256(query id) among the 600 test questions",
              "setupSeconds": setup, "loadAverage1m": {"median": statistics.median(load), "max": max(load)},
              "crossEncoder": {"batch": 8, "threads": 2, "maxLength": 512},
              "fourRouteTop10EqualsCleanReport": agree4, "summary": summary,
              "queryIds": [q.id for q in chosen], "rows": rows}
    out_file = OUT / ("e2e-latency-report.json" if n == 100 else f"e2e-latency-smoke-{n}.json")
    atomic_write(out_file, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "queryIds")}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("nonstructural", "latency"))
    ap.add_argument("--n", type=int, default=100)
    a = ap.parse_args()
    nonstructural() if a.mode == "nonstructural" else latency(a.n)
