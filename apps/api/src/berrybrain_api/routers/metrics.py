from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.models import MetricRecord

router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])


@router.get("/")
def list_metrics():
    with SessionLocal() as session:
        metrics = (
            session.execute(
                select(MetricRecord).order_by(MetricRecord.measured_at.desc())
            )
            .scalars()
            .all()
        )
        return {
            "metrics": [
                {
                    "id": m.id,
                    "name": m.name,
                    "value": m.value,
                    "unit": m.unit,
                    "formula": m.formula,
                    "version": m.version,
                    "window": m.window,
                    "sample_size": m.sample_size,
                    "sources": m.sources,
                    "measured_at": m.measured_at.isoformat() if m.measured_at else None,
                }
                for m in metrics
            ]
        }
