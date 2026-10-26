---
id: sciref-database-lookup-ensembl
name: "Scientific Ref: Ensembl REST API"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (database-lookup): Ensembl REST API"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "database lookup ensembl"
  - "ensembl rest api"
keywords:
  - "database"
  - "lookup"
  - "ensembl"
  - "specialized"
  - "scientific"
  - "reference"
---

# Ensembl REST API

## Base URL

```
https://rest.ensembl.org
```

For the Ensembl Genomes (plants, fungi, bacteria, protists, metazoa):
```
https://rest.ensembl.org
```
(Same base; Ensembl Genomes was merged into the main REST API.)

For the GRCh37 (hg19) archive:
```
https://grch37.rest.ensembl.org
```

## Authentication

No API key required. All endpoints are public.

## Common Headers

All requests should include:
```
Content-Type: application/json
```

The API uses content negotiation. Append `?content-type=application/json` to GET requests, or set the `Accept` header.

## Key Endpoints

### 1. Gene lookup by symbol

```
GET /lookup/symbol/{species}/{symbol}?content-type=application/json
```

| Parameter   | Type   | Description |
|------------|--------|-------------|
| `species`   | string | **Required.** Species name (e.g., `homo_sapiens`, `mus_musculus`). |
| `symbol`    | string | **Required.** Gene symbol (e.g., `TP53`, `BRCA1`). |
| `expand`    | int    | Set to `1` to include transcripts, translations, exons. |

**Example:**
```
https://rest.ensembl.org/lookup/symbol/homo_sapiens/TP53?content-type=application/json
https://rest.ensembl.org/lookup/symbol/homo_sapiens/BRCA1?content-type=application/json;expand=1
```

**Response:**
```json
{
  "id": "ENSG00000141510",
  "display_name": "TP53",
  "description": "tumor protein p53 [Source:HGNC Symbol;Acc:HGNC:11998]",
  "species": "homo_sapiens",
  "object_type": "Gene",
  "biotype": "protein_coding",
  "assembly_name": "GRCh38",
  "seq_region_name": "17",
  "start": 7661779,
  "end": 7687538,
  "strand": -1,
  "source": "ensembl_havana",
  "logic_name": "ensembl_havana_gene_homo_sapiens",
  "version": 16,
  "Transcript": [...]
}
```

---

### 2. Gene/feature lookup by Ensembl ID

```
GET /lookup/id/{id}?content-type=application/json
```

| Parameter | Type   | Description |
|-----------|--------|-------------|
| `id`      | string | **Required.** Ensembl stable ID (gene, transcript, protein, exon). |
| `expand`  | int    | Set to `1` to include child objects (transcripts for genes, etc.). |
| `db_type` | string | Database type: `core`, `otherfeatures`, `cdna`, `rnaseq`. |

**Example:**
```
https://rest.ensembl.org/lookup/id/ENSG00000141510?content-type=application/json;expand=1
https://rest.ensembl.org/lookup/id/ENST00000269305?content-type=application/json
https://rest.ensembl.org/lookup/id/ENSP00000269305?content-type=application/json
```

---

### 3. Batch lookup (POST, up to 1000 IDs)

```
POST /lookup/id
Content-Type: application/json

{ "ids": ["ENSG00000141510", "ENSG00000012048", "ENSG00000157764"] }
```

**Example response:** Returns a map keyed by ID:
```json
{
  "ENSG00000141510": {
    "id": "ENSG00000141510",
    "display_name": "TP53",
    ...
  },
  "ENSG00000012048": { ... }
}
```

---

### 4. Sequence retrieval

```
GET /sequence/id/{id}?content-type=application/json
```

| Parameter     | Type   | Description |
|--------------|--------|-------------|
| `id`          | string | Ensembl stable ID (gene, transcript, or protein). |
| `type`        | string | `genomic`, `cdna`, `cds`, `protein`. Default varies by object type. |
| `format`      | string | `fasta`; select JSON with the content-type/Accept header. |
| `expand_3prime` | int  | Expand 3' end by N bases. |
| `expand_5prime` | int  | Expand 5' end by N bases. |
| `mask`        | string | `soft` (lowercase repeats) or `hard` (N-mask repeats). |

**Examples:**

Protein sequence:
```
https://rest.ensembl.org/sequence/id/ENSP00000269305?content-type=application/json
```

CDS sequence:
```
https://rest.ensembl.org/sequence/id/ENST00000269305?type=cds&content-type=application/json
```

Genomic sequence with flanking:
```
https://rest.ensembl.org/sequence/id/ENSG00000141510?type=genomic&expand_5prime=1000&expand_3prime=500&content-type=application/json
```

FASTA format:
```
https://rest.ensembl.org/sequence/id/ENSP00000269305?content-type=text/x-fasta
```

**Response (JSON):**
```json
{
  "id": "ENSP00000269305",
  "seq": "MEEPQSDPSVEPPLSQETFSDL...",
  "molecule": "protein",
  "desc": "chromosome:GRCh38:17:7661779:7687538:-1"
}
```

---

### 5. Sequence by region

```
GET /sequence/region/{species}/{region}?content-type=application/json
```

Region format: `chromosome:start..end` or `chromosome:start..end:strand`

**Example:**
```
https://rest.ensembl.org/sequence/region/homo_sapiens/17:7661779..7662000:1?content-type=application/json
```

---

### 6. Variant annotation (VEP -- Variant Effect Predictor)

**By HGVS notation:**
```
GET /vep/{species}/hgvs/{hgvs_notation}?content-type=application/json
```

**Example:**
```
https://rest.ensembl.org/vep/homo_sapiens/hgvs/ENST00000269305.9:c.817C>T?content-type=application/json
https://rest.ensembl.org/vep/homo_sapiens/hgvs/17:g.7675088C>G?CADD=1&content-type=application/json
```

`CADD=1` is how you get `cadd_phred`. Without it the field is absent.
Verified 2026-09-11: `17:g.7675088C>G` is `missense_variant` / TP53 /
`cadd_phred` **29.4**. The older worked example `17:g.7674220G>A` is
HTTP 400 — the reference at 7674220 is `C`, not `G`.

**By genomic region:**
```
GET /vep/{species}/region/{region}/{allele}?content-type=application/json
```

**Example:**
```
https://rest.ensembl.org/vep/homo_sapiens/region/17:7675088-7675088:1/G?CADD=1&content-type=application/json
```

The path carries the **alt** only. VEP reads the reference from the
assembly. `17:7675088-7675088:1/G` returns `allele_string: C/G` even if
you thought the ref was `A`. Compare `allele_string` to the alleles you
meant, or use `/hgvs/` (which 400s on a wrong ref).

**By rsID:**
```
GET /vep/{species}/id/{rsid}?content-type=application/json
```

**Example:**
```
https://rest.ensembl.org/vep/homo_sapiens/id/rs28934578?CADD=1&content-type=application/json
https://rest.ensembl.org/vep/homo_sapiens/id/rs699?content-type=application/json
```

`rs28934578` is multi-allelic (`C/A/G/T`). `most_severe_consequence` is
one label across **every** transcript (117 here, vs 39 on the single-alt
region call). Do not quote it as the consequence of one allele.

**VEP Response:**
```json
[
  {
    "input": "17:g.7675088C>G",
    "assembly_name": "GRCh38",
    "seq_region_name": "17",
    "start": 7675088,
    "end": 7675088,
    "strand": 1,
    "allele_string": "C/G",
    "most_severe_consequence": "missense_variant",
    "transcript_consequences": [
      {
        "gene_id": "ENSG00000141510",
        "gene_symbol": "TP53",
        "transcript_id": "ENST0000026

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

