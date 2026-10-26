---
id: sciref-gget-database-info
name: "Scientific Ref: gget data sources and adapter contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gget): gget data sources and adapter contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gget database info"
  - "gget data sources and adapter contracts"
keywords:
  - "gget"
  - "database"
  - "info"
  - "specialized"
  - "scientific"
  - "reference"
  - "sources"
---

# gget data sources and adapter contracts

Reviewed against [gget 0.30.8 source](https://github.com/scverse/gget/tree/v0.30.8/gget)
and the [current manual](https://scverse.org/gget/), 2026-09-30. Pin
`gget==0.30.8` in Python >=3.12. A package pin does not freeze remote databases.
Record query inputs, species, genome assembly, dataset release, retrieval date,
software versions, warnings, and raw outputs. Most public queries need no key;
COSMIC downloads and the deprecated GPT wrapper are exceptions.

## Reference, sequence, and structure services

| Module | Transport and result contract | Boundaries |
| --- | --- | --- |
| `ref` | Reads Ensembl directory listings under `ftp.ensembl.org/pub/` and `ftp.ensemblgenomes.org/pub/`; returns release/file metadata or links. CLI `-d` downloads with curl. | Python has no `download` or `out_dir` parameter. Choose an explicit release; `info`/`seq` do not inherit that release. Non-vertebrate support excludes bacteria. |
| `search` | Public MySQL (`mysql-eg-publicsql.ebi.ac.uk`, candidate ports 3306/5306/4157/3337/5316), with release discovery via Ensembl listings. Returns `ensembl_id`, `gene_name`, descriptions, `biotype`, `synonym`, `url`. | Matches names/descriptions/synonyms by substring. `limit=1` is not exact symbol resolution; require a unique exact symbol. `limit` is a local result cap, not a cursor. |
| `info` | Ensembl `POST /lookup/id` (`ids`, `expand`), plus UniProtKB search, NCBI Gene **HTML parsing**, and optional PDBe `GET /pdbe/aggregated-api/mappings/ensembl_to_pdb/{id}`. | Returns a DataFrame indexed by query ID, with `primary_gene_name`/`ensembl_gene_name`, not `gene_name`. `pdb_id` may be a list. Preserve the index. Maximum Ensembl batch is 1000 IDs; versioned IDs are resolved against current data. |
| `seq` | Ensembl `/sequence/id` for nucleotide sequence; `info` and UniProtKB for protein sequence. Python returns a list of alternating FASTA header/sequence lines or `None`. | Gene nucleotide sequence is genomic, not transcript CDS. Never apply HGVS `c.` positions to that sequence without obtaining the exact versioned transcript CDS. Protein isoforms are distinct records. |
| `pdb` | Structure text from `files.rcsb.org/download/{id}.pdb` or `.cif`; metadata from `data.rcsb.org/rest/v1/core/{resource}/{id}` with an assembly/entity/chain identifier where required. | Prefer explicit `resource="mmcif"`; default PDB retrieval can fall back to mmCIF. Save with the corresponding extension. No pagination for one object. |
| `g2p` | Public `GET https://g2p.broadinstitute.org/api/gene/{gene}/protein/{accession}/protein-features`, `/gene-transcript-protein-isoform-structure-map`, or `/{alternative_isoform}/alignment`; TSV parsed to DataFrame. | No pagination. Missing one identifier triggers a UniProt lookup; gene-only resolution picks the first reviewed human match. Supply the exact pair for reproducibility. `residues` filters locally after download. Invalid arguments can raise `ValueError`; network/unknown-pair failures return `None`. |
| `blast` | NCBI `https://blast.ncbi.nlm.nih.gov/Blast.cgi`, submitting `CMD=Put`, then polling the RID with `CMD=Get`; gget parses the returned hit table. | Search job, not a synchronous database lookup. `limit` controls hit count, not database completeness. Respect [NCBI remote BLAST usage guidance](https://blast.ncbi.nlm.nih.gov/doc/blast-help/developerinfo.html); use local BLAST/DIAMOND for large batches. |
| `blat` | UCSC `https://genome.ucsc.edu/cgi-bin/hgBlat` with sequence, type, assembly, and JSON output. Returns alignment rows. | Exact assembly matters; UCSC may throttle or return HTML errors. Coordinates/strand must be checked before mapping variants. No gget pagination. |
| `muscle`, `diamond` | Local bundled/platform binaries; DIAMOND builds a database from supplied reference sequences. | MUSCLE writes `out` or prints alignment and returns `None`; no `save` argument. OpenMP runtime libraries may be required. DIAMOND `diamond_db` names the database to create/save; it does not replace the required `reference`. |
| `elm` | `gget setup elm` downloads instances/classes/interaction-domain files from `elm.eu.org`; local regex and DIAMOND searches, with UniProt lookup when requested. | Returns `(ortholog_df, regex_df)`; short motif matches alone do not demonstrate function. Setup is a network download, not authentication. |

The released `info`/`seq` adapter still uses **HTTP** for Ensembl REST. Public
execution returned HTTP 500 here on 2026-09-30; the equivalent direct HTTPS POST
also returned 500, so HTTP alone is not established as the cause. Treat this as
a transport/service failure, not missing biological evidence. Check upstream
availability and the [Ensembl REST API](https://rest.ensembl.org/) before retrying.
No SDK transport patch is silently applied by this skill. UniProt search helpers
prefer reviewed entries and retry without that restriction if none match; they
do not follow search pagination links. `seq(isoforms=True)` therefore should not
be treated as an exhaustive, release-frozen protein archive.

## Expression, association, and enrichment services

| Module | Transport and output | Completeness and interpretation |
| --- | --- | --- |
| `archs4` correlation | `POST https://maayanlab.cloud/matrixapi/coltop`, JSON `id` and `count`; `rowids`/`values` become `gene_symbol`/`pearson_correlation`. | Human coexpression only; the `species` argument does not select mouse correlations. `gene_count` defaults to 100. No pagination. Correlation is not causation. |
| `archs4` tissue | `POST https://maayanlab.cloud/archs4/search/loadExpressionTissue.php?search={symbol}&species={human|mouse}&type=tissue`; CSV becomes `id`, `min`, `q1`, `median`, `q3`, `max`. | Tissue labels are hierarchical IDs, not a `tissue` column. Bulk ARCHS4 values and Census counts are different measurements; do not compare their magnitudes as a shared scale. |
| `cellxgene` | `cellxgene_census.open_soma` + `get_anndata`; `meta_only=True` reads the observation table instead. | Metadata rows are **cells**, not datasets. The gene filter is ignored in metadata-only mode. `is_primary_data=True` by default; use observation filters and a dated Census release. A small gene set can still select millions of cells. Raw-count QC/library normalization needs the full measured feature universe. |
| `enrichr` human/mouse | Uploads a gene list via multipart `POST https://maayanlab.cloud/speedrichr/api/addList` (`list`, `description`); r

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

