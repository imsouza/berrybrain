---
id: sciref-generate-image-models
name: "Scientific Ref: OpenRouter image model reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (generate-image): OpenRouter image model reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "generate image models"
  - "openrouter image model reference"
keywords:
  - "generate"
  - "image"
  - "models"
  - "specialized"
  - "scientific"
  - "reference"
  - "openrouter"
---

# OpenRouter image model reference

Reviewed 2026-09-30 using the public [image catalogue](https://openrouter.ai/api/v1/images/models)
and all 55 corresponding `/api/v1/images/models/{model_id}/endpoints` responses. These are
read-only metadata checks, not generation benchmarks or evidence that a paid request will succeed.

```bash
python scripts/generate_image.py --list-models
python scripts/generate_image.py --list-models gemini
python scripts/generate_image.py --model-info openai/gpt-image-2.5-sunburst
```

The first endpoint returns a `data` array and each model's capability **union**. Endpoint discovery
returns an object with `id` and `endpoints`; there is no documented pagination for either list.
The CLI additionally checks that at least one endpoint accepts the whole parameter combination.
Account access, provider availability, moderation and undeclared cross-parameter constraints still
require a real request. `--model-info` prints each provider's definitive capabilities and prices.

## Catalogue snapshot

`n` and `refs` are inclusive ranges. A dash is unsupported, not unlimited; omitting `n` uses the
provider default. `n` is an upper bound and can produce fewer images. A positive `refs` minimum
means text-only generation is not supported. Prices below are **output only**, not total cost.

| Model | n | refs | stream | Output rates |
| --- | --- | --- | --- | --- |
| `black-forest-labs/flux.2-flex` | 1–1 | 0–8 | no | $0.06/megapixel |
| `black-forest-labs/flux.2-klein-4b` | 1–1 | 0–4 | no | $0.014/megapixel |
| `black-forest-labs/flux.2-max` | 1–1 | 0–8 | no | $0.07/megapixel |
| `black-forest-labs/flux.2-pro` | 1–1 | 0–8 | no | $0.03/megapixel |
| `bytedance-seed/seedream-4.5` | 1–10 | 0–14 | no | $0.04/image |
| `bytedance-seed/seedream-5-0-lite` | 1–4 | 0–14 | no | $0.035/image |
| `bytedance-seed/seedream-5-0-pro` | 1–1 | 0–14 | no | $0.045/image; $0.09/image (high_resolution) |
| `google/gemini-2.5-flash-image` | 1–1 | 0–3 | no | $0.000054/token; $0.000015/token; $0.00003/token |
| `google/gemini-3-pro-image` | 1–1 | 0–14 | no | $0.00012/token |
| `google/gemini-3-pro-image-preview` | 1–1 | 0–14 | no | $0.00006/token; $0.00012/token |
| `google/gemini-3.1-flash-image` | 1–1 | 0–14 | no | $0.00006/token |
| `google/gemini-3.1-flash-image-preview` | 1–1 | 0–14 | no | $0.00006/token |
| `google/gemini-3.1-flash-lite-image` | 1–1 | 0–14 | no | $0.00003/token |
| `inclusionai/ming-image-0.1-design` | 1–1 | 0–0 | no | $0/token |
| `inclusionai/ming-image-0.1-design-layer` | 1–1 | 1–1 | no | $0/token |
| `krea/krea-2-large` | — | 0–1 | no | not published |
| `krea/krea-2-medium` | — | 0–1 | no | not published |
| `krea/krea-2-medium-turbo` | — | 0–1 | no | not published |
| `meta/muse-image` | — | — | no | not published |
| `microsoft/mai-image-2.5` | 1–1 | 0–1 | no | $0.000047/token |
| `microsoft/mai-image-2.5-pro` | 1–1 | 0–1 | no | $0.000108/token |
| `microsoft/mai-image-2.6` | 1–1 | 0–5 | no | $0.000038/token |
| `microsoft/mai-image-2.6-flash` | 1–1 | 0–5 | no | $0.000019/token |
| `openai/gpt-5-image` | 1–10 | 0–16 | yes | $0.00004/token |
| `openai/gpt-5-image-mini` | 1–10 | 0–16 | yes | $0.000008/token |
| `openai/gpt-5.4-image-2` | 1–10 | 0–16 | yes | $0.00003/token |
| `openai/gpt-image-1` | 1–10 | 0–16 | yes | $0.00004/token |
| `openai/gpt-image-1-mini` | 1–10 | 0–16 | yes | $0.000008/token |
| `openai/gpt-image-2` | 1–10 | 0–16 | yes | $0.00003/token |
| `openai/gpt-image-2.5-flare` | 1–10 | 0–16 | yes | $0.00003/token |
| `openai/gpt-image-2.5-sunburst` | 1–10 | 0–16 | yes | $0.00003/token |
| `qwen/qwen-image-3` | 1–6 | 0–4 | no | $0.03/image (1k); $0.03/image (2k) |
| `qwen/qwen-image-3-pro` | 1–6 | 0–4 | no | $0.04/image (1k); $0.075/image (2k) |
| `recraft/recraft-v3` | 1–6 | 0–1 | no | $0.04/image |
| `recraft/recraft-v4` | 1–6 | 0–1 | no | $0.04/image |
| `recraft/recraft-v4-pro` | 1–6 | 0–1 | no | $0.25/image |
| `recraft/recraft-v4-pro-vector` | 1–6 | 0–1 | no | $0.3/image |
| `recraft/recraft-v4-styles` | 1–6 | 1–10 | no | $0.035/image |
| `recraft/recraft-v4-styles-pro` | 1–6 | 1–10 | no | $0.1/image |
| `recraft/recraft-v4-styles-pro-vector` | 1–6 | 1–10 | no | $0.12/image |
| `recraft/recraft-v4-styles-vector` | 1–6 | 1–10 | no | $0.05/image |
| `recraft/recraft-v4-vector` | 1–6 | 0–1 | no | $0.08/image |
| `recraft/recraft-v4.1` | 1–6 | 0–1 | no | $0.035/image |
| `recraft/recraft-v4.1-flash` | 1–6 | — | no | $0.007/image |
| `recraft/recraft-v4.1-pro` | 1–6 | 0–1 | no | $0.21/image |
| `recraft/recraft-v4.1-pro-vector` | 1–6 | 0–1 | no | $0.3/image |
| `recraft/recraft-v4.1-utility` | 1–6 | 0–1 | no | $0.035/image |
| `recraft/recraft-v4.1-utility-pro` | 1–6 | 0–1 | no | $0.21/image |
| `recraft/recraft-v4.1-vector` | 1–6 | 0–1 | no | $0.08/image |
| `sourceful/riverflow-v2-fast` | 1–1 | 0–4 | no | $0.02/image; $0.04/image (2k) |
| `sourceful/riverflow-v2-pro` | 1–1 | 0–10 | no | $0.15/image; $0.15/image (2k); $0.33/image (4k) |
| `sourceful/riverflow-v2.5-fast` | 1–1 | 0–4 | no | $0.019/image; $0.021/image (2k) |
| `sourceful/riverflow-v2.5-pro` | 1–1 | 0–10 | no | $0.13/image; $0.15/image (2k); $0.17/image (4k) |
| `x-ai/grok-imagine-image-2.0` | 1–1 | 0–3 | no | $0.04/image (low_1k); $0.06/image (low_2k); $0.06/image (medium_1k); $0.08/image (medium_2k) |
| `x-ai/grok-imagine-image-quality` | 1–1 | 0–3 | no | $0.05/image (1k); $0.07/image (2k) |

`meta/muse-image` was listed but returned no provider endpoints: catalogue membership does not
establish availability. Krea returned empty pricing arrays. Ming's zero published rates are not a
promise of permanently free generation. Gemini 2.5 and Gemini 3 Pro Preview offer multiple
endpoints/tiers with different prices; inspect the endpoint and routing tag instead of assuming
the lowest rate. Gemini 3 Pro's Vertex endpoint advertises only 1K/2K although its model union
includes 4K through AI Studio.

Input charges matter: Riverflow v2 reports $0.20/reference and $0.03/font; Seedream 5.0 Pro
reports $0.003/input image; Grok reports $0.01/input image. OpenAI and MAI advertise input token
rates. Recraft Styles charges $0.005/request for the input-reference line. Inspect every pricing
line and its `billable`, `unit`, and optional `variant`; do not multiply a token or megapixel rate
as if it were per image. The discovery schema supplies variant labels but does not always explain
how they map to a particular request (for example Seedream Pro's `high_resolution`).

## Allowed values

This table records t

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

