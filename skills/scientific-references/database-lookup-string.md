---
id: sciref-database-lookup-string
name: "Scientific Ref: STRING REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): STRING REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup string"
  - "string rest api"
keywords:
  - "database"
  - "lookup"
  - "string"
  - "specialized"
  - "scientific"
  - "reference"
---

# STRING REST API

## Base URL

```
https://string-db.org/api
```

## URL Pattern

```
/api/{output_format}/{method}
```

- **output_format**: `json`, `tsv`, `tsv-no-header`, `image`, `svg` (not all formats for all endpoints)
- **method**: endpoint name (see below)

## Authentication

No API key required. All endpoints are public.

## Key Endpoints

### 1. Resolve protein identifiers

Map protein names/identifiers to STRING internal IDs. Always do this first to get canonical STRING IDs.

```
GET /api/json/get_string_ids?identifiers={query}&species={taxid}
```

| Parameter    | Type   | Description |
|-------------|--------|-------------|
| `identifier` | string | **Required.** Protein name, gene symbol, or external ID. |
| `species`    | int    | NCBI taxonomy ID (9606 = human, 10090 = mouse). Recommended to avoid ambiguity. |

**Example:**
```
https://string-db.org/api/json/get_string_ids?identifiers=TP53&species=9606
```

**Response:**
```json
[
  {
    "stringId": "9606.ENSP00000269305",
    "preferredName": "TP53",
    "ncbiTaxonId": 9606,
    "taxonName": "Homo sapiens",
    "annotation": "Cellular tumor antigen p53; ..."
  }
]
```

---

### 2. Get interaction partners (network)

```
GET /api/json/interaction_partners?identifiers={proteins}&species={taxid}
```

| Parameter           | Type   | Description |
|--------------------|--------|-------------|
| `identifiers`       | string | **Required.** Protein name(s). Use `%0d` (newline) to separate multiple. |
| `species`           | int    | NCBI taxonomy ID. |
| `limit`             | int    | Max number of interaction partners to return (per input protein). |
| `required_score`    | int    | Minimum combined score (0-1000). Default: 400. Common thresholds: 400 (medium), 700 (high), 900 (highest). |
| `network_type`      | string | `functional` (default, all associations) or `physical` (predicted physical associations, which need not prove direct binding). |

**Example:**
```
https://string-db.org/api/json/interaction_partners?identifiers=TP53&species=9606&limit=10&required_score=900
```

**Response:**
```json
[
  {
    "stringId_A": "9606.ENSP00000269305",
    "stringId_B": "9606.ENSP00000261842",
    "preferredName_A": "TP53",
    "preferredName_B": "MDM2",
    "ncbiTaxonId": 9606,
    "score": 0.999,
    "nscore": 0,
    "fscore": 0,
    "pscore": 0,
    "ascore": 0.93,
    "escore": 0.994,
    "dscore": 0.9,
    "tscore": 0.981
  }
]
```

Score channels: `nscore` (neighborhood), `fscore` (fusion), `pscore` (phylogenetic co-occurrence), `ascore` (co-expression), `escore` (experimental), `dscore` (database/curated), `tscore` (text mining).

---

### 3. Get network interactions between a set of proteins

```
GET /api/json/network?identifiers={proteins}&species={taxid}
```

| Parameter         | Type   | Description |
|------------------|--------|-------------|
| `identifiers`     | string | **Required.** Protein names separated by `%0d` (newline-encoded). |
| `species`         | int    | NCBI taxonomy ID. |
| `required_score`  | int    | Minimum combined score (0-1000). |
| `network_type`    | string | `functional` or `physical`. |
| `add_nodes`       | int    | Number of additional interactors to add (expands the network). |

**Example — network among a set of proteins:**
```
https://string-db.org/api/json/network?identifiers=TP53%0dBRCA1%0dATM%0dCHEK2%0dMDM2&species=9606&required_score=700
```

Returns all pairwise interactions among the input set.

---

### 4. Network image

```
GET /api/image/network?identifiers={proteins}&species={taxid}
GET /api/svg/network?identifiers={proteins}&species={taxid}
```

Returns a PNG image or SVG of the interaction network.

**Example:**
```
https://string-db.org/api/image/network?identifiers=TP53%0dBRCA1%0dMDM2&species=9606
```

---

### 5. Functional enrichment analysis

Perform Gene Ontology, KEGG pathway, and other enrichment analysis on a set of proteins.

```
GET /api/json/enrichment?identifiers={proteins}&species={taxid}
```

| Parameter     | Type   | Description |
|--------------|--------|-------------|
| `identifiers` | string | **Required.** Newline-separated (`%0d`) protein names. |
| `species`     | int    | NCBI taxonomy ID. |

**Example:**
```
https://string-db.org/api/json/enrichment?identifiers=TP53%0dBRCA1%0dATM%0dCHEK2%0dCDK2%0dCDKN1A&species=9606
```

**Response:**
```json
[
  {
    "category": "Process",
    "term": "GO:0006974",
    "description": "cellular response to DNA damage stimulus",
    "number_of_genes": 6,
    "number_of_genes_in_background": 781,
    "ncbiTaxonId": 9606,
    "inputGenes": "TP53,BRCA1,ATM,CHEK2,CDK2,CDKN1A",
    "preferredNames": "TP53,BRCA1,ATM,CHEK2,CDK2,CDKN1A",
    "p_value": 1.2e-12,
    "fdr": 5.6e-10
  }
]
```

Categories include: `Process` (GO Biological Process), `Function` (GO Molecular Function), `Component` (GO Cellular Component), `KEGG`, `Pfam`, `InterPro`, `SMART`, `Keyword` (UniProt), `Reactome`, `WikiPathways`, `HPO` (Human Phenotype Ontology).

---

### 6. Get protein annotations/info

```
GET /api/json/get_string_ids?identifiers={proteins}&species={taxid}
```

Maps arbitrary names to STRING IDs with annotation text.

**Example:**
```
https://string-db.org/api/json/get_string_ids?identifiers=CDK2%0dp53&species=9606
```

**Response:**
```json
[
  {
    "queryIndex": 0,
    "queryItem": "CDK2",
    "stringId": "9606.ENSP00000266970",
    "ncbiTaxonId": 9606,
    "taxonName": "Homo sapiens",
    "preferredName": "CDK2",
    "annotation": "Cyclin-dependent kinase 2; ..."
  }
]
```

---

### 7. Get homology / best-hit in another species

```
GET /api/json/homology_best?identifiers={proteins}&species={taxid}&species_b={taxid_b}
```

| Parameter   | Type | Description |
|------------|------|-------------|
| `identifiers` | string | Source protein(s). |
| `species`     | int | Source species. |
| `species_b`   | int | Target species for homolog lookup. |

**Example:**
```
https://string-db.org/api/json/homology_best?identifiers=TP53&species=9606&species_b=10090
```

---

### 8. PPI enrichment (is my set more connected than expected?)

```
GET /api/json/ppi_enrichment?identifiers={proteins}&species={taxid}
```

**Example:**
```
https://string-db.org/api/json/ppi_enrichment?identifiers=TP53%0dBRCA1%0dATM%0dCHEK2&species=9606
```

**Response:**
```json
[
  {
    "number_of_nodes": 4,
    "number_of_edges": 6,
    "average_node_degree": 3.0,
    "local_clustering_coefficient": 1.0,
    "expected_number_of_edges": 1,
    "p_value": 0

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

