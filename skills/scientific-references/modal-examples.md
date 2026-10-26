---
id: sciref-modal-examples
name: "Scientific Ref: Modal Common Examples"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (modal): Modal Common Examples"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "modal examples"
  - "modal common examples"
keywords:
  - "modal"
  - "examples"
  - "specialized"
  - "scientific"
  - "reference"
  - "common"
---

# Modal Common Examples

Reviewed against Modal 1.6.0. These are **illustrative cloud workload templates**:
SDK registration and selected local handlers were checked, but container builds,
GPU jobs, weights and database writes were not executed. Package pins are examples,
not a validated combined environment. Resolve a lockfile per workload and record the
model revision, hardware, seeds and input provenance before a scientific run.
External helpers such as `transform()` are application-defined.

## LLM Inference Service (vLLM)

```python
import modal

app = modal.App("vllm-service")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install("vllm==0.21.0", "fastapi[standard]==0.136.3")
)

@app.cls(gpu="H100", image=image, max_containers=1)
class LLMService:
    @modal.enter()
    def load(self):
        from vllm import LLM
        self.llm = LLM(model="Qwen/Qwen3-8B", max_model_len=4096)

    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        from vllm import SamplingParams
        params = SamplingParams(max_tokens=max_tokens, temperature=0.7)
        outputs = self.llm.generate([prompt], sampling_params=params)
        return outputs[0].outputs[0].text

    @modal.fastapi_endpoint(method="POST", requires_proxy_auth=True)
    def api(self, request: dict):
        text = self.generate.local(request["prompt"], request.get("max_tokens", 512))
        return {"text": text}
```

[vLLM `LLM.generate`](https://docs.vllm.ai/en/latest/serving/offline_inference/) uses
`SamplingParams`; `max_tokens` is not a `generate()` keyword. This template accepts
a preformatted completion prompt. Apply the model's chat template for chat messages.
Use your Proxy Token to call the endpoint. A 70B BF16 model does not fit one H100;
GPU capacity must include weights and KV cache, not just parameter count.

## Image Generation (Flux)

```python
import modal

app = modal.App("image-gen")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install(
        "diffusers==0.38.0",
        "torch==2.12.0",
        "transformers==5.9.0",
        "accelerate==1.13.0",
    )
)

vol = modal.Volume.from_name("flux-weights", create_if_missing=True)

@app.cls(gpu="L40S", image=image, volumes={"/models": vol})
class ImageGenerator:
    @modal.enter()
    def load(self):
        import torch
        from diffusers import FluxPipeline
        self.pipe = FluxPipeline.from_pretrained(
            "black-forest-labs/FLUX.1-schnell",
            torch_dtype=torch.bfloat16,
            cache_dir="/models",
        ).to("cuda")
        vol.commit()

    @modal.method()
    def generate(self, prompt: str) -> bytes:
        image = self.pipe(prompt, num_inference_steps=4, guidance_scale=0.0).images[0]
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()
```

## Speech Transcription (Whisper)

The audio path must exist inside the container. Upload it to the named Volume
first; passing a local laptop path does not transfer audio.

```python
import modal

app = modal.App("transcription")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .uv_pip_install("openai-whisper==20250625", "torch==2.12.0")
)

audio_vol = modal.Volume.from_name("audio-data", create_if_missing=True)

@app.cls(gpu="T4", image=image, volumes={"/audio": audio_vol})
class Transcriber:
    @modal.enter()
    def load(self):
        import whisper
        self.model = whisper.load_model("large-v3")

    @modal.method()
    def transcribe(self, audio_path: str) -> dict:
        audio_vol.reload()
        return self.model.transcribe(audio_path)
```

## Batch Data Processing

```python
import modal

app = modal.App("batch-processor")

image = modal.Image.debian_slim().uv_pip_install("pandas", "pyarrow")
vol = modal.Volume.from_name("batch-data", create_if_missing=True)

@app.function(image=image, volumes={"/data": vol}, cpu=4.0, memory=8192)
def process_chunk(chunk_id: int) -> dict:
    import pandas as pd
    from pathlib import Path
    from uuid import uuid4
    vol.reload()
    df = pd.read_parquet(f"/data/input/chunk_{chunk_id:04d}.parquet")
    result = df.groupby("category").agg({"value": ["sum", "mean", "count"]})
    output_dir = Path("/data/output") / uuid4().hex
    output_dir.mkdir(parents=True)
    output = output_dir / f"result_{chunk_id:04d}.parquet"
    result.to_parquet(output)
    vol.commit()
    return {"chunk_id": chunk_id, "rows": len(df), "output": str(output)}

@app.local_entrypoint()
def main():
    chunk_ids = list(range(500))
    results = list(process_chunk.map(chunk_ids))
    total = sum(r["rows"] for r in results)
    print(f"Processed {total} total rows across {len(results)} chunks")
```

## Web Scraping at Scale

```python
import modal

app = modal.App("scraper")

image = modal.Image.debian_slim().uv_pip_install("httpx", "beautifulsoup4")

@app.function(image=image, retries=3, timeout=60)
def scrape_url(url: str) -> dict:
    import httpx
    from bs4 import BeautifulSoup
    response = httpx.get(url, follow_redirects=True, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return {
        "url": url,
        "title": soup.title.string if soup.title else None,
        "text": soup.get_text()[:5000],
    }

@app.local_entrypoint()
def main():
    urls = ["https://example.com", "https://example.org"]  # Your URL list
    results = list(scrape_url.map(urls))
    for r in results:
        print(f"{r['url']}: {r['title']}")
```

## Protein Structure Prediction

```python
import modal

app = modal.App("protein-folding")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .uv_pip_install("chai-lab")
)

vol = modal.Volume.from_name("protein-data", create_if_missing=True)

@app.function(gpu="A100-80GB", image=image, volumes={"/data": vol}, timeout=3600)
def fold_protein(sequence: str) -> list[str]:
    from pathlib import Path
    from uuid import uuid4
    from chai_lab.chai1 import run_inference
    if not sequence or any(c not in "ACDEFGHIKLMNPQRSTVWY" for c in sequence):
        raise ValueError("Provide one non-empty canonical protein sequence")
    run_dir = Path("/data/runs") / uuid4().hex
    run_dir.mkdir(parents=True)
    fasta = run_dir / "input.fasta"
    fasta.write_text(f">protein|name=target\n{sequence}\n")
    candidates = run_inference(
        fasta_file=fasta,
        output_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

