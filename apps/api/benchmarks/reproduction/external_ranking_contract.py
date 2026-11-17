"""Versioned contract for official external retrieval baseline rankings."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Collection, Mapping, Sequence
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "berrybrain.external-ranking.v1"


class ExternalRankingContractError(ValueError):
    """Raised when an external baseline cannot support a fair comparison."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(
    *,
    method_id: str,
    display_name: str,
    repository: str,
    commit: str,
    version: str,
    corpus_sha256: str,
    queries_sha256: str,
    ranking_depth: int,
    rankings: Mapping[str, Sequence[str]],
    latencies_ms: Mapping[str, float],
    configuration: Mapping[str, Any],
    generated_at: str,
) -> dict[str, Any]:
    return {
        "schemaVersion": SCHEMA_VERSION,
        "method": {
            "id": method_id,
            "displayName": display_name,
            "implementationKind": "official",
            "repository": repository,
            "commit": commit,
            "version": version,
        },
        "dataset": {
            "corpusSha256": corpus_sha256,
            "queriesSha256": queries_sha256,
        },
        "protocol": {
            "rankingDepth": ranking_depth,
            "oracleAccess": False,
            "queryCount": len(rankings),
        },
        "rankings": {key: list(value) for key, value in rankings.items()},
        "latenciesMs": dict(latencies_ms),
        "failures": {},
        "configuration": dict(configuration),
        "generatedAt": generated_at,
    }


def validate_manifest(
    payload: Mapping[str, Any],
    *,
    expected_query_ids: Collection[str],
    expected_document_ids: Collection[str],
    corpus_sha256: str,
    queries_sha256: str,
    ranking_depth: int,
) -> dict[str, list[str]]:
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise ExternalRankingContractError("Unsupported external ranking schema")
    method = _mapping(payload.get("method"), "method")
    required_method_fields = (
        "id",
        "displayName",
        "repository",
        "commit",
        "version",
    )
    for field in required_method_fields:
        if not str(method.get(field) or "").strip():
            raise ExternalRankingContractError(f"Missing method.{field}")
    if method.get("implementationKind") != "official":
        raise ExternalRankingContractError("External baseline is not marked official")
    commit = str(method["commit"])
    if len(commit) != 40 or any(
        character not in "0123456789abcdef" for character in commit
    ):
        raise ExternalRankingContractError(
            "method.commit must be a lowercase full Git commit"
        )

    dataset = _mapping(payload.get("dataset"), "dataset")
    if dataset.get("corpusSha256") != corpus_sha256:
        raise ExternalRankingContractError("External corpus hash does not match")
    if dataset.get("queriesSha256") != queries_sha256:
        raise ExternalRankingContractError("External query hash does not match")

    protocol = _mapping(payload.get("protocol"), "protocol")
    if protocol.get("oracleAccess") is not False:
        raise ExternalRankingContractError(
            "External baseline must explicitly deny oracle access"
        )
    if protocol.get("rankingDepth") != ranking_depth:
        raise ExternalRankingContractError("External ranking depth does not match")

    rankings = _mapping(payload.get("rankings"), "rankings")
    expected_queries = set(expected_query_ids)
    actual_queries = set(rankings)
    missing_queries = sorted(expected_queries - actual_queries)
    unknown_queries = sorted(actual_queries - expected_queries)
    if missing_queries or unknown_queries:
        raise ExternalRankingContractError(
            "External query coverage mismatch: "
            f"missing={len(missing_queries)}, unknown={len(unknown_queries)}"
        )
    if protocol.get("queryCount") != len(expected_queries):
        raise ExternalRankingContractError("External query count does not match")
    failures = _mapping(payload.get("failures"), "failures")
    if failures:
        raise ExternalRankingContractError(
            "Confirmatory external ranking contains failures"
        )

    expected_documents = set(expected_document_ids)
    normalized: dict[str, list[str]] = {}
    for query_id in sorted(expected_queries):
        raw_ranking = rankings[query_id]
        if not isinstance(raw_ranking, list):
            raise ExternalRankingContractError(f"Ranking for {query_id} is not a list")
        ranking = [str(document_id) for document_id in raw_ranking]
        if len(ranking) != ranking_depth:
            raise ExternalRankingContractError(
                f"Ranking for {query_id} must contain exactly {ranking_depth} documents"
            )
        if len(set(ranking)) != len(ranking):
            raise ExternalRankingContractError(
                f"Ranking for {query_id} contains duplicates"
            )
        unknown_documents = sorted(set(ranking) - expected_documents)
        if unknown_documents:
            raise ExternalRankingContractError(
                f"Ranking for {query_id} contains unknown document IDs"
            )
        normalized[query_id] = ranking

    latencies = _mapping(payload.get("latenciesMs"), "latenciesMs")
    if set(latencies) != expected_queries:
        raise ExternalRankingContractError("External latency coverage does not match")
    for query_id, latency in latencies.items():
        if not isinstance(latency, (int, float)) or latency < 0:
            raise ExternalRankingContractError(f"Invalid latency for {query_id}")
    configuration = _mapping(payload.get("configuration"), "configuration")
    if not configuration:
        raise ExternalRankingContractError("External configuration must not be empty")
    return normalized


def load_and_validate_manifest(
    path: Path,
    **kwargs: Any,
) -> tuple[dict[str, Any], dict[str, list[str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ExternalRankingContractError(
            "External ranking manifest must be an object"
        )
    rankings = validate_manifest(payload, **kwargs)
    return payload, rankings


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ExternalRankingContractError(f"{field} must be an object")
    return value
