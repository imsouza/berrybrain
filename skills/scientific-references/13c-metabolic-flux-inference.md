---
id: sciref-13c-metabolic-flux-inference
name: "Scientific Ref: Inference and interpretation"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (13c-metabolic-flux): Inference and interpretation"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "13c metabolic flux inference"
  - "inference and interpretation"
keywords:
  - "13c"
  - "metabolic"
  - "flux"
  - "inference"
  - "specialized"
  - "scientific"
  - "reference"
---

# Inference and interpretation

## What is fitted

The adapter constructs internal carbon-pool balances S v = 0 and exact reference
constraints. Linear programming checks feasibility in normalized flux units and
explicitly verifies the returned vector. A null-space basis parameterizes
the equalities, while linear inequalities preserve every directional flux bound.
Bounds that force a reaction to a single value on a feasible face are promoted to
equalities using a tolerance relative to each reaction's own feasible values. Thus a
flux profile endpoint can correctly have fewer free dimensions. Optimizer constraints
also use normalized units; an unrelated loose bound does not define this tolerance.

mfapy evaluates the steady-state isotope model using elementary metabolite units.
The pinned mfapy generator drops EMU rows with absolute turnover <= 0.001. The
adapter uniformly rescales positive directional fluxes so the smallest is 1 for
forward simulation only. Steady-state isotope distributions are invariant under
this rescaling; reported fluxes and measured-rate residuals retain their original
units. This avoids unit-dependent disappearance of slowly turning-over pools.
Exact zero-throughput pools can still be undefined and are not repaired by rescaling.
The fitting code does not use mfapy's built-in optimizer, confidence intervals, or
natural-abundance correction. It uses SciPy SLSQP with multiple feasible starts,
constructed from convex combinations of linear-programming vertices. This is a local
optimization strategy; no global optimum is guaranteed. Seeds control starting-point
generation, not bit-identical behavior across numerical libraries or machines.

For each normalized distribution, omit one bin and minimize

    RSS = sum_b (prediction_b - mean_b)^T covariance_b^-1 (prediction_b - mean_b)
          + sum_k ((predicted_flux_k - measured_flux_k) / SEM_k)^2

The implementation uses a Cholesky solve rather than explicitly inverting covariance.
With a consistent full compositional covariance, changing the omitted bin leaves this
quadratic form invariant. A diagonal SEM approximation does not have that property.
Covariance validation checks row/column sums relative to each row/column's magnitude
and positive semidefiniteness after variance scaling, so large-variance bins cannot
hide invalid rare-bin uncertainty. MDV normalization error must be negligible relative
to the declared measurement error as well as small in absolute terms.

## Read the JSON results

- `fluxes`: one best converged feasible point, including arbitrary coordinates along
  unresolved directions. Preserve the declared `flux_unit` and exact reference.
- `rss`, `predictions`: weighted residual sum and observed/predicted distributions.
  A low residual can reflect an uninformative experiment or an overflexible model.
- `optimizer_starts`: success, residual, iterations, and termination message for every
  start. Failed numerical evaluations are penalized during optimization; a result is
  accepted only if its final simulation is finite, constraints hold, and the optimizer
  reports convergence. No converged solution makes the command fail with exit code 2.
- `free_flux_dimensions`: affine feasible flux dimension, not parameter count guessed
  from a reaction list. `independent_measurements` counts retained bins and rates.
- `local_sensitivity_rank`: numerical rank of the whitened residual Jacobian in
  normalized feasible coordinates. Finite differences use step 1e-5 and a singular-
  value cutoff max(1e-4, largest singular value * 1e-6). This is a local diagnostic,
  not a proof of structural identifiability. Poor scaling, bounds, near-zero pools,
  and strongly nonlinear behavior can affect it. A null value means feasible
  perturbations could not be evaluated.
- `weak_flux_directions`: relative reaction changes along locally insensitive
  directions, normalized to maximum absolute component 1. These are local directions,
  not permissible finite flux changes without another feasibility check.
- `active_bounds`: estimated reactions at imposed bounds, excluding declared fixed
  reactions. Inspect why the bound is active before making a biological claim.
- `goodness_of_fit`: approximate chi-square tail probability only when local rank is
  full, residual degrees of freedom are positive, and no nonfixed bound is active.
  Known Gaussian covariance, an adequate observation model, interior parameters,
  and asymptotic regularity are assumptions. Estimated SEMs, low counts, inequality
  boundaries, or nonlinearity can invalidate this approximation. A high p-value is not
  evidence that a biological mechanism is true.

## Flux profiles

Every requested reaction is fixed at each grid value across its feasible range;
all nuisance fluxes are refitted. The grid includes the best fitted reaction value.
Acceptance uses RSS(profile) - RSS(best) <= chi-square(confidence, 1). This is an
asymptotic likelihood-ratio approximation for the declared Gaussian observation
model, not a universal MFA confidence formula. Profiles of parameter combinations
or exact finite-sample coverage require a different analysis.

| Status | Meaning and next action |
| --- | --- |
| `threshold_crossings_bracketed` | Grid points bracket threshold crossings. Report the brackets; increase resolution and repeat starts if precise limits matter. Inspect all crossings because disconnected accepted regions are possible. |
| `bound_limited` | At least one feasible-range edge remains accepted. Report that edge as constraint-limited, not measurement-determined. |
| `unresolved_within_bounds` | All sampled points across the feasible range remain accepted. Do not report the arbitrary optimum as an identified pathway rate. This finite grid is not a global structural proof. |
| `incomplete_profile` | At least one point failed. Missing points are unknown. Improve starts, numerical conditioning, or model specification before interpreting limits. |
| `baseline_not_optimal_refit_required` | A profile found a materially smaller RSS. Refit the baseline before using any confidence claim. |
| `fixed_by_constraints` | The reaction is fixed by exact constraints; it has no data-estimated profile interval. |

Even a flat reaction can acquire an apparent bound through coupling to a different
bounded reaction. In the TCA demonstration, increasing `v7` also increases `v6`, and
`v6` has an imposed upper bound. This can create an upper profile edge even though
the isotope measu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

