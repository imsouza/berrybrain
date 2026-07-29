from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from berrybrain_api.config import PROJECT_ROOT
from berrybrain_api.database import SessionLocal
from berrybrain_api.judge_committee import (
    JudgeConfig,
    JudgeMode,
    disagreement,
    generator_model_blocked_in_committee,
    is_high_impact,
    load_judge_config,
    persist_committee_run,
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
)

router = APIRouter(prefix="/api/v1/judge", tags=["judge"])

_VERDICT_ORDER = {"rejected": 0, "review": 1, "passed": 2}


def _with_judge_route(config: dict[str, str]) -> dict[str, str]:
    routed = dict(config)
    provider = routed.get("judge_provider") or routed.get("provider") or "local"
    model = routed.get("judge_model") or (
        routed.get("cloud_model") if provider == "cloud" else routed.get("ollama_model")
    )
    routed["provider"] = provider
    if provider == "cloud":
        routed["cloud_model"] = model or ""
    else:
        routed["ollama_model"] = model or ""
    return routed


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
                artifact.quality_gate_status = eval_req.verdict
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


@router.post("/evaluate-artifact-internal")
async def evaluate_artifact_internal(req: EvaluateInternalRequest):
    import json

    from berrybrain_api.ai_gateway import generate_graph_answer, get_ai_config

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
            return {"status": "error", "message": "Artifact not found"}

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

        prompt_path = PROJECT_ROOT / "prompts" / "artifact-judge.v1.md"
        if not prompt_path.exists():
            return {"status": "error", "message": "Prompt file not found"}

        system = prompt_path.read_text("utf-8")

        prompt = json.dumps({"artifact": artifact_json, "evidence": evidence})

        config = _with_judge_route(get_ai_config(session))

        try:
            result = await generate_graph_answer(
                config=config,
                prompt=prompt,
                system=system,
                session=session,
                prompt_version="artifact-judge.v1.md",
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
                prompt_version="artifact-judge.v1.md",
            )
            session.add(evaluation)

            artifact.quality_gate_status = verdict
            artifact.quality_score = score
            if hasattr(artifact, "updated_at"):
                artifact.updated_at = datetime.now(UTC).replace(tzinfo=None)

            session.commit()
            return {"status": "success", "verdict": verdict, "score": score}

        except Exception:
            # Deterministic graceful failure
            return {"status": "error", "message": "Judge evaluation failed."}


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
    consent_at: str | None = None


@router.post("/mode")
def set_judge_mode(req: JudgeModeUpdate):
    try:
        mode = JudgeMode(req.mode)
    except ValueError:
        return {"status": "error", "message": "invalid judge_mode"}
    with SessionLocal() as session:
        cfg = load_judge_config(session)
        cfg.mode = mode
        if req.committee is not None:
            if not isinstance(req.committee, list) or len(req.committee) < 2:
                return {"status": "error", "message": "committee needs >= 2 judges"}
            cfg.committee = req.committee
        if mode == JudgeMode.COMMITTEE and not cfg.consent_at:
            if not req.consent_at:
                return {
                    "status": "error",
                    "message": "committee mode requires explicit consent_at",
                }
            cfg.consent_at = req.consent_at
        save_judge_config(session, cfg)
        return cfg.to_dict()


class CommitteeRequest(BaseModel):
    artifact_type: str
    artifact_id: int
    enforcing: bool = False
    generator_model: str | None = None


@router.post("/committee")
async def judge_committee(req: CommitteeRequest):
    import json as _json

    from berrybrain_api.ai_gateway import generate_graph_answer, get_ai_config

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

        blocked = generator_model_blocked_in_committee(
            req.generator_model or "", cfg.committee
        )
        if blocked:
            return {
                "status": "error",
                "message": "generator model present in committee",
                "blocked_slots": blocked,
            }

        prompt_path = PROJECT_ROOT / "prompts" / "artifact-judge.v1.md"
        if not prompt_path.exists():
            return {"status": "error", "message": "Prompt file not found"}
        system = prompt_path.read_text("utf-8")

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
        prompt = _json.dumps({"artifact": artifact_json, "evidence": evidence})

        verdicts: list[dict] = []
        for judge in cfg.committee:
            local_config = get_ai_config(session)
            local_config["judge_provider"] = judge.get("provider", "ollama")
            local_config["judge_model"] = judge.get("model", "")
            routed_config = _with_judge_route(local_config)
            t0 = datetime.now(UTC)
            try:
                result = await generate_graph_answer(
                    config=routed_config,
                    prompt=prompt,
                    system=system,
                    session=session,
                    prompt_version="artifact-judge.v1.md",
                )
                elapsed = (datetime.now(UTC) - t0).total_seconds() * 1000
                verdicts.append(
                    {
                        "slot": judge.get("slot", ""),
                        "provider": local_config["judge_provider"],
                        "model": local_config["judge_model"],
                        "verdict": result.get("verdict", "error"),
                        "score": float(result.get("score", 0.0)),
                        "rubric": result.get("rubric", {}),
                        "reasoning": result.get("reasoning", ""),
                        "latency_ms": int(elapsed),
                    }
                )
            except Exception:
                verdicts.append(
                    {
                        "slot": judge.get("slot", ""),
                        "provider": local_config["judge_provider"],
                        "model": local_config["judge_model"],
                        "verdict": "error",
                        "score": 0.0,
                        "rubric": {},
                        "reasoning": "judge-unavailable",
                        "latency_ms": 0,
                    }
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
