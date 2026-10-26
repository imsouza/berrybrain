---
id: sciref-database-lookup-encode
name: "Scientific Ref: ENCODE (Encyclopedia of DNA Elements)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): ENCODE (Encyclopedia of DNA Elements)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup encode"
  - "encode (encyclopedia of dna elements)"
keywords:
  - "database"
  - "lookup"
  - "encode"
  - "specialized"
  - "scientific"
  - "reference"
---

# ENCODE (Encyclopedia of DNA Elements)

## Base URL
```
https://www.encodeproject.org
```

## Auth
No auth required. Append `?format=json` or set `Accept: application/json`.

## Portal data objects and search support JSON; file download URLs return file content.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/search/?type=Experiment&format=json` | Search experiments |
| `/experiments/{accession}/?format=json` | Specific experiment |
| `/files/{accession}/?format=json` | File metadata |
| `/biosamples/{accession}/?format=json` | Biosample info |
| `/annotations/?format=json` | Search annotations |

## Search Parameters
- `type` — Experiment, File, Biosample, Annotation, etc.
- `assay_title` — ChIP-seq, RNA-seq, ATAC-seq, etc.
- `target.label` — target protein (e.g. CTCF, H3K27ac)
- `biosample_ontology.term_name` — cell type
- `limit` — results per page
- `field` — specific fields to return

## Example Calls
```
# ChIP-seq experiments for CTCF
https://www.encodeproject.org/search/?type=Experiment&assay_title=ChIP-seq&target.label=CTCF&format=json&limit=5

# Specific experiment
https://www.encodeproject.org/experiments/ENCSR000AAA/?format=json

# Files for an experiment
https://www.encodeproject.org/search/?type=File&dataset=/experiments/ENCSR000AAA/&format=json
```

## Response Format
JSON-LD. Search: `@graph` array + `total` + `facets`. Use `frame=object` or `frame=embedded` to control depth.

## Rate Limits
No published limits. Use `limit=` and `field=` to reduce payload.

Search pagination uses `limit` and `from`; verify `@graph` length against `total`. Preserve file assembly, output_type, status and audit flags before selecting a download. Public reads need no key, while restricted/unreleased objects require authorized access.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

