from fastapi import APIRouter

from berrybrain_api.performance_metrics import performance_snapshot

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("/performance")
def performance_metrics() -> dict:
    return performance_snapshot()
