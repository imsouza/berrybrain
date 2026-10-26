---
id: sciref-histolab-core-capabilities
name: "Scientific Ref: Histolab core API map"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (histolab): Histolab core API map"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "histolab core capabilities"
  - "histolab core api map"
keywords:
  - "histolab"
  - "core"
  - "capabilities"
  - "specialized"
  - "scientific"
  - "reference"
---

# Histolab core API map

The skill targets published Histolab 0.7.0. Read the per-topic reference for
executable examples and scientific limitations; placeholder WSI paths require
user data. Upstream [API index](https://histolab.readthedocs.io/en/latest/py-modindex.html)
currently labels itself 0.6.0, so use the linked 0.7.0 source for release-specific
behavior.

| Capability | Public API | Key contract |
| --- | --- | --- |
| Slide inspection | `histolab.slide.Slide` | `levels` is a list; `level_dimensions(level)` is a method |
| Tissue detection | `histolab.masks.TissueMask`, `BiggestTissueBoxMask`, `BinaryMask` | Boolean mask; custom filters are positional |
| Tiling | `histolab.tiler.RandomTiler`, `GridTiler`, `ScoreTiler` | Mask passed to methods; preview returns Pillow image |
| Ranking | `histolab.scorer.NucleiScorer`, `CellularityScorer` | Stain-derived area heuristics, not cell counts or diagnosis |
| Filters | `histolab.filters.image_filters.Compose` and filter classes | Preserve Pillow/NumPy type transitions |
| Normalization | `histolab.stain_normalizer.MacenkoStainNormalizer`, `ReinhardStainNormalizer` | `fit(target)` then `transform(source)` |
| Spatial provenance | `histolab.types.CoordinatePair`, `Tile.coords` | Four level-0 pixel coordinates |

The slide-management reference covers native OpenSlide, exact MPP backend
requirements and small versus remote sample data. The tissue-mask reference
provides ROI conversion and pen-mask examples. The tile-extraction reference
covers strategy choice, CSV schema and concentric multi-resolution patches.
The filters reference covers type-correct compositions and stain normalization.
The visualization reference provides aligned mask overlays, mosaics and score
plots. The typical-workflows reference combines these APIs into extraction runs.

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

