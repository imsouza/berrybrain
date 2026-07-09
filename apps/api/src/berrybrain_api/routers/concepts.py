from fastapi import APIRouter
from fastapi import HTTPException

from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.home_summary import list_detected_concepts
from berrybrain_api.jobs import enqueue_note_changed_jobs
from berrybrain_api.models import ConceptRecord
from berrybrain_api.sync import sync_note_record
from berrybrain_api.vault import create_note

router = APIRouter(prefix="/api/v1/concepts", tags=["concepts"])


@router.get("")
def list_concepts(limit: int = 20) -> dict:
    with SessionLocal() as session:
        return {"concepts": list_detected_concepts(session, limit=min(limit, 100))}


@router.get("/{concept_id}")
def get_concept(concept_id: int) -> dict:
    with SessionLocal() as session:
        concept = session.get(ConceptRecord, concept_id)
        if concept is None:
            raise HTTPException(status_code=404, detail="Concept not found")
        return {
            "id": concept.id,
            "name": concept.name,
            "normalizedName": concept.normalized_name,
            "description": concept.description,
            "frequency": concept.frequency,
            "relatedNoteIds": concept.related_note_ids,
            "confidence": concept.confidence,
            "status": concept.status,
            "provider": concept.provider,
            "model": concept.model,
            "sourceEvidence": concept.source_evidence,
            "createdAt": concept.created_at.isoformat() if concept.created_at else None,
            "updatedAt": concept.updated_at.isoformat() if concept.updated_at else None,
        }


@router.post("/{concept_id}/create-note")
def create_concept_note(concept_id: int) -> dict:
    settings = get_settings()
    with SessionLocal() as session:
        concept = session.get(ConceptRecord, concept_id)
        if concept is None:
            raise HTTPException(status_code=404, detail="Concept not found")
        content = "\n".join(
            [
                f"# {concept.name}",
                "",
                concept.description or "Nota permanente criada a partir de conceito detectado.",
                "",
                "## Evidencias",
                concept.source_evidence,
            ]
        )
        note = create_note(settings.vault_path, concept.name, "permanentes", content)
        record = sync_note_record(session, settings.vault_path, str(note["path"]))
        enqueue_note_changed_jobs(session, record.path, "NOTE_CREATED", record.content_hash)
        concept.status = "confirmed"
        session.commit()
        return {
            "status": "created",
            "note": {"id": record.id, "title": record.title, "path": record.path},
        }
