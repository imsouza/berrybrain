"""End-to-end single-query local latency for BerryBrain-Rerank_Title on Raspberry Pi 4 (P5).

Measures the exact same 100 hash-selected MuSiQue test questions as
clean-rerun/e2e-latency-report.json (musique_clean_controls.py mode=latency),
replacing OpenIeGraph with TitleMentionGraph so that Table 10 (tab:latency)
and §5.3 report measured single-query latency for BerryBrain-Rerank_Title
alongside BerryBrain-Rerank_OIE.
"""

from __future__ import annotations

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
sys.path.insert(0, str(ROOT))

from same_corpus_rag_benchmark import (  # noqa: E402
    Bm25Index,
    MiniLmEncoder,
    load_musique,
    reciprocal_rank_fusion,
    top_indices,
)
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores  # noqa: E402
from external_2wiki_retrieval import TitleMentionGraph  # noqa: E402
from musique_clean_controls import (  # noqa: E402
    CORPUS,
    CROSS_ENCODER,
    EMBED_CACHE,
    EMBEDDER,
    OUT,
    QUESTIONS,
    SPLIT,
    TOKENIZER,
    TOP_K,
)

E2E_REF = OUT / "e2e-latency-report.json"
TITLE_2X2_REF = OUT / "musique-title-2x2-report.json"
CKPT = OUT / "e2e-title-latency-100.checkpoint.json"
REPORT_OUT = OUT / "e2e-title-latency-report.json"


def main() -> None:
    documents, all_queries = load_musique(CORPUS, QUESTIONS)
    split = json.loads(SPLIT.read_text(encoding="utf-8"))["splits"]["confirmatory"]
    by_id = {q.id: q for q in all_queries}
    queries = [by_id[i] for i in split]
    chosen = sorted(queries, key=lambda q: hashlib.sha256(q.id.encode()).hexdigest())[:100]

    e2e_ref = json.loads(E2E_REF.read_text(encoding="utf-8"))
    assert [q.id for q in chosen] == e2e_ref["queryIds"]
    title_ref = json.loads(TITLE_2X2_REF.read_text(encoding="utf-8"))["rankings"]["four_route_title_ce"]

    doc_ids = [d.id for d in documents]
    text = [f"{d.title}\n{d.text}" for d in documents]

    setup = {}
    t0 = time.perf_counter()
    bm25 = Bm25Index([d.searchable_text for d in documents])
    setup["bm25IndexS"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    enc = MiniLmEncoder(EMBEDDER, batch_size=1)
    vectors, _, _ = enc.encode_cached([d.searchable_text for d in documents], EMBED_CACHE)
    setup["denseLoadS"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    graph = TitleMentionGraph(documents)
    setup["titleGraphIndexS"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    ce = OnnxCrossEncoder(
        model_path=CROSS_ENCODER,
        tokenizer_name=str(TOKENIZER),
        revision=None,
        max_length=512,
        intra_op_threads=2,
    )
    setup["crossEncoderLoadS"] = time.perf_counter() - t0

    enc.encode(["warm up"])
    ce.predict([("warm up", "warm up")], batch_size=8)

    if CKPT.exists():
        saved = json.loads(CKPT.read_text(encoding="utf-8"))
        rows = saved["rows"]
        load = saved["load"]
    else:
        rows = {}
        load = []

    for k, q in enumerate(chosen):
        if q.id in rows:
            continue
        t_start = time.perf_counter()
        t_e0 = time.perf_counter()
        qv = enc.encode([q.question])[0]
        t_e1 = time.perf_counter()
        lex = top_indices(bm25.scores(q.question), len(documents))
        t_l1 = time.perf_counter()
        dense_scores = vectors @ qv
        den = top_indices(dense_scores, len(documents))
        t_d1 = time.perf_counter()
        hyb = reciprocal_rank_fusion((lex, den))
        gs = graph.propagate(dense_scores)
        reached = np.flatnonzero(gs > 0)
        grank = reached[np.argsort(gs[reached], kind="stable")[::-1]]
        proxy = reciprocal_rank_fusion((den, grank))
        t_src = time.perf_counter()

        idx = [*lex[:TOP_K], *den[:TOP_K], *top_indices(hyb, TOP_K), *top_indices(proxy, TOP_K)]
        pool = list(dict.fromkeys(int(i) for i in idx))
        scores = ce.predict([(q.question, text[i]) for i in pool], batch_size=8)
        top = rank_from_scores([doc_ids[i] for i in pool], scores, TOP_K)
        t_end = time.perf_counter()

        rows[q.id] = {
            "totalMs": (t_end - t_start) * 1000,
            "sourceMs": (t_src - t_start) * 1000,
            "rerankMs": (t_end - t_src) * 1000,
            "queryEmbedMs": (t_e1 - t_e0) * 1000,
            "bm25E2eMs": (t_l1 - t_e1) * 1000,
            "denseE2eMs": ((t_e1 - t_e0) + (t_d1 - t_l1)) * 1000,
            "titleGraphPropagateAndFuseMs": (t_src - t_d1) * 1000,
            "pool": len(pool),
            "top10": top,
        }
        load.append(os.getloadavg()[0])
        if (k + 1) % 10 == 0 or (k + 1) == len(chosen):
            atomic_write(CKPT, {"rows": rows, "load": load})
            print(f"title-latency {k + 1}/{len(chosen)}", flush=True)

    tot = [rows[q.id]["totalMs"] for q in chosen]
    src = [rows[q.id]["sourceMs"] for q in chosen]
    rer = [rows[q.id]["rerankMs"] for q in chosen]
    gprop = [rows[q.id]["titleGraphPropagateAndFuseMs"] for q in chosen]
    pools = [rows[q.id]["pool"] for q in chosen]
    agree = sum(rows[q.id]["top10"] == title_ref[q.id] for q in chosen)

    summary = {
        "four_route_title_ce": {
            "medianMs": statistics.median(tot),
            "p95Ms": float(np.percentile(tot, 95)),
            "meanMs": statistics.fmean(tot),
            "sourceMedianMs": statistics.median(src),
            "sourceP95Ms": float(np.percentile(src, 95)),
            "rerankMedianMs": statistics.median(rer),
            "rerankP95Ms": float(np.percentile(rer, 95)),
            "titleGraphStageMedianMs": statistics.median(gprop),
            "titleGraphStageP95Ms": float(np.percentile(gprop, 95)),
            "meanPool": statistics.fmean(pools),
            "medianPool": statistics.median(pools),
        }
    }
    report = {
        "classification": "end-to-end local latency for BerryBrain-Rerank_Title, Raspberry Pi 4",
        "n": len(chosen),
        "selection": "identical 100 smallest SHA-256(query id) test questions as e2e-latency-report.json",
        "setupSeconds": setup,
        "graphStats": graph.stats,
        "loadAverage1m": {"median": statistics.median(load), "max": max(load)},
        "crossEncoder": {"batch": 8, "threads": 2, "maxLength": 512},
        "fourRouteTitleTop10Equals2x2Report": agree,
        "summary": summary,
        "queryIds": [q.id for q in chosen],
        "rows": rows,
    }
    atomic_write(REPORT_OUT, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ("rows", "queryIds")}, indent=2))


if __name__ == "__main__":
    main()
