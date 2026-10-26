---
id: sciref-scientific-brainstorming-idea-evaluation
name: "Scientific Ref: Transparent Idea Evaluation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-brainstorming): Transparent Idea Evaluation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific brainstorming idea evaluation"
  - "cientifico brainstorming idea evaluation"
  - "transparent idea evaluation"
keywords:
  - "scientific"
  - "brainstorming"
  - "idea"
  - "evaluation"
  - "cientifico"
  - "specialized"
  - "reference"
  - "transparent"
---

# Transparent Idea Evaluation

Evaluation narrows a candidate set; it does not convert ideas into evidence.
Use explicit criteria, independent ratings, uncertainty, qualitative review,
adversarial checks, and noncompensatory gates.

## Define criteria before viewing scores

For every criterion record:

- name and decision relevance;
- direction (`higher` or `lower`);
- observable anchors for the minimum, midpoint, and maximum;
- weight and who set it;
- evidence required for a rating;
- uncertainty representation;
- conflicts or overlap with other criteria.

Possible criteria include information gain, ability to distinguish mechanisms,
importance to stakeholders, feasibility, reversibility, novelty relative to a
documented search, methodological rigor, cost, time, equity, safety, and
dual-use burden.

Avoid:

- “impact” or “quality” without anchors;
- counting correlated criteria twice;
- silently converting missing information to a zero;
- changing weights after seeing which idea wins;
- averaging away an ethics, safety, regulatory, or feasibility veto.

## Rating process

1. Train raters on two neutral examples that are not session candidates.
2. Ask raters to score independently and cite the reason or source.
3. Allow `not assessable` and abstention rather than forced precision.
4. Collect a central score and plausible low/high values when uncertainty is
   material.
5. Reveal distributions and reasons.
6. Discuss disagreements, then retain both original and revised ratings.
7. Resolve factual errors separately from preference differences.

Do not report inter-rater agreement as evidence that an idea is correct.
Agreement can reflect shared information or shared bias.

## Weighted additive matrix

The bundled `scripts/evaluate_matrix.py` uses a simple, fully disclosed model.
For criterion \(j\), observed score \(x_{ij}\), minimum \(L_j\), maximum \(U_j\),
and positive weight \(w_j\):

- higher-is-better: \(n_{ij}=(x_{ij}-L_j)/(U_j-L_j)\)
- lower-is-better: \(n_{ij}=(U_j-x_{ij})/(U_j-L_j)\)
- normalized weight: \(p_j=w_j/\sum_j w_j\)
- displayed score: \(100\sum_j p_j n_{ij}\)

This compensatory formula means a high value on one criterion can offset a low
value on another. Keep hard gates outside the formula.

### Criteria configuration

```json
{
  "schema_version": "1.0",
  "criteria": [
    {
      "name": "information_gain",
      "description": "Ability to discriminate plausible mechanisms",
      "weight": 3,
      "direction": "higher",
      "minimum": 1,
      "maximum": 5
    },
    {
      "name": "resource_burden",
      "description": "Relative time, cost, and scarce-resource burden",
      "weight": 2,
      "direction": "lower",
      "minimum": 1,
      "maximum": 5
    }
  ]
}
```

Weights must be explicit, finite, and positive. They need not sum to one; the
script reports both supplied and normalized values. Criterion names must not
collide with `idea_id`, `qualitative_review`, `uncertainties`, or another
criterion's generated `_low`/`_high` columns. Scale widths must be finite.

### Scores CSV

```csv
idea_id,information_gain,information_gain_low,information_gain_high,resource_burden,resource_burden_low,resource_burden_high,qualitative_review,uncertainties,evidence_status,ethics_status
I001,4,3,5,3,2,4,"Distinguishing prediction is clear","Assay performance unknown",search-incomplete,review-required
I002,3,2,4,2,2,3,"Lower burden but less discriminating","Population transfer uncertain",mixed,not-assessed
```

Required columns are `idea_id`, every configured criterion,
`qualitative_review`, and `uncertainties`. Low/high columns are optional but
must appear as pairs and contain `low <= score <= high`. Extra columns are
preserved as qualitative context.

Missing central scores, including abstentions, are rejected. Keep them in the
session record and defer the comparison or document a separate complete-case
matrix; never impute zero or drop a criterion silently. Missing or jointly blank
bounds hold the central rating fixed only for calculation. The output records
`bounds_supplied` per criterion, lists `criteria_without_uncertainty_bounds`,
and warns that this does not imply certainty. Even fully supplied bounds are
plausibility judgments, not confidence or credible intervals.

Run:

```bash
python scripts/evaluate_matrix.py scores.csv \
  --config criteria.json \
  --weight-delta 0.10 \
  --output matrix.json
```

The output includes:

- raw and normalized criterion scores;
- supplied and normalized weights;
- base score and deterministic presentation rank;
- score interval implied by input low/high values;
- minimum/maximum score and rank when each weight is perturbed one at a time
  by the requested fraction and all weights are renormalized;
- qualitative fields, limitations, formula, and tie rule;
- `decision: null` and an explicit notice that no scientific conclusion or
automatic selection was made.

The sensitivity analysis is local and one-factor-at-a-time. It does not explore
all possible weights, criterion dependence, model-form uncertainty, correlated
ratings, or uncertainty in the scale anchors.

## Interpreting sensitivity

Treat a ranking as fragile when:

- rank changes under small, plausible weight perturbations;
- score intervals overlap materially;
- one criterion dominates the result;
- rankings change after a reasonable alternative definition;
- missing evidence is driving optimistic ratings;
- qualitative review or a gate conflicts with the numeric order.

Do not “fix” fragility by choosing weights that stabilize a preferred result.
Use it to identify value judgments, missing information, or candidates that
need further comparison.

## Adversarial review template

For every shortlisted idea record:

```text
Idea ID:
Reviewer (not an originator):
Strongest version of the idea:
Observation that would count against it:
At least two alternative explanations:
Measurement or analysis failure:
Sampling or generalizability failure:
Prior evidence that challenges it:
Potential harm, inequity, or misuse:
Mitigation:
Residual uncertainty:
Disposition: retain / revise / pause / stop / external review
```

Review the strongest version before attacking it. Avoid performative “devil's
advocacy” with no follow-up; every challenge needs a response, owner, and
status.

## Literature check

For each idea:

1. Translate the idea into searchable concepts and alternative terminology.
2. Search primary literature, systematic reviews, methods guidance, negative
   f

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

