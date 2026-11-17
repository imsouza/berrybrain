"""Exploratory MuSiQue edit stream through BerryBrain's real vault and graph services.

Uses an isolated temporary SQLite database and vault. No production state changes.
The pre-edit graph is the naive frozen-view baseline.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
import zipfile
from collections import Counter
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.artifact_state import apply_quality_verdict
from berrybrain_api.cognitive_query import retrieve_graph
from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.graph_contracts import SYMMETRIC_EDGE_TYPES
from berrybrain_api.graph_expansion import expand_knowledge_graph
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, NoteRecord
from berrybrain_api.sync import remove_note_record, sync_note_record


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "artifact" / "inputs"
ARTIFACT = Path("/home/mtz-nas/BerryBrain_TCC_Artefato_Completo_2026-09-05.zip")
OUTPUT = ROOT / "musique-edit-stream-report.json"
N_QUESTIONS = 20
N_DISTRACTORS = 50
N_DELETE = 10
N_EDIT = 10


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def corpus_key(title: str, text: str) -> str:
    return digest(title + "\0" + text)


def entities_for_doc(doc: dict, extraction: dict) -> list[str]:
    names = extraction.get("extracted_entities") or []
    normalized = []
    seen = set()
    for name in names:
        if not isinstance(name, str):
            continue
        name = name.strip()
        if not 3 <= len(name) <= 80 or len(name.split()) > 7:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(name)
    # Bound the graph to a reproducible six entities per passage so the
    # lifecycle experiment remains tractable on the Raspberry Pi class machine.
    return normalized[:6]


def source_ids(evidence) -> set[int]:
    return {
        int(value)
        for value in evidence.metadata.get("sourceNoteIds", [])
        if str(value).isdigit()
    }


def result_key(evidence) -> str:
    metadata = evidence.metadata
    return (
        f"node:{metadata['nodeId']}"
        if "nodeId" in metadata
        else f"edge:{metadata['edgeId']}"
    )


def semantic_signature(item, node_by_id: dict[int, GraphNodeRecord]) -> str:
    source = sorted(json.loads(item.source_note_ids or "[]"))
    if isinstance(item, GraphNodeRecord):
        payload = ["node", item.type, (item.canonical_label or item.label).casefold(), source]
    else:
        left = node_by_id.get(item.source_node_id)
        right = node_by_id.get(item.target_node_id)
        endpoints = [
            (left.canonical_label or left.label).casefold() if left else "missing",
            (right.canonical_label or right.label).casefold() if right else "missing",
        ]
        if item.type in SYMMETRIC_EDGE_TYPES:
            endpoints.sort()
        payload = [
            "edge", item.type, (item.label or "").casefold(),
            *endpoints,
            source,
        ]
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def tracked_results(session, query: str) -> list[dict]:
    results, _ = retrieve_graph(session, query, limit=10)
    return [
        {
            "key": result_key(item),
            "type": item.metadata.get("type"),
            "sourceIds": sorted(source_ids(item)),
            "score": round(item.score, 6),
        }
        for item in results
        if item.metadata.get("type") != "note"
    ]


def main() -> None:
    questions = json.loads((INPUT / "musique.json").read_text())
    corpus = json.loads((INPUT / "musique_corpus.json").read_text())
    with zipfile.ZipFile(ARTIFACT) as archive:
        extracted = json.loads(
            archive.read("artifact/inputs/openie_results_ner_gpt-4o-mini.json")
        )["docs"]
    assert len(corpus) == len(extracted)
    assert all(
        x["title"] == y["title"] and x["text"] == y["text"]
        for x, y in zip(corpus, extracted)
    )

    selected_questions = sorted(questions, key=lambda q: digest(q["id"]))[:N_QUESTIONS]
    support_keys = {
        corpus_key(p["title"], p["paragraph_text"])
        for q in selected_questions
        for p in q["paragraphs"]
        if p.get("is_supporting")
    }
    by_key = {corpus_key(d["title"], d["text"]): i for i, d in enumerate(corpus)}
    assert support_keys <= by_key.keys()
    distractor_keys = sorted(
        by_key.keys() - support_keys, key=digest
    )[:N_DISTRACTORS]
    selected_keys = sorted(support_keys | set(distractor_keys))
    selected_indices = [by_key[key] for key in selected_keys]
    selection = {
        "questionIds": [q["id"] for q in selected_questions],
        "supportDocumentKeys": sorted(support_keys),
        "distractorDocumentKeys": distractor_keys,
        "corpusSize": len(corpus),
        "selectedDocumentCount": len(selected_indices),
    }

    with tempfile.TemporaryDirectory(prefix="berrybrain-musique-edit-") as temp:
        temp_path = Path(temp)
        vault = temp_path / "vault"
        vault.mkdir()
        engine = create_engine(f"sqlite:///{temp_path / 'test.sqlite3'}")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        note_by_key: dict[str, int] = {}
        concept_by_key: dict[str, list[str]] = {}
        t0 = time.monotonic()
        for index in selected_indices:
            document = corpus[index]
            key = corpus_key(document["title"], document["text"])
            relative = f"sources/{key[:20]}.md"
            path = vault / relative
            path.parent.mkdir(exist_ok=True)
            path.write_text(f"# {document['title']}\n\n{document['text']}\n")
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
        initial_graph = expand_knowledge_graph(session)
        build_seconds = round(time.monotonic() - t0, 3)

        # Published OpenIE extraction acts as the controlled reference review.
        # This uses BerryBrain's quality-gate transition so derived evidence
        # enters the same accepted retrieval path as production artifacts.
        initial_nodes = list(session.scalars(select(GraphNodeRecord)))
        initial_edges = list(session.scalars(select(GraphEdgeRecord)))
        for node in initial_nodes:
            if node.type != "note" and json.loads(node.source_note_ids or "[]"):
                apply_quality_verdict(node, "passed")
        for edge in initial_edges:
            if json.loads(edge.source_note_ids or "[]"):
                apply_quality_verdict(edge, "passed")
        session.commit()
        initial_derived_keys = {
            *(f"node:{node.id}" for node in initial_nodes if node.type != "note"),
            *(f"edge:{edge.id}" for edge in initial_edges),
        }

        # Operations are fixed by ID hash and do not inspect retrieval output.
        support_order = sorted(support_keys, key=digest)
        operations = [
            {"action": "delete", "key": key} for key in support_order[:N_DELETE]
        ] + [
            {"action": "edit", "key": key}
            for key in support_order[N_DELETE : N_DELETE + N_EDIT]
        ]
        assert len(operations) == N_DELETE + N_EDIT
        changed_ids = {note_by_key[op["key"]] for op in operations}

        # A held-out, unchanged concept from each changed source is the probe.
        # It is chosen before observing any graph result.
        probes = [
            {
                "action": op["action"],
                "sourceKey": op["key"],
                "sourceId": note_by_key[op["key"]],
                "query": next(
                    (concept for concept in concept_by_key[op["key"]]
                     if len(concept.split()) >= 2),
                    concept_by_key[op["key"]][0],
                ),
            }
            for op in operations
        ]
        for probe in probes:
            probe["frozenTop10"] = tracked_results(session, probe["query"])

        # Additional unaffected probes detect excessive invalidation.
        unchanged_keys = sorted(
            set(selected_keys) - {op["key"] for op in operations}, key=digest
        )[:20]
        unaffected_probes = [
            {
                "sourceId": note_by_key[key],
                "query": concept_by_key[key][0],
                "before": tracked_results(session, concept_by_key[key][0]),
            }
            for key in unchanged_keys
        ]
        initial_unaffected_items = {
            f"node:{node.id}" for node in initial_nodes
            if node.type != "note"
            and json.loads(node.source_note_ids or "[]")
            and not set(json.loads(node.source_note_ids or "[]")) & changed_ids
        } | {
            f"edge:{edge.id}" for edge in initial_edges
            if json.loads(edge.source_note_ids or "[]")
            and not set(json.loads(edge.source_note_ids or "[]")) & changed_ids
        }
        initial_node_by_id = {node.id: node for node in initial_nodes}
        initial_unaffected_signatures = Counter(
            semantic_signature(item, initial_node_by_id)
            for item in [*initial_nodes, *initial_edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and json.loads(item.source_note_ids or "[]")
            and not set(json.loads(item.source_note_ids or "[]")) & changed_ids
            and item.quality_gate_status == "passed"
        )
        neighbor_sources: dict[int, set[int]] = {}
        for edge in initial_edges:
            ids = set(json.loads(edge.source_note_ids or "[]"))
            neighbor_sources.setdefault(edge.source_node_id, set()).update(ids)
            neighbor_sources.setdefault(edge.target_node_id, set()).update(ids)
        initial_unaffected_context = {}
        for item in [*initial_nodes, *initial_edges]:
            if isinstance(item, GraphNodeRecord) and item.type == "note":
                continue
            direct = set(json.loads(item.source_note_ids or "[]"))
            if not direct or direct & changed_ids or item.quality_gate_status != "passed":
                continue
            if isinstance(item, GraphNodeRecord):
                indirect = neighbor_sources.get(item.id, set())
            else:
                indirect = set()
                for endpoint in (item.source_node_id, item.target_node_id):
                    node = initial_node_by_id.get(endpoint)
                    if node:
                        indirect.update(json.loads(node.source_note_ids or "[]"))
            initial_unaffected_context[semantic_signature(item, initial_node_by_id)] = {
                "directSourceIds": sorted(direct),
                "indirectSourceIds": sorted(indirect),
                "indirectChanged": bool(indirect & changed_ids),
            }

        per_operation = []
        for op in operations:
            key = op["key"]
            note_id = note_by_key[key]
            relative = f"sources/{key[:20]}.md"
            start = time.monotonic()
            if op["action"] == "delete":
                (vault / relative).unlink()
                remove_note_record(session, relative, vault)
            else:
                (vault / relative).write_text(
                    "# Corrected source\n\nThe earlier passage has been retracted.\n"
                )
                note = sync_note_record(session, vault, relative)
                upsert_generated_metadata(
                    session, note.id, "concepts", {"concepts": []},
                    note.content_hash, model_used="authored-correction-v1",
                )
            per_operation.append({
                "action": op["action"], "sourceId": note_id,
                "seconds": round(time.monotonic() - start, 3),
            })

        rebuild_start = time.monotonic()
        final_graph = expand_knowledge_graph(session)
        final_rebuild_seconds = round(time.monotonic() - rebuild_start, 3)

        for probe in probes:
            probe["afterTop10"] = tracked_results(session, probe["query"])
        for probe in unaffected_probes:
            probe["after"] = tracked_results(session, probe["query"])

        def residue(items: list[dict], source_id: int) -> int:
            return sum(source_id in item["sourceIds"] for item in items)

        frozen_residue = sum(
            residue(p["frozenTop10"], p["sourceId"]) for p in probes
        )
        after_residue = sum(
            residue(p["afterTop10"], p["sourceId"]) for p in probes
        )
        graph_nodes = list(session.scalars(select(GraphNodeRecord)))
        graph_edges = list(session.scalars(select(GraphEdgeRecord)))
        surviving_keys = {
            *(f"node:{node.id}" for node in graph_nodes if node.type != "note"),
            *(f"edge:{edge.id}" for edge in graph_edges),
        }
        retained_unchanged = initial_unaffected_items & surviving_keys
        final_node_by_id = {node.id: node for node in graph_nodes}
        final_unaffected_signatures = Counter(
            semantic_signature(item, final_node_by_id)
            for item in [*graph_nodes, *graph_edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and json.loads(item.source_note_ids or "[]")
            and not set(json.loads(item.source_note_ids or "[]")) & changed_ids
            and item.quality_gate_status == "passed"
        )
        final_unaffected_all_statuses: dict[str, list[str]] = {}
        for item in [*graph_nodes, *graph_edges]:
            if isinstance(item, GraphNodeRecord) and item.type == "note":
                continue
            direct = set(json.loads(item.source_note_ids or "[]"))
            if not direct or direct & changed_ids:
                continue
            signature = semantic_signature(item, final_node_by_id)
            final_unaffected_all_statuses.setdefault(signature, []).append(
                item.quality_gate_status
            )
        retained_semantic = initial_unaffected_signatures & final_unaffected_signatures
        lost_semantic = initial_unaffected_signatures - final_unaffected_signatures
        lost_with_indirect_change = sum(
            count for key, count in lost_semantic.items()
            if initial_unaffected_context.get(key, {}).get("indirectChanged")
        )
        lost_present_unadmitted = sum(
            min(count, sum(status != "passed" for status in final_unaffected_all_statuses.get(key, [])))
            for key, count in lost_semantic.items()
        )
        lost_without_indirect_present = sum(
            min(count, sum(status != "passed" for status in final_unaffected_all_statuses.get(key, [])))
            for key, count in lost_semantic.items()
            if not initial_unaffected_context.get(key, {}).get("indirectChanged")
        )
        surviving_stale_provenance = sum(
            bool(set(json.loads(item.source_note_ids or "[]")) & changed_ids)
            for item in [*graph_nodes, *graph_edges]
            if (item.type != "note" if isinstance(item, GraphNodeRecord) else True)
            and (f"node:{item.id}" if isinstance(item, GraphNodeRecord) else f"edge:{item.id}")
            in initial_derived_keys
        )
        report = {
            "design": "exploratory actual-service edit stream versus frozen derived graph",
            "selection": selection,
            "sourceHashes": {
                "questions": hashlib.sha256((INPUT / "musique.json").read_bytes()).hexdigest(),
                "corpus": hashlib.sha256((INPUT / "musique_corpus.json").read_bytes()).hexdigest(),
                "openieZip": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
                "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            },
            "initialGraph": initial_graph,
            "finalGraph": final_graph,
            "buildSeconds": build_seconds,
            "finalRebuildSeconds": final_rebuild_seconds,
            "operations": per_operation,
            "metrics": {
                "probeCount": len(probes),
                "frozenStaleAt10Count": frozen_residue,
                "afterStaleAt10Count": after_residue,
                "frozenStaleAt10PerProbe": round(frozen_residue / len(probes), 4),
                "afterStaleAt10PerProbe": round(after_residue / len(probes), 4),
                "referenceUnchangedEvidenceCount": len(initial_unaffected_items),
                "retainedUnchangedEvidenceCount": len(retained_unchanged),
                "unaffectedEvidenceRetention": (
                    round(len(retained_unchanged) / len(initial_unaffected_items), 4)
                    if initial_unaffected_items else None
                ),
                "referenceUnchangedSemanticCount": sum(initial_unaffected_signatures.values()),
                "retainedUnchangedSemanticCount": sum(retained_semantic.values()),
                "unaffectedSemanticRetention": (
                    round(sum(retained_semantic.values()) / sum(initial_unaffected_signatures.values()), 4)
                    if initial_unaffected_signatures else None
                ),
                "lostUnchangedSemanticByKind": dict(Counter(
                    json.loads(key)[0] for key, count in lost_semantic.items()
                    for _ in range(count)
                )),
                "lostWithIndirectChangedSourceCount": lost_with_indirect_change,
                "lostWithoutRecordedIndirectChangedSourceCount": (
                    sum(lost_semantic.values()) - lost_with_indirect_change
                ),
                "lostPresentButUnadmittedCount": lost_present_unadmitted,
                "lostAbsentAfterRebuildCount": sum(lost_semantic.values()) - lost_present_unadmitted,
                "lostWithoutIndirectPresentButUnadmittedCount": lost_without_indirect_present,
                "lostWithoutIndirectAbsentCount": (
                    sum(lost_semantic.values()) - lost_with_indirect_change
                    - lost_without_indirect_present
                ),
                "survivingChangedSourceProvenanceCount": surviving_stale_provenance,
                "operationMedianSeconds": sorted(x["seconds"] for x in per_operation)[len(per_operation)//2],
            },
            "probes": probes,
            "unaffectedProbes": unaffected_probes,
            "operationTypeCounts": dict(Counter(x["action"] for x in per_operation)),
            "lostUnchangedSemanticDetails": [
                {
                    "signature": json.loads(key),
                    "count": count,
                    "finalQualityStatuses": final_unaffected_all_statuses.get(key, []),
                    **initial_unaffected_context.get(key, {}),
                }
                for key, count in sorted(lost_semantic.items())
            ],
        }
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps({"metrics": report["metrics"], "initialGraph": initial_graph}, indent=2))
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
