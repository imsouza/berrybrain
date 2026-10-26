---
id: sciref-pydeseq2-analysis-patterns
name: "Scientific Ref: Designs and contrasts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pydeseq2): Designs and contrasts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pydeseq2 analysis patterns"
  - "pydeseq2 analise patterns"
  - "designs and contrasts"
keywords:
  - "pydeseq2"
  - "analysis"
  - "patterns"
  - "analise"
  - "specialized"
  - "scientific"
  - "reference"
  - "pydeseq"
  - "designs"
  - "contrasts"
---

# Designs and contrasts

The snippets below assume a validated samples × genes count table, aligned
metadata, and `DeseqDataSet`, `DeseqStats`, `numpy as np`, and `pandas as pd`
imports. They were exercised on small synthetic metadata/count matrices; choosing
an estimable scientific model still requires the actual study design.

## Additive adjustment and pairing

`~batch + condition` adjusts for a measured batch effect. `~condition + batch`
spans the same additive model; an explicit contrast selects the condition effect
regardless of term order. Perfect batch/condition confounding is unidentifiable.
Dropping batch changes the estimand and does not solve the confounding.

```python
metadata['condition'] = pd.Categorical(metadata['condition'], categories=['control', 'treated'])
metadata['batch'] = metadata['batch'].astype('category')
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design='~batch + condition', n_cpus=1)
X = dds.obsm['design_matrix']
assert np.linalg.matrix_rank(X.to_numpy()) == X.shape[1] < X.shape[0]
dds.deseq2()
ds = DeseqStats(dds, contrast=['condition', 'treated', 'control'], n_cpus=1)
ds.summary()
```

For repeated conditions within a subject, an additive `~subject + condition` can
model the pairing. Each subject must contribute the appropriate conditions; check
rank and residual degrees of freedom. This is a fixed-effect design, not a random
intercept or a general mixed model. Technical lanes from one library are not
independent subjects.

## Continuous variables

Store age/dose as numeric if the intended effect is per numeric unit. Conversely,
integer-coded categories need categorical dtype or `C(variable)`. Centering/scaling
changes the interpretation; record units and the center used.

```python
metadata['age'] = pd.to_numeric(metadata['age'], errors='raise')
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design='~age + condition', n_cpus=1)
dds.deseq2()
# Difference between age 51 and 50 in the control group: effect per one age unit.
v = np.asarray(dds.cond(age=51, condition='control') - dds.cond(age=50, condition='control'))
ds = DeseqStats(dds, contrast=v, n_cpus=1)
ds.summary()
```

For a raw design-matrix DataFrame, align rows to samples and use a finite 1D NumPy
contrast vector with one entry per design column. `cond()` and string factor
contrasts require the formula-based constructor.

## Interactions: simple effects versus differences of effects

Set both factors' reference levels before fitting and retain all observed cells:

```python
metadata['group'] = pd.Categorical(metadata['group'], categories=['A', 'B'])
metadata['condition'] = pd.Categorical(metadata['condition'], categories=['control', 'treated'])
dds = DeseqDataSet(counts=counts_df, metadata=metadata, design='~group * condition', n_cpus=1)
X = dds.obsm['design_matrix']
assert np.linalg.matrix_rank(X.to_numpy()) == X.shape[1] < X.shape[0]
dds.deseq2()
effect_A = dds.cond(group='A', condition='treated') - dds.cond(group='A', condition='control')
effect_B = dds.cond(group='B', condition='treated') - dds.cond(group='B', condition='control')
# Difference in log2 treatment effects: B minus A, not the treatment effect within B.
interaction = np.asarray(effect_B - effect_A)
ds = DeseqStats(dds, contrast=interaction, n_cpus=1)
ds.summary()
```

Use `np.asarray(effect_B)` to test the simple treatment effect in B. A main-effect
coefficient in an interaction model refers to the other factor's reference level,
not a universal or averaged treatment effect. `cond()` fills unspecified factors
with baseline/default values, so specify the context deliberately. Compound
contrasts cannot be shrunk by selecting one of their component coefficients.

## Multiple comparisons and thresholded tests

Reuse a fitted dataset, but create a fresh `DeseqStats` for every comparison and
copy its results before another operation mutates the object:

```python
all_results = {}
for treatment in ['treatment_A', 'treatment_B']:
    stats = DeseqStats(dds_multi, contrast=['condition', treatment, 'control'], alpha=0.05, n_cpus=1)
    stats.summary()
    all_results[treatment] = stats.results_df.copy(deep=True)
```

The above block assumes `dds_multi` was fitted to metadata containing those exact
levels. BH adjustment is performed separately for each contrast. Prespecify the
family if interpreting discoveries jointly across many comparisons.

```python
# A fresh test of |log2FC| > 1, rather than filtering a zero-null test by observed LFC.
threshold_test = DeseqStats(dds, contrast=interaction, lfc_null=1,
                           alt_hypothesis='greaterAbs', n_cpus=1)
threshold_test.summary()
```

This example tests the interaction effect's magnitude because `interaction` is
its contrast; substitute the exact intended contrast for another hypothesis.

Sources: [formulaic contrast construction](https://formulaic-contrasts.readthedocs.io/en/latest/contrasts.html),
[formulaic API](https://formulaic-contrasts.readthedocs.io/en/latest/generated/formulaic_contrasts.FormulaicContrasts.html),
[DESeq2 design guidance](https://bioconductor.org/packages/release/bioc/vignettes/DESeq2/inst/doc/DESeq2.html#model-matrix-not-full-rank).

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

