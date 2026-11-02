---
id: sciref-medchem-rules-catalog
name: "Scientific Ref: Medchem Rules and Filters Catalog"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (medchem): Medchem Rules and Filters Catalog"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "medchem rules catalog"
  - "medchem rules and filters catalog"
keywords:
  - "medchem"
  - "rules"
  - "catalog"
  - "specialized"
  - "scientific"
  - "reference"
---

# Medchem Rules and Filters Catalog

Catalog of medicinal chemistry rules, alert sets, and filters in **medchem 2.1.1** (reviewed 2026-10-01).

Thresholds below describe the **implemented functions**, which can differ from simplified literature summaries. See [versioned basic-rule source](https://github.com/datamol-io/medchem/blob/2.1.1/medchem/rules/basic_rules.py) and [official API](https://medchem-docs.datamol.io/stable/api/medchem.rules.html). Examples assume valid `mol`/`mols` supplied by the caller.

## Table of Contents

1. [Drug-Likeness Rules](#drug-likeness-rules)
2. [Lead-Likeness Rules](#lead-likeness-rules)
3. [Fragment Rules](#fragment-rules)
4. [CNS and Target-Class Rules](#cns-and-target-class-rules)
5. [Structural Alert Filters](#structural-alert-filters)
6. [Named Catalogs](#named-catalogs)
7. [Complexity Metrics](#complexity-metrics)
8. [Chemical Group Collections](#chemical-group-collections)
9. [Filter Selection Guidelines](#filter-selection-guidelines)

---

## Drug-Likeness Rules

### Rule of Five (Lipinski)

**Reference:** Lipinski et al., *Adv Drug Deliv Rev* (1997) 23:3–25

**Criteria:** MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10

```python
mc.rules.basic_rules.rule_of_five(mol)
# or
mc.rules.RuleFilters(rule_list=["rule_of_five"])
```

### Rule of Five Beyond

**Reference:** Doak et al., (2015) — compounds beyond Ro5 for large binding sites

**Criteria:** MW ≤ 1000, LogP ∈ [-2, 10], HBD ≤ 6, HBA ≤ 15, TPSA ≤ 250, rotatable bonds ≤ 20

```python
mc.rules.basic_rules.rule_of_five_beyond(mol)
```

### Rule of Veber

**Reference:** Veber et al., *J Med Chem* (2002) 45:2615–2623

**Criteria:** Rotatable bonds ≤ 10, TPSA ≤ 140 Å²

```python
mc.rules.basic_rules.rule_of_veber(mol)
```

### REOS (Rapid Elimination Of Swill)

**Implementation reference:** [Walters & Namchuk (2003), Designing screens: how to make your hits a hit](https://pubmed.ncbi.nlm.nih.gov/12669025/).

**Implemented criteria:** MW 200–500, cLogP −5 to 5, HBD 0–5, HBA 0–10, rotatable bonds 0–8, heavy atoms 15–50 (inclusive). The implementation computes formal charge but does not constrain it, despite the docstring advertising −2 to 2. Add an explicit charge bound when needed.

```python
mc.rules.basic_rules.rule_of_reos(mol)
```

### Egan, Ghose, Pfizer, GSK, Xu

Additional literature filters available as `rule_of_egan`, `rule_of_ghose`, `rule_of_pfizer_3_75`, `rule_of_gsk_4_400`, `rule_of_xu`.

### Rule of Druglike (Soft)

Combined soft drug-likeness criteria:

```python
mc.rules.basic_rules.rule_of_druglike_soft(mol)
```

---

## Lead-Likeness Rules

### Rule of Oprea

**Implementation reference:** [Oprea (2000), Property distribution of drug-related chemical databases](https://pubmed.ncbi.nlm.nih.gov/10756480/).

**Implemented criteria:** HBD 0–2, HBA 2–9, rotatable bonds 2–8, rings 1–4 (inclusive). This function does not constrain MW or cLogP; add explicit bounds if the project needs them.

```python
mc.rules.basic_rules.rule_of_oprea(mol)
```

### Rule of Leadlike (Soft)

**Implemented criteria:** MW 150–400, cLogP −3 to 4, HBD ≤4, HBA ≤7, TPSA ≤160 Å², rotatable bonds ≤9, rigid bonds ≤30, rings ≤4, maximum ring-system size ≤18, carbons 3–35, heteroatoms 1–15, heteroatom/carbon ratio 0.1–1.1, formal charge −4 to 4, charged atoms ≤4, stereocenters ≤2.

```python
mc.rules.basic_rules.rule_of_leadlike_soft(mol)
```

---

## Fragment Rules

### Rule of Three

**Reference:** Congreve et al., *Drug Discov Today* (2003) 8:876–877

**Implemented criteria:** MW ≤300, cLogP ≤3, HBD ≤3, HBA ≤3, rotatable bonds ≤3. There is no TPSA bound in `rule_of_three`. `rule_of_three_extended` adds TPSA ≤60 Å² and cLogP ≥−3 but permits HBA ≤6; it is not simply the base rule plus TPSA.

```python
mc.rules.basic_rules.rule_of_three(mol)
```

Also available: `rule_of_three_extended` and `rule_of_two`. `rule_of_four` instead selects larger, lipophilic PPI-inhibitor space (MW ≥400, cLogP ≥4, rings ≥4, HBA ≥4); it is not a fragment filter.

---

## CNS and Target-Class Rules

### Rule of CNS

**Implemented criteria:** MW 135–582, cLogP −0.2 to 6.1, TPSA 3–118 Å², HBD ≤3, HBA ≤5. These are inclusive heuristic bounds, not evidence of blood-brain barrier penetration.

```python
mc.rules.basic_rules.rule_of_cns(mol)
```

### Rule of Respiratory

Target-class filter for respiratory drugs:

```python
mc.rules.basic_rules.rule_of_respiratory(mol)
```

### Generative Design Rules

For ML-generated molecules:

```python
mc.rules.basic_rules.rule_of_generative_design(mol)
mc.rules.basic_rules.rule_of_generative_design_strict(mol)
```

---

## Structural Alert Filters

### PAINS (Pan Assay INterference compoundS)

**Reference:** Baell & Holloway, *J Med Chem* (2010) 53:2719–2740

Apply via named catalog — not a `basic_rules` function:

```python
mc.functional.catalog_filter(mols, catalogs=["pains"], n_jobs=-1)
# or query: NOT HASALERT("pains")
```

Sub-catalogs: `pains_a`, `pains_b`, `pains_c`.

### Common Alerts Filters

ChEMBL-curated rule sets (Glaxo, Dundee, BMS, MLSMR, etc.):

```python
alert_filter = mc.structural.CommonAlertsFilters(alerts_set=["BMS", "Dundee", "Glaxo"])
df = alert_filter(mols=mol_list, n_jobs=-1)
# current common-alert status: exclude | ok
```

### NIBR Filters

Novartis screening-deck curation ([Schuffenhauer et al., 2020](https://dx.doi.org/10.1021/acs.jmedchem.0c01332)):

```python
nibr_filter = mc.structural.NIBRFilters()
df = nibr_filter(mols=mol_list, n_jobs=-1)
# class rejects explicit exclusion alerts; also apply accumulated severity cutoff
passes = df["pass_filter"] & (df["severity"] < 10)
```

Or via functional API with `max_severity=10`.

### Lilly Demerits (optional)

Install native upstream tools with `medchem install-lilly`; requires C++/make/zlib/Ruby and network access for installation. The native integration uses upstream 2.1 rules and was not executed locally. The wrapper requires native `pass_filter=True` and either a missing score or a score strictly below `max_demerits=160` (a score of 160 fails). Native hard-rejection and atom-count rules also apply.

```python
mc.functional.lilly_demerit_filter(mols, max_demerits=160, n_jobs=-1)
```

---

## Named Catalogs

Available via `mc.catalogs.list_named_catalogs()` and `NamedCatalogs` static methods:

| Catalog | Purpose |
|---------|---------|
| `pains`, `pains_a/b/c` | PAINS substructure filters |
| `brenk` | Unwanted functional groups |
| `nih` | NIH screening filters |
| `zinc` | ZINC structural filters |
| `glaxo`, `dundee`, `bms` | Phar

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

