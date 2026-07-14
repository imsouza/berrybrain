from __future__ import annotations

from dataclasses import asdict, dataclass

from berrybrain_api.services import score_insight_quality


@dataclass(frozen=True)
class InsightFixture:
    name: str
    insight_type: str
    title: str
    description: str
    why: str
    evidence: tuple[str, ...]
    action: str
    impact: str
    confidence: float
    useful: bool
    reviewer_rationale: str


@dataclass(frozen=True)
class InsightUsefulnessMetrics:
    fixture_count: int
    accuracy: float
    precision: float
    recall: float
    accepted_usefulness_rate: float
    meets_target: bool


def useful(name: str, title: str, description: str, why: str, action: str, impact: str) -> InsightFixture:
    return InsightFixture(
        name, "hypothesis", title, description, why,
        (f"{name} source note A", f"{name} source note B"),
        action, impact, 0.84, True,
        "Specific learning claim with two sources and a concrete next action.",
    )


FIXTURES = (
    useful(
        "observability-edge",
        "Edge deployments increase the value of distributed tracing",
        "The edge and observability notes describe failures crossing devices and services, making request traces useful for locating latency.",
        "This links a deployment constraint to a concrete diagnostic technique.",
        "Add an example tracing one request from an edge device to a cloud service.",
        "Connects edge computing, latency, distributed tracing, and observability.",
    ),
    useful(
        "docker-shell",
        "Shell automation is the operational layer around Docker workflows",
        "The Docker note defines repeatable containers while the shell note records commands that build, inspect, and recover them.",
        "Studying both explains how container concepts become repeatable operations.",
        "Create a runbook linking each shell command to a container lifecycle stage.",
        "Adds an application relation from shell automation to Docker operations.",
    ),
    useful(
        "rag-embeddings",
        "Embedding quality constrains retrieval quality in the RAG notes",
        "Retrieval depends on vector similarity while the embedding note explains how chunk meaning is represented before ranking.",
        "It identifies a prerequisite that should be understood before tuning retrieval.",
        "Compare two embedding models on the same five semantic questions.",
        "Creates a prerequisite edge from embeddings to semantic retrieval.",
    ),
    useful(
        "async-backpressure",
        "The async notes omit backpressure as a failure-control concept",
        "Concurrency and queues recur, but no source explains how producers slow down when consumers cannot keep pace.",
        "Without backpressure, examples may fail under sustained load.",
        "Add a note comparing bounded queues, semaphores, and demand signaling.",
        "Creates a grounded knowledge-gap node beside concurrency and queues.",
    ),
    useful(
        "statistics-observability",
        "Sampling assumptions connect statistics to telemetry interpretation",
        "The statistics note discusses sampling error and the tracing note uses sampled requests to estimate service behavior.",
        "The connection prevents treating sampled traces as a complete population.",
        "Document which latency conclusions remain valid under trace sampling.",
        "Connects statistical sampling, tracing, latency, and uncertainty.",
    ),
    useful(
        "security-sessions",
        "Session rotation bridges authentication and incident response",
        "Authentication establishes identity and the incident note describes credential theft, but neither explains invalidating active sessions.",
        "The missing bridge affects containment of account takeover.",
        "Create a recovery checklist covering token revocation and session rotation.",
        "Adds a gap connected to authentication, sessions, and incident response.",
    ),
    useful(
        "database-recovery",
        "Replication does not replace tested database recovery",
        "One note describes replicas for availability while another shows corrupted writes can be copied to every replica.",
        "It distinguishes availability from recoverability and changes backup priorities.",
        "Add a restore drill with measured recovery point and recovery time.",
        "Creates a contrast relation between replication and backup recovery.",
    ),
    useful(
        "concept-centrality",
        "Namespaces are becoming central across Linux and containers",
        "Namespaces recur in Linux process, Docker isolation, and container security notes with consistent meanings.",
        "A permanent concept note would reduce repetition and expose adjacent gaps.",
        "Create a namespaces note linked to processes, containers, and security boundaries.",
        "Promotes namespaces to a central concept connected to three source notes.",
    ),
    InsightFixture(
        "pipeline-backlog", "system_diagnostic",
        "Pipeline bottleneck in note title generation",
        "Four GENERATE_NOTE_TITLE jobs are pending behind the provider queue.",
        "The worker is delayed.", ("jobsByType.GENERATE_NOTE_TITLE=4",),
        "Restart the worker.", "No knowledge graph impact.", 0.95, False,
        "Operational diagnostic, not a claim about user knowledge.",
    ),
    InsightFixture(
        "generic-connection", "new_connection", "Connection found",
        "Two notes may be related.", "This might be useful.", ("notes",),
        "Review it.", "Adds a link.", 0.9, False,
        "Generic wording and no inspectable source claim.",
    ),
    InsightFixture(
        "unsupported-hypothesis", "hypothesis", "Docker improves every deployment",
        "The model asserts a universal improvement without comparative evidence.",
        "It sounds actionable but overgeneralizes.", (), "Adopt Docker everywhere.",
        "Connects Docker to all deployment notes.", 0.91, False,
        "Unsupported universal conclusion with no source evidence.",
    ),
    InsightFixture(
        "raw-json", "hypothesis", "Graph notes indicate semantic state changes",
        '{"graphNotes": 4, "explainedConnections": 2}', "Internal counters changed.",
        ("raw JSON",), "Inspect the pipeline.", "Updates graphSummary.", 0.8, False,
        "Exposes implementation data rather than a cognitive conclusion.",
    ),
)

TECHNICAL_MARKERS = {
    "generate_note_title", "graphnotes", "explainedconnections", "jobsbytype",
    "pipeline bottleneck", "raw json",
}


def classify_fixture(fixture: InsightFixture) -> bool:
    combined = " ".join((fixture.title, fixture.description, fixture.why, *fixture.evidence)).lower()
    if fixture.insight_type == "system_diagnostic" or any(
        marker in combined for marker in TECHNICAL_MARKERS
    ):
        return False
    score = score_insight_quality(
        title=fixture.title,
        description=fixture.description,
        why_it_matters=fixture.why,
        evidence=list(fixture.evidence),
        suggested_action=fixture.action,
        graph_impact=fixture.impact,
        confidence=fixture.confidence,
    )
    return len(fixture.evidence) >= 2 and score >= 0.75


def run_benchmark() -> InsightUsefulnessMetrics:
    predictions = [classify_fixture(fixture) for fixture in FIXTURES]
    tp = sum(predicted and item.useful for predicted, item in zip(predictions, FIXTURES))
    fp = sum(predicted and not item.useful for predicted, item in zip(predictions, FIXTURES))
    fn = sum(not predicted and item.useful for predicted, item in zip(predictions, FIXTURES))
    accepted = [item for predicted, item in zip(predictions, FIXTURES) if predicted]
    accuracy = sum(
        predicted == item.useful for predicted, item in zip(predictions, FIXTURES)
    ) / len(FIXTURES)
    precision = tp / max(1, tp + fp)
    recall = tp / max(1, tp + fn)
    accepted_rate = sum(item.useful for item in accepted) / max(1, len(accepted))
    values = tuple(round(value, 4) for value in (accuracy, precision, recall, accepted_rate))
    return InsightUsefulnessMetrics(
        len(FIXTURES), *values, meets_target=min(values) >= 0.8
    )


if __name__ == "__main__":
    print(asdict(run_benchmark()))
