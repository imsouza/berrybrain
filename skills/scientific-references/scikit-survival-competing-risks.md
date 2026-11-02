---
id: sciref-scikit-survival-competing-risks
name: "Scientific Ref: Competing risks and cumulative incidence"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scikit-survival): Competing risks and cumulative incidence"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scikit survival competing risks"
  - "competing risks and cumulative incidence"
keywords:
  - "scikit"
  - "survival"
  - "competing"
  - "risks"
  - "specialized"
  - "scientific"
  - "reference"
---

# Competing risks and cumulative incidence

Verified for scikit-survival 0.28.0 on 2026-10-01.

## Estimand

Competing risks are mutually exclusive causes \(J \in \{1,\ldots,K\}\), where the
first observed cause prevents observing the others as first events.

The cause-\(k\) cumulative incidence function (CIF) is:

\[
F_k(t) = P(T \le t, J=k).
\]

It is an absolute cause-specific event probability accounting for all competing
causes. It is not:

- a cause-specific hazard;
- `1 - Kaplan-Meier` after censoring other causes;
- a conditional probability among only those still event-free;
- a causal effect or clinical-utility measure.

The total risk is \(\sum_k F_k(t)\). Its complement is estimated all-cause
event-free survival. Censoring is an observation mechanism, not an additional
event-free state.

## Event coding

The nonparametric CIF API takes two separate arrays:

```python
# event: 0=censored; 1..K=mutually exclusive causes
event = frame["status"].to_numpy(dtype=int)
time = frame["time"].to_numpy(dtype=float)
```

Requirements:

- `event` is integer and non-negative;
- 0 always denotes right-censoring;
- positive codes 1..K are contiguous;
- the data contains observations for every code 1..K;
- `time` is finite and positive;
- event/time lengths match.

Do not pass a boolean `Surv` outcome to
`cumulative_incidence_competing_risks()`. `Surv` intentionally collapses event
status to event versus censoring and loses cause identity.

## Nonparametric CIF API

```python
from sksurv.nonparametric import cumulative_incidence_competing_risks

time_points, cumulative_incidence = (
    cumulative_incidence_competing_risks(event, time)
)
```

Current signature:

```text
cumulative_incidence_competing_risks(
    event,
    time_exit,
    time_min=None,
    conf_level=0.95,
    conf_type=None,
    var_type="Aalen",
)
```

Returns:

- `time_points`: shape `(n_times,)`;
- `cumulative_incidence`: shape `(K + 1, n_times)`;
- row 0: total risk of any cause;
- row `k`: CIF for cause `k`.

```python
total_risk = cumulative_incidence[0]
cause_1 = cumulative_incidence[1]
cause_2 = cumulative_incidence[2]

assert np.allclose(
    total_risk,
    cumulative_incidence[1:].sum(axis=0),
)
```

`time_min` is documented as conditional survival. In released 0.28.0 it fails
with a broadcasting error when it removes any unique times; the bundled helper
rejects that setting. Do not claim a conditional/landmark analysis from this
helper. A different verified method and explicit target population are needed.

### Confidence intervals

```python
time_points, cumulative_incidence, confidence_interval = (
    cumulative_incidence_competing_risks(
        event,
        time,
        conf_type="log-log",
        conf_level=0.95,
        var_type="Aalen",
    )
)
```

`confidence_interval` has shape `(K + 1, 2, n_times)`. Native 0.28.0 returns
cause-specific rows in lower/upper order, but **total-risk row 0 is reversed and
ignores `conf_level`**. Repair that row with the public all-event KM estimator:

```python
from sksurv.nonparametric import kaplan_meier_estimator

km_time, _, km_ci = kaplan_meier_estimator(
    event > 0, time, conf_type="log-log", conf_level=0.95,
)
assert np.array_equal(km_time, time_points)
confidence_interval[0] = 1.0 - km_ci[::-1]
assert np.all(confidence_interval[:, 0] <= confidence_interval[:, 1])
```

The bundled helper applies this repair using the requested level and rejects
non-finite or reversed intervals. This repairs the total-risk row, not general
small-sample coverage.
Current variance choices are:

- `"Aalen"`
- `"Dinse"`
- `"Dinse_Approx"`

Pointwise confidence intervals are not simultaneous confidence bands. Sparse
causes and late follow-up can make estimates unstable even when the function
returns a result.

## Built-in competing-risk datasets

```python
from sksurv.datasets import load_bmt, load_cgvhd

X_bmt, y_bmt = load_bmt()       # status codes 0, 1, 2
X_cgvhd, y_cgvhd = load_cgvhd() # status codes 0, 1, 2, 3
```

The first structured field is integer cause status, not boolean. These are real
study datasets distributed for examples. The bundled tests do not use them; they
use synthetic non-clinical outcomes only.

## Why `1 - Kaplan-Meier` is wrong for one cause

If cause 2 prevents cause 1, censoring cause 2 in a Kaplan-Meier curve treats those
subjects as if they could still experience cause 1 later under non-informative
censoring. That counterfactual risk set does not estimate the observed-world
probability \(F_1(t)\) and typically overstates cause-1 probability.

Use CIF for cause-specific absolute probability:

```python
time_points, cif = cumulative_incidence_competing_risks(event, time)
probability_cause_1_by_t = cif[1]
```

Kaplan-Meier remains appropriate for all-cause event-free survival after collapsing
all causes to event, if that is the estimand and censoring assumptions hold.

## Comparing groups

For prespecified groups where every original cause occurs (the native function
requires contiguous observed causes), estimate point curves:

```python
curves = {}
for label in prespecified_groups:
    mask = group == label
    curves[label] = cumulative_incidence_competing_risks(
        event[mask],
        time[mask],
    )
```

If a subgroup has no event for a cause, do not silently relabel its rows or invent
an event to satisfy the API. Preserve a global cause mapping and use a method
that supports absent causes; an all-censored group needs separate handling.

Plotting pointwise intervals does not test equality. scikit-survival 0.28 does not
provide Gray's test in this API. Do not substitute an ordinary log-rank test:
survival and CIF group hypotheses differ.

Group labels and comparison times should be prespecified. Report at-risk/event
support; late visual separation with few rows can be misleading.

## Cause-specific Cox hazards

For cause \(k\), a cause-specific hazard model encodes that cause as an event and
other causes as censored at their occurrence time:

```python
from sksurv.linear_model import CoxPHSurvivalAnalysis
from sksurv.util import Surv

y_cause_1 = Surv.from_arrays(
    event=(event == 1),
    time=time,
)
cause_1_hazard_model = CoxPHSurvivalAnalysis(alpha=0.1)
cause_1_hazard_model.fit(X_train, y_cause_1_train)
```

This estimates association with the instantaneous cause-specific hazard under a
PH model. Other causes are censored for this hazard likelihood, which is different
from pretending they are independent censoring when estimatin

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

