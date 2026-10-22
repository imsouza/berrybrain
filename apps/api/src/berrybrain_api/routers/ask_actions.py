"""Human-approved Ask drafts. The model never calls the write executor directly."""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import and_, select, update
from sqlalchemy.exc import IntegrityError

from berrybrain_api.automation_logs import create_automation_log
from berrybrain_api.config import get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.filesystem import atomic_write_text, serialized_vault, vault_lock
from berrybrain_api.graph_expansion import sync_note_graph_node
from berrybrain_api.jobs import enqueue_note_changed_jobs
from berrybrain_api.models import AskActionPlanRecord, NoteRecord, VaultRecord
from berrybrain_api.security import assert_csrf, get_session_user, require_session_user
from berrybrain_api.sync import sync_note_record
from berrybrain_api.vault import (
    SAFE_FOLDERS,
    planned_ask_note_in_vault_path,
    planned_ask_note_path,
    planned_ask_vault_path,
    read_note,
    resolve_note_path,
)

router = APIRouter(prefix="/api/v1/ask/action-plans", tags=["ask"])
PLAN_TTL = timedelta(minutes=15)
MAX_EXECUTION_ATTEMPTS = 2


class CreateNotePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    folder: str = Field(default="inbox", max_length=40)
    content: str = Field(min_length=1, max_length=50000)
    new_vault_name: str | None = Field(default=None, max_length=160)
    vault_id: str | None = Field(default=None, max_length=36)
    request_key: UUID | None = None


class ApprovePlanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    arguments_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReviewDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewed: Literal[True]
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class ReconcileChangedFileRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reviewed: Literal[True]
    content_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class NotePlanArguments(BaseModel):
    title: str
    folder: str
    content: str
    newVaultName: str | None = None
    targetVaultId: str | None = None
    targetVaultPath: str | None = None
    targetVaultName: str | None = None


class ActionPlanResponse(BaseModel):
    id: str
    action: Literal["create_note"]
    arguments: NotePlanArguments
    argumentsHash: str
    attempts: int
    status: Literal[
        "proposed", "executing", "completed", "partial", "cancelled", "expired", "failed"
    ]
    expiresAt: datetime
    approvedAt: datetime | None
    resultPath: str | None
    vaultId: str | None
    recoveryPath: str | None
    orphanPath: str | None
    errorCode: str | None
    evidenceStatus: Literal["draft", "eligible"] | None


class ReviewableDraftSummary(BaseModel):
    id: str
    title: str
    resultPath: str
    createdAt: datetime


class FailedPlanSummary(BaseModel):
    id: str
    title: str
    orphanPath: str | None
    errorCode: str | None
    createdAt: datetime


class ActionCapabilities(BaseModel):
    workspaceModel: Literal["shared"]
    supportedActions: list[Literal["create_note"]]
    availableActions: list[Literal["create_note"]]
    approvalMode: Literal["one_note_per_approval"]
    requiresBrowserSession: bool
    requiresCsrfForWrites: bool
    serviceTokenCanApprove: bool
    createsIndependentVault: bool
    canCreateNamedVaultWithNote: bool
    canTargetExistingNamedVault: bool
    allowedFolders: list[str]
    maxContentChars: int


def _identity(request: Request):
    settings = get_settings()
    with SessionLocal() as session:
        user, browser_session = require_session_user(session, settings, request)
        if request.method not in {"GET", "HEAD"}:
            assert_csrf(settings, request, browser_session)
        return user.id, browser_session.id


def _arguments(payload: CreateNotePlanRequest) -> dict[str, str]:
    title = payload.title.strip()
    content = payload.content.strip()
    if not title or not content:
        raise HTTPException(status_code=422, detail="Title and content are required")
    if payload.folder not in SAFE_FOLDERS:
        raise HTTPException(status_code=422, detail="Unsupported note folder")
    if payload.new_vault_name is not None and payload.vault_id is not None:
        raise HTTPException(status_code=422, detail="Select one vault destination")
    arguments = {"title": title, "folder": payload.folder, "content": content}
    if payload.new_vault_name is not None:
        name = payload.new_vault_name.strip()
        if not name or re.search(r"[/\\:\x00-\x1f\x7f]", name):
            raise HTTPException(status_code=422, detail="Invalid vault name")
        arguments["newVaultName"] = name
    return arguments


def _serialized(arguments: dict[str, str]) -> str:
    return json.dumps(
        arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _result_note(session, plan: AskActionPlanRecord) -> NoteRecord | None:
    if plan.result_note_id:
        note = session.get(NoteRecord, plan.result_note_id)
        return (
            note
            if note is not None and note.stable_id == plan.result_note_stable_id
            else None
        )
    # Never infer identity from a path: it may now belong to a different note.
    return None


def _planned_relative_path(plan: AskActionPlanRecord) -> str:
    arguments = json.loads(plan.arguments_json)
    if arguments.get("newVaultName"):
        return planned_ask_note_in_vault_path(
            arguments["folder"],
            arguments["title"],
            arguments["newVaultName"],
            plan.id,
        )
    if arguments.get("targetVaultPath"):
        return (
            f"{arguments['targetVaultPath']}/"
            f"{planned_ask_note_path(arguments['folder'], arguments['title'], plan.id)}"
        )
    return planned_ask_note_path(arguments["folder"], arguments["title"], plan.id)


def _validate_target_vault(session, plan: AskActionPlanRecord, root: Path) -> None:
    arguments = json.loads(plan.arguments_json)
    vault_id = arguments.get("targetVaultId")
    if not vault_id:
        return
    vault = session.get(VaultRecord, vault_id)
    if vault is None or vault.path != arguments.get("targetVaultPath"):
        raise HTTPException(status_code=409, detail="Target vault changed")
    directory = root.resolve() / vault.path
    if not directory.is_dir() or directory.resolve() != directory:
        raise HTTPException(status_code=409, detail="Target vault directory is unavailable")


def _register_vault(session, plan: AskActionPlanRecord) -> None:
    arguments = json.loads(plan.arguments_json)
    name = arguments.get("newVaultName")
    if not name:
        return
    path = planned_ask_vault_path(name, plan.id)
    existing = session.get(VaultRecord, plan.id)
    if existing is not None:
        if existing.path != path or existing.name != name:
            raise HTTPException(status_code=409, detail="Vault identity changed")
        return
    occupied = session.scalar(select(VaultRecord).where(VaultRecord.path == path))
    if occupied is not None:
        raise HTTPException(status_code=409, detail="Vault path is occupied")
    session.add(VaultRecord(id=plan.id, name=name, path=path))
    session.flush()


def _orphan_path(plan: AskActionPlanRecord) -> str | None:
    if plan.status not in {"executing", "failed"} or plan.result_note_id:
        return None
    try:
        relative_path = _planned_relative_path(plan)
        vault_path = get_settings().vault_path
        path = resolve_note_path(vault_path, relative_path)
        # A symlink would attach a different canonical note to this plan.
        if path == vault_path.resolve() / relative_path and path.is_file():
            return relative_path
    except (HTTPException, KeyError, OSError, TypeError, ValueError):
        pass
    return None


def _recovery_path(plan: AskActionPlanRecord) -> str | None:
    relative_path = _orphan_path(plan)
    if relative_path is None:
        return None
    try:
        path = resolve_note_path(get_settings().vault_path, relative_path)
        expected = json.loads(plan.arguments_json)["content"]
        if path.read_text(encoding="utf-8") == expected:
            return relative_path
    except (HTTPException, KeyError, OSError, TypeError, ValueError):
        pass
    return None


def _view(session, plan: AskActionPlanRecord) -> dict:
    note = _result_note(session, plan)
    return {
        "id": plan.id,
        "action": plan.action,
        "arguments": json.loads(plan.arguments_json),
        "argumentsHash": plan.arguments_hash,
        "attempts": plan.execution_attempts,
        "status": plan.status,
        "expiresAt": plan.expires_at.replace(tzinfo=UTC).isoformat(),
        "approvedAt": plan.approved_at.replace(tzinfo=UTC).isoformat()
        if plan.approved_at
        else None,
        "resultPath": note.path if note is not None else None,
        "vaultId": note.vault_id if note is not None else None,
        "recoveryPath": _recovery_path(plan) if note is None else None,
        "orphanPath": _orphan_path(plan) if note is None else None,
        "errorCode": plan.error_code or None,
        "evidenceStatus": note.evidence_status if note is not None else None,
    }


def _owned_plan(
    session, plan_id: str, user_id: int, session_id: int, *, allow_saved: bool = False
):
    plan = session.get(AskActionPlanRecord, plan_id)
    if (
        plan is None
        or plan.user_id != user_id
        or (
            plan.session_id != session_id
            and not (
                allow_saved
                and (
                    plan.status in {"completed", "partial"}
                    or (plan.status == "failed" and plan.approved_at is not None)
                )
            )
        )
    ):
        raise HTTPException(status_code=404, detail="Action plan not found")
    return plan


@serialized_vault
def _write_once(vault_path: Path, plan: AskActionPlanRecord) -> tuple[str, str]:
    arguments = json.loads(plan.arguments_json)
    relative_path = _planned_relative_path(plan)
    path = resolve_note_path(vault_path, relative_path)
    if path != vault_path.resolve() / relative_path:
        raise HTTPException(status_code=409, detail="Planned vault path is unsafe")
    if arguments.get("newVaultName"):
        vault_dir = vault_path.resolve() / planned_ask_vault_path(
            arguments["newVaultName"], plan.id
        )
        if vault_dir.exists() and not path.is_file():
            raise HTTPException(
                status_code=409, detail="Planned vault directory is occupied"
            )
    try:
        atomic_write_text(path, arguments["content"], overwrite=False)
    except FileExistsError as exc:
        # A retry after a crash may observe its own completed filesystem write.
        if path.read_text(encoding="utf-8") != arguments["content"]:
            raise HTTPException(
                status_code=409, detail="Planned note path is occupied"
            ) from exc
    note = read_note(vault_path, relative_path)
    return relative_path, str(note["content_hash"])


@router.post("", status_code=201, response_model=ActionPlanResponse)
def propose_note(payload: CreateNotePlanRequest, request: Request) -> dict:
    user_id, browser_session_id = _identity(request)
    arguments = _arguments(payload)
    request_key = str(payload.request_key) if payload.request_key else None
    now = datetime.now(UTC)
    with SessionLocal() as session:
        if payload.vault_id and payload.vault_id != "default":
            vault = session.get(VaultRecord, payload.vault_id)
            if vault is None:
                raise HTTPException(status_code=404, detail="Vault not found")
            arguments["targetVaultId"] = vault.id
            arguments["targetVaultPath"] = vault.path
            arguments["targetVaultName"] = vault.name
        serialized = _serialized(arguments)
        arguments_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        if request_key:
            existing = session.scalar(
                select(AskActionPlanRecord).where(
                    AskActionPlanRecord.request_key == request_key
                )
            )
            if existing is not None:
                if (
                    existing.user_id != user_id
                    or existing.session_id != browser_session_id
                    or existing.arguments_hash != arguments_hash
                ):
                    raise HTTPException(
                        status_code=409, detail="Request key already used"
                    )
                return _view(session, existing)
        plan = AskActionPlanRecord(
            id=str(uuid4()),
            request_key=request_key,
            user_id=user_id,
            session_id=browser_session_id,
            action="create_note",
            arguments_json=serialized,
            arguments_hash=arguments_hash,
            status="proposed",
            created_at=now,
            expires_at=now + PLAN_TTL,
        )
        session.add(plan)
        try:
            session.commit()
        except IntegrityError as exc:
            session.rollback()
            if request_key is None:
                raise
            existing = session.scalar(
                select(AskActionPlanRecord).where(
                    AskActionPlanRecord.request_key == request_key
                )
            )
            if (
                existing is not None
                and existing.user_id == user_id
                and existing.session_id == browser_session_id
                and existing.arguments_hash == arguments_hash
            ):
                return _view(session, existing)
            raise HTTPException(
                status_code=409, detail="Request key already used"
            ) from exc
        return _view(session, plan)


@router.get("/capabilities", response_model=ActionCapabilities)
def action_capabilities(request: Request) -> dict:
    """Declare the narrow action contract without implying service-token approval."""
    with SessionLocal() as session:
        has_browser_session = (
            get_session_user(session, get_settings(), request) is not None
        )
    return {
        "workspaceModel": "shared",
        "supportedActions": ["create_note"],
        "availableActions": ["create_note"] if has_browser_session else [],
        "approvalMode": "one_note_per_approval",
        "requiresBrowserSession": True,
        "requiresCsrfForWrites": True,
        "serviceTokenCanApprove": False,
        "createsIndependentVault": False,
        "canCreateNamedVaultWithNote": True,
        "canTargetExistingNamedVault": True,
        "allowedFolders": sorted(SAFE_FOLDERS),
        "maxContentChars": 50000,
    }


@router.get("/reviewable", response_model=list[ReviewableDraftSummary])
def reviewable_drafts(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """Only the same signed-in owner can discover unreviewed saved drafts."""
    user_id, _ = _identity(request)
    with SessionLocal() as session:
        rows = session.execute(
            select(
                AskActionPlanRecord.id,
                AskActionPlanRecord.arguments_json,
                AskActionPlanRecord.created_at,
                NoteRecord.path,
            )
            .join(
                NoteRecord,
                and_(
                    NoteRecord.id == AskActionPlanRecord.result_note_id,
                    NoteRecord.stable_id == AskActionPlanRecord.result_note_stable_id,
                ),
            )
            .where(
                AskActionPlanRecord.user_id == user_id,
                AskActionPlanRecord.status.in_(("completed", "partial")),
                NoteRecord.evidence_status == "draft",
            )
            .order_by(
                AskActionPlanRecord.created_at.desc(), AskActionPlanRecord.id.desc()
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return [
            {
                "id": plan_id,
                "title": json.loads(arguments_json)["title"],
                "resultPath": path,
                "createdAt": created_at.replace(tzinfo=UTC).isoformat(),
            }
            for plan_id, arguments_json, created_at, path in rows
        ]


@router.get("/failed", response_model=list[FailedPlanSummary])
def failed_plans(
    request: Request,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[dict]:
    """List only the signed-in owner's approved failed Ask writes."""
    user_id, _ = _identity(request)
    with SessionLocal() as session:
        rows = session.scalars(
            select(AskActionPlanRecord)
            .where(
                AskActionPlanRecord.user_id == user_id,
                AskActionPlanRecord.action == "create_note",
                AskActionPlanRecord.status == "failed",
                AskActionPlanRecord.approved_at.is_not(None),
                AskActionPlanRecord.result_note_id == 0,
            )
            .order_by(
                AskActionPlanRecord.created_at.desc(),
                AskActionPlanRecord.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        ).all()
        return [
            {
                "id": plan.id,
                "title": json.loads(plan.arguments_json)["title"],
                "orphanPath": _orphan_path(plan),
                "errorCode": plan.error_code or None,
                "createdAt": plan.created_at.replace(tzinfo=UTC).isoformat(),
            }
            for plan in rows
        ]


@router.get("/{plan_id}", response_model=ActionPlanResponse)
def get_plan(plan_id: str, request: Request) -> dict:
    user_id, browser_session_id = _identity(request)
    with SessionLocal() as session:
        return _view(
            session,
            _owned_plan(
                session, plan_id, user_id, browser_session_id, allow_saved=True
            ),
        )


@router.post("/{plan_id}/cancel", response_model=ActionPlanResponse)
def cancel_plan(plan_id: str, request: Request) -> dict:
    user_id, browser_session_id = _identity(request)
    with SessionLocal() as session:
        plan = _owned_plan(session, plan_id, user_id, browser_session_id)
        if plan.status == "proposed":
            plan.status = "cancelled"
            session.commit()
        return _view(session, plan)


@router.post("/{plan_id}/approve", response_model=ActionPlanResponse)
def approve_plan(plan_id: str, payload: ApprovePlanRequest, request: Request) -> dict:
    user_id, browser_session_id = _identity(request)
    now = datetime.now(UTC)
    with SessionLocal() as session:
        plan = _owned_plan(session, plan_id, user_id, browser_session_id)
        if plan.arguments_hash != payload.arguments_hash:
            raise HTTPException(status_code=409, detail="Plan contents changed")
        if plan.status == "completed":
            return _view(session, plan)
        if plan.status in {"cancelled", "expired", "failed", "partial"}:
            raise HTTPException(status_code=409, detail="Plan is no longer approvable")
        if plan.status == "proposed" and plan.expires_at.replace(tzinfo=UTC) < now:
            plan.status = "expired"
            session.commit()
            raise HTTPException(status_code=409, detail="Plan expired")
        # Compare-and-set prevents two requests from executing the same proposal.
        # A stale execution can be resumed using the deterministic note path.
        stale_before = now - timedelta(seconds=90)
        if (
            plan.status == "executing"
            and plan.approved_at is not None
            and plan.approved_at.replace(tzinfo=UTC) < stale_before
            and plan.execution_attempts >= MAX_EXECUTION_ATTEMPTS
        ):
            plan.status = "failed"
            plan.error_code = "execution_attempts_exhausted"
            session.commit()
            return _view(session, plan)
        claim = session.execute(
            update(AskActionPlanRecord)
            .where(
                AskActionPlanRecord.id == plan_id,
                AskActionPlanRecord.user_id == user_id,
                AskActionPlanRecord.session_id == browser_session_id,
                AskActionPlanRecord.execution_attempts < MAX_EXECUTION_ATTEMPTS,
                (AskActionPlanRecord.status == "proposed")
                | (
                    (AskActionPlanRecord.status == "executing")
                    & (AskActionPlanRecord.approved_at < stale_before)
                ),
            )
            .values(
                status="executing",
                approved_at=now,
                error_code="",
                execution_attempts=AskActionPlanRecord.execution_attempts + 1,
            )
            .execution_options(synchronize_session=False)
        )
        session.commit()
        if claim.rowcount != 1:
            session.refresh(plan)
            return _view(session, plan)
        try:
            vault_path = get_settings().vault_path
            with vault_lock(vault_path):
                _validate_target_vault(session, plan, vault_path)
                note_path, content_hash = _write_once(vault_path, plan)
                _register_vault(session, plan)
                record = sync_note_record(
                    session, vault_path, note_path, evidence_status="draft"
                )
                if record.content_hash != content_hash:
                    # The file exists and was indexed, but another editor changed
                    # it before we could finalize. Keep its stable identity and
                    # leave it uncitable until the owner reviews this version.
                    plan.result_path = note_path
                    plan.result_note_id = record.id
                    plan.result_note_stable_id = record.stable_id
                    plan.status = "partial"
                    plan.error_code = "content_changed_before_sync"
                    session.commit()
                    raise HTTPException(
                        status_code=409,
                        detail="Saved note changed before sync; current content was preserved for review",
                    )
                plan.result_path = note_path
                plan.result_note_id = record.id
                plan.result_note_stable_id = record.stable_id
                plan.status = "completed"
                plan.completed_at = datetime.now(UTC)
                session.commit()
            return _view(session, plan)
        except HTTPException:
            if plan.status != "partial":
                plan.error_code = "write_conflict"
                plan.status = "failed"
                session.commit()
            raise
        except Exception:
            # The filesystem write may already exist. Keep the deterministic
            # execution resumable once, but never retry an unknown failure in
            # an unbounded loop. Use a fresh transaction after SQLAlchemy error.
            session.rollback()
            with SessionLocal() as recovery:
                stored = recovery.get(AskActionPlanRecord, plan_id)
                if stored is not None and stored.status == "executing":
                    stored.error_code = "execution_interrupted"
                    if stored.execution_attempts >= MAX_EXECUTION_ATTEMPTS:
                        stored.status = "failed"
                        stored.error_code = "execution_attempts_exhausted"
                    recovery.commit()
            raise


@router.post("/{plan_id}/reconcile", response_model=ActionPlanResponse)
def reconcile_failed_plan(
    plan_id: str, request: Request, payload: ReconcileChangedFileRequest | None = None
) -> dict:
    """Attach an orphaned Markdown file as a draft without rewriting it."""
    user_id, browser_session_id = _identity(request)
    vault_path = get_settings().vault_path
    with SessionLocal() as session:
        plan = _owned_plan(
            session, plan_id, user_id, browser_session_id, allow_saved=True
        )
        if plan.status in {"partial", "completed"}:
            return _view(session, plan)
        if plan.status != "failed":
            raise HTTPException(status_code=409, detail="Plan is not ready for reconciliation")
        with vault_lock(vault_path):
            session.refresh(plan)
            if plan.status in {"partial", "completed"}:
                return _view(session, plan)
            if plan.status != "failed":
                raise HTTPException(
                    status_code=409, detail="Plan is no longer ready for reconciliation"
                )
            _validate_target_vault(session, plan, vault_path)
            relative_path = _orphan_path(plan)
            if relative_path is None:
                raise HTTPException(
                    status_code=409,
                    detail="The planned file is missing or unsafe; nothing was overwritten",
                )
            try:
                current = read_note(vault_path, relative_path)
            except (FileNotFoundError, HTTPException) as exc:
                if isinstance(exc, HTTPException) and exc.status_code != 404:
                    raise
                raise HTTPException(
                    status_code=409, detail="The planned file disappeared during recovery"
                ) from exc
            current_hash = str(current["content_hash"])
            approved_content = json.loads(plan.arguments_json)["content"]
            changed = current["content"] != approved_content
            if changed and payload is None:
                raise HTTPException(
                    status_code=409,
                    detail="The file changed; review its current content and submit its hash before recovery",
                )
            if payload is not None and payload.content_hash != current_hash:
                raise HTTPException(
                    status_code=409,
                    detail="The saved file changed since preview; refresh before recovery",
                )
            existing = session.scalar(
                select(NoteRecord).where(NoteRecord.path == relative_path)
            )
            if existing is not None and existing.evidence_status != "draft":
                raise HTTPException(
                    status_code=409,
                    detail="The file is already a released note; manual review is required",
                )
            _register_vault(session, plan)
            record = sync_note_record(
                session, vault_path, relative_path, evidence_status="draft"
            )
            try:
                final_hash = read_note(vault_path, relative_path)["content_hash"]
            except (FileNotFoundError, HTTPException) as exc:
                if isinstance(exc, HTTPException) and exc.status_code != 404:
                    raise
                raise HTTPException(
                    status_code=409, detail="The planned file disappeared during recovery"
                ) from exc
            if record.content_hash != current_hash or final_hash != current_hash:
                raise HTTPException(
                    status_code=409,
                    detail="The planned file changed during recovery",
                )
            plan.result_path = relative_path
            plan.result_note_id = record.id
            plan.result_note_stable_id = record.stable_id
            plan.status = "partial"
            plan.error_code = (
                "recovered_changed_file" if changed else "recovered_after_interruption"
            )
            create_automation_log(
                session,
                action_type="RECONCILE_ASK_DRAFT",
                target_type="note",
                target_id=record.path,
                description="User attached an interrupted Ask file as an unreviewed draft",
                before_state={"planStatus": "failed"},
                after_state={
                    "planStatus": "partial",
                    "planId": plan.id,
                    "userId": user_id,
                    "contentHash": current_hash,
                    "changedFromApproval": changed,
                },
                reversible=False,
                autocommit=False,
            )
            session.commit()
            return _view(session, plan)


@router.post("/{plan_id}/review-draft", response_model=ActionPlanResponse)
def review_draft(plan_id: str, payload: ReviewDraftRequest, request: Request) -> dict:
    """Human review is distinct from accepting the file write."""
    user_id, browser_session_id = _identity(request)
    vault_path = get_settings().vault_path
    with SessionLocal() as session:
        plan = _owned_plan(
            session, plan_id, user_id, browser_session_id, allow_saved=True
        )
        if plan.status not in {"completed", "partial"} or not plan.result_path:
            raise HTTPException(status_code=409, detail="Draft has not been saved")
        with vault_lock(vault_path):
            note = _result_note(session, plan)
            if note is None:
                raise HTTPException(status_code=409, detail="Saved draft is missing")
            if note.evidence_status == "eligible":
                return _view(session, plan)
            try:
                current = read_note(vault_path, note.path)
            except FileNotFoundError as exc:
                raise HTTPException(
                    status_code=409, detail="Saved draft file is missing"
                ) from exc
            except HTTPException as exc:
                if exc.status_code != 404:
                    raise
                raise HTTPException(
                    status_code=409, detail="Saved draft file is missing"
                ) from exc
            if current["content_hash"] != payload.content_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Draft changed since preview; refresh the current note before releasing it",
                )
            if current["content_hash"] != note.content_hash:
                note = sync_note_record(session, vault_path, note.path)
            try:
                final_hash = read_note(vault_path, note.path)["content_hash"]
            except (FileNotFoundError, HTTPException) as exc:
                if isinstance(exc, HTTPException) and exc.status_code != 404:
                    raise
                raise HTTPException(
                    status_code=409, detail="Saved draft file is missing"
                ) from exc
            if note.content_hash != payload.content_hash or final_hash != payload.content_hash:
                raise HTTPException(
                    status_code=409,
                    detail="Draft changed during review; refresh its current content before releasing it",
                )
            if note.evidence_status == "draft":
                note.evidence_status = "eligible"
                if plan.status == "partial":
                    plan.status = "completed"
                    plan.error_code = ""
                sync_note_graph_node(session, note)
                enqueue_note_changed_jobs(
                    session,
                    note.path,
                    "NOTE_CREATED",
                    note.content_hash,
                    autocommit=False,
                )
                create_automation_log(
                    session,
                    action_type="REVIEW_ASK_DRAFT",
                    target_type="note",
                    target_id=note.path,
                    description="User reviewed an Ask-assisted draft for evidence use",
                    before_state={
                        "evidenceStatus": "draft",
                        "contentHash": note.content_hash,
                    },
                    after_state={
                        "evidenceStatus": "eligible",
                        "contentHash": note.content_hash,
                        "planId": plan.id,
                        "userId": user_id,
                    },
                    reversible=False,
                    autocommit=False,
                )
                session.commit()
            return _view(session, plan)
