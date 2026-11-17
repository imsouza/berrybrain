"""MuSiQue edit-stream B4 comparative study: direct-provenance baselines and pending recovery.

Protocol: EDIT_STREAM_B4_PROTOCOL_2026-11-01.md.
Reproduces the exact 99-note vault, 20 operations, and 20 probes of musique_edit_stream.py,
adds direct-provenance-only comparators and a clean post-edit ground-truth reference graph,
and measures recovery of the 27 pending unchanged-source signatures after one quality-gate pass.
"""

from __future__ import annotations

import json
import random
import re
import statistics
import sys
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import berrybrain_api.models  # noqa: F401, E402
from berrybrain_api.artifact_state import apply_quality_verdict  # noqa: E402
from berrybrain_api.cognitive_query import retrieve_graph  # noqa: E402
from berrybrain_api.database import Base  # noqa: E402
from berrybrain_api.generated_metadata import upsert_generated_metadata  # noqa: E402
from berrybrain_api.graph_contracts import SYMMETRIC_EDGE_TYPES  # noqa: E402
from berrybrain_api.graph_expansion import expand_knowledge_graph  # noqa: E402
from berrybrain_api.graph_ontology import validate_node_name  # noqa: E402
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, NoteRecord  # noqa: E402
from berrybrain_api.sync import remove_note_record, sync_note_record  # noqa: E402
from musique_edit_stream import (  # noqa: E402
    ARTIFACT,
    INPUT,
    N_DELETE,
    N_DISTRACTORS,
    N_EDIT,
    N_QUESTIONS,
    corpus_key,
    digest,
    entities_for_doc,
    semantic_signature,
)

OPENIE_DIRECT = ROOT / "external-corpus" / "openie_results_ner_gpt-4o-mini.json"
OUTPUT = ROOT / "musique-edit-stream-b4-report.json"
SEED = 20261101
RESAMPLES = 10_000

_LINKS_COUNT_RE = re.compile(r'^(connection pattern: ".+" links )\d+( notes)$')


def normalize_insight_count(label_cf: str) -> str:
    return _LINKS_COUNT_RE.sub(r"\1>=2\2", label_cf)


def semantic_key(item, node_by_id: dict[int, GraphNodeRecord], *, normalize_counts: bool = False) -> str:
    if isinstance(item, GraphNodeRecord):
        lbl = (item.canonical_label or item.label).casefold()
        if normalize_counts:
            lbl = normalize_insight_count(lbl)
        payload = ["node", item.type, lbl]
    else:
        left = node_by_id.get(item.source_node_id)
        right = node_by_id.get(item.target_node_id)
        l_lbl = (left.canonical_label or left.label).casefold() if left else "missing"
        r_lbl = (right.canonical_label or right.label).casefold() if right else "missing"
        if normalize_counts:
            l_lbl = normalize_insight_count(l_lbl)
            r_lbl = normalize_insight_count(r_lbl)
        endpoints = [l_lbl, r_lbl]
        if item.type in SYMMETRIC_EDGE_TYPES:
            endpoints.sort()
        payload = ["edge", item.type, (item.label or "").casefold(), *endpoints]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def load_openie_docs() -> list[dict]:
    if OPENIE_DIRECT.exists():
        return json.loads(OPENIE_DIRECT.read_text(encoding="utf-8"))["docs"]
    with zipfile.ZipFile(ARTIFACT) as archive:
        return json.loads(
            archive.read("artifact/inputs/openie_results_ner_gpt-4o-mini.json")
        )["docs"]


def admit_valid_derived_items(session) -> tuple[dict[str, int], float]:
    """Run one post-rebuild quality-gate worker pass over pending nodes and edges."""
    t0 = time.perf_counter()
    active_note_ids = set(
        session.scalars(
            select(NoteRecord.id).where(NoteRecord.evidence_status == "eligible")
        )
    )
    nodes = list(session.scalars(select(GraphNodeRecord)))
    node_by_id = {n.id: n for n in nodes}
    admitted_nodes = 0
    rejected_nodes = 0
    for node in nodes:
        if node.type == "note" or node.quality_gate_status != "pending":
            continue
        srcs = set(json.loads(node.source_note_ids or "[]"))
        issues = validate_node_name(node.type, node.label)
        if srcs and srcs <= active_note_ids and not issues:
            apply_quality_verdict(node, "passed")
            admitted_nodes += 1
        else:
            rejected_nodes += 1
    admitted_edges = 0
    rejected_edges = 0
    for edge in list(session.scalars(select(GraphEdgeRecord))):
        if edge.quality_gate_status != "pending":
            continue
        srcs = set(json.loads(edge.source_note_ids or "[]"))
        left = node_by_id.get(edge.source_node_id)
        right = node_by_id.get(edge.target_node_id)
        left_ok = left is not None and (left.type == "note" or left.quality_gate_status == "passed")
        right_ok = right is not None and (right.type == "note" or right.quality_gate_status == "passed")
        if srcs and srcs <= active_note_ids and left_ok and right_ok:
            apply_quality_verdict(edge, "passed")
            admitted_edges += 1
        else:
            rejected_edges += 1
    session.commit()
    elapsed = round(time.perf_counter() - t0, 4)
    return {
        "admittedNodes": admitted_nodes,
        "admittedEdges": admitted_edges,
        "admittedTotal": admitted_nodes + admitted_edges,
        "unadmittedNodes": rejected_nodes,
        "unadmittedEdges": rejected_edges,
    }, elapsed


def tracked_results(session, query: str) -> list[dict]:
    nodes = {n.id: n for n in session.scalars(select(GraphNodeRecord))}
    edges = {e.id: e for e in session.scalars(select(GraphEdgeRecord))}
    results, _ = retrieve_graph(session, query, limit=10)
    out = []
    for item in results:
        if item.metadata.get("type") == "note":
            continue
        if "nodeId" in item.metadata:
            nid = int(item.metadata["nodeId"])
            rec = nodes.get(nid)
            skey_exact = semantic_key(rec, nodes, normalize_counts=False) if rec else f'["node","missing","{nid}"]'
            skey_norm = semantic_key(rec, nodes, normalize_counts=True) if rec else skey_exact
            key = f"node:{nid}"
        else:
            eid = int(item.metadata["edgeId"])
            rec = edges.get(eid)
            skey_exact = semantic_key(rec, nodes, normalize_counts=False) if rec else f'["edge","missing","{eid}"]'
            skey_norm = semantic_key(rec, nodes, normalize_counts=True) if rec else skey_exact
            key = f"edge:{eid}"
        srcs = sorted(
            int(v) for v in item.metadata.get("sourceNoteIds", []) if str(v).isdigit()
        )
        out.append(
            {
                "key": key,
                "type": item.metadata.get("type"),
                "label": getattr(rec, "label", ""),
                "semanticKeyExact": skey_exact,
                "semanticKeyNorm": skey_norm,
                "sourceIds": srcs,
                "score": round(item.score, 6),
            }
        )
    return out


def bootstrap_diff(a: list[float], b: list[float], seed: int = SEED, resamples: int = RESAMPLES) -> dict:
    assert len(a) == len(b)
    n = len(a)
    diffs = [x - y for x, y in zip(a, b, strict=True)]
    rng = random.Random(seed)
    means = sorted(
        statistics.fmean(diffs[rng.randrange(n)] for _ in range(n))
        for _ in range(resamples)
    )
    return {
        "meanDifference": round(statistics.fmean(diffs), 4),
        "ci95": [
            round(means[int(0.025 * resamples)], 4),
            round(means[int(0.975 * resamples)], 4),
        ],
    }


def build_initial_vault(temp_path: Path, corpus: list[dict], extracted: list[dict], selected_indices: list[int]):
    vault = temp_path / "vault"
    vault.mkdir()
    engine = create_engine(f"sqlite:///{temp_path / 'test.sqlite3'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
    note_by_key: dict[str, int] = {}
    concept_by_key: dict[str, list[str]] = {}
    for index in selected_indices:
        document = corpus[index]
        key = corpus_key(document["title"], document["text"])
        relative = f"sources/{key[:20]}.md"
        path = vault / relative
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"# {document['title']}\n\n{document['text']}\n", encoding="utf-8")
        note = sync_note_record(session, vault, relative)
        concepts = entities_for_doc(document, extracted[index])
        if document["title"] not in concepts:
            concepts.insert(0, document["title"])
        concept_by_key[key] = concepts
        upsert_generated_metadata(
            session,
            note.id,
            "concepts",
            {"concepts": concepts},
            note.content_hash,
            model_used="published-musicque-openie-gpt-4o-mini",
        )
        note_by_key[key] = note.id
    expand_knowledge_graph(session)
    for node in session.scalars(select(GraphNodeRecord)):
        if node.type != "note" and json.loads(node.source_note_ids or "[]"):
            apply_quality_verdict(node, "passed")
    for edge in session.scalars(select(GraphEdgeRecord)):
        if json.loads(edge.source_note_ids or "[]"):
            apply_quality_verdict(edge, "passed")
    session.commit()
    return vault, session, note_by_key, concept_by_key


def build_clean_post_edit_reference(
    corpus: list[dict],
    extracted: list[dict],
    selected_indices: list[int],
    delete_keys: set[str],
    edit_keys: set[str],
) -> tuple[Counter, set[str], Counter, set[str]]:
    """Build ground-truth post-update graph G_clean(D') from scratch on the 89 notes."""
    with tempfile.TemporaryDirectory(prefix="berrybrain-b4-clean-") as temp:
        temp_path = Path(temp)
        vault = temp_path / "vault"
        vault.mkdir()
        engine = create_engine(f"sqlite:///{temp_path / 'clean.sqlite3'}")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        for index in selected_indices:
            document = corpus[index]
            key = corpus_key(document["title"], document["text"])
            if key in delete_keys:
                continue
            relative = f"sources/{key[:20]}.md"
            path = vault / relative
            path.parent.mkdir(exist_ok=True)
            if key in edit_keys:
                path.write_text(
                    "# Corrected source\n\nThe earlier passage has been retracted.\n",
                    encoding="utf-8",
                )
                note = sync_note_record(session, vault, relative)
                upsert_generated_metadata(
                    session, note.id, "concepts", {"concepts": []},
                    note.content_hash, model_used="authored-correction-v1",
                )
            else:
                path.write_text(f"# {document['title']}\n\n{document['text']}\n", encoding="utf-8")
                note = sync_note_record(session, vault, relative)
                concepts = entities_for_doc(document, extracted[index])
                if document["title"] not in concepts:
                    concepts.insert(0, document["title"])
                upsert_generated_metadata(
                    session, note.id, "concepts", {"concepts": concepts},
                    note.content_hash, model_used="published-musicque-openie-gpt-4o-mini",
                )
        expand_knowledge_graph(session)
        nodes = list(session.scalars(select(GraphNodeRecord)))
        edges = list(session.scalars(select(GraphEdgeRecord)))
        for node in nodes:
            if node.type != "note" and json.loads(node.source_note_ids or "[]"):
                apply_quality_verdict(node, "passed")
        for edge in edges:
            if json.loads(edge.source_note_ids or "[]"):
                apply_quality_verdict(edge, "passed")
        session.commit()
        node_by_id = {n.id: n for n in nodes}
        derived = [
            item for item in [*nodes, *edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and item.quality_gate_status == "passed"
        ]
        exact_counts = Counter(semantic_key(item, node_by_id, normalize_counts=False) for item in derived)
        norm_counts = Counter(semantic_key(item, node_by_id, normalize_counts=True) for item in derived)
        session.close()
        return exact_counts, set(exact_counts.keys()), norm_counts, set(norm_counts.keys())


def evaluate_view(
    session,
    probes: list[dict],
    changed_ids: set[int],
    clean_exact_counts: Counter,
    clean_exact_set: set[str],
    clean_norm_counts: Counter,
    clean_norm_set: set[str],
    initial_unaffected_sigs: Counter,
    pending_27_sigs: set[str],
) -> dict:
    nodes = list(session.scalars(select(GraphNodeRecord)))
    edges = list(session.scalars(select(GraphEdgeRecord)))
    node_by_id = {n.id: n for n in nodes}

    accepted_derived = [
        item for item in [*nodes, *edges]
        if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
        and item.quality_gate_status == "passed"
    ]
    pending_derived = [
        item for item in [*nodes, *edges]
        if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
        and item.quality_gate_status == "pending"
    ]

    view_exact = Counter(semantic_key(item, node_by_id, normalize_counts=False) for item in accepted_derived)
    view_norm = Counter(semantic_key(item, node_by_id, normalize_counts=True) for item in accepted_derived)
    view_sigs = Counter(semantic_signature(item, node_by_id) for item in accepted_derived)

    graph_broken_derivation = sum((view_norm - clean_norm_counts).values())
    graph_broken_by_kind = Counter(
        json.loads(k)[0] + ":" + json.loads(k)[1]
        for k, c in (view_norm - clean_norm_counts).items()
        for _ in range(c)
    )
    graph_exact_stale = sum((view_exact - clean_exact_counts).values())
    graph_direct_changed_prov = sum(
        1 for item in accepted_derived
        if set(json.loads(item.source_note_ids or "[]")) & changed_ids
    )
    clean_norm_retained = sum((clean_norm_counts & view_norm).values())
    clean_norm_missing = sum((clean_norm_counts - view_norm).values())
    unaffected_sig_retained = sum((initial_unaffected_sigs & view_sigs).values())
    pending_27_recovered = sum(1 for sig in pending_27_sigs if view_sigs.get(sig, 0) > 0)

    per_probe_target_source_stale = []
    per_probe_any_changed_source_stale = []
    per_probe_broken_derivation_stale = []
    per_probe_exact_stale = []
    total_derived_slots = 0
    probe_details = []
    for p in probes:
        res = tracked_results(session, p["query"])
        total_derived_slots += len(res)
        target_stale = sum(1 for r in res if p["sourceId"] in r["sourceIds"])
        any_changed_stale = sum(1 for r in res if (set(r["sourceIds"]) & changed_ids))
        broken_stale = sum(
            1 for r in res
            if (set(r["sourceIds"]) & changed_ids) or (r["semanticKeyNorm"] not in clean_norm_set)
        )
        exact_stale = sum(
            1 for r in res
            if (set(r["sourceIds"]) & changed_ids) or (r["semanticKeyExact"] not in clean_exact_set)
        )
        per_probe_target_source_stale.append(target_stale)
        per_probe_any_changed_source_stale.append(any_changed_stale)
        per_probe_broken_derivation_stale.append(broken_stale)
        per_probe_exact_stale.append(exact_stale)
        probe_details.append(
            {
                "query": p["query"],
                "action": p["action"],
                "sourceId": p["sourceId"],
                "derivedSlots": len(res),
                "targetSourceStaleCount": target_stale,
                "anyChangedSourceStaleCount": any_changed_stale,
                "brokenDerivationStaleCount": broken_stale,
                "exactStaleCount": exact_stale,
                "brokenExamples": [
                    {"type": r["type"], "label": r["label"], "sourceIds": r["sourceIds"]}
                    for r in res
                    if (set(r["sourceIds"]) & changed_ids) or (r["semanticKeyNorm"] not in clean_norm_set)
                ][:3],
            }
        )

    return {
        "probeDerivedTop10Slots": total_derived_slots,
        "probeTargetSourceStaleCount": sum(per_probe_target_source_stale),
        "probeAnyChangedSourceStaleCount": sum(per_probe_any_changed_source_stale),
        "probeBrokenDerivationStaleCount": sum(per_probe_broken_derivation_stale),
        "probeBrokenDerivationStalePerProbe": round(statistics.fmean(per_probe_broken_derivation_stale), 4),
        "probeExactStaleCount": sum(per_probe_exact_stale),
        "perProbeBrokenDerivationStale": per_probe_broken_derivation_stale,
        "perProbeTargetSourceStale": per_probe_target_source_stale,
        "graphAcceptedDerivedCount": len(accepted_derived),
        "graphPendingDerivedCount": len(pending_derived),
        "graphDirectChangedProvenanceCount": graph_direct_changed_prov,
        "graphBrokenDerivationCount": graph_broken_derivation,
        "graphBrokenDerivationByKind": dict(graph_broken_by_kind),
        "graphExactStaleVsCleanCount": graph_exact_stale,
        "cleanReferenceNormTotal": sum(clean_norm_counts.values()),
        "cleanReferenceNormRetained": clean_norm_retained,
        "cleanReferenceNormRetentionRate": round(
            clean_norm_retained / max(1, sum(clean_norm_counts.values())), 4
        ),
        "cleanReferenceNormFalseSuppression": clean_norm_missing,
        "unchangedDirectSignatureTotal": sum(initial_unaffected_sigs.values()),
        "unchangedDirectSignatureRetained": unaffected_sig_retained,
        "pending27RecoveredCount": pending_27_recovered,
        "probes": probe_details,
    }


def main() -> None:
    questions = json.loads((INPUT / "musique.json").read_text(encoding="utf-8"))
    corpus = json.loads((INPUT / "musique_corpus.json").read_text(encoding="utf-8"))
    extracted = load_openie_docs()
    assert len(corpus) == len(extracted)

    orig_report = json.loads((ROOT / "musique-edit-stream-report.json").read_text(encoding="utf-8"))
    pending_27_sigs = {
        json.dumps(row["signature"], ensure_ascii=False, separators=(",", ":"))
        for row in orig_report["lostUnchangedSemanticDetails"]
        if not row["indirectChanged"]
    }
    assert len(pending_27_sigs) == 27

    selected_questions = sorted(questions, key=lambda q: digest(q["id"]))[:N_QUESTIONS]
    support_keys = {
        corpus_key(p["title"], p["paragraph_text"])
        for q in selected_questions
        for p in q["paragraphs"]
        if p.get("is_supporting")
    }
    by_key = {corpus_key(d["title"], d["text"]): i for i, d in enumerate(corpus)}
    distractor_keys = sorted(by_key.keys() - support_keys, key=digest)[:N_DISTRACTORS]
    selected_keys = sorted(support_keys | set(distractor_keys))
    selected_indices = [by_key[key] for key in selected_keys]

    support_order = sorted(support_keys, key=digest)
    delete_keys = set(support_order[:N_DELETE])
    edit_keys = set(support_order[N_DELETE : N_DELETE + N_EDIT])
    operations = (
        [{"action": "delete", "key": k} for k in support_order[:N_DELETE]]
        + [{"action": "edit", "key": k} for k in support_order[N_DELETE : N_DELETE + N_EDIT]]
    )

    clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set = build_clean_post_edit_reference(
        corpus, extracted, selected_indices, delete_keys, edit_keys
    )

    with tempfile.TemporaryDirectory(prefix="berrybrain-b4-main-") as temp:
        vault, session, note_by_key, concept_by_key = build_initial_vault(
            Path(temp), corpus, extracted, selected_indices
        )
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
            initial_unaffected_sigs, pending_27_sigs,
        )

        # Apply the 20 source updates (triggers _detach_note_graph_provenance, BEFORE expand_knowledge_graph)
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

        # 2. Direct-provenance-only detach baseline
        direct_detach_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_27_sigs,
        )

        # 3. BerryBrain dependency-propagating rebuild
        t_reb0 = time.perf_counter()
        expand_knowledge_graph(session)
        rebuild_seconds = round(time.perf_counter() - t_reb0, 3)
        dep_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_27_sigs,
        )

        # 4. Post-rebuild quality-gate worker admission pass
        gate_stats, gate_seconds = admit_valid_derived_items(session)
        dep_gate_eval = evaluate_view(
            session, probes, changed_ids,
            clean_exact_counts, clean_exact_set, clean_norm_counts, clean_norm_set,
            initial_unaffected_sigs, pending_27_sigs,
        )
        session.close()

    # Run 2: Strict direct-provenance purge baseline
    with tempfile.TemporaryDirectory(prefix="berrybrain-b4-purge-") as temp:
        vault2, session2, note_by_key2, _ = build_initial_vault(
            Path(temp), corpus, extracted, selected_indices
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
            initial_unaffected_sigs, pending_27_sigs,
        )
        session2.close()

    comparisons = {
        "directDetachMinusDepBrokenPerProbe": bootstrap_diff(
            direct_detach_eval["perProbeBrokenDerivationStale"],
            dep_eval["perProbeBrokenDerivationStale"],
        ),
        "frozenMinusDepBrokenPerProbe": bootstrap_diff(
            frozen_eval["perProbeBrokenDerivationStale"],
            dep_eval["perProbeBrokenDerivationStale"],
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

    report = {
        "protocol": "EDIT_STREAM_B4_PROTOCOL_2026-11-01.md",
        "classification": "post-hoc comparative lifecycle baseline and worker-recovery analysis",
        "replicatesOriginal25OctExactNumbers": {
            "frozenTargetSourceStaleAt10": frozen_eval["probeTargetSourceStaleCount"],
            "depTargetSourceStaleAt10": dep_eval["probeTargetSourceStaleCount"],
            "unchangedDirectSignaturesInitial": dep_eval["unchangedDirectSignatureTotal"],
            "unchangedDirectSignaturesAfterDep": dep_eval["unchangedDirectSignatureRetained"],
        },
        "timingsSeconds": {
            "directDetachOperations": direct_detach_seconds,
            "dependencyRebuild": rebuild_seconds,
            "qualityGateRecoveryPass": gate_seconds,
        },
        "qualityGateRecovery": {
            "pendingBeforePass": dep_eval["graphPendingDerivedCount"],
            "gateStats": gate_stats,
            "pendingAfterPass": dep_gate_eval["graphPendingDerivedCount"],
            "pending27BeforePass": dep_eval["pending27RecoveredCount"],
            "pending27AfterPass": dep_gate_eval["pending27RecoveredCount"],
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
                "replicates25Oct": report["replicatesOriginal25OctExactNumbers"],
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
