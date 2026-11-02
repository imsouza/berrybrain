---
id: sciref-flowio-troubleshooting
name: "Scientific Ref: FlowIO Troubleshooting and Safety"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (flowio): FlowIO Troubleshooting and Safety"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "flowio troubleshooting"
  - "flowio troubleshooting and safety"
keywords:
  - "flowio"
  - "troubleshooting"
  - "specialized"
  - "scientific"
  - "reference"
---

# FlowIO Troubleshooting and Safety

Use the narrowest remedy that matches the observed failure. Keep the original
file unchanged and record every recovery option used.

## Confirm the Runtime First

```bash
uv run python -c "import flowio; print(flowio.__version__)"
```

This skill targets `1.4.0`. If the runtime differs, inspect that release's API
and changelog before assuming examples are compatible.

## Import Errors for Exceptions

Symptom:

```text
ImportError: cannot import name 'FCSParsingError' from 'flowio'
```

Cause: Exception classes are not top-level exports.

Correct:

```python
from flowio import FlowData
from flowio.exceptions import FCSParsingError
```

## `MultipleDataSetsError`

Symptom: Opening a file with `FlowData(...)` reports that it contains multiple
datasets.

Use:

```python
from flowio import read_multiple_data_sets

datasets = read_multiple_data_sets("legacy.fcs")
```

Do not manually treat `text["nextdata"]` as an absolute offset. The legacy
format uses relative offsets, and FCS 3.1 deprecated this representation.

## `DataOffsetDiscrepancyError`

Symptom: HEADER and TEXT identify different DATA byte locations.

Default behavior is correct: stop rather than guessing.

Triage:

1. Preserve the source file and calculate a checksum.
2. Confirm the file came directly from a known instrument/exporter.
3. Check vendor documentation or a known-good file from the same software.
4. Prefer TEXT offsets only when evidence supports them:

   ```python
   flow = FlowData(
       "known-file.fcs",
       ignore_offset_discrepancy=True,
   )
   ```

5. Use HEADER offsets only when evidence supports HEADER:

   ```python
   flow = FlowData(
       "known-file.fcs",
       use_header_offsets=True,
   )
   ```

6. Validate event count, channel ranges, distributions, and controls.

Do not set both options reflexively or make them global defaults.

## Off-by-One DATA Offset

Some producers report the final DATA byte as exclusive rather than inclusive.
For a known instance:

```python
flow = FlowData(
    "known-off-by-one.fcs",
    ignore_offset_error=True,
)
```

FlowIO emits a warning stating that event data should be reviewed. Preserve
that warning in logs and perform distribution/control checks.

## Large Files With Zero HEADER DATA Offsets

FCS 3.1 requires HEADER DATA offsets to be zero when a segment extends beyond
the eight-digit HEADER limit; real offsets remain in TEXT. FlowIO recognizes
this case.

Do not enable `use_header_offsets=True` merely because the file is large.
Doing so can select zeros instead of the valid TEXT values.

## `only_text=True` Followed by Array Failure

Symptom: `as_array()` fails after metadata-only parsing.

Cause: `only_text=True` intentionally leaves `events` unset.

Reopen normally:

```python
metadata_only = FlowData("sample.fcs", only_text=True)
# ...decide whether full loading is safe...
with_events = FlowData("sample.fcs")
events = with_events.as_array()
```

## Unexpected Metadata Lookup Results

Symptom: `flow.text.get("$DATE")` returns `None`.

Use normalized keys:

```python
flow.text.get("date")
flow.text.get("cyt")
flow.text.get("spillover", flow.text.get("spill"))
```

All parsed keys are lowercase and omit `$`.

FlowIO 1.4.0 also removes literal `$` characters inside values. If exact TEXT
fidelity is required, inspect the source bytes with a standards-aware tool
rather than reconstructing metadata from `flow.text`.

## Unexpected Event Values

Compare both representations:

```python
encoded = flow.as_array(preprocess=False)
scaled = flow.as_array(preprocess=True)
```

Then inspect:

- `flow.data_type`
- `flow.channels[n]["pne"]`
- `flow.channels[n]["png"]`
- `flow.channels[n]["pnr"]`
- `flow.text.get("timestep")`
- `flow.time_index`

FlowIO preprocessing divides by gain; it does not multiply by gain. It also
does not apply compensation. If values differ from a higher-level application,
check whether that application applied compensation, display transforms, or
vendor-specific scaling.

For integer DATA, `preprocess=False` still contains PnR-masked decoded values.
Also check `flow.text.get(f"p{n}g")` (with the actual parameter number) against
`flow.channels[n]["png"]`: a recognized Time channel is forced to gain one.

## Declared Counts Disagree With DATA

`as_array()` infers rows from loaded DATA and does not enforce `$TOT`. Check
`len(flow.events) == flow.event_count * flow.channel_count` before converting
and compare the resulting shape. Do not silently replace the declared count
or trust metadata-only inspection as a DATA validation. The bundled inspector
rejects this mismatch with `--stats`.

## Channel Classification Looks Wrong

`scatter_indices`, `fluoro_indices`, and `time_index` are label-based
conveniences. Instrument/vendor labels can be unusual.

Inspect all channel metadata:

```python
for parameter_number, channel in flow.channels.items():
    print(parameter_number, channel)
```

Use an explicit, provenance-backed mapping for downstream analysis. Do not
rename columns solely from guessed channel type.

`flow.null_channels` contains PnN labels supplied through
`null_channel_list`, not integer indices. Matching labels are omitted from the
derived index lists but remain in the event array.

## Closed File Handle

`FlowData` closes a file handle passed by the caller. Do not expect to reuse it:

```python
with open("sample.fcs", "rb") as handle:
    flow = FlowData(handle)
    # handle is already closed here by FlowIO 1.4.0
```

Prefer a path. In particular, pass a path to `read_multiple_data_sets()`;
passing one handle fails when the utility tries to read the second dataset
after the first `FlowData` closed it.

## Duplicate or Empty DataFrame Columns

PnN values may be duplicated or malformed, and PnS is optional. Validate and
make names unique before constructing a DataFrame. Retain the original PnN/PnS
lists in provenance.

See `workflows.md` for a deterministic `unique_labels()` helper that also
avoids collisions with existing names such as `FL1-A__2`. Keep the original
PnN mapping for compensation metadata.

## `create_fcs()` Receives a Path

Incorrect:

```python
create_fcs("output.fcs", values, labels)
```

Correct:

```python
with open("output.fcs", "xb") as handle:
    create_fcs(handle, values.ravel(order="C"), labels)
```

The first argument is a binary file handle, not a path.

## `create_fcs()` Receives a 2-D Array

The writer expects flattened event data. Validate before flattening:

```pyt

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

