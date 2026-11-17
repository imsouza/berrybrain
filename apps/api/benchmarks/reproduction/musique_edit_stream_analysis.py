"""Paired query-level uncertainty for the MuSiQue source-edit stream."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "musique-edit-stream-report.json"
OUTPUT = ROOT / "musique-edit-stream-analysis.json"


def main() -> None:
    report = json.loads(INPUT.read_text())
    probes = report["probes"]
    if len(probes) != 20 or report["metrics"]["probeCount"] != 20:
        raise ValueError("Expected 20 fixed source probes")
    rows = []
    for probe in probes:
        source_id = probe["sourceId"]
        frozen = probe["frozenTop10"]
        after = probe["afterTop10"]
        rows.append({
            "sourceId": source_id,
            "action": probe["action"],
            "frozenDerivedAt10": len(frozen),
            "afterDerivedAt10": len(after),
            "frozenStaleAt10": sum(source_id in item["sourceIds"] for item in frozen),
            "afterStaleAt10": sum(source_id in item["sourceIds"] for item in after),
        })
    frozen = np.array([row["frozenStaleAt10"] for row in rows], dtype=float)
    after = np.array([row["afterStaleAt10"] for row in rows], dtype=float)
    differences = frozen - after
    rng = np.random.default_rng(20261023)
    indices = rng.integers(0, len(rows), size=(10_000, len(rows)))
    means = differences[indices].mean(axis=1)
    derived_frozen = sum(row["frozenDerivedAt10"] for row in rows)
    derived_after = sum(row["afterDerivedAt10"] for row in rows)
    result = {
        "inputReportSha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "scriptSha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "probeCount": len(rows),
        "summary": {
            "frozenStaleCount": int(frozen.sum()),
            "afterStaleCount": int(after.sum()),
            "frozenDerivedTop10Slots": derived_frozen,
            "afterDerivedTop10Slots": derived_after,
            "meanStaleCountDifferencePerProbe": round(float(differences.mean()), 6),
            "bootstrap95": [
                round(float(np.quantile(means, 0.025)), 6),
                round(float(np.quantile(means, 0.975)), 6),
            ],
            "bootstrapSeed": 20261023,
            "bootstrapResamples": 10_000,
            "unaffectedSemanticRetention": report["metrics"]["unaffectedSemanticRetention"],
        },
        "byAction": {
            action: {
                "probeCount": sum(row["action"] == action for row in rows),
                "frozenStaleCount": sum(row["frozenStaleAt10"] for row in rows if row["action"] == action),
                "afterStaleCount": sum(row["afterStaleAt10"] for row in rows if row["action"] == action),
            }
            for action in ("delete", "edit")
        },
        "observations": rows,
        "interpretation": (
            "Exploratory fixed probes chosen from the edited sources. The bootstrap resamples "
            "probes, not independent artifacts. It does not estimate ordinary-use edit prevalence."
        ),
    }
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result["summary"]))


if __name__ == "__main__":
    main()
