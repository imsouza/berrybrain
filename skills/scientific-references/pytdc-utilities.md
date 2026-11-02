---
id: sciref-pytdc-utilities
name: "Scientific Ref: Splits, evaluators, and benchmark groups"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (pytdc): Splits, evaluators, and benchmark groups"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "pytdc utilities"
  - "splits, evaluators, and benchmark groups"
keywords:
  - "pytdc"
  - "utilities"
  - "specialized"
  - "scientific"
  - "reference"
  - "splits"
  - "evaluators"
---

# Splits, evaluators, and benchmark groups

This reference describes behavior verified in the **PyTDC 1.1.15** source
distribution on 2026-10-01. The official website documents user-facing intent;
source inspection resolves exact method spellings and edge cases.

## Split API overview

Ordinary loaders return:

```python
{
    "train": train_frame,
    "valid": validation_frame,
    "test": test_frame,
}
```

The key is `valid`, not `val`. Generic defaults are:

```python
split = data.get_split(
    method="random",
    seed=42,
    frac=[0.7, 0.1, 0.2],
)
```

Fractions are train/validation/test and should be finite, non-negative, and sum to
one. Upstream does not consistently validate this before arithmetic; the bundled
CLI does.

### Loader-specific methods

| Loader family | Verified methods | Additional arguments |
|---|---|---|
| Single prediction | `random`, `scaffold`, internal `cold_<entity>` | none |
| Pair prediction (`DTI`, `DDI`, etc.) | `random`, `cold_split`, entity aliases such as `cold_drug`, `combination`, `time` | `column_name`, `time_column` |
| General multi-prediction frame | `random`, `cold_split`, `combination` | `column_name` |
| `MolGen`, `Reaction`, `RetroSyn` | `random` | none |
| Benchmark train/valid | group metadata chooses `scaffold`, `random`, `combination`, or `group` | `benchmark`, `split_type`, `seed` |

The generic official cold-start spelling is:

```python
split = data.get_split(
    method="cold_split",
    column_name=["Drug", "Target"],
    seed=42,
    frac=[0.7, 0.1, 0.2],
)
```

Inspect `data.get_data().columns` first. A DTI frame commonly uses `Drug` and
`Target`, but other tasks have different entity names. Prefer `cold_split` with
explicit columns over inferred aliases.

## Random split details

`create_fold`:

1. samples test rows with `random_state=seed`;
2. samples validation rows from the remainder with **fixed**
   `random_state=1`;
3. assigns remaining rows to train;
4. resets partition indices.

Consequences:

- the supplied seed changes test membership;
- it does not independently seed validation sampling;
- integer rounding and Pandas sampling can make exact counts differ from naïve
  multiplication;
- a different seed is not a guarantee that every partition changes.

Record content hashes or stable IDs when exact split reproducibility matters.

## Scaffold split details

The official generic documentation limits scaffold split to molecule-based
single-instance ADME, Tox, and HTS tasks. In 1.1.15 the implementation:

- requires RDKit;
- parses the configured molecular entity as SMILES;
- computes Bemis–Murcko scaffold strings with `includeChirality=False`;
- groups rows by exact scaffold string;
- shuffles large and small scaffold groups with `seed`;
- greedily assigns whole groups to partitions;
- omits SMILES that raise during scaffold generation.

The requested row fractions are targets, not guarantees, because whole scaffold
groups are assigned together. “Scaffold split” means exact computed scaffold groups
do not cross partitions in that implementation. It does **not** establish that:

- close analogs or similar scaffolds cannot cross;
- duplicates, labels, assay batches, sources, or dates are isolated;
- stereochemistry is isolated;
- invalid/missing structures are represented;
- preprocessing performed before splitting did not leak information.

Audit exact structures, scaffolds, identifiers, labels, provenance, and temporal
fields appropriate to the scientific question. Use cautious language such as
“partitioned by PyTDC's 1.1.15 Murcko-scaffold implementation,” not “leakage-free.”

## Cold split details

`cold_split` samples unique values independently for each requested column, then:

- keeps test rows satisfying all sampled test-entity memberships;
- removes any row containing a test entity from the train/validation pool;
- samples validation entity values from the remainder;
- keeps validation rows satisfying all validation memberships;
- removes validation entities from train.

For multiple columns this intersection/removal process can discard many
cross-combination rows, produce empty validation/test partitions, and yield row
fractions far from `frac`. PyTDC raises `ValueError` when test or validation is
empty.

Exact values in each requested column are designed to be disjoint across returned
partitions. That is a narrow entity-overlap property, not proof against:

- aliases or duplicated entities with different identifiers;
- homologous targets or structurally near-identical compounds;
- shared higher-level groups;
- preprocessing or label leakage.

The bundled loader CLI reports pairwise exact-value overlap counts for requested
columns without making a broader claim.

`cold_drug_target` is not a 1.1.15 method. Use:

```python
data.get_split(
    method="cold_split",
    column_name=["Drug", "Target"],
    seed=42,
)
```

## Combination and time splits

### Combination

The built-in `combination` implementation is designed for DrugSyn data with
`Drug1_ID`, `Drug2_ID`, and `Cell_Line_ID`. It separates drug-pair combinations
across partitions while representing cell lines.

In 1.1.15 it adds an internal `concat` column and does not remove it consistently
from every returned partition. Inspect schemas rather than assuming identical
columns. Do not apply it generically to DDI or DTI.

### Time

Pair loaders use:

```python
split = data.get_split(
    method="time",
    time_column="Year",
    frac=[0.7, 0.1, 0.2],
)
```

The verified built-in dataset case is `DTI(name="BindingDB_Patent")`, whose loader
adds `Year`. The implementation sorts by the time column and returns an additional
`split_time` summary. It does not use `seed`.

The spelling `temporal` is unsupported. Time boundaries can contain ties and the
implementation uses boundary comparisons, so inspect timestamps and counts.

`stratified=True` is not a supported `get_split` argument in these loaders.

## Evaluator registry

Discover exact names from the installed package:

```bash
python scripts/discover_metadata.py --kind evaluators --limit 100
```

Verified scalar registry names include:

```text
roc-auc, f1, pr-auc, precision, recall, accuracy,
mse, rmse, mae, r2, pcc, spearman,
micro-f1, macro-f1, kappa, avg-roc-auc,
rp@k, pr@k, range_logAUC
```

Generation/distribution names include:

```text
novelty, diversity, uniqueness, validity, fcd_distance, kl_divergence
```

Coordinate names include `rmsd` and `kabsch_rmsd`. Metadata also lists `smina`, bu

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

