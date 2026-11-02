---
id: sciref-shap-modalities
name: "Scientific Ref: Text, Images, and Deep Models"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (shap): Text, Images, and Deep Models"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "shap modalities"
  - "text, images, and deep models"
keywords:
  - "shap"
  - "modalities"
  - "specialized"
  - "scientific"
  - "reference"
  - "text"
  - "images"
---

# Text, Images, and Deep Models

Framework/model integration fragments below are illustrative: they were checked against SHAP 0.52.0 source but not run with pretrained weights or a TensorFlow/PyTorch/Transformers installation during this review. Tiny local text and constant-image masking games are tested separately.

Structured inputs require structured maskers. Token deletion, image inpainting, and neural-network reference activations define different explanation games; do not reduce them to ordinary independent tabular columns without justification.

## General Pattern

1. Define a batched model callable with named outputs.
2. Choose a masker that produces valid model inputs.
3. Restrict outputs and evaluation rows before expensive computation.
4. Inspect result shapes.
5. Validate output reconstruction when the explainer supports it.
6. Run masking and baseline sensitivity checks.

The `max_evals`/`outputs` pattern below applies to supported permutation/partition paths; it is not a universal call signature for tree, linear, or deep explainers.

```python
explainer = shap.Explainer(
    model_fn,
    masker,
    output_names=output_names,
    seed=7,
)
explanation = explainer(
    inputs,
    max_evals=evaluation_budget,
    outputs=selected_outputs,
)
```

## Text Classification

Use the model's tokenizer:

```python
masker = shap.maskers.Text(tokenizer)
explainer = shap.Explainer(
    model_fn,
    masker,
    algorithm="partition",
    output_names=class_names,
    seed=7,
)

all_outputs = explainer(texts)
class_exp = all_outputs[..., class_index]
shap.plots.text(class_exp)
```

The model callable should accept a batch of strings and return a 2-D numeric array `(batch, outputs)`.

```python
def model_fn(text_batch):
    encoded = tokenizer(
        list(text_batch),
        padding=True,
        truncation=True,
        return_tensors="pt",
    ).to(device)

    with torch.inference_mode():
        logits = model(**encoded).logits

    return logits.detach().cpu().numpy()
```

Decide whether to explain:

- raw class logits (multiclass softmax logits are not per-class log-odds);
- explicit binary or one-versus-rest log-odds, when that is the intended output;
- probabilities, which stakeholders may understand but couple classes through normalization;
- another scalar score.

State the choice in every plot.

### Transformers pipelines

SHAP provides `shap.models.TransformersPipeline`. Configure the existing text-classification pipeline with `top_k=None` so every class score is returned; a top-one pipeline leaves other columns at zero in this wrapper. Validate the complete label mapping and finite output values on a tiny batch before explaining:

```python
wrapped = shap.models.TransformersPipeline(
    classifier_pipeline,
    rescale_to_logits=True,
)
masker = shap.maskers.Text(classifier_pipeline.tokenizer)
explainer = shap.Explainer(wrapped, masker, algorithm="partition")
explanation = explainer(texts)
```

`rescale_to_logits=True` applies `log(p / (1-p))` independently to each returned class probability. These are one-versus-rest log-odds, not recovered multiclass model logits; scores at 0 or 1 produce infinities. Prefer an explicit model callable when original logits are required. Do not compare these values directly with probability-space explanations.

SHAP 0.52.0's upstream test extras pin `transformers<4.54.0`; this is a compatibility warning, not proof of current Transformers 5 support. Test a separately locked integration rather than promising compatibility from the wrapper's existence. Generation wrappers below have the same framework-validation requirement.

### Text masking choices

Check:

- tokenizer special tokens;
- subword splitting;
- mask token;
- whether consecutive masked tokens are collapsed;
- maximum sequence length and truncation;
- normalization and whitespace behavior;
- language-specific token boundaries.

SHAP can merge tokens hierarchically for display. A displayed phrase attribution may be a grouped coalition, not the sum from an independent-token game.

### Generative and sequence-to-sequence models

SHAP includes model wrappers such as:

- `TeacherForcing`;
- `TextGeneration`;
- `TopKLM`.

Generation explanations are target- and decoding-dependent. Record:

- generated or fixed target sequence;
- teacher-forcing setup;
- decoding parameters;
- top-k output selection;
- tokenizer/model revision.

Do not describe one generation explanation as a general explanation of the language model.

## Image Classification

`shap.maskers.Image` needs OpenCV (`cv2`) for string-based blur/inpainting, not for a numeric constant/array baseline. OpenCV is not installed by the `plots` extra. Add a compatible OpenCV build only when those methods are required. Inpainting converts pixels to `uint8`; use a suitable 0–255 image representation and put the model's normalization inside the callable. Applying it directly to normalized floats can destroy image information.

Wrap preprocessing inside the model callable so masked images receive the same transformations:

```python
def image_model_fn(image_batch):
    prepared = preprocess(image_batch.copy())
    return model(prepared)
```

Choose an image masker:

```python
masker = shap.maskers.Image(
    "inpaint_telea",
    shape=image_shape,
)

explainer = shap.Explainer(
    image_model_fn,
    masker,
    output_names=class_names,
    seed=7,
)

explanation = explainer(
    images,
    max_evals=500,
    batch_size=50,
    outputs=shap.Explanation.argsort.flip[:3],
)

shap.plots.image(explanation)
```

The current constructor also accepts blur specifications or constant mask values. Compare plausible alternatives:

```python
inpaint = shap.maskers.Image("inpaint_telea", image_shape)
blur = shap.maskers.Image("blur(32,32)", image_shape)
zero = shap.maskers.Image(0, image_shape)
```

These answer different questions:

- inpainting replaces a region using nearby pixels;
- blur removes high-frequency detail while retaining coarse structure;
- a constant value creates a fixed visual baseline.

None guarantees an in-distribution counterfactual.

### Output selection

Image classifiers may have thousands of outputs. Use:

```python
outputs=shap.Explanation.argsort.flip[:k]
```

The selected outputs can vary by row. Preserve `output_indexes`/`output_names` and never assume position zero refers to the same class for every image when ranked outputs are used.

### Interpreting image overlays

Attribution overlays:

- explain a 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

