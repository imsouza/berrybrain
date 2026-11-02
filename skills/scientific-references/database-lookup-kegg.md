---
id: sciref-database-lookup-kegg
name: "Scientific Ref: KEGG REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): KEGG REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup kegg"
  - "kegg rest api"
keywords:
  - "database"
  - "lookup"
  - "kegg"
  - "specialized"
  - "scientific"
  - "reference"
---

# KEGG REST API

## Base URL
```
https://rest.kegg.jp
```

## Auth
No API key required. Free for academic use. Commercial use requires license.

## Important: KEGG returns tab-delimited text and flat-file format, NOT JSON.

## Key Operations (URL-path-based, no query parameters)

| URL Pattern | Description |
|-------------|-------------|
| `/list/{database}` | List all entries |
| `/list/{database}/{organism}` | List entries for organism |
| `/get/{dbentries}` | Get entry data (flat-file) |
| `/get/{dbentries}/image` | Pathway image (PNG) |
| `/get/{dbentries}/kgml` | Pathway as KGML XML |
| `/find/{database}/{query}` | Search by keyword |
| `/find/{database}/{query}/formula` | Search by molecular formula |
| `/find/{database}/{value}/exact_mass` | Search by exact mass |
| `/link/{target_db}/{source_db}` | Find linked entries between databases |
| `/link/{target_db}/{dbentries}` | Links for specific IDs |
| `/conv/{target_db}/{dbentries}` | Cross-reference ID conversion |
| `/ddi/{dbentries}` | Drug-drug interactions |

## Database Codes

| Code | Database | Example ID |
|------|----------|------------|
| `pathway` | Pathways | `hsa00010` |
| `compound` | Compounds | `C00001` |
| `drug` | Drugs | `D00001` |
| `enzyme` | Enzymes | `ec:1.1.1.1` |
| `genes`/`hsa` | Genes | `hsa:10458` |
| `disease` | Diseases | `H00001` |
| `reaction` | Reactions | `R00001` |
| `ko` | KO orthologs | `K00001` |

## Example Calls

```
# List human pathways
https://rest.kegg.jp/list/pathway/hsa

# Get pathway entry
https://rest.kegg.jp/get/hsa00010

# Search compounds by name
https://rest.kegg.jp/find/compound/aspirin

# Search by molecular formula
https://rest.kegg.jp/find/compound/C9H8O4/formula

# Find pathways for a gene
https://rest.kegg.jp/link/pathway/hsa:10458

# Find diseases for a gene
https://rest.kegg.jp/link/disease/hsa:672

# Convert KEGG to PubChem IDs
https://rest.kegg.jp/conv/pubchem/C00001

# Get multiple entries (max 10, joined with +)
https://rest.kegg.jp/get/C00001+C00002+C00003

# Drug-drug interactions
https://rest.kegg.jp/ddi/D00564+D00110
```

## Response Format
Tab-delimited text for list/find/link/conv. Flat-file text for get. **No JSON support.**

## Rate Limits
KEGG requests at most 3 calls per second; pace below that and honor failures. Batch up to 10 IDs per `/get` with `+`. May return HTTP 403 if too many requests.

KEGG `conv/pubchem/...` maps to PubChem **Substance IDs (SIDs)**, not Compound IDs (CIDs). Resolve SID to CID through PubChem before joining compound properties. Official contract: https://www.kegg.jp/kegg/rest/keggapi.html

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

