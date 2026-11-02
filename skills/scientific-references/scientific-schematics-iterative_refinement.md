---
id: sciref-scientific-schematics-iterative-refinement
name: "Scientific Ref: Smart Iterative Refinement Workflow"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (scientific-schematics): Smart Iterative Refinement Workflow"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "scientific schematics iterative refinement"
  - "cientifico schematics iterative refinement"
  - "smart iterative refinement workflow"
keywords:
  - "scientific"
  - "schematics"
  - "iterative"
  - "refinement"
  - "cientifico"
  - "specialized"
  - "reference"
  - "smart"
---

# Smart Iterative Refinement Workflow

How the generate-review-refine loop works: the initial generation, the quality review,
the decision to continue or stop, subsequent iterations, and the review log. Then the
advanced generation options (Python API, command-line options, prompt engineering) and
four worked examples.

## Smart Iterative Refinement Workflow

The AI generation system uses **smart iteration** - it regenerates when the score is below the local document threshold or the reviewer explicitly requests improvement, within the two-attempt budget:

### How Smart Iteration Works

```text
Source-backed prompt -> Generate PNG -> Review PNG
                                        |
                    +-------------------+-------------------+
                    |                   |                   |
              Criteria met       Improvement needed   Review unavailable
                    |                   |                   |
               Keep draft       Refine if budget left   Keep unchecked
                                (2 attempts maximum)

Generation error -> Stop; retain any earlier successful draft
All paths -> Review log -> Manual scientific and visual verification
```

### Iteration 1: Initial Generation
**Prompt Construction:**
```
Scientific diagram guidelines + User request
```

**Output:** `diagram_v1.png`

### Quality Review by Gemini 3.7 Flash

Gemini 3.7 Flash evaluates the diagram on:
1. **Scientific Accuracy** (0-2 points) - Correct concepts, notation, relationships
2. **Clarity and Readability** (0-2 points) - Easy to understand, clear hierarchy
3. **Label Quality** (0-2 points) - Complete, readable, consistent labels
4. **Layout and Composition** (0-2 points) - Logical flow, balanced, no overlaps
5. **Professional Appearance** (0-2 points) - Publication-ready quality

**Illustrative review output** (not an actual model run):
```
SCORE: 8.0

STRENGTHS:
- Clear flow from top to bottom
- All phases properly labeled
- Professional typography

ISSUES:
- Participant counts slightly small
- Minor overlap on exclusion box

VERDICT: ACCEPTABLE (for poster, threshold 7.0)
```

### Decision Point: Continue or Stop?

| If Score... | Action |
|-------------|--------|
| >= threshold and no improvement verdict | **STOP** - local review criteria met; inspect manually |
| < threshold or improvement verdict | Refine if another iteration is available |
| No usable review | Keep the image, stop, report unverified quality |
| Generation fails | Stop; retain an earlier successful image if one exists |

**Example:**
- For a **poster** (threshold 7.0): Score of 7.5 → **DONE after 1 iteration!**
- For a **journal** (threshold 8.5): Score of 7.5 → Continue improving

### Subsequent Iterations (Only If Needed)

If quality is below threshold, the system:
1. Extracts specific issues from Gemini 3.7 Flash's review
2. Enhances the prompt with improvement instructions
3. Regenerates with Nano Banana 2
4. Reviews again with Gemini 3.7 Flash
5. Repeats until threshold met or max iterations reached

### Review Log
Every attempt is saved in a JSON review log. This illustrative excerpt omits some fields:
```json
{
  "user_prompt": "CONSORT participant flow diagram...",
  "doc_type": "poster",
  "quality_threshold": 7.0,
  "iterations": [
    {
      "iteration": 1,
      "image_path": "figures/consort_v1.png",
      "score": 7.5,
      "reviewed": true,
      "review_error": null,
      "needs_improvement": false,
      "critique": "SCORE: 7.5\nSTRENGTHS:..."
    }
  ],
  "final_score": 7.5,
  "final_reviewed": true,
  "early_stop": true,
  "early_stop_reason": "Quality score 7.5 meets threshold 7.0 for poster"
}
```

**Note:** With smart iteration, you may see only 1 iteration instead of the full 2 if quality is achieved early!

### When the review does not run

The reviewer is a second model call, and it can fail on its own — a rate limit, a content filter,
an answer in a shape the parser cannot read. The image is generated first and is kept regardless;
what is missing in that case is the *measurement*, so the log says so rather than substituting a
number:

```json
{
  "iterations": [
    {
      "iteration": 1,
      "image_path": "figures/consort_v1.png",
      "score": null,
      "reviewed": false,
      "review_error": "the review model returned no choices",
      "needs_improvement": false,
      "critique": "Review unavailable: the review model returned no choices."
    }
  ],
  "final_score": null,
  "final_reviewed": false
}
```

The run exits 0 — the diagram is real — and prints
`Review unavailable - image kept, quality not verified`. It does **not** regenerate: a reviewer that
did not answer says nothing about the diagram, so another generation would be guesswork. Look at the
image yourself, and re-run if you want a score; first diagnose the failure rather than assuming another paid run will fix it.

`final_reviewed` indicates a numeric review; `quality_met` also requires the threshold and no improvement verdict. Neither means author-approved. `termination_reason` distinguishes `quality_threshold_met`, `review_unavailable`, `max_iterations`, and `generation_failed`. The selected image is the latest successful draft, not automatically the highest-scoring one. A failed second attempt does not discard the first image. A fully failed run exits 1; any retained image exits 0, even below threshold.

## Advanced AI Generation Usage

### Python API

```python
from scripts.generate_schematic_ai import ScientificSchematicGenerator

# Illustrative paid call; credentials are resolved from the environment/.env.
generator = ScientificSchematicGenerator(verbose=True)

# Generate with iterative refinement (max 2 iterations)
results = generator.generate_iterative(
    user_prompt="Transformer architecture diagram",
    output_path="figures/transformer.png",
    iterations=2
)

# Access results
print(f"Final score: {results['final_score']}/10")
print(f"Final image: {results['final_image']}")

# Review individual iterations
for iteration in results['iterations']:
    if iteration.get("success"):
        print(f"Iteration {iteration['iteration']}: {iteration['score']}/10")
        print(f"Critique: {iteration['critique']}")
    else:
        print(f"Generation error: {iteration['error']}")
```

### Command-Line Options

```bash
# Basic usage (default threshold 7.5/10)
python scripts/generate_schematic.py "diagram description" -o output.png

# Specify document type for appropriate qual

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

