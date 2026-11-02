---
id: sciref-pkpd-modeling-special-populations
name: "Scientific Ref: Scaling, extrapolation and first-in-human calculations"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pkpd-modeling): Scaling, extrapolation and first-in-human calculations"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pkpd modeling special populations"
  - "scaling, extrapolation and first-in-human calculations"
keywords:
  - "pkpd"
  - "modeling"
  - "special"
  - "populations"
  - "specialized"
  - "scientific"
  - "reference"
  - "scaling"
---

# Scaling, extrapolation and first-in-human calculations

## Size is not maturation

The helper uses `CL=CLref*(WT/WTref)^b` and an optional sigmoidal postmenstrual-age multiplier.
The default b=0.75 for clearance and 1 for volume are modeling conventions, not universal biological
laws. Drug/pathway-specific ontogeny, disease, organ function and binding can change the relation.
Generic TM50/Hill values are illustrative; justify them before predicting neonatal exposure.
Maturation of volume is not implemented by the helper's clearance-only multiplier.

A log-log interspecies slope estimates an association conditional on species/data selection.
Small-sample intervals use t degrees of freedom, but that does not resolve species relevance,
protein binding, transporter differences or nonlinear kinetics. Report the species, weight,
clearance basis, assay, uncertainty and extrapolation range. Do not turn an exponent cutoff into a
automatic correction method.

## Pediatrics and organ function

ICH E11A asks how disease, pharmacology and treatment response support extrapolation between
reference and target populations. Exposure matching can be appropriate with supporting evidence;
80–125% is not a universal pediatric acceptance requirement. Prespecify justified exposure
criteria, uncertainty and safety evaluation for the intended population.
[E11A FDA guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e11a-pediatric-extrapolation).

Renal-function measures differ by equation and indexing. Creatinine clearance, eGFR indexed to
1.73m² and absolute mL/min are not interchangeable. Likewise, hepatic impairment is not fully
summarized by one enzyme value. Changing physiology, dialysis and critical illness need models
that represent those mechanisms and time courses; weight scaling alone is insufficient.

## Starting-dose arithmetic

The FDA 2005 healthy-adult framework uses NOAEL, species relevance, human-equivalent dose and a
safety factor. The helper applies its Km table and reports the calculation, not clinical safety.
Verify the species/body-weight applicability and exposure margins; additional uncertainty can need
a larger safety factor. [FDA starting-dose guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/estimating-maximum-safe-starting-dose-initial-clinical-trials-therapeutics-adult-healthy-volunteers).

MABEL reasoning integrates target biology, species relevance, binding/function, human cell data,
PK and uncertainty. It is not simply choosing the smaller of two calculator outputs. The helper's
`--mabel` inverts an Emax or equilibrium occupancy curve at a requested fractional effect, then
multiplies concentration by clearance (systemic F=1 assumption) to give a **dose rate**. Functional EC50 is not generally
binding Kd. Dose rate is not a bolus starting dose; duration/regimen and absorption are additional
assumptions. High-risk agonism and complex biologics can invalidate this simple relationship.
[EMA first-in-human revision](https://www.ema.europa.eu/en/news/revised-guideline-first-human-clinical-trials).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

