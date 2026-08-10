from datetime import UTC, datetime

from fastapi import APIRouter

from berrybrain_api.ai_configuration import configuration_gate
from berrybrain_api.database import SessionLocal
from berrybrain_api.job_contracts import canonical_job_counts
from berrybrain_api.schema_migrations import get_schema_version
from berrybrain_api.second_brain import summarize_graph

router = APIRouter(tags=["bootstrap"])


@router.get("/api/v1/bootstrap")
def get_bootstrap() -> dict[str, object]:
    with SessionLocal() as session:
        return {
            "configurationGate": configuration_gate(session),
            "graphSummary": summarize_graph(session),
            "jobCounts": canonical_job_counts(session),
            "schemaVersion": get_schema_version(session.get_bind()),
            "serverTime": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
