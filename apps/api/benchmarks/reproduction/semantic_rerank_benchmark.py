"""Evaluate a pinned cross-encoder over a fixed multi-route retrieval pool."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from comparative_retrieval_benchmark import (
    acceptance_result,
    evaluate_rankings,
    internal_latencies,
    paired_comparisons,
)
from comparative_split_manifest import (
    duplicate_question_audit,
)
from comparative_split_manifest import (
    validate_manifest as validate_split_manifest,
)
from same_corpus_rag_benchmark import load_musique, sha256_file

SCHEMA_VERSION = "berrybrain.semantic-rerank.v1"
CANDIDATE_METHOD = "semantic_rerank"
DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_REVISION = "233902d25c440f23af6f7d6e94d2946bac0bee0a"
SOURCE_METHODS = ("bm25", "dense", "hybrid", "openie_graphrag")
FINAL_FUSION_MODES = (
    "semantic",
    "semantic_hybrid_rrf",
    "semantic_hybrid_reserve",
)
INFERENCE_BACKENDS = ("pytorch", "onnx")
RETRIEVAL_METRICS = (
    "recallAt1",
    "recallAt5",
    "recallAt10",
    "mrrAt10",
    "ndcgAt10",
    "completeSupportAt10",
)


def candidate_pool(
    rankings: Mapping[str, Mapping[str, Sequence[str]]],
    query_id: str,
    source_methods: Sequence[str],
) -> list[str]:
    pool: list[str] = []
    seen: set[str] = set()
    for method in source_methods:
        if method not in rankings or query_id not in rankings[method]:
            raise ValueError(f"Missing source ranking for {method}:{query_id}")
        for document_id in rankings[method][query_id]:
            if document_id not in seen:
                seen.add(document_id)
                pool.append(document_id)
    return pool


def rank_from_scores(
    document_ids: Sequence[str], scores: Sequence[float], depth: int
) -> list[str]:
    if depth < 1:
        raise ValueError("Ranking depth must be positive")
    if len(document_ids) != len(scores):
        raise ValueError("Document and score counts differ")
    return [
        document_id
        for _, _, document_id in sorted(
            (
                (float(score), -position, document_id)
                for position, (document_id, score) in enumerate(
                    zip(document_ids, scores, strict=True)
                )
            ),
            reverse=True,
        )[:depth]
    ]


def reciprocal_rank_fusion(
    rankings: Sequence[Sequence[str]], depth: int, rank_constant: int
) -> list[str]:
    if depth < 1 or rank_constant < 1:
        raise ValueError("RRF depth and rank constant must be positive")
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    order = 0
    for ranking in rankings:
        for rank, document_id in enumerate(ranking, start=1):
            first_seen.setdefault(document_id, order)
            order += 1
            scores[document_id] = scores.get(document_id, 0.0) + 1.0 / (
                rank_constant + rank
            )
    return [
        document_id
        for document_id, _ in sorted(
            scores.items(),
            key=lambda item: (-item[1], first_seen[item[0]], item[0]),
        )[:depth]
    ]


def final_candidate_rankings(
    semantic_rankings: Mapping[str, Sequence[str]],
    hybrid_rankings: Mapping[str, Sequence[str]],
    *,
    mode: str,
    depth: int,
    rank_constant: int,
    hybrid_reserve: int = 1,
) -> dict[str, list[str]]:
    if mode not in FINAL_FUSION_MODES:
        raise ValueError(f"Unsupported final fusion mode: {mode}")
    if mode == "semantic":
        return {
            query_id: list(ranking[:depth])
            for query_id, ranking in semantic_rankings.items()
        }
    if mode == "semantic_hybrid_reserve":
        if hybrid_reserve < 1 or hybrid_reserve >= depth:
            raise ValueError("Hybrid reserve must be between one and depth minus one")
        result: dict[str, list[str]] = {}
        retained_count = depth - hybrid_reserve
        for query_id, ranking in semantic_rankings.items():
            retained = list(ranking[:retained_count])
            additions = [
                document_id
                for document_id in hybrid_rankings[query_id]
                if document_id not in retained
            ][:hybrid_reserve]
            fallback = [
                document_id
                for document_id in ranking[retained_count:]
                if document_id not in retained and document_id not in additions
            ]
            result[query_id] = (retained + additions + fallback)[:depth]
        return result
    return {
        query_id: reciprocal_rank_fusion(
            [ranking, hybrid_rankings[query_id]], depth, rank_constant
        )
        for query_id, ranking in semantic_rankings.items()
    }


def constrain_ranking_to_routes(
    ranking: Sequence[str],
    source_rankings: Mapping[str, Mapping[str, Sequence[str]]],
    query_id: str,
    allowed_methods: Sequence[str],
    depth: int,
) -> list[str]:
    allowed = candidate_pool(source_rankings, query_id, allowed_methods)
    allowed_set = set(allowed)
    retained = [document_id for document_id in ranking if document_id in allowed_set]
    return (retained + [item for item in allowed if item not in retained])[:depth]


def summarize_by_hops(
    observations: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    result: dict[str, dict[str, dict[str, float | int]]] = {}
    for method, rows in observations.items():
        groups: dict[int, list[Mapping[str, Any]]] = {}
        for row in rows:
            groups.setdefault(int(row["hops"]), []).append(row)
        result[method] = {}
        for hops, group in sorted(groups.items()):
            latencies = sorted(float(row["latencyMs"]) for row in group)
            p95_index = min(
                len(latencies) - 1, max(0, int(0.95 * len(latencies) + 0.999999) - 1)
            )
            result[method][str(hops)] = {
                "queries": len(group),
                **{
                    metric: statistics.fmean(float(row[metric]) for row in group)
                    for metric in RETRIEVAL_METRICS
                },
                "latencyMedianMs": statistics.median(latencies),
                "latencyP95Ms": latencies[p95_index],
            }
    return result


def atomic_write(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class OnnxCrossEncoder:
    def __init__(
        self,
        *,
        model_path: Path,
        tokenizer_name: str,
        revision: str | None,
        max_length: int,
        intra_op_threads: int,
    ) -> None:
        import onnxruntime as ort
        from transformers import AutoTokenizer

        options = ort.SessionOptions()
        options.intra_op_num_threads = intra_op_threads
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        options.enable_mem_pattern = False
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(
            str(model_path),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self.input_names = {item.name for item in self.session.get_inputs()}
        self.tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_name,
            revision=revision,
            local_files_only=Path(tokenizer_name).exists(),
        )
        self.max_length = max_length

    def predict(
        self,
        pairs: Sequence[tuple[str, str]],
        *,
        batch_size: int,
        show_progress_bar: bool = False,
    ) -> list[float]:
        del show_progress_bar
        scores: list[float] = []
        for offset in range(0, len(pairs), batch_size):
            batch = pairs[offset : offset + batch_size]
            encoded = self.tokenizer(
                [item[0] for item in batch],
                [item[1] for item in batch],
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="np",
            )
            inputs = {
                key: value for key, value in encoded.items() if key in self.input_names
            }
            logits = self.session.run(["logits"], inputs)[0]
            scores.extend(float(item[0]) for item in logits)
        return scores


def render_markdown(report: Mapping[str, Any]) -> str:
    protocol = report["protocol"]
    candidate_policy = report.get("candidatePolicy") or {}
    lines = [
        "# BerryBrain Semantic Rerank Benchmark",
        "",
        f"- Classification: **{report['classification']}**",
        f"- Split: `{report['split']}`",
        f"- Model: `{protocol['model']}`",
        f"- Revision: `{protocol['revision']}`",
        f"- Candidate routes: {', '.join(protocol['sourceMethods'])}",
        f"- Final fusion: `{candidate_policy.get('finalFusion', 'semantic')}`",
        "- Gold relevance labels available to reranker: no",
        "",
        "## Retrieval",
        "",
        "| Method | Recall@10 | MRR@10 | nDCG@10 | Complete support@10 | Median latency (ms) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method, summary in report["summaries"].items():
        lines.append(
            f"| {report['methods'][method]['displayName']} | {summary['recallAt10']:.4f} | "
            f"{summary['mrrAt10']:.4f} | {summary['ndcgAt10']:.4f} | "
            f"{summary['completeSupportAt10']:.4f} | {summary['latencyMedianMs']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Paired Comparison Against Hybrid RRF",
            "",
            "| Metric | Mean difference | 95% CI |",
            "| --- | ---: | ---: |",
        ]
    )
    for metric, comparison in report["pairedBootstrap"]["hybrid"].items():
        lines.append(
            f"| {metric} | {comparison['meanDifference']:.4f} | "
            f"[{comparison['lower95']:.4f}, {comparison['upper95']:.4f}] |"
        )
    hop_strata = report.get("hopStrata") or {}
    if hop_strata:
        lines.extend(
            [
                "",
                "## Hop Strata",
                "",
                "| Method | Hops | Queries | Recall@10 | nDCG@10 | Complete support@10 |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for method, strata in hop_strata.items():
            for hops, summary in strata.items():
                lines.append(
                    f"| {report['methods'][method]['displayName']} | {hops} | "
                    f"{summary['queries']} | {summary['recallAt10']:.4f} | "
                    f"{summary['ndcgAt10']:.4f} | "
                    f"{summary['completeSupportAt10']:.4f} |"
                )
    route_sensitivity = (report.get("routeSensitivity") or {}).get("withoutOpenIEProxy")
    if route_sensitivity:
        recall = route_sensitivity["candidateMinusAblationPairedBootstrap"][
            "recallAt10"
        ]
        lines.extend(
            [
                "",
                "## OpenIE Route Sensitivity",
                "",
                f"- Classification: {route_sensitivity['classification']}",
                f"- Reranker reexecuted: {str(route_sensitivity['rerankerReexecuted']).lower()}",
                f"- Recall@10 difference: {recall['meanDifference']:.4f} "
                f"[{recall['lower95']:.4f}, {recall['upper95']:.4f}]",
            ]
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- Retrieval criterion passed: {str(report['acceptance']['retrievalCriterionPassed']).lower()}",
            f"- Claim authorized: {str(report['acceptance']['claimAuthorized']).lower()}",
            "",
            "## Limitations",
            "",
            *(f"- {item}" for item in report["limitations"]),
            "",
        ]
    )
    return "\n".join(lines)


def fingerprint(args: argparse.Namespace) -> dict[str, Any]:
    result = {
        "baseReportSha256": sha256_file(args.base_report),
        "corpusSha256": sha256_file(args.corpus),
        "queriesSha256": sha256_file(args.queries),
        "splitManifestSha256": sha256_file(args.split_manifest),
        "split": args.split,
        "model": args.model,
        "revision": args.revision,
        "maxLength": args.max_length,
        "rankingDepth": args.ranking_depth,
        "sourceMethods": list(args.source_methods),
        "inferenceBackend": args.inference_backend,
        "intraOpThreads": args.intra_op_threads,
    }
    if args.inference_backend == "onnx":
        if not args.onnx_model:
            raise ValueError("An ONNX model path is required for the ONNX backend")
        result["onnxModelSha256"] = sha256_file(args.onnx_model)
        result["onnxOpset"] = args.onnx_opset
    return result


def load_checkpoint(path: Path, expected: Mapping[str, Any]) -> dict[str, Any]:
    if not path.exists():
        return {"fingerprint": dict(expected), "rankings": {}, "latenciesMs": {}}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fingerprint") != expected:
        raise ValueError(
            "Semantic rerank checkpoint does not match the active protocol"
        )
    return payload


def apply_claim_gate(acceptance: dict[str, Any], split: str) -> dict[str, Any]:
    gated = dict(acceptance)
    criterion_passed = bool(gated.get("retrievalCriterionPassed"))
    gated["claimAuthorized"] = criterion_passed and split == "confirmatory"
    gated["authorizationSplit"] = "confirmatory"
    return gated


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.split == "confirmatory" and not args.unlock_confirmatory:
        raise ValueError(
            "Confirmatory split is locked; freeze the candidate before opening it"
        )
    if len(args.revision) != 40:
        raise ValueError("Model revision must be a full 40-character commit")

    base_report = json.loads(args.base_report.read_text(encoding="utf-8"))
    documents, all_queries = load_musique(args.corpus, args.queries)
    split_payload = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    splits = validate_split_manifest(
        split_payload, corpus=args.corpus, queries=args.queries
    )
    contamination_audit = duplicate_question_audit(all_queries, splits)
    if args.split not in splits:
        raise ValueError(f"Unknown split: {args.split}")
    query_by_id = {query.id: query for query in all_queries}
    queries = [query_by_id[query_id] for query_id in splits[args.split]]
    document_by_id = {document.id: document for document in documents}
    source_rankings = base_report["retrieval"]["rankings"]

    active_fingerprint = fingerprint(args)
    checkpoint = load_checkpoint(args.checkpoint, active_fingerprint)
    rankings = checkpoint["rankings"]
    latencies_ms = checkpoint["latenciesMs"]
    pending = [query for query in queries if query.id not in rankings]

    if pending:
        if args.inference_backend == "onnx":
            model = OnnxCrossEncoder(
                model_path=args.onnx_model,
                tokenizer_name=args.tokenizer_path or args.model,
                revision=None if args.tokenizer_path else args.revision,
                max_length=args.max_length,
                intra_op_threads=args.intra_op_threads,
            )
        else:
            from sentence_transformers import CrossEncoder

            model = CrossEncoder(
                args.model,
                revision=args.revision,
                max_length=args.max_length,
            )

    for offset in range(0, len(pending), args.query_batch_size):
        query_batch = pending[offset : offset + args.query_batch_size]
        pairs: list[tuple[str, str]] = []
        pools: list[list[str]] = []
        for query in query_batch:
            pool = candidate_pool(source_rankings, query.id, args.source_methods)
            pools.append(pool)
            pairs.extend(
                (
                    query.question,
                    f"{document_by_id[item].title}\n{document_by_id[item].text}",
                )
                for item in pool
            )
        started = time.perf_counter()
        scores = model.predict(
            pairs,
            batch_size=args.inference_batch_size,
            show_progress_bar=False,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        cursor = 0
        total_pairs = max(1, len(pairs))
        for query, pool in zip(query_batch, pools, strict=True):
            pool_scores = scores[cursor : cursor + len(pool)]
            cursor += len(pool)
            rankings[query.id] = rank_from_scores(pool, pool_scores, args.ranking_depth)
            latencies_ms[query.id] = elapsed_ms * len(pool) / total_pairs
        checkpoint["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        atomic_write(args.checkpoint, checkpoint)
        print(
            json.dumps(
                {
                    "completedQueries": len(rankings),
                    "totalQueries": len(queries),
                }
            ),
            flush=True,
        )

    candidate_rankings = final_candidate_rankings(
        rankings,
        source_rankings["hybrid"],
        mode=args.final_fusion,
        depth=args.ranking_depth,
        rank_constant=args.rrf_rank_constant,
        hybrid_reserve=args.hybrid_reserve,
    )
    method_metadata = {
        "bm25": {"displayName": "BM25", "kind": "baseline"},
        "dense": {"displayName": "Dense retrieval", "kind": "baseline"},
        "hybrid": {"displayName": "Hybrid RRF", "kind": "baseline"},
        CANDIDATE_METHOD: {
            "displayName": (
                "BerryBrain semantic rerank"
                if args.final_fusion == "semantic"
                else (
                    "BerryBrain semantic-hybrid RRF"
                    if args.final_fusion == "semantic_hybrid_rrf"
                    else "BerryBrain semantic rerank with hybrid reserve"
                )
            ),
            "kind": "candidate",
        },
    }
    all_rankings = {
        method: source_rankings[method] for method in ("bm25", "dense", "hybrid")
    }
    all_rankings[CANDIDATE_METHOD] = candidate_rankings
    observations: dict[str, list[dict[str, Any]]] = {}
    summaries: dict[str, dict[str, float]] = {}
    for method, method_rankings in all_rankings.items():
        method_latencies = (
            latencies_ms
            if method == CANDIDATE_METHOD
            else internal_latencies(base_report, method)
        )
        observations[method], summaries[method] = evaluate_rankings(
            method_rankings, queries, method_latencies
        )
    comparisons = paired_comparisons(
        observations,
        candidate_method=CANDIDATE_METHOD,
        seed=args.bootstrap_seed,
        resamples=args.bootstrap_resamples,
    )
    acceptance = apply_claim_gate(
        acceptance_result(
            summaries,
            comparisons,
            method_metadata,
            candidate_method=CANDIDATE_METHOD,
        ),
        args.split,
    )
    if args.posthoc_rerun:
        acceptance["claimAuthorized"] = False
        acceptance["authorizationSplit"] = "none: previously observed split"
    pool_sizes = [
        len(candidate_pool(source_rankings, query.id, args.source_methods))
        for query in queries
    ]
    route_sensitivity: dict[str, Any] = {}
    if "openie_graphrag" in args.source_methods:
        non_graph_methods = [
            method for method in args.source_methods if method != "openie_graphrag"
        ]
        constrained_rankings = {
            query.id: constrain_ranking_to_routes(
                candidate_rankings[query.id],
                source_rankings,
                query.id,
                non_graph_methods,
                args.ranking_depth,
            )
            for query in queries
        }
        constrained_observations, constrained_summary = evaluate_rankings(
            constrained_rankings, queries, {}
        )
        sensitivity_comparison = paired_comparisons(
            {
                CANDIDATE_METHOD: observations[CANDIDATE_METHOD],
                "without_openie_proxy": constrained_observations,
            },
            candidate_method=CANDIDATE_METHOD,
            seed=args.bootstrap_seed,
            resamples=args.bootstrap_resamples,
        )["without_openie_proxy"]
        route_sensitivity["withoutOpenIEProxy"] = {
            "classification": "post-hoc route-exclusion sensitivity",
            "rerankerReexecuted": False,
            "allowedSourceMethods": non_graph_methods,
            "summary": constrained_summary,
            "candidateMinusAblationPairedBootstrap": sensitivity_comparison,
        }
    report = {
        "schemaVersion": SCHEMA_VERSION,
        "status": "completed",
        "classification": "post-hoc exploratory clean-source rerun"
        if args.posthoc_rerun
        else ("exploratory" if args.split != "confirmatory" else "confirmatory"),
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "split": args.split,
        "protocol": active_fingerprint,
        "execution": {
            "queryBatchSize": args.query_batch_size,
            "inferenceBatchSize": args.inference_batch_size,
            "onnxCpuMemoryArena": False if args.inference_backend == "onnx" else None,
            "onnxMemoryPattern": False if args.inference_backend == "onnx" else None,
            "onnxExecutionMode": "sequential"
            if args.inference_backend == "onnx"
            else None,
        },
        "candidatePolicy": {
            "finalFusion": args.final_fusion,
            "rrfRankConstant": args.rrf_rank_constant
            if args.final_fusion == "semantic_hybrid_rrf"
            else None,
            "hybridReserve": args.hybrid_reserve
            if args.final_fusion == "semantic_hybrid_reserve"
            else None,
            "selectionRule": "development-only",
        },
        "candidatePool": {
            "meanSize": statistics.fmean(pool_sizes),
            "minimumSize": min(pool_sizes),
            "maximumSize": max(pool_sizes),
            "oracleAccess": False,
        },
        "contaminationAudit": contamination_audit,
        "routeSensitivity": route_sensitivity,
        "methods": method_metadata,
        "summaries": summaries,
        "hopStrata": summarize_by_hops(observations),
        "pairedBootstrap": comparisons,
        "acceptance": acceptance,
        "rankings": candidate_rankings,
        "observations": observations,
        "limitations": [
            "The candidate pool is limited to documents already returned by frozen source routes.",
            (
                "This rerun uses a previously observed split and cannot authorize a new confirmatory claim."
                if args.posthoc_rerun
                else "Development and validation results select a candidate; only the locked confirmatory split can authorize the final claim."
            ),
            "Latency was measured on the active ARM host without an accelerator.",
        ],
    }
    atomic_write(args.output, report)
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-report", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument(
        "--split", choices=("development", "validation", "confirmatory"), required=True
    )
    parser.add_argument("--unlock-confirmatory", action="store_true")
    parser.add_argument("--posthoc-rerun", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--max-length", type=int, default=512)
    parser.add_argument(
        "--inference-backend", choices=INFERENCE_BACKENDS, default="pytorch"
    )
    parser.add_argument("--onnx-model", type=Path)
    parser.add_argument("--onnx-opset", type=int, default=14)
    parser.add_argument("--tokenizer-path")
    parser.add_argument("--intra-op-threads", type=int, default=4)
    parser.add_argument("--ranking-depth", type=int, default=10)
    parser.add_argument(
        "--final-fusion", choices=FINAL_FUSION_MODES, default="semantic"
    )
    parser.add_argument("--rrf-rank-constant", type=int, default=60)
    parser.add_argument("--hybrid-reserve", type=int, default=1)
    parser.add_argument("--source-methods", nargs="+", default=list(SOURCE_METHODS))
    parser.add_argument("--query-batch-size", type=int, default=8)
    parser.add_argument("--inference-batch-size", type=int, default=32)
    parser.add_argument("--bootstrap-seed", type=int, default=20260829)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    return parser.parse_args()


def main() -> int:
    report = run(parse_args())
    print(json.dumps({"status": report["status"], "acceptance": report["acceptance"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
