---
id: sciref-database-lookup-ena
name: "Scientific Ref: European Nucleotide Archive (ENA) API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): European Nucleotide Archive (ENA) API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup ena"
  - "european nucleotide archive (ena) api reference"
keywords:
  - "database"
  - "lookup"
  - "ena"
  - "specialized"
  - "scientific"
  - "reference"
  - "european"
---

# European Nucleotide Archive (ENA) API Reference

## Overview
The ENA is Europe's primary nucleotide sequence repository, part of the International Nucleotide Sequence Database Collaboration (INSDC) alongside NCBI GenBank and DDBJ. It stores raw sequencing reads, assembled sequences, genome assemblies, and associated metadata. ENA provides five complementary APIs for different access patterns.

## 1. ENA Portal API (Advanced Search)

### Base URL
```
https://www.ebi.ac.uk/ena/portal/api
```

No authentication required. All endpoints are public.

### Key Endpoints

#### Search records
```
GET /search?result={result_type}&query={query}&fields={fields}&limit={N}&format={format}
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `result` | string | **Required.** Data type to search. See Result Types below. |
| `query` | string | Search query using ENA query syntax. |
| `fields` | string | Comma-separated list of fields to return. Use `/returnFields` to see available fields per result type. |
| `limit` | int | Bound results explicitly; 0 or omission can request the entire result set. |
| `format` | string | `json`, `tsv` (default). |

**Query syntax:**
```
tax_id=9606 AND description="*hemoglobin*"
tax_id=9606 AND library_strategy="RNA-Seq"
accession="PRJEB40665"
scientific_name="Escherichia coli" AND dataclass="STD"
country="United Kingdom" AND first_public>2024-01-01
```

Operators: `=`, `!=`, `>`, `<`, `>=`, `<=`. Use `AND`, `OR`, `NOT`. Wildcards: `*`. Enclose values with spaces in double quotes.

**Example -- search human RNA-Seq runs:**
```
https://www.ebi.ac.uk/ena/portal/api/search?result=read_run&query=tax_id%3D9606%20AND%20library_strategy%3D%22RNA-Seq%22&fields=run_accession,experiment_accession,sample_accession,study_accession,instrument_platform,library_strategy,read_count,base_count&limit=5&format=json
```

**Example -- search nucleotide sequences by organism:**
```
https://www.ebi.ac.uk/ena/portal/api/search?result=sequence&query=tax_id%3D9606%20AND%20description%3D%22*hemoglobin*%22&fields=accession,description,tax_id,scientific_name,base_count&limit=5&format=json
```

**Response:**
```json
[
  {
    "accession": "AA126503",
    "description": "zk94h05.s1 Soares_pregnant_uterus_NbHPU Homo sapiens cDNA clone ...",
    "tax_id": "9606"
  }
]
```

#### Count records
```
GET /count?result={result_type}&query={query}
```

Returns a plain integer count.

**Example:**
```
https://www.ebi.ac.uk/ena/portal/api/count?result=read_run&query=tax_id%3D9606%20AND%20library_strategy%3D%22RNA-Seq%22
```

#### List available result types
```
GET /results?format=json
```

#### List searchable fields for a result type
```
GET /searchFields?result={result_type}
```

#### List returnable fields for a result type
```
GET /returnFields?result={result_type}
```

### Result Types

| Result Type | Description |
|-------------|-------------|
| `sequence` | Nucleotide sequences |
| `coding` | Coding sequences (CDS) |
| `noncoding` | Non-coding sequences |
| `read_run` | Raw sequencing reads (runs) |
| `read_experiment` | Sequencing experiments |
| `read_study` | Studies for raw reads |
| `analysis` | Analyses |
| `analysis_study` | Studies for analyses |
| `assembly` | Genome assemblies |
| `sample` | Samples |
| `study` | Studies |
| `taxon` | Taxonomic classification |
| `wgs_set` | Genome assembly contig sets (WGS) |
| `tsa_set` | Transcriptome assembly contig sets (TSA) |
| `tls_set` | Targeted locus study contig sets (TLS) |

---

## 2. ENA Browser API (Record Retrieval)

### Base URL
```
https://www.ebi.ac.uk/ena/browser/api
```

Use this for direct retrieval of records by accession number.

### Key Endpoints

#### Retrieve record in XML format
```
GET /xml/{accession}
```

**Example:**
```
https://www.ebi.ac.uk/ena/browser/api/xml/PRJEB40665
https://www.ebi.ac.uk/ena/browser/api/xml/SRR12345678
https://www.ebi.ac.uk/ena/browser/api/xml/ERS1234567
```

#### Retrieve record in EMBL flat file format
```
GET /embl/{accession}
```

**Example:**
```
https://www.ebi.ac.uk/ena/browser/api/embl/AY585947
```

Supports `?lineLimit=N` to truncate long records.

#### Retrieve sequence in FASTA format
```
GET /fasta/{accession}
```

**Example:**
```
https://www.ebi.ac.uk/ena/browser/api/fasta/AY585947
```

### Response Formats

| Endpoint | Format | Use case |
|----------|--------|----------|
| `/xml/{accession}` | XML | Full structured metadata for studies, samples, experiments, runs |
| `/embl/{accession}` | EMBL flat file | Annotated sequences with features |
| `/fasta/{accession}` | FASTA | Raw nucleotide/protein sequences |

### Accession Types

| Prefix | Entity | Example |
|--------|--------|---------|
| `PRJEB` / `PRJNA` / `PRJDB` | Study/Project | `PRJEB40665` |
| `ERX` / `SRX` / `DRX` | Experiment | `ERX1234567` |
| `ERS` / `SRS` / `DRS` | Sample | `ERS1234567` |
| `ERR` / `SRR` / `DRR` | Run | `ERR1234567` |
| `GCA` | Genome assembly | `GCA_000001405.29` |
| Standard INSDC | Sequence | `AY585947`, `M10051` |

---

## 3. ENA Taxonomy REST API

### Base URL
```
https://www.ebi.ac.uk/ena/taxonomy/rest
```

### Key Endpoints

#### Lookup by taxonomy ID
```
GET /tax-id/{taxId}
```

**Example:**
```
https://www.ebi.ac.uk/ena/taxonomy/rest/tax-id/9606
```

**Response:**
```json
{
  "taxId": 9606,
  "scientificName": "Homo sapiens",
  "commonName": "human",
  "formalName": true,
  "rank": "species",
  "division": "HUM",
  "lineage": "Eukaryota; Metazoa; Chordata; Craniata; Vertebrata; ...; Homo; ",
  "geneticCode": "1",
  "mitochondrialGeneticCode": "2",
  "submittable": true,
  "binomial": true,
  "metagenome": false,
  "otherNames": [
    {"nameClass": "authority", "name": "Linnaeus, 1758"},
    {"nameClass": "genbank common name", "name": "human"}
  ]
}
```

#### Search by scientific name
```
GET /scientific-name/{name}
```

**Example:**
```
https://www.ebi.ac.uk/ena/taxonomy/rest/scientific-name/Homo%20sapiens
```

Returns an array of matching taxonomy records.

#### Search by common name
```
GET /any-name/{name}
```

**Example:**
```
https://www.ebi.ac.uk/ena/taxonomy/rest/any-name/human
```

#### Suggest names (autocomplete)
```
GET /suggest-for-submission/{partialName}
```

**Example:**
```
https://www.ebi.ac.uk/ena/taxonomy/rest/suggest-for-submission/Homo%20sap
```

---

## 4. ENA Cross Reference Service

### Base URL
```
https://www.ebi.ac.uk/ena/xref/rest
```

Retrieves links between ENA records and external databases (UniProt, PDB, PubMed, etc.).

### Key Endpo

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

