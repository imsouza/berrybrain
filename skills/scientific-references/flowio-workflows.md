---
id: sciref-flowio-workflows
name: "Scientific Ref: FlowIO Workflows"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (flowio): FlowIO Workflows"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "flowio workflows"
keywords:
  - "flowio"
  - "workflows"
  - "specialized"
  - "scientific"
  - "reference"
---

# FlowIO Workflows

These patterns target `flowio==1.4.0`. Examples below were exercised with
synthetic files; placeholder filenames and `source_events` must be supplied for
real data. Keep raw files immutable and write derived outputs separately.

## 1. Inventory a File Without Loading Events

Use `only_text=True` when the goal is file structure, labels, or acquisition
metadata:

```python
from pathlib import Path

from flowio import FlowData

path = Path("sample.fcs")
flow = FlowData(path, only_text=True)

summary = {
    "file": path.name,
    "size_bytes": path.stat().st_size,
    "fcs_version": flow.version,
    "data_type": flow.data_type,
    "event_count": flow.event_count,
    "channel_count": flow.channel_count,
    "pnn_labels": flow.pnn_labels,
    "pns_labels": flow.pns_labels,
    "date": flow.text.get("date"),
    "instrument": flow.text.get("cyt"),
}
print(summary)
```

Do not call `as_array()` on this object.
`only_text=True` skips DATA loading but still parses ANALYSIS.

For an inventory that also handles multi-dataset files and emits JSON, use:

```bash
FLOWIO_SKILL_DIR="skills/flowio"  # Set to the installed skill directory.
uv run --no-project --with "flowio==1.4.0" \
  python "$FLOWIO_SKILL_DIR/scripts/inspect_fcs.py" sample.fcs
```

## 2. Load Encoded or Metadata-Scaled Events

```python
from flowio import FlowData

flow = FlowData("sample.fcs")

# Gain/log/time scaling from FCS metadata.
scaled = flow.as_array(preprocess=True)

# Decoded DATA values without gain/log/time scaling (integer masks remain).
encoded = flow.as_array(preprocess=False)

assert scaled.shape == (flow.event_count, flow.channel_count)
assert encoded.shape == scaled.shape
```

Check shape against both declared counts: FlowIO infers the number of rows from
DATA rather than validating `$TOT`. Integer DATA has already been masked to its
PnR range even with `preprocess=False`. Neither array is compensated or gated.
Name output variables to preserve this distinction; avoid generic names such
as `processed`.

## 3. Build a DataFrame

This example assumes pandas is already present in the project environment.
Add and lock an environment-compatible pandas release only when tabular
integration is required; FlowIO itself does not depend on pandas. The tested
pandas 3.0.6 stack is for standalone FlowIO. FlowKit has separate dependency
constraints, so retain the compatible pandas version in its environment.

FCS files can contain duplicate or empty labels. Make DataFrame names unique
instead of silently assuming PnN values are valid columns:

```python
import pandas as pd
from flowio import FlowData


def unique_labels(labels):
    bases = [value.strip() or f"channel_{i + 1}" for i, value in enumerate(labels)]
    reserved = set(bases)  # Do not steal a later detector's existing name.
    used = set()
    result = []
    for base in bases:
        name = base
        if name in used:
            suffix = 2
            while f"{base}__{suffix}" in reserved or f"{base}__{suffix}" in used:
                suffix += 1
            name = f"{base}__{suffix}"
        used.add(name)
        result.append(name)
    return result


flow = FlowData("sample.fcs")
columns = unique_labels(flow.pnn_labels)
assert len(columns) == len(set(columns))
values = flow.as_array(preprocess=True)
if values.shape != (flow.event_count, flow.channel_count):
    raise ValueError("DATA shape disagrees with declared event/channel counts")
frame = pd.DataFrame(
    values,
    columns=columns,
)

frame.attrs.update(
    {
        "flowio_version": "1.4.0",
        "fcs_version": flow.version,
        "event_semantics": "gain/log/time scaled; uncompensated; ungated",
        "source_pnn_labels": flow.pnn_labels,
        "source_pns_labels": flow.pns_labels,
    }
)
```

For example, `["A", "A", "A__2"]` becomes `["A", "A__3", "A__2"]`.
The position-to-source-label mapping is authoritative; never use renamed export
labels to align a spillover matrix.

DataFrame attributes are not preserved by every export format. Store a
sidecar JSON provenance record for durable pipelines.

## 4. Export CSV Safely

CSV loses most FCS metadata and type information. Export a sidecar record:

```python
import json
from pathlib import Path

import pandas as pd
from flowio import FlowData

source = Path("sample.fcs")
flow = FlowData(source)
values = flow.as_array(preprocess=False)
if values.shape != (flow.event_count, flow.channel_count):
    raise ValueError("DATA shape disagrees with declared event/channel counts")

frame = pd.DataFrame(
    values,
    columns=unique_labels(flow.pnn_labels),  # Helper from the previous workflow.
)
csv_path = Path("sample.events.csv")
with csv_path.open("x", encoding="utf-8", newline="") as handle:
    frame.to_csv(handle, index=False)

provenance = {
    "source_file": source.name,
    "flowio_version": "1.4.0",
    "fcs_version": flow.version,
    "event_semantics": "decoded DATA values; preprocess=False; integer range masks retained",
    "pnn_labels": flow.pnn_labels,
    "pns_labels": flow.pns_labels,
    "event_count": flow.event_count,
    "channel_count": flow.channel_count,
}
with Path("sample.events.json").open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(provenance, indent=2) + "\n")
```

Before sharing either output, review labels and metadata for subject or sample
identifiers.

## 5. Batch Metadata Inventory

This pattern reads no event arrays:

```python
from pathlib import Path

from flowio import read_multiple_data_sets
from flowio.exceptions import FlowIOException

records = []
failures = []

for path in sorted(Path("fcs").rglob("*.fcs")):
    try:
        datasets = read_multiple_data_sets(path, only_text=True)
        for dataset_index, flow in enumerate(datasets):
            records.append(
                {
                    "file": str(path),
                    "dataset_index": dataset_index,
                    "fcs_version": flow.version,
                    "event_count": flow.event_count,
                    "channel_count": flow.channel_count,
                    "pnn_labels": flow.pnn_labels,
                }
            )
    except (FlowIOException, OSError, ValueError) as error:
        failures.append({"file": str(path), "error": str(error)})
```

Do not automatically retry failed files with every relaxed offset option.
Triage each error type and file source.

## 6. Read Legacy Multi-Dataset Files

Pass a path, not an open handle. FlowIO 1.4.0 closes caller-provid

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

