---
id: sciref-matchms-importing-exporting
name: "Scientific Ref: Importing and Exporting (matchms 0.33.1)"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matchms): Importing and Exporting (matchms 0.33.1)"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matchms importing exporting"
  - "importing and exporting (matchms 0.33.1)"
keywords:
  - "matchms"
  - "importing"
  - "exporting"
  - "specialized"
  - "scientific"
  - "reference"
---

# Importing and Exporting (matchms 0.33.1)

Use this reference for file-format selection, return types, streaming behavior,
and safe serialization. The authoritative APIs are the matchms
[`importing`](https://matchms.readthedocs.io/en/latest/api/matchms.importing.html)
and
[`exporting`](https://matchms.readthedocs.io/en/latest/api/matchms.exporting.html)
packages.

## Recommended Entry Points

Use extension-based helpers for ordinary local files:

```python
from matchms.importing import load_spectra
from matchms.exporting import save_spectra

spectra = list(load_spectra("library.msp"))
save_spectra(spectra, "cleaned.mgf")
```

`load_spectra()` supports mzML, mzXML, MGF, MSP, JSON, and `.pickle`.
`save_spectra()` supports MGF, MSP, JSON, and `.pickle` in 0.33.1. Use
format-specific functions when you need an MS level, file-like MGF input,
mzSpecLib output, or precise writer options.

`save_spectra()` refuses to overwrite an existing output unless
`append=True`, and append mode is restricted to MGF and MSP. This makes it
safer than direct writers, whose MGF/MSP defaults are append mode.

## Import Matrix

### MGF

```python
from matchms.importing import load_from_mgf

spectra = list(load_from_mgf("queries.mgf"))
```

Signature:

```text
load_from_mgf(filename: str | Path | TextIO,
              metadata_harmonization: bool = True) -> Generator[Spectrum]
```

MGF is a practical interchange format for centroided MS/MS spectra and supports
streaming iteration. It can also read an already-open text handle:

```python
with open("queries.mgf", encoding="utf-8") as handle:
    spectra = list(load_from_mgf(handle))
```

### MSP

```python
from matchms.importing import load_from_msp

library = list(load_from_msp("library.msp"))
```

Signature:

```text
load_from_msp(filename: str,
              metadata_harmonization: bool = True) -> Generator[Spectrum]
```

MSP is common for reference libraries. Matchms 0.29+ includes support for
GOLM-style MSP data, but source metadata still varies substantially by library.

### mzML and mzXML

```python
from matchms.importing import load_from_mzml, load_from_mzxml

ms2 = list(load_from_mzml("sample.mzML", ms_level=2))
ms1 = list(load_from_mzxml("legacy.mzXML", ms_level=1))
```

Signatures:

```text
load_from_mzml(filename: str | Path, ms_level: int = 2,
               metadata_harmonization: bool = True) -> Generator[Spectrum]
load_from_mzxml(filename: str | Path, ms_level: int = 2,
                metadata_harmonization: bool = True) -> Generator[Spectrum]
```

These readers select one MS level. For chromatograms, binary arrays beyond the
Spectrum abstraction, vendor-specific metadata, or more complex raw-data
parsing, use pyteomics, pymzML, or pyopenms.

### JSON

```python
from matchms.importing import load_from_json

spectra = load_from_json("spectra.json")
```

Signature:

```text
load_from_json(filename: str,
               metadata_harmonization: bool = True) -> list[Spectrum]
```

The JSON reader returns a list, not a generator. It supports matchms JSON and
GNPS-style spectral-library JSON and skips spectra with zero peaks.

### Metabolomics USI

```python
from matchms.importing import load_from_usi

spectrum = load_from_usi(
    "mzspec:GNPS:GNPS-LIBRARY:accession:CCMSLIB00000424840"
)
```

Signature:

```text
load_from_usi(
    usi: str,
    server: str = "https://metabolomics-usi.gnps2.org",
    metadata_harmonization: bool = True,
)
```

The 0.33.1 helper makes an unauthenticated GET to
`https://metabolomics-usi.gnps2.org/json/?usi1=<USI>` with a 10-second timeout.
It expects one JSON object with nonempty `peaks` pairs and `precursor_mz`; there
is no pagination. It returns one `Spectrum` or `None`, not a generator.
Only `usi`, `server`, and `precursor_mz` are retained as metadata: the resolver
also returns fields such as `precursor_charge` and `splash`, which the helper
does not retain. Save the raw response separately when those fields matter.

The helper handles some invalid/404 responses with `None` but does not fully
validate HTTP/schema failures; request, header, or malformed-peak exceptions
can propagate. Check the result before scoring. Use `load_from_usi` directly: the
generic `load_spectra` has a `.usi` dispatch branch but first checks local file
existence, so it is not a reliable entry point for a USI string. Preserve USI,
resolver, retrieval date, and original response alongside analysis outputs.

### Pickle

```python
from matchms.importing import load_from_pickle

spectra = load_from_pickle("trusted-cache.pickle", metadata_harmonization=True)
```

The `metadata_harmonization` argument is required in 0.33.1.

**Security:** Python pickle is executable serialization. Loading an untrusted
pickle can run arbitrary code. Use MGF, MSP, JSON, or mzSpecLib for exchanged or
downloaded data. Restrict pickle to trusted, local, reproducible caches.

## Generator and Memory Semantics

MGF, MSP, mzML, and mzXML readers yield generators. JSON and pickle readers
return lists. Converting a generator with `list(...)` loads all spectra and peak
arrays into memory.

Pairwise scoring requires materialized collections. Before scoring, estimate:

```python
pair_count = len(references) * len(queries)
```

For preprocessing-only MGF/MSP workflows, stream one spectrum at a time:

```python
from pathlib import Path

from matchms.exporting import save_spectra
from matchms.filtering import default_filters, normalize_intensities
from matchms.importing import load_from_mgf

output = Path("cleaned.mgf")
if output.exists():
    raise FileExistsError(output)

first_write = True
for spectrum in load_from_mgf("large.mgf"):
    spectrum = default_filters(spectrum)
    spectrum = normalize_intensities(spectrum)
    if spectrum is None:
        continue
    save_spectra([spectrum], str(output), append=not first_write)
    first_write = False
```

For many spectra, writing larger batches is usually faster than one record per
call.

## Metadata Harmonization

The importers default to `metadata_harmonization=True`. This harmonizes keys
and selected values while constructing each `Spectrum`. In 0.33.1, disabling
this flag skips value harmonization but **still harmonizes keys**, including
lowercasing and alias replacement; it does not preserve source keys.

Keep harmonization enabled for cross-source comparisons. Disable it only when:

- automatic value harmonization must be deferred for inspection;
- you have a documented custom normalization layer; or
- you are investig

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

