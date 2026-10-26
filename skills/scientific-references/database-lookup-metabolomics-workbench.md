---
id: sciref-database-lookup-metabolomics-workbench
name: "Scientific Ref: Metabolomics Workbench REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Metabolomics Workbench REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup metabolomics workbench"
  - "metabolomics workbench rest api"
keywords:
  - "database"
  - "lookup"
  - "metabolomics"
  - "workbench"
  - "specialized"
  - "scientific"
  - "reference"
---

# Metabolomics Workbench REST API

## Base URL
```
https://www.metabolomicsworkbench.org/rest/
```

## Auth
No API key required. Fully public.

## URL Structure
```
/rest/{context}/{input_item}/{input_value}/{output_item}
```

Contexts: `study`, `compound`, `refmet`, `gene`, `protein`, `moverz` (`exactmass` is an input item, not a context)

## Key Endpoints

### Study Context
| URL Pattern | Description |
|---|---|
| `/rest/study/study_id/{ST_ID}/summary` | Study summary metadata |
| `/rest/study/study_id/{ST_ID}/metabolites` | Metabolites in a study |
| `/rest/study/study_id/{ST_ID}/analysis` | Analysis details |
| `/rest/study/study_id/{ST_ID}/factors` | Experimental factors |
| `/rest/study/study_id/{ST_ID}/data` | Named metabolite data matrix |
| `/rest/study/study_title/{keyword}/summary` | Search studies by title keyword |
| `/rest/study/analysis_id/{AN_ID}/summary` | Summary by analysis ID |

Study IDs: `ST######` (e.g., `ST000001`). Analysis IDs: `AN######`.

### Compound Context
| URL Pattern | Description |
|---|---|
| `/rest/compound/formula/{FORMULA}/all` | Search compound by molecular formula |
| `/rest/compound/pubchem_cid/{CID}/all` | Search by PubChem CID |
| `/rest/compound/hmdb_id/{HMDB_ID}/all` | Search by HMDB ID |
| `/rest/compound/kegg_id/{KEGG_ID}/all` | Search by KEGG ID |
| `/rest/compound/inchi_key/{KEY}/all` | Search by InChI key |
| `/rest/compound/regno/{REGNO}/classification` | Compound classification |
| `/rest/compound/regno/{REGNO}/molfile` | MOL file (structure) |

### RefMet (Standardized Nomenclature)
| URL Pattern | Description |
|---|---|
| `/rest/refmet/name/{NAME}/all` | Full RefMet record |
| `/rest/refmet/match/{NAME}/name` | Match name to standardized RefMet name |

### Gene / Protein Context
| URL Pattern | Description |
|---|---|
| `/rest/gene/gene_symbol/{SYMBOL}/all` | Gene info by symbol |
| `/rest/gene/gene_id/{ID}/all` | Gene info by Entrez ID |
| `/rest/protein/uniprot_id/{ID}/all` | Protein by UniProt ID |

### Mass search

The moverz input encodes library, m/z, adduct and tolerance in Daltons:
```text
/rest/moverz/MB/635.52/M+H/0.5
```
`MB` selects the Metabolomics Workbench library. Encode a plus sign as `%2B`
when a client treats it as a space. Specify the ion/adduct; a positive/negative
mode label alone is not sufficient. Exact mass for a lipid abbreviation is:
```text
/rest/moverz/exactmass/PC(34:1)/M+H
```

## Example Calls

```
# Study summary
https://www.metabolomicsworkbench.org/rest/study/study_id/ST000001/summary

# Metabolites in a study
https://www.metabolomicsworkbench.org/rest/study/study_id/ST000001/metabolites

# Search studies by title
https://www.metabolomicsworkbench.org/rest/study/study_title/diabetes/summary

# Compounds with a formula (not unique chemical identity)
https://www.metabolomicsworkbench.org/rest/compound/formula/C6H12O6/all

# Compound by PubChem CID
https://www.metabolomicsworkbench.org/rest/compound/pubchem_cid/5793/all

# RefMet standardized name match
https://www.metabolomicsworkbench.org/rest/refmet/match/alpha-D-Glucose/name

# m/z search in positive mode
https://www.metabolomicsworkbench.org/rest/moverz/MB/635.52/M%2BH/0.5

# Exact mass search
https://www.metabolomicsworkbench.org/rest/moverz/exactmass/PC(34:1)/M%2BH
```

## Response Format
Most record queries default to JSON. `mwtab` returns MWTab text and `molfile` returns MOL text. `/moverz/exactmass/` returns a short HTML/text result: the live PC(34:1), M+H example returned 760.585077 and C42H83NO8P. No general pagination contract is exposed; keep queries narrow and inspect the actual content type and body. An HTTP 200 can contain an unsupported-input error. Resolve names through RefMet; `compound/name` is not a supported input item.

## Rate Limits
No published limits. Be reasonable. Add 0.5-1s delay for batch calls.

Official query builder and contract: https://www.metabolomicsworkbench.org/tools/mw_rest.php

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

