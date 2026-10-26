---
id: sciref-hypothesis-generation-literature-search-strategies
name: "Scientific Ref: Evidence Search and Source Traceability"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypothesis-generation): Evidence Search and Source Traceability"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypothesis generation literature search strategies"
  - "hipotese generation literatura search strategies"
  - "evidence search and source traceability"
keywords:
  - "hypothesis"
  - "generation"
  - "literature"
  - "search"
  - "strategies"
  - "hipotese"
  - "literatura"
  - "specialized"
  - "scientific"
  - "reference"
  - "evidence"
---

# Evidence Search and Source Traceability

## Scope

This workflow supports hypothesis formulation. It is not automatically a systematic review, evidence-grade, patentability search, regulatory determination, or proof of novelty.

## Data and confidentiality gate

Before searching:

- remove confidential identifiers, unpublished results, proprietary sequences, exact vulnerabilities, and controlled operational details from queries;
- confirm that external search is authorized;
- translate sensitive observations into the minimum non-sensitive concepts needed;
- use approved local or institutional search tools when policy requires;
- record what was withheld and how that limits the search.

Do not send unpublished or sensitive data to an external search engine, AI service, citation service, or model without explicit authorization.

## Frame the search

Separate search objectives:

1. **Phenomenon:** Has the observation or a close analogue been reported?
2. **Mechanism:** Which processes could explain it?
3. **Rivals:** Which alternative mechanisms, artifacts, or biases are documented?
4. **Measurement:** How have the constructs been operationalized and validated?
5. **Design:** Which tests discriminate the candidates?
6. **Contrary evidence:** What findings challenge each candidate?
7. **Safety and governance:** Which ethical, biosafety, dual-use, data, or regulatory rules apply?
8. **Priority/novelty:** What prior work, registrations, preprints, patents, and grey literature address the same claim?

Use separate queries so a mechanism search is not mistaken for a novelty search.

## Question structures

Choose a structure matched to the question:

- PICO/PICOT: population, intervention, comparator, outcome, optional time;
- PECO: population, exposure, comparator, outcome;
- diagnostic: population, index test, reference standard, target condition;
- prognostic: population, prognostic factor, outcome, time;
- qualitative: population/sample, phenomenon, context;
- mechanistic: system, perturbation/condition, mediator/process, observable outcome;
- computational/theoretical: model class, assumptions, parameter regime, predicted observable.

Cochrane uses PICO for intervention-effect review questions and distinguishes review PICO, PICO for each synthesis, and PICO of included studies. Do not force PICO onto every domain.

## Source priority

Prefer the source closest to the claim:

1. law, regulation, official policy, or current institutional guidance for governance claims;
2. original paper, protocol, dataset, standard, or methods source for primary claims;
3. current reporting guideline and explanation/elaboration for reporting expectations;
4. systematic review or consensus report for landscape orientation;
5. narrative review for terminology and citation mining;
6. preprint or conference abstract, clearly labeled, for recent unreviewed work;
7. secondary webpages only when they point to a primary source or document current implementation.

Authority does not replace critical appraisal. A primary study may be weak, and a current official policy may be jurisdiction-specific.

## Search sequence

### 1. Broad orientation

- Search the phenomenon and field terminology.
- Locate one or more current reviews or consensus documents.
- Extract synonyms, controlled vocabulary, candidate mechanisms, and landmark sources.

### 2. Primary evidence

- Search each candidate mechanism separately.
- Search the original observation and closest analogues.
- Search prospective, experimental, longitudinal, and replication evidence where relevant.
- Search measurement-validation papers for each operationalization.

### 3. Rival and falsification search

For every candidate, run terms such as:

- alternative explanation;
- confounding;
- selection bias;
- collider bias;
- reverse causation;
- measurement error/artifact;
- negative control;
- failed replication;
- null or contradictory result;
- boundary condition/effect modification.

Record whether a source challenges the mechanism, the measurement, the design, or only its generalizability.

### 4. Foundational and historical search

Use backward citation tracing from methods and review papers. Search original titles, authors, books, standards, and DOI/PMID records. Recency is not a proxy for relevance.

### 5. Forward citation and registration search

Use citation indexes, trial registries, preregistration repositories, preprint servers, data/code repositories, and correction/retraction records as appropriate.

### 6. Policy search

Use current official sites and record:

- jurisdiction and applicability;
- effective or revision date;
- superseded documents;
- local implementation requirements;
- date checked.

For high-consequence work, a search result is not legal, regulatory, ethics, biosafety, or dual-use clearance.

## Search documentation

Complete `assets/search_boundary_template.json`. At minimum include:

- `search_boundary_id`;
- `searched_on`;
- purpose;
- databases/indexes;
- exact queries or reproducible query descriptions;
- date/language/source-type limits;
- inclusion and exclusion scope;
- stop rule or last result screened;
- known access and coverage limitations;
- novelty status.

Use `novelty_status: not_assessed` unless a qualified human has reviewed a fit-for-purpose search. Even a comprehensive search supports only a bounded statement.

## Evidence ledger

Complete `assets/evidence_ledger_template.csv` with one row per source:

- stable source ID;
- linked claim IDs;
- title and author/organization;
- publication date;
- source type and identifier;
- canonical HTTPS URL;
- access date;
- relation: supportive, challenging, contextual, method, safety, or mixed;
- design/document type;
- limitations and notes.

The audit validates structure and links only:

```bash
python3 scripts/audit_evidence_ledger.py \
  local-evidence-ledger.csv \
  local-search-boundary.json \
  --record local-hypothesis-record.json
```

It does not visit URLs, verify existence, appraise evidence, or decide whether a citation supports a claim.

## Claim-to-source notes

For each consequential claim, record:

- the exact source location (section, table, figure, page, or quoted sentence);
- whether the evidence is direct, indirect, analogous, or contradictory;
- study design and target population/system;
- magnitude and uncertainty actually reported;
- key limitations and conflicts;
- applicability to the candidate.

Verify every identifier and claim against th

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

