---
id: sciref-medchem-api-guide
name: "Scientific Ref: Medchem API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (medchem): Medchem API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "medchem api guide"
  - "medchem api reference"
keywords:
  - "medchem"
  - "api"
  - "guide"
  - "specialized"
  - "scientific"
  - "reference"
---

# Medchem API Reference

Reference for **medchem 2.1.1**, checked 2026-10-01 against current documentation and installed release source. Requires Python 3.11+. Official API: https://medchem-docs.datamol.io/stable/api/medchem.rules.html

## Module: medchem.rules

### Class: RuleFilters

Filter molecules by multiple medicinal chemistry rules. Returns a **pandas DataFrame**.

**Constructor:**

```python
RuleFilters(rule_list: List[Union[str, Callable]], rule_list_names: Optional[List[str]] = None)
```

**Call signature:**

```python
__call__(
    mols: Sequence[Union[str, Mol]],
    n_jobs: int = -1,
    progress: bool = False,
    progress_leave: bool = False,
    scheduler: str = "auto",
    keep_props: bool = False,
    fail_if_invalid: bool = True,
) -> pd.DataFrame
```

**Return columns:** `mol`, `pass_all`, `pass_any`, plus one boolean column per rule. With `keep_props=True`, descriptor columns (`mw`, `clogp`, `tpsa`, etc.) are included.

**Class methods:**

```python
RuleFilters.list_available_rules_names()  # list of 22 rule names
RuleFilters.list_available_rules()        # rules with property metadata
```

**Example:**

```python
rfilter = mc.rules.RuleFilters(rule_list=["rule_of_five", "rule_of_cns"])
df = rfilter(mols=mol_list, n_jobs=-1, progress=True)
passing = df[df["pass_all"]]
```

### Module: medchem.rules.basic_rules

Individual rule functions for single molecules. Each returns `bool` (True = passes).

| Function | Description |
|----------|-------------|
| `rule_of_five(mol)` | Lipinski Rule of Five |
| `rule_of_five_beyond(mol)` | Beyond Ro5 (large binding sites) |
| `rule_of_four(mol)` | Rule of Four |
| `rule_of_three(mol)` | Fragment library Rule of Three |
| `rule_of_three_extended(mol)` | Extended Ro3 |
| `rule_of_two(mol)` | Rule of Two |
| `rule_of_ghose(mol)` | Ghose filter |
| `rule_of_veber(mol)` | Veber oral bioavailability |
| `rule_of_reos(mol)` | REOS filter |
| `rule_of_chemaxon_druglikeness(mol)` | ChemAxon drug-likeness |
| `rule_of_egan(mol)` | Egan permeability |
| `rule_of_pfizer_3_75(mol)` | Pfizer 3/75 filter |
| `rule_of_gsk_4_400(mol)` | GSK 4/400 filter |
| `rule_of_oprea(mol)` | Oprea lead-like |
| `rule_of_xu(mol)` | Xu filter |
| `rule_of_cns(mol)` | CNS drug-likeness |
| `rule_of_respiratory(mol)` | Respiratory drug-likeness |
| `rule_of_zinc(mol)` | ZINC-like |
| `rule_of_leadlike_soft(mol)` | Soft lead-like |
| `rule_of_druglike_soft(mol)` | Soft drug-like |
| `rule_of_generative_design(mol)` | Generative design space |
| `rule_of_generative_design_strict(mol)` | Strict generative design |

### Descriptor helpers

```python
mc.rules.list_descriptors()  # property names for query language
```

---

## Module: medchem.structural

### Class: CommonAlertsFilters

ChEMBL-derived structural alert filter sets (Glaxo, Dundee, BMS, etc.).

```python
CommonAlertsFilters(alerts_set=["BMS", "Dundee", "Glaxo"], alerts_db_path=None)
```

The source defaults to **BMS only**, despite an older constructor docstring saying BMS+Dundee+Glaxo. Select sets explicitly.

**Returns DataFrame columns:** `mol`, `pass_filter`, `status`, `reasons`

- `status`: `"exclude"` or `"ok"` in the current common-alert implementation
- `pass_filter`: bool — True if compound passes

**Methods:**

```python
list_default_available_alerts()  # DataFrame of alert definitions
__call__(mols, n_jobs=-1, progress=False, ...) -> pd.DataFrame
```

### Class: NIBRFilters

Novartis screening-deck curation filters ([Schuffenhauer et al., J. Med. Chem. 2020](https://dx.doi.org/10.1021/acs.jmedchem.0c01332)).

```python
NIBRFilters()
```

**Returns DataFrame columns:** `mol`, `pass_filter`, `status`, `severity`, `reasons`, `n_covalent_motif`, `special_mol`

- `severity`: sum of flag scores; any explicit exclusion alert yields 10.
- `status`: `"exclude"`, `"flag"`, `"annotations"`, or `"ok"`.
- Class `pass_filter` rejects explicit exclusions only. Combine it with `severity < 10` to also reject accumulated flags. For prevalidated molecules, `functional.nibr_filter(max_severity=10)` supplies the severity cutoff. The functional wrapper checks severity only and can admit invalid inputs (reported by the class with severity zero); never use it as a parse-validity check.

### Lilly demerits (optional)

Requires native tools installed with `medchem install-lilly` (C++/make/zlib/Ruby, source download and build; WSL on Windows). This native installation/execution was not exercised locally. Access via:

```python
mc.functional.lilly_demerit_filter(mols, max_demerits=160, n_jobs=-1)
# or
from medchem.structural.lilly_demerits import LillyDemeritsFilters
```

---

## Module: medchem.functional

High-level boolean-mask API. **True = passes** (no alert / passes all rules). `return_idx=True` returns indices instead of the default NumPy mask. `alert_filter` uses the names from `CommonAlertsFilters.list_default_available_alerts()`; it does not validate unknown names, which can silently create an empty alert set. For `brenk` and `pains_a`, use `catalog_filter`. Its string interface deliberately rejects `nibr` and `bredt`; use `nibr_filter` and `bredt_filter` respectively. Raw NIBR catalog matching ignores severity and includes annotations.

| Function | Description |
|----------|-------------|
| `rules_filter(mols, rules, n_jobs=None, ...)` | Apply rule list |
| `nibr_filter(mols, max_severity=10, n_jobs=None, ...)` | NIBR filter |
| `alert_filter(mols, alerts, alerts_db=None, n_jobs=1, ...)` | Common-alert collection names, case-insensitive |
| `catalog_filter(mols, catalogs, n_jobs=-1, ...)` | Named catalogs or RDKit FilterCatalog objects |
| `complexity_filter(mols, complexity_metric="bertz", limit="99", ...)` | Complexity threshold |
| `lilly_demerit_filter(mols, max_demerits=160, ...)` | Lilly demerits (optional) |
| `chemical_group_filter(mols, chemical_group, ...)` | Exclude group matches |
| `bredt_filter(mols, ...)` | Bredt instability filter |
| `macrocycle_filter(mols, ...)` | Macrocycle filter |
| `protecting_groups_filter(mols, ...)` | Protecting group filter |
| `ring_infraction_filter(mols, ...)` | Ring infraction filter |
| `symmetry_filter(mols, ...)` | Symmetry filter |

---

In 2.1.1, `bredt_filter` kekulizes supplied RDKit objects in place, changing later aromatic substructure/PAINS matches. Preserve the shared input molecules by copying them:

```python
from rdkit import Chem
passes_bredt = mc.functional.bredt_filter([Chem.Mol(mol) for mol in mol_list], n_jobs=1)
```

## Module: medc

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

