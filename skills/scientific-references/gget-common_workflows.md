---
id: sciref-gget-common-workflows
name: "Scientific Ref: Common gget workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (gget): Common gget workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "gget common workflows"
  - "common gget workflows"
keywords:
  - "gget"
  - "common"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# Common gget workflows

Use [workflows.md](workflows.md) for current 0.30.8 integration examples and their
verification boundaries. Use [database_info.md](database_info.md) for service,
authentication, pagination, and return-shape details.

| Task | Sequence of operations | Check before interpretation |
| --- | --- | --- |
| Gene characterization | `search` -> unique exact `gene_name` -> `info` / `seq` | Preserve Ensembl index; inspect service failures; distinguish genomic sequence from CDS. |
| Ortholog comparison | `bgee` -> select species/ortholog -> `seq` -> FASTA file -> `muscle(out=...)` | Reject ambiguous orthology and nested FASTA lists. MUSCLE returns None. |
| Structures and residue features | `g2p` with exact accession -> inspect isoform/PDB map -> `pdb(resource="mmcif")` | Match chain/residue coverage; predicted features are not experimental validation. |
| Expression | `archs4` or scoped `cellxgene` query | Human-only ARCHS4 correlations; species-specific tissue query; Census metadata counts cells. |
| Enrichment | selected genes + measured background -> `enrichr` with full library -> adjusted-p-value filter | Species/library compatibility, mapped IDs, selection universe, and returned `adj_p_val`. |
| Disease/drug exploration | human Ensembl ID -> `opentargets` resources | Dot-separated columns, local filtering after limit, partial pages, association versus causation. |
| Cancer data | chosen cBioPortal studies -> `cbio_plot`; licensed local COSMIC TSV -> `cosmic` | Study denominators, project/release/assembly, download completeness. |
| Reference preparation | `ref` with release -> CLI `-d` download -> checksums -> downstream index | `which` is comma-separated on CLI; Python has no download parameter. |

Bundled scripts (run from the skill root):

```bash
python scripts/gene_analysis.py TP53
python scripts/enrichment_pipeline.py selected.txt --background tested.txt --no-plot
python scripts/enrichment_pipeline.py fly_genes.txt --species fly --database SPECIES_SPECIFIC_LIBRARY --no-plot
python scripts/batch_sequence_analysis.py proteins.fasta --database swissprot
```

These network invocations are illustrative. Confirm that a species-specific
library exists before submitting it; its example name is not a freshness claim.
The script suite verifies local control flow with mocked responses. The gene
pipeline depends on the Ensembl REST adapter, which failed during the current
public probe. The batch script is for small exploratory queries and never runs
AlphaFold; large searches should use local alignment tooling.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

