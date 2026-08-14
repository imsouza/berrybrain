from __future__ import annotations

import logging
import urllib.error
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from berrybrain_api.artifact_state import apply_quality_verdict
from berrybrain_api.config import PROJECT_ROOT, get_settings
from berrybrain_api.database import SessionLocal
from berrybrain_api.judge_committee import (
    DEFAULT_COMMITTEE_SIZE,
    MAX_COMMITTEE_SIZE,
    MIN_COMMITTEE_SIZE,
    JudgeConfig,
    JudgeMode,
    disagreement,
    eligible_committee_slots,
    is_high_impact,
    load_judge_config,
    persist_committee_run,
    recommend_committee,
    save_judge_config,
    should_use_committee,
)
from berrybrain_api.models import (
    ArtifactEvaluationRecord,
    ConnectionRecord,
    GraphEdgeRecord,
    GraphNodeRecord,
    HumanReviewRecord,
    InsightRecord,
    JudgeVerdictRecord,
    NoteRecord,
)
from berrybrain_api.security import assert_csrf, normalize_email, require_session_user

router = APIRouter(prefix="/api/v1/judge", tags=["judge"])
logger = logging.getLogger(__name__)

_VERDICT_ORDER = {"rejected": 0, "review": 1, "passed": 2}
JUDGE_PROMPT_VERSION = "artifact-judge.v2.md"


def _require_admin_csrf(request: Request) -> None:
    settings = get_settings()
    with SessionLocal() as session:
        user, session_record = require_session_user(session, settings, request)
        if normalize_email(user.email) != normalize_email(settings.admin_email):
            raise HTTPException(status_code=403, detail="Owner access required")
        assert_csrf(settings, request, session_record)


def _load_judge_prompt() -> str:
    prompt_path = PROJECT_ROOT / "prompts" / JUDGE_PROMPT_VERSION
    try:
        prompt = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        logger.exception("Judge prompt could not be read from %s", prompt_path)
        raise HTTPException(
            status_code=503, detail="Judge prompt is unavailable."
        ) from exc
    if not prompt:
        raise HTTPException(status_code=503, detail="Judge prompt is empty.")
    return prompt


def _with_judge_route(config: dict[str, str]) -> dict[str, str]:
    from berrybrain_api.ai_configuration import PROVIDERS

    routed = dict(config)
    provider = routed.get("judge_provider") or ""
    model = routed.get("judge_model") or ""
    if provider in {"cloud", "local"}:
        mode = provider
    elif provider in PROVIDERS:
        mode = str(PROVIDERS[provider]["mode"])
    else:
        raise ValueError("Judge provider is not configured")
    if not model:
        raise ValueError("Judge model is not configured")
    configured_mode = routed.get("provider") or mode
    if configured_mode != mode:
        raise ValueError("Judge provider cannot mix Cloud and Local modes")
    routed["provider"] = mode
    if mode == "cloud":
        routed["cloud_model"] = model or ""
    else:
        routed["ollama_model"] = model or ""
    return routed


def _parse_json_list(raw: object) -> list[object]:
    import json

    if isinstance(raw, list):
        return raw
    try:
        parsed = json.loads(str(raw or "[]"))
    except (TypeError, json.JSONDecodeError):
        return []
    return parsed if isinstance(parsed, list) else []


def _judge_source_context(session, artifact: object, artifact_type: str) -> dict:
    from berrybrain_api.learning import build_learning_guidance

    source_note_ids = {
        int(value)
        for value in _parse_json_list(getattr(artifact, "source_note_ids", "[]"))
        if str(value).isdigit()
    }
    if artifact_type == "connection":
        source_note_ids.update(
            int(value)
            for value in (
                getattr(artifact, "source_note_id", 0),
                getattr(artifact, "target_note_id", 0),
            )
            if int(value or 0) > 0
        )
    if artifact_type == "insight":
        source_note_ids.update(
            int(value)
            for value in _parse_json_list(getattr(artifact, "related_notes", "[]"))
            if str(value).isdigit()
        )
    notes = (
        session.query(NoteRecord)
        .filter(NoteRecord.id.in_(sorted(source_note_ids)))
        .order_by(NoteRecord.id)
        .limit(6)
        .all()
        if source_note_ids
        else []
    )
    context: dict[str, object] = {
        "sourceDocuments": [
            {
                "id": note.id,
                "title": note.title,
                "path": note.path,
                "contentExcerpt": " ".join((note.content or "").split())[:800],
            }
            for note in notes
        ],
        "learningGuidance": build_learning_guidance(
            session,
            source_note_ids=sorted(source_note_ids),
            target_type=f"graph_{artifact_type}",
        ),
    }
    if artifact_type == "edge":
        endpoint_ids = [
            int(getattr(artifact, "source_node_id", 0) or 0),
            int(getattr(artifact, "target_node_id", 0) or 0),
        ]
        endpoints = (
            session.query(GraphNodeRecord)
            .filter(GraphNodeRecord.id.in_(endpoint_ids))
            .all()
        )
        context["endpoints"] = [
            {"id": node.id, "type": node.type, "label": node.label}
            for node in endpoints
        ]
    return context


async def _run_committee_models(
    *,
    session,
    committee: list[dict[str, str]],
    generator_model: str,
    prompt: str,
    system: str,
) -> list[dict]:
    from berrybrain_api.ai_gateway import generate_graph_answer, get_ai_config

    eligible = eligible_committee_slots(committee, generator_model)
    if len(eligible) < 2:
        raise HTTPException(
            status_code=409,
            detail=(
                "Committee mode requires at least two unique configured Judge models "
                "that differ from the artifact generator."
            ),
        )
    verdicts: list[dict] = []
    for judge in eligible:
        local_config = get_ai_config(session)
        local_config["judge_provider"] = judge["provider"]
        local_config["judge_model"] = judge["model"]
        routed_config = _with_judge_route(local_config)
        started_at = datetime.now(UTC)
        try:
            role = judge.get("role") or "general"
            focus = judge.get("focus") or "Evaluate the complete artifact rubric."
            role_system = (
                f"{system}\n\nCommittee assignment\n"
                f"Role: {role}\nFocus: {focus}\n"
                "Return the complete required rubric. Give special attention to this role, "
                "but do not ignore decisive failures in other dimensions."
            )
            result = await generate_graph_answer(
                config=routed_config,
                prompt=prompt,
                system=role_system,
                session=session,
                prompt_version=JUDGE_PROMPT_VERSION,
            )
            elapsed = (datetime.now(UTC) - started_at).total_seconds() * 1000
            rubric = result.get("rubric", {})
            if not isinstance(rubric, dict):
                rubric = {}
            rubric["committeeRole"] = role
            verdicts.append(
                {
                    "slot": judge["slot"],
                    "provider": judge["provider"],
                    "model": judge["model"],
                    "role": role,
                    "verdict": result.get("verdict", "error"),
                    "score": float(result.get("score", 0.0)),
                    "rubric": rubric,
                    "reasoning": result.get("reasoning", ""),
                    "latency_ms": int(elapsed),
                }
            )
        except Exception as exc:
            logger.warning(
                "Committee Judge %s failed: %s", judge["slot"], type(exc).__name__
            )
            verdicts.append(
                {
                    "slot": judge["slot"],
                    "provider": judge["provider"],
                    "model": judge["model"],
                    "role": judge.get("role") or "general",
                    "verdict": "error",
                    "score": 0.0,
                    "rubric": {},
                    "reasoning": "judge-unavailable",
                    "latency_ms": 0,
                }
            )
    available = [item for item in verdicts if item["verdict"] != "error"]
    if len(available) < 2:
        raise HTTPException(
            status_code=503,
            detail="Fewer than two committee Judge models returned valid verdicts.",
            headers={"Retry-After": "30"},
        )
    return verdicts


def _weighted_kappa(pairs: list[tuple[str, str]]) -> float:
    """Quadratic weighted Cohen kappa for ordinal judge verdicts."""
    if not pairs:
        return 0.0
    labels = tuple(_VERDICT_ORDER)
    size = len(labels)
    observed = [[0 for _ in labels] for _ in labels]
    left_counts = [0 for _ in labels]
    right_counts = [0 for _ in labels]
    total = 0
    for predicted, actual in pairs:
        if predicted not in _VERDICT_ORDER or actual not in _VERDICT_ORDER:
            continue
        i = _VERDICT_ORDER[predicted]
        j = _VERDICT_ORDER[actual]
        observed[i][j] += 1
        left_counts[i] += 1
        right_counts[j] += 1
        total += 1
    if total == 0:
        return 0.0
    observed_disagreement = 0.0
    expected_disagreement = 0.0
    max_distance = (size - 1) ** 2
    for i in range(size):
        for j in range(size):
            weight = ((i - j) ** 2) / max_distance
            observed_disagreement += weight * observed[i][j] / total
            expected_disagreement += (
                weight * (left_counts[i] * right_counts[j]) / (total * total)
            )
    if expected_disagreement == 0:
        return 1.0 if observed_disagreement == 0 else 0.0
    return round(1 - (observed_disagreement / expected_disagreement), 4)


def _scorecard_agreement(rows: list[tuple[str, str]]) -> dict:
    matched = 0
    disagreed = 0
    false_accept = 0
    false_reject = 0
    positive = 0
    negative = 0
    pairs: list[tuple[str, str]] = []
    for predicted, actual in rows:
        if predicted not in _VERDICT_ORDER or actual not in _VERDICT_ORDER:
            continue
        pairs.append((predicted, actual))
        if predicted == actual:
            matched += 1
        else:
            disagreed += 1
            if actual == "rejected" and predicted == "passed":
                false_accept += 1
            if actual == "passed" and predicted == "rejected":
                false_reject += 1
        if actual == "passed":
            positive += 1
        elif actual == "rejected":
            negative += 1
    return {
        "comparable": matched + disagreed,
        "matched": matched,
        "disagreed": disagreed,
        "weighted_kappa": _weighted_kappa(pairs),
        "false_acceptance_rate": 0.0
        if negative == 0
        else round(false_accept / negative, 4),
        "false_rejection_rate": 0.0
        if positive == 0
        else round(false_reject / positive, 4),
    }


class ArtifactEvaluationCreate(BaseModel):
    artifact_type: str
    artifact_id: int
    verdict: str
    score: float
    rubric: str
    reasoning: str
    evidence_used: str
    provider: str
    model: str
    prompt_version: str


@router.post("/evaluations")
def submit_evaluation(eval_req: ArtifactEvaluationCreate):
    with SessionLocal() as session:
        evaluation = ArtifactEvaluationRecord(
            artifact_type=eval_req.artifact_type,
            artifact_id=eval_req.artifact_id,
            verdict=eval_req.verdict,
            score=eval_req.score,
            rubric=eval_req.rubric,
            reasoning=eval_req.reasoning,
            evidence_used=eval_req.evidence_used,
            provider=eval_req.provider,
            model=eval_req.model,
            prompt_version=eval_req.prompt_version,
        )
        session.add(evaluation)
        session.commit()
        session.refresh(evaluation)

        model_class = None
        if eval_req.artifact_type == "node":
            model_class = GraphNodeRecord
        elif eval_req.artifact_type == "edge":
            model_class = GraphEdgeRecord
        elif eval_req.artifact_type == "connection":
            model_class = ConnectionRecord
        elif eval_req.artifact_type == "insight":
            model_class = InsightRecord

        if model_class:
            artifact = (
                session.query(model_class)
                .filter(model_class.id == eval_req.artifact_id)
                .first()
            )
            if artifact:
                apply_quality_verdict(artifact, eval_req.verdict)
                artifact.quality_score = eval_req.score
                artifact.latest_evaluation_id = evaluation.id
                if hasattr(artifact, "updated_at"):
                    artifact.updated_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()

        return {"status": "success", "evaluation_id": evaluation.id}


@router.get("/review")
def get_evaluations_for_review(limit: int = 50, offset: int = 0):
    with SessionLocal() as session:
        evals = (
            session.query(ArtifactEvaluationRecord)
            .filter(ArtifactEvaluationRecord.verdict == "review")
            .order_by(ArtifactEvaluationRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "results": [
                {
                    "id": e.id,
                    "type": e.artifact_type,
                    "artifact_id": e.artifact_id,
                    "score": e.score,
                    "reasoning": e.reasoning,
                }
                for e in evals
            ]
        }


@router.get("/calibration")
def get_calibration_stats():
    with SessionLocal() as session:
        passed = (
            session.query(ArtifactEvaluationRecord)
            .filter(ArtifactEvaluationRecord.verdict == "passed")
            .count()
        )
        review = (
            session.query(ArtifactEvaluationRecord)
            .filter(ArtifactEvaluationRecord.verdict == "review")
            .count()
        )
        rejected = (
            session.query(ArtifactEvaluationRecord)
            .filter(ArtifactEvaluationRecord.verdict == "rejected")
            .count()
        )

        return {
            "passed": passed,
            "review": review,
            "rejected": rejected,
            "total": passed + review + rejected,
        }


class EvaluateInternalRequest(BaseModel):
    artifact_type: str
    artifact_id: int
    artifact_version: str | None = None


@router.post("/evaluate-artifact-internal")
async def evaluate_artifact_internal(req: EvaluateInternalRequest):
    import json

    from berrybrain_api.ai_gateway import (
        GraphAIUnavailable,
        generate_graph_answer,
        get_ai_config,
    )

    with SessionLocal() as session:
        model_class = None
        evidence = "[]"
        if req.artifact_type == "node":
            model_class = GraphNodeRecord
        elif req.artifact_type == "edge":
            model_class = GraphEdgeRecord
        elif req.artifact_type == "connection":
            model_class = ConnectionRecord
        elif req.artifact_type == "insight":
            model_class = InsightRecord

        if not model_class:
            return {"status": "error", "message": "Unknown artifact type"}

        artifact = (
            session.query(model_class).filter(model_class.id == req.artifact_id).first()
        )
        if not artifact:
            return {"status": "superseded", "message": "Artifact no longer exists"}

        if req.artifact_version and hasattr(artifact, "updated_at"):
            updated_at = getattr(artifact, "updated_at", None)
            if updated_at and updated_at.tzinfo is None:
                updated_at = updated_at.replace(tzinfo=UTC)
            current_version = updated_at.timestamp() if updated_at else None
            try:
                queued_version = float(req.artifact_version)
            except (TypeError, ValueError):
                queued_version = None
            if (
                current_version is None
                or queued_version is None
                or abs(current_version - queued_version) > 0.000001
            ):
                return {
                    "status": "superseded",
                    "message": "Artifact changed after this evaluation was queued",
                }

        if hasattr(artifact, "evidence"):
            evidence = artifact.evidence
        elif hasattr(artifact, "source_evidence"):
            evidence = artifact.source_evidence

        artifact_json = {
            k: v for k, v in artifact.__dict__.items() if not k.startswith("_")
        }
        # Convert datetime objects to string before json.dumps
        for k, v in artifact_json.items():
            if isinstance(v, datetime):
                artifact_json[k] = v.isoformat()

        system = _load_judge_prompt()

        prompt = json.dumps(
            {
                "artifact": artifact_json,
                "evidence": evidence,
                "context": _judge_source_context(session, artifact, req.artifact_type),
            },
            ensure_ascii=False,
        )

        try:
            judge_config = load_judge_config(session)
            if judge_config.mode == JudgeMode.DETERMINISTIC:
                evaluation = ArtifactEvaluationRecord(
                    artifact_type=req.artifact_type,
                    artifact_id=req.artifact_id,
                    verdict="review",
                    score=0.0,
                    rubric=json.dumps({"mode": "deterministic"}),
                    reasoning=(
                        "No LLM Judge was invoked. Deterministic mode requires human review."
                    ),
                    evidence_used=evidence,
                    provider="deterministic",
                    model="policy-only",
                    prompt_version=JUDGE_PROMPT_VERSION,
                )
                session.add(evaluation)
                session.flush()
                artifact.quality_gate_status = "review"
                artifact.quality_score = 0.0
                artifact.latest_evaluation_id = evaluation.id
                if hasattr(artifact, "updated_at"):
                    artifact.updated_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()
                return {
                    "status": "success",
                    "executionMode": "deterministic",
                    "verdict": "review",
                    "score": 0.0,
                }

            if should_use_committee(judge_config, req.artifact_type):
                if not judge_config.consent_at:
                    raise HTTPException(
                        status_code=409,
                        detail="Committee mode requires explicit consent.",
                    )
                generator_model = str(
                    getattr(artifact, "created_by_model", "")
                    or getattr(artifact, "model", "")
                    or ""
                )
                verdicts = await _run_committee_models(
                    session=session,
                    committee=judge_config.committee,
                    generator_model=generator_model,
                    prompt=prompt,
                    system=system,
                )
                summary = persist_committee_run(
                    session,
                    artifact_type=req.artifact_type,
                    artifact_id=req.artifact_id,
                    verdicts=verdicts,
                    enforcing=False,
                )
                session.refresh(artifact)
                apply_quality_verdict(artifact, summary.verdict)
                artifact.quality_score = summary.score
                artifact.latest_evaluation_id = summary.id
                if hasattr(artifact, "updated_at"):
                    artifact.updated_at = datetime.now(UTC).replace(tzinfo=None)
                session.commit()
                return {
                    "status": "success",
                    "executionMode": "committee",
                    "evaluationId": summary.id,
                    "verdict": summary.verdict,
                    "score": summary.score,
                    "judgeCount": len(verdicts),
                }

            config = _with_judge_route(get_ai_config(session))
            result = await generate_graph_answer(
                config=config,
                prompt=prompt,
                system=system,
                session=session,
                prompt_version=JUDGE_PROMPT_VERSION,
            )

            verdict = result.get("verdict", "error")
            score = float(result.get("score", 0.0))
            rubric = json.dumps(result.get("rubric", {}))
            reasoning = result.get("reasoning", "")

            evaluation = ArtifactEvaluationRecord(
                artifact_type=req.artifact_type,
                artifact_id=req.artifact_id,
                verdict=verdict,
                score=score,
                rubric=rubric,
                reasoning=reasoning,
                evidence_used=evidence,
                provider=config.get("judge_provider", "local"),
                model=config.get("judge_model", ""),
                prompt_version=JUDGE_PROMPT_VERSION,
            )
            session.add(evaluation)
            session.flush()

            apply_quality_verdict(artifact, verdict)
            artifact.quality_score = score
            artifact.latest_evaluation_id = evaluation.id
            if hasattr(artifact, "updated_at"):
                artifact.updated_at = datetime.now(UTC).replace(tzinfo=None)

            session.commit()
            return {
                "status": "success",
                "executionMode": "single_model",
                "verdict": verdict,
                "score": score,
            }

        except GraphAIUnavailable as exc:
            raise HTTPException(
                status_code=503,
                detail=str(exc),
                headers={
                    "Retry-After": str(max(1, round(exc.retry_after_seconds or 30)))
                },
            ) from exc
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "Judge evaluation failed for %s:%s",
                req.artifact_type,
                req.artifact_id,
            )
            raise HTTPException(
                status_code=503, detail="Judge evaluation is temporarily unavailable."
            ) from exc


@router.get("/mode")
def get_judge_mode():
    try:
        with SessionLocal() as session:
            cfg = load_judge_config(session)
            return cfg.to_dict()
    except SQLAlchemyError:
        return JudgeConfig().to_dict()


class JudgeModeUpdate(BaseModel):
    mode: str
    committee: list[dict] | None = None
    committee_size: int = DEFAULT_COMMITTEE_SIZE
    consent_at: str | None = None


@router.post("/mode", dependencies=[Depends(_require_admin_csrf)])
def set_judge_mode(req: JudgeModeUpdate):
    try:
        mode = JudgeMode(req.mode)
    except ValueError:
        return {"status": "error", "message": "invalid judge_mode"}
    with SessionLocal() as session:
        cfg = load_judge_config(session)
        cfg.mode = mode
        cfg.committee_size = max(
            MIN_COMMITTEE_SIZE,
            min(MAX_COMMITTEE_SIZE, req.committee_size),
        )
        if req.committee is not None:
            cfg.committee = eligible_committee_slots(req.committee)[
                : cfg.committee_size
            ]
        if mode == JudgeMode.COMMITTEE:
            from berrybrain_api.ai_configuration import load_configuration

            ai_configuration = load_configuration(session)
            generator_model = ai_configuration.main.model_id if ai_configuration else ""
            active_provider = (
                ai_configuration.judge.provider_id if ai_configuration else ""
            )
            eligible = eligible_committee_slots(cfg.committee, generator_model)
            if len(eligible) < cfg.committee_size or any(
                item["provider"] != active_provider for item in eligible
            ):
                return {
                    "status": "error",
                    "message": (
                        "Committee mode requires the selected number of unique, "
                        "non-generator models from the active provider."
                    ),
                }
            cfg.committee = eligible
        if mode == JudgeMode.COMMITTEE and not cfg.consent_at:
            if not req.consent_at:
                return {
                    "status": "error",
                    "message": "committee mode requires explicit consent_at",
                }
            cfg.consent_at = req.consent_at
        save_judge_config(session, cfg)
        return cfg.to_dict()


class JudgeDefaultsRequest(BaseModel):
    provider: str
    models: list[str]
    generator_model: str = ""
    primary_judge_model: str = ""
    committee_size: int = DEFAULT_COMMITTEE_SIZE


def _judge_defaults_response(
    committee: list[dict[str, str]], requested_size: int
) -> dict[str, object]:
    ready = len(committee) >= MIN_COMMITTEE_SIZE
    assigned_size = len(committee) if ready else requested_size
    return {
        "mode": "committee" if ready else "single_model",
        "committee_size": assigned_size,
        "committee": committee,
        "ready": ready,
        "message": (
            f"Assigned {assigned_size} distinct compatibility-tested Judge models."
            if ready
            else "At least two non-generator chat models are required for committee mode."
        ),
    }


@router.post("/defaults", dependencies=[Depends(_require_admin_csrf)])
def get_judge_defaults(req: JudgeDefaultsRequest) -> dict:
    from berrybrain_api.ai_configuration import PROVIDERS, load_configuration
    from berrybrain_api.routers.ai_configuration import (
        _fetch_models,
        _probe_judge_models,
        _provider_endpoint,
        _setting,
    )

    if req.provider not in PROVIDERS:
        raise HTTPException(status_code=422, detail="Judge provider is not supported")
    committee_size = max(
        MIN_COMMITTEE_SIZE,
        min(MAX_COMMITTEE_SIZE, req.committee_size),
    )
    with SessionLocal() as session:
        configuration = load_configuration(session)
        if configuration is None or configuration.judge.provider_id != req.provider:
            raise HTTPException(
                status_code=409,
                detail="Judge defaults require the active validated provider.",
            )
        endpoint = _provider_endpoint(session, req.provider)
        api_key = _setting(session, "ai_api_key")
        try:
            provider_models = _fetch_models(req.provider, endpoint, api_key)
        except (OSError, ValueError, urllib.error.URLError) as exc:
            raise HTTPException(
                status_code=502,
                detail="Judge provider models could not be loaded.",
            ) from exc
    from berrybrain_api.judge_committee import judge_model_candidates

    requested_models = set(req.models)
    available_models = [
        model
        for model in provider_models
        if not requested_models or model in requested_models
    ]
    candidates = judge_model_candidates(
        available_models=available_models,
        generator_model=req.generator_model,
        primary_judge_model=req.primary_judge_model,
    )
    validated_models = _probe_judge_models(
        req.provider,
        endpoint,
        api_key,
        candidates,
        required=committee_size,
    )
    committee = recommend_committee(
        provider=req.provider,
        available_models=validated_models,
        generator_model=req.generator_model,
        primary_judge_model=req.primary_judge_model,
        committee_size=committee_size,
    )
    return _judge_defaults_response(committee, committee_size)


class CommitteeRequest(BaseModel):
    artifact_type: str
    artifact_id: int
    enforcing: bool = False
    generator_model: str | None = None


@router.post("/committee")
async def judge_committee(req: CommitteeRequest):
    import json as _json

    with SessionLocal() as session:
        cfg = load_judge_config(session)
        if not should_use_committee(cfg, req.artifact_type):
            return {
                "status": "error",
                "message": "committee mode not enabled for this artifact_type",
            }
        if not is_high_impact(req.artifact_type):
            return {
                "status": "error",
                "message": "committee only for high-impact artifacts",
            }
        if not cfg.consent_at:
            return {"status": "error", "message": "missing committee consent"}

        if req.enforcing:
            total_evals = session.query(ArtifactEvaluationRecord).count()
            total_reviews = session.query(HumanReviewRecord).count()
            if total_evals < 100 or total_reviews < 30:
                return {"status": "error", "message": "uncalibrated enforcing blocked"}

        system = _load_judge_prompt()

        model_class = {
            "node": GraphNodeRecord,
            "edge": GraphEdgeRecord,
            "connection": ConnectionRecord,
            "insight": InsightRecord,
        }.get(req.artifact_type)
        if not model_class:
            return {"status": "error", "message": "Unknown artifact type"}
        artifact = (
            session.query(model_class).filter(model_class.id == req.artifact_id).first()
        )
        if not artifact:
            return {"status": "error", "message": "Artifact not found"}
        evidence = getattr(
            artifact, "evidence", getattr(artifact, "source_evidence", "[]")
        )
        artifact_json = {
            k: v for k, v in artifact.__dict__.items() if not k.startswith("_")
        }
        for k, v in artifact_json.items():
            if isinstance(v, datetime):
                artifact_json[k] = v.isoformat()
        prompt = _json.dumps(
            {
                "artifact": artifact_json,
                "evidence": evidence,
                "context": _judge_source_context(session, artifact, req.artifact_type),
            },
            ensure_ascii=False,
        )

        verdicts = await _run_committee_models(
            session=session,
            committee=cfg.committee,
            generator_model=(
                req.generator_model
                or str(
                    getattr(artifact, "created_by_model", "")
                    or getattr(artifact, "model", "")
                    or ""
                )
            ),
            prompt=prompt,
            system=system,
        )

        summary = persist_committee_run(
            session,
            artifact_type=req.artifact_type,
            artifact_id=req.artifact_id,
            verdicts=verdicts,
            enforcing=req.enforcing,
        )
        disagreement_flag = disagreement([v["verdict"] for v in verdicts])
        return {
            "status": "success",
            "evaluation_id": summary.id,
            "summary_verdict": summary.verdict,
            "score": summary.score,
            "verdicts": verdicts,
            "disagreement": disagreement_flag,
            "fail_closed": req.enforcing and disagreement_flag,
        }


@router.get("/scorecard")
def get_judge_scorecard():
    try:
        session_ctx = SessionLocal()
    except SQLAlchemyError:
        return _empty_judge_scorecard(JudgeConfig())

    with session_ctx as session:
        try:
            cfg = load_judge_config(session)
            total_evals = session.query(ArtifactEvaluationRecord).count()
            total_reviews = session.query(HumanReviewRecord).count()
            total_judge_verdicts = session.query(JudgeVerdictRecord).count()
        except SQLAlchemyError:
            return _empty_judge_scorecard(JudgeConfig())

        agreement = _scorecard_agreement([])
        if total_evals and total_reviews:
            rows = (
                session.query(JudgeVerdictRecord, HumanReviewRecord)
                .filter(
                    JudgeVerdictRecord.committee_id == HumanReviewRecord.committee_id,
                    JudgeVerdictRecord.is_summary == 1,
                )
                .all()
            )
            agreement = _scorecard_agreement(
                [(jv.verdict, hr.verdict) for jv, hr in rows]
            )

        calibrated = (
            total_evals >= 100
            and total_reviews >= 30
            and agreement["weighted_kappa"] >= 0.70
            and agreement["false_acceptance_rate"] <= 0.05
            and agreement["false_rejection_rate"] <= 0.10
        )
        return {
            "mode": cfg.mode.value,
            "consent_at": cfg.consent_at,
            "total_evaluations": total_evals,
            "total_human_reviews": total_reviews,
            "total_judge_verdicts": total_judge_verdicts,
            **agreement,
            "gates": {
                "weighted_kappa_min": 0.70,
                "fa_max": 0.05,
                "fr_max": 0.10,
                "min_evals": 100,
                "min_reviews": 30,
            },
            "calibrated": calibrated,
            "status": "calibrated" if calibrated else "NOT_CALIBRATED",
        }


def _empty_judge_scorecard(cfg: JudgeConfig) -> dict:
    return {
        "mode": cfg.mode.value,
        "consent_at": cfg.consent_at,
        "total_evaluations": 0,
        "total_human_reviews": 0,
        "total_judge_verdicts": 0,
        "comparable": 0,
        "matched": 0,
        "disagreed": 0,
        "weighted_kappa": 0.0,
        "false_acceptance_rate": 0.0,
        "false_rejection_rate": 0.0,
        "gates": {
            "weighted_kappa_min": 0.70,
            "fa_max": 0.05,
            "fr_max": 0.10,
            "min_evals": 100,
            "min_reviews": 30,
        },
        "calibrated": False,
        "status": "NOT_CALIBRATED",
    }


class HumanReviewIn(BaseModel):
    committee_id: str
    artifact_type: str
    artifact_id: int
    reviewer: str
    verdict: str
    score: float = 0.0
    notes: str = ""


@router.post("/human-reviews")
def submit_human_review(req: HumanReviewIn):
    with SessionLocal() as session:
        row = HumanReviewRecord(
            committee_id=req.committee_id,
            artifact_type=req.artifact_type,
            artifact_id=req.artifact_id,
            reviewer=req.reviewer,
            verdict=req.verdict,
            score=req.score,
            notes=req.notes,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"status": "success", "id": row.id}


@router.get("/human-reviews/export")
def export_human_reviews(fmt: str = "jsonl"):
    import json as _json

    if fmt not in ("jsonl", "json"):
        return {"status": "error", "message": "fmt must be jsonl or json"}
    with SessionLocal() as session:
        rows = (
            session.query(HumanReviewRecord)
            .order_by(HumanReviewRecord.created_at.desc())
            .all()
        )
        payload = [
            {
                "committee_id": r.committee_id,
                "artifact_type": r.artifact_type,
                "artifact_id": r.artifact_id,
                "reviewer": r.reviewer,
                "verdict": r.verdict,
                "score": r.score,
                "notes": r.notes,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
        if fmt == "json":
            return {"reviews": payload}
        return {"lines": [_json.dumps(p) for p in payload]}
