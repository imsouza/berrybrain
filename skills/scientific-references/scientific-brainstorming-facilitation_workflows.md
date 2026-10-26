---
id: sciref-scientific-brainstorming-facilitation-workflows
name: "Scientific Ref: Facilitation Workflows and Records"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-brainstorming): Facilitation Workflows and Records"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific brainstorming facilitation workflows"
  - "cientifico brainstorming facilitation workflows"
  - "facilitation workflows and records"
keywords:
  - "scientific"
  - "brainstorming"
  - "facilitation"
  - "workflows"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Facilitation Workflows and Records

These workflows make a session reproducible without turning facilitation into
an automatic scientific decision. Adapt timing and accessibility needs, but
record adaptations.

## Minimum session record

Create one record with:

- session ID, date, title, focal question, and decision owner;
- facilitator, participant pseudonyms, represented perspectives, missing
  perspectives, and relevant conflicts;
- in-scope/out-of-scope boundaries and constraints;
- information and examples shown before independent generation;
- idea, assumption, cluster, criterion, review, evidence-check, gate, and
  decision-log entries;
- method, timing, anonymization, voting, merge, and stopping rules;
- AI tool/version/purpose when used, without storing sensitive prompt content;
- deviations from the planned process and their reasons.

Use `scripts/session_scaffold.py` to create a deterministic JSON starting
point. It intentionally omits a generated timestamp: provide `--date` when a
date belongs in the record.

## Provenance templates

### Idea

```json
{
  "id": "I001",
  "statement": "A concise candidate research direction.",
  "provenance": {
    "origin": "human",
    "contributor_ids": ["P01"],
    "recorded_stage": "independent",
    "source_refs": [],
    "ai_tool": null
  },
  "assumption_ids": ["A001"],
  "predicted_observations": ["What would be expected if the idea were useful"],
  "uncertainties": ["The main unresolved uncertainty"],
  "evidence_status": "not-checked",
  "status": "candidate"
}
```

Allowed origin labels in the bundled validator are `human`, `ai-assisted`,
`literature-inspired`, `mixed`, and `other`. An origin label documents process;
it does not determine quality or ownership.

### Assumption

```json
{
  "id": "A001",
  "statement": "The measurement reflects the proposed construct.",
  "category": "measurement",
  "status": "untested",
  "test_or_check": "Compare with an orthogonal measure.",
  "owner_id": "P01",
  "evidence_refs": []
}
```

Useful categories include `causal`, `mechanistic`, `measurement`, `sampling`,
`operational`, `statistical`, `feasibility`, `ethical`, and `value`.

### Literature check

```json
{
  "idea_id": "I001",
  "checked_on": "2026-07-23",
  "queries": ["Exact query or protocol identifier"],
  "sources_screened": ["DOI or stable URL"],
  "support": [],
  "challenges": [],
  "search_limits": ["Databases, date, language, or access limits"],
  "status": "search-incomplete",
  "reviewer_id": "P02"
}
```

Do not store copyrighted full text, confidential reviews, credentials, or
personal data in the register.

## 30-minute individual or pair workflow

### Minute 0–5: scope

1. Write one question and one decision the session can inform.
2. List real and assumed constraints separately.
3. Check whether clinical, ethics, safety, dual-use, privacy, or regulatory
   concerns require a different process.

### Minute 5–12: independent generation

- Work silently, even as a pair.
- Generate one idea per record.
- Attach at least one assumption and one uncertainty.
- Do not search or ask an AI system during this first round unless the session
  explicitly studies AI anchoring.

### Minute 12–17: share and expand

- Read ideas without ranking.
- Clarify wording.
- Run a second two-minute private round for additions and contradictions.

### Minute 17–23: cluster and criteria

- Cluster by one declared relation.
- Define three to five criteria with directions and scale anchors.
- Identify any noncompensatory safety or ethics gates.

### Minute 23–28: challenge

- Write one disconfirming observation and one alternative explanation for each
  leading candidate.
- Mark literature work as `not-checked` unless a real search was performed.

### Minute 28–30: log

- Select the next information-gathering action, not a scientific conclusion.
- Record owner, due/revisit condition, and unresolved concerns.

## 60–90 minute facilitated group workflow

### Before the session

- Obtain a neutral focal question from the decision owner.
- Recruit complementary perspectives and identify missing voices.
- Send constraints and definitions, not example solutions.
- Choose an anonymous contribution path.
- Predeclare how ideas are retained, clustered, rated, and escalated.
- Decide what information must not enter shared notes or external tools.

### Opening (10 minutes)

- State purpose, boundaries, and what the session cannot establish.
- Explain the sequence: independent generation, sharing, clustering,
  evaluation, challenge, then next-step logging.
- Ask leaders and sponsors to withhold preferences.
- Invite conflict and accessibility disclosures.

### Independent round (10–15 minutes)

- Same prompt and time for all.
- Require stable idea IDs, assumptions, and uncertainty.
- Allow private submission to the facilitator.

### Round robin and second round (15–20 minutes)

- One item per person per turn; passing is permitted.
- Clarify without advocacy.
- Display all items simultaneously only after initial capture.
- Add a short second private generation round.

### Clustering (10–15 minutes)

- Name the relationship used for each cluster.
- Keep originals visible.
- Log every merge and preserve minority interpretations.
- Do not use lexical similarity as a claim of semantic equivalence.

### Independent evaluation (10 minutes)

- Publish criteria, definitions, directions, and weights first.
- Rate privately; permit uncertainty ranges and abstention.
- Reveal distributions before discussion.

### Challenge and gate (15 minutes)

- Assign each candidate to a non-originator.
- Record falsifiers, alternatives, bias risks, harm/misuse potential, and
  mitigations.
- Route triggered reviews to the responsible office; do not resolve them by
  vote.

### Close (5–10 minutes)

- Log candidate dispositions and dissent.
- Assign literature, feasibility, consultation, or protocol tasks.
- State that any score or rank is provisional.
- Schedule a revisit after evidence checks or external review.

## Asynchronous workflow

Use for distributed teams or when status differences make live contribution
difficult.

1. Freeze the prompt, definitions, scope, and deadline.
2. Collect independent entries without showing the current pool.
3. Release a de-identified pool at the same time to all participants.
4. Collect clarification requests and second-round ideas.
5. Publish a merge log and let originators contest merges.
6. Collect ratings and rationales independen

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

