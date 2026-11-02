---
id: sci-relsa-severity-assessment
name: "Scientific: relsa-severity-assessment"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Supports multivariate severity assessment and exploratory endpoint-time score forecasting for laboratory animal studies using the RELSA (RELative Severity Assessment) score and ARIMA-based foRcast forecasting. Use when combining welfare readouts — body weight or weight loss, body"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "relsa severity assessment"
  - "relsa-severity-assessment"
keywords:
  - "relsa"
  - "severity"
  - "assessment"
  - "supports"
  - "multivariate"
  - "exploratory"
  - "endpoint"
---

# RELSA severity assessment and exploratory score forecasting

## Overview

This skill computes reference-relative multivariate scores and exploratory ARIMA forecasts.
It targets the equations and printed example of [RELSA 0.0.1.9000](https://github.com/mytalbot/RELSA)
(commit `e68e8451e8719ccc3600179f55900cd7254ede9d`, current upstream at review), plus the
published [foRcast methodology](https://doi.org/10.3389/fphys.2026.1869563).
The Python forecast helper is an independent nonseasonal approximation, not an exact R port.

RELSA is the RMS of directional deviations divided by each variable's reference maximum
**deviation**. Zero means no measured worsening in those directions; it does not establish
normal welfare. One is a reference scale unit, not a universal endpoint or an upper bound.
Different variables may attain their reference extrema in different animals or at different
times, so the reference cohort need not contain a score of exactly one.

Forecasts estimate a **score at a specified time**, not time-to-endpoint or probability of death.
Keep the approved study's observation schedule and humane endpoint criteria separate from
these exploratory outputs. See [Boundaries](#boundaries-state-these-when-you-report).

## When to use this skill

- Combining weight loss, temperature, clinical scoring, biomarkers, or telemetry into a single
  per-animal severity score
- Asking which animals in a cohort are at risk of reaching a humane endpoint, or predicting
  the severity score at a coming time point
- Comparing severity between treatment groups, interventions, or animal models on a common
  relative scale
- Defining thresholds or zones on a severity scale from the data
- Writing the severity-assessment section of an animal welfare report, a 3Rs/refinement
  analysis, or an application under EU Directive 2010/63/EU

For general forecasting of a time series that is not a severity score, use
**timesfm-forecasting** or **statsmodels**. For study design and sample size, use
**experimental-design** and **statistical-power**.

## Installation

```bash
uv venv --python 3.13 .venv-relsa
uv pip install --python .venv-relsa/bin/python numpy==2.5.3 pandas==3.0.6 scipy==1.18.1 statsmodels==0.15.0 matplotlib==3.11.2
source .venv-relsa/bin/activate
```

Run the examples from this skill directory. `relsa_score.py` needs numpy/pandas;
`kde_thresholds.py` additionally needs scipy; statsmodels is required
for forecasting and matplotlib only for figures.

## Data format

One row per animal per time point, in a CSV:

| id | treatment | condition | day | temp | weight | score | il6 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M01 | treated | endpoint | -1 | 37.15 | 25.17 | 0 | 35.1 |
| M01 | treated | endpoint | 0 | 37.26 | 25.25 | 0 | 39.5 |
| M01 | treated | endpoint | 1 | 35.83 | 23.12 | 4 | 162.0 |

- `id` and a time column (`day`, `time`, `hour`, …) are required; `treatment` and `condition`
  are optional labels used for grouping and for selecting the reference set.
- Time must be finite, with one consistent unit and origin across cohorts. Forecast training and
  target times must align with the chosen regular grid; disable interpolation only on regular observations. The RELSA
  convention codes the baseline time point as `-1`.
- **One row per animal per time point.** Average hourly telemetry to one value per interval
  first (the published models average heart rate, HRV, and temperature, and sum activity).
- Preserve lexical animal IDs (including leading zeros). Duplicate IDs/times, nonnumeric
  measurements and infinities are rejected. Leave missing measurements empty. They are dropped from the score, never imputed — a
  missing value treated as "no deviation" biases severity downward.

`assets/example_cohort.csv` is a small synthetic cohort (6 mice, 9 days, temperature, body
weight, an 0–8 clinical score, and an IL-6-like biomarker) used by every command below, so
each one is runnable as written.

## The four decisions that determine the result

Make these explicitly and write them into the methods. Nothing else about the procedure
matters as much.

**1. Directionality — which variables rise under worsening?** Falling is the default (body
weight, activity, food intake, burrowing, wheel running). Variables that *rise* must be
declared as `--turned`: clinical scores, inflammatory biomarkers, fever, tachycardia. Get
this wrong and the variable contributes nothing at all, silently, because deviations in the
"wrong" direction are floored at zero. Body temperature is model-dependent — it *falls* in
sepsis and endotoxaemia, *rises* in fever models. Nothing in the data can settle this for you:
in the published sepsis model activity legitimately swings further above baseline than below,
so only a variable that *never once* moves the declared way is detectable, and
`build_reference()` warns about exactly that case.

**2. The reference set — relative to what?** RELSA scores mean nothing without it. Choose a scientifically characterized reference and document its burden; the 2026
forecasting study uses the group assumed to carry the greatest burden in each model. A mild reference can push new scores
above 1; too severe compresses everything toward 0. Save it with `--save-reference` and reuse
it with `--load-reference` so later cohorts stay on the same scale. New CLI reference files
also store and reuse normalization, ordinal mappings, baseline selection and rounding; conflicting
options are rejected. Legacy references lack that contract and require the original options.

**3. Scores with a zero baseline.** A clinical score of 0 in a healthy animal cannot be
ratio-normalized — `0/0` is undefined. Use `--score-scale score=8` to map the score's scale
instead (healthy → 100%, worst possible → 200%), which also marks it as turned. This assumes meaningful numeric spacing between ordinal categories. An affine rescaling
applied identically to reference and target cancels in the weight ratio before rounding; the
category encoding, healthy anchor and reference cohort still matter. State those choices. The alternative is to keep the score out of RELSA and use it as an
independent endpoint criterion.

**4. Which variables are measured throughout.** Because the score averages over whichever
variables are available, a variable that appears or disappears mid-trajectory moves the score
by itself. An intermittent measure joining only at the endpoint can lower or raise the composite
without any change in the o

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

