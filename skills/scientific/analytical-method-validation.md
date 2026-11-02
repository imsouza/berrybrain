---
id: sci-analytical-method-validation
name: "Scientific: analytical-method-validation"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Plans, executes, and documents validation, verification, and transfer of analytical procedures under the governing framework - ICH Q2(R2) and Q14, USP <1220>/<1225>/<1226>, ICH M10 bioanalytical, CLSI EP, or ISO/IEC 17025. Use for HPLC, LC-MS/MS, GC, CE, ICP-MS, dissolution, qNMR"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "analytical method validation"
  - "analytical-method-validation"
keywords:
  - "analytical"
  - "method"
  - "validation"
  - "plans"
  - "executes"
  - "documents"
  - "verification"
  - "transfer"
---

# Analytical Method Validation

## When to use

Any time the question is whether an analytical procedure is fit for its intended purpose:
designing a validation study, evaluating validation data, verifying a compendial procedure,
transferring a procedure to another laboratory or instrument, or defending any of these in a
report.

## The two rules

**1. Establish which framework governs before designing anything.** The same assay validates
differently under ICH Q2(R2), USP <1225>, ICH M10, CLSI EP, and ISO/IEC 17025. They differ in
which characteristics are required, how the studies are laid out, and whether numeric acceptance
criteria are supplied at all. Blending them produces a protocol that satisfies none of them.

**2. State acceptance criteria before collecting data.** Criteria chosen after seeing results are
not acceptance criteria, and deciding them post hoc is a standing audit finding. ICH Q2(R2)
deliberately supplies almost no numeric criteria — they have to come from the specification, the
analytical target profile (ICH Q14 section 3), or development data. ICH M10 is the exception: it
supplies explicit numbers, and they differ between chromatographic assays and ligand binding
assays.

## Scope

This skill plans studies, computes the statistics correctly, and structures the documentation. It
does **not** decide that a procedure is validated, release a batch, accept or reject a run, close
an investigation, or substitute for the analyst, the technical reviewer, the quality unit, or the
regulator. Every script reports computations and supported findings; only the responsible reviewers can
make the fitness-for-purpose decision. JSON uses `null` for unavailable statistics.

## Copyright boundary

ICH guidelines are published openly and licensed for reuse with acknowledgement, so their
requirements are encoded directly in this skill. **USP general chapters, CLSI EP documents, and
ISO standards are copyrighted and paywalled.** For those, this skill supplies the designation,
scope, and where to obtain an authorised copy — never the text, never invented thresholds. Do not
ask an agent to retrieve, transcribe, or reconstruct their content. If a number matters and it
lives in a paywalled document, read it from the authorised copy.

## Frameworks

```bash
cd skills/analytical-method-validation/scripts
python3 plan_validation.py --list-frameworks
```

| Key | Governs | Numeric criteria supplied |
| --- | --- | --- |
| `ich-q2r2` | Release and stability testing of drug substances and products | Almost none — you derive them |
| `ich-m10` | Bioanalytical concentration measurement (PK, TK, BE) | Yes, and they differ by modality |
| `usp-1220` | Compendial procedure lifecycle, three stages | Paywalled |
| `usp-1225` / `usp-1226` | Validation / verification of compendial procedures | Paywalled |
| `clsi` | Clinical laboratory measurement procedures (EP series) | Paywalled |
| `iso-17025` | Lab-developed and modified methods under accreditation | No — "to the extent necessary" |

**Q2(R2) replaced Q2(R1) in November 2023 and restructured the characteristics.** Range is now
the parent characteristic (section 3.2), containing *response* (linearity) and *validation of
lower range limits* (DL/QL). Accuracy and precision are section 3.3 and may be evaluated in
combination against a single criterion. Robustness is treated as a development activity and
cross-refers to ICH Q14. Multivariate procedures are addressed explicitly (2.5 and 3.2.2.3), and
Annex 2 adds worked examples for techniques Q2(R1) never covered — quantitative ¹H-NMR, NIR,
quantitative LC/MS, qPCR, biological assays, and particle size. A Q2(R1)-shaped protocol — a flat
list of linearity, range, accuracy, precision, specificity, LOD, LOQ, robustness — is out of date.
Note also the error correction dated 30 November 2023 to Table 5 and Tables 6–11.

## Scripts

```bash
cd skills/analytical-method-validation/scripts
```

| Script | Question answered |
| --- | --- |
| `plan_validation.py` | Which framework, which characteristics, what study layout, what protocol? |
| `check_response.py` | Does the calibration model actually hold across the range? |
| `check_accuracy_precision.py` | What is the recovery, and how much of the variability is between days? |
| `check_detection_limits.py` | What are DL and QL by each allowed approach, and do they serve the reporting threshold? |
| `check_bioanalytical_run.py` | Which supported ICH M10 numerical checks raise findings? |
| `compare_methods.py` | Are two procedures equivalent, at a pre-stated margin? |

Commands below use placeholder data filenames; supply your own controlled data. The printed
numerical examples were re-executed with synthetic repository fixtures under
`tests/analytical-method-validation/fixtures/` on Python 3.13.3. They are computational smoke
tests, not evidence that a physical assay is validated. All scripts take `--format table|tsv|json`. Provenance, guideline citations, and caveats go to stderr;
data goes to stdout, so `> out.tsv` keeps them separate. Exit code is `0` for no findings, `1`
when findings were raised, `2` for bad input — so any of them can gate a workflow.

Version 2.0 tightens the numerical input contract: QL confirmation needs explicit bias/CV limits;
intercept-based limits need independent curves; M10 runs need complete labelled calibrator/QC
records; grouped accuracy uses group means; unavailable JSON statistics are `null`. Re-run saved
analyses rather than comparing their exit codes with version 1.x unchanged.

## Workflow

### 1. Fix the framework and the required characteristics

```bash
python3 plan_validation.py --framework ich-q2r2 --attribute assay --technique hplc --range-use assay
```

Q2(R2) Table 1 decides what is required from the *measured attribute*, not from the technique. For
an assay: specificity, response, accuracy, repeatability, intermediate precision. For a limit
test: specificity and DL only. For an identity test: specificity alone. Attributes accepted include
`assay`, `impurity` (quantitative), `impurity-limit`, and `identity`.

Reportable range comes from the specification. Q2(R2) Table 2 gives worked examples — 80–120% of
declared content for an assay, 70–130% for content uniformity, reporting threshold to 120% of the
specification for an impurity.

### 2. Generate the protocol and fill in the criteria

```bash
python3 plan_validation.py --framework ich-q2r2 --attribute impurity --protocol > protocol.md
```

Every bracketed fie

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

