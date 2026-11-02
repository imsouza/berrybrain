---
id: sci-statistical-power
name: "Scientific: statistical-power"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Calculates sample sizes and statistical power for study planning. Applies when someone asks 'how many subjects/samples/replicates do I need', wants an a priori power analysis, a minimum detectable effect (MDE), a power curve, or needs to justify a sample size for a grant, IRB pro"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "statistical power"
  - "estatistica power"
  - "statistical-power"
keywords:
  - "statistical"
  - "power"
  - "estatistica"
  - "calculates"
  - "sample"
  - "sizes"
  - "study"
---

# Statistical Power & Sample Size

## Overview

Power analysis plans the probability of rejecting a specified null under an assumed alternative. It answers **how many independent experimental units are needed to detect a scientifically important effect**, or what effects a feasible sample could detect. Choose the inferential goal first: precision, equivalence, noninferiority, or sequential monitoring need their own calculations; the bundled superiority-test helpers do not cover them.

Four quantities are locked together for any given test: **sample size (n)**, **effect size**, **significance level (α)**, and **power (1 − β)**. For a fixed design, analysis, and nuisance parameters, fixing three permits solving for the fourth when a solution exists. Every calculation in this skill is some rearrangement of that relationship.

This skill covers the two ways to do power analysis:
- **Analytical** power calculations (exact under some standard-test assumptions; asymptotic approximations for others) — see `references/closed_form_recipes.md`.
- **Simulation / Monte Carlo** (requires a credible data-generating process and a calibrated planned analysis) — see `references/simulation_based_power.md`.

For choosing and converting effect sizes — usually the hardest part — see `references/effect_sizes.md`.

## When to Use This Skill

- Determining required sample size before collecting data (a priori power analysis)
- Finding the minimum detectable effect (MDE) for a fixed, already-determined sample size
- Producing power curves (power vs. n, or power vs. effect size) for a grant or protocol
- Justifying a sample size for an IRB submission, grant, or pre-registration
- Powering designs with unequal group sizes or non-1:1 allocation
- Planning complex mixed models, GLMs, clustering, survival, mediation, and interactions through simulation when simpler approximations do not fit
- Accounting for multiple comparisons, attrition/dropout, or clustering in the sample-size estimate

## Installation

The local examples were checked on Python 3.13 with statsmodels 0.15.0, SciPy
1.18.1, NumPy 2.5.3, pandas 2.3.3, and Matplotlib 3.11.2. Use an environment
separate from the repository's development environment:

```bash
uv venv --python 3.13 .venv-power
uv pip install --python .venv-power/bin/python "statsmodels==0.15.0" "scipy==1.18.1" "numpy==2.5.3" "pandas==2.3.3" "matplotlib==3.11.2"
# Optional comparison / survival methods (also checked for current API use):
uv pip install --python .venv-power/bin/python "pingouin==0.7.0" "lifelines==0.30.3"
```

On Windows use `.venv-power/Scripts/python.exe`. Lifelines 0.30.3 requires
`pandas<3`; the tested pin above accommodates it. Mixed models and GLMs are
included in statsmodels. Record versions and seeds with the output; numerical
smoke tests do not establish a study's effect assumptions or Type I error control.

---

## The one decision that drives everything: the effect size

Power calculations are only as trustworthy as the effect size you feed them. **Do not invent a number.** Use, in rough order of preference:

1. A **minimally important effect** — the smallest effect that would actually change a decision or matter scientifically/clinically (the "smallest effect size of interest", SESOI). This is the most defensible basis: you power to detect what matters, not what you hope to see.
2. A **pilot or prior-study estimate**, with uncertainty and selection bias considered. Small pilots are imprecise; publication or significance-based selection can inflate effects. Use a justified uncertainty model or sensitivity range instead of an arbitrary shrinkage factor.
3. A **convention** (Cohen's small/medium/large) only as a last resort, and say so explicitly.

Whatever you pick, run a **sensitivity analysis**: report how required n changes across a plausible range of effect sizes, not a single point. A power analysis presented as one number hides its biggest source of uncertainty. See `references/effect_sizes.md` for benchmarks and conversions between d, f, r, η², odds ratios, and Cohen's h/w.

> **Avoid post-hoc ("observed") power.** Computing power from the effect size you just estimated is circular: for standard tests it largely restates the test statistic/p-value and adds no independent evidence of adequacy. If a study is already done and you want to know what it could have detected, report a **sensitivity analysis** (MDE at the achieved n) or, better, the confidence interval around the observed effect. This is a common reviewer complaint — do not produce observed power even if asked without flagging the issue.

---

## Quick recipes (closed-form)

The bundled `scripts/power.py` wraps statsmodels and SciPy into one consistent interface so you don't have to remember which solver belongs to which test. Run from `skills/statistical-power/scripts/` or add that directory to `sys.path`.

```python
from power import sample_size, power, mde, power_curve

# 1. How many per group to detect Cohen's d = 0.5, two-sided, 80% power?
sample_size(test="t_ind", effect_size=0.5, power=0.80, alpha=0.05)
# -> 64 in sample 1; equal allocation gives 64 in sample 2

# 2. Two groups, 3:1 allocation (e.g. more controls than cases)
sample_size(test="t_ind", effect_size=0.5, power=0.80, ratio=3.0)

# 3. Fixed n=30/group — what's the minimum detectable d at 80% power?
mde(test="t_ind", nobs1=30, power=0.80, alpha=0.05)

# 4. One-way ANOVA, 4 groups, detect Cohen's f = 0.25
sample_size(test="anova", effect_size=0.25, k_groups=4, power=0.80)

# 5. Two proportions: 0.40 vs 0.55 (auto-converts to Cohen's h)
sample_size(test="two_proportions", prop1=0.40, prop2=0.55, power=0.80)

# 6. Correlation: detect r = 0.30
sample_size(test="correlation", effect_size=0.30, power=0.80)

# 7. Power curve for the grant figure
power_curve(test="t_ind", effect_size=0.5, n_range=range(10, 120, 5),
            save="power_curve.png")
```

For two-sample tests the return is **n1**, with `n2 = ceil(ratio * n1)`; `ratio=n2/n1`. Recheck power using the realized integer ratio. ANOVA rounds total n to a multiple of `k_groups`; paired n counts pairs. One-sided alternatives use signed effects and `"larger"`/`"smaller"`. Proportion MDEs return signed Cohen's h and need a baseline to convert to feasible probabilities.

Supported `test=` values: `t_ind` (two independent means), `t_paired`/`t_one` (paired or one-sample mean), `anova` (one-way), `two_proportions`, `one_proportion`, `correlation`, `chi2` (goodness-of-fit / conti

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

