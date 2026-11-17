"""Evaluate fixed, label-blind route budgets on MuSiQue development data."""

from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path

from comparative_retrieval_benchmark import evaluate_rankings, paired_comparisons
from comparative_split_manifest import validate_manifest
from same_corpus_rag_benchmark import load_musique, sha256_file
from semantic_rerank_benchmark import OnnxCrossEncoder, atomic_write, rank_from_scores

POLICIES = {
    "hybrid40": (("hybrid", 40),),
    "hybrid30_graph10": (("hybrid", 30), ("openie_graphrag", 10)),
    "four10": (("bm25", 10), ("dense", 10), ("hybrid", 10), ("openie_graphrag", 10)),
}


def candidate_pool(rankings: dict, query_id: str, policy: tuple) -> list[str]:
    return list(dict.fromkeys(
        document_id
        for route, depth in policy
        for document_id in rankings[route][query_id][:depth]
    ))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--source", type=Path, required=True)
    result.add_argument("--corpus", type=Path, required=True)
    result.add_argument("--queries", type=Path, required=True)
    result.add_argument("--split-manifest", type=Path, required=True)
    result.add_argument("--onnx-model", type=Path, required=True)
    result.add_argument("--tokenizer", type=Path, required=True)
    result.add_argument("--split", choices=("development", "validation"), required=True)
    result.add_argument("--checkpoint", type=Path, required=True)
    result.add_argument("--output", type=Path, required=True)
    result.add_argument("--limit", type=int, default=0)
    return result


def main() -> None:
    args = parser().parse_args()
    if args.limit < 0:
        raise ValueError("Limit must be nonnegative")
    source = json.loads(args.source.read_text(encoding="utf-8"))
    if source.get("git", {}).get("dirty"):
        raise ValueError("Source rankings were not produced from a clean commit")
    rankings = source["retrieval"]["rankings"]
    documents, all_queries = load_musique(args.corpus, args.queries)
    splits = validate_manifest(
        json.loads(args.split_manifest.read_text(encoding="utf-8")),
        corpus=args.corpus,
        queries=args.queries,
    )
    by_id = {query.id: query for query in all_queries}
    by_document = {document.id: document for document in documents}
    queries = [by_id[query_id] for query_id in splits[args.split]]
    if args.limit:
        queries = queries[:args.limit]
    inputs = {
        "sourceSha256": sha256_file(args.source),
        "corpusSha256": sha256_file(args.corpus),
        "queriesSha256": sha256_file(args.queries),
        "splitSha256": sha256_file(args.split_manifest),
        "onnxSha256": sha256_file(args.onnx_model),
        "tokenizerRevision": args.tokenizer.name,
        "split": args.split,
        "limit": args.limit,
        "maxLength": 512,
        "batchSize": 8,
        "threads": 2,
        "policies": {
            name: [[route, depth] for route, depth in policy]
            for name, policy in POLICIES.items()
        },
    }
    if args.checkpoint.exists():
        checkpoint = json.loads(args.checkpoint.read_text(encoding="utf-8"))
        if checkpoint["inputs"] != inputs:
            raise ValueError("Checkpoint fingerprint differs from active inputs")
    else:
        checkpoint = {"inputs": inputs, "scores": {}, "latenciesMs": {}}

    pending = [query for query in queries if query.id not in checkpoint["scores"]]
    if pending:
        model = OnnxCrossEncoder(
            model_path=args.onnx_model,
            tokenizer_name=str(args.tokenizer),
            revision=None,
            max_length=512,
            intra_op_threads=2,
        )
    for offset in range(0, len(pending), 8):
        batch = pending[offset:offset + 8]
        pools = []
        pairs = []
        for query in batch:
            pool = list(dict.fromkeys(
                document_id
                for policy in POLICIES.values()
                for document_id in candidate_pool(rankings, query.id, policy)
            ))
            pools.append(pool)
            pairs.extend(
                (query.question, f"{by_document[item].title}\n{by_document[item].text}")
                for item in pool
            )
        started = time.perf_counter()
        scores = model.predict(pairs, batch_size=8)
        elapsed_ms = (time.perf_counter() - started) * 1000
        cursor = 0
        for query, pool in zip(batch, pools, strict=True):
            values = scores[cursor:cursor + len(pool)]
            cursor += len(pool)
            checkpoint["scores"][query.id] = dict(zip(pool, values, strict=True))
            checkpoint["latenciesMs"][query.id] = elapsed_ms * len(pool) / len(pairs)
        if cursor != len(scores):
            raise ValueError("Model score count differs from candidate count")
        atomic_write(args.checkpoint, checkpoint)
        print(f"scored {len(checkpoint['scores'])}/{len(queries)}", flush=True)

    policy_rankings = {}
    policy_sizes = {}
    observations = {}
    summaries = {}
    for name, policy in POLICIES.items():
        pools = {query.id: candidate_pool(rankings, query.id, policy) for query in queries}
        policy_sizes[name] = {
            "minimum": min(map(len, pools.values())),
            "mean": statistics.fmean(map(len, pools.values())),
            "maximum": max(map(len, pools.values())),
        }
        policy_rankings[name] = {
            query.id: rank_from_scores(
                pools[query.id],
                [checkpoint["scores"][query.id][item] for item in pools[query.id]],
                10,
            )
            for query in queries
        }
        observations[name], summaries[name] = evaluate_rankings(
            policy_rankings[name], queries, {}
        )
        for key in list(summaries[name]):
            if key.startswith("latency"):
                del summaries[name][key]
    comparisons = paired_comparisons(
        observations,
        candidate_method="hybrid30_graph10",
        seed=20261025,
        resamples=10000,
    )
    selected = all(
        summaries["hybrid30_graph10"][metric] >= summaries["hybrid40"][metric]
        for metric in ("recallAt10", "completeSupportAt10")
    )
    total_model_ms = sum(checkpoint["latenciesMs"][query.id] for query in queries)
    total_scored_pairs = sum(len(checkpoint["scores"][query.id]) for query in queries)
    atomic_write(args.output, {
        "status": "completed",
        "classification": "exploratory post-observation MuSiQue development/validation study",
        "inputs": inputs,
        "questionCount": len(queries),
        "candidatePools": policy_sizes,
        "sharedModelStage": {
            "scoredPairs": total_scored_pairs,
            "allocatedWallMs": total_model_ms,
            "allocatedMsPerPair": total_model_ms / total_scored_pairs,
            "description": "One model pass scores the union of all policy candidates; host-load-dependent, not per-policy latency.",
        },
        "summaries": summaries,
        "pairedBootstrap": comparisons,
        "policies": policy_rankings,
        "selectionCriterionPassed": selected,
        "claimAuthorized": False,
        "limitations": [
            "MuSiQue outcomes and development/validation candidate-pool coverage had already been inspected.",
            "Model-stage time was shared across policy pools and cannot be attributed to one policy.",
            "The OpenIE route is a deterministic graph proxy rather than the full system ontology.",
        ],
    })
    print(json.dumps({"status": "completed", "summaries": summaries, "selectionCriterionPassed": selected}))


if __name__ == "__main__":
    main()
