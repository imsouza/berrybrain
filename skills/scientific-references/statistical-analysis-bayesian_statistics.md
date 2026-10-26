---
id: sciref-statistical-analysis-bayesian-statistics
name: "Scientific Ref: Bayesian Statistical Analysis"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (statistical-analysis): Bayesian Statistical Analysis"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "statistical analysis bayesian statistics"
  - "estatistica analise bayesian statistics"
  - "bayesian statistical analysis"
keywords:
  - "statistical"
  - "analysis"
  - "bayesian"
  - "statistics"
  - "estatistica"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
---

# Bayesian Statistical Analysis

Reviewed 2026-10-01 for PyMC 6.3.2 and ArviZ 1.3.0 (Python 3.12+). The examples are local statistical APIs, with no authentication or service endpoint. PyMC returns xarray `DataTree` groups such as `posterior`, `sample_stats`, `observed_data` and `posterior_predictive`. ArviZ's current API is split across `arviz-stats` and `arviz-plots`, re-exported by `arviz`.

The model fragments below require finite, aligned data supplied by the analyst. Their API mechanics were exercised on small synthetic datasets with short native PyMC NUTS chains, using the Python PyTensor backend on the reviewed Mac. Those runs do not establish convergence or validate the scientific models. On this host C linking failed with missing `-ld64`; `PYTENSOR_FLAGS=cxx=` was an explicit runtime workaround, not evidence of successful C-backend execution.

## Questions, priors and uncertainty

Bayes' theorem gives posterior density proportional to likelihood times prior density. A posterior probability statement is conditional on that likelihood, prior, sampling design and available data. A continuous prior generally assigns zero probability to an exact point null: posterior draws cannot by themselves give a Bayes factor for that null.

Specify the estimand, units, independent sampling unit, censoring/missingness and dependence before choosing a model. Small samples may be weakly identified and sensitive to priors; Bayesian inference does not create information absent from the data.

- Scale priors using meaningful units and external knowledge. A Normal(0, 10) prior is not universally weakly informative. Using the same data to tune priors is an empirical choice that must be disclosed.
- A HalfNormal or HalfCauchy prior on `sigma` is a prior on standard deviation, not variance. Very heavy tails can cause computational problems.
- A flat prior over the real line is improper, not a proper Uniform(-infinity, infinity) distribution; it can yield an improper posterior or undefined marginal likelihood.
- Examine prior predictions, fit the prespecified model, and repeat with scientifically plausible alternative priors. Similar outputs across a few priors do not prove robustness to model misspecification.
- Sequential analysis needs an explicit stopping/decision rule. A fixed-prior Bayes factor has different optional-stopping properties from a posterior-threshold rule; there is no blanket exemption from calibration or multiplicity concerns.

## Two independent normal groups

This estimates a mean difference under a shared residual SD; it is not Welch's unequal-variance model. Set the prior scales to the measurement units. For unequal variances, model separate SDs and state the resulting model.

```python
import numpy as np
import pymc as pm
import arviz as az

with pm.Model() as group_model:
    mu1 = pm.Normal('mu1', mu=0, sigma=10)
    mu2 = pm.Normal('mu2', mu=0, sigma=10)
    sigma = pm.HalfNormal('sigma', sigma=10)
    pm.Normal('y1', mu=mu1, sigma=sigma, observed=group1)
    pm.Normal('y2', mu=mu2, sigma=sigma, observed=group2)
    pm.Deterministic('diff', mu1 - mu2)
    trace = pm.sample(2000, tune=1000, chains=4, cores=1,
                      random_seed=42, nuts_sampler='pymc')

# Explicit interval probability/type; avoid rounded diagnostics for decisions.
print(az.summary(trace, var_names=['mu1', 'mu2', 'diff'],
                 ci_prob=0.95, ci_kind='eti', round_to='none'))
draws = trace.posterior['diff'].values
print(f"P(mu1 > mu2 | data, model) = {np.mean(draws > 0):.3f}")
az.plot_dist(trace, var_names=['diff'], ci_prob=0.95, ci_kind='eti')
```

A posterior directional probability is not a one-sided Bayes factor. Pingouin 0.7 intentionally omits the `BF10` column for a one-sided `ttest`. Its two-sided default uses the documented JZS prior on standardized effect (Cauchy scale `r=0.707`):

```python
import pingouin as pg
result = pg.ttest(group1, group2, correction=False, r=0.707)
bf10 = float(result['BF10'].iloc[0])  # default output may be a formatted string
```

BF10 is the ratio of the data's marginal likelihoods under H1 and H0. Posterior odds equal BF10 times prior odds. BF10=3 means threefold evidence for H1 relative to H0 under those models; it does not by itself mean H1 is three times as probable. Conventional labels (3–10 moderate, 10–30 strong, 30–100 very strong, >100 extreme) are reporting conventions. State both models, priors and sensitivity. The BF printed beside a Welch statistic is not an unequal-variance Bayesian model comparison.

## Credible intervals and practical equivalence

An equal-tailed 95% interval has 2.5% in each tail. A highest-density region favors high-density values and may be disconnected for multimodal posteriors; a single shortest interval need not contain every mode. Neither interval proves the model is correct.

```python
posterior_samples = trace.posterior['diff']
eti = posterior_samples.quantile([0.025, 0.975], dim=('chain', 'draw'))
hdi = az.hdi(posterior_samples, prob=0.95, dim=['chain', 'draw'])
# Define a negligible raw-unit difference BEFORE looking at the result.
rope_lower, rope_upper = -0.1, 0.1
in_rope = ((posterior_samples >= rope_lower) &
           (posterior_samples <= rope_upper)).mean().item()
print(f"Posterior probability inside the prespecified ROPE: {in_rope:.3f}")
```

The ROPE must match the parameter's units: raw mean difference and standardized d cannot use the same threshold without justification. A posterior-mass decision rule and an HDI-inside-ROPE rule are distinct. Prespecify the rule and assess its consequences rather than presenting 95% as a universal decision threshold.

## Hierarchical group comparisons / Bayesian ANOVA

Use integer `group_idx` aligned with `y`, ranging from 0 to `n_groups-1`. The noncentered parameterization below gives partial pooling of group means. Prior scales remain illustrative; compare pooling assumptions and within-group residual distributions.

```python
with pm.Model() as hierarchical_model:
    mu_global = pm.Normal('mu_global', mu=0, sigma=10)
    sigma_between = pm.HalfNormal('sigma_between', sigma=5)
    sigma_within = pm.HalfNormal('sigma_within', sigma=5)
    z_group = pm.Normal('z_group', mu=0, sigma=1, shape=n_groups)
    group_means = pm.Deterministic('group_means', mu_global + sigma_between * z_group)
    pm.Normal('y_obs', mu=group_means[group_idx], sigma=sigma_within, observed=y)
    group_trace = pm.sample(2000, tune=1000, chains=4, cores=1,
                        

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

