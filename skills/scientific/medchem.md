---
id: sci-medchem
name: "Scientific: medchem"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Applies medicinal chemistry filters for compound triage, using drug-likeness rules (Lipinski, Veber, CNS), structural alert catalogs (PAINS, NIBR, ChEMBL), complexity metrics, and the medchem query language for library filtering."
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "medchem"
keywords:
  - "medchem"
  - "applies"
  - "medicinal"
  - "chemistry"
  - "filters"
  - "compound"
  - "triage"
---

# Medchem

## Overview

Medchem is a Python library from [datamol-io](https://github.com/datamol-io/medchem) for molecular filtering and prioritization in drug discovery. Apply literature-derived drug-likeness rules, named alert catalogs, complexity thresholds, chemical-group detection, and a custom query language to triage compound libraries at scale. Filters are context-specific guidelines — combine with domain expertise and target knowledge.

**Verified runtime:** medchem **2.1.1**, datamol **0.13.0**, RDKit **2026.3.6**; Python **3.11+**. `RuleFilters` and structural classes return pandas DataFrames. Filters run locally; installation and documentation lookup need network access. Lilly native execution was not tested in this review.

## When to Use This Skill

This skill should be used when:
- Applying drug-likeness rules (Lipinski, Veber, CNS, lead-like) to compound libraries
- Filtering molecules by structural alerts, PAINS, or NIBR screening-deck rules
- Prioritizing compounds for hit-to-lead or lead optimization
- Calculating complexity metrics against ZINC-derived thresholds
- Detecting functional groups or named substructure catalogs
- Building multi-criteria filters with the medchem query language

## Installation

```bash
uv pip install "medchem==2.1.1" "datamol==0.13.0" "rdkit==2026.3.6"
```

Optional Lilly integration: install the upstream checksum-pinned native tools beside the active Python. This downloads source, builds executables, and runs native regression tests (C++ compiler, make, zlib, Ruby; WSL on Windows). This installation command is documented upstream, not executed here:

```bash
medchem install-lilly
```

## Core Capabilities

### 1. Medicinal Chemistry Rules

Apply established drug-likeness rules via `medchem.rules`.

**List available rules:**

```python
import medchem as mc

mc.rules.RuleFilters.list_available_rules_names()
# ['rule_of_five', 'rule_of_five_beyond', 'rule_of_four', 'rule_of_three', ...]
```

**Single rule on one molecule:**

```python
import datamol as dm
import medchem as mc

smiles = "CC(=O)OC1=CC=CC=C1C(=O)O"  # aspirin
mc.rules.basic_rules.rule_of_five(smiles)   # True
mc.rules.basic_rules.rule_of_cns(smiles)    # True
mc.rules.basic_rules.rule_of_veber(smiles)  # True
```

**Multiple rules with `RuleFilters` (returns a DataFrame):**

```python
import datamol as dm
import medchem as mc

mols = [dm.to_mol(s) for s in smiles_list]

rfilter = mc.rules.RuleFilters(
    rule_list=["rule_of_five", "rule_of_oprea", "rule_of_cns", "rule_of_leadlike_soft"]
)
df = rfilter(mols=mols, n_jobs=-1, progress=True, keep_props=False)

# Columns: mol, pass_all, pass_any, rule_of_five, rule_of_oprea, ...
passing = df[df["pass_all"]]
```

Examples below use already parsed `mol_list`, `smiles_list`, and `candidates` supplied by the caller; reject missing/empty structures before filtering. Use `keep_props=True` to include computed descriptors (`mw`, `clogp`, `tpsa`, etc.) in the result.

### 2. Structural Alert Filters

Detect problematic patterns with `medchem.structural`. Both classes return **DataFrames** with `pass_filter`, `status`, and `reasons` columns.

**Common alerts (ChEMBL-derived rule sets):**

```python
import medchem as mc

alert_filter = mc.structural.CommonAlertsFilters(alerts_set=["BMS", "Dundee", "Glaxo"])
df = alert_filter(mols=mol_list, n_jobs=-1, progress=True)
# df columns: mol, pass_filter, status, reasons

clean = df[df["pass_filter"]]
```

**NIBR filters (Novartis screening-deck curation):**

```python
nibr_filter = mc.structural.NIBRFilters()
df = nibr_filter(mols=mol_list, n_jobs=-1, progress=True)
# df columns: mol, pass_filter, status, severity, reasons, n_covalent_motif, special_mol
```

The class rejects explicit exclusion alerts. To also reject accumulated flag severity ≥10, use `df["pass_filter"] & (df["severity"] < 10)`, or `mc.functional.nibr_filter(..., max_severity=10)`. The functional cutoff is strict `< 10` and assumes valid molecules: it checks severity alone and can admit parse failures with severity zero. Prevalidate inputs.

### 3. Named Catalog Filters (PAINS, Brenk, etc.)

Use `medchem.catalogs.NamedCatalogs` for RDKit `FilterCatalog` instances, or the functional API:

```python
import medchem as mc

# List available named catalogs
mc.catalogs.list_named_catalogs()
# ['tox', 'pains', 'pains_a', 'brenk', 'nibr', 'zinc', ...]

# Functional API — True means molecule passes (no alert match)
passes = mc.functional.catalog_filter(mols=mol_list, catalogs=["pains"], n_jobs=-1)

# Or via catalog objects
passes = mc.functional.catalog_filter(
    mols=mol_list,
    catalogs=[mc.catalogs.NamedCatalogs.pains()],
    n_jobs=-1,
)
```

`alert_filter` is a different API: it uses the ChEMBL common-alert collection names from `CommonAlertsFilters.list_default_available_alerts()`, not every `NamedCatalogs` name. For example, `brenk` and `pains_a` belong in `catalog_filter`. Set common-alert sets explicitly; the current class implementation defaults to BMS only. `catalog_filter` rejects the string names `nibr` and `bredt`; use their dedicated functional filters. Raw NIBR catalog matches include annotations, regardless of severity.

### 4. Functional API

`medchem.functional` provides one-call wrappers that return boolean masks (True = passes):

```python
import medchem as mc

mc.functional.rules_filter(mols=mol_list, rules=["rule_of_five", "rule_of_cns"], n_jobs=-1)
mc.functional.nibr_filter(mols=mol_list, max_severity=10, n_jobs=-1)
mc.functional.catalog_filter(mols=mol_list, catalogs=["pains", "brenk"], n_jobs=-1)
mc.functional.complexity_filter(mols=mol_list, complexity_metric="bertz", limit="99", n_jobs=-1)
```

Other helpers: `catalog_filter`, `chemical_group_filter`, `lilly_demerit_filter` (requires optional binaries), `macrocycle_filter`, `bredt_filter`, `protecting_groups_filter`, and more. Pass copies to `bredt_filter` (`[Chem.Mol(m) for m in mol_list]`, after `from rdkit import Chem`): its in-place kekulization changes later aromatic alert matches in 2.1.1.

### 5. Chemical Groups

Detect functional groups and curated pattern collections via `medchem.groups`:

```python
import medchem as mc

# Browse available group collections
mc.groups.list_default_chemical_groups()
# ['privileged_scaffolds', 'common_warhead_covalent_inhibitors', 'rings_in_drugs', ...]

group = mc.groups.ChemicalGroup(groups=["privileged_scaffolds"])
group.has_match(mol)                          # bool
group.get_matches(mol)                      

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

