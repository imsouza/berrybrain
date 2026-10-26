---
id: sciref-database-lookup-pdb
name: "Scientific Ref: RCSB Protein Data Bank (PDB) API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): RCSB Protein Data Bank (PDB) API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup pdb"
  - "rcsb protein data bank (pdb) api reference"
keywords:
  - "database"
  - "lookup"
  - "pdb"
  - "specialized"
  - "scientific"
  - "reference"
  - "rcsb"
---

# RCSB Protein Data Bank (PDB) API Reference

## Base URLs
- **Data API**: `https://data.rcsb.org/rest/v1`
- **Search API**: `https://search.rcsb.org/rcsbsearch/v2/query`
- **GraphQL**: `https://data.rcsb.org/graphql`
- **Files**: `https://files.rcsb.org`

## Authentication
None required. Fully public API.

## Rate Limits
No published hard limits; be courteous (a few requests/second). Bulk downloads available via FTP.

## Key Endpoints

### 1. Entry Lookup (Data API)
```
GET https://data.rcsb.org/rest/v1/core/entry/{entry_id}
```
Example:
```
GET https://data.rcsb.org/rest/v1/core/entry/4HHB
```
Returns JSON with resolution, method, deposition date, title, authors, etc.

### 2. Polymer Entity (unique molecular entity)
```
GET https://data.rcsb.org/rest/v1/core/polymer_entity/{entry_id}/{entity_id}
```
Example:
```
GET https://data.rcsb.org/rest/v1/core/polymer_entity/4HHB/1
```

An entity may have multiple chain instances. For chain-specific coordinates/annotations use `/core/polymer_entity_instance/{entry_id}/{label_asym_id}`; `label_asym_id` is the mmCIF identifier, not necessarily the author chain ID.

### 3. Assembly Info
```
GET https://data.rcsb.org/rest/v1/core/assembly/{entry_id}/{assembly_id}
```

### 4. Full-Text and Attribute Search (Search API)
```
POST https://search.rcsb.org/rcsbsearch/v2/query
Content-Type: application/json
```
Example — search by UniProt accession:
```json
{
  "query": {
    "type": "terminal",
    "service": "text",
    "parameters": {
      "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
      "operator": "exact_match",
      "value": "P69905"
    }
  },
  "return_type": "entry"
}
```

### 5. Sequence Search (Search API)
```json
{
  "query": {
    "type": "terminal",
    "service": "sequence",
    "parameters": {
      "evalue_cutoff": 0.1,
      "identity_cutoff": 0.9,
      "sequence_type": "protein",
      "value": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSH"
    }
  },
  "return_type": "polymer_entity"
}
```

### 6. Structure Similarity Search
```json
{
  "query": {
    "type": "terminal",
    "service": "structure",
    "parameters": {
      "value": {"entry_id": "4HHB", "assembly_id": "1"},
      "operator": "strict_shape_match"
    }
  },
  "return_type": "assembly"
}
```

### 7. Download Structure Files
```
GET https://files.rcsb.org/download/{entry_id}.cif
GET https://files.rcsb.org/download/{entry_id}.pdb
```

### 8. GraphQL Query
```
POST https://data.rcsb.org/graphql
```
Body example:
```json
{
  "query": "{ entry(entry_id: \"4HHB\") { rcsb_entry_info { resolution_combined } struct { title } } }"
}
```

## Response Format
REST/Data and successful Search results return JSON. Search can return HTTP 204 for no matches; do not attempt to JSON-decode an empty body. File downloads return PDB/mmCIF text.

## Useful `return_type` Values for Search
- `entry` — PDB IDs
- `polymer_entity` — entity-level results (e.g., 4HHB_1)
- `assembly` — biological assembly results

## Notes
- Search API uses POST with a JSON query DSL. Combine queries with `"type": "group"` and `"logical_operator": "and"/"or"`.
- Pagination via `"request_options": {"paginate": {"start": 0, "rows": 25}}`.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

