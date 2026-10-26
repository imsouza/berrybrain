---
id: sciref-pymc-sampling-inference
name: "Scientific Ref: PyMC Sampling and Inference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymc): PyMC Sampling and Inference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymc sampling inference"
  - "pymc sampling and inference"
keywords:
  - "pymc"
  - "sampling"
  - "inference"
  - "specialized"
  - "scientific"
  - "reference"
---

# PyMC Sampling and Inference

Targets PyMC 6.3.2 / PyTensor 3.3.2 / ArviZ 1.3.0, reviewed 2026-10-01.
Fragments requiring `model` or data variables below are illustrative patterns;
NUTS, ADVI, predictive sampling and the complete workflow have bounded native
smoke tests. Alternative samplers are source-checked, not runtime-validated here.

## Sampling contract

```python
with model:
    idata = pm.sample(draws=1000, tune=1000, chains=4, cores=4,
                      nuts_sampler="pymc", random_seed=42,
                      nuts={"target_accept": .9})
    pm.compute_log_likelihood(idata)
```

- `draws` counts retained samples **per chain**; warmup is additional and discarded
  by default. Choose counts from diagnostics and the estimand's precision target.
- Omitted `cores` is capped at four CPUs; omitted `chains` is at least two and
  otherwise based on cores. Set both explicitly to bound resources.
- `nuts_sampler=None` can select installed nutpie; `"pymc"` forces the native
  implementation. Alternatives are `"nutpie"`, `"numpyro"`, `"blackjax"`; optional
  implementations need compatible dependencies and entirely continuous models.
- `backend` chooses graph execution (`"numba"`, `"c"`, `"jax"`) and is distinct
  from the sampler. Not every model op supports every backend.
- Use `nuts={...}` for sampler-specific settings; `nuts_sampler_kwargs` is
  deprecated. PyMC NUTS tree-depth options are not portable assumptions for
  other implementations.
- `init="auto"` currently chooses `jitter+adapt_diag` for PyMC NUTS. Initialization
  settings do not carry over identically to every alternative sampler.
- A seed supports replay in a fixed environment; it is not cross-version/backend
  bitwise reproducibility. Retain resolved package versions and numerical backend.
- `return_inferencedata=True` returns an xarray `DataTree` in PyMC 6. Some API
  prose still says InferenceData; the released annotations and runtime establish
  the DataTree behavior. `False` requests the legacy MultiTrace route.

## Geometry and diagnostics

Use rank-normalized R-hat near 1 (flag values above 1.01), bulk/tail ESS, and
MCSE for the quantity being reported. ESS in `az.summary` is pooled over chains;
400 is only a screening floor, not assurance that a rare-event probability is
accurate. Multiple modes may remain undiscovered even when chains agree.

Inspect divergences at their parameter locations, posterior correlations, scale
priors and parameterization. Higher `target_accept` can reduce integration error
but cannot identify an unidentifiable model. A lack of divergence flags does not
prove exploration. Energy **overlap**, not separation, is the useful visual
comparison; `az.bfmi` below about 0.3 merits investigation. Check the actual
configured tree-depth limit or recorded `reached_max_treedepth`, not the maximum
observed tree depth.

For weakly informed hierarchical effects, non-centering often helps:

```python
with pm.Model(coords={"group": group_names}) as model:
    population_mean = pm.Normal("population_mean", 0, sigma=2)
    group_scale = pm.HalfNormal("group_scale", sigma=1)
    offset = pm.Normal("offset", 0, sigma=1, dims="group")
    theta = pm.Deterministic("theta", population_mean + group_scale * offset,
                             dims="group")
    pm.Normal("y", theta[group_idx], sigma=1, observed=y)
```

For strongly informed effects, a centered form may be more efficient. Do not
"non-center" an observed likelihood by placing parameter-dependent transformed
data in `observed`; that changes the density and drops the necessary Jacobian.
Non-center latent effects while preserving the observation model.

QR can reduce predictor correlation but changes priors unless transformed
consistently. Use `pytensor.tensor.linalg.solve(R, beta_tilde)` for a symbolic
solve, check full column rank, and record the implied original-coefficient prior.
An independent Normal prior on QR coefficients is not automatically the original
independent Normal prior on regression coefficients.

## Discrete and non-gradient inference

For mixed models PyMC can assign compound samplers; explicitly assigning a
step method is also supported:

```python
with model:
    idata = pm.sample(step=[pm.NUTS(vars=[continuous_parameter]),
                            pm.Metropolis(vars=[discrete_parameter])],
                      draws=1000, tune=1000, chains=4, random_seed=42)
```

Marginalize discrete latent variables when feasible. Binary/categorical Gibbs
methods may be more appropriate than generic Metropolis. Slice sampling handles
some univariate non-gradient targets and adapts its width during tuning; it is
not a no-tuning algorithm. HMC-only diagnostics may be absent for these methods.

`pm.sample_smc` supports Sequential Monte Carlo and can explore difficult modes;
its marginal likelihood requires proper, normalized priors and repeated runs to
assess Monte Carlo stability. It is not automatically a reliable evidence estimate.

## Variational inference

```python
with model:
    approx = pm.fit(n=10000, method="advi", random_seed=42,
                    progressbar=False)
    variational_draws = approx.sample(draws=1000, random_seed=43)
```

`pm.fit` supports `advi`, `fullrank_advi`, `svgd` and `asvgd`. Mean-field ADVI can
miss dependence and underestimate uncertainty. Full-rank approximations capture
Gaussian correlations but need not recover modes or tails. SVGD also has no
guarantee of recovering multimodality. Inspect the optimization history, restart
with multiple seeds and compare important marginals/contrasts with MCMC where
possible. Ordinary chain R-hat and ESS on independently generated VI draws
measure draws from the approximation, not its accuracy relative to the posterior.

For optional PyMC NUTS ADVI initialization use the documented `init="advi+adapt_diag"`
path. Do not casually use `approx.sample(...)[0]`: a `MultiTrace` returns point
objects under a different contract than DataTree, and transformed/free-variable
names and independent initializations matter. Starting from ADVI is not required.

Minibatch VI must pair predictors/outcomes in a shared batch and provide the
correct full-data `total_size` on the likelihood. It changes optimization noise,
not the scientific sampling design; biased batches or group leakage remain biased.

## Forward sampling

`pm.sample_prior_predictive(draws=...)` samples the generative model before fitting.
`pm.sample_posterior_predictive(idata, predictions=False)` creates re

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

