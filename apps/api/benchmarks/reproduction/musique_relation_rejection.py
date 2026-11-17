"""MuSiQue-corpus rejection stream using BerryBrain's real graph write service."""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
import zipfile
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

import berrybrain_api.models  # noqa: F401
from berrybrain_api.artifact_state import accepted_edge_clause, apply_quality_verdict
from berrybrain_api.database import Base
from berrybrain_api.generated_metadata import upsert_generated_metadata
from berrybrain_api.graph_expansion import expand_knowledge_graph
from berrybrain_api.graph_feedback import edge_artifact_key, resolve_feedback
from berrybrain_api.graph_write_service import GraphWriteService
from berrybrain_api.models import GraphEdgeRecord, GraphNodeRecord, NoteRecord
from berrybrain_api.sync import sync_note_record

from musique_edit_stream import (
    ARTIFACT,
    INPUT,
    ROOT,
    corpus_key,
    digest,
    entities_for_doc,
    semantic_signature,
)

OUTPUT = ROOT / "musique-relation-rejection-report.json"
N_DOCUMENTS = 40
N_REJECTIONS = 5


def main() -> None:
    corpus = json.loads((INPUT / "musique_corpus.json").read_text())
    with zipfile.ZipFile(ARTIFACT) as archive:
        extracted = json.loads(
            archive.read("artifact/inputs/openie_results_ner_gpt-4o-mini.json")
        )["docs"]
    assert len(corpus) == len(extracted)
    chosen = sorted(
        range(len(corpus)),
        key=lambda i: digest(corpus_key(corpus[i]["title"], corpus[i]["text"])),
    )[:N_DOCUMENTS]

    with tempfile.TemporaryDirectory(prefix="berrybrain-musique-reject-") as temp:
        vault = Path(temp) / "vault"
        vault.mkdir()
        engine = create_engine(f"sqlite:///{Path(temp) / 'test.sqlite3'}")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine, autoflush=False, autocommit=False)()
        for index in chosen:
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
            upsert_generated_metadata(
                session,
                note.id,
                "concepts",
                {"concepts": concepts},
                note.content_hash,
                model_used="published-musicque-openie-gpt-4o-mini",
            )
        started = time.monotonic()
        initial_graph = expand_knowledge_graph(session)
        initial_build_seconds = round(time.monotonic() - started, 3)
        nodes = list(session.scalars(select(GraphNodeRecord)))
        edges = list(session.scalars(select(GraphEdgeRecord)))
        node_by_id = {node.id: node for node in nodes}
        for node in nodes:
            if node.type != "note" and json.loads(node.source_note_ids or "[]"):
                apply_quality_verdict(node, "passed")
        for edge in edges:
            if json.loads(edge.source_note_ids or "[]"):
                apply_quality_verdict(edge, "passed")
        session.commit()

        candidates = [
            edge for edge in edges
            if edge.type == "related"
            and edge.status not in {"ignored", "archived", "stale"}
            and json.loads(edge.source_note_ids or "[]")
        ]
        chosen_edges = sorted(
            candidates,
            key=lambda edge: digest(semantic_signature(edge, node_by_id)),
        )[:N_REJECTIONS]
        if len(chosen_edges) != N_REJECTIONS:
            raise RuntimeError("Not enough eligible graph relations")
        selections = []
        writer = GraphWriteService(session)
        for edge in chosen_edges:
            source = node_by_id[edge.source_node_id]
            target = node_by_id[edge.target_node_id]
            ids = json.loads(edge.source_note_ids or "[]")
            key = edge_artifact_key(source, target, edge.type)
            signature = semantic_signature(edge, node_by_id)
            began = time.monotonic()
            deleted = writer.delete_edge(
                edge.id, reason="Experimental user rejection", user_decision=True
            )
            selections.append({
                "signature": json.loads(signature),
                "artifactKey": key,
                "sourceIds": ids,
                "deleted": deleted,
                "deleteSeconds": round(time.monotonic() - began, 3),
            })
        rebuild_started = time.monotonic()
        final_graph = expand_knowledge_graph(session)
        rebuild_seconds = round(time.monotonic() - rebuild_started, 3)
        final_nodes = {node.id: node for node in session.scalars(select(GraphNodeRecord))}
        final_edges = list(session.scalars(select(GraphEdgeRecord)))
        accepted_edges = list(
            session.scalars(select(GraphEdgeRecord).where(accepted_edge_clause()))
        )
        accepted_signatures = {
            semantic_signature(edge, final_nodes) for edge in accepted_edges
        }
        final_by_signature: dict[str, list[GraphEdgeRecord]] = {}
        for edge in final_edges:
            final_by_signature.setdefault(
                semantic_signature(edge, final_nodes), []
            ).append(edge)
        raw_final_signatures = {
            semantic_signature(edge, final_nodes) for edge in final_edges
        }
        for row in selections:
            key = json.dumps(row["signature"], ensure_ascii=False, separators=(",", ":"))
            decision = resolve_feedback(
                session,
                artifact_kind="edge",
                artifact_key=row["artifactKey"],
                source_note_ids=row["sourceIds"],
            )
            row["reappearedAccepted"] = key in accepted_signatures
            row["retainedRawRow"] = key in raw_final_signatures
            row["finalStates"] = [
                {
                    "status": edge.status,
                    "semanticStatus": edge.semantic_status,
                    "qualityGateStatus": edge.quality_gate_status,
                }
                for edge in final_by_signature.get(key, [])
            ]
            row["feedbackAction"] = decision.action if decision else None
        report = {
            "classification": "exploratory corpus-scale user-rejection contract",
            "selection": {
                "documentCount": N_DOCUMENTS,
                "documentKeys": [
                    corpus_key(corpus[i]["title"], corpus[i]["text"])
                    for i in chosen
                ],
                "rejectedRelationCount": N_REJECTIONS,
                "relationRule": "five lowest SHA256 semantic signatures of active related edges",
            },
            "sourceHashes": {
                "script": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "semanticSignatureHelper": hashlib.sha256(
                    (ROOT / "musique_edit_stream.py").read_bytes()
                ).hexdigest(),
                "corpus": hashlib.sha256((INPUT / "musique_corpus.json").read_bytes()).hexdigest(),
                "openieZip": hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(),
            },
            "initialGraph": initial_graph,
            "finalGraph": final_graph,
            "initialBuildSeconds": initial_build_seconds,
            "rebuildSeconds": rebuild_seconds,
            "rejections": selections,
            "metrics": {
                "rejectedRelations": len(selections),
                "activeFeedbackCount": sum(row["feedbackAction"] == "deleted" for row in selections),
                "reappearedAcceptedCount": sum(bool(row["reappearedAccepted"]) for row in selections),
                "suppressedTombstoneCount": sum(
                    any(state["status"] == "ignored" and state["semanticStatus"] == "quarantined"
                        for state in row["finalStates"])
                    for row in selections
                ),
            },
        }
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        print(json.dumps(report["metrics"]))
        session.close()
        engine.dispose()


if __name__ == "__main__":
    main()
