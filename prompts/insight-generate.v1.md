# BerryBrain Knowledge Insight Generate v1

Generate real second-brain Knowledge Insights for a learner. Analyze only notes,
concepts, graph nodes, graph edges, and source evidence to find patterns, gaps,
contexts, conclusions, hypotheses, premises, assertions, and study paths.

STRICT SEPARATION:
- Knowledge Insights are about learning: concepts, gaps, connections, context,
  study direction, assumptions, conclusions, and actionable knowledge work.
- System Diagnostics are about operations: jobs, queues, providers, workers,
  backlog, pipeline, latency, errors, JSON payloads, or internal architecture.
- If the evidence only contains system/job/provider/backlog/pipeline data, do
  not create a Knowledge Insight. Return it under `diagnostics` or return no
  insight.
- Never put System Diagnostics in `insights`.

STRICT RULES:
- Use ONLY the provided evidence. Do not invent.
- Output must be in English. User note titles/content may remain in their
  original language when cited.
- Each insight MUST have type, title, description, priority, confidence, and
  evidence.
- Every Knowledge Insight must cite at least two evidence items from notes,
  concepts, graph nodes, graph edges, or retrieved knowledge chunks.
- Do not cite system-only evidence such as jobs, queue, provider status, worker
  state, monitor data, semanticState, jobsByType, raw JSON, or pipeline metrics.
- Do not expose internal keys in title, description, evidence, or suggested
  action. Forbidden examples: explainedConnections, graphNotes, jobsByType,
  GENERATE_NOTE_TITLE, ENRICH_GRAPH_NODE, semanticState, raw JSON, Pipeline
  Bottleneck.
- Technical details can exist only in a separate `technical_details` field, not
  in user-facing text.
- Do not generate generic central-node insights unless the insight explains a
  specific learning conclusion supported by evidence.
- Vary types between context, conclusion, hypothesis, premise, assertion,
  knowledge_gap, new_connection, and study_path.
- Priority: 1-10. Use 10 only for urgent learning gaps, 5 for medium, 1-3 for
  interesting but non-urgent patterns.
- Confidence: 0.1 to 0.99. Be honest. 0.5 = moderate, 0.8+ = strong, 0.3- =
  speculative.
- Title: specific human-readable sentence. Never use the type as title.
- Description: 2-3 clear sentences for a learner, not a system operator.

Insight types:

- **context** — Shared background across notes. Example: "DevOps cluster: Docker, Shell, and Python form the user's automation core."
- **conclusion** — A claim the evidence supports with confidence. Example: "Python acts as the orchestration language between Docker and scripts."
- **hypothesis** — A plausible but unconfirmed relationship. Example: "The user may be migrating from shell scripts to Python automation."
- **premise** — A recurring foundational idea. Example: "Every infrastructure note treats containerization as a standard practice."
- **assertion** — A proposition supported by at least two pieces of evidence. Example: "Backlinks confirm that the user connects Docker to Linux Shell."
- **knowledge_gap** — Missing or weak knowledge. Example: "The vault lacks a note about orchestration with Docker Compose or Kubernetes."
- **new_connection** — A non-obvious relationship with a reason. Example: "Async Python connects to Docker through the concept of scalability."
- **study_path** - A logical learning sequence. Example: "Suggested path: Shell basics -> Docker essentials -> Python async -> FastAPI deployment."

Return valid JSON:

```json
{
  "insights": [
    {
      "type": "context",
      "title": "Specific learner-facing title",
      "description": "2-3 sentences of grounded analysis",
      "priority": 7,
      "why_it_matters": "Why this helps the user's learning",
      "evidence": ["note/path.md: human-readable evidence", "connection A-B: reason"],
      "suggested_action": "Concrete learning action",
      "graph_impact": "How it changes or clarifies the knowledge graph",
      "confidence": 0.82,
      "related_notes": ["path/to/note.md"]
    }
  ],
  "diagnostics": [
    {
      "type": "system_diagnostic",
      "title": "Operational issue title",
      "description": "Only use this for jobs, queues, providers, workers, backlog, or pipeline status."
    }
  ]
}
```

Maximum 5 Knowledge Insights per call. Only include insights with confidence >= 0.3.
Priority and confidence MUST be numbers, never strings.
If there is not enough note/concept/graph evidence, return `{"insights":[],"diagnostics":[]}`.
