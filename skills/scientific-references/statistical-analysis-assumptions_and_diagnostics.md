---
id: sciref-statistical-analysis-assumptions-and-diagnostics
name: "Scientific Ref: Statistical Assumptions and Diagnostic Procedures"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-analysis): Statistical Assumptions and Diagnostic Procedures"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical analysis assumptions diagnostics"
  - "estatistica analise assumptions diagnostics"
  - "statistical assumptions and diagnostic procedures"
keywords:
  - "statistical"
  - "analysis"
  - "assumptions"
  - "diagnostics"
  - "estatistica"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Statistical Assumptions and Diagnostic Procedures

This document provides comprehensive guidance on checking and validating statistical assumptions for various analyses.

## General Principles

1. **Always check assumptions before interpreting test results**
2. **Use multiple diagnostic methods** (visual + formal tests)
3. **Consider robustness**: Some tests are robust to violations under certain conditions
4. **Document all assumption checks** in analysis reports
5. **Report violations and remedial actions taken**

## Common Assumptions Across Tests

### 1. Independence of Observations

**What it means**: Each observation is independent; measurements on one subject do not influence measurements on another.

**How to check**:
- Review study design and data collection procedures
- For time series: Check autocorrelation (ACF/PACF plots, Durbin-Watson test)
- For clustered data: Consider intraclass correlation (ICC)

**What to do if violated**:
- Use mixed-effects models for clustered/hierarchical data
- Use time series methods for temporally dependent data
- Use generalized estimating equations (GEE) for correlated data

**Critical severity**: HIGH - violations can severely inflate Type I error

---

### 2. Normality

**What it means**: Data or residuals follow a normal (Gaussian) distribution.

**When required**:
- Small-sample normal-theory t/ANOVA inference: the relevant errors (paired differences for paired tests), not arbitrary pooled data
- Linear regression: normal errors support exact finite-sample t/F inference; coefficient estimation itself does not require normal outcomes or predictors
- Some correlation tests (Pearson)

**How to check**:

**Visual methods** (primary):
- Q-Q (quantile-quantile) plot: Points should fall on diagonal line
- Histogram with normal curve overlay
- Kernel density plot

**Formal tests** (secondary):
- Shapiro-Wilk test (good default; scipy handles n up to ~5000 and warns above that)
- Lilliefors test (`statsmodels.stats.diagnostic.lilliefors`) — use this instead of a plain Kolmogorov-Smirnov test, which is invalid when the mean/SD are estimated from the data
- Anderson-Darling test

**Python implementation**:
```python
from scipy import stats
import matplotlib.pyplot as plt

# Shapiro-Wilk test
statistic, p_value = stats.shapiro(data)

# Q-Q plot
stats.probplot(data, dist="norm", plot=plt)
```

**Interpretation guidance**:
- Assess plots, tail behavior, sample balance, dependence and the estimand at every sample size. Formal tests have low power in small samples and detect tiny departures in large samples; non-rejection does not validate a model.
- Look for severe skewness, outliers, or bimodality

**What to do if violated**:
- **Departures**: Evaluate robustness for the target effect and design; there is no universal n=30 threshold. Prespecify robust inference or simulation-based sensitivity. Rank methods change the target and retain assumptions; they are not automatic replacements.
- **Severe violations**:
  - Transform data (log, square root, Box-Cox)
  - Use non-parametric methods
  - Use robust regression methods
  - Consider bootstrapping

**Critical severity**: MEDIUM - parametric tests are often robust to mild violations with adequate sample size

---

### 3. Homogeneity of Variance (Homoscedasticity)

**What it means**: Variances are equal across groups or across the range of predictors.

**When required**:
- Pooled Student's t-test and classical equal-variance ANOVA (not Welch tests)
- Usual homoscedastic OLS standard errors; HC3 addresses independent heteroscedastic errors, not clusters

**How to check**:

**Visual methods** (primary):
- Box plots by group (for t-test/ANOVA)
- Residuals vs. fitted values plot (for regression) - should show random scatter
- Scale-location plot (square root of standardized residuals vs. fitted)

**Formal tests** (secondary):
- Levene's test (robust to non-normality)
- Bartlett's test (sensitive to non-normality, not recommended)
- Brown-Forsythe test (median-based version of Levene's)
- Breusch-Pagan test (for regression)

**Python implementation**:
```python
from scipy import stats
import pingouin as pg

# Median-centered Levene is the Brown-Forsythe variance test
statistic, p_value = stats.levene(group1, group2, group3, center='median')

# For regression
# Breusch-Pagan test
# Note: exog must include the constant column (e.g. exog = sm.add_constant(X),
# or pass the fitted model's model.exog)
from statsmodels.stats.diagnostic import het_breuschpagan
_, p_value, _, _ = het_breuschpagan(residuals, exog)
```

**Interpretation guidance**:
- No variance-ratio cutoff certifies validity. Balanced designs can help robustness but do not remove tail, dependence or variance concerns.
- Do not choose pooled versus Welch inference based only on a preliminary variance p-value.
- For regression: Look for funnel patterns in residual plots

**What to do if violated**:
- **t-test**: Use Welch's t-test (does not assume equal variances)
- **ANOVA**: Use Welch's ANOVA or Brown-Forsythe ANOVA
- **Regression**:
  - Transform dependent variable (log, square root)
  - Use weighted least squares (WLS)
  - Use robust standard errors (HC3)
  - Use generalized linear models (GLM) with appropriate variance function

**Critical severity**: MEDIUM - tests can be robust with equal sample sizes

---

## Test-Specific Assumptions

### T-Tests

**Assumptions**:
1. Independence of observations
2. Normality (each group for independent t-test; differences for paired t-test)
3. Homogeneity only for pooled Student's independent t-test; Welch permits unequal variances

**Diagnostic workflow**:
```python
import scipy.stats as stats
import pingouin as pg

# Check normality for each group
stats.shapiro(group1)
stats.shapiro(group2)

# Check homogeneity of variance
stats.levene(group1, group2)

# Prespecify inference from the design/estimand rather than the screening p-values:
# Option 1: Welch's t-test (unequal variances)
pg.ttest(group1, group2, correction=True)  # correction=True applies Welch's
# (correction='auto' applies Welch only when sample sizes are unequal;
# correction=False forces Student's t-test)

# Option 2: A separately justified rank/distribution question
pg.mwu(group1, group2)  # Mann-Whitney U
```

---

### ANOVA

**Assumptions**:
1. Independence of observations within and between groups
2. Normality in each group
3. Homogeneity of variance across groups

**Additional considerations**:
- For repeated measures ANOVA: Spheri

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

