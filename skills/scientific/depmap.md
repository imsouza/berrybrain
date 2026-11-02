---
id: sci-depmap
name: "Scientific: depmap"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Retrieves and analyzes Cancer Dependency Map (DepMap) release data, including CRISPR Chronos gene effects, cancer model annotations, omics biomarkers, and PRISM drug sensitivity. Supports cancer-selective dependency, co-essentiality, and candidate synthetic-lethality analyses wit"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "depmap"
keywords:
  - "depmap"
  - "retrieves"
  - "analyzes"
  - "cancer"
  - "dependency"
  - "release"
---

# DepMap — Cancer Dependency Map

## When to use

Use this skill to rank dependencies in cancer models, compare prespecified biomarker
cohorts, inspect co-essentiality, or relate genetic dependencies to PRISM compound
response. These analyses generate target and synthetic-lethality hypotheses; they
do not establish clinical efficacy, a therapeutic window, or a causal interaction.

DepMap integrates Broad and Sanger CRISPR screens and hosts independent RNAi and
drug-screen datasets. Match each question to its assay and pinned release. RNAi
DEMETER2 is a different perturbation modality, not an older CRISPR scoring method.

## 1. Discover a release, then obtain its files

Use [DepMap Downloads](https://depmap.org/portal/data_page/) and the selected
release's README and release notes. On review, the live catalogue's latest
`DepMap Public` release was **26Q1**, dated 2026-04-01. Rediscover before new work;
a release name or expected quarter is not evidence a release is available.

### Verified public endpoint

`GET https://depmap.org/portal/api/no-captcha/download/files` returns a complete
CSV catalogue, with no request body, API key, or pagination parameters. Required
metadata columns are `release`, `release_date`, `filename`, and `md5_hash`.
The live response also has `url`: **older files can have links, while recent
release rows have blank links**. All 85 entries for 26Q1 had blank `url` values at
review. Treat availability per row, not per endpoint.

The [staff announcement](https://forum.depmap.org/t/provide-an-open-endpoint-for-latest-version-retrieval/4652)
introduced this metadata route in July 2026. The older
`https://depmap.org/portal/api/download/files` catalogue can supply download links
but returned an HTML verification page during review, including with HTTP 200.
Validate content before parsing. Obtain current files through the portal when
verification is required. Refresh expiring signed links immediately before use;
do not fabricate storage URLs or assume every new release is on Figshare.

No supported contract was verified for the former `/api/gene?gene_id=...` or
`/api/data/gene_dependency` examples. Use local release matrices for gene slices.
Do not assume a Python package named `depmap` is an official portal client.

From the skill root, use the bundled [helpers](scripts/depmap_data.py):

```python
from scripts.depmap_data import fetch_catalogue, select_file, verify_md5

catalogue = fetch_catalogue()
public = catalogue[catalogue["release"].str.startswith("DepMap Public ")]
print(public[["release", "release_date"]].drop_duplicates()
      .sort_values("release_date", ascending=False).head(12))

# Explicit example pin; inspect discovery output before selecting your release.
release = "DepMap Public 26Q1"
record = select_file(catalogue, release, "CRISPRGeneEffect.csv")
print(record[["release", "filename", "md5_hash"]])
# After obtaining this file from the portal:
# verify_md5("CRISPRGeneEffect.csv", record["md5_hash"])
```

Save the selected metadata, retrieval date, release citation, local checksum, and
README alongside analysis outputs. Record source dataset terms separately from
this skill's license; newer release terms differ from older Figshare releases.
For a missing published checksum, retain a local SHA-256 and explicitly state
that it was not compared with a publisher checksum.

## 2. Inspect file contracts before joining

The following names were verified in the 26Q1 catalogue. Check that release's
README for units and identifier level before treating a file as a numeric matrix.

| File | Use and important contract |
|---|---|
| `CRISPRGeneEffect.csv` | Integrated, model-level Chronos effects; rows are ModelID, columns preserve `Symbol (EntrezID)` |
| `CRISPRGeneEffectUncorrected.csv` | Uncorrected effects; not interchangeable with corrected effects |
| `CRISPRGeneDependency.csv` | Release-specific dependency statistics; confirm probability/FDR definition and direction in the README |
| `Model.csv` | Model metadata keyed by `ModelID` |
| `ModelCondition.csv` | Growth/treatment conditions keyed by `ModelConditionID`, mapping to `ModelID` |
| `ScreenGeneEffect.csv`, `ScreenSequenceMap.csv`, `CRISPRScreenMap.csv` | Screen-level effects and mappings; multiple screens can belong to one model |
| `OmicsExpressionTPMLogp1HumanProteinCodingGenes.csv` | Expression output with sequencing/model metadata and default-entry flags; exclude metadata columns from expression calculations |
| `OmicsSomaticMutationsMatrixDamaging.csv`, `OmicsSomaticMutationsMatrixHotspot.csv` | Distinct mutation annotations; damaging and hotspot calls answer different biological questions |
| `OmicsCNGeneWGS.csv`, `OmicsCNGeneMC_WES.csv` | Separate WGS/WES copy-number products; do not concatenate as one uniformly processed cohort |
| `PortalOmicsCNGeneLog2.csv` | Transformed portal copy-number product; establish the exact transform before inversion |
| `OmicsProfiles.csv`, `Gene.csv` | Omics provenance/mappings and gene annotations |
| `AchillesScreenQCReport.csv`, `AchillesSequenceQCReport.csv` | Screen/sequence QC; apply documented eligibility rules rather than invented universal cutoffs |

Current model annotations include `CellLineName`, `OncotreeLineage`,
`OncotreePrimaryDisease`, and `OncotreeSubtype`. Legacy `sample_info.csv` fields
(`DepMap_ID`, `lineage`, `primary_disease`) require an explicit conversion.
`Model.csv` includes models without CRISPR measurements: absence from the effect
matrix is not a nondependency score.

Omics may be indexed by `SequencingID`, `ModelConditionID`, or `ModelID`. For a
basal model analysis, use the release's `IsDefaultEntryForModel == Yes` flag,
then require one row per `ModelID`. The condition-level flag
`IsDefaultEntryForMC` answers a different question. Subset the assay/datatype
before selecting defaults from a mapping table. Never average repeated conditions
or count them as independent models without an explicit scientific design.

See the [mapping guide source](https://github.com/broadinstitute/depmap-portal/blob/master/frontend/packages/portal-frontend/src/dataPage/components/MapSection.tsx)
and [metadata definitions](https://forum.depmap.org/t/depmap-metadata/3694).

## 3. Interpret Chronos and inspect a target

Chronos gene effect is continuous and unbounded. More negative values indicate
stronger loss of fitness. In the normalized release matrix, approximately 0 is
the nonessential-control anchor and −1 is the common-essential-control anchor;

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

