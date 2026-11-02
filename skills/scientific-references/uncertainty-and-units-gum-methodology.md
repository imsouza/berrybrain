---
id: sciref-uncertainty-and-units-gum-methodology
name: "Scientific Ref: GUM methodology"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (uncertainty-and-units): GUM methodology"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "uncertainty units gum methodology"
  - "gum methodology"
keywords:
  - "uncertainty"
  - "units"
  - "gum"
  - "methodology"
  - "specialized"
  - "scientific"
  - "reference"
---

# GUM methodology

The *Guide to the Expression of Uncertainty in Measurement* (JCGM 100:2008, "the GUM")
and its Supplement 1 (JCGM 101:2008, the Monte Carlo method) define how an uncertainty
is evaluated, combined, and reported. This file covers the parts that decide whether a
number is defensible.

## Vocabulary that has to stay straight

| Term | Symbol | Meaning |
| --- | --- | --- |
| Measurand | Y | the quantity intended to be measured |
| Estimate | y | the value obtained for it |
| Standard uncertainty | u(x) | uncertainty of an input, expressed as a standard deviation |
| Combined standard uncertainty | u_c(y) | standard uncertainty of the result |
| Expanded uncertainty | U | k * u_c(y) |
| Coverage factor | k | multiplier chosen for a stated coverage probability |
| Coverage probability | p | probability that the interval contains the measurand |

"Error" and "uncertainty" are not synonyms: error is measured value minus a reference
value; uncertainty characterizes dispersion of values attributed to the measurand.
Accuracy is qualitative. Precision can be quantified by a standard deviation, variance,
or coefficient of variation under specified conditions (VIM 2.15).

## Type A and Type B are methods, not qualities

The distinction is only about *how the uncertainty was evaluated*. Neither is more
reliable than the other, and both produce a standard uncertainty on the same footing.

**Type A** — evaluated from a statistical analysis of repeated observations.

For n independent readings with experimental standard deviation s(q):

```text
u(q_bar) = s(q) / sqrt(n)          degrees of freedom: nu = n - 1
```

The standard uncertainty of the *mean* is what enters the budget when the reported
value is a mean. Using s(q) itself overstates it by sqrt(n); using `numpy.std` without
`ddof=1` understates s(q) itself. Both mistakes are common and neither is visible in
the output.

Pool repeatability only when a common variance model is defensible; the same instrument
does not rule out drift, dependence, or different between-run variation.

**Type B** — evaluated by any other means: a calibration certificate, a manufacturer's
specification, a handbook value, a previous measurement, or documented judgement.

The stated quantity is converted to a standard uncertainty by dividing by a factor that
depends on what the statement means:

| What the source states | Assumed density | Divisor | u |
| --- | --- | --- | --- |
| Expanded uncertainty U with stated factor k | use the source model; not necessarily normal | k | U / k |
| Symmetric 95% interval justified by a large-sample normal model | normal | 1.96 | half-width / 1.96 |
| A standard uncertainty | any assigned density with this SD | 1 | as stated |
| Limits ±a, any value equally likely | rectangular | sqrt(3) | a / sqrt(3) |
| Limits ±a, centre far more likely | triangular | sqrt(6) | a / sqrt(6) |
| Limits ±a, extremes more likely (sinusoidal drift, cyclic error) | arcsine | sqrt(2) | a / sqrt(2) |

A 95% label alone does not identify a divisor: recover the source method, degrees of
freedom, asymmetry, and whether the interval is a confidence, coverage, or prediction
interval. Rectangular is a common model when a specification gives limits and says nothing about the
distribution inside them. Digital resolution of one least significant digit d gives
half-width a = d/2, so u = d / (2 sqrt(3)).

The most frequent Type B error is treating a certificate's expanded uncertainty as a
standard uncertainty: it silently doubles the reported interval.

## Law of propagation of uncertainty

For a model Y = f(X_1, ..., X_N) with uncorrelated inputs (JCGM 100:2008 equation 10):

```text
u_c(y)^2 = sum_i ( df/dx_i )^2 * u(x_i)^2
```

with correlated inputs (equation 13):

```text
u_c(y)^2 = sum_i ( df/dx_i )^2 u(x_i)^2
         + 2 * sum_i sum_{j>i} (df/dx_i)(df/dx_j) u(x_i) u(x_j) r(x_i, x_j)
```

The partial derivatives are the **sensitivity coefficients** c_i. They carry units, and
`c_i * u(x_i)` is the contribution of that input expressed in the units of the result.
Comparing contributions, not raw uncertainties, is what tells you where to spend effort.

Correlation is not exotic. It appears whenever two inputs were calibrated against the
same standard, corrected with the same reference value, measured with the same
instrument, or derived from a common fit. The sign of the covariance contribution is `c_i*c_j*r_ij`, not the sign of `r_ij`
alone. Positive correlation increases uncertainty in a sum and can reduce it in a
difference; negative correlation has the reverse effect. In a difference of two similar quantities
measured the same way, the correlation is the whole point — it is what makes the
difference more precise than either term.

## Degrees of freedom and the coverage factor

k = 2 gives about 95% coverage for an approximately normal output with sufficiently
well-determined standard uncertainty. Large degrees of freedom alone do not make an
output normal. The Welch-Satterthwaite formula (JCGM 100:2008 G.2b)
gives them:

```text
nu_eff = u_c(y)^4 / sum_i ( (c_i u(x_i))^4 / nu_i )
```

Assigning infinite degrees of freedom to Type B components assumes their uncertainty
evaluations are sufficiently reliable. This is not automatic: GUM G.4.2 allows finite
values based on the uncertainty of the uncertainty. Infinite-dof terms drop out of the denominator. A single Type A component
from a handful of readings can pull nu_eff low enough that k rises well above 2:

| nu_eff | k for p = 95% |
| --- | --- |
| 2 | 4.30 |
| 5 | 2.57 |
| 10 | 2.23 |
| 20 | 2.09 |
| 50 | 2.01 |
| infinite | 1.96 |

If the dominant component came from five readings, reporting k = 2 understates the
interval by about a quarter. The formula assumes uncorrelated inputs; with correlation
the independent-input formula must not be used without a justified extension or
reformulation in terms of independent sources.

## When the GUM framework is not applicable

The framework linearizes f about the estimates. That is fine when the model is close to
linear across the input uncertainties, and wrong when it is not. Specifically, it
breaks down when:

- the model is significantly nonlinear over ±2u of an input — squares, reciprocals,
  ratios of comparable quantities, exponentials;
- a single non-normal component dominates, so the output is not approximately normal
  and k from a t-distribution does not deliver the claimed coverage;
- the output distribution is asymmetric, which th

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

