---
id: sciref-pymc-distributions
name: "Scientific Ref: PyMC Distributions Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pymc): PyMC Distributions Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pymc distributions"
  - "pymc distributions reference"
keywords:
  - "pymc"
  - "distributions"
  - "specialized"
  - "scientific"
  - "reference"
---

# PyMC Distributions Reference

Targets PyMC 6.3.2, reviewed 2026-10-01. This reference provides a selected catalog of probability distributions available in PyMC, organized by category. Use this to select appropriate distributions for priors and likelihoods when building Bayesian models.

## Continuous Distributions

Continuous distributions define probability densities over real-valued domains.

### Common Continuous Distributions

**`pm.Normal(name, mu, sigma)`**
- Normal (Gaussian) distribution
- Parameters: `mu` (mean), `sigma` (standard deviation)
- Support: (-∞, ∞)
- Common uses: Default prior for unbounded parameters, likelihood for continuous data with additive noise

**`pm.HalfNormal(name, sigma)`**
- Half-normal distribution (positive half of normal)
- Parameters: `sigma` (underlying Normal scale; not the half-normal standard deviation)
- Support: [0, ∞)
- Common uses: Prior for scale/standard deviation parameters

**`pm.Uniform(name, lower, upper)`**
- Uniform distribution
- Parameters: `lower`, `upper` (bounds)
- Support: [lower, upper]
- Common uses: Weakly informative prior when parameter must be bounded

**`pm.Beta(name, alpha, beta)`**
- Beta distribution
- Parameters: `alpha`, `beta` (shape parameters)
- Support: [0, 1]
- Common uses: Prior for probabilities and proportions

**`pm.Gamma(name, alpha, beta)`**
- Gamma distribution
- Parameters: `alpha` (shape), `beta` (rate)
- Support: (0, ∞)
- Common uses: Prior for positive parameters, rate parameters

**`pm.Exponential(name, lam)`**
- Exponential distribution
- Parameters: `lam` (rate parameter)
- Support: [0, ∞)
- Common uses: Prior for scale parameters, waiting times

**`pm.LogNormal(name, mu, sigma)`**
- Log-normal distribution
- Parameters: `mu`, `sigma` (parameters of underlying normal)
- Support: (0, ∞)
- Common uses: Prior for positive parameters with multiplicative effects

**`pm.StudentT(name, nu=nu, mu=mu, sigma=sigma)`**
- Student's t-distribution
- Parameters: `nu` (degrees of freedom), `mu` (location), `sigma` (scale)
- Support: (-∞, ∞)
- Common uses: Robust alternative to normal for outlier-resistant models

**`pm.Cauchy(name, alpha, beta)`**
- Cauchy distribution
- Parameters: `alpha` (location), `beta` (scale)
- Support: (-∞, ∞)
- Common uses: Heavy-tailed alternative to normal

**`pm.HalfStudentT(name, nu, sigma)`**
- Positive half-Student-t distribution
- Common uses: Heavy-tailed prior for scale parameters

### Specialized Continuous Distributions

**`pm.Laplace(name, mu, b)`** - Laplace (double exponential) distribution

**`pm.AsymmetricLaplace(name, kappa, mu, b)`** - Asymmetric Laplace distribution

**`pm.InverseGamma(name, alpha, beta)`** - Inverse gamma distribution

**`pm.Weibull(name, alpha, beta)`** - Weibull distribution for reliability analysis

**`pm.Logistic(name, mu, s)`** - Logistic distribution

**`pm.LogitNormal(name, mu, sigma)`** - Logit-normal distribution for (0,1) support

**`pm.Pareto(name, alpha, m)`** - Pareto distribution for power-law phenomena

**`pm.ChiSquared(name, nu)`** - Chi-squared distribution

**`pm.ExGaussian(name, mu=mu, sigma=sigma, nu=nu)`** - Exponentially modified Gaussian

**`pm.VonMises(name, mu, kappa)`** - Von Mises (circular normal) distribution

**`pm.SkewNormal(name, mu=mu, sigma=sigma, alpha=alpha)`** - Skew-normal distribution

**`pm.Triangular(name, lower=lower, c=c, upper=upper)`** - Triangular distribution

**`pm.Gumbel(name, mu, beta)`** - Gumbel distribution for extreme values

**`pm.PolyaGamma(name, h, z)`** - Polya-gamma distribution for data augmentation patterns

**`pm.Rice(name, nu, sigma)`** - Rice (Rician) distribution

**`pm.Moyal(name, mu, sigma)`** - Moyal distribution

**`pm.Kumaraswamy(name, a, b)`** - Kumaraswamy distribution (Beta alternative)

**`pm.Wald(name, mu, lam)`** - Wald / inverse Gaussian distribution

**`pm.Interpolated(name, x_points, pdf_points)`** - Custom distribution from interpolation

## Discrete Distributions

Discrete distributions define probabilities over integer-valued domains.

### Common Discrete Distributions

**`pm.Bernoulli(name, p)`**
- Bernoulli distribution (binary outcome)
- Parameters: `p` (success probability)
- Support: {0, 1}
- Common uses: Binary classification, coin flips

**`pm.Binomial(name, n, p)`**
- Binomial distribution
- Parameters: `n` (number of trials), `p` (success probability)
- Support: {0, 1, ..., n}
- Common uses: Number of successes in fixed trials

**`pm.Poisson(name, mu)`**
- Poisson distribution
- Parameters: `mu` (rate parameter)
- Support: {0, 1, 2, ...}
- Common uses: Count data, rates, occurrences

**`pm.Categorical(name, p)`**
- Categorical distribution
- Parameters: `p` (probability vector)
- Support: {0, 1, ..., K-1}
- Common uses: Multi-class classification

**`pm.DiscreteUniform(name, lower, upper)`**
- Discrete uniform distribution
- Parameters: `lower`, `upper` (bounds)
- Support: {lower, ..., upper}
- Common uses: Uniform prior over finite integers

**`pm.NegativeBinomial(name, mu, alpha)`**
- Negative binomial distribution
- Parameters: `mu` (mean), `alpha` (dispersion)
- Support: {0, 1, 2, ...}
- Common uses: Overdispersed count data

**`pm.Geometric(name, p)`**
- Geometric distribution
- Parameters: `p` (success probability)
- Support: {1, 2, 3, ...}
- Common uses: Trial count through the first success (includes that success)

### Specialized Discrete Distributions

**`pm.BetaBinomial(name, alpha, beta, n)`** - Beta-binomial (overdispersed binomial)

**`pm.HyperGeometric(name, N, k, n)`** - Hypergeometric distribution

**`pm.DiscreteWeibull(name, q, beta)`** - Discrete Weibull distribution

**`pm.OrderedLogistic(name, eta, cutpoints)`** - Ordered logistic for ordinal data

**`pm.OrderedProbit(name, eta, cutpoints)`** - Ordered probit for ordinal data

## Multivariate Distributions

Multivariate distributions define joint probability distributions over vector-valued random variables.

### Common Multivariate Distributions

**`pm.MvNormal(name, mu, cov)`**
- Multivariate normal distribution
- Parameters: `mu` (mean vector), `cov` (covariance matrix)
- Common uses: Correlated continuous variables, Gaussian processes

**`pm.Dirichlet(name, a)`**
- Dirichlet distribution
- Parameters: `a` (concentration parameters)
- Support: Simplex (sums to 1)
- Common uses: Prior for probability vectors, topic modeling

**`pm.Multinomial(name, n, p)`**
- Multinomial distribution
- Parameters: `n` (number of trials), `p` (probability vector)
- Common uses: Count data acro

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

