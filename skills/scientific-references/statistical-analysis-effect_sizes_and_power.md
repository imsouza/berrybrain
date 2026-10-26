---
id: sciref-statistical-analysis-effect-sizes-and-power
name: "Scientific Ref: Effect Sizes and Power Analysis"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-analysis): Effect Sizes and Power Analysis"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical analysis effect sizes power"
  - "estatistica analise effect sizes power"
  - "effect sizes and power analysis"
keywords:
  - "statistical"
  - "analysis"
  - "effect"
  - "sizes"
  - "power"
  - "estatistica"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Effect Sizes and Power Analysis

This document provides guidance on calculating, interpreting, and reporting effect sizes, as well as conducting power analyses for study planning.

## Why Effect Sizes Matter

1. **Statistical significance ≠ practical significance**: p-values measure incompatibility with a null model under its assumptions, not existence or magnitude
2. **Sample size dependent**: With large samples, trivial effects become "significant"
3. **Interpretation**: Effect sizes provide magnitude and practical importance
4. **Meta-analysis**: Effect sizes enable combining results across studies
5. **Power analysis**: Required for sample size determination

**Golden rule**: ALWAYS report effect sizes alongside p-values.

---

## Effect Sizes by Analysis Type

### T-Tests and Mean Differences

#### Cohen's d (Standardized Mean Difference)

**Formula**:
- Independent groups: d = (M₁ - M₂) / SD_pooled
- Paired groups: specify the standardizer. d_z = M_diff / SD_diff; d_av = M_diff / sqrt((SD_pre² + SD_post²)/2). These are different effects.

**Interpretation** (Cohen, 1988):
- Small: |d| = 0.20
- Medium: |d| = 0.50
- Large: |d| = 0.80

**Context-dependent interpretation**:
- Justify a smallest scientifically meaningful effect from the outcome, intervention and context; no discipline-wide threshold is universally meaningful.
- In medicine: Small effect sizes can be clinically important

**Python calculation**:
```python
import pingouin as pg
import numpy as np

# Independent t-test with effect size
result = pg.ttest(group1, group2, correction=False)
cohens_d = pg.compute_effsize(group1, group2, eftype='cohen')  # signed; ttest returns abs(d)
# (pingouin 0.6.0 renamed columns; on 0.5.x use 'p-val', 'cohen-d', 'CI95%', 'p-unc')

# Manual calculation
mean_diff = np.mean(group1) - np.mean(group2)
n1, n2 = len(group1), len(group2)
pooled_std = np.sqrt(((n1 - 1) * np.var(group1, ddof=1) + (n2 - 1) * np.var(group2, ddof=1)) / (n1 + n2 - 2))
cohens_d = mean_diff / pooled_std

# Paired t-test
result = pg.ttest(pre, post, paired=True)
d_av = pg.compute_effsize(pre, post, paired=True, eftype='cohen')
d_z = pg.compute_effsize(pre, post, paired=True, eftype='cohen_dz')
```

**Confidence intervals for independent pooled d** (approximate parametric interval; supply analyzed, non-missing sample sizes; do not reuse this formula for d_av or assume unequal-variance validity):
```python
import pingouin as pg

# compute_effsize_from_t returns only the point estimate;
# get the CI separately with compute_esci
d = pg.compute_effsize(group1, group2, eftype='cohen')
ci = pg.compute_esci(stat=d, nx=len(group1), ny=len(group2),
                     eftype='cohen', confidence=0.95)
```

---

#### Hedges' g (Bias-Corrected d)

**Why use it**: Cohen's d has slight upward bias with small samples (n < 20)

**Formula**: g = d × correction_factor, where correction_factor = 1 - 3/(4df - 1)

**Python calculation**:
```python
# pg.ttest output has no Hedges' g column; compute it directly
hedges_g = pg.compute_effsize(group1, group2, eftype='hedges')
```

**Use Hedges' g when**:
- Sample sizes are small (n < 20 per group)
- Conducting meta-analyses (standard in meta-analysis)

---

#### Glass's Δ (Delta)

**When to use**: When one group is a control with known variability

**Formula**: Δ = (M₁ - M₂) / SD_control

**Use cases**:
- Clinical trials (use control group SD)
- When treatment affects variability

---

### ANOVA

#### Eta-squared (η²)

**What it measures**: Proportion of total variance explained by factor

**Formula**: η² = SS_effect / SS_total

**Interpretation**:
- Small: η² = 0.01 (1% of variance)
- Medium: η² = 0.06 (6% of variance)
- Large: η² = 0.14 (14% of variance)

**Limitation**: In multi-factor designs each effect's η² shrinks as other factors are added (orthogonal decompositions give additive shares; Type II/III sums in unbalanced designs need not add to total SS); it is partial η² that can sum to > 1.0 across factors

**Python calculation**:
```python
import pingouin as pg

# One-way ANOVA (detailed=True is required for the SS column)
aov = pg.anova(dv='value', between='group', data=df, detailed=True)
eta_squared = aov['SS'][0] / aov['SS'].sum()

# Or read pingouin's np2 column, which is PARTIAL eta-squared:
partial_eta_sq = aov['np2'][0]
# np2 coincides with classical eta-squared only for one-way (single-factor) designs
```

---

#### Partial Eta-squared (η²_p)

**What it measures**: Proportion of variance explained by factor, excluding other factors

**Formula**: η²_p = SS_effect / (SS_effect + SS_error)

**Interpretation**: Same benchmarks as η²

**When to use**: Multi-factor ANOVA (standard in factorial designs)

**Limitation**: Across factors, partial η² values can sum to > 1.0 — they are not additive shares of total variance

**Python calculation**:
```python
aov = pg.anova(dv='value', between=['factor1', 'factor2'], data=df)
# pingouin reports partial eta-squared by default
partial_eta_sq = aov['np2']
```

---

#### Omega-squared (ω²)

**What it measures**: Less biased estimate of population variance explained

**Why use it**: η² overestimates effect size; ω² provides better population estimate

**Formula**: ω² = (SS_effect - df_effect × MS_error) / (SS_total + MS_error)

**Interpretation**: Same benchmarks as η², but typically smaller values

**Python calculation** (one-way table with effect row first and residual row last; the estimator can be negative, so state any truncation convention):
```python
def omega_squared(aov_table):
    ss_effect = aov_table.loc[0, 'SS']
    ss_total = aov_table['SS'].sum()
    ms_error = aov_table.loc[aov_table.index[-1], 'MS']  # Residual MS
    df_effect = aov_table.loc[0, 'DF']

    omega_sq = (ss_effect - df_effect * ms_error) / (ss_total + ms_error)
    return omega_sq
```

---

#### Cohen's f

**What it measures**: Effect size for ANOVA (analogous to Cohen's d)

**Formula**: f = √(η² / (1 - η²))

**Interpretation**:
- Small: f = 0.10
- Medium: f = 0.25
- Large: f = 0.40

**Python calculation**:
```python
eta_squared = 0.06  # From ANOVA
cohens_f = np.sqrt(eta_squared / (1 - eta_squared))
```

**Use in power analysis**: Required for ANOVA power calculations

---

### Correlation

#### Pearson's r / Spearman's ρ

**Interpretation**:
- Small: |r| = 0.10
- Medium: |r| = 0.30
- Large: |r| = 0.50

**Important notes**:
- For Pearson correlation in simple OLS with an intercept, r² equals R². Spearman ρ² concerns ranks and is not raw-outcome variance exp

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

