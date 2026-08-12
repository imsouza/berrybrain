from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_analysis_artifacts(report: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    retrieval = report["releaseGate"]["retrieval_ablation"]
    graph = report["graphOnDisk"]
    worker = report["workerQueue"]
    http = report.get("httpLoad")
    rows = [
        (
            item["configuration"],
            item["recall_at_10"],
            item["mean_reciprocal_rank"],
            item["ndcg_at_10"],
            item["latency_p95_ms"],
        )
        for item in retrieval["ablations"]
    ]
    table = "\n".join(
        f"| {name} | {recall:.3f} | {mrr:.3f} | {ndcg:.3f} | {latency:.2f} |"
        for name, recall, mrr, ndcg, latency in rows
    )
    http_text = (
        f"{http['requests']} requests, {http['throughput_rps']:.2f} requests/s, "
        f"p95 {http['latency_p95_ms']:.2f} ms, error rate {http['error_rate']:.3f}"
        if http
        else "not executed"
    )
    markdown = f"""# BerryBrain Evaluation Table

**Caption:** Exploratory profile {report['profile']} results generated from the machine-readable
evaluation bundle. Synthetic retrieval results are internal regression evidence and must not be
interpreted as external comparative validity.

**Provenance:** `reports/evaluation/full-evaluation.json`, generated
`{report['generatedAt']}`. Evidence manifests retain revision, dirty state, environment, seed,
configuration, observations, and checksums.

| Retrieval configuration | Recall@10 | MRR | NDCG@10 | p95 latency (ms) |
| --- | ---: | ---: | ---: | ---: |
{table}

## System Profile

- HTTP: {http_text}.
- On-disk graph: {graph['node_count']} nodes, {graph['edge_count']} edges, p95
  {graph['latency_p95_ms']:.2f} ms, payload {graph['payload_bytes']} bytes, peak traced memory
  {graph['peak_memory_bytes']} bytes.
- Worker queue: enqueue {worker['enqueue_rate_jobs_per_second']:.2f} jobs/s, drain
  {worker['drain_rate_jobs_per_second']:.2f} jobs/s, end-to-end p95
  {worker['end_to_end_p95_ms']:.2f} ms, duplicate claims {worker['duplicate_claims']}.
- Maturity V3: {report['maturity']['readiness']}, minimum Level
  {report['maturity']['minimum_level']}, median Level {report['maturity']['median_level']}.
"""
    chart = {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "description": (
            "Exploratory BerryBrain retrieval quality and latency by configuration. "
            "Source: reports/evaluation/full-evaluation.json."
        ),
        "data": {
            "values": [
                {
                    "configuration": name,
                    "recallAt10": recall,
                    "mrr": mrr,
                    "ndcgAt10": ndcg,
                    "latencyP95Ms": latency,
                }
                for name, recall, mrr, ndcg, latency in rows
            ]
        },
        "hconcat": [
            {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "configuration", "type": "nominal", "sort": None},
                    "y": {
                        "field": "recallAt10",
                        "type": "quantitative",
                        "scale": {"domain": [0, 1]},
                    },
                    "color": {"value": "#CC4168"},
                },
                "title": "Recall@10",
            },
            {
                "mark": "bar",
                "encoding": {
                    "x": {"field": "configuration", "type": "nominal", "sort": None},
                    "y": {"field": "latencyP95Ms", "type": "quantitative"},
                    "color": {"value": "#96B55C"},
                },
                "title": "p95 latency (ms)",
            },
        ],
        "usermeta": {
            "classification": report["classification"],
            "generatedAt": report["generatedAt"],
            "profile": report["profile"],
            "caption": "Internal controlled retrieval ablation; not an external benchmark.",
        },
    }
    return markdown, chart


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate thesis tables and chart specifications."
    )
    parser.add_argument("--report", default="reports/evaluation/full-evaluation.json")
    parser.add_argument("--markdown", default="reports/evaluation/thesis-table.md")
    parser.add_argument("--chart", default="reports/evaluation/retrieval-chart.vl.json")
    args = parser.parse_args()
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    markdown, chart = build_analysis_artifacts(report)
    markdown_path = Path(args.markdown)
    chart_path = Path(args.chart)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    chart_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")
    chart_path.write_text(
        json.dumps(chart, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps({"markdown": str(markdown_path), "chart": str(chart_path)}, indent=2)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
