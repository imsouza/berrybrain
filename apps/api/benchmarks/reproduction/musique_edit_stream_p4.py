"""Prospective MuSiQue edit-stream P4 confirmation on a strictly disjoint second stream.

Protocol: PROSPECTIVE_EDIT_STREAM_P4_PROTOCOL_2026-11-13.md
(SHA-256: 81c714e9024056c25f7e32b7c5726430e4680b3bbdfe73ac15f1c4ab721ca5a1).

Evaluates whether the MIN_INSIGHT_SUPPORT_NOTES = 2 lifecycle fix (originally
identified post-hoc on Stream 1 in EDIT_STREAM_N4_PROTOCOL_2026-11-08.md)
prospectively achieves 0 broken top-10 derivations and 100.0% post-gate
retention of G_clean(D'') on a second, strictly disjoint MuSiQue edit stream
selected by salted SHA-256 hash.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent
FIXED_API_SRC = Path("/mnt/HDD_1/Antigravity/berrybrain-insight-support/apps/api/src")
if FIXED_API_SRC.exists():
    sys.path.insert(0, str(FIXED_API_SRC))
sys.path.insert(0, str(ROOT))

import berrybrain_api.graph_expansion as graph_expansion_mod  # noqa: E402
import berrybrain_api.models  # noqa: F401, E402
from berrybrain_api.graph_expansion import expand_knowledge_graph  # noqa: E402
from berrybrain_api.generated_metadata import upsert_generated_metadata  # noqa: E402
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, NoteRecord  # noqa: E402
from berrybrain_api.sync import remove_note_record, sync_note_record  # noqa: E402
from musique_edit_stream import (  # noqa: E402
    INPUT,
    N_DELETE,
    N_DISTRACTORS,
    N_EDIT,
    N_QUESTIONS,
    corpus_key,
    digest,
    semantic_signature,
)
from musique_edit_stream_b4 import (  # noqa: E402
    admit_valid_derived_items,
    bootstrap_diff,
    build_clean_post_edit_reference,
    build_initial_vault,
    evaluate_view,
    load_openie_docs,
)

PROTOCOL_PATH = ROOT / "PROSPECTIVE_EDIT_STREAM_P4_PROTOCOL_2026-11-13.md"
EXPECTED_PROTOCOL_SHA256 = "81c714e9024056c25f7e32b7c5726430e4680b3bbdfe73ac15f1c4ab721ca5a1"
EXPECTED_GRAPH_EXPANSION_SHA256 = "1c38afecca76af2079c653cb9e1bacb043f0a32baf0cb5d618463c75cce371ee"
OUTPUT = ROOT / "musique-edit-stream-p4-report.json"
STREAM2_SALT = "p4-prospective-edit-stream-2026-11-13:"
SEED = 20261113
RESAMPLES = 10_000


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stream2_digest(value: str) -> str:
    return hashlib.sha256((STREAM2_SALT + value).encode("utf-8")).hexdigest()


def main() -> None:
    protocol_sha = sha256_path(PROTOCOL_PATH)
    if protocol_sha != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"Protocol SHA-256 mismatch: {protocol_sha} != {EXPECTED_PROTOCOL_SHA256}")

    ge_path = Path(graph_expansion_mod.__file__).resolve()
    ge_sha = sha256_path(ge_path)
    if ge_sha != EXPECTED_GRAPH_EXPANSION_SHA256:
        raise ValueError(
            f"graph_expansion.py SHA-256 mismatch ({ge_path}): {ge_sha} != {EXPECTED_GRAPH_EXPANSION_SHA256}"
        )
    assert getattr(graph_expansion_mod, "MIN_INSIGHT_SUPPORT_NOTES", None) == 2

    questions = json.loads((INPUT / "musique.json").read_text(encoding="utf-8"))
    corpus = json.loads((INPUT / "musique_corpus.json").read_text(encoding="utf-8"))
    extracted = load_openie_docs()
    assert len(corpus) == len(extracted)
    by_key = {corpus_key(d["title"], d["text"]): i for i, d in enumerate(corpus)}

    # 1. Reconstruct Stream 1 exclusion sets exactly
    s1_questions = sorted(questions, key=lambda q: digest(q["id"]))[:N_QUESTIONS]
    s1_question_ids = {q["id"] for q in s1_questions}
    s1_support_keys = {
        corpus_key(p["title"], p["paragraph_text"])
        for q in s1_questions
        for p in q["paragraphs"]
        if p.get("is_supporting")
    }
    s1_distractor_keys = set(sorted(by_key.keys() - s1_support_keys, key=digest)[:N_DISTRACTORS])
    s1_selected_keys = s1_support_keys | s1_distractor_keys
    assert len(s1_question_ids) == 20
    assert len(s1_support_keys) == 49
    assert len(s1_selected_keys) == 99

    # 2. Deterministically select Stream 2 questions & passages strictly disjoint from Stream 1
    candidates = sorted(questions, key=lambda q: (stream2_digest(q["id"]), q["id"]))
    s2_questions = []
    for q in candidates:
        if q["id"] in s1_question_ids:
            continue
        q_supp = {
            corpus_key(p["title"], p["paragraph_text"])
            for p in q["paragraphs"]
            if p.get("is_supporting")
        }
        if not q_supp or (q_supp & s1_selected_keys):
            continue
        s2_questions.append(q)
        if len(s2_questions) == N_QUESTIONS:
            break

    s2_question_ids = [q["id"] for q in s2_questions]
    s2_support_keys = {
        corpus_key(p["title"], p["paragraph_text"])
        for q in s2_questions
        for p in q["paragraphs"]
        if p.get("is_supporting")
    }
    s2_distractor_keys = sorted(
        by_key.keys() - s1_selected_keys - s2_support_keys,
        key=stream2_digest,
    )[:N_DISTRACTORS]
    s2_selected_keys = sorted(s2_support_keys | set(s2_distractor_keys))
    s2_selected_indices = [by_key[k] for k in s2_selected_keys]

    # Enforce preregistered disjointness assertions before building any vault
    assert s1_question_ids.isdisjoint(s2_question_ids)
    assert s1_selected_keys.isdisjoint(s2_selected_keys)
    assert len(s2_question_ids) == N_QUESTIONS
    assert len(s2_distractor_keys) == N_DISTRACTORS
    assert len(s2_support_keys) >= N_DELETE + N_EDIT

    support_order = sorted(s2_support_keys, key=stream2_digest)
    delete_keys = set(support_order[:N_DELETE])
    edit_keys = set(support_order[N_DELETE : N_DELETE + N_EDIT])
    operations = (
        [{"action": "delete", "key": k} for k in support_order[:N_DELETE]]
        + [{"action": "edit", "key": k} for k in support_order[N_DELETE : N_DELETE + N_EDIT]]
    )

    clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set = build_clean_post_edit_reference(
        corpus, extracted, s2_selected_indices, delete_keys, edit_keys
    )

    with tempfile.TemporaryDirectory(prefix="berrybrain-p4-main-") as temp:
        t_build0 = time.perf_counter()
        vault, session, note_by_key, concept_by_key = build_initial_vault(
            Path(temp), corpus, extracted, s2_selected_indices
        )
        initial_build_seconds = round(time.perf_counter() - t_build0, 3)
        changed_ids = {note_by_key[op["key"]] for op in operations}
        probes = [
            {
                "action": op["action"],
                "sourceKey": op["key"],
                "sourceId": note_by_key[op["key"]],
                "query": next(
                    (c for c in concept_by_key[op["key"]] if len(c.split()) >= 2),
                    concept_by_key[op["key"]][0],
                ),
            }
            for op in operations
        ]
        init_nodes = list(session.scalars(select(GraphNodeRecord)))
        init_edges = list(session.scalars(select(GraphEdgeRecord)))
        init_by_id = {n.id: n for n in init_nodes}
        initial_unaffected_sigs = Counter(
            semantic_signature(item, init_by_id)
            for item in [*init_nodes, *init_edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and json.loads(item.source_note_ids or "[]")
            and not (set(json.loads(item.source_note_ids or "[]")) & changed_ids)
            and item.quality_gate_status == "passed"
        )

        # 1. Frozen view
        frozen_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, set(),
        )

        # 2. Apply the 20 source updates (direct-provenance detach before rebuild)
        t_direct0 = time.perf_counter()
        for op in operations:
            key = op["key"]
            relative = f"sources/{key[:20]}.md"
            if op["action"] == "delete":
                (vault / relative).unlink()
                remove_note_record(session, relative, vault)
            else:
                (vault / relative).write_text(
                    "# Corrected source\n\nThe earlier passage has been retracted.\n",
                    encoding="utf-8",
                )
                note = sync_note_record(session, vault, relative)
                upsert_generated_metadata(
                    session, note.id, "concepts", {"concepts": []},
                    note.content_hash, model_used="authored-correction-v1",
                )
        direct_detach_seconds = round(time.perf_counter() - t_direct0, 3)

        direct_detach_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, set(),
        )

        # 3. BerryBrain dependency-propagating rebuild
        t_reb0 = time.perf_counter()
        expand_knowledge_graph(session)
        rebuild_seconds = round(time.perf_counter() - t_reb0, 3)

        # Identify unchanged-direct signatures temporarily placed in pending state by rebuild
        reb_nodes = list(session.scalars(select(GraphNodeRecord)))
        reb_edges = list(session.scalars(select(GraphEdgeRecord)))
        reb_by_id = {n.id: n for n in reb_nodes}
        pending_unchanged_sigs = {
            semantic_signature(item, reb_by_id)
            for item in [*reb_nodes, *reb_edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and item.quality_gate_status == "pending"
            and (set(json.loads(item.source_note_ids or "[]")) <= (set(note_by_key.values()) - changed_ids))
            and semantic_signature(item, reb_by_id) in initial_unaffected_sigs
        }

        dep_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_unchanged_sigs,
        )

        # 4. Post-rebuild quality-gate worker admission pass
        gate_stats, gate_seconds = admit_valid_derived_items(session)
        dep_gate_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_unchanged_sigs,
        )
        session.close()

    # Run 2: Strict direct-provenance purge baseline
    with tempfile.TemporaryDirectory(prefix="berrybrain-p4-purge-") as temp:
        _, session2, note_by_key2, _ = build_initial_vault(
            Path(temp), corpus, extracted, s2_selected_indices
        )
        changed_ids2 = {note_by_key2[op["key"]] for op in operations}
        nodes2 = list(session2.scalars(select(GraphNodeRecord)))
        purge_node_ids = {
            n.id for n in nodes2
            if (n.type == "note" and n.source_id in changed_ids2)
            or (n.type != "note" and (set(json.loads(n.source_note_ids or "[]")) & changed_ids2))
        }
        for e in list(session2.scalars(select(GraphEdgeRecord))):
            if (
                e.source_node_id in purge_node_ids
                or e.target_node_id in purge_node_ids
                or (set(json.loads(e.source_note_ids or "[]")) & changed_ids2)
            ):
                session2.delete(e)
        for n in nodes2:
            if n.id in purge_node_ids:
                session2.delete(n)
        for op in operations:
            key = op["key"]
            relative = f"sources/{key[:20]}.md"
            if op["action"] == "delete":
                rec = session2.scalar(select(NoteRecord).where(NoteRecord.path == relative))
                if rec:
                    session2.delete(rec)
        session2.commit()
        direct_purge_eval = evaluate_view(
            session2, probes, changed_ids2,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_unchanged_sigs,
        )
        session2.close()

    comparisons = {
        "directDetachMinusDepBrokenPerProbe": bootstrap_diff(
            direct_detach_eval["perProbeBrokenDerivationStale"],
            dep_eval["perProbeBrokenDerivationStale"],
            seed=SEED,
            resamples=RESAMPLES,
        ),
        "frozenMinusDepBrokenPerProbe": bootstrap_diff(
            frozen_eval["perProbeBrokenDerivationStale"],
            dep_eval["perProbeBrokenDerivationStale"],
            seed=SEED,
            resamples=RESAMPLES,
        ),
    }

    keep_fields = (
        "probeDerivedTop10Slots",
        "probeTargetSourceStaleCount",
        "probeAnyChangedSourceStaleCount",
        "probeBrokenDerivationStaleCount",
        "probeBrokenDerivationStalePerProbe",
        "probeExactStaleCount",
        "graphAcceptedDerivedCount",
        "graphPendingDerivedCount",
        "graphBrokenDerivationCount",
        "graphBrokenDerivationByKind",
        "graphExactStaleVsCleanCount",
        "cleanReferenceNormTotal",
        "cleanReferenceNormRetained",
        "cleanReferenceNormRetentionRate",
        "cleanReferenceNormFalseSuppression",
        "unchangedDirectSignatureTotal",
        "unchangedDirectSignatureRetained",
        "pending27RecoveredCount",
    )
    summary = {
        name: {m: view[m] for m in keep_fields}
        for name, view in (
            ("frozen", frozen_eval),
            ("directProvenanceDetach", direct_detach_eval),
            ("directProvenancePurge", direct_purge_eval),
            ("dependencyInvalidation", dep_eval),
            ("dependencyPlusQualityGate", dep_gate_eval),
        )
    }

    h1_confirmed = (
        dep_eval["probeBrokenDerivationStaleCount"] == 0
        and dep_gate_eval["probeBrokenDerivationStaleCount"] == 0
        and dep_eval["graphBrokenDerivationCount"] == 0
        and dep_gate_eval["graphBrokenDerivationCount"] == 0
        and comparisons["directDetachMinusDepBrokenPerProbe"]["ci95"][0] > 0
    )
    h2_confirmed = (
        dep_gate_eval["cleanReferenceNormRetentionRate"] == 1.0
        and dep_gate_eval["cleanReferenceNormFalseSuppression"] == 0
        and dep_gate_eval["cleanReferenceNormRetained"] > direct_purge_eval["cleanReferenceNormRetained"]
    )

    report = {
        "protocol": "PROSPECTIVE_EDIT_STREAM_P4_PROTOCOL_2026-11-13.md",
        "protocolSha256": protocol_sha,
        "graphExpansionSha256": ge_sha,
        "classification": "prospective confirmatory second edit stream (strictly disjoint from Stream 1)",
        "streamSelection": {
            "salt": STREAM2_SALT,
            "questionCount": len(s2_question_ids),
            "questionIds": s2_question_ids,
            "supportPassageCount": len(s2_support_keys),
            "distractorPassageCount": len(s2_distractor_keys),
            "totalNoteCount": len(s2_selected_keys),
            "postEditNoteCount": len(s2_selected_keys) - N_DELETE,
            "disjointWithStream1Questions": s1_question_ids.isdisjoint(s2_question_ids),
            "disjointWithStream1Notes": s1_selected_keys.isdisjoint(s2_selected_keys),
        },
        "hypothesesConfirmed": {
            "H1_P4_zeroBrokenDerivations": h1_confirmed,
            "H2_P4_fullCleanGraphRetentionAfterGate": h2_confirmed,
        },
        "timingsSeconds": {
            "initialBuild": initial_build_seconds,
            "directDetachOperations": direct_detach_seconds,
            "dependencyRebuild": rebuild_seconds,
            "qualityGateRecoveryPass": gate_seconds,
        },
        "qualityGateRecovery": {
            "pendingBeforePass": dep_eval["graphPendingDerivedCount"],
            "gateStats": gate_stats,
            "pendingAfterPass": dep_gate_eval["graphPendingDerivedCount"],
            "pendingUnchangedSignaturesCount": len(pending_unchanged_sigs),
            "pendingUnchangedRecoveredBeforePass": dep_eval["pending27RecoveredCount"],
            "pendingUnchangedRecoveredAfterPass": dep_gate_eval["pending27RecoveredCount"],
            "unchangedDirectSignaturesBeforePass": dep_eval["unchangedDirectSignatureRetained"],
            "unchangedDirectSignaturesAfterPass": dep_gate_eval["unchangedDirectSignatureRetained"],
            "unchangedDirectSignaturesReference": dep_eval["unchangedDirectSignatureTotal"],
        },
        "comparisons": comparisons,
        "summary": summary,
        "views": {
            "frozen": frozen_eval,
            "directProvenanceDetach": direct_detach_eval,
            "directProvenancePurge": direct_purge_eval,
            "dependencyInvalidation": dep_eval,
            "dependencyPlusQualityGate": dep_gate_eval,
        },
    }
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "streamSelection": {
                    k: v for k, v in report["streamSelection"].items() if k != "questionIds"
                },
                "hypothesesConfirmed": report["hypothesesConfirmed"],
                "timings": report["timingsSeconds"],
                "recovery": report["qualityGateRecovery"],
                "comparisons": comparisons,
                "summary": summary,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
