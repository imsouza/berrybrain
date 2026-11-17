"""Evaluate internal and official rankings on a preregistered comparative split."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from comparative_split_manifest import validate_manifest as validate_split_manifest
from external_ranking_contract import load_and_validate_manifest, sha256_file
from same_corpus_rag_benchmark import (
    QueryCase,
    bootstrap_difference,
    load_musique,
    retrieval_metrics,
)

SCHEMA_VERSION = "berrybrain.comparative-retrieval.v1"
BASE_METHODS = {
    "bm25": ("bm25", "BM25", "baseline"),
    "dense": ("dense", "Dense retrieval", "baseline"),
    "hybrid": ("hybrid", "Hybrid RRF", "baseline"),
    "openie_graph_proxy": (
        "openie_graphrag",
        "OpenIE document-entity propagation proxy",
        "proxy",
    ),
    "legacy_berrybrain": (
        "berrybrain",
        "Exploratory BerryBrain fixed fusion",
        "legacy_candidate",
    ),
}


def percentile(values: Sequence[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, int(fraction * len(ordered) + 0.999999) - 1))
    return float(ordered[index])


def evaluate_rankings(
    rankings: Mapping[str, Sequence[str]],
    queries: Sequence[QueryCase],
    latencies_ms: Mapping[str, float],
) -> tuple[list[dict[str, Any]], dict[str, float]]:
    observations: list[dict[str, Any]] = []
    for query in queries:
        if query.id not in rankings:
            raise ValueError(f"Ranking missing query {query.id}")
        metrics = retrieval_metrics(rankings[query.id], query.relevant_ids)
        observations.append(
            {
                "queryId": query.id,
                "hops": query.hops,
                "latencyMs": float(latencies_ms.get(query.id, 0.0)),
                **metrics,
            }
        )
    latencies = [row["latencyMs"] for row in observations]
    summary = {
        metric: statistics.fmean(float(row[metric]) for row in observations)
        for metric in (
            "recallAt1",
            "recallAt5",
            "recallAt10",
            "mrrAt10",
            "ndcgAt10",
            "completeSupportAt10",
        )
    }
    summary["latencyMedianMs"] = statistics.median(latencies)
    summary["latencyP95Ms"] = percentile(latencies, 0.95)
    return observations, summary


def internal_latencies(
    report: Mapping[str, Any], source_method: str
) -> dict[str, float]:
    observations = report["retrieval"]["observations"][source_method]
    return {str(row["queryId"]): float(row["latencyMs"]) for row in observations}


def load_candidate_report(
    path: Path,
    *,
    source_method: str,
    candidate_method: str,
    split: str,
    expected_query_ids: set[str],
    expected_document_ids: set[str],
    corpus_sha256: str,
    queries_sha256: str,
    split_manifest_sha256: str,
    base_report_sha256: str,
    ranking_depth: int,
) -> tuple[dict[str, list[str]], dict[str, float], dict[str, str]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    protocol = payload.get("protocol")
    if not isinstance(protocol, Mapping):
        raise ValueError("Candidate report protocol is missing")
    expected_protocol = {
        "corpusSha256": corpus_sha256,
        "queriesSha256": queries_sha256,
        "splitManifestSha256": split_manifest_sha256,
        "baseReportSha256": base_report_sha256,
        "split": split,
    }
    for field, expected in expected_protocol.items():
        if str(protocol.get(field, "")) != expected:
            raise ValueError(f"Candidate report {field} does not match")
    if int(protocol.get("rankingDepth", 0)) != ranking_depth:
        raise ValueError("Candidate report ranking depth does not match")
    if str(payload.get("split", "")) != split:
        raise ValueError("Candidate report split does not match")

    raw_rankings = payload.get("rankings")
    if not isinstance(raw_rankings, Mapping):
        raise ValueError("Candidate report rankings are missing")
    if {str(query_id) for query_id in raw_rankings} != expected_query_ids:
        raise ValueError("Candidate report query coverage does not match")
    rankings: dict[str, list[str]] = {}
    for query_id, raw_document_ids in raw_rankings.items():
        if not isinstance(raw_document_ids, Sequence) or isinstance(
            raw_document_ids, (str, bytes)
        ):
            raise ValueError(f"Candidate ranking is invalid for {query_id}")
        document_ids = [str(document_id) for document_id in raw_document_ids]
        if len(document_ids) != ranking_depth:
            raise ValueError(f"Candidate ranking depth differs for {query_id}")
        if len(set(document_ids)) != len(document_ids):
            raise ValueError(f"Candidate ranking contains duplicates for {query_id}")
        unknown_ids = set(document_ids) - expected_document_ids
        if unknown_ids:
            raise ValueError(
                f"Candidate ranking contains unknown documents for {query_id}"
            )
        rankings[str(query_id)] = document_ids

    raw_observations = payload.get("observations")
    if not isinstance(raw_observations, Mapping) or not isinstance(
        raw_observations.get(source_method), Sequence
    ):
        raise ValueError("Candidate report observations are missing")
    latencies = {
        str(row["queryId"]): float(row["latencyMs"])
        for row in raw_observations[source_method]
    }
    if set(latencies) != expected_query_ids:
        raise ValueError("Candidate report latency coverage does not match")

    raw_methods = payload.get("methods")
    source_metadata = (
        raw_methods.get(source_method, {}) if isinstance(raw_methods, Mapping) else {}
    )
    display_name = str(
        source_metadata.get("displayName", "BerryBrain frozen candidate")
    )
    return (
        rankings,
        latencies,
        {
            "displayName": display_name,
            "kind": "candidate",
            "source": str(path),
            "sourceMethod": source_method,
            "candidateMethod": candidate_method,
        },
    )


def paired_comparisons(
    observations: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    candidate_method: str,
    seed: int,
    resamples: int,
) -> dict[str, dict[str, Any]]:
    candidate_by_query = {
        str(row["queryId"]): row for row in observations[candidate_method]
    }
    comparisons: dict[str, dict[str, Any]] = {}
    for method, rows in observations.items():
        if method == candidate_method:
            continue
        baseline_by_query = {str(row["queryId"]): row for row in rows}
        ordered_ids = sorted(candidate_by_query)
        if set(ordered_ids) != set(baseline_by_query):
            raise ValueError(f"Paired query coverage differs for {method}")
        comparisons[method] = {}
        for metric in ("recallAt10", "completeSupportAt10", "mrrAt10", "ndcgAt10"):
            comparisons[method][metric] = bootstrap_difference(
                [
                    float(candidate_by_query[query_id][metric])
                    for query_id in ordered_ids
                ],
                [
                    float(baseline_by_query[query_id][metric])
                    for query_id in ordered_ids
                ],
                seed=seed,
                resamples=resamples,
            )
    return comparisons


def acceptance_result(
    summaries: Mapping[str, Mapping[str, float]],
    comparisons: Mapping[str, Mapping[str, Mapping[str, float]]],
    method_metadata: Mapping[str, Mapping[str, str]],
    *,
    candidate_method: str,
) -> dict[str, Any]:
    deployable_baselines = [
        method
        for method, metadata in method_metadata.items()
        if method != candidate_method and metadata["kind"] in {"baseline", "official"}
    ]
    if not deployable_baselines:
        raise ValueError("No deployable baseline is available")
    strongest = max(
        deployable_baselines, key=lambda method: summaries[method]["recallAt10"]
    )
    recall_comparison = comparisons[strongest]["recallAt10"]
    criterion_passed = recall_comparison["lower95"] > 0
    candidate_kind = method_metadata[candidate_method]["kind"]
    return {
        "strongestDeployableBaseline": strongest,
        "candidateRecallAt10": summaries[candidate_method]["recallAt10"],
        "baselineRecallAt10": summaries[strongest]["recallAt10"],
        "meanDifference": recall_comparison["meanDifference"],
        "lower95": recall_comparison["lower95"],
        "upper95": recall_comparison["upper95"],
        "retrievalCriterionPassed": criterion_passed,
        "claimAuthorized": criterion_passed and candidate_kind != "legacy_candidate",
        "candidateKind": candidate_kind,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    base_report = json.loads(args.base_report.read_text(encoding="utf-8"))
    if base_report["inputs"]["corpus"]["sha256"] != sha256_file(args.corpus):
        raise ValueError("Base report corpus hash does not match")
    if base_report["inputs"]["queries"]["sha256"] != sha256_file(args.queries):
        raise ValueError("Base report query hash does not match")
    documents, all_queries = load_musique(args.corpus, args.queries)
    split_payload = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    splits = validate_split_manifest(
        split_payload, corpus=args.corpus, queries=args.queries
    )
    query_by_id = {query.id: query for query in all_queries}
    queries = [query_by_id[query_id] for query_id in splits[args.split]]
    ranking_depth = int(base_report["protocol"]["rankingDepth"])
    if args.split == "confirmatory" and not args.unlock_confirmatory:
        raise ValueError(
            "Confirmatory split is locked; freeze the protocol before unlocking it"
        )

    rankings: dict[str, dict[str, list[str]]] = {}
    latencies: dict[str, dict[str, float]] = {}
    metadata: dict[str, dict[str, str]] = {}
    for method, (source_method, display_name, kind) in BASE_METHODS.items():
        source_rankings = base_report["retrieval"]["rankings"][source_method]
        rankings[method] = {query.id: source_rankings[query.id] for query in queries}
        source_latencies = internal_latencies(base_report, source_method)
        latencies[method] = {query.id: source_latencies[query.id] for query in queries}
        metadata[method] = {
            "displayName": display_name,
            "kind": kind,
            "source": str(args.base_report),
        }

    expected_query_ids = {query.id for query in queries}
    expected_document_ids = {document.id for document in documents}
    candidate_report_hash: str | None = None
    if args.candidate_report is not None:
        if args.candidate_method in rankings:
            raise ValueError(f"Duplicate method ID: {args.candidate_method}")
        candidate_rankings, candidate_latencies, candidate_metadata = (
            load_candidate_report(
                args.candidate_report,
                source_method=args.candidate_source_method,
                candidate_method=args.candidate_method,
                split=args.split,
                expected_query_ids=expected_query_ids,
                expected_document_ids=expected_document_ids,
                corpus_sha256=sha256_file(args.corpus),
                queries_sha256=sha256_file(args.queries),
                split_manifest_sha256=sha256_file(args.split_manifest),
                base_report_sha256=sha256_file(args.base_report),
                ranking_depth=ranking_depth,
            )
        )
        rankings[args.candidate_method] = candidate_rankings
        latencies[args.candidate_method] = candidate_latencies
        metadata[args.candidate_method] = candidate_metadata
        candidate_report_hash = sha256_file(args.candidate_report)
    official_ids: set[str] = set()
    external_hashes: dict[str, str] = {}
    for path in args.external_ranking:
        payload, external_rankings = load_and_validate_manifest(
            path,
            expected_query_ids=expected_query_ids,
            expected_document_ids=expected_document_ids,
            corpus_sha256=sha256_file(args.corpus),
            queries_sha256=sha256_file(args.queries),
            ranking_depth=ranking_depth,
        )
        method_id = str(payload["method"]["id"])
        if method_id in rankings:
            raise ValueError(f"Duplicate method ID: {method_id}")
        rankings[method_id] = external_rankings
        latencies[method_id] = {
            query_id: float(value) for query_id, value in payload["latenciesMs"].items()
        }
        metadata[method_id] = {
            "displayName": str(payload["method"]["displayName"]),
            "kind": "official",
            "source": str(path),
            "repository": str(payload["method"]["repository"]),
            "commit": str(payload["method"]["commit"]),
        }
        official_ids.add(method_id)
        external_hashes[method_id] = sha256_file(path)
    if args.split == "confirmatory" and "official-hipporag2" not in official_ids:
        raise ValueError(
            "Confirmatory comparison requires official HippoRAG 2 rankings"
        )
    if args.candidate_method not in rankings:
        raise ValueError(f"Candidate method is unavailable: {args.candidate_method}")

    observations: dict[str, list[dict[str, Any]]] = {}
    summaries: dict[str, dict[str, float]] = {}
    for method in rankings:
        observations[method], summaries[method] = evaluate_rankings(
            rankings[method], queries, latencies[method]
        )
    comparisons = paired_comparisons(
        observations,
        candidate_method=args.candidate_method,
        seed=args.bootstrap_seed,
        resamples=args.bootstrap_resamples,
    )
    acceptance = acceptance_result(
        summaries,
        comparisons,
        metadata,
        candidate_method=args.candidate_method,
    )
    if args.candidate_method == "legacy_berrybrain":
        acceptance["reason"] = (
            "Legacy fixed fusion is exploratory and not runtime parity."
        )
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "status": "completed",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": "confirmatory"
        if args.split == "confirmatory"
        else "developmental",
        "split": args.split,
        "candidateMethod": args.candidate_method,
        "protocol": {
            "queryCount": len(queries),
            "rankingDepth": ranking_depth,
            "bootstrapSeed": args.bootstrap_seed,
            "bootstrapResamples": args.bootstrap_resamples,
            "oracleAccess": False,
        },
        "inputs": {
            "corpusSha256": sha256_file(args.corpus),
            "queriesSha256": sha256_file(args.queries),
            "baseReportSha256": sha256_file(args.base_report),
            "splitManifestSha256": sha256_file(args.split_manifest),
            "externalManifestSha256": external_hashes,
            "candidateReportSha256": candidate_report_hash,
        },
        "methods": metadata,
        "summaries": summaries,
        "observations": observations,
        "pairedBootstrap": comparisons,
        "acceptance": acceptance,
        "limitations": [
            "The OpenIE graph condition is a proxy, not Microsoft GraphRAG or HippoRAG 2.",
            "The legacy BerryBrain condition uses historical fixed fusion and cannot authorize a product superiority claim.",
            "Retrieval quality does not establish generated-answer quality or human-workflow benefit.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument(
        "--split",
        choices=("development", "validation", "confirmatory"),
        required=True,
    )
    parser.add_argument("--external-ranking", type=Path, action="append", default=[])
    parser.add_argument("--candidate-report", type=Path)
    parser.add_argument("--candidate-source-method", default="semantic_rerank")
    parser.add_argument("--candidate-method", default="legacy_berrybrain")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap-seed", type=int, default=20260829)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    parser.add_argument("--unlock-confirmatory", action="store_true")
    return parser.parse_args()


def main() -> int:
    report = run(parse_args())
    print(json.dumps({"split": report["split"], "acceptance": report["acceptance"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
