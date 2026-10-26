---
id: sci-generate-image
name: "Scientific: generate-image"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Generates or edits images with AI models through the OpenRouter Image API (Gemini, Seedream, Recraft, GPT-Image, Riverflow). Use for photos, illustrations, artwork, concept art, visual assets, logos, and image editing or compositing from reference images. For flowcharts, circuits"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "generate image"
  - "generate-image"
keywords:
  - "generate"
  - "image"
  - "generates"
  - "edits"
  - "images"
  - "models"
  - "through"
  - "openrouter"
---

# Generate Image

Generate and edit images through OpenRouter's Image API, which reaches Gemini, Seedream, Recraft,
GPT-Image, Riverflow, and other models behind one request shape.

## When to use

**Use this skill for:** photos and photorealistic images, illustrations and artwork, concept art,
presentation and poster visuals, logos and vector marks, image editing, and compositing from
reference images.

**Use `scientific-schematics` instead for:** flowcharts, circuit diagrams, biological pathways,
system architecture diagrams, CONSORT diagrams, and other technical schematics.

## API key

Generation requires an OpenRouter key. The script resolves it in this order:

1. `--api-key`
2. the `OPENROUTER_API_KEY` environment variable
3. `OPENROUTER_API_KEY=` in a `.env` file, searching the working directory upward, then the
   script's own directory

If none is present the script exits with setup instructions. Keys: https://openrouter.ai/keys

`--list-models`, `--model-info`, and `--dry-run` need no key.

## Quick start

```bash
# Generate
python scripts/generate_image.py "A beautiful sunset over mountains"

# Edit an existing image
python scripts/generate_image.py "Make the sky purple" -i photo.jpg -o edited.png
```

Run these commands from the skill directory; input and output paths resolve from the working
directory. Output defaults to `generated_image.<ext>`, using each image's returned media type
(or `.bin` when unknown). An explicit output suffix is kept, with a warning on mismatch; the
script does not transcode. OpenRouter and upstream costs are printed separately when supplied.

**Then look at the image.** Read the file back and check it before using it anywhere: composition,
aspect ratio, and any text are all things models get wrong silently.

## Choosing a model

Default: `google/gemini-3.1-flash-image`.

| Need | Model |
| --- | --- |
| General quality, prompt adherence | `google/gemini-3.1-flash-image` |
| Highest Gemini tier | `google/gemini-3-pro-image` |
| Cheap iteration | `google/gemini-3.1-flash-lite-image` (1K only), `openai/gpt-image-1-mini` |
| Photoreal control, seeded generation | `bytedance-seed/seedream-4.5` |
| Several images per request | `bytedance-seed/seedream-4.5`, `openai/gpt-image-2` (up to 10) |
| Vector / SVG output | `recraft/recraft-v4.1-vector` |
| Transparent background | `openai/gpt-image-1` with `--background transparent` |
| Legible text inside the image | `recraft/recraft-v4.1`, `sourceful/riverflow-v2.5-pro` — see the caveat below |

[references/models.md](references/models.md) carries the reviewed capability and pricing snapshot. The live listing is authoritative and free:

```bash
python scripts/generate_image.py --list-models            # every model and its allowed values
python scripts/generate_image.py --list-models gemini     # filtered by substring
python scripts/generate_image.py --model-info openai/gpt-image-1   # one model, plus pricing
```

## Parameter support varies by model

This is the main thing to get right. Models advertise different parameter sets **and different
allowed values**. The CLI conservatively rejects unadvertised options; individual providers may
ignore or normalize some fields. The generic guide can lag the discovery records.

The script checks the model catalogue and requires at least one provider endpoint to accept the
complete combination before generation. Model capabilities are a union across endpoints, not a
promise that every provider supports them. Unsupported requests fail locally with legal values:

```console
$ python scripts/generate_image.py "abstract pattern" -m openai/gpt-image-2 --background transparent
Error: Request rejected before billing (1 problem):
  - background=transparent is not allowed; this model accepts: auto, opaque
```

Current examples of capability differences (reviewed 2026-09-30):

- `--resolution`: Gemini 3.1 Flash accepts `512`, `1K`, `2K`, `4K`; Flash Lite and Krea
  accept only `1K`. Seedream 5.0 Lite accepts `2K`/`4K`, while 5.0 Pro accepts `1K`/`2K`.
- `--output-format`: Riverflow 2.5 Pro accepts `png`/`jpeg`/`webp`; its Fast variant accepts
  only `jpeg`. Recraft vector models accept `svg`. OpenAI models do not advertise this flag.
- `--quality`: GPT Image 2.5 Flare/Sunburst also accept `xhigh`/`max`; Grok 2.0 accepts
  only `low`/`medium`. Inspect the specific model before selecting a quality value.
- `--background transparent` is **not available** on `gpt-image-2` or `gpt-5.4-image-2`.
  It is advertised on GPT Image 1 and 2.5. Do not combine transparency with JPEG; when no
  output format is selectable, inspect the returned file for an actual alpha channel.
- `--aspect-ratio`: GPT-5 Image and Mini now accept `1:1`, `3:2`, `2:3`, `auto`;
  GPT-5.4 Image 2 also accepts wider ratios. None accept a resolution flag in this snapshot.
- `--n` is an upper bound, not a guarantee: providers may return fewer images. Seedream 4.5
  caps at 10, Seedream 5.0 Lite at 4, and 5.0 Pro at 1. Krea does not advertise `n`.
- `--seed` is available on Seedream, Krea, Qwen and FLUX, but not Gemini or OpenAI.
  Keep the model/provider, prompt and parameters fixed; a seed is not a cross-version guarantee.

`--dry-run` performs free discovery and prints the request without generating. If discovery
fails, the command stops; `--no-preflight` explicitly bypasses it. Combining both flags is an
offline payload inspection, **not** validation of provider support.

## Writing the prompt

Prompt quality decides output quality more than model choice does. Name, in one sentence each:

1. **Subject** — what is in frame, and how much of it. "A single pipette tip above a 96-well plate."
2. **Medium and style** — photograph, watercolour, 3D render, flat vector, scientific illustration.
3. **Lighting and palette** — "soft diffuse lighting, cool blue and white palette."
4. **Composition** — "wide shot, subject left of centre, empty space on the right for a title."
5. **What to avoid** — "no text, no labels, no watermark."

Asking for empty space where a caption or title will go is the single most useful compositional
instruction for posters and slides.

Iterate cheaply: draft on `gemini-3.1-flash-lite-image`, then regenerate the wording you settled on
with the model you actually want. To refine rather than restart, feed the last output back as a
reference (`-i out.png`) and describe only the change.

## Editing and reference images

`-i/--input` is repeatable and accepts local paths, HTTP(S) URLs, or data URL

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

