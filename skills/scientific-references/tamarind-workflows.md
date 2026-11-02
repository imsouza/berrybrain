---
id: sciref-tamarind-workflows
name: "Scientific Ref: Tamarind Bio HTTP workflow recipes"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (tamarind): Tamarind Bio HTTP workflow recipes"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "tamarind workflows"
  - "tamarind bio http workflow recipes"
keywords:
  - "tamarind"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
  - "http"
---

# Tamarind Bio HTTP workflow recipes

These Python recipes target the official REST contracts reviewed **2026-09-30**.
They were smoke-tested locally using simulated responses, including failure,
normalization, pagination, and asynchronous-result cases. They have **not** been
executed against an authenticated Tamarind account. Scientific submissions below
are illustrative and consume compute when run.

Use Python 3.10+ and `requests`; set `TAMARIND_API_KEY` outside code. On a dedicated
organization deployment set `TAMARIND_BASE_URL` to that host's `/api` base. Save
job names so long runs can be checked in a later session.

## Common helpers

Copy this block into the working script. Validation is part of submission; the
result downloader only handles retrieval and never creates a replacement job.

```python
import json
import os
import re
import time
from pathlib import Path

import requests

BASE = os.environ.get("TAMARIND_BASE_URL", "https://app.tamarind.bio/api").rstrip("/")
HEADERS = {"x-api-key": os.environ["TAMARIND_API_KEY"]}
TERMINAL = {"Complete", "Stopped", "Failed", "Deleted"}


def api(method, path, *, timeout=(10, 60), **kwargs):
    response = requests.request(method, BASE + path, headers=HEADERS,
                                timeout=timeout, **kwargs)
    response.raise_for_status()  # inspect response body on HTTPError
    return response


def clean_name(name):
    # Use conservative names that exact GET /jobs can address.
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", name):
        raise ValueError("Use a nonempty clean name of at most 200 characters")
    return name


def validate_settings(tool_type, settings, name=None):
    payload = {"type": tool_type, "settings": settings}
    if name is not None:
        payload["jobName"] = clean_name(name)
    verdict = api("POST", "/validate-job", json=payload).json()
    if not verdict.get("valid") or verdict.get("unrecognized_settings"):
        raise ValueError(f"Validation needs attention: {verdict}")
    return verdict


def submit_checked(tool_type, settings, name, project_tag=None):
    verdict = validate_settings(tool_type, settings, name)
    stored_name = clean_name(verdict.get("job_name", name))
    payload = {"jobName": stored_name, "type": tool_type,
               "settings": verdict["normalized"]}
    if project_tag is not None:
        payload["projectTag"] = project_tag
    # Persist before submitting; a timeout may still have queued the job.
    Path(f"{stored_name}.submission.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    response = api("POST", "/submit-job", json=payload)
    suffix = " submitted to queue."
    if not response.text.endswith(suffix):
        raise RuntimeError("Unexpected receipt; inspect the persisted name before retrying")
    return clean_name(response.text[:-len(suffix)])


def wait_job(name, *, batch=False, max_seconds=3600, interval=30):
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        row = api("GET", "/jobs", params={"jobName": name}).json()
        if batch:
            status = row.get("batchStatus")
            if status == "Complete":
                return row
            if status in {"Stopped", "AggregationFailed"} or row.get("JobStatus") in {
                "Stopped", "Failed", "Deleted"
            }:
                raise RuntimeError(f"Batch {name}: {row.get('AggregationError') or status}")
        else:
            status = row.get("JobStatus")
            if status in TERMINAL:
                return row
        time.sleep(interval)
    raise TimeoutError(f"Still pending: {name}; resume lookup later, do not resubmit")


def download_result(name, destination, *, file_name=None, max_seconds=3600):
    payload = {"jobName": name}
    if file_name is not None:
        payload["fileName"] = file_name
    deadline = time.monotonic() + max_seconds
    while time.monotonic() < deadline:
        # /result may wait about 290 seconds while assembling an archive.
        response = api("POST", "/result", json=payload, timeout=(10, 310))
        if response.status_code == 202:
            if response.json().get("status") != "preparing":
                raise RuntimeError("Unexpected asynchronous result response")
            time.sleep(30)
            continue
        if response.status_code != 200:
            raise RuntimeError(f"Unexpected result status: {response.status_code}")
        url = response.json()  # JSON string, not .text.strip('"')
        if not isinstance(url, str) or not url.startswith("https://"):
            raise ValueError("Result response did not contain an HTTPS download URL")
        # No Tamarind API key on a storage request. Stream potentially large zips.
        with requests.get(url, stream=True, timeout=(10, 120)) as download:
            download.raise_for_status()
            with Path(destination).open("wb") as handle:
                for chunk in download.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
        return
    raise TimeoutError(f"Archive still preparing for {name}; retry retrieval later")


def iter_jobs(**selectors):
    params = {"limit": 1000, **selectors}
    while True:
        page = api("GET", "/jobs", params=params).json()
        yield from page["jobs"]
        cursor = page.get("startKey")
        if not cursor:
            return
        params["startKey"] = cursor
```

A timeout is a local waiting limit, not cancellation. Inspect the persisted name
before retrying a submission. The helpers deliberately do not automatically
retry a state-changing request.

## 1. Discover, inspect, and fold a sequence

```python
tools = api("GET", "/tools").json()
tool = next(t for t in tools if t["name"] == "alphafold")
schema = api("GET", f"/tools/{tool['name']}/schema").json()
# Inspect schema and selected defaults before executing this illustrative job.
sequence = "MQIFVKTLTGKTITLEVEPSDTIENVKAKIQDKEGIPPDQQRLIFAGKQLEDGRTLSDYNIQKESTLHLVLRLRGG"
name = submit_checked(tool["name"], {"sequence": sequence}, "ubiquitin-fold")
print("[OK] Submitted", name)
```

Check in a later session, or use bounded polling for a short run:

```python
name = "ubiquitin-fold"  # use the stored name returned at submission
row = wait_job(name)
if row["JobStatus"] == "Complete":
    download_result(name, f"{name}.zip")
elif row["JobStatus"] in {"Stopped", "Failed"}:
    download_resul

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

