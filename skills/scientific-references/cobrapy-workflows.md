---
id: sciref-cobrapy-workflows
name: "Scientific Ref: COBRApy workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (cobrapy): COBRApy workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "cobrapy workflows"
keywords:
  - "cobrapy"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# COBRApy workflows

The five Python workflows below were executed with cobra 0.32.1, GLPK, and Python
3.12 on the bundled textbook model. They are small demonstrations, not validated
predictions for an organism or condition. Run this setup first, then each workflow
independently; each loads a fresh model. Plotting needs matplotlib/seaborn. Choose
`OUTDIR` from the task context; authorization to produce outputs covers those files.

```python
from pathlib import Path
import cobra

OUTDIR = Path("cobrapy_output")
OUTDIR.mkdir(parents=True, exist_ok=True)
cobra.Configuration().solver = "glpk"
cobra.Configuration().processes = 1
```

## Workflow 1: Knockouts and synthetic-lethal candidates

The 1% wild-type growth threshold is an analysis choice. Separate successful
low-growth predictions from infeasible, numerical, or other unresolved solves.
The `ids` column contains sets, including singletons for self-pairs. Never derive
identifiers from the integer row index. GPR redundancy means one gene need not
correspond to one reaction. A bounded subset is a screen, not an exhaustive study.

```python
import pandas as pd
import matplotlib.pyplot as plt
from cobra.io import load_model
from cobra.flux_analysis import single_gene_deletion, double_gene_deletion

model = load_model("textbook")
baseline = model.slim_optimize(error_value=None)
assert baseline > 0
threshold = 0.01 * baseline
single_results = single_gene_deletion(model, processes=1)
valid_single = single_results[
    single_results.status.eq("optimal") & single_results.growth.notna()
].copy()
valid_single["gene"] = valid_single.ids.map(lambda ids: next(iter(ids)))
single_by_gene = valid_single.set_index("gene")["growth"]
low_growth = valid_single[valid_single.growth < threshold]
unresolved_single = single_results.drop(valid_single.index)
target_genes = sorted(single_by_gene[single_by_gene >= 0.5 * baseline].index)[:30]
double_results = double_gene_deletion(
    model, gene_list1=target_genes, gene_list2=target_genes, processes=1,
)
synthetic_lethals = double_results[
    double_results.status.eq("optimal")
    & double_results.growth.lt(threshold)
    & double_results.ids.map(
        lambda ids: len(ids) == 2
        and all(single_by_gene.get(g, float("nan")) >= 0.5 * baseline for g in ids)
    )
].copy()

fig, ax = plt.subplots()
valid_single.growth.hist(bins=25, ax=ax)
ax.axvline(baseline, color="red", linestyle="--", label="Wild type")
ax.set(xlabel="Predicted growth (1/h)", ylabel="Number of genes")
ax.legend()
fig.savefig(OUTDIR / "single_deletion_distribution.png", dpi=150)
plt.close(fig)
# Sort identifiers for reproducible, human-readable CSVs.
for name, table in [("single", single_results), ("double", double_results),
                    ("synthetic_lethals", synthetic_lethals)]:
    exported = table.assign(ids=table.ids.map(lambda ids: ";".join(sorted(ids))))
    exported.sort_values("ids").to_csv(OUTDIR / f"{name}_deletions.csv", index=False)
print("Low-growth single mutants:", len(low_growth))
print("Unresolved single mutants:", len(unresolved_single))
print("Candidate synthetic-lethal pairs:", len(synthetic_lethals))
```

## Workflow 2: Minimal and custom media

With `open_exchanges=False`, the **allowed nutrient universe stays fixed**. The
optimizer still **selects the nutrient subset and its import bounds** within that
universe; the selected nutrients and amounts are not fixed. This workflow therefore
minimizes component count within allowed nutrients, then rechecks the selected
medium. Opening all exchanges expands the allowed universe, permits alternative
carbon sources, and defines a different experiment. Minimal media may be nonunique; integer tolerances can affect tiny
imports. Report the objective, growth target and tested uptake units.

```python
import pandas as pd
from cobra.io import load_model
from cobra.medium import minimal_medium

model = load_model("textbook")
baseline = model.slim_optimize(error_value=None)
assert baseline > 0
minimal_media = {}
rechecked_growth = {}
for fraction in [0.25, 0.5, 0.75, 0.95]:
    target = fraction * baseline
    medium = minimal_medium(
        model, min_objective_value=target,
        minimize_components=True, open_exchanges=False,
    )
    if medium is None:
        raise RuntimeError(f"No medium found for growth {target}")
    with model:
        model.medium = medium.to_dict()
        growth = model.slim_optimize(error_value=None)
        assert growth >= target - 1e-6
    minimal_media[fraction] = medium
    rechecked_growth[fraction] = growth
pd.DataFrame(minimal_media).fillna(0).to_csv(OUTDIR / "minimal_media.csv")

# Retain valid IDs and other nutrients in this model; textbook has no EX_so4_e.
custom_medium = model.medium
custom_medium["EX_glc__D_e"] = 5.0
custom_medium["EX_o2_e"] = 0.0
with model:
    model.medium = custom_medium
    custom_growth = model.slim_optimize(error_value=None)
    limiting = []
    if custom_growth > model.tolerance:
        for exchange, bound in custom_medium.items():
            if bound <= 0:  # Doubling zero is not nutrient supplementation.
                continue
            with model:
                altered = model.medium
                altered[exchange] = 2 * bound
                model.medium = altered
                growth = model.slim_optimize(error_value=None)
                if growth > 1.01 * custom_growth:
                    limiting.append((exchange, growth / custom_growth - 1))
print("Custom growth:", custom_growth, "Candidate limiting imports:", limiting)
```

## Workflow 3: Matched FVA and sampling

FVA constraints are temporary. Explicitly install the growth floor **before**
creating the sampler. Compare samples with FVA from that same constrained model.
OptGP feasibility checks do not measure convergence; use independent seeds/chains,
trace plots and effective sample size for scientific inference. Correlation from
stoichiometric constraints is not evidence of regulation or causation.

```python
import matplotlib.pyplot as plt
import seaborn as sns
from cobra.io import load_model
from cobra.flux_analysis import flux_variability_analysis
from cobra.sampling import OptGPSampler

model = load_model("textbook")
biomass_id = "Biomass_Ecoli_core"
baseline = model.slim_optimize(error_value=None)
key_reactions = ["PFK", "FBA", "TPI", "GAPD", "PGK", "PGM", "ENO", "PYK"]
fva_optimal = flux_variability_analysis(
    model, reaction_list=key_reactions, fraction_of_optimum=1.0, processes=1,
)
with model:
    model.reac

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

