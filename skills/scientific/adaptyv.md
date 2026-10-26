---
id: sci-adaptyv
name: "Scientific: adaptyv"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Uses the Adaptyv Bio Foundry API and Python SDK to design protein characterization experiments, estimate costs, submit sequences, monitor laboratory progress, and retrieve results. Applies to Adaptyv Foundry, its target catalog, binding screening and affinity assays, thermostabil"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "adaptyv"
keywords:
  - "adaptyv"
  - "uses"
  - "foundry"
  - "python"
  - "design"
  - "protein"
---

# Adaptyv Bio Foundry API

Use this skill to turn protein sequences into experimentally measured data through
Adaptyv's cloud laboratory. Confirm the target construct, assay conditions, controls,
and replicate plan before submitting a batch; turnaround depends on the experiment.

Reviewed against the deployed [OpenAPI schema](https://devs.adaptyvbio.com/api/v1/openapi.json)
(`info.version: 0.0.2`) and official SDK `0.1.0` at commit
`cdf207819ed5a58e0c127453626d2bce125c8064`. The schema version alone does not identify
all changes. See the [endpoint reference](references/api-endpoints.md) for current
request/response details and discrepancies in upstream examples.

## Connect

**Base URL:** `https://devs.adaptyvbio.com/api/v1`. The schema is at
`/openapi.json`; never append that filename to normal endpoint requests.

Create a bearer token in [Foundry](https://foundry.adaptyvbio.com/) under
Organization → Settings → Tokens. Use Viewer for reads and Member for experiment
writes. Read credentials from `ADAPTYV_API_KEY`; the documentation's
`FOUNDRY_API_TOKEN` is an alternative variable name for the same token. If using a
project `.env`, explicitly call `python-dotenv.load_dotenv()` before SDK setup;
the SDK does not load that file automatically. Never print or commit tokens.

```bash
# ADAPTYV_API_KEY is already set in the environment.
curl --fail-with-body 'https://devs.adaptyvbio.com/api/v1/targets?limit=3' \
  -H "Authorization: Bearer $ADAPTYV_API_KEY"
```

Resource endpoints require bearer authentication. The schema and liveness endpoint
`GET /info/health` are public. `GET /whoami` reports the active organization and
permissions; check it when account scope is unclear.

## Python SDK

Install the reviewed revision in your project environment (requires Python 3.11+):

```bash
uv pip install "git+https://github.com/adaptyvbio/adaptyv-sdk.git@cdf207819ed5a58e0c127453626d2bce125c8064"
```

Import from `adaptyv`, not `adaptyv_sdk`. `FoundryClient` requires explicit `api_key`
and `base_url`; the `lab` convenience object reads `ADAPTYV_API_KEY` and
`ADAPTYV_API_URL`. Set the latter to the base URL above to override the SDK's
older hostname default.

The following examples are illustrative for authenticated use. Their request
construction and parsing were checked with mocked HTTP responses, not a paid lab
run. Replace environment inputs with real, reviewed sequence data and catalog IDs.

### Browse, estimate, create a draft

```python
import json
import os
from pathlib import Path
from adaptyv import FoundryClient

client = FoundryClient(
    api_key=os.environ["ADAPTYV_API_KEY"],
    base_url="https://devs.adaptyvbio.com/api/v1",
)

# Review vendor, catalog number, construct, and pricing before selecting an ID.
targets = client.targets.list(search="EGFR", selfservice_only=True, detailed=True)
for target in targets.items:
    print(target.id, target.name, target.vendor_name, target.catalog_number)

# candidates.json is a map of unique names to full amino acid sequences.
sequences = json.loads(Path("candidates.json").read_text())
spec = {
    "experiment_type": "screening",
    "method": "bli",
    "target_id": os.environ["ADAPTYV_TARGET_ID"],
    "sequences": sequences,
    "n_replicates": 3,
}

# SDK takes the spec itself; REST takes {"experiment_spec": spec}.
estimate = client.experiments.cost_estimate(spec)
if estimate.breakdown is None:
    raise ValueError("Incomplete estimate: review warnings and obtain a full quote")
print("Estimated USD cents, excluding VAT:", estimate.breakdown.total_cents)

# After the batch and estimated cost have been reviewed:
exp = client.experiments.create(name="EGFR binder screen batch 1", experiment_spec=spec)
experiment_id = exp.experiment_id
client.close()
```

`create(name=..., experiment_spec=...)` does not accept a single REST-body dictionary.
`cost_estimate(spec)` wraps the spec itself; do not wrap it a second time.
For an affinity experiment, the SDK additionally requires explicit
`antigen_concentrations`, even though REST supplies a default when omitted.

### Submit, then inspect and confirm the quote

With a configured client and the saved `experiment_id`:

```python
client.experiments.submit(experiment_id)
# Quote generation is asynchronous. Retry get_quote with a bounded timeout if it
# returns 404 after successful submission; a draft has no forthcoming quote.
quote = client.experiments.get_quote(experiment_id)
print(quote.amount_total, quote.currency, quote.expires_at)

# Once the quote is accepted within the user's authorized scope:
accepted = client.experiments.confirm_quote(experiment_id)
print(accepted.invoice_id, accepted.hosted_invoice_url)
```

Confirmation creates/finalizes an invoice; it does not settle payment. Use the
returned hosted invoice URL or the current REST payment pointer. SDK 0.1.0 does
not expose invoice payment, organization webhooks, or `whoami` helpers.

Avoid the reviewed SDK's `lab.experiment(target="EGFR")` shortcut: it passes only
UUID-shaped targets and does not resolve a target name. `auto_confirm=True` and
`lab.confirm_experiment()` call submission, not the quote-confirm endpoint. Use
the explicit client methods above. The decorator also supplies `method` for
non-binding experiments, which the current API rejects.

### Retrieve every result without losing fields

The SDK's generated models predate some live result fields and may discard them.
Use REST JSON when archiving results, target references, or newer kinetic fits:

```python
import json
import os
from pathlib import Path
import httpx

experiment_id = os.environ["ADAPTYV_EXPERIMENT_ID"]
with httpx.Client(
    base_url="https://devs.adaptyvbio.com/api/v1",
    headers={"Authorization": f"Bearer {os.environ['ADAPTYV_API_KEY']}"},
    timeout=30,
) as api:
    response = api.get(f"/experiments/{experiment_id}")
    response.raise_for_status()
    experiment = response.json()
    if experiment["results_status"] != "all":
        raise RuntimeError("Results are not complete; inspect status before analysis")
    results, offset = [], 0
    while True:
        response = api.get(f"/experiments/{experiment_id}/results",
                           params={"limit": 100, "offset": offset})
        response.raise_for_status()
        page = response.json()
        results.extend(page["items"])
        offset += len(page["items"])
        if not page["items"] or offset >= page["total"]:
            break
Path("foundry-results.json").write_text(json.dumps(
    {"expe

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

