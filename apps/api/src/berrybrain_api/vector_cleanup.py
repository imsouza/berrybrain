"""Transactional invalidation outbox; retries never generate embeddings."""

import json
import logging
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from berrybrain_api.filesystem import serialized_vault
from berrybrain_api.models import NoteRecord, SettingRecord

REGISTRY = "internal.vector_registry."
PENDING = "internal.vector_cleanup."


def register_collection(
    session: Session, store: str, url: str, collection: str
) -> None:
    import hashlib

    value = json.dumps(
        {"store": store, "url": url.rstrip("/"), "collection": collection},
        sort_keys=True,
    )
    key = REGISTRY + hashlib.sha256(value.encode()).hexdigest()
    if session.scalar(select(SettingRecord.id).where(SettingRecord.key == key)) is None:
        session.add(SettingRecord(key=key, value=value))


def queue_vector_cleanup(
    session: Session, note: NoteRecord, *, attachment_id: int | None = None
) -> None:
    targets = [
        json.loads(value)
        for value in session.scalars(
            select(SettingRecord.value).where(
                SettingRecord.key.startswith(REGISTRY, autoescape=True)
            )
        )
    ]
    if not targets:
        return
    match = {
        "source": "berrybrain",
        "note_id": note.id,
        "note_stable_id": note.stable_id,
    }
    if attachment_id is not None:
        match["attachment_id"] = attachment_id
    else:
        match["content_hash"] = note.content_hash
    session.add(
        SettingRecord(
            key=PENDING + uuid4().hex,
            value=json.dumps(
                {
                    "targets": targets,
                    "match": match,
                }
            ),
        )
    )


@serialized_vault
def drain_vector_cleanup(session: Session) -> dict[str, int]:
    from urllib.parse import quote

    from berrybrain_api.vector_store import _chroma_collections_url, _http_json

    tasks = list(
        session.scalars(
            select(SettingRecord)
            .where(SettingRecord.key.startswith(PENDING, autoescape=True))
            .limit(25)
        )
    )
    completed = 0
    for task in tasks:
        try:
            payload = json.loads(task.value)
            match = payload["match"]
            if match.get("source") != "berrybrain" or not match.get("note_stable_id"):
                raise ValueError("Unscoped vector cleanup")
            for target in payload["targets"]:
                collection = quote(target["collection"], safe="")
                if target["store"] == "qdrant":
                    _http_json(
                        "POST",
                        f'{target["url"]}/collections/{collection}/points/delete?wait=true',
                        {
                            "filter": {
                                "must": [
                                    {"key": key, "match": {"value": value}}
                                    for key, value in match.items()
                                ]
                            },
                        },
                        {200, 404},
                    )
                elif target["store"] == "chroma":
                    base = _chroma_collections_url({"chroma_url": target["url"]})
                    record = _http_json("GET", f"{base}/{collection}", {}, {200, 404})
                    if not record.get("id"):
                        continue
                    identity = quote(str(record["id"]), safe="")
                    _http_json(
                        "POST",
                        f"{base}/{identity}/delete",
                        {
                            "where": {
                                "$and": [
                                    {key: {"$eq": value}}
                                    for key, value in match.items()
                                ]
                            },
                        },
                        {200, 404},
                    )
                else:
                    raise ValueError("Unknown vector store")
            session.delete(task)
            session.commit()
            completed += 1
        except Exception:
            session.rollback()
            logging.warning(
                "Vector deletion remains queued; external cleanup was not completed"
            )
    remaining = (
        session.scalar(
            select(func.count())
            .select_from(SettingRecord)
            .where(SettingRecord.key.startswith(PENDING, autoescape=True))
        )
        or 0
    )
    return {"completed": completed, "pending": remaining}
