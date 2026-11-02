---
id: sciref-biopython-databases
name: "Scientific Ref: Database Access with Bio.Entrez"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (biopython): Database Access with Bio.Entrez"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "biopython databases"
  - "database access with bio.entrez"
keywords:
  - "biopython"
  - "databases"
  - "specialized"
  - "scientific"
  - "reference"
  - "database"
  - "access"
---

# Database Access with Bio.Entrez

## Overview

Bio.Entrez provides programmatic access to NCBI's Entrez databases, including PubMed, GenBank, Gene, Protein, Nucleotide, and many others. It provides request construction, process-local pacing, retries, and XML parsing. Applications must still coordinate shared IP/API-key limits across workers and validate database-specific results.

## Setup and Configuration

### Email Address (Required)

NCBI requires an email address to track usage and contact users if issues arise:

```python
from Bio import Entrez

# Always set your email
Entrez.email = "your.email@example.com"

# For reusable software, set a stable tool name and register
# the tool/email pair with NCBI.
Entrez.tool = "your_tool_name"
```

### API Key (Recommended)

Using an API key increases E-utilities rate limits from 3 to 10 requests per second. Register at https://www.ncbi.nlm.nih.gov/account/settings/ and read only `NCBI_API_KEY` from the environment — do not hardcode it and do not load unrelated environment variables:

```python
import os

# Check NCBI_API_KEY from the environment (or export it before running)
if api_key := os.environ.get("NCBI_API_KEY"):
    Entrez.api_key = api_key
```

### Rate Limiting

For serial calls in one process, Biopython paces requests at the standard limits:
- **Without API key**: 3 requests per second
- **With API key**: 10 requests per second

The module handles ordinary request pacing automatically and retries transient HTTP 5XX failures. For large jobs, use Entrez history (`usehistory="y"` / `WebEnv` / `query_key`) and batch requests rather than making one request per record. NCBI also recommends scheduling large jobs for weekends or between 9:00 PM and 5:00 AM Eastern time.

## Core Entrez Functions

### EInfo - Database Information

Get information about available databases and their statistics:

```python
# List all databases
handle = Entrez.einfo()
result = Entrez.read(handle)
handle.close()
print(result["DbList"])

# Get information about a specific database
handle = Entrez.einfo(db="pubmed")
result = Entrez.read(handle)
handle.close()
print(result["DbInfo"]["Description"])
print(result["DbInfo"]["Count"])  # Number of records
```

### ESearch - Search Databases

Search for records and retrieve their IDs:

```python
# Search PubMed
handle = Entrez.esearch(db="pubmed", term="biopython")
result = Entrez.read(handle)
handle.close()

id_list = result["IdList"]
count = result["Count"]
print(f"Found {count} results")
print(f"Retrieved IDs: {id_list}")
```

### Advanced ESearch Parameters

```python
# Search with additional parameters
handle = Entrez.esearch(
    db="pubmed",
    term="biopython[Title]",
    retmax=100,           # Return up to 100 IDs
    sort="relevance",     # Sort by relevance
    reldate=365,          # Only results from last year
    datetype="pdat"       # Use publication date
)
result = Entrez.read(handle)
handle.close()
```

### ESummary - Get Record Summaries

Retrieve summary information for a list of IDs:

```python
# Get summaries for multiple records
handle = Entrez.esummary(db="pubmed", id="19304878,18606172")
results = Entrez.read(handle)
handle.close()

for record in results:
    print(f"Title: {record['Title']}")
    print(f"Authors: {record['AuthorList']}")
    print(f"Journal: {record['Source']}")
    print()
```

### EFetch - Retrieve Full Records

Fetch complete records in various formats:

```python
# Fetch a GenBank record
handle = Entrez.efetch(db="nucleotide", id="EU490707", rettype="gb", retmode="text")
record_text = handle.read()
handle.close()

# Parse with SeqIO
from Bio import SeqIO
handle = Entrez.efetch(db="nucleotide", id="EU490707", rettype="gb", retmode="text")
record = SeqIO.read(handle, "genbank")
handle.close()
print(record.description)
```

### EFetch Return Types

Different databases support different return types:

**Nucleotide/Protein:**
- `rettype="fasta"` - FASTA format
- `rettype="gb"` - GenBank text for nucleotide records (parse with `SeqIO`, `"genbank"`)
- `rettype="gp"` - GenPept format (proteins)

**PubMed:**
- `rettype="medline"` - MEDLINE format
- `rettype="abstract"` - Abstract text

**Common modes:**
- `retmode="text"` - Plain text
- `retmode="xml"` - XML format

### ELink - Find Related Records

Find links between records in different databases:

```python
# Find protein records linked to a nucleotide record
with Entrez.esearch(db="nuccore", term="EU490707[Accession]", retmax=1) as handle:
    source_ids = Entrez.read(handle)["IdList"]
if not source_ids:
    raise ValueError("Sequence accession was not found")
handle = Entrez.elink(dbfrom="nuccore", db="protein", id=source_ids)
result = Entrez.read(handle)
handle.close()

# Extract linked IDs
for linkset in result[0]["LinkSetDb"]:
    if linkset["LinkName"] == "nuccore_protein":
        protein_ids = [link["Id"] for link in linkset["Link"]]
        print(f"Linked protein IDs: {protein_ids}")
```

### EPost - Upload ID Lists

Upload large lists of IDs to the server for later use:

```python
# Post IDs to server
id_list = ["19304878", "18606172", "16403221"]
handle = Entrez.epost(db="pubmed", id=",".join(id_list))
result = Entrez.read(handle)
handle.close()

# Get query_key and WebEnv for later use
query_key = result["QueryKey"]
webenv = result["WebEnv"]

# Use in subsequent queries
handle = Entrez.efetch(
    db="pubmed",
    query_key=query_key,
    WebEnv=webenv,
    rettype="medline",
    retmode="text"
)
```

### Counts Across Selected Databases

`Entrez.egquery` was removed in Biopython 1.87 because its NCBI service stopped
working. Use explicit, serial ESearch calls for the databases actually needed:

```python
for db in ("pubmed", "nucleotide", "protein"):
    with Entrez.esearch(db=db, term="biopython", retmax=0) as handle:
        result = Entrez.read(handle)
    print(db, int(result["Count"]))
```

### ESpell - Spelling Suggestions

Get spelling suggestions for search terms:

```python
handle = Entrez.espell(db="pubmed", term="biopythn")
result = Entrez.read(handle)
handle.close()

print(f"Original: {result['Query']}")
print(f"Suggestion: {result['CorrectedQuery']}")
```

## Working with Different Databases

### PubMed

```python
# Search for articles
handle = Entrez.esearch(db="pubmed", term="cancer genomics", retmax=10)
result = Entrez.read(handle)
handle.close()

# Fetch abstracts
handle = Entrez.efetch(
    db="pubmed",
    id=result["IdList"],
    rettype="medline",
    retmode="text"
)
records = hand

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

