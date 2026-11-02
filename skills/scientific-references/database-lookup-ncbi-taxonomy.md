---
id: sciref-database-lookup-ncbi-taxonomy
name: "Scientific Ref: NCBI Taxonomy API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): NCBI Taxonomy API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup ncbi taxonomy"
  - "ncbi taxonomy api reference"
keywords:
  - "database"
  - "lookup"
  - "ncbi"
  - "taxonomy"
  - "specialized"
  - "scientific"
  - "reference"
---

# NCBI Taxonomy API Reference

## Overview
Taxonomic classification data (names, lineages, ranks) for all organisms in NCBI databases. Accessible via E-utilities with `db=taxonomy`.

## Base URL
```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils/
```

## Authentication
- **API key** (recommended): Append `&api_key=YOUR_KEY` (register at ncbi.nlm.nih.gov/account).
- Without key: 3 req/sec. With key: 10 req/sec.
- Provide `tool` and `email` parameters.

## Key Endpoints

### 1. ESearch -- Search taxonomy by name
```
GET esearch.fcgi?db=taxonomy&term=QUERY&retmode=json
```
| Param | Description |
|-------|-------------|
| `term` | Organism name, common name, or taxid. Fields: `[Scientific Name]`, `[Common Name]`, `[All Names]`, `[Rank]` |
| `retmax` | Max IDs returned (default 20) |

**Example -- search by scientific name:**
```
GET esearch.fcgi?db=taxonomy&term=Homo+sapiens[Scientific Name]&retmode=json
```
Response:
```json
{
  "esearchresult": {
    "count": "1",
    "idlist": ["9606"]
  }
}
```

**Example -- search by common name:**
```
GET esearch.fcgi?db=taxonomy&term=dog[Common Name]&retmode=json
```

### 2. EFetch -- Retrieve full taxonomy records
```
GET efetch.fcgi?db=taxonomy&id=TAXIDS&retmode=xml
```
Note: Taxonomy EFetch only supports XML output.

**Example -- fetch human taxonomy (taxid 9606):**
```
GET efetch.fcgi?db=taxonomy&id=9606&retmode=xml
```
Response (abbreviated XML):
```xml
<TaxaSet>
  <Taxon>
    <TaxId>9606</TaxId>
    <ScientificName>Homo sapiens</ScientificName>
    <OtherNames>
      <CommonName>human</CommonName>
    </OtherNames>
    <Rank>species</Rank>
    <Division>Primates</Division>
    <GeneticCode><GCId>1</GCId><GCName>Standard</GCName></GeneticCode>
    <MitoGeneticCode><MGCId>2</MGCId><MGCName>Vertebrate Mitochondrial</MGCName></MitoGeneticCode>
    <Lineage>cellular organisms; Eukaryota; Opisthokonta; Metazoa; ... ; Hominidae; Homo</Lineage>
    <LineageEx>
      <Taxon><TaxId>131567</TaxId><ScientificName>cellular organisms</ScientificName><Rank>no rank</Rank></Taxon>
      <Taxon><TaxId>2759</TaxId><ScientificName>Eukaryota</ScientificName><Rank>superkingdom</Rank></Taxon>
      <!-- ... each ancestor node ... -->
    </LineageEx>
  </Taxon>
</TaxaSet>
```

### 3. ESummary -- Brief taxonomy summaries
```
GET esummary.fcgi?db=taxonomy&id=TAXIDS&retmode=json
```
**Example -- multiple taxa:**
```
GET esummary.fcgi?db=taxonomy&id=9606,10090,7227&retmode=json
```
Response includes: lowercase JSON keys `scientificname`, `commonname`, `rank`, `division`, `taxid`, `genus`, `species` (XML uses different capitalization).

### 4. ELink -- Cross-link taxonomy to other databases
```
GET elink.fcgi?dbfrom=taxonomy&db=protein&id=9606&term=insulin
```
Find all protein records for a given taxid, optionally filtered by keyword.

## Common Search Patterns
```
# All species under a genus
term=Drosophila[Next Level] AND species[Rank]

# Search Taxonomy by taxid directly
term=9606[Taxonomy ID]

# By rank
term=Mammalia[Scientific Name] AND class[Rank]

# Taxonomy subtree search
term=9605[Subtree]
```

`txid9606[Organism:exp]` is a sequence-database search expression, not a Taxonomy field. Discover Taxonomy search fields with `einfo.fcgi?db=taxonomy&retmode=json`; resolve scientific names to taxids before subtree searches.

## Useful Cross-references
| Link | Description |
|------|-------------|
| `taxonomy_protein` | All proteins for a taxon |
| `taxonomy_gene` | All genes for a taxon |
| `taxonomy_nuccore` | All nucleotide records for a taxon |
| `taxonomy_genome` | Genome assemblies for a taxon |

## Rate Limits
- Without API key: 3 requests/second
- With API key: 10 requests/second
- EFetch supports multiple taxids in a single call (comma-separated)

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

