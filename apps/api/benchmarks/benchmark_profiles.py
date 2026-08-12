from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ScaleProfile:
    name: str
    notes: int
    graph_nodes: int
    graph_edges: int
    query_repetitions: int
    intended_use: str


@dataclass(frozen=True)
class AblationProfile:
    identifier: str
    family: str
    retrieval: str
    graph_expansion: bool
    generation: bool
    judge: bool
    continuous_agents: bool
    description: str


SCALE_PROFILES: dict[str, ScaleProfile] = {
    "S": ScaleProfile("S", 100, 500, 1_000, 7, "pull-request regression"),
    "M": ScaleProfile("M", 1_000, 5_000, 10_000, 15, "nightly representative"),
    "L": ScaleProfile("L", 10_000, 50_000, 100_000, 30, "release candidate"),
    "XL": ScaleProfile("XL", 25_000, 125_000, 250_000, 30, "bounded stress"),
}

ABLATION_PROFILES: dict[str, AblationProfile] = {
    "A0": AblationProfile(
        "A0", "answer", "lexical", False, False, False, False, "lexical retrieval"
    ),
    "A1": AblationProfile(
        "A1", "answer", "dense", False, False, False, False, "dense retrieval"
    ),
    "A2": AblationProfile(
        "A2", "answer", "hybrid", False, False, False, False, "hybrid retrieval"
    ),
    "A3": AblationProfile(
        "A3", "answer", "hybrid", True, False, False, False, "graph retrieval"
    ),
    "A4": AblationProfile(
        "A4", "answer", "hybrid", True, True, False, False, "vanilla RAG"
    ),
    "A5": AblationProfile(
        "A5", "answer", "hybrid", True, True, True, False, "Judge-gated RAG"
    ),
    "A6": AblationProfile(
        "A6", "answer", "hybrid", True, True, True, True, "full BerryBrain"
    ),
    "G0": AblationProfile(
        "G0", "graph", "none", False, False, False, False, "notes only"
    ),
    "G1": AblationProfile(
        "G1", "graph", "none", True, False, False, False, "explicit graph"
    ),
    "G2": AblationProfile(
        "G2", "graph", "none", True, False, True, False, "validated inference"
    ),
    "G3": AblationProfile(
        "G3", "graph", "none", True, False, True, True, "continuous graph"
    ),
}


def experiment_manifest(
    profile: str,
    ablations: tuple[str, ...],
    *,
    seed: int = 20260812,
    chunk_size: int = 1_000,
    context_limit: int = 8_192,
    cache_mode: str = "cold",
) -> dict[str, Any]:
    if profile not in SCALE_PROFILES:
        raise ValueError(f"unknown scale profile: {profile}")
    unknown = sorted(set(ablations) - ABLATION_PROFILES.keys())
    if unknown:
        raise ValueError(f"unknown ablation profiles: {', '.join(unknown)}")
    if cache_mode not in {"cold", "warm", "disabled"}:
        raise ValueError(f"unsupported cache mode: {cache_mode}")
    shared = {
        "seed": seed,
        "chunkSize": chunk_size,
        "contextLimit": context_limit,
        "cacheMode": cache_mode,
        "corpusParityRequired": True,
        "queryParityRequired": True,
        "modelParityRequired": True,
    }
    return {
        "schemaVersion": "berrybrain-experiment.v1",
        "scale": asdict(SCALE_PROFILES[profile]),
        "sharedControls": shared,
        "ablations": [asdict(ABLATION_PROFILES[item]) for item in ablations],
    }
