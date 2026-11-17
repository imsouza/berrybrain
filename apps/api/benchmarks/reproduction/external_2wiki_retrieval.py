"""Exploratory 2Wiki retrieval with frozen local models and checkpointed scores.

The graph route is a title-mention proxy built only from corpus text. It is
deliberately labeled as different from the MuSiQue OpenIE route.
"""

from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import ahocorasick
import numpy as np

ROOT = Path(__file__).resolve().parent
REPO = Path("/mnt/HDD_1/Antigravity/berrybrain")
sys.path.insert(0, str(REPO / "apps/api/benchmarks"))

from comparative_retrieval_benchmark import evaluate_rankings, paired_comparisons  # noqa: E402
from same_corpus_rag_benchmark import (  # noqa: E402
    Bm25Index,
    CorpusDocument,
    MiniLmEncoder,
    QueryCase,
    reciprocal_rank_fusion,
    sha256_file,
    stable_document_id,
    top_indices,
)
from semantic_rerank_benchmark import (  # noqa: E402
    OnnxCrossEncoder,
    atomic_write,
    candidate_pool,
    rank_from_scores,
)

DATA = ROOT / "external-corpus"
CORPUS = DATA / "2wikimultihopqa_corpus.json"
QUESTIONS = DATA / "2wikimultihopqa.json"
EMBEDDER = REPO / ".benchmark-cache/models/all-MiniLM-L6-v2"
CROSS_ENCODER = REPO / ".benchmark-cache/onnx-crossencoder/model.int8.onnx"
TOKENIZER = REPO / ".benchmark-cache/huggingface/hub/models--cross-encoder--ms-marco-MiniLM-L-6-v2/snapshots/233902d25c440f23af6f7d6e94d2946bac0bee0a"
EMBED_CACHE = DATA / "2wiki-minilm-embeddings.npy"
SOURCE_CHECKPOINT = DATA / "2wiki-source-rankings.checkpoint.json"
SCORE_CHECKPOINT = DATA / "2wiki-crossencoder.checkpoint.json"
OUTPUT = DATA / "2wiki-retrieval-report.json"
SELECTED_COUNT = 200
TOP_K = 10
RRF_K = 60
GRAPH_SEEDS = 20
MAX_ENTITY_DF = 64


def fingerprint() -> dict[str, object]:
    return {
        "scriptSha256": sha256_file(Path(__file__)),
        "corpusSha256": sha256_file(CORPUS),
        "questionsSha256": sha256_file(QUESTIONS),
        "embedderSha256": sha256_file(EMBEDDER / "onnx/model_qint8_arm64.onnx"),
        "crossEncoderSha256": sha256_file(CROSS_ENCODER),
        "tokenizerRevision": TOKENIZER.name,
        "selectedCount": SELECTED_COUNT,
        "sourceDepth": TOP_K,
        "rrfK": RRF_K,
        "graphSeeds": GRAPH_SEEDS,
        "maxEntityDf": MAX_ENTITY_DF,
        "crossEncoderMaxLength": 512,
        "crossEncoderBatch": 8,
        "crossEncoderThreads": 2,
    }


def load_data() -> tuple[list[CorpusDocument], list[QueryCase]]:
    corpus_raw = json.loads(CORPUS.read_text(encoding="utf-8"))
    questions_raw = json.loads(QUESTIONS.read_text(encoding="utf-8"))
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
    ids = [str(row["_id"]) for row in questions_raw]
    if len(ids) != len(set(ids)):
        raise ValueError("Question IDs are not unique")
    chosen = sorted(
        questions_raw,
        key=lambda row: (hashlib.sha256(str(row["_id"]).encode()).hexdigest(), str(row["_id"])),
    )[:SELECTED_COUNT]
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
    if len(queries) != SELECTED_COUNT or any(not q.relevant_ids for q in queries):
        raise ValueError("Selected question coverage is incomplete")
    return documents, queries


class TitleMentionGraph:
    def __init__(self, documents: list[CorpusDocument]) -> None:
        automaton = ahocorasick.Automaton()
        for item in documents:
            title = item.title.strip().casefold()
            if len(title) >= 4 and title not in automaton:
                automaton.add_word(title, title)
        automaton.make_automaton()
        self.document_entities: list[set[str]] = []
        entity_documents: dict[str, set[int]] = defaultdict(set)
        for index, item in enumerate(documents):
            body = f"{item.title}. {item.text}".casefold()
            entities: set[str] = set()
            for ending, title in automaton.iter(body):
                start = ending - len(title) + 1
                if (start == 0 or not body[start - 1].isalnum()) and (
                    ending + 1 == len(body) or not body[ending + 1].isalnum()
                ):
                    entities.add(title)
            self.document_entities.append(entities)
            for title in entities:
                entity_documents[title].add(index)
        retained = {
            title: sorted(indices)
            for title, indices in entity_documents.items()
            if 2 <= len(indices) <= MAX_ENTITY_DF
        }
        self.document_entities = [items.intersection(retained) for items in self.document_entities]
        self.entity_documents = retained
        count = len(documents)
        self.entity_weight = {
            title: math.log((count + 1.0) / (len(indices) + 1.0)) + 1.0
            for title, indices in retained.items()
        }
        self.stats = {
            "distinctRetainedTitles": len(retained),
            "documentMentionPairs": sum(len(items) for items in self.document_entities),
        }

    def propagate(self, seed_scores: np.ndarray) -> np.ndarray:
        graph_scores = np.zeros_like(seed_scores, dtype=np.float32)
        count = min(GRAPH_SEEDS, len(seed_scores))
        if count == 0:
            return graph_scores
        seed_indices = np.argpartition(seed_scores, -count)[-count:]
        for seed_index in seed_indices:
            seed_score = max(0.0, float(seed_scores[seed_index]))
            for title in self.document_entities[int(seed_index)]:
                targets = self.entity_documents[title]
                contribution = seed_score * self.entity_weight[title] / len(targets)
                for target in targets:
                    if target != seed_index:
                        graph_scores[target] += contribution
        return graph_scores


def load_checkpoint(path: Path, fp: dict[str, object], name: str) -> dict[str, object]:
    if path.exists():
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("fingerprint") != fp:
            raise ValueError(f"{name} checkpoint fingerprint differs")
        return payload
    return {"fingerprint": fp, "rows": {}}


def source_rankings(documents: list[CorpusDocument], queries: list[QueryCase], fp: dict[str, object]) -> dict[str, object]:
    checkpoint = load_checkpoint(SOURCE_CHECKPOINT, fp, "source")
    rows: dict[str, object] = checkpoint["rows"]  # type: ignore[assignment]
    if len(rows) == len(queries):
        return checkpoint
    bm25 = Bm25Index([item.searchable_text for item in documents])
    encoder = MiniLmEncoder(EMBEDDER, batch_size=16)
    vectors, _, _ = encoder.encode_cached([item.searchable_text for item in documents], EMBED_CACHE)
    query_vectors = encoder.encode([item.question for item in queries])
    encoder.close()
    graph = TitleMentionGraph(documents)
    checkpoint["graphStats"] = graph.stats
    doc_ids = [item.id for item in documents]
    for query_index, query in enumerate(queries):
        if query.id in rows:
            continue
        started = time.perf_counter()
        lexical = bm25.scores(query.question)
        dense = vectors @ query_vectors[query_index]
        lexical_rank = top_indices(lexical, len(documents))
        dense_rank = top_indices(dense, len(documents))
        hybrid = reciprocal_rank_fusion((lexical_rank, dense_rank), constant=RRF_K)
        graph_scores = graph.propagate(dense)
        reached = np.flatnonzero(graph_scores > 0)
        graph_rank = reached[np.argsort(graph_scores[reached], kind="stable")[::-1]]
        graph_proxy = reciprocal_rank_fusion((dense_rank, graph_rank), constant=RRF_K)
        ranks = {
            "bm25": lexical_rank,
            "dense": dense_rank,
            "hybrid": top_indices(hybrid, TOP_K),
            "graph_proxy": top_indices(graph_proxy, TOP_K),
        }
        rows[query.id] = {
            "rankings": {
                method: [doc_ids[int(index)] for index in rank[:TOP_K]]
                for method, rank in ranks.items()
            },
            "sourceMs": (time.perf_counter() - started) * 1000,
        }
        if len(rows) % 20 == 0:
            atomic_write(SOURCE_CHECKPOINT, checkpoint)
            print(f"source {len(rows)}/{len(queries)}", flush=True)
    atomic_write(SOURCE_CHECKPOINT, checkpoint)
    return checkpoint


def rerank(documents: list[CorpusDocument], queries: list[QueryCase], source: dict[str, object], fp: dict[str, object]) -> dict[str, object]:
    checkpoint = load_checkpoint(SCORE_CHECKPOINT, fp, "cross-encoder")
    rows: dict[str, object] = checkpoint["rows"]  # type: ignore[assignment]
    by_id = {item.id: item for item in documents}
    source_rows = source["rows"]
    if len(rows) == len(queries):
        return checkpoint
    model = OnnxCrossEncoder(
        model_path=CROSS_ENCODER,
        tokenizer_name=str(TOKENIZER),
        revision=None,
        max_length=512,
        intra_op_threads=2,
    )
    pending = [query for query in queries if query.id not in rows]
    for offset in range(0, len(pending), 8):
        batch = pending[offset : offset + 8]
        pools = [
            candidate_pool(
                {method: {query.id: source_rows[query.id]["rankings"][method]} for method in ("bm25", "dense", "hybrid", "graph_proxy")},
                query.id,
                ("bm25", "dense", "hybrid", "graph_proxy"),
            )
            for query in batch
        ]
        pairs = [
            (query.question, f"{by_id[item].title}\n{by_id[item].text}")
            for query, pool in zip(batch, pools, strict=True)
            for item in pool
        ]
        started = time.perf_counter()
        scores = model.predict(pairs, batch_size=8)
        elapsed_ms = (time.perf_counter() - started) * 1000
        cursor = 0
        for query, pool in zip(batch, pools, strict=True):
            row_scores = scores[cursor : cursor + len(pool)]
            cursor += len(pool)
            rows[query.id] = {
                "pool": pool,
                "scores": row_scores,
                "modelPredictMs": elapsed_ms * len(pool) / len(pairs),
            }
        atomic_write(SCORE_CHECKPOINT, checkpoint)
        print(f"rerank {len(rows)}/{len(queries)}", flush=True)
    return checkpoint


def summarize(queries: list[QueryCase], source: dict[str, object], score: dict[str, object], fp: dict[str, object]) -> None:
    source_rows = source["rows"]
    score_rows = score["rows"]
    rankings = {method: {} for method in ("bm25", "dense", "hybrid", "graph_proxy", "nonstructural_ce", "berrybrain_rerank")}
    latencies = {method: {} for method in rankings}
    pool_sizes = []
    for query in queries:
        item = source_rows[query.id]
        scored = score_rows[query.id]
        for method in ("bm25", "dense", "hybrid", "graph_proxy"):
            rankings[method][query.id] = item["rankings"][method]
            latencies[method][query.id] = item["sourceMs"]
        pool = scored["pool"]
        pool_sizes.append(len(pool))
        scores = dict(zip(pool, scored["scores"], strict=True))
        nonstructural = list(dict.fromkeys(
            doc for method in ("bm25", "dense", "hybrid") for doc in item["rankings"][method]
        ))
        rankings["nonstructural_ce"][query.id] = rank_from_scores(
            nonstructural, [scores[doc] for doc in nonstructural], TOP_K
        )
        rankings["berrybrain_rerank"][query.id] = rank_from_scores(
            pool, scored["scores"], TOP_K
        )
        latencies["nonstructural_ce"][query.id] = scored["modelPredictMs"]
        latencies["berrybrain_rerank"][query.id] = scored["modelPredictMs"]
    observations, summaries = {}, {}
    for method in rankings:
        observations[method], summaries[method] = evaluate_rankings(
            rankings[method], queries, latencies[method]
        )
    comparisons = {
        "fullMinusHybrid": paired_comparisons(
            {"hybrid": observations["hybrid"], "berrybrain_rerank": observations["berrybrain_rerank"]},
            candidate_method="berrybrain_rerank", seed=20261023, resamples=10000,
        )["hybrid"],
        "fullMinusNonstructural": paired_comparisons(
            {"nonstructural_ce": observations["nonstructural_ce"], "berrybrain_rerank": observations["berrybrain_rerank"]},
            candidate_method="berrybrain_rerank", seed=20261023, resamples=10000,
        )["nonstructural_ce"],
    }
    result = {
        "classification": "exploratory external-corpus replication with title-mention graph proxy",
        "fingerprint": fp,
        "queryCount": len(queries),
        "documentCount": 6119,
        "graphStats": source.get("graphStats"),
        "pool": {
            "pairs": sum(pool_sizes),
            "mean": statistics.fmean(pool_sizes),
            "median": statistics.median(pool_sizes),
            "minimum": min(pool_sizes),
            "maximum": max(pool_sizes),
        },
        "queryIds": [query.id for query in queries],
        "rankings": rankings,
        "summaries": summaries,
        "comparisons": comparisons,
        "limitations": [
            "The structural route uses a deterministic title-mention graph proxy, not MuSiQue OpenIE.",
            "The same test corpus was available before this exploratory protocol was written; selection is by question ID hash without using answers.",
            "Model-prediction latency excludes source retrieval and is allocated from batch time.",
        ],
    }
    atomic_write(OUTPUT, result)
    print(json.dumps({"status": "complete", "summaries": summaries}), flush=True)


def main() -> None:
    fp = fingerprint()
    documents, queries = load_data()
    source = source_rankings(documents, queries, fp)
    score = rerank(documents, queries, source, fp)
    summarize(queries, source, score, fp)


if __name__ == "__main__":
    main()
