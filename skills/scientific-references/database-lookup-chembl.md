---
id: sciref-database-lookup-chembl
name: "Scientific Ref: ChEMBL REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): ChEMBL REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup chembl"
  - "chembl rest api"
keywords:
  - "database"
  - "lookup"
  - "chembl"
  - "specialized"
  - "scientific"
  - "reference"
---

# ChEMBL REST API

## Base URL
```
https://www.ebi.ac.uk/chembl/api/data
```

## Auth
No API key required. Fully open and free.

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/molecule/{chembl_id}` | Get molecule by ChEMBL ID |
| `/molecule/search?q={query}` | Free-text molecule search |
| `/target/{chembl_id}` | Get target by ChEMBL ID |
| `/target/search?q={query}` | Free-text target search |
| `/activity?molecule_chembl_id={id}` | Activities for a molecule |
| `/activity?target_chembl_id={id}` | Activities for a target |
| `/mechanism?molecule_chembl_id={id}` | Mechanism of action |
| `/drug_indication?molecule_chembl_id={id}` | Drug indications |
| `/similarity/{smiles}/{threshold}` | Similarity search (threshold 40-100) |
| `/substructure/{smiles}` | Substructure search |

## Common Parameters

- `format=json` or `.json` — request JSON explicitly; do not assume the default negotiated format
- `limit` — results per page (default 20, max 1000)
- `offset` — pagination offset
- `order_by` — sort field (prefix `-` for descending)
- `only` — return only specified fields (comma-separated)

### Filtering operators (append to field names)
`__exact`, `__icontains`, `__gt`, `__gte`, `__lt`, `__lte`, `__in`, `__isnull`, `__startswith`, `__range`, `__regex`

## Example Calls

```
# Get molecule by ID
/molecule/CHEMBL25.json

# Search molecules by name
/molecule/search?q=aspirin&format=json

# Activities for a target with potency filter
/activity?target_chembl_id=CHEMBL240&pchembl_value__gte=6&format=json&limit=100

# Similarity search (80% threshold)
/similarity/CC(%3DO)Oc1ccccc1C(%3DO)O/80.json

# Approved drugs only
/molecule?max_phase=4&format=json

# Mechanism of action
/mechanism?molecule_chembl_id=CHEMBL25&format=json
```

## Response Format (molecule collection)
```json
{
  "page_meta": {"limit": 20, "offset": 0, "total_count": 150},
  "molecules": [{
    "molecule_chembl_id": "CHEMBL25",
    "pref_name": "ASPIRIN",
    "max_phase": 4,
    "molecule_properties": {
      "full_mwt": 180.16, "full_molformula": "C9H8O4",
      "alogp": 1.31, "hba": 3, "hbd": 1, "psa": 63.60
    },
    "molecule_structures": {
      "canonical_smiles": "CC(=O)Oc1ccccc1C(=O)O",
      "standard_inchi_key": "BSYNRYMUTXBXSQ-UHFFFAOYSA-N"
    }
  }]
}
```

## Rate Limits
No strict limit. Keep under ~10 req/sec. No auth required.

Single `/molecule/{id}.json` returns the molecule object directly, while list/search
responses include `page_meta` and `molecules`. Follow `page_meta.next`. Molecular
weights can be numeric strings; retain activity units, relation qualifiers and assay
type rather than treating every reported value as comparable binding affinity.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

