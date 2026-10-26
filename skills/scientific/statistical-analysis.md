---
id: sci-statistical-analysis
name: "Scientific: statistical-analysis"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Guided statistical analysis for research data - test selection, assumption checking, effect sizes, power analysis, Bayesian alternatives, and APA-formatted reporting. Use whenever a user wants to compare groups, test a hypothesis, analyze experimental or survey data, check statis"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "statistical analysis"
  - "estatistica analise"
  - "statistical-analysis"
keywords:
  - "statistical"
  - "analysis"
  - "estatistica"
  - "analise"
  - "guided"
  - "research"
  - "test"
  - "selection"
---

# Statistical Analysis

## Overview

Conduct hypothesis tests (t-tests, ANOVA, chi-square), regression, correlation, and Bayesian analyses with systematic assumption checking, effect sizes, and APA-style reporting. Define the estimand and sampling units, diagnose model limitations, and report effect estimates with uncertainty. Numerical screens cannot certify assumptions or scientific validity.

## When to Use This Skill

Use this skill when:
- Conducting statistical hypothesis tests (t-tests, ANOVA, chi-square, non-parametric)
- Performing regression or correlation analyses
- Running Bayesian statistical analyses
- Checking statistical assumptions and diagnostics
- Calculating effect sizes and conducting power analyses
- Reporting statistical results in APA format
- Analyzing experimental or observational data for research

---

## Installation

Targets Pingouin 0.7.0, SciPy 1.18.1, statsmodels 0.15.0, PyMC 6.3.2 and ArviZ 1.3.0 (reviewed 2026-10-01). Create a separate environment; do not add mutually incompatible scientific stacks to a shared project environment.

```bash
uv venv --python 3.12 .venv-statistics
uv pip install --python .venv-statistics/bin/python "pingouin==0.7.0" "scipy==1.18.1" "statsmodels==0.15.0" pandas matplotlib seaborn
# Optional Bayesian examples:
uv pip install --python .venv-statistics/bin/python "pymc==6.3.2" "arviz==1.3.0"
```

On Windows use `.venv-statistics/Scripts/python.exe`. Lock the resolved environment for reproduction.

- Pingouin 0.7 fixes erroneous mixed/repeated-measures corrections, categorical ANOVA, and other results; do not reproduce an old analysis by merely changing its reported version. See the [official changelog](https://pingouin-stats.org/changelog.html).
- Pingouin 0.6+ names are `p_val`, `cohen_d`, `CI95`, `p_unc`. `ttest` reports **absolute** Cohen's d; calculate a signed estimate explicitly. Its `power` column is observed power and should not be used to interpret a null result.
- `correction='auto'` chooses Welch by unequal **sample sizes**, not by variance evidence. Set `correction=True` for prespecified Welch inference.
- PyMC 6 returns an xarray `DataTree`. ArviZ 1 uses `ci_prob` in `summary`/`plot_dist` and `prob` in `hdi`; specify 95% intervals explicitly. See [Bayesian guidance](references/bayesian_statistics.md).
- Pingouin omits `BF10` for one-sided t-tests; posterior directional probabilities are not Bayes factors. A two-sided `BF10` uses its own model/prior and is not the Bayesian counterpart of a Welch unequal-variance model.

For model-specific APIs (OLS, GLM, ARIMA), see the **statsmodels** skill. For PyMC workflows, see the **pymc** skill.

---

## Analysis Workflow

Use the following workflow, documenting prespecified decisions and exploratory departures.

1. **Frame the question before touching the data.** State the hypothesis, the outcome and predictor variables, and the design (independent vs. paired, number of groups). Specify the target effect, sampling unit, dependence, contrasts and multiplicity family before outcome-driven selection. Label adaptive exploration explicitly.
2. **Inspect the data.** Per group: n, mean, SD, median, missing values. Plot the raw data (histograms or box plots) before any test. Unequal group sizes, missingness, floor/ceiling effects, and outliers all change what test is appropriate — surface them to the user rather than silently working around them.
3. **Select the test** using the quick reference below, or `references/test_selection_guide.md` for designs beyond the basics (counts, time-to-event, reliability, factorial).
4. **Check assumptions** with `scripts/assumption_checks.py`. Interpret plots and screens alongside the design and estimand; do not switch tests automatically at a diagnostic p-value threshold. Report justified sensitivity analyses and any departures from the plan.
5. **Run the test** and always compute the effect size alongside it — a p-value assesses incompatibility with the null model; the effect estimate and its uncertainty support judgments about practical importance.
6. **Report** using the APA templates below, including descriptives, exact statistics, effect sizes with CIs, and the assumption checks performed.

If the user only needs one step (e.g., "how many participants do I need?"), jump straight to that section — but still confirm the design assumptions the calculation rests on.

---

## Test Selection Guide

### Quick Reference: Choosing the Right Test

Use `references/test_selection_guide.md` for comprehensive guidance (counts, survival, reliability, factorial designs). Quick reference:

**Group comparisons:** Independent continuous means usually use prespecified Welch's t-test or Welch's ANOVA. Pooled Student/ANOVA inference needs justified equal variance. Paired means use a paired t-test on aligned within-person differences. Repeated or clustered observations require a model of that dependence.

**Rank questions:** Mann-Whitney or Kruskal-Wallis can address distribution/rank contrasts; they are not automatic tests of medians. Wilcoxon signed-rank requires meaningful, symmetrically distributed paired differences. Friedman addresses blocked/repeated rank contrasts. See the reference for ties, small samples, and exact/permutation choices.

**Relationships:** Pearson measures linear association; Spearman measures monotone rank association. Choose by the scientific question, not a normality pretest. Use a suitable regression likelihood for continuous, binary, count or time-to-event outcomes.

**Bayesian alternatives:** Specify the likelihood, prior and comparison explicitly. Posterior estimation does not automatically yield a Bayes factor for a point null.

---

## Assumption Checking

**Always check assumptions before interpreting test results**, and report the checks — reviewers look for them.

Use the bundled `scripts/assumption_checks.py` module. Add the skill’s `scripts/` directory to `PYTHONPATH` (the skill root alone is insufficient):

```python
from assumption_checks import comprehensive_assumption_check

# Within-group outlier screens, normality and variance diagnostics; with plots
results = comprehensive_assumption_check(
    data=df,
    value_col='score',
    group_col='group',  # Independent groups; paired tests use difference scores
    alpha=0.05
)
```

For targeted checks, import individual functions:

```python
from assumption_checks import (
    check_normality,                # Shapiro-Wilk + Q-Q plot + histogram
    check_normal

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

