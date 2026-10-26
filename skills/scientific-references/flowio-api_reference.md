---
id: sciref-flowio-api-reference
name: "Scientific Ref: FlowIO 1.4.0 API Reference"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (flowio): FlowIO 1.4.0 API Reference"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "flowio api reference"
  - "flowio 1.4.0 api reference"
keywords:
  - "flowio"
  - "api"
  - "reference"
  - "specialized"
  - "scientific"
---

# FlowIO 1.4.0 API Reference

This reference records the public API and behavior of the stable
`flowio==1.4.0` release. Prefer the exact parameter names shown here.

## Public Imports

```python
from flowio import (
    FlowData,
    create_fcs,
    fcs_keywords,
    read_multiple_data_sets,
)
from flowio.exceptions import (
    DataOffsetDiscrepancyError,
    FCSParsingError,
    FlowIOException,
    FlowIOWarning,
    MultipleDataSetsError,
    PnEWarning,
)
```

Exception classes are not re-exported at the top-level `flowio` namespace.
Import them from `flowio.exceptions`.

## `FlowData`

### Signature

```python
FlowData(
    fcs_file,
    ignore_offset_error=False,
    ignore_offset_discrepancy=False,
    use_header_offsets=False,
    only_text=False,
    nextdata_offset=None,
    null_channel_list=None,
)
```

### Parameters

- `fcs_file`: Local path string, `pathlib.Path`, or readable binary file
  handle. `FlowData` closes the handle after parsing, including a
  caller-provided handle.
- `ignore_offset_error`: Permit a DATA end offset that is off by one byte.
  FlowIO emits a warning because event values still require review.
- `ignore_offset_discrepancy`: Suppress the error raised when HEADER and TEXT
  DATA offsets disagree. FlowIO uses the TEXT offsets unless
  `use_header_offsets=True`.
- `use_header_offsets`: Use DATA offsets from HEADER. This also suppresses the
  HEADER/TEXT discrepancy error.
- `only_text`: Parse metadata without loading the DATA segment. `events` is
  `None`, so `as_array()` must not be called. HEADER, TEXT, and ANALYSIS are
  still parsed.
- `nextdata_offset`: Internal/careful-use byte offset for one dataset in a
  multi-dataset file. Prefer `read_multiple_data_sets()`.
- `null_channel_list`: PnN labels for channels not intended for analysis.
  Matching channels are omitted from `fluoro_indices`, `scatter_indices`, and
  `time_index`. The supplied label list is stored unchanged in
  `null_channels`; it is not converted to indices and may include labels that
  were not present.

### File support

- FCS versions: 2.0, 3.0, and 3.1
- DATA mode: list mode (`$MODE=L`)
- Event types used in practice: integer (`I`), single precision (`F`), and
  double precision (`D`)
- Correlated and uncorrelated histogram modes (`C` and `U`) are unsupported.
  The released parser only explicitly rejects lowercase `c`/`u`; uppercase
  values can be interpreted as list data. Validate `flow.text["mode"].upper() == "L"`
  before downstream use. The bundled inspector enforces this.

The FCS standard defines ASCII (`A`) DATA, but FlowIO 1.4.0 does not provide a
reliable ASCII parser path. Do not claim ASCII event-data support without a
fixture-specific test.

### Core attributes

- `name`: Source file name, or `"InMemoryFile"` for a nameless handle.
- `file_size`: Source size in bytes.
- `version`: FCS version string.
- `header`: Parsed HEADER values.
- `text`: Parsed TEXT keyword/value mapping.
- `analysis`: Parsed ANALYSIS keyword/value mapping, or an empty mapping when
  absent.
- `data_type`: `$DATATYPE` value from the file.
- `channel_count`: Number of parameters/channels (`$PAR`).
- `event_count`: Number of events (`$TOT`).
- `events`: Flattened one-dimensional sequence of decoded event values, usually
  `array.array`. Mixed-width integer channels use a Python `list`.
  `events` is `None` when `only_text=True`.
- `channels`: Mapping whose keys are one-based FCS parameter numbers. Each value
  contains:
  - `pnn`: required PnN label
  - `pns`: optional PnS label, or `""`
  - `pne`: `(decades, log_zero)` tuple
  - `png`: gain as `float`, defaulting to `1.0`; forced to `1.0` for a
    recognized, non-null `Time` channel regardless of the TEXT PnG value
  - `pnr`: range as `float`
- `pnn_labels`: Required channel labels in array-column order.
- `pns_labels`: Optional channel labels in array-column order; missing values
  are empty strings.
- `pnr_values`: Channel ranges in array-column order.
- `fluoro_indices`: Zero-based fluorescence-channel indices inferred by
  FlowIO.
- `scatter_indices`: Zero-based scatter-channel indices inferred by FlowIO.
- `time_index`: Zero-based time-channel index, or `None`.
- `null_channels`: PnN label strings supplied through `null_channel_list`.

### TEXT and ANALYSIS normalization

FlowIO removes `$` from standard keyword names, converts every key to
lowercase, and retains values as strings:

```python
flow.text["par"]
flow.text.get("date")
flow.text.get("spillover", flow.text.get("spill"))
flow.text.get("nextdata", "0")
```

The same key normalization applies to `analysis`. FlowIO 1.4.0 removes every
`$` character from the decoded segment before splitting keys and values, so a
value such as `"a$b"` is parsed as `"ab"`. Keep the source file when exact
metadata round-trip fidelity matters.

## `FlowData.as_array`

### Signature

```python
flow.as_array(preprocess=True)
```

Returns a two-dimensional NumPy `float64` array. For valid input its shape is:

```python
(flow.event_count, flow.channel_count)
```

FlowIO actually reshapes to `(-1, channel_count)` and does not compare DATA
length with `$TOT`. Validate the resulting shape or check
`len(flow.events) == flow.event_count * flow.channel_count` first.

With `preprocess=False`, FlowIO reshapes decoded values without applying
metadata-driven scaling. Integer decoding has already applied PnR bit masks,
so this does not recover the original binary words.

With `preprocess=True`, FlowIO:

1. Multiplies the time channel by the `timestep` keyword when available.
2. Converts logarithmically stored channels to linear values from PnE and PnR.
3. Divides channel values by PnG when gain is neither zero nor one.
   FlowIO forces the recognized `Time` channel gain to one.

For logarithmic PnE with `log_zero == 0`, channel extraction substitutes `1.0`.

It does not perform spillover compensation, logicle/biexponential/asinh
transformation, gating, or quality control.

The method materializes a new array in addition to `flow.events`.

## `FlowData.write_fcs`

### Signature

```python
flow.write_fcs(filename, metadata=None)
```

Writes the instance to an FCS 3.1 file.

Metadata behavior:

- `metadata=None`: preserve source `cyt`, `date`, and `spillover`/`spill` when
  present, plus PnR values needed by the writer.
- `metadata={}`: omit those selected defaults.
- Any other dictionary: write the supplied custom metadata instead of merging
  it with the selected defaults.

Required interpretation fields a

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

