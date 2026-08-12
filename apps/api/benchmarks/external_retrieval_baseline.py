from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from benchmarks.evidence import create_manifest, percentile, write_evidence_bundle

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class ExternalBaselineMetrics:
    method: str
    query_count: int
    recall_at_10: float
    mean_reciprocal_rank: float
    ndcg_at_10: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number} must contain a JSON object")
        rows.append(value)
    return rows


def _tokens(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.casefold())


def _bm25_scores(corpus: list[dict[str, Any]], query: str) -> dict[str, float]:
    tokenized = [_tokens(str(item["text"])) for item in corpus]
    average_length = statistics.fmean(len(tokens) for tokens in tokenized) or 1.0
    document_frequency: Counter[str] = Counter()
    for tokens in tokenized:
        document_frequency.update(set(tokens))
    query_tokens = _tokens(query)
    scores: dict[str, float] = {}
    for item, tokens in zip(corpus, tokenized, strict=True):
        frequencies = Counter(tokens)
        score = 0.0
        for token in query_tokens:
            frequency = frequencies[token]
            if not frequency:
                continue
            inverse_frequency = math.log(
                1
                + (len(corpus) - document_frequency[token] + 0.5)
                / (document_frequency[token] + 0.5)
            )
            denominator = frequency + 1.5 * (
                1 - 0.75 + 0.75 * len(tokens) / average_length
            )
            score += inverse_frequency * frequency * 2.5 / denominator
        scores[str(item["id"])] = score
    return scores


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("embedding dimensions must match and be non-empty")
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    return (
        sum(a * b for a, b in zip(left, right, strict=True)) / denominator
        if denominator
        else 0.0
    )


def _dense_scores(
    corpus: list[dict[str, Any]], query: dict[str, Any]
) -> dict[str, float]:
    query_embedding = query.get("embedding")
    if not isinstance(query_embedding, list):
        raise ValueError("dense and hybrid baselines require query embeddings")
    scores: dict[str, float] = {}
    for item in corpus:
        embedding = item.get("embedding")
        if not isinstance(embedding, list):
            raise ValueError("dense and hybrid baselines require corpus embeddings")
        scores[str(item["id"])] = _cosine(query_embedding, embedding)
    return scores


def _rank(scores: dict[str, float]) -> list[str]:
    return sorted(scores, key=lambda key: (-scores[key], key))


def _rrf(rankings: list[list[str]], constant: int = 60) -> list[str]:
    scores: defaultdict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, identifier in enumerate(ranking, 1):
            scores[identifier] += 1 / (constant + rank)
    return _rank(dict(scores))


def _metrics(
    ranking: list[str], relevant: dict[str, int], limit: int = 10
) -> tuple[float, float, float]:
    relevant_ids = {key for key, value in relevant.items() if value > 0}
    recall = (
        len(set(ranking[:limit]) & relevant_ids) / len(relevant_ids)
        if relevant_ids
        else 1.0
    )
    reciprocal_rank = next(
        (
            1 / rank
            for rank, identifier in enumerate(ranking, 1)
            if identifier in relevant_ids
        ),
        0.0,
    )
    gains = [relevant.get(identifier, 0) for identifier in ranking[:limit]]
    dcg = sum((2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(gains, 1))
    ideal = sorted(relevant.values(), reverse=True)[:limit]
    ideal_dcg = sum(
        (2**gain - 1) / math.log2(rank + 1) for rank, gain in enumerate(ideal, 1)
    )
    return recall, reciprocal_rank, dcg / ideal_dcg if ideal_dcg else 1.0


def run_external_baseline(
    corpus_path: Path,
    queries_path: Path,
    qrels_path: Path,
    *,
    method: str,
) -> tuple[ExternalBaselineMetrics, list[dict[str, Any]]]:
    if method not in {"bm25", "dense", "hybrid"}:
        raise ValueError(f"unsupported baseline method: {method}")
    corpus = _read_jsonl(corpus_path)
    queries = _read_jsonl(queries_path)
    qrels_rows = _read_jsonl(qrels_path)
    if not corpus or not queries or not qrels_rows:
        raise ValueError("corpus, queries, and qrels must be non-empty")
    qrels: defaultdict[str, dict[str, int]] = defaultdict(dict)
    for row in qrels_rows:
        qrels[str(row["query_id"])][str(row["document_id"])] = int(row["relevance"])

    observations: list[dict[str, Any]] = []
    for query in queries:
        query_id = str(query["id"])
        if query_id not in qrels:
            raise ValueError(f"query {query_id} has no qrels")
        started = time.perf_counter()
        lexical = _rank(_bm25_scores(corpus, str(query["text"])))
        if method == "bm25":
            ranking = lexical
        else:
            dense = _rank(_dense_scores(corpus, query))
            ranking = dense if method == "dense" else _rrf([lexical, dense])
        latency_ms = (time.perf_counter() - started) * 1000
        recall, reciprocal_rank, ndcg = _metrics(ranking, qrels[query_id])
        observations.append(
            {
                "benchmark": "external-retrieval-baseline",
                "method": method,
                "queryId": query_id,
                "recallAt10": recall,
                "reciprocalRank": reciprocal_rank,
                "ndcgAt10": ndcg,
                "latencyMs": latency_ms,
                "resultIds": ranking[:10],
            }
        )
    latencies = [float(item["latencyMs"]) for item in observations]
    metrics = ExternalBaselineMetrics(
        method=method,
        query_count=len(observations),
        recall_at_10=statistics.fmean(
            float(item["recallAt10"]) for item in observations
        ),
        mean_reciprocal_rank=statistics.fmean(
            float(item["reciprocalRank"]) for item in observations
        ),
        ndcg_at_10=statistics.fmean(float(item["ndcgAt10"]) for item in observations),
        latency_p50_ms=percentile(latencies, 0.50),
        latency_p95_ms=percentile(latencies, 0.95),
        latency_p99_ms=percentile(latencies, 0.99),
    )
    return metrics, observations


def main() -> int:
    parser = argparse.ArgumentParser(description="Run independent retrieval baselines.")
    parser.add_argument("--corpus", required=True)
    parser.add_argument("--queries", required=True)
    parser.add_argument("--qrels", required=True)
    parser.add_argument("--method", choices=("bm25", "dense", "hybrid"), required=True)
    parser.add_argument("--output", default="reports/external-retrieval-baseline.json")
    parser.add_argument("--evidence-root", default="")
    args = parser.parse_args()
    paths = [Path(args.corpus), Path(args.queries), Path(args.qrels)]
    metrics, observations = run_external_baseline(*paths, method=args.method)
    summary = asdict(metrics)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    if args.evidence_root:
        manifest = create_manifest(
            "external-retrieval-baseline",
            dataset={"files": [str(path) for path in paths]},
            configuration={"method": args.method, "topK": 10, "rrfConstant": 60},
        )
        write_evidence_bundle(
            Path(args.evidence_root),
            manifest,
            summary=summary,
            observations=observations,
        )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
