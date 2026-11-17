"""Paired, post-hoc comparison of two clean-source MuSiQue CE runs."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from comparative_retrieval_benchmark import paired_comparisons
from same_corpus_rag_benchmark import sha256_file
from semantic_rerank_benchmark import candidate_pool


def candidate_rows(report: dict) -> list[dict]:
    return report["observations"]["semantic_rerank"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--four-route", type=Path, required=True)
    parser.add_argument("--hybrid40", type=Path, required=True)
    parser.add_argument("--source-ten", type=Path, required=True)
    parser.add_argument("--source-forty", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    four = json.loads(args.four_route.read_text())
    hybrid = json.loads(args.hybrid40.read_text())
    ten = json.loads(args.source_ten.read_text())
    forty = json.loads(args.source_forty.read_text())
    assert four["status"] == hybrid["status"] == "completed"
    assert four["classification"] == hybrid["classification"] == "post-hoc exploratory clean-source rerun"
    assert four["split"] == hybrid["split"] == "confirmatory"
    assert four["acceptance"]["claimAuthorized"] is hybrid["acceptance"]["claimAuthorized"] is False
    for key in ("corpusSha256", "queriesSha256", "splitManifestSha256", "model", "revision", "maxLength", "rankingDepth", "inferenceBackend", "intraOpThreads", "onnxModelSha256"):
        assert four["protocol"][key] == hybrid["protocol"][key], key
    assert four["execution"] == hybrid["execution"]
    assert four["protocol"]["baseReportSha256"] == sha256_file(args.source_ten)
    assert hybrid["protocol"]["baseReportSha256"] == sha256_file(args.source_forty)
    assert four["protocol"]["sourceMethods"] == ["bm25", "dense", "hybrid", "openie_graphrag"]
    assert hybrid["protocol"]["sourceMethods"] == ["hybrid"]

    observations = {
        "four_route_ce": candidate_rows(four),
        "hybrid40_ce": candidate_rows(hybrid),
        "hybrid_rrf": four["observations"]["hybrid"],
    }
    qsets = [{row["queryId"] for row in rows} for rows in observations.values()]
    assert len(qsets[0]) == len(qsets[1]) == len(qsets[2]) == 600
    assert qsets[0] == qsets[1] == qsets[2]
    comparisons = paired_comparisons(
        observations,
        candidate_method="four_route_ce",
        seed=20261024,
        resamples=10000,
    )
    four_ms_per_pair = [
        row["latencyMs"] / len(candidate_pool(ten["retrieval"]["rankings"], row["queryId"], four["protocol"]["sourceMethods"]))
        for row in observations["four_route_ce"]
    ]
    hybrid_ms_per_pair = [
        row["latencyMs"] / len(candidate_pool(forty["retrieval"]["rankings"], row["queryId"], hybrid["protocol"]["sourceMethods"]))
        for row in observations["hybrid40_ce"]
    ]
    result = {
        "classification": "post-hoc exploratory comparison on a previously observed MuSiQue split",
        "claimAuthorized": False,
        "questionCount": 600,
        "sha256": {
            "fourRouteReport": sha256_file(args.four_route),
            "hybrid40Report": sha256_file(args.hybrid40),
            "sourceTen": sha256_file(args.source_ten),
            "sourceForty": sha256_file(args.source_forty),
        },
        "poolSizes": {
            "fourRoute": four["candidatePool"],
            "hybrid40": hybrid["candidatePool"],
        },
        "summaries": {
            "four_route_ce": four["summaries"]["semantic_rerank"],
            "hybrid40_ce": hybrid["summaries"]["semantic_rerank"],
            "hybrid_rrf": four["summaries"]["hybrid"],
        },
        "comparisons": comparisons,
        "localModelMillisecondsPerPair": {
            "fourRouteMean": statistics.fmean(four_ms_per_pair),
            "fourRouteMedian": statistics.median(four_ms_per_pair),
            "hybrid40Mean": statistics.fmean(hybrid_ms_per_pair),
            "hybrid40Median": statistics.median(hybrid_ms_per_pair),
            "definition": "each query's allocated model-stage milliseconds divided by its actual deduplicated candidate count; excludes retrieval, indexing and cloud provider time",
        },
        "limitations": [
            "Both methods were tested post-hoc on a previously observed 600-question split.",
            "The Hybrid40 pool has a different candidate budget from each of the four depth-10 routes; actual deduplicated pool sizes are reported.",
            "Source rankings from the clean run differ from historical rankings despite matching input and embedding-model hashes; historical results are not an exact replication.",
            "Model-stage timing is local to the Pi; cloud-provider response time is excluded.",
            "The two local inference jobs overlapped on the four-core Pi after a short staggered start, so their model-stage times are contended descriptive costs, not a matched speed comparison.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": "completed", "summaries": result["summaries"], "comparisons": result["comparisons"]}))


if __name__ == "__main__":
    main()
