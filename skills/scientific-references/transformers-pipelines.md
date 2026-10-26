---
id: sciref-transformers-pipelines
name: "Scientific Ref: Pipeline API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (transformers): Pipeline API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "transformers pipelines"
  - "pipeline api reference"
keywords:
  - "transformers"
  - "pipelines"
  - "specialized"
  - "scientific"
  - "reference"
  - "pipeline"
---

# Pipeline API Reference

Targets Transformers 5.18.0. Pretrained examples below are illustrative; the local regression suite checks pipeline behavior with small random models. See [review evidence](review.md).

## Overview

Pipelines provide the simplest way to use pre-trained models for inference. They abstract away tokenization, model loading, and post-processing, offering a unified interface for dozens of tasks.

## Basic Usage

Create a pipeline by specifying a task:

```python
from transformers import pipeline

# Explicit checkpoints avoid changing task defaults. Pin revision to a reviewed commit for research.
pipe = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = pipe("This is great!")
```

Or specify a model:

```python
pipe = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
```

## Supported Tasks

### Natural Language Processing

**text-generation**: Generate text continuations
```python
generator = pipeline("text-generation", model="openai-community/gpt2")
output = generator("Once upon a time", max_new_tokens=50, do_sample=True, num_return_sequences=2)
```

**text-classification**: Classify text into categories
```python
classifier = pipeline("text-classification", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = classifier("I love this product!")  # Returns label and score
```

**token-classification**: Label individual tokens (NER, POS tagging)
```python
ner = pipeline("token-classification", model="dslim/bert-base-NER")
entities = ner("Hugging Face is based in New York City")
```

**Extractive question answering:** the old `question-answering` pipeline is removed. For extractive semantics, load `AutoModelForQuestionAnswering`, tokenize question/context with `truncation="only_second"`, and decode valid context spans from start/end logits using offset and sequence-ID mappings. Long documents require overlapping windows and alignment back to the original text; independent argmax can produce an invalid span. Generative QA via a chat model does not supply equivalent calibrated answer spans.

**fill-mask**: Predict masked tokens
```python
unmasker = pipeline("fill-mask", model="google-bert/bert-base-uncased")
result = unmasker("Paris is the [MASK] of France")
```

**Summarization and translation:** `summarization`, `translation*`, and `text2text-generation` pipelines are removed. Existing seq2seq checkpoints still use `AutoModelForSeq2SeqLM.generate()` (see [generation](generation.md)). For instruction-based generation, use a chat checkpoint:

```python
summarizer = pipeline("text-generation", model="Qwen/Qwen2.5-0.5B-Instruct")
messages = [{"role": "user", "content": "Summarize this text: [replace with the source text]"}]
summary = summarizer(messages, max_new_tokens=128, do_sample=False)
print(summary[0]["generated_text"][-1]["content"])
```

**zero-shot-classification**: Classify without training data
```python
classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
result = classifier(
    "This is a course about Python programming",
    candidate_labels=["education", "politics", "business"]
)
```

**sentiment-analysis**: Alias for text-classification focused on sentiment
```python
sentiment = pipeline("sentiment-analysis", model="distilbert/distilbert-base-uncased-finetuned-sst-2-english")
result = sentiment("This product exceeded my expectations!")
```

### Computer Vision

**image-classification**: Classify images
```python
classifier = pipeline("image-classification", model="google/vit-base-patch16-224")
result = classifier("path/to/image.jpg")
# Or use PIL Image or URL
from PIL import Image
result = classifier(Image.open("image.jpg"))
```

**object-detection**: Detect objects in images
```python
detector = pipeline("object-detection", model="facebook/detr-resnet-50")
results = detector("image.jpg")  # Returns bounding boxes and labels
```

**image-segmentation**: Segment images
```python
segmenter = pipeline("image-segmentation", model="facebook/detr-resnet-50-panoptic")
segments = segmenter("image.jpg")
```

**depth-estimation**: Estimate depth from images
```python
depth = pipeline("depth-estimation", model="Intel/dpt-large")
result = depth("image.jpg")
```

For DPT, use `predicted_depth` for the raw tensor. The `depth` PIL output is a per-image min-max visualization, not metric distance; constant depth can make that normalization degenerate. Preserve preprocessing/resolution and do not infer meters without a metric-depth model/calibration.

**zero-shot-image-classification**: Classify images without training
```python
classifier = pipeline("zero-shot-image-classification", model="openai/clip-vit-base-patch32")
result = classifier("image.jpg", candidate_labels=["cat", "dog", "bird"])
```

CLIP scores are normalized over the supplied candidate prompts; changing that set changes scores. They are not an open-world detection probability.

### Audio

**automatic-speech-recognition**: Transcribe speech
```python
asr = pipeline("automatic-speech-recognition", model="openai/whisper-base")
text = asr("audio.mp3")
```

**audio-classification**: Classify audio
```python
classifier = pipeline("audio-classification", model="MIT/ast-finetuned-audioset-10-10-0.4593")
result = classifier("audio.wav", function_to_apply="sigmoid", top_k=5)
```

AudioSet AST predicts potentially simultaneous events: use independent sigmoid scores. The audio-classification pipeline otherwise defaults to softmax, which forces competition between labels. Match postprocessing to the checkpoint's training objective; neither score is automatically calibrated.

**text-to-speech**: Generate speech from text (with specific models)
```python
tts = pipeline("text-to-speech", model="facebook/mms-tts-eng")
audio = tts("Hello, this is a test")
# audio["audio"] is a waveform array; audio["sampling_rate"] supplies its rate.
```

### Multimodal

**image-text-to-text**: Generative captions or visual questions. The former `visual-question-answering` and `image-to-text` pipelines are removed. Put images inside message content; do not pass a separate images argument alongside chats.

```python
captioner = pipeline("image-text-to-text", model="Qwen/Qwen3-VL-2B-Instruct")
messages = [{"role": "user", "content": [
    {"type": "image", "image": "image.jpg"},
    {"type": "text", "text": "Describe this image."},
]}]
caption = captioner(messages, max_new_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

