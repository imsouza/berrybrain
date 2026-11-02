---
id: sciref-primer-design-design-workflows
name: "Scientific Ref: Assay-specific design workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (primer-design): Assay-specific design workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "primer design design workflows"
  - "assay-specific design workflows"
keywords:
  - "primer"
  - "design"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "assay"
---

# Assay-specific design workflows

Documentation checked: 2026-10-01. These are design and review procedures. The
bundled tools automate ordinary DNA-primer design, thermodynamics, and bounded
local-reference screening; they do not implement every specialized assay below.

## Define success before choosing sequences

Write a design brief with:

- Assay purpose: genomic PCR, RT-PCR/RT-qPCR, cloning, genotyping, or another named
  assay; biological material and expected background DNA.
- Intended target set: one locus, one transcript, several named isoforms, or all
  members of an explicitly listed set. A gene symbol alone is insufficient.
- Reference identity: accession **with version**, assembly and annotation release,
  strand, extraction coordinates, FASTA checksum, and reference retrieval date.
- Desired product interval, region that must be contained in the product, regions
  primers must avoid, and any fixed primer or required junction.
- Polymerase/master mix, known reaction chemistry, available empirical validation,
  and constraints imposed by the downstream method.

Keep defaults provisional when chemistry is unknown. Do not translate a missing
reference or ambiguous target into a made-up sequence. Acquire the sequence or
provide the unfinished design specification and the missing inputs.

## Ordinary genomic PCR

1. Extract the target with enough flanking sequence for alternative binding sites.
   Retain its mapping to the full reference; template-local coordinates are not
   chromosome coordinates.
2. Mark low-confidence sequence, repeats, and relevant population/sample variants
   as exclusions when their avoidance is part of the assay specification.
3. Design several candidates with explicit product and primer constraints. Inspect
   rejection reasons if none return; relax one justified constraint at a time and
   record each change.
4. Verify both synthesized primer sequences against the template, their inward
   orientation, and the entire expected product. Include primer-binding sites in
   the product length.
5. Screen against the broader reference and expected background. A successful
   design on a small extracted window establishes no genome-wide specificity.
6. Retain at least one alternative pair at different sites when feasible. Rank
   acceptable candidates by assay priorities, not solely by Primer3 penalty.

Keep intended product size distinct from the maximum unintended-product size
screened. Search for plausible off-target products outside the intended design
range as well. See [specificity.md](specificity.md).

## RT-PCR and RT-qPCR

Choose **transcript-specific**, **gene-level**, or **explicit multi-transcript**
detection before designing. Enumerate intended and excluded transcript accessions;
check that the selected annotation actually contains the junction of interest.

An exon-junction primer can reduce genomic amplification, but its binding site must
be checked against genomic DNA and processed pseudogenes. A pair in different
exons instead relies on intervening genomic structure; short introns can still
produce genomic products. Test the annotated transcript sequence and corresponding
genomic context separately. NCBI Primer-BLAST supports these distinctions when
appropriate reference records are supplied. Its “allow splice variants” option
permits additional variants; it does **not** require coverage of all variants.
[Primer-BLAST guidance](https://www.ncbi.nlm.nih.gov/tools/primer-blast/).

For qPCR, select product dimensions appropriate to the chemistry, sample quality,
and assay purpose; no size or Tm range guarantees an efficient assay. Plan
experimental specificity checks, no-template controls, and a no-RT control where
genomic carryover matters. Estimate efficiency and usable quantitative range with
suitable material. A single melt peak is evidence to review with product identity,
not proof that the desired transcript was amplified. Report sequences, product
identity, chemistry, controls, and measured validation separately from predictions.
[MIQE 2.0](https://academic.oup.com/clinchem/article/71/6/634/8119148).

Primer design does not establish stable reference-gene expression, valid
normalization, or biological replication. Hydrolysis probes additionally require
probe-specific chemistry and modification-aware analysis; a Primer3 internal oligo
alone is not a validated probe assay.

## Variants and allele discrimination

For a general assay, intersect **both complete binding intervals** with variants
from the relevant assembly and population or sample. Inspect near-3′ variants
closely, but retain the position and identity of every overlapping variant.
Variant absence from a database is not evidence that a sample has no variation.

Use an explicit coordinate conversion before creating exclusions. For example, a
1-based SNP at reference position `p` occupies `[p-1, p)` in 0-based half-open
coordinates. If a plus-strand extracted template starts at offset `s`, its local
interval is `[p-1-s, p-s)`. For reverse-complement extraction, additionally transform
through the extracted sequence length. Confirm the reference allele after mapping.
Indels require their complete affected interval and attention to normalization;
do not treat every VCF record as a one-base exclusion.

For intended allele-specific PCR, state which allele each primer should recognize,
retain both allele sequences, and predict binding/product formation on both.
Deliberate 3′ discrimination needs validation with known positive and negative
genotypes. Neither a terminal mismatch nor a numerical mismatch budget proves
allele discrimination; this is a specialized assay, not an automatic “pass” from
the ordinary specificity screen. The need to consider polymorphic binding sites
is discussed in the [Primer-BLAST paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC3412702/).

## Cloning primers and 5′ additions

Store three distinct sequences for each oligo: the **annealing core**, the **5′
tail**, and the **full ordered oligo** (`tail + core`, all 5′→3′). The reverse primer
is already supplied in synthesized orientation; do not reverse-complement its
entire ordered sequence again.

Use the core for initial template binding and reference specificity. Assess the
full oligo for hairpins and primer-primer interactions. Reconstruct the final
double-stranded product explicitly: in forward orientation its ends are the
forward tail and the reverse complement of the reverse tail. Verify every ju

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

