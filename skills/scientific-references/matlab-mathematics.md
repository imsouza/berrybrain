---
id: sciref-matlab-mathematics
name: "Scientific Ref: Numerical Methods, Tolerances, and Reproducibility"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): Numerical Methods, Tolerances, and Reproducibility"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab mathematics"
  - "numerical methods, tolerances, and reproducibility"
keywords:
  - "matlab"
  - "mathematics"
  - "specialized"
  - "scientific"
  - "reference"
  - "numerical"
  - "methods"
---

# Numerical Methods, Tolerances, and Reproducibility

This reference targets MATLAB R2026a. Confirm every non-base product before
using toolbox-specific functions.

## Linear systems and decompositions

Solve systems; do not form an inverse as an intermediate:

```matlab
x = A \ b;
residual = A*x - b;
relativeResidual = norm(residual) / ...
    max(norm(A)*norm(x) + norm(b), realmin(class(A)));
```

Check dimensions, rank/conditioning, scaling, symmetry, definiteness, and
sparsity. A small residual does not guarantee a small forward error for an
ill-conditioned problem.

Common base MATLAB operations include:

- `lu`, `qr`, `chol`, `ldl`, `schur`;
- `eig`, `svd`, `eigs`, `svds`;
- `rank`, `cond`, `rcond`, `norm`, `pinv`;
- `lsqminnorm`, `lsqnonneg`, and backslash least squares.

Use an economy decomposition where appropriate and request only the spectrum
needed for large/sparse problems. Eigenvector signs/phases and bases in
degenerate subspaces are not unique; compare invariant quantities rather than
raw vectors.

## Floating-point comparison

Binary floating point does not represent most decimal fractions exactly.
Choose tolerances from the model, scale, conditioning, discretization,
measurement uncertainty, and algorithm—not from a universal constant.

A robust scalar/elementwise policy often has the form:

```matlab
errorMagnitude = abs(actual - expected);
limit = absoluteTolerance + relativeTolerance .* abs(expected);
isAcceptable = errorMagnitude <= limit;
```

Handle these explicitly:

- expected values near zero need an absolute tolerance;
- large expected values often need a relative tolerance;
- `NaN` equality is a semantic decision (`isequaln` differs from `==`);
- `Inf` signs should match when infinity is expected;
- class, size, sparsity, and complex values are part of the contract.

R2026a documents `isapprox` alongside equality operations. In
`matlab.unittest`, use `AbsTol`/`RelTol` or
`AbsoluteTolerance`/`RelativeTolerance`. Record why values are scientifically
acceptable.

Do not widen tolerances automatically after an upgrade. First investigate RNG,
ordering, reduction order, solver defaults/options, data type, threading,
compiler, library, and release-note changes.

## Random streams

Record algorithm and seed, not only a seed:

```matlab
rng(1729, "twister");
stateAtStart = rng;
samples = randn(1000, 1);
```

For local independent streams:

```matlab
stream = RandStream("Threefry", Seed=1729);
stream.Substream = 4;
samples = randn(stream, 1000, 1);
```

Generator availability and bitwise sequences can vary by algorithm/release.
Avoid `rng("shuffle")` for reproducible work. On parallel workers, time-based
seeding can collide; use supported independent streams/substreams and record
worker mapping. Parallel computing requires Parallel Computing Toolbox.

## Integration, roots, and differential equations

Base MATLAB provides general numerical methods including:

- `integral`, `integral2`, `integral3`, `trapz`, `cumtrapz`;
- `gradient`, `diff`;
- `fzero`;
- ODE solvers such as `ode45`, `ode23`, `ode113`, `ode15s`, `ode23s`,
  `ode23t`, and `ode23tb`;
- boundary-value solvers such as `bvp4c` and `bvp5c`.

Define tolerances and failure criteria:

```matlab
options = odeset( ...
    RelTol=1e-7, ...
    AbsTol=1e-10, ...
    MaxStep=0.05);
[t, y] = ode45(@rhs, [0 5], 1, options);
```

Solver tolerances control local error estimates, not proof of a globally
correct model. Check conservation laws, event localization, stiffness,
step-size convergence, and an independent formulation. R2026a adds an
automatic-differentiation Jacobian option for the `ode` object; verify the
specific solver/problem and release notes before using it.
R2026b extends `ode` automatic Jacobians to complex equations and adds the
`Waypoints` property for time values the solver must reach exactly. These are
release-specific `ode` object features, not `ode45` options.

## Optimization and fitting boundaries

Base MATLAB includes `fminsearch` and `fminbnd`. These do not replace
constrained or specialized solvers.

Examples of separately licensed boundaries:

| Capability | Representative API | Product to confirm |
|---|---|---|
| constrained/nonlinear optimization | `fmincon`, `fminunc`, `lsqnonlin`, `lsqcurvefit` | Optimization Toolbox |
| global/metaheuristic optimization | `ga`, `particleswarm`, `surrogateopt` | Global Optimization Toolbox |
| curve fitting objects/apps | `fit`, Curve Fitter | Curve Fitting Toolbox |
| statistical modeling/distributions | `fitlm`, `fitdist`, `anova`, many tests | Statistics and Machine Learning Toolbox |
| symbolic algebra | `syms`, `solve`, symbolic differentiation | Symbolic Math Toolbox |
| signal design/analysis | `fir1`, `filtfilt`, `designfilt`, `spectrogram` | Signal Processing Toolbox |
| parallel loops/GPU | `parfor`, `parpool`, `gpuArray` | Parallel Computing Toolbox |

Some base functions have similarly named toolbox alternatives. Check the
function's current product page and the project dependency report; never infer
ownership from a code example.

Optimization reproducibility requires objective/constraint definitions,
starting points, bounds, solver/options, stopping tolerances, gradients,
scaling, RNG state for stochastic methods, and exit diagnostics. Compare
feasibility and optimality measures, not only the objective value.

## Statistics and signal processing

Base array summaries include `mean`, `median`, `std`, `var`, `min`, `max`,
`movmean`, `movmedian`, `cov`, `corrcoef`, `histcounts`, and polynomial
`polyfit`/`polyval`. Some distribution, model, hypothesis-test, robust,
classification, and specialized plotting APIs require Statistics and Machine
Learning Toolbox.

For FFT work:

```matlab
n = numel(x);
Y = fft(x);
frequency = (0:n-1).' * (sampleRate/n);
```

Document sample rate, units, window, detrending, normalization, one- versus
two-sided spectrum, zero padding, and endpoint convention. `fft` and `conv` are
base MATLAB; many filter-design and spectral-estimation functions are Signal
Processing Toolbox.

## Verification patterns

Use several layers:

1. **Dimensional/invariant checks**: sizes, units, conservation, monotonicity,
   positivity, symmetry.
2. **Analytic cases**: small problems with known solutions.
3. **Refinement studies**: mesh, step, quadrature, or tolerance convergence.
4. **Independent implementation**: alternative solver or formulation.
5. **Condition/sensitivity analysis**: perturb inputs and options.
6. **Release com

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

