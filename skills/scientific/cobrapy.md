---
id: sci-cobrapy
name: "Scientific: cobrapy"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Performs constraint-based metabolic modeling with COBRApy, including FBA, pFBA, FVA, gene knockouts, flux sampling, growth media, production envelopes, gap filling, and SBML model validation for systems biology and metabolic engineering."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "cobrapy"
keywords:
  - "cobrapy"
  - "performs"
  - "constraint"
  - "metabolic"
  - "modeling"
  - "including"
---

# COBRApy - Constraint-Based Reconstruction and Analysis

## When to use

Use for loading/building metabolic networks, optimizing their steady-state fluxes,
knockout screens, medium design, feasible-space sampling, and gap-filling hypotheses.
FBA is a constraint-based prediction; it does not infer kinetic rates or establish
experimental growth, thermodynamic feasibility, or flux identifiability.

## Setup and reproducibility

Targets **cobra 0.32.1** (import `cobra`), checked against its released source and
[current documentation](https://cobrapy.readthedocs.io/en/latest/).

```bash
uv pip install "cobra==0.32.1"
# Optional SciPy support for MATLAB I/O and array operations:
uv pip install "cobra[array]==0.32.1"
```

Plotting examples additionally require matplotlib, pandas, and seaborn. The
`cobra[chrr]` extra supplies hopsy for the new CHRR sampler; that optional backend
was documentation-reviewed, not executed in this refresh. In 0.32.1, `sample()`
defaults to `method="auto"` (CHRR when hopsy is installed, otherwise OptGP).
Choose the method explicitly to avoid environment-dependent changes.

Record model source/version/checksum, cobra and solver versions, objective,
medium, bounds, tolerances, and any random seed with each analysis. GLPK handles
the examples below; inspect `cobra.util.solver.solvers` before choosing an
optional solver. Use `"hybrid"` for its HiGHS/OSQP interface when installed;
the legacy `"osqp"` alias is deprecated. QP methods require a suitable backend.
Start with `processes=1`; scripts using multiprocessing need a guarded entry point.

## Workflow

### 1. Load, inspect, and validate a model

```python
from cobra.io import load_model

# These names are bundled: textbook, iJO1366, salmonella.
model = load_model("textbook")  # model.id is e_coli_core; 95 reactions
model.solver = "glpk"
print(model.id, len(model.reactions), len(model.metabolites), len(model.genes))
print(model.reactions.get_by_id("PFK").reaction)
print(model.reactions.PFK.gene_reaction_rule)
print(model.medium)

solution = model.optimize(raise_error=True)
assert solution.status == "optimal"
print(solution.objective_value, solution.fluxes["PFK"])
# error_value=None raises on a failed solve; the default instead returns NaN.
baseline = model.slim_optimize(error_value=None)
assert baseline > 0
```

`e_coli_core` is a remote BiGG identifier, **not** a bundled alias for `textbook`.
The released remote adapters encounter redirects on current BiGG/BioModels URLs;
see [model I/O](references/api_quick_reference.md) for verified download routes
and local SBML loading. Do not assume `load_model` caches: its 0.32.1 implementation
accepts `cache` but does not use it. Save source files for reproducibility.

Check chemical formulas/charges and boundary annotations separately from solver
feasibility. Review excluded biomass/pseudo reactions and missing chemistry;
an empty imbalance dictionary alone cannot establish a chemically valid model.
The [validation workflow](references/workflows.md) distinguishes those cases.

### 2. Compare FBA, pFBA, and FVA under stated constraints

```python
from cobra.flux_analysis import pfba, geometric_fba, flux_variability_analysis

biomass_id = "Biomass_Ecoli_core"  # inspect IDs/objective for each new model
parsimonious = pfba(model)
print(parsimonious.fluxes[biomass_id])
# parsimonious.objective_value is the minimized total flux, not biomass growth.
centered = geometric_fba(model, processes=1)

fva = flux_variability_analysis(
    model, reaction_list=["PFK", "FBA", "PGI"],
    fraction_of_optimum=0.9, processes=1,
)
loopless_fva = flux_variability_analysis(
    model, reaction_list=["PFK", "FBA", "PGI"],
    fraction_of_optimum=0.9, loopless="fastSNP", processes=1,
)
print(fva)  # index: reaction ID; columns: minimum, maximum
```

FVA extrema are optimized separately and need not be jointly achievable.
`loopless="fastSNP"` computes loopless bounds; `"cycleFreeFlux"` is an alternative
that need not find the optimal bounds. Boolean `loopless` arguments are deprecated.
Loop removal does not impose measured Gibbs energies or metabolite concentrations.
Fractional objective thresholds here assume a positive biomass maximization
objective; use an explicit constraint for other objective signs/directions.

### 3. Knockouts and media

```python
from cobra.flux_analysis import single_gene_deletion
from cobra.medium import minimal_medium

results = single_gene_deletion(model, processes=1)
valid = results[results.status.eq("optimal") & results.growth.notna()]
low_growth = valid[valid.growth < 0.01 * baseline]  # declared 1% criterion
unresolved = results[~results.index.isin(valid.index)]
print(low_growth[["ids", "growth"]], unresolved[["ids", "status"]])

with model:
    medium = model.medium
    medium["EX_o2_e"] = 0.0
    model.medium = medium  # editing the returned dict alone does not change model
    anaerobic = model.optimize()
    print(anaerobic.status, anaerobic.objective_value)

min_medium = minimal_medium(model, 0.5 * baseline, minimize_components=True)
if min_medium is None:
    raise RuntimeError("No medium found at the requested growth target")
with model:
    model.medium = min_medium.to_dict()
    assert model.slim_optimize(error_value=None) >= 0.5 * baseline - 1e-6
```

Deletion results contain `ids` **sets**, `growth`, and `status`; the index is not a
pair MultiIndex. Double-deletion results also contain singleton sets (self-pairs).
Classify failed/infeasible solves separately from feasible low-growth mutants.
A knockout's `growth` column means the model's objective, so ensure it is biomass.

`model.medium` values are positive import bounds, not measured concentrations.
Exchange flux signs depend on reaction stoichiometry; the textbook's one-reactant
exchanges use negative flux for uptake. `open_exchanges=False` retains the allowed
nutrient universe while the optimizer selects a nutrient subset and its import
bounds; it does not fix the selected nutrients or amounts. `open_exchanges=True`
expands that universe and can choose unintended carbon sources. Minimal media can
be nonunique; validate the returned medium with the intended growth objective.

### 4. Sample the same feasible region as the FVA comparison

```python
from cobra.sampling import OptGPSampler

with model:
    model.reactions.get_by_id(biomass_id).lower_bound = 0.9 * baseline
    # The growth floor is already installed. fraction=0 adds no stronger optimum.
    sampled_fva = flux_variability_analysis(
  

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

