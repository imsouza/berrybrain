---
id: sciref-hypogenic-upstream
name: "Scientific Ref: Upstream package, source, CLI, and workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypogenic): Upstream package, source, CLI, and workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypogenic upstream"
  - "upstream package, source, cli, and workflows"
keywords:
  - "hypogenic"
  - "upstream"
  - "specialized"
  - "scientific"
  - "reference"
  - "package"
---

# Upstream package, source, CLI, and workflows

Review date: 2026-10-01. Package/source assertions were rechecked against the
verified release wheel, current official metadata, and provider documentation.

## Release and integrity status

The latest stable PyPI artifact is `hypogenic==0.3.5`, uploaded
2025-07-16. PyPI metadata declares Python `>=3.10`, MIT, and Development Status
4 (Beta). Both files are non-yanked:

- wheel: `hypogenic-0.3.5-py3-none-any.whl`, 96,169 bytes,
  SHA-256
  `f4ee8d7fa433cd59c58e0a8fe7df2f481ae29e7465a1b30ccbdac2c216a1b755`;
- sdist: `hypogenic-0.3.5.tar.gz`, 65,423 bytes, SHA-256
  `5e1e5590f3612cb606a669909aab117d66577cf078dd56cae0f4123c5e8c44ae`.

PyPI trusted-publisher attestations identify repository
`ChicagoHAI/hypothesis-generation`, tag `v0.3.5`, commit
`8c3800ccae155e333fac5b530afa8abdaac38300`, and the repository's
`publish-to-pypi.yml` workflow. This is sufficient to recommend a pinned PyPI
install, while still requiring ordinary lockfile/hash controls.

The default `master` commit observed was
`bd37a3129a2f98ee586f545a57b10b59496eedad` (2025-07-17). It is four commits
ahead of the release tag; the changed files add logging/visualization support
and a debug option. The `README.md` and `pyproject.toml` blobs are identical
between `v0.3.5` and that master revision, and the source version remains
`0.3.5`. No newer GitHub release or PyPI version was found on 2026-10-01.

Interpretation: artifact, source tag, metadata, and README provenance align.
The branch has small unreleased logging changes, so do not substitute branch
tip for the release.

## Declared dependency surface

The default artifact declares broad compatible-release ranges around:

- NumPy 1.26.3, pandas 2.1.4, datasets 2.16.1;
- Transformers 4.45.1, PyTorch 2.4.0, Accelerate 0.33.0;
- OpenAI 1.40.3, Anthropic 0.32.0, Redis 5.0.1;
- scikit-learn 1.3.0, matplotlib 3.8.0, PuLP 2.9.0;
- PyYAML 6.0.1 and several document/web packages.

The `dev` extra adds vLLM 0.6.2 and `vllm-flash-attn` 2.6.2. Resolve this in an
isolated environment. The package declaration says Python `>=3.10` but does not
state an upper bound; actual resolver/platform support is constrained by those
older compiled dependencies. PyTorch 2.4.1 still has no CPython 3.13 wheels;
use Python 3.12 for a separately resolved upstream environment. This review
executed the small local tools, task/prompt code, and mocked hosted wrappers;
it did not install the full PyTorch/Transformers/vLLM dependency set.

## Verified import and registry surface

The package root does not export `BaseTask`. The source imports used by its own
examples include:

```python
from hypogenic.tasks import BaseTask
from hypogenic.prompt import BasePrompt
from hypogenic.extract_label import extract_label_register
from hypogenic.LLM_wrapper import llm_wrapper_register
```

These are source-level interfaces in 0.3.5, not a separately versioned public
API contract. Prefer the pinned examples when writing custom code.

Registered model wrapper types:

- `gpt`: OpenAI Python client and chat-completions calls;
- `claude`: Anthropic Python client and Messages calls;
- `huggingface`: local Transformers text-generation pipeline;
- `vllm`: local vLLM generation.

Important local-provider limitation: `hypogenic.LLM_wrapper.__init__` imports
both local wrappers from one module, and that module raises when `vllm` is
absent. The exception is caught, leaving both `huggingface` and `vllm`
unregistered. Thus the base install's CLI advertises both choices, but local
wrapper registration depends on the `dev` path in this release.

The hosted wrappers instantiate `OpenAI()` and `Anthropic()` without an
explicit key, so their API-key environment names are `OPENAI_API_KEY` and
`ANTHROPIC_API_KEY`. The pinned SDKs also honor `OPENAI_BASE_URL` and
`ANTHROPIC_BASE_URL`. Consequently the local policy records an intended
destination; it does not enforce the network endpoint or SDK account settings.

## Hosted request and response contracts

Both wrappers use non-streaming requests; there is no pagination or provider
Batch API here. `batched_generate` means local concurrent individual requests.
The following paths/authentication were checked with the pinned SDKs and an
HTTP mock transport; no authenticated service calls were performed.

| Wrapper | Default request | Authentication | Request / returned value |
| --- | --- | --- | --- |
| `gpt` | `POST https://api.openai.com/v1/chat/completions` | SDK Bearer API key | `model`, chat `messages`, `max_tokens`, `temperature`, `n`; reads `usage.prompt_tokens`, `usage.completion_tokens`, then `choices[0].message.content` |
| `claude` | `POST https://api.anthropic.com/v1/messages` | SDK `x-api-key` and `anthropic-version: 2023-06-01` | Extracts one system message into top-level `system`; sends remaining `messages`, `model`, `max_tokens`, `temperature`; reads only `content[0].text` |

Current [OpenAI Chat Completions documentation](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
marks `max_tokens` deprecated and incompatible with o-series models. HypoGeniC
0.3.5 always supplies it; the presence of `o1` and `o3-mini` in its historical
cost table does not make those models compatible. Newer model IDs and dated
snapshots missing from `MODEL_COSTS` raise `KeyError` **after a successful
request**, so they may incur charges without returning a usable result. The
wrapper discards choices after the first even if `n > 1`; keep `n=1`. Its
current code also assumes usage and a text completion exist, and does not check
truncation, refusal, or tool-only responses.

Current [Anthropic Messages documentation](https://platform.claude.com/docs/en/api/messages/create)
rejects non-default temperature for models released after Opus 4.6. The wrapper
always sends `temperature=1e-5` unless overridden. The documented compatibility
value is `1.0`; omission requires a wrapper change. Verify the exact model and
[deprecation table](https://platform.claude.com/docs/en/about-claude/model-deprecations)
before choosing it. Upgrading a model name alone is not an integration test.

The Claude wrapper removes the system entry from the caller's list with
`pop`, requires a system entry although the API itself does not, and assumes
the first returned block is text. Use fresh/deep-copied messages for every call.
It cannot safely handle thinking/tool/mixed-content responses without an
adapter. Any `BadRequestError`, including

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

