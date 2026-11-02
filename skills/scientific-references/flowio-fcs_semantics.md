---
id: sciref-flowio-fcs-semantics
name: "Scientific Ref: FCS Semantics for FlowIO"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (flowio): FCS Semantics for FlowIO"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "flowio fcs semantics"
  - "fcs semantics for flowio"
keywords:
  - "flowio"
  - "fcs"
  - "semantics"
  - "specialized"
  - "scientific"
  - "reference"
---

# FCS Semantics for FlowIO

Use this reference when the task depends on what values or metadata mean, not
just how to call the API.

## Scope

FlowIO reads FCS 2.0, 3.0, and 3.1 and writes a constrained FCS 3.1
representation. It is a file-format library, not a complete flow-cytometry
analysis system.

Before downstream biological interpretation, decide whether the workflow also
requires:

- Spillover compensation
- Logicle, biexponential, or arcsinh transformation
- Quality-control filtering
- Singlet, viability, or population gating
- Batch correction or normalization

FlowIO does none of these. Its optional preprocessing is limited to scaling
defined by FCS acquisition metadata.

## File Segments

An FCS dataset can contain:

- **HEADER**: Version and byte offsets for other segments.
- **TEXT**: Required and optional keyword/value metadata.
- **DATA**: Event values.
- **ANALYSIS**: Optional keyword/value results.

FlowIO exposes these through `header`, `text`, `events`, and `analysis`.

FCS 3.1 deprecated storing multiple datasets in one file through `$NEXTDATA`,
but FlowIO can read legacy multi-dataset files with
`read_multiple_data_sets()`.

## TEXT Keyword Normalization

The FCS standard treats keyword names as case-insensitive. Standard keywords
are written with `$`, but FlowIO normalizes parsed keys:

1. Strip the leading `$`.
2. Convert the key to lowercase.
3. Keep the value as a string.

Examples:

- `$DATE` becomes `text["date"]`
- `$P1N` becomes `text["p1n"]`
- `$SPILLOVER` becomes `text["spillover"]`
- `$NEXTDATA` becomes `text["nextdata"]`

Use:

```python
date = flow.text.get("date")
spill = flow.text.get("spillover", flow.text.get("spill"))
nextdata = int(flow.text.get("nextdata", "0"))
```

Avoid:

```python
date = flow.text.get("$DATE")  # Always misses in FlowIO's normalized mapping.
```

Custom, non-standard keys are also lowercased. The normalized mapping may
contain subject, sample, operator, institution, instrument serial-number, and
free-text fields. Treat an unrestricted metadata dump as potentially
identifying.

FlowIO 1.4.0 implements the first step by removing every `$` character from the
decoded segment before splitting keys and values. A literal `$` inside a value
is therefore lost (`"a$b"` becomes `"ab"`). Do not use the parsed mapping as a
lossless metadata archive.

## Parameters, Labels, and Indices

FCS parameter numbers begin at 1:

- P1N, P2N, ... are required primary labels.
- P1S, P2S, ... are optional descriptive/stain labels.
- PnR records a parameter range.
- PnE records logarithmic amplification information.
- PnG records gain.

FlowIO presents these through two index systems:

- `flow.channels[1]`, `flow.channels[2]`, ... use one-based parameter numbers.
- NumPy columns and all `*_indices` attributes use zero-based indices.

When reporting a channel, label both values if ambiguity matters:

```python
for array_index, pnn in enumerate(flow.pnn_labels):
    parameter_number = array_index + 1
    pns = flow.pns_labels[array_index]
    print(parameter_number, array_index, pnn, pns)
```

PnS is optional. FlowIO inserts `""` for missing PnS entries so that
`pns_labels` and `pnn_labels` have the same length.

FlowIO infers scatter, fluorescence, and time indices from channel labels.
Treat these as conveniences, not a substitute for checking the instrument
panel. Vendor-specific labels may not classify as expected.

`null_channel_list` accepts PnN labels and excludes matching channels from the
derived fluorescence/scatter/time index lists. It does not remove columns from
the event data. `flow.null_channels` stores the supplied labels unchanged; it
does not contain zero-based indices and can retain labels that did not match a
channel.

## Encoded and Preprocessed Event Values

### Encoded representation

`flow.events` is a decoded flattened one-dimensional sequence, ordered by event and
then channel. It is usually an `array.array`; mixed-width integer channels use
a Python `list`:

```text
event_1_channel_1, event_1_channel_2, ..., event_2_channel_1, ...
```

`flow.as_array(preprocess=False)` reshapes that representation to:

```text
(event_count, channel_count)
```

For integer DATA, FlowIO applies the PnR range mask during decoding, before
`as_array()`. Values with high bits outside that range do not retain those bits
in `flow.events` or `preprocess=False`; preserve the original file for byte fidelity.
The number of array rows is inferred from DATA and may disagree with `$TOT`.
Verify shape/counts explicitly.

The returned NumPy array is `float64`, even when the encoded file uses integer
or single-precision event data.

### FlowIO preprocessing

`flow.as_array(preprocess=True)` performs the following operations.

#### Time scaling

When a time channel and nonempty `timestep` keyword exist:

```text
time_scaled = time_encoded * timestep
```

An empty or whitespace-only `timestep` is treated as `1.0` in FlowIO 1.4.0.

#### Logarithmically stored channels

For PnE `(decades, log_zero)` and PnR `range`:

```text
linear_value = 10 ** (decades * encoded_value / range) * log_zero
```

The conversion is applied when `decades > 0`. FlowIO replaces a zero
`log_zero` with `1.0` when decades is nonzero.

#### Gain

For PnG `gain`:

```text
gain_scaled = value / gain
```

FlowIO skips division when gain is zero or one. For a recognized non-null
channel named `Time` (case-insensitive), FlowIO forces the parsed channel
gain to `1.0`, regardless of TEXT PnG; `timestep` scaling still applies.

The operations are metadata-driven. Bad metadata can therefore produce bad
scaled values even when the DATA bytes were parsed correctly.

### What preprocessing does not do

FlowIO does not:

- Parse and apply `$SPILL`/`$SPILLOVER` compensation
- Perform logicle, biexponential, hyperlog, or arcsinh transformation
- Normalize between files
- Identify acquisition anomalies
- Remove debris, doublets, or dead cells
- Gate populations

For compensation/transformation/gating, use a higher-level package such as
FlowKit and preserve a record of the matrix and transform parameters.

## Spillover Metadata

FlowIO can expose or write a spillover keyword as a string. It does not validate
the matrix scientifically or apply it.

A standard spillover string begins with:

1. Number of compensated fluorescence parameters
2. Matching PnN labels
3. Flattened matrix values

Items are comma-delimited with no newline characters.

Before passing the matrix downstream:

- Confirm the labels 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

