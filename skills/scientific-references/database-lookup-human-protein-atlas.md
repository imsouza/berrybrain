---
id: sciref-database-lookup-human-protein-atlas
name: "Scientific Ref: Human Protein Atlas (HPA)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Human Protein Atlas (HPA)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup human protein atlas"
  - "human protein atlas (hpa)"
keywords:
  - "database"
  - "lookup"
  - "human"
  - "protein"
  - "atlas"
  - "specialized"
  - "scientific"
  - "reference"
---

# Human Protein Atlas (HPA)

## Base URL
```
https://www.proteinatlas.org
```

## Auth
No API key required.

## Key Endpoints

| Purpose | URL Pattern |
|---|---|
| Gene data by Ensembl ID | `/{ENSEMBL_ID}.json` |
| Search | `/search/{QUERY}`; use the result page Download control for XML/TSV/JSON |

## Example Calls

```
# Gene data by Ensembl ID
https://www.proteinatlas.org/ENSG00000141510.json

# Search
https://www.proteinatlas.org/search/TP53
```

## Response Format (JSON, gene endpoint)
```json
{
  "Gene": "TP53",
  "Gene synonym": ["p53", "LFS1"],
  "Ensembl": "ENSG00000141510",
  "Gene description": "tumor protein p53",
  "Uniprot": ["P04637"],
  "Chromosome": "17",
  "Protein class": ["Transcription factors"],
  "RNA tissue specificity": "Low tissue specificity",
  "Subcellular location": ["Nucleoplasm"],
  "Pathology prognostics": [...]
}
```

## Bulk Downloads
For large-scale work, use TSV files from https://www.proteinatlas.org/about/download:
- `normal_tissue.tsv` — IHC tissue expression
- `rna_tissue_consensus.tsv` — RNA consensus
- `subcellular_location.tsv`
- `pathology.tsv` — cancer prognostics

## Rate Limits
No published limits. Be reasonable. Prefer bulk downloads for large queries.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

