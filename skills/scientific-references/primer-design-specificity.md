---
id: sciref-primer-design-specificity
name: "Scientific Ref: Reference specificity and amplicon geometry"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (primer-design): Reference specificity and amplicon geometry"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "primer design specificity"
  - "reference specificity and amplicon geometry"
keywords:
  - "primer"
  - "design"
  - "specificity"
  - "specialized"
  - "scientific"
  - "reference"
---

# Reference specificity and amplicon geometry

Documentation checked: 2026-10-01. Specificity is a claim about named sequences,
search settings, and assay conditions. A favorable thermodynamic score or a clean
search of an incomplete reference does not establish a unique biological product.

## Select the reference universe

Create a manifest before screening. Include reference source, accession/version or
assembly release, annotation release if relevant, date retrieved, checksums, record
IDs, lengths, topology, and which intended/expected background molecules it covers.

| Assay | References to consider |
| --- | --- |
| Genomic locus | Appropriate assembly; alternate/unplaced sequences and relevant haplotypes when required |
| Transcript assay | Intended and excluded isoforms; related genes/pseudogenes; genomic DNA as a separate check |
| Plasmid or cloning | Complete construct, parental vector, inserts, and plausible host background |
| Family-wide detection | Explicit intended sequence collection and near-neighbor negatives |
| Mixed sample | Target plus likely host and other background relevant to interpretation |

Document omitted components. Do not silently reduce a reference to the design
window to make screening faster. Preserve distinct sequence identifiers; duplicated
records and multiple genomic loci are different issues. Several loci with the same
amplicon sequence remain several loci.

## What the bundled local methods establish

`screen_specificity.py` supports two local search strategies. Their guarantees are
different; retain the method and all settings in the report.

- **Exhaustive ungapped search:** evaluate complete primer-length windows on both
  strands under the configured total and 3′ mismatch rules. Completeness is only
  for the supplied reference, implemented geometry, and bounded mismatch model.
  Insertions/deletions, longer permissible products, absent haplotypes, and unknown
  bases cannot be dismissed from biological consideration.
- **BLAST discovery with full-length verification:** use short-query alignment to
  locate candidate binding windows, then verify the full primer sequence at those
  windows. This avoids treating a short favorable local alignment as a complete
  primer match. BLAST remains a heuristic: realignment cannot recover sites that
  discovery never returned.

Inspect the script's current options and emitted limitations for size, hit, and
product caps and for supported topology. A cap reached during screening means the
analysis is incomplete. Missing expected amplification, unsupported input, or
truncated enumeration is not a specificity pass.

The exhaustive method is useful for constructs and bounded references. For large
genomes, use scalable search or Primer-BLAST, retain limitations, and avoid treating
the Python scanner as a whole-genome performance guarantee.

## Binding orientation and coordinates

Store oligos in **synthesized 5′→3′ orientation**. Relative to the supplied reference:

- A primer equal to the plus-strand window has a plus-direction binding hit and
  extends toward increasing reference coordinates.
- A primer equal to the reverse complement of that window has a minus-direction
  hit and extends toward decreasing reference coordinates.

“Forward” and “reverse” are design labels; either oligo can find hits in either
orientation elsewhere. For linear reference intervals, a plus-direction binding
site upstream and a minus-direction site downstream may form an inward-facing
product. The product extends from the upstream primer's outer 5′ boundary to the
downstream primer's outer 5′ boundary and includes both primers.

Enumerate the two-oligo reaction's **F/R, F/F, and R/R** possibilities, not just the
intended F/R orientation. For multiplex reactions, additionally evaluate
cross-assay pairs. Primer-BLAST checks same-primer as well as mixed-primer products;
this avoids overlooking inverted-repeat products.
[Primer-BLAST publication](https://pmc.ncbi.nlm.nih.gov/articles/PMC3412702/).

The bundled specificity CLI's `--multiplex` mode generates all cross-pair oligo
combinations under a declared cap and preserves their source identities. All
cross-pair products are classified as unintended in that mode. Assess intentional
shared-primer designs using explicit standalone combinations and expected intervals.

For circular templates, wrapped products cross coordinate zero. Use an explicitly
supported circular search and a documented maximum product length; preserve
original record length and wrapped coordinates. Doubling a reference without
deduplication and length constraints can create misleading duplicate or
multi-circumference products. Linear screening cannot clear origin-spanning risk.

## Expected versus unintended products

Supply intended **record and coordinate intervals**, not just a record-name
allowlist. A chromosome can contain the intended site and many unintended sites.
If several loci or isoforms are acceptable, list each explicitly with its rationale.

Classify every predicted product against that specification. Report binding
coordinates, primer identities, product length, total mismatches, and mismatch
positions counted from the synthesized primer's 3′ end. Review expected products
that are missing or mismatched separately from additional products.

For a whole-reference reverse-complement transformation, `[start, end)` becomes
`[L-end, L-start)` and the direction flips. This simple identity is useful for
testing coordinate handling. An oligo's last base is its 3′ end on either strand;
using the genomic window's last base unconditionally is wrong.

## Interpreting mismatch settings

A mismatch budget is a screening model, not a polymerase law. Mismatch identity,
position, reaction conditions, and template abundance affect whether amplification
occurs. Review especially plausible competing products even if they lie just
outside a chosen bound. Compare total mismatch counts with the positions near each
primer's 3′ end; do not summarize both as a single identity percentage.

Use a stricter discovery model only when justified by the assay. Raising required
3′ mismatches or decreasing a total-mismatch budget may reduce predicted products
by definition; it does not improve the oligo. Keep settings constant when ranking
candidates, or report the difference clearly.

Ambiguous reference bases represent unknown or multiple possibilities. A sequence
containing `N` should not be treated as strong evidence of

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

