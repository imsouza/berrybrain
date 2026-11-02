---
id: sciref-scholar-evaluation-responsible-assessment
name: "Scientific Ref: Responsible Assessment and Safety Boundary"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scholar-evaluation): Responsible Assessment and Safety Boundary"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scholar evaluation responsible assessment"
  - "responsible assessment and safety boundary"
keywords:
  - "scholar"
  - "evaluation"
  - "responsible"
  - "assessment"
  - "specialized"
  - "scientific"
  - "reference"
---

# Responsible Assessment and Safety Boundary

## Non-negotiable boundary

This skill is for **developmental review of scholarly works** and for auditing a
low-stakes assessment process. It must not automate, recommend, materially
influence, or provide a score for:

- hiring, promotion, or tenure;
- admissions;
- grant or other funding decisions;
- prizes, honors, or awards;
- discipline, dismissal, or sanctions; or
- any other high-impact personnel decision.

Do not rank people. Do not convert several judgments into a single composite
person score. Do not infer a person's ability, character, integrity, future
performance, protected characteristics, or institutional worth.

This boundary remains in force when a human is nominally “in the loop.”
Checklists, committees, or disclaimers do not make a prohibited workflow safe.
If a request crosses the boundary, stop and offer one of these alternatives:

1. developmental comments on a public or authorized scholarly work, with no
   person comparison or decision advice;
2. an audit of whether an existing assessment process follows responsible
   assessment principles, without processing applications or recommending an
   outcome; or
3. neutral documentation of criteria for review by the organization's legal,
   privacy, accessibility, labor, ethics, and disciplinary experts.

## Allowed scope

Examples of allowed uses, subject to authorization and data protection:

- feedback on a draft paper, protocol, research idea, or literature synthesis;
- a retrospective methods or reporting review;
- calibration exercises using synthetic or public scholarly works;
- checking evidence traceability;
- describing the sensitivity of work-level scores to rubric weights; and
- auditing a low-stakes evaluation design for missing governance controls.

“Publication readiness” and “accept/reject” recommendations are excluded.
Describe evidence, limitations, and improvement options instead.

## Accountable human process

For any organizational use, an accountable committee must own the process. It
must include relevant disciplinary and assessment-methods expertise and must:

- publish the construct, intended use, rubric, weights, evidence requirements,
  and interpretation limits before reviewing;
- record member qualifications, training, calibration, and drift checks;
- disclose conflicts, require recusal, and maintain a conflict record;
- provide an understandable notice and a meaningful appeal or correction route;
- provide accessible materials and reasonable accommodations;
- define lawful purpose, access controls, minimization, retention, and deletion;
- review disciplinary, language, career-path, disability, and subgroup effects;
- document disagreements and uncertainty rather than force consensus; and
- periodically evaluate and revise the evaluation.

No script in this skill is the accountable reviewer. Script output is a
descriptive record for qualified human interpretation.

## Qualitative-first evidence

Start with the values and construct, not the data that happen to be available.
Use evidence that directly bears on the criterion:

- the work's questions, methods, analyses, outputs, limitations, and provenance;
- datasets, software, protocols, materials, registrations, replications, and
  negative or null findings where relevant;
- transparent records of responsible practices and justified restrictions;
- contribution records, including CRediT roles when useful, without treating a
  role as proof of quality; and
- influence on policy, practice, communities, teaching, infrastructure, or
  knowledge, when this is within the stated construct and supported by evidence.

Ask what is missing, inaccessible, contested, or not applicable. A missing item
is not a zero. A not-applicable item is not evidence of deficiency.

## Prohibited proxies and contextual indicators

The exclusions below are this skill's scope policy. DORA and CoARA permit
responsible contextual indicator use; they do not validate this rubric or
authorize its use for the consequential decisions excluded above.

Do not score or infer quality from:

- Journal Impact Factor or other journal-level measures;
- h-index, i10-index, publication counts, or citation counts;
- altmetrics or attention counts;
- journal, conference, institutional, geographic, or employer prestige;
- venue identity or ranking; or
- author affiliation, career path, network, or reputation.

The bundled rubric validator rejects common proxy-measure criteria.

If a qualified reviewer has a legitimate, predeclared reason to mention a
quantitative indicator descriptively outside the bundled scoring tools, record:

1. the exact construct and purpose;
2. why the indicator bears on that construct at the correct unit of analysis;
3. source, version, query date, coverage, exclusions, and data quality;
4. field, language, output-type, publication-age, career-stage, and time-window
   effects, including the reference cohort and normalization method;
5. uncertainty, missingness, gaming risks, and known biases;
6. why qualitative evidence is insufficient by itself; and
7. a statement that the indicator is not a direct measure of quality.

Do not add counts from different databases as though their covered works or
citing records were disjoint. Preserve the provider, snapshot date, exact work
identifiers, version/deduplication rule, and unavailable values. A failed query
is not a measured zero. A DOI identifies a work record, not scientific validity;
author-name matches alone do not establish identity. These scripts fetch no
bibliometric or author data.

Never use an indicator merely because it is available. Never hide several
different indicators inside an opaque composite.

## Rubric evidence and psychometric caution

A rubric is a measurement claim. Before operational use, record:

- **construct:** what is and is not being assessed;
- **intended interpretation and use:** the exact meaning claimed for scores;
- **provenance:** who designed and approved criteria, anchors, and weights;
- **content evidence:** disciplinary expert and stakeholder review of coverage;
- **response process:** how raters interpret anchors and use evidence;
- **rater protocol:** selection, training, calibration, qualification, and drift;
- **agreement/reliability:** a design-appropriate analysis and its uncertainty;
- **fairness:** accessibility, subgroup, language, and disciplinary review;
- **traceability:** stable evidence references for each rating;
-

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

