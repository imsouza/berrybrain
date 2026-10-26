---
id: sci-folklore-variant-evidence
name: "Scientific: folklore-variant-evidence"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Retrieves ClinGen gene-disease validity assertions for a public gene or disease, and reviews source-linked public evidence and literature for one supported GRCh38 germline nuclear SNV or simple indel through Folklore Clinical Variant Interpretation MCP. Used when a scientific age"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "folklore variant evidence"
  - "folklore-variant-evidence"
keywords:
  - "folklore"
  - "variant"
  - "evidence"
  - "retrieves"
  - "clingen"
  - "gene"
  - "disease"
  - "validity"
  - "assertions"
---

# Folklore Variant Evidence

Use Folklore Clinical Variant Interpretation MCP to retrieve structured public
variant evidence, automated variant-level ACMG/AMP decision support, provenance,
and source-linked literature for professional review. Keep the workflow limited
to public identifiers and preserve every explicit outcome state. Adapter 1.5.0 also provides ClinGen Gene-Disease Validity assertions; source coverage is bounded, not every known association.

Folklore Clinical Variant Interpretation MCP is published by Helena
Bioinformatics. Its hosted endpoint is:

```text
https://api.helena.bio/folklore/v1/mcp
```

No account or API key is required. The public Apache-2.0 adapter and contract are
available at <https://github.com/helena-bioinformatics/folklore-mcp>.

## Minimal connection example

A host without native MCP support can make the same public JSON-RPC call:

```bash
curl --silent --show-error --fail-with-body --max-time 60 \
  -X POST https://api.helena.bio/folklore/v1/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: search_variant_evidence' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}},"name":"search_variant_evidence","arguments":{"assembly":"GRCh38","query":"rs80357914"}}}'
```

The routing headers must match the JSON-RPC method and tool name. A successful
HTTP response is not sufficient: inspect JSON-RPC `error`, then
`result.structuredContent.adapter_error`, then this tool's
`result.structuredContent.result.status`. Other tools use different response
shapes; use the [contract table](references/mcp-contract.md).

Inspect the returned outcome before continuing. This example can return
`ambiguous` with multiple candidates: stop and request an unambiguous public
variant notation instead of selecting a candidate automatically.

## Select the right skill

Use this skill when the task is one public variant to structured Folklore
evidence, explicit resolution-state handling, variant-linked literature, or ClinGen gene-to-disease/disease-to-gene assertions.

- Use `database-lookup` for broad direct queries across ClinVar, dbSNP, gnomAD,
  Ensembl VEP, COSMIC, or multiple databases.
- Use `genomic-coordinates` first when the assembly, coordinate convention,
  contig name, or variant representation is uncertain.
- Do not use this skill for VCF annotation, batch processing, somatic variants,
  structural variants, polygenic scores, or patient-specific interpretation.

Folklore Clinical Variant Interpretation MCP complements those skills with one
source-linked public evidence contract. It does not replace direct database
review or qualified clinical judgment.

## Enforce the input boundary

Before a variant tool call:

1. Extract exactly one public variant identifier or notation.
2. Require GRCh38 and a germline nuclear SNV or simple insertion/deletion shorter
   than 50 base pairs. An unsupported assembly may be rejected by the input
   schema before any scientific `unsupported` status exists.
3. Remove or refuse patient names, case identifiers, phenotypes, family history,
   segregation evidence, clinical records, uploaded files, and other private or
   patient-specific context.
4. If the task depends on patient context, stop and explain that Folklore
   Clinical Variant Interpretation MCP does not accept or evaluate it.
5. Never transform a patient-specific request into a public variant query while
   implying that the result answers the patient-specific question.

Accepted public variant forms include genomic coordinates, genomic/coding/
protein HGVS, SPDI, rsID, or a `canonical_key` returned by Folklore Clinical
Variant Interpretation MCP.

## Verify the live tool catalog

Connect to the hosted endpoint and call `tools/list`. Verify the available tools
instead of relying on model memory. The documented public catalog contains:

- `search_variant_evidence`
- `search_variant_literature`
- `get_publication_details`
- `search_literature_corpus`
- `get_gene_disease_associations`
- `search_disease_genes`

The separate seventh tool `support_helena` is not scientific evidence; use it only when explicitly requested.

If discovery or a tool call fails, preserve the failure as an availability
problem. Do not reinterpret it as lack of scientific evidence.

Read [the public MCP contract](references/mcp-contract.md) before composing tool
calls or interpreting response states.

## Retrieve gene-disease assertions

Use `get_gene_disease_associations` for one exact gene symbol or HGNC identifier, or `search_disease_genes` for an exact MONDO identifier or public disease-name substring. Both accept `limit` (default 20, 1–50) and `offset` (default 0, 0–1000). See the reference for request examples. This is a separate source lookup and requires no variant input or assembly.

Preserve each returned disease identity, inheritance, evidence assessment, source
URL, date, `source.version` and `source.snapshotSha256`. This is a local ClinGen
snapshot, not a guarantee of the latest ClinGen release. Follow
`pagination.nextOffset` while it is present; preserve pagination-ceiling warnings.
An empty page after the total has been passed does not mean the initial query had
no matches. Do not combine distinct diseases or silently choose among name matches.
Gene-disease validity does not classify a particular variant. A `not_found`
response means no matching assertion in the available source, not no association.
No patient, phenotype, family, segregation, private case data or sequencing files
may be sent. Qualified professional review remains required.

## Run the variant-evidence workflow

### 1. Resolve and retrieve evidence

Call `search_variant_evidence` with:

```text
assembly: GRCh38
query: <one public variant identifier or notation>
```

Do not add phenotype, disease, patient, family, or treatment context to this
call. Preserve the returned contract fields, source links, limitations, and
usage boundary.

### 2. Branch on the returned status

Read transport/JSON-RPC errors and `adapter_error` first. For
`search_variant_evidence`, let `envelope = result.structuredContent`; only if
`envelope.result` is non-null, branch on `envelope.result.status`. An
`invalid_arguments` adapter error is distinct from scientific `invalid_request`.
Preserve

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

