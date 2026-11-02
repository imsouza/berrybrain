---
id: sciref-statistical-power-closed-form-recipes
name: "Scientific Ref: Closed-Form Power Recipes"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-power): Closed-Form Power Recipes"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical power closed form recipes"
  - "estatistica power closed form recipes"
  - "closed-form power recipes"
keywords:
  - "statistical"
  - "power"
  - "closed"
  - "form"
  - "recipes"
  - "estatistica"
  - "specialized"
  - "scientific"
  - "reference"
---

# Closed-Form Power Recipes

Argument conventions and the underlying statsmodels/scipy calls for every test
the `scripts/power.py` helper supports. Use this when you need to call statsmodels
directly, understand an argument, or handle a case the wrapper doesn't cover.

The four solver quantities — `effect_size`, sample size, `alpha`, `power` — obey
a test-specific equation: set exactly one to `None` for `solve_power`. Check that the requested solution exists and re-evaluate power after rounding. The wrapper requires `alpha < target_power < 1`, validates domains, and rejects unexpected keyword arguments. All examples below were executed with statsmodels 0.15.0 / SciPy 1.18.1 on 2026-10-01.

## Table of contents
- [Two independent means (t-test)](#two-independent-means)
- [Paired / one-sample mean](#paired--one-sample-mean)
- [One-way ANOVA](#one-way-anova)
- [Two proportions](#two-proportions)
- [One proportion](#one-proportion)
- [Correlation](#correlation)
- [Chi-square (goodness-of-fit / contingency)](#chi-square)
- [Multiple regression (R² increment)](#multiple-regression)
- [Effect-size argument cheat sheet](#effect-size-units-per-test)

---

## Two independent means

Effect size = **Cohen's d** = (μ₁ − μ₂) / σ_pooled.

```python
from statsmodels.stats.power import TTestIndPower
analysis = TTestIndPower()

# n per group for d=0.5, 80% power, two-sided
n1 = analysis.solve_power(effect_size=0.5, alpha=0.05, power=0.80,
                          ratio=1.0, alternative="two-sided")

# achieved power at n1=64 per group
pw = analysis.solve_power(effect_size=0.5, nobs1=64, alpha=0.05,
                          ratio=1.0, alternative="two-sided")

# minimum detectable d at n1=30 per group, 80% power
d_min = analysis.solve_power(nobs1=30, alpha=0.05, power=0.80, ratio=1.0,
                             alternative="two-sided")
```

`ratio = nobs2 / nobs1`. For 2:1 allocation set `ratio=2.0`; the returned `nobs1`
is the smaller group for that ratio. Return n1, then enroll `ceil(ratio*n1)` in group 2 and recheck with the realized ratio. The helper assumes equal variances; Welch/heteroskedastic or clustered designs need a matching method. Effects are signed as mean1 minus mean2. `alternative` ∈ `"two-sided"`, `"larger"`, `"smaller"`.

## Paired / one-sample mean

Effect size = **Cohen's dz** for paired (mean difference / SD of the differences),
or d for one-sample. Use `TTestPower` (single-sample solver); `nobs` is the number
of pairs / observations.

```python
from statsmodels.stats.power import TTestPower
TTestPower().solve_power(effect_size=0.4, alpha=0.05, power=0.80,
                         alternative="two-sided")  # -> number of pairs
```

Note: for paired designs dz depends on the within-pair correlation ρ:
`dz = d / sqrt(2*(1-rho))` only if the two marginal SDs are equal and d uses that common SD. Generally `SD(diff) = sqrt(SD1**2 + SD2**2 - 2*rho*SD1*SD2)`. Higher ρ ⇒ larger dz ⇒ smaller n. If you only know
the raw mean difference and SDs, estimate ρ or simulate.

## One-way ANOVA

Effect size = **Cohen's f** = sqrt(η² / (1 − η²)). `nobs` here is **total** n
across all groups under equal allocation and common within-group variance. Round per-group n up, then multiply by `k_groups`; the wrapper performs this balanced rounding.

```python
import math
from statsmodels.stats.power import FTestAnovaPower
total_n = FTestAnovaPower().solve_power(effect_size=0.25, k_groups=4,
                                        alpha=0.05, power=0.80)
per_group = math.ceil(total_n / 4)
total_enrolled = 4 * per_group
```

Conversions: f = 0.10 (small), 0.25 (medium), 0.40 (large). From η²:
`f = sqrt(eta2/(1-eta2))`. From R²: same formula with R².

## Two proportions

Effect size = **Cohen's h** = 2·asin(√p₁) − 2·asin(√p₂). Convert proportions to h,
then use the normal approximation `NormalIndPower`.

```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
h = proportion_effectsize(0.40, 0.55)
n1 = NormalIndPower().solve_power(effect_size=h, alpha=0.05, power=0.80,
                                  ratio=1.0, alternative="two-sided")
```

Alternative **normal approximation for a pooled-null / unpooled-alternative z-test**, not the same arcsine calculation and not an exact binomial test:

```python
from statsmodels.stats.proportion import (
    samplesize_proportions_2indep_onetail, power_proportions_2indep,
)
n1 = samplesize_proportions_2indep_onetail(
    diff=0.55 - 0.40, prop2=0.40, power=0.80, ratio=1,
    alpha=0.05, alternative="two-sided",
)
pw = power_proportions_2indep(
    diff=0.15, prop2=0.40, nobs1=n1, ratio=1, alpha=0.05,
    alternative="two-sided", return_results=False,
)
```

`samplesize_proportions_2indep_onetail` accepts two-sided alternatives but neglects the distant rejection tail when solving n. Pass the intended alpha directly; it handles tail selection internally. Only a null difference of zero is currently supported.

For small samples or rare events, prefer **simulation** with the exact test you'll
run (Fisher's exact, or a chi-square with continuity correction).

## One proportion

Test p against a fixed reference p₀. Convert both to the arcsine scale via Cohen's h
and select statsmodels' single-sample branch (`ratio=0` is a special switch, not an allocation ratio). This is an arcsine-normal approximation, not the exact binomial test.

```python
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
h = proportion_effectsize(0.60, 0.50)
n = NormalIndPower().solve_power(effect_size=h, alpha=0.05, power=0.80, ratio=0.0)
```

For exact binomial planning, enumerate binomial outcomes or simulate using `scipy.stats.binomtest(k, n, p=prop0, alternative=...)`. Its alternatives are `"two-sided"`, `"greater"`, `"less"`; power can change irregularly with integer n because of discrete rejection regions. Cohen's h is only an effect transform, not an exact-test power calculation.

`mde("one_proportion", nobs=100)` and `mde("two_proportions", nobs1=100)` return h; omit proportions. To convert a signed h at baseline p0, let `theta = asin(sqrt(p0)) + h/2`. A feasible p1 exists only when `0 <= theta <= pi/2`; then `p1 = sin(theta)**2`. Squaring sine outside that interval gives a spurious probability. For two-sided h, examine both signs and baseline feasibility.

## Correlation

Effect size = **Pearson r**. No statsmodels solver; use the Fisher z transform
(implemen

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

