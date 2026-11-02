---
id: sciref-analytical-method-validation-ich-q2r2
name: "Scientific Ref: ICH Q2(R2) — Structure and Recommended Data"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (analytical-method-validation): ICH Q2(R2) — Structure and Recommended Data"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "analytical method validation ich q2r2"
  - "ich q2(r2) — structure and recommended data"
keywords:
  - "analytical"
  - "method"
  - "validation"
  - "ich"
  - "q2r2"
  - "specialized"
  - "scientific"
  - "reference"
---

# ICH Q2(R2) — Structure and Recommended Data

Research basis: **2026-09-30**, read from the ICH Harmonised Guideline *Validation of Analytical
Procedures Q2(R2)*, Final Version adopted 1 November 2023, with the error correction dated
30 November 2023. ICH licenses its documents for reuse with acknowledgement, so requirements are
summarised here directly. Confirm the current text and your region's implementation date at
<https://database.ich.org/sites/default/files/ICH_Q2%28R2%29_Guideline_2023_1130.pdf>.

## Document history that matters

| Version | Date | Note |
| --- | --- | --- |
| Q2A | Oct 1994 | Text |
| Q2B | Nov 1996 | Methodology |
| Q2(R1) | Nov 2005 | Q2B merged into the parent guideline |
| Q2(R2) | 1 Nov 2023 | Complete revision, aligned with the new Q14 |
| Q2(R2) correction | 30 Nov 2023 | Table 5 reportable-range linearity formulae; Tables 6–11 |

If a protocol cites "ICH Q2(R1)" or lists characteristics in the R1 order, it is working from the
superseded structure. The error correction is easy to miss and applies to the dissolution example
and to Annex 2 Tables 6–11.

## The restructure

Q2(R1) presented a flat list. Q2(R2) groups methodology under section 3 by performance
characteristic:

```
3.1  Specificity/Selectivity
       3.1.1 General considerations (absence of interference, orthogonal comparison,
             technology-inherent justification)
3.2  Range                                    <-- parent characteristic
       3.2.2 Response
               3.2.2.1 Linear response        <-- what R1 called "linearity"
               3.2.2.2 Non-linear response
               3.2.2.3 Multivariate calibration
       3.2.3 Validation of lower range limits <-- what R1 called LOD and LOQ
3.3  Accuracy and Precision
       3.3.1 Accuracy
       3.3.2 Precision (repeatability, intermediate precision, reproducibility)
       3.3.3 Combined approaches for accuracy and precision   <-- new
3.4  Robustness  --> largely a development activity, see ICH Q14
```

Section 2 carries the general considerations, including two concepts absent from R1: **reportable
range** (2.3) and **considerations for multivariate analytical procedures** (2.5).

## Table 1 — which tests for which measured attribute

Table 1 identifies tests normally conducted by measured quality attribute. It allows justified
alternatives; the table is not an unconditional legal requirement.

| Characteristic | Identity | Impurity: quantitative | Impurity: limit test | Assay (content/potency) |
| --- | --- | --- | --- | --- |
| Specificity test | yes | yes | yes | yes |
| Response (calibration model) | no | yes | no | yes |
| Lower range limit | no | QL† | DL | no |
| Accuracy test | no | yes | no | yes |
| Repeatability test | no | yes | no | yes |
| Intermediate precision test | no | yes‡ | no | yes‡ |

† In some complex cases DL may also be evaluated.
‡ Not required independently where reproducibility has been performed and intermediate precision
can be derived from that dataset.

Further notes from Table 1: other quantitative measurements follow the impurity scheme when the
range limit is close to DL/QL, and the assay scheme when it is not. Some characteristics may be
substituted by technology-inherent justification for physicochemical properties. Lack of specificity
in one procedure should be compensated by one or more supporting procedures unless justified.

## Table 2 — reportable range examples

The reportable range derives from the specification and must include the upper and lower
specification or reporting limits. Other ranges are acceptable if justified; at low amounts a wider
upper range may be more practical.

| Use | Low end | High end |
| --- | --- | --- |
| Assay of a product | 80% of declared content, or 80% of the lower specification limit | 120% of declared content, or 120% of the upper specification limit |
| Potency | lowest specification limit −20% | highest specification limit +20% |
| Content uniformity | 70% of declared content | 130% of declared content |
| Dissolution, IR, one point | Q − 45% of the lowest strength specification | 130% of declared content of the highest strength |
| Dissolution, IR, multi-point | lower limit as justified, or QL | 130% of declared content of the highest strength |
| Dissolution, modified release | lower limit as justified, or QL | 130% of declared content of the highest strength |
| Impurity | reporting threshold | 120% of the specification limit |
| Purity (area %) | 80% of the lower specification limit | upper specification limit, or 100% |

Where assay and impurity run as a single test with one standard, linearity must be shown both at the
impurity reporting level and up to 120% of the assay specification limit.

**Reportable range vs working range.** The reportable range is the interval of *reported results*.
A working range is what is presented to the instrument, and may differ because of dilution or other
sample preparation. They can be identical. Mathematical calculation normally links the two.

## Recommended data, by characteristic

**Specificity (3.1).** Demonstrate absence of relevant interference, or compare against an
orthogonal procedure, or justify from the technology. For a stability-indicating claim (2.4),
include samples containing relevant degradation products: spiked with target analytes and known
interferences, stressed physically and chemically, and aged or stress-stored product samples.

**Response — linear (3.2.2.1).** Evaluate across the range. **A minimum of five concentrations,
appropriately distributed, is recommended.** Report the plot, the correlation coefficient or
coefficient of determination, the y-intercept, the slope, and *an analysis of the deviation of the
actual data points from the regression line* — for a linear response, assess the impact of any
non-random pattern in the residual plot. Data may be transformed (for example logarithmically) if
necessary. Other approaches require justification.

**Response — non-linear (3.2.2.2).** Some procedures are legitimately non-linear; immunoassays and
cell-based assays commonly give an S-shaped curve, typically modelled with four- or five-parameter
logistic functions. For these, **linearity of the concentration–response relationship is not
required.** Assess the model by non-linear regression, and evaluate whether results are proportional
to the true values across the range.

**Response — multivariate (3.2.2.3).** Algorithms may be linear or non-linear. Accuracy depends on

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

