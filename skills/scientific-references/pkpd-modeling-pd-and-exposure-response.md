---
id: sciref-pkpd-modeling-pd-and-exposure-response
name: "Scientific Ref: PD and exposure-response workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pkpd-modeling): PD and exposure-response workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pkpd modeling exposure response"
  - "pd and exposure-response workflow"
keywords:
  - "pkpd"
  - "modeling"
  - "exposure"
  - "response"
  - "specialized"
  - "scientific"
  - "reference"
---

# PD and exposure-response workflow

## Choose a structure the observations can distinguish

| Structure | Equation/role | Main identification concern |
| --- | --- | --- |
| Direct Emax | `E0 + Emax*C/(EC50+C)` | Without a plateau, Emax and EC50 trade off |
| Sigmoid Emax | `E0 + Emax*C^h/(EC50^h+C^h)` | Hill, EC50 and Emax need concentration-range support |
| Effect compartment | `dCe/dt=ke0*(C-Ce)` | Delay can also arise from sampling, metabolites or turnover |
| Indirect response | Production/loss modulated by drug | Baseline turnover and drug effect can be confounded |
| Logistic | `logit(p)=a+b*exposure` | Separation, confounding and repeated observations |

Effect-compartment Ce is a link variable, not an additional drug mass. Indirect response models I–IV
inhibit/stimulate production or loss. An inhibitory fraction must stay between zero and one;
stimulation terms must not make rates negative. Estimate/fix turnover with independent evidence
where possible. Similar hysteresis loops do not uniquely select one mechanism.

The ODE and regression helpers check finite inputs and solver/optimizer outcomes, but local
standard errors are not evidence of structural identifiability. A converged fit with a deficient
Jacobian must not imply precise parameters. Check profiles, bounds, starting-value sensitivity and
predictions under perturbation, especially when the sampled range never reaches a plateau.

## Exposure-response is not automatically causal

Randomized dose does not randomize realized exposure. Clearance can covary with disease severity,
body size, adherence and prognosis. Derived exposure carries estimation error; time-varying
clearance and survival-dependent sampling can induce bias. Define the estimand, temporal ordering,
confounders, missingness and sensitivity analyses before interpreting a slope as a dose benefit.
Balance efficacy and safety outcomes rather than maximizing a single modeled response.
[FDA exposure-response guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/exposure-response-relationships-study-design-data-analysis-and-regulatory-applications).

`exposure_response.py` uses independent observations. Repeated longitudinal responses, count or
time-to-event endpoints need models with appropriate distributions and dependence. Logistic data
must contain both outcomes and exposure variation; complete/quasi-complete separation is rejected
rather than returning a misleading finite estimate. C-QTc limitations are in [DDI/QT](ddi-and-qt.md).

## Pharmpy model construction

These transformations were executed independently on the bundled example model under Pharmpy 2.2.0.
They return new models; they do not estimate parameters or establish adequacy:

```python
import pharmpy.modeling as m
base = m.load_example_model("pheno")
direct = m.set_direct_effect(base, expr="sigmoid")
link = m.add_effect_compartment(base, expr="emax")
turnover = m.add_indirect_effect(base, expr="emax", prod=True)
```

`prod=True` targets production; `False` targets elimination. Inspect the resulting symbolic model,
observation mapping, parameter signs and baseline conditions before fitting it to actual data.
[Pharmpy modeling API](https://pharmpy.github.io/latest/api/pharmpy.modeling.add_indirect_effect.html).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

