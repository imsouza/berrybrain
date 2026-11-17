"""Create an immutable, hash-based split manifest for comparative RAG evaluation."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from same_corpus_rag_benchmark import QueryCase, load_musique, sha256_file, tokens

SCHEMA_VERSION = "berrybrain.comparative-split.v1"


def split_query_ids(
    query_ids: Sequence[str],
    *,
    development_count: int,
    validation_count: int,
    salt: str,
) -> dict[str, list[str]]:
    unique = set(query_ids)
    if len(unique) != len(query_ids):
        raise ValueError("Query IDs must be unique")
    if development_count < 1 or validation_count < 1:
        raise ValueError("Development and validation counts must be positive")
    if development_count + validation_count >= len(unique):
        raise ValueError("The confirmatory split must contain at least one query")
    ordered = sorted(
        unique,
        key=lambda query_id: hashlib.sha256(f"{salt}:{query_id}".encode()).hexdigest(),
    )
    development_end = development_count
    validation_end = development_end + validation_count
    return {
        "development": ordered[:development_end],
        "validation": ordered[development_end:validation_end],
        "confirmatory": ordered[validation_end:],
    }


def duplicate_question_audit(
    queries: Sequence[QueryCase], splits: dict[str, list[str]]
) -> dict[str, Any]:
    split_by_id = {
        query_id: split_name
        for split_name, query_ids in splits.items()
        for query_id in query_ids
    }
    grouped: dict[str, list[str]] = {}
    for query in queries:
        grouped.setdefault(" ".join(tokens(query.question)), []).append(query.id)
    duplicates = [sorted(ids) for ids in grouped.values() if len(ids) > 1]
    cross_split = [
        ids
        for ids in duplicates
        if len({split_by_id[query_id] for query_id in ids}) > 1
    ]
    return {
        "normalizedQuestionGroups": len(grouped),
        "duplicateNormalizedQuestionGroups": len(duplicates),
        "crossSplitDuplicateGroups": len(cross_split),
        "duplicateQueryIds": sorted(duplicates),
    }


def build_manifest(
    *,
    corpus: Path,
    queries: Path,
    development_count: int,
    validation_count: int,
    salt: str,
) -> dict[str, Any]:
    _, query_rows = load_musique(corpus, queries)
    splits = split_query_ids(
        [query.id for query in query_rows],
        development_count=development_count,
        validation_count=validation_count,
        salt=salt,
    )
    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selection": "sha256(salt + ':' + query_id), ascending",
        "salt": salt,
        "inputs": {
            "corpusSha256": sha256_file(corpus),
            "queriesSha256": sha256_file(queries),
        },
        "counts": {name: len(query_ids) for name, query_ids in splits.items()},
        "contaminationAudit": duplicate_question_audit(query_rows, splits),
        "splits": splits,
        "policy": {
            "development": "Parameter and prompt selection is allowed.",
            "validation": "Selection confirmation is allowed; final claims are forbidden.",
            "confirmatory": "Open once after configuration freeze; no post-result tuning.",
        },
    }


def validate_manifest(
    payload: dict[str, Any],
    *,
    corpus: Path,
    queries: Path,
) -> dict[str, list[str]]:
    if payload.get("schemaVersion") != SCHEMA_VERSION:
        raise ValueError("Unsupported comparative split schema")
    inputs = payload.get("inputs")
    if not isinstance(inputs, dict):
        raise ValueError("Split inputs must be an object")
    if inputs.get("corpusSha256") != sha256_file(corpus):
        raise ValueError("Split corpus hash does not match")
    if inputs.get("queriesSha256") != sha256_file(queries):
        raise ValueError("Split query hash does not match")
    _, query_rows = load_musique(corpus, queries)
    expected = {query.id for query in query_rows}
    raw_splits = payload.get("splits")
    if not isinstance(raw_splits, dict):
        raise ValueError("Split definitions must be an object")
    required = {"development", "validation", "confirmatory"}
    if set(raw_splits) != required:
        raise ValueError(
            "Split definitions must contain development, validation, and confirmatory"
        )
    splits: dict[str, list[str]] = {}
    combined: list[str] = []
    for name in sorted(required):
        values = raw_splits[name]
        if not isinstance(values, list) or not values:
            raise ValueError(f"Split {name} must be a non-empty list")
        split_ids = [str(value) for value in values]
        if len(set(split_ids)) != len(split_ids):
            raise ValueError(f"Split {name} contains duplicate query IDs")
        splits[name] = split_ids
        combined.extend(split_ids)
    if len(set(combined)) != len(combined):
        raise ValueError("Query IDs overlap between splits")
    if set(combined) != expected:
        raise ValueError("Split query coverage does not match the dataset")
    contamination_audit = duplicate_question_audit(query_rows, splits)
    if contamination_audit["crossSplitDuplicateGroups"]:
        raise ValueError("Normalized duplicate questions overlap between splits")
    if (
        "contaminationAudit" in payload
        and payload["contaminationAudit"] != contamination_audit
    ):
        raise ValueError("Split contamination audit does not match the dataset")
    counts = payload.get("counts")
    if not isinstance(counts, dict) or any(
        counts.get(name) != len(values) for name, values in splits.items()
    ):
        raise ValueError("Split counts do not match")
    return splits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--development-count", type=int, default=200)
    parser.add_argument("--validation-count", type=int, default=200)
    parser.add_argument("--salt", default="berrybrain-v1.4.10-preregistered")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = build_manifest(
        corpus=args.corpus,
        queries=args.queries,
        development_count=args.development_count,
        validation_count=args.validation_count,
        salt=args.salt,
    )
    validate_manifest(payload, corpus=args.corpus, queries=args.queries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "counts": payload["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
