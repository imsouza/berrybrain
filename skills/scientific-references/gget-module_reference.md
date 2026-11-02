---
id: sciref-gget-module-reference
name: "Scientific Ref: gget Module Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gget): gget Module Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gget module reference"
keywords:
  - "gget"
  - "module"
  - "reference"
  - "specialized"
  - "scientific"
---

# gget Module Reference

Selected CLI parameters and Python differences for gget 0.30.8. Source-checked against the [released implementation](https://github.com/scverse/gget/tree/v0.30.8/gget); use `gget <module> --help` and `inspect.signature(gget.<module>)` for the full surface. [Database contracts](database_info.md) document return fields and completeness limits.

## Reference & Gene Information Modules

### gget ref
Retrieve Ensembl reference genome FTPs and metadata.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `species` | str | Species in Genus_species format or shortcuts ('human', 'mouse') | Required |
| `-w/--which` | str/list | File types to return: gtf, cdna, dna, cds, cdrna, pep | All |
| `-r/--release` | int | Ensembl release number | Latest |
| `-od/--out_dir` | str | Output directory path | None |
| `-o/--out` | str | JSON file path for results | None |
| `-l/--list_species` | flag | List available vertebrate species | False |
| `-liv/--list_iv_species` | flag | List available invertebrate species | False |
| `-ftp` | flag | Return only FTP links | False |
| `-d/--download` | flag | CLI-only download (requires curl; Python returns links) | False |
| `-q/--quiet` | flag | Suppress progress information | False |

**Returns:** JSON containing FTP links, Ensembl release numbers, release dates, file sizes

---

### gget search
Search for genes by name or description in Ensembl.
Search includes Ensembl synonyms in current gget versions.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `searchwords` | str/list | Search terms (case-insensitive) | Required |
| `-s/--species` | str | Target species or core database name | Required |
| `-r/--release` | int | Ensembl release number | Latest |
| `-t/--id_type` | str | Return 'gene' or 'transcript' | 'gene' |
| `-ao/--andor` | str | 'or' (ANY term) or 'and' (ALL terms) | 'or' |
| `-l/--limit` | int | Maximum results to return | None |
| `-o/--out` | str | Output file path (CSV/JSON) | None |
| `wrap_text` | bool | Python-only wrapped text display for wide results | False |

**Returns:** ensembl_id, gene_name, ensembl_description, ext_ref_description, biotype, synonym, url

---

### gget info
Get comprehensive gene/transcript metadata from Ensembl, UniProt, and NCBI.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `ens_ids` | str/list | Ensembl IDs (WormBase, Flybase also supported) | Required |
| `-o/--out` | str | Output file path (CSV/JSON) | None |
| `-n/--ncbi` | bool | Disable NCBI data retrieval | False |
| `-u/--uniprot` | bool | Disable UniProt data retrieval | False |
| `-pdb` | bool | Include PDB identifiers | False |
| `-csv` | flag | Return CSV format (CLI) | False |
| `-q/--quiet` | flag | Suppress progress display | False |

**Python-specific:**
- `save=True`: Save output to current directory
- `wrap_text=True`: Format dataframe with wrapped text

**Note:** Processing >1000 IDs simultaneously may cause server errors.

**Returns:** DataFrame indexed by query Ensembl ID, with `uniprot_id`, `ncbi_gene_id`, `primary_gene_name`, `ensembl_gene_name`, annotations and transcript metadata. Preserve the index on export.

---

### gget seq
Retrieve nucleotide or amino acid sequences in FASTA format.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `ens_ids` | str/list | Ensembl identifiers | Required |
| `-o/--out` | str | Output file path | stdout |
| `-t/--translate` | flag | Fetch amino acid sequences | False |
| `-iso/--isoforms` | flag | Return all transcript variants (gene IDs only) | False |
| `-q/--quiet` | flag | Suppress progress information | False |

**Data sources:** Ensembl (nucleotide), UniProt (amino acid)

**Returns:** Python list of FASTA lines (header, sequence, ...), or None on failure; CLI prints FASTA

---

## Sequence Analysis & Alignment Modules

### gget blast
BLAST sequences against standard databases.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `sequence` | str | Sequence or path to FASTA/.txt | Required |
| `-p/--program` | str | blastn, blastp, blastx, tblastn, tblastx | Auto-detect |
| `-db/--database` | str | nt, refseq_rna, pdbnt, nr, swissprot, pdbaa, refseq_protein | nt or nr |
| `-l/--limit` | int | Max hits returned | 50 |
| `-e/--expect` | float | E-value cutoff | 10.0 |
| `-lcf/--low_comp_filt` | flag | Enable low complexity filtering | False |
| `-mbo/--megablast_off` | flag | Disable MegaBLAST (blastn only) | False |
| `-o/--out` | str | Output file path | None |
| `-q/--quiet` | flag | Suppress progress | False |

**Returns:** Description, Scientific Name, Common Name, Taxid, Max Score, Total Score, Query Coverage

---

### gget blat
Find genomic positions using UCSC BLAT.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `sequence` | str | Sequence or path to FASTA/.txt | Required |
| `-st/--seqtype` | str | 'DNA', 'protein', 'translated%20RNA', 'translated%20DNA' | Auto-detect |
| `-a/--assembly` | str | Target assembly (hg38, mm39, taeGut2, etc.) | 'human'/hg38 |
| `-o/--out` | str | Output file path | None |
| `-csv` | flag | Return CSV format (CLI) | False |
| `-q/--quiet` | flag | Suppress progress | False |

**Returns:** genome, query size, alignment start/end, matches, mismatches, alignment percentage

---

### gget muscle
Align multiple sequences using Muscle5.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `fasta` | str/list | Sequences or FASTA file path | Required |
| `-o/--out` | str | Output file path | stdout |
| `-s5/--super5` | flag | Use Super5 algorithm (faster, large datasets) | False |
| `-q/--quiet` | flag | Suppress progress | False |

**Returns:** Python returns None; prints ClustalW alignment or writes aligned FASTA using `out="alignment.afa"`

---

### gget diamond
Fast local protein alignment and translated nucleotide-to-protein alignment.

**Parameters:**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `query` | str/list | Query sequences or FASTA file | Required |
| `-ref/--reference` | str/list | Reference sequences or FASTA file | Required |
| `-s/--sensitivity` | str | fast, mid-sensitiv

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

