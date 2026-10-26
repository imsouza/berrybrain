---
id: sciref-hypogenic-sources
name: "Scientific Ref: Dated official sources and verification"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (hypogenic): Dated official sources and verification"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "hypogenic sources"
  - "dated official sources and verification"
keywords:
  - "hypogenic"
  - "sources"
  - "specialized"
  - "scientific"
  - "reference"
  - "dated"
  - "official"
---

# Dated official sources and verification

Review date: **2026-10-01**. The July 2026 review remains historical evidence;
package, source, dataset revisions, provider contracts and the local tools were
rechecked for this refresh. Source inspection and mock transport tests are not
authenticated provider or scientific validation.

## Release and implementation

- [PyPI package](https://pypi.org/project/hypogenic/) and
  [official metadata](https://pypi.org/pypi/hypogenic/json): latest release
  remains 0.3.5, released 2025-07-16, Python >=3.10, beta classifier, MIT,
  dependencies, artifact hashes and trusted-publisher provenance. The 96,169-byte
  wheel was downloaded and its SHA-256 matched the metadata.
- [Official repository](https://github.com/ChicagoHAI/hypothesis-generation),
  [latest release](https://api.github.com/repos/ChicagoHAI/hypothesis-generation/releases/latest),
  and [default branch](https://api.github.com/repos/ChicagoHAI/hypothesis-generation/commits/master):
  v0.3.5 and master `bd37a3129a2f98ee586f545a57b10b59496eedad` remain unchanged.
- [Pinned release source](https://github.com/ChicagoHAI/hypothesis-generation/tree/8c3800ccae155e333fac5b530afa8abdaac38300)
  and [pyproject](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/pyproject.toml):
  source/API review targets this exact version rather than an unpinned branch.
- [Generation CLI](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic_cmd/generation.py),
  [inference CLI](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic_cmd/inference.py),
  and [logger](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/logger_config.py):
  parser flags and positional arguments, early help exit, swapped logger and
  hosted-wrapper constructor arguments, small-bank assertion and averaging bug.
- [Task loader](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/tasks.py)
  and [prompt implementation](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/prompt.py):
  config fields, column JSON, sampling, return order, OOD aliasing, and template
  substitution. The shipped template rendered locally with synthetic examples.
- [Model wrappers](https://github.com/ChicagoHAI/hypothesis-generation/tree/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/LLM_wrapper):
  SDK calls, cost table, local registration, model loading, retries, message
  mutation, block assumptions and error behavior. Executed hosted paths used
  mock HTTP responses and stubbed heavy import-only dependencies.
- [Output serializer](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/algorithm/update/base.py)
  and [SummaryInformation](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/algorithm/summary_information.py):
  JSON hypothesis-bank structure and stored statistics.
- [Redis cache](https://github.com/ChicagoHAI/hypothesis-generation/blob/8c3800ccae155e333fac5b530afa8abdaac38300/hypogenic/LLM_cache.py):
  cache keys, prompt/response storage and pickle serialization. No Redis server
  was started or contacted.
- [PyTorch 2.4.1 release metadata](https://pypi.org/pypi/torch/2.4.1/json):
  no CPython 3.13 wheels; the upstream package's `torch~=2.4.0` range still
  prevents the default repository interpreter from installing its full stack.
- [PyYAML release metadata](https://pypi.org/pypi/PyYAML/json) and
  [parser documentation](https://pyyaml.org/wiki/PyYAMLDocumentation): reviewed
  local parser pin advanced to 6.0.3. Valid YAML and rejection of duplicate keys,
  aliases, anchors, tags, dates and malformed input were exercised locally.

## Datasets

- [HypoBench GitHub repository](https://github.com/ChicagoHAI/HypoBench-datasets)
  and [default commit](https://api.github.com/repos/ChicagoHAI/HypoBench-datasets/commits/main):
  remain at `7e4bbc341ee90b7efaa607f67a81543cd68cdf2e`.
- [Pinned dataset tree](https://github.com/ChicagoHAI/HypoBench-datasets/tree/7e4bbc341ee90b7efaa607f67a81543cd68cdf2e):
  the deceptive-review config and train/validation/test JSON hashes were
  rechecked; 800/300/500 rows and three cross-split duplicate groups reproduced.
  The optional OOD file was acquired only to verify the task's path contract.
- [Official Hugging Face publication](https://huggingface.co/datasets/ChicagoHAI/HypoGeniC-datasets)
  and [Hub metadata](https://huggingface.co/api/datasets/ChicagoHAI/HypoGeniC-datasets):
  revision remains `613860dcbcda9e522a6163ee9edf78c261ebe4bb`.

## Provider contracts and privacy

- [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create):
  request and response fields, legacy `max_tokens`, choice/usage semantics and
  incompatibility with o-series models. The pinned OpenAI 1.40.3 SDK was exercised
  through HTTPX MockTransport; it sent the documented route and Bearer header.
- [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
  and [deprecations](https://developers.openai.com/api/docs/deprecations):
  endpoint/model-specific storage and availability must be checked at execution
  time. This review did not query an authenticated model catalog or account.
- [Anthropic Messages](https://platform.claude.com/docs/en/api/messages/create):
  top-level system field, content-block response, version header, token parameter,
  and current temperature restriction. Anthropic 0.32.0 sent the expected route,
  `x-api-key` and API-version header in mock transport tests.
- [Anthropic model deprecations](https://platform.claude.com/docs/en/about-claude/model-deprecations):
  retired model IDs and rejection of non-default temperature on newer models.
- [Anthropic API retention](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
  and [commercial retention](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data):
  standard deletion policy, exceptions, ZDR eligibility, and covered-model
  30-day requirements. No account-specific arrangement was verified.
- [OpenAI 1.40.3 client source](https://github.com/openai/openai-python/blob/v1.40.3/src/openai/_

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

