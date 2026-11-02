---
id: sciref-shap-plots
name: "Scientific Ref: SHAP Plotting"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): SHAP Plotting"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap plots"
  - "shap plotting"
keywords:
  - "shap"
  - "plots"
  - "specialized"
  - "scientific"
  - "reference"
  - "plotting"
---

# SHAP Plotting

This reference uses the SHAP 0.52 plotting API. Prefer `shap.plots.*` functions that consume `shap.Explanation` objects. Legacy functions such as `summary_plot`, `dependence_plot`, and top-level `force_plot` remain relevant to old code but lose metadata and should not anchor a new workflow.

## Validate Before Plotting

For every plot:

```python
print("values:", explanation.values.shape)
print("base_values:", np.shape(explanation.base_values))
print("data:", np.shape(explanation.data))
print("features:", explanation.feature_names)
print("outputs:", explanation.output_names)
```

For multi-output tabular data, select one output:

```python
class_exp = explanation[..., class_index]
# or, when output names are populated:
class_exp = explanation[..., list(explanation.output_names).index("class_name")]
```

Verify output names against the model first; 0.52.0 can discard names in permutation dispatch. Use integer output selection to avoid the ellipsis/string slicing bug.

Most tabular plots expect either:

- one local row: `(features,)`; or
- many rows: `(samples, features)`.

Passing `(samples, features, outputs)` without selecting an output is a common source of misleading or failed plots.

## Plot Selection

| Question | Plot | Input |
|---|---|---|
| Which features have the greatest average absolute attribution? | `bar` | multi-row `Explanation` |
| What are the direction, spread, and observed values of attributions? | `beeswarm` | multi-row `Explanation` |
| How does one row move from baseline to output? | `waterfall` | one-row `Explanation` |
| How does attribution vary with a feature value? | `scatter` | one feature column |
| Are there sample-level explanation patterns? | `heatmap` | multi-row `Explanation` |
| How do cohorts compare descriptively? | `bar` | `Cohorts` or dictionary |
| Which tokens or regions contribute? | `text`, `image` | modality-specific `Explanation` |
| Is an interactive additive layout useful? | `force` | one or multiple rows |
| How do cumulative paths differ? | `decision` | arrays plus base value |

No plot proves causality or fairness. A plot is an aggregation of attributions under a model, output, background, and masker.

## Global Bar Plot

```python
ax = shap.plots.bar(
    explanation,
    max_display=20,
    show=False,
)
ax.set_title("Mean absolute SHAP value")
ax.figure.tight_layout()
ax.figure.savefig("shap-bar.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

A multi-row explanation is aggregated by mean absolute attribution. A single row creates a local bar plot.

### Cohort bar plot

```python
cohorts = explanation.cohorts(group_labels)
ax = shap.plots.bar(cohorts.abs.mean(0), max_display=15, show=False)
ax.figure.savefig("shap-cohorts.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

Alternatively:

```python
ax = shap.plots.bar(
    {
        "Group A": explanation[group_labels == "A"],
        "Group B": explanation[group_labels == "B"],
    },
    show=False,
)
```

Use one shared explainer and background for direct cohort comparison. Include sample counts and uncertainty; different mean magnitudes can reflect feature distributions, performance, or model behavior.

### Feature clustering

```python
clustering = shap.utils.hclust(X_background, y_background)
ax = shap.plots.bar(
    explanation,
    clustering=clustering,
    clustering_cutoff=0.5,
    show=False,
)
```

`hclust(X, y)` defaults to an XGBoost-based outcome-redundancy metric and requires the optional `xgboost` package. This fragment is illustrative unless that integration is installed and exercised. For unsupervised feature clustering, use an explicit distance such as `shap.utils.hclust(X_background, metric="correlation")`; constant columns require care. Outcome-aware clustering can be expensive. Do not compute it using held-out labels if that would contaminate the analysis.

## Beeswarm Plot

```python
ax = shap.plots.beeswarm(
    explanation,
    max_display=20,
    alpha=0.7,
    s=12,
    group_remaining_features=True,
    show=False,
)
ax.figure.savefig("shap-beeswarm.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

Current 0.52 controls include:

- `order`: default `explanation.abs.mean(0)`;
- `clustering` and `cluster_threshold`;
- `ax` (set `plot_size=None` when supplying an existing axis);
- `log_scale`;
- `color_bar`;
- `s` for marker size;
- `plot_size`;
- `group_remaining_features`.

Interpretation:

- horizontal position: signed attribution in the explained output's units;
- color: observed feature value when numeric display data are available;
- vertical density/jitter: observations, not uncertainty;
- row order: an aggregation rule, not causal importance.

Useful alternatives:

```python
# Highlight features with rare large effects.
shap.plots.beeswarm(
    explanation,
    order=explanation.abs.max(0),
)

# Absolute magnitude only; direction is intentionally removed.
shap.plots.beeswarm(
    explanation.abs,
    color="shap_red",
)
```

Do not interpret red as "risk" or blue as "protective" without first defining output and units.

## Waterfall Plot

```python
ax = shap.plots.waterfall(
    explanation[row_index],
    max_display=15,
    show=False,
)
ax.figure.savefig("shap-waterfall.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

Input must be one-dimensional. A waterfall shows how values move from the selected background's base value to the selected output for one row.

Report:

- why the row was selected;
- baseline population and value;
- output name and units;
- final model output;
- whether omitted features were grouped.

Never describe the arrows as what would happen if a person changed a feature. They decompose a predictive output; they are not recourse or intervention estimates.

## Scatter Plot

```python
ax = shap.plots.scatter(
    explanation[:, "age"],
    color=explanation[:, "bmi"],
    alpha=0.5,
    x_jitter="auto",
    show=False,
)
ax.figure.savefig("shap-age-scatter.png", dpi=200, bbox_inches="tight")
plt.close(ax.figure)
```

If `color=explanation` is passed, SHAP selects a likely interaction color automatically:

```python
shap.plots.scatter(explanation[:, "age"], color=explanation)
```

Vertical spread at one x-value can arise from:

- interactions;
- correlated features;
- heterogeneous subgroups;
- approximation noise;
- model discontinuities.

It does not by itself prove an interaction or causal effect.

Current scatter features include categorical support, au

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

