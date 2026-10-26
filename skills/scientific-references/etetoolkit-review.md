---
id: sciref-etetoolkit-review
name: "Scientific Ref: ETE 4.4.0 review — September 30, 2026"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (etetoolkit): ETE 4.4.0 review — September 30, 2026"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "etetoolkit review"
  - "etetoolkit revisao"
  - "ete 4.4.0 review — september 30, 2026"
keywords:
  - "etetoolkit"
  - "review"
  - "revisao"
  - "specialized"
  - "scientific"
  - "reference"
  - "september"
---

# ETE 4.4.0 review — September 30, 2026

PyPI and the official GitHub release catalogue still identify **4.4.0** as the
current release. This skill targets that package. The installed core-tree,
NCBI, GTDB, and PhyloTree source files were byte-identical to the official
`4.4.0` tag during this review. The current documentation can disagree with
released defaults; runtime behavior and tagged source resolve those differences.

## Checked behavior

The isolated Python 3.13 suite exercises the bundled CLIs and synthetic
scientific examples: parser selection, Newick/NHX/Nexus round trips, leaf
identity, pruning with pairwise-distance preservation, rooting, RF, property
caches, monophyly, ultrametric conversion, species-overlap events,
reconciliation, alignment linkage, duplication splitting, and topology-only
patterns. Tiny synthetic NCBI and converted-GTDB archives exercise actual
SQLite construction, names/ranks/lineages, descendants, topology and annotation.
The taxonomy fixtures reject unexpected `requests.get()` downloads.

Standalone runs also execute the documented preprocessing, metadata-join,
midpoint, RF and offline-taxonomy examples. Qt SVG/PDF and SmartView PNG were
rendered locally with their optional extras. These are small functional
fixtures, not evidence of scientific accuracy for a real inferred tree.

## Contracts that need particular care

- `parser=0` is a valid explicit output choice. Never use a truthiness fallback
  when forwarding parser IDs.
- `prune()` accepts node objects. Resolve actual tips when internal labels can
  collide with leaf names; validating tip names and then passing strings still
  allows ambiguous resolution elsewhere in the tree.
- A zero maximum RF means normalization is undefined. The CLI emits JSON
  `null`, and rejects fewer than two common tips.
- `set_midpoint_outgroup()` computes the exact diameter midpoint. Selecting
  its containing edge with `get_midpoint_outgroup()` and using default
  `set_outgroup()` placement can produce a different root position.
- Support scale belongs to the input source. One percent and fractional one
  are different values; the color helper now requires a declared scale.
- Both CLI loaders reject nonfinite branch lengths and support. The released
  Newick parser accepts `nan`, `inf`, and overflowing exponents; these must not
  reach distance calculations, rendering, or JSON statistics.
- `distance_matrix(squared=True)` returns a square list of lists ordered by
  leaf iteration; it does not return labels or squared distances.
- `render_sm()` warns and returns if Selenium is absent. The helper checks
  dependencies and actual PNG bytes before reporting a saved artifact.
- The Qt PDF renderer selects A4 paper; drawing dimensions do not specify
  cropped page bounds. SmartView's narrow aligned panel can clip long titles.
  Inspect final artifacts rather than equating a successful write with layout QA.
- `NCBITaxa(update=False)` can still download when the database is missing.
  Pass the local archive during construction, or check that the pinned database
  exists before opening it offline. Retain its trusted traversal cache.
- A GTDB genome's `sci_name` may be its parent species. Use the original
  accession for genome identity.
- Alignment sequences are stored in `leaf.props["sequence"]`, not a
  `leaf.sequence` attribute; check that all intended alignment names matched.

## Public data access

These interfaces query local SQLite, not remote paginated JSON APIs. The
released updater fetches public archives without credentials:

- NCBI: `https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/taxdump.tar.gz`; its `.md5`
  sidecar returned a valid digest record during the review. ETE consults it for
  freshness of an existing archive, without verifying a fresh download. Its
  requests also lack timeouts and HTTP status checks.
- GTDB conversion:
  `https://github.com/etetoolkit/ete-data/raw/main/gtdb_taxonomy/gtdblatest/gtdb_latest_dump.tar.gz`.
  The official directory listing contained this archive but no `.md5` sidecar;
  the sidecar returned 404. Pin an explicitly acquired release archive instead
  of treating this moving converted dump as a dated GTDB release.

No full public taxonomy database was downloaded. Real taxon-name examples
remain illustrative until checked against the selected snapshot. External PAML
models, large-tree performance, and remote SmartView deployments were not run.
SmartView uses an unauthenticated local viewer; keep its loopback default.

## Official sources

- [Release 4.4.0](https://github.com/etetoolkit/ete/releases/tag/4.4.0)
- [PyPI release metadata](https://pypi.org/pypi/ete4/json)
- [Tree API](https://etetoolkit.github.io/ete/reference/reference_tree.html)
- [Parser API](https://etetoolkit.github.io/ete/reference/reference_parsers.html)
- [PhyloTree API](https://etetoolkit.github.io/ete/reference/reference_phylo.html)
- [SmartView API](https://etetoolkit.github.io/ete/reference/reference_smartview.html)
- [Taxonomy tutorial](https://etetoolkit.github.io/ete/tutorial/tutorial_taxonomy.html)
- [Released core source](https://github.com/etetoolkit/ete/blob/4.4.0/ete4/core/tree.pyx)
- [Released NCBI source](https://github.com/etetoolkit/ete/blob/4.4.0/ete4/ncbi_taxonomy/ncbiquery.py)
- [Released GTDB source](https://github.com/etetoolkit/ete/blob/4.4.0/ete4/gtdb_taxonomy/gtdbquery.py)
- [Converted GTDB archive directory](https://github.com/etetoolkit/ete-data/tree/main/gtdb_taxonomy/gtdblatest)

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

