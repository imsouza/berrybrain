---
id: sciref-scientific-brainstorming-brainstorming-methods
name: "Scientific Ref: Brainstorming and Elicitation Methods"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-brainstorming): Brainstorming and Elicitation Methods"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific brainstorming brainstorming methods"
  - "cientifico brainstorming brainstorming methods"
  - "brainstorming and elicitation methods"
keywords:
  - "scientific"
  - "brainstorming"
  - "methods"
  - "cientifico"
  - "specialized"
  - "reference"
---

# Brainstorming and Elicitation Methods

Use methods as fit-for-purpose process choices, not creativity guarantees. The
best-supported finding in classic laboratory work is narrow: interacting
face-to-face groups often produce fewer nonredundant ideas than the pooled
output of the same number of people working independently, with turn-taking
(`production blocking`) an important mechanism. That does not establish that
independent work is always better for learning, synthesis, commitment,
selection, or every real-world task. See `sources.md` for studies and
limitations.

## Choose by purpose

| Need | Suitable pattern | Main caution |
|---|---|---|
| Broad initial idea pool | Independent generation, then structured sharing | A larger pool is not automatically a better decision |
| Equal participation and same-day prioritization | Nominal group technique (NGT) | Votes show panel preference, not scientific truth |
| Iterative geographically distributed judgment | Delphi | Consensus can stabilize around shared bias |
| Quantitative uncertain values for a model | Structured expert elicitation | Expert judgment does not replace empirical evidence |
| Explore a combinatorial design space | Morphological analysis | Combinations may be infeasible or meaningless |
| Reframe an existing concept | SCAMPER or assumption reversal | Prompting heuristics have context-dependent evidence |
| Stress-test shortlisted ideas | Red team, premortem, alternative explanations | Critique needs an explicit response and owner |

For consequential decisions, state why the chosen process fits the question,
who is included, what information participants see, and how uncertainty and
dissent will be retained.

## Independent-then-interactive generation

This is the default for a live research session.

1. Give every participant the same neutral question, constraints, and time.
2. Ask them to write ideas privately and in parallel.
3. Capture each idea before anyone sees another participant's answer.
4. Pool ideas with stable IDs; optionally mask contributor identity.
5. Clarify in a round robin without advocacy or scoring.
6. Add a second private round after participants have seen the pool.
7. Cluster by a declared relation while preserving original text.
8. Move to a separately announced evaluation phase.

Why use it:

- Parallel work avoids waiting to speak.
- Human-first generation limits early leader, example, and AI anchors.
- The second private round permits stimulation from others' ideas without
  requiring immediate public performance.

Limits:

- Classic brainstorming studies often used short, artificial tasks and student
  samples.
- Pooled individual output may contain redundancy and miss benefits of
  dialogue, knowledge integration, or implementation commitment.
- Higher idea counts do not guarantee better final selections. One experiment
  found nominal groups produced more and more-original ideas, but selected
  ideas were not better than those of interactive groups.

## Nominal group technique

NGT is a facilitated, usually synchronous process for eliciting and
prioritizing contributions. A common four-stage form is:

1. **Silent generation:** participants independently answer one precise
   question.
2. **Round-robin recording:** each person contributes one item at a time until
   all items are recorded.
3. **Clarification:** discuss meaning, not merit; merge only with originators'
   agreement and preserve a merge log.
4. **Independent rating or ranking:** participants vote privately using
   predeclared rules.

Use NGT when equal airtime, traceability, and prompt prioritization matter.
Report:

- recruitment and relevant perspectives;
- exact question and materials shown in advance;
- group size, facilitator, accessibility adaptations, and conflicts;
- how items were edited, merged, removed, or added;
- rating scale, consensus or retention rule, missing votes, ties, and
  abstentions;
- full distribution, not only top-ranked items.

Do not:

- call a ranked list “validated”;
- drop low-ranked minority concerns when they concern safety or ethics;
- infer population prevalence from a purposive panel;
- silently modify NGT and still imply a standardized procedure.

NGT is flexible, and reviews document substantial variation in implementation.
Describe the procedure actually used.

## Delphi

Delphi is an iterative, usually anonymous elicitation process with controlled
feedback between rounds. It is useful when participants are dispersed,
face-to-face status effects are a concern, or judgments need time for revision.

### Minimal defensible design

1. Define why Delphi is appropriate and what decision it will inform.
2. Predefine “expertise” or stakeholder eligibility; sample multiple relevant
   perspectives rather than only prestigious titles.
3. Pilot unambiguous questions and scales.
4. Predefine the number or stopping logic for rounds, feedback statistics,
   consensus rule, missing-data handling, and treatment of new items.
5. Collect round 1 independently.
6. Return controlled feedback that includes the distribution and anonymized
   reasons, not only a mean.
7. Let participants retain or revise judgments and explain important changes.
8. Report attrition by round, disagreement, stability, and items without
   consensus.

### Interpretation

- Consensus means convergence among this panel under this protocol.
- It does not establish correctness, causality, clinical effectiveness, or
  ethical acceptability.
- Anonymity can reduce interpersonal pressure but also removes conversational
  repair and may obscure conflicts of interest.
- Repeated feedback may manufacture agreement. Preserve rationales and
  minority estimates.
- “Modified Delphi” is not self-explanatory; list every modification.

Use the CREDES checklist or the 2023 RAND methodological guidance when a Delphi
result will be published or relied upon. Those resources are indexed in
`sources.md`.

## Structured expert elicitation

Use structured expert elicitation when empirical evidence is incomplete and a
decision model needs quantities or probability distributions—not simply a list
of ideas. Follow domain guidance where available.

High-level sequence:

1. Define the target quantity, unit, conditioning information, time horizon,
   and resolution criterion.
2. Review available evidence systematically before asking for judgment.
3. Select experts for relevant and complementary expertise; disclose conflicts.
4. Train participants to 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

