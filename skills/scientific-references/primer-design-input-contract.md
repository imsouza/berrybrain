---
id: sciref-primer-design-input-contract
name: "Scientific Ref: Files, coordinates, settings, and result contracts"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (primer-design): Files, coordinates, settings, and result contracts"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "primer design contract"
  - "files, coordinates, settings, and result contracts"
keywords:
  - "primer"
  - "design"
  - "contract"
  - "specialized"
  - "scientific"
  - "reference"
  - "files"
---

# Files, coordinates, settings, and result contracts

Use local UTF-8 files. All scripts accept `--help` without contacting a service.
Generated JSON is evidence, not a command file. Keep results outside the skill.

## Template and screening FASTA

- The first whitespace-delimited token after `>` is the record ID. IDs must be unique.
- Sequence is case-normalized. Internal whitespace, digits, gaps, RNA U, and non-IUPAC
  symbols are rejected. Empty records and sequence before a header are rejected.
- Design uses one selected record; `--record` is required with multiple records.
- Design replaces ambiguity with N and excludes it from primers. Screen reference
  ambiguity uses possible-base sets and reports unresolved matching sites.
- Preserve full reference ID/version/source in a separate manifest. A user-written
  FASTA label is not verified evidence of an accession or assembly.
- Local files are hashed. Checksums identify the bytes used; they do not independently
  establish database currency, biological correctness, or adequate coverage.

The example FASTA in `../assets/demo-template.fasta` contains 500 deterministic
synthetic bases generated with Python `random.Random(717)`, choosing A/C/G/T uniformly.
It is reproducible demonstration input with no claimed biological function.

## Primer pair TSV

Required columns: `pair_id`, `forward`, `reverse`.
Optional columns: `forward_tail`, `reverse_tail` (empty means no tail).
Columns are tab-separated; unknown/duplicate columns and malformed rows are errors.

```text
pair_id	forward	reverse	forward_tail	reverse_tail
assay_1	ACGTCAGTACGATCGTACGA	TCGATGCACTGATCGTACGT	GGATCC	GAATTC
```

These illustrative oligos explain the schema; they are not recommended experimental
primers. Pair IDs use letters, digits, underscores, periods, and hyphens and must be
unique. Cores and tails are unambiguous ACGT DNA, written in ordering orientation
5′→3′. Modified bases and degenerate symbols are rejected, not stripped.

The full ordering sequence is `tail + core`. A reverse primer is already reverse-
complemented relative to its target; do not reverse-complement it again for ordering.
For an exact-match product oriented from the forward primer toward the reverse:

```text
final top strand = forward_tail + template_product + reverse_complement(reverse_tail)
```

For mismatched primers, late-cycle products incorporate primer bases; a reference
product hash does not identify that final synthesized molecule. The screen explicitly
names its hash `reference_product_sha256` and does not reconstruct such products.

## Design configuration JSON

Top-level keys are only `sequence_args` and `global_args`, both objects. Template,
record ID, paired-primer task, 0-based indexing, and unambiguous output are controlled
by the adapter. It rejects unsupported tags, including tags for another Primer3 task.

Example (JSON, not skill frontmatter):

```json
{
  "sequence_args": {
    "SEQUENCE_TARGET": [[235, 30]],
    "SEQUENCE_EXCLUDED_REGION": [[80, 5]]
  },
  "global_args": {
    "PRIMER_PRODUCT_SIZE_RANGE": [[90, 180]],
    "PRIMER_NUM_RETURN": 3,
    "PRIMER_SALT_MONOVALENT": 50.0,
    "PRIMER_SALT_DIVALENT": 1.5,
    "PRIMER_DNTP_CONC": 0.6,
    "PRIMER_DNA_CONC": 50.0
  }
}
```

### Sequence constraints supported by the adapter

| Tag | Value and meaning |
| --- | --- |
| `SEQUENCE_TARGET` | List of alternative `[start,length]` regions; a pair must flank at least one, not necessarily all |
| `SEQUENCE_INCLUDED_REGION` | One `[start,length]` design region within the selected template |
| `SEQUENCE_EXCLUDED_REGION` | List of `[start,length]` regions where primer binding is disallowed |
| `SEQUENCE_PRIMER_PAIR_OK_REGION_LIST` | List of `[left_start,left_length,right_start,right_length]`; `[-1,-1]` makes that side unconstrained |
| `SEQUENCE_OVERLAP_JUNCTION_LIST` | Indices of bases immediately left of internal junctions; verify returned overlap against transcript annotation |
| `SEQUENCE_PRIMER` | Fixed forward core in ordering orientation |
| `SEQUENCE_PRIMER_REVCOMP` | Fixed reverse core in ordering orientation |
| `SEQUENCE_QUALITY` | One nonnegative integer score per template base; pair with explicit quality thresholds or weights |

`SEQUENCE_OVERLAP_JUNCTION_LIST` uses the index of the base immediately **before**
the junction with this adapter's `PRIMER_FIRST_BASE_INDEX=0`. A junction between
bases at indices 99 and 100 is supplied as **99**. Use the minimum 5′/3′ overlap controls and verify the returned
binding interval, not just the command's exit status.

### Global controls supported by the adapter

- Candidate count (`PRIMER_NUM_RETURN`, 1–100).
- Primer size: `PRIMER_MIN_SIZE`, `PRIMER_OPT_SIZE`, `PRIMER_MAX_SIZE`; adapter range
  15–36 nt, ordered minimum ≤ optimum ≤ maximum.
- Tm: `PRIMER_MIN_TM`, `PRIMER_OPT_TM`, `PRIMER_MAX_TM`, `PRIMER_PAIR_MAX_DIFF_TM`.
- GC: `PRIMER_MIN_GC`, `PRIMER_OPT_GC_PERCENT`, `PRIMER_MAX_GC`, `PRIMER_GC_CLAMP`,
  `PRIMER_MAX_END_GC`; `PRIMER_MAX_POLY_X`, `PRIMER_MAX_END_STABILITY`.
- Thermodynamic structure limits: `PRIMER_MAX_SELF_ANY_TH`, `PRIMER_MAX_SELF_END_TH`,
  `PRIMER_MAX_HAIRPIN_TH`, `PRIMER_PAIR_MAX_COMPL_ANY_TH`, `PRIMER_PAIR_MAX_COMPL_END_TH`.
- Chemistry: `PRIMER_SALT_MONOVALENT`, `PRIMER_SALT_DIVALENT`, `PRIMER_DNTP_CONC`,
  `PRIMER_DNA_CONC`. Salt/dNTP units are mM; DNA concentration is nM.
- Core Tm model: `PRIMER_TM_FORMULA` is 0 Breslauer or 1 SantaLucia; salt correction
  `PRIMER_SALT_CORRECTIONS` is 0 Schildkraut, 1 SantaLucia, or 2 Owczarzy. Match these
  to `check_thermodynamics.py --tm-method` and `--salt-corrections-method` respectively.
  Defaults are SantaLucia for both. Structure calculations use libprimer3 defaults.
- `PRIMER_PRODUCT_SIZE_RANGE`: nonempty list of `[minimum,maximum]` inclusive ranges.
  Multiple ranges retain Primer3's preference ordering; no global optimum is implied.
- Junction overlap: `PRIMER_MIN_5_PRIME_OVERLAP_OF_JUNCTION` and
  `PRIMER_MIN_3_PRIME_OVERLAP_OF_JUNCTION`.
- Optional ranking weights: `PRIMER_WT_TM_GT`, `PRIMER_WT_TM_LT`, `PRIMER_WT_SIZE_GT`,
  `PRIMER_WT_SIZE_LT`, `PRIMER_PAIR_WT_DIFF_TM`, `PRIMER_PAIR_WT_PR_PENALTY`.
- Quality controls: `PRIMER_MIN_QUALITY`, `PRIMER_MIN_END_QUALITY`,
  `PRIMER_QUALITY_RANGE_MIN`, `PRIMER_QUALITY_RANGE_MAX`, `PRIMER_WT_SEQ_QUAL`,
  `PRIMER_WT_END_QUAL`; supply `SEQUENCE_QUALITY` and meaningful assay-specific values.
- `PRIMER_MAX_NS_ACCEPTED` must remain zero.

To cover multiple intervals with one product, provide their enclosin

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

