---
id: sciref-matlab-python-integration
name: "Scientific Ref: MATLAB and Python Integration"
category: scientific-reference
source_repo: K-Dense-AI/claude-scientific-skills
description: "Specialized scientific reference skill (matlab): MATLAB and Python Integration"
priority_tier: 3
recommended_max_tokens: 3584
task_types:
  - ask
  - synthesis
triggers:
  - "matlab python integration"
  - "matlab and python integration"
keywords:
  - "matlab"
  - "python"
  - "integration"
  - "specialized"
  - "scientific"
  - "reference"
---

# MATLAB and Python Integration

The executable planner is pinned to MATLAB R2026a, reviewed on 2026-10-01.
Calling Python from MATLAB and calling MATLAB from Python are different
interfaces with different process, data, and license behavior.

Current R2026b documentation lists CPython 3.10-3.14. At review time, PyPI
still publishes `matlabengine==26.1.12` for R2026a, not R2026b. For R2026b use
the Engine distributed with that installed release and verify its requirements;
the bundled planner deliberately rejects R2026b rather than applying the
R2026a package pin. No MATLAB or Engine runtime was started in this review.

## Exact R2026a compatibility

MathWorks' support table lists 64-bit CPython **3.9, 3.10, 3.11, 3.12,
and 3.13** for:

- MATLAB Interface to Python;
- MATLAB Engine for Python;
- MATLAB Compiler SDK for Python;
- MATLAB Production Server Client Library.

The current MathWorks-maintained PyPI release reviewed here is
`matlabengine==26.1.12`, released 2026-05-08. It requires MATLAB R2026a.
Do not install a floating latest package for a reproducible environment.

```bash
uv pip install "matlabengine==26.1.12"
```

Installation does not include MATLAB or grant a license. Engine requires an
installed R2026a on the same machine; MATLAB Runtime alone is insufficient.
The Python architecture must match MATLAB.

R2026a also ships a preinstalled Engine distribution at the single named path:

```text
<matlabroot>/extern/engines/python/dist
```

Add only that confirmed path to the selected environment when using this
method. Do not print or upload the full `PATH`, `PYTHONPATH`, environment,
license configuration, home directory, or credentials.

## Plan compatibility without execution

```bash
python scripts/plan_python_compatibility.py \
  --matlab-release R2026a \
  --python-version 3.13 \
  --engine-version 26.1.12
```

The planner uses a bundled dated support table. It does not import
`matlab.engine`, inspect the environment, locate installations, start MATLAB,
or check out a license. `--include-launch-snippet` adds an explicitly labeled
launch example to the JSON plan but still does not execute it.

## Calling Python from MATLAB

Review and pin one interpreter before any `py.*` access:

```matlab
environment = pyenv( ...
    Version="/reviewed/venv/bin/python", ...
    ExecutionMode="OutOfProcess");
```

On Windows, a registered version can be selected by version, but a full named
executable is clearer. On macOS/Linux, use the full executable. The Python
build architecture must match MATLAB. MATLAB does not support CPython from the
Microsoft Store.

Interpreter switching:

- in-process: restart MATLAB before changing the loaded interpreter;
- out-of-process: `terminate(pyenv)` can stop the external interpreter, after
  which `pyenv` can be reconfigured.

Out-of-process isolates interpreter crashes and allows reload, but it is not a
security sandbox. Data plus transfer metadata are limited to 2 GiB per
out-of-process transfer. Python modules can perform arbitrary process, file,
network, native, and credential operations.

Never run untrusted `py.*`, `pyrun`, `pyrunfile`, Python modules, wheels, or
requirements files. `pyrun` and `pyrunfile` are dynamic code execution
surfaces.

## Calling MATLAB from Python

Starting Engine is explicit execution:

```python
import matlab.engine

engine = matlab.engine.start_matlab()
try:
    result = engine.sqrt(16.0)
finally:
    engine.quit()
```

`start_matlab()` creates a MATLAB process, can execute startup code, and can
check out a MATLAB license. Never call it merely to probe availability.
Review startup paths/actions and confirm entitlement first.

Engine transfers are limited to 2 GB including supporting information.
Python `None`, Python class objects, and recursive containers are unsupported
Engine input types. These limits are separate from MATLAB-to-Python conversion.

`connect_matlab()` connects to a deliberately shared local MATLAB session;
`find_matlab()` lists shared sessions. Sharing changes the trust boundary and
must be explicitly approved. Do not connect to an unknown session.

Only add narrow reviewed paths:

```python
engine.addpath("/reviewed/project/src", nargout=0)
value = engine.analyzeSignal(
    matlab.double([[1.0], [2.0], [3.0]]),
    nargout=1,
)
```

Do not use recursive path additions. Pass fixed function names, not text to
`eval`, and set `nargout` deliberately. Redirect output to bounded
`io.StringIO` only when needed; logs can contain paths or data.

## MATLAB-to-Python conversion in R2026a

Scalar automatic mappings include:

| MATLAB | Python |
|---|---|
| real `double`/`single` | `float` by default; type hints can select `int` |
| complex float | `complex` |
| integer scalar | `int` |
| logical scalar | `bool` |
| string scalar/character vector | `str` |
| missing string through `py.str` | Python string `"None"`, not the Python `None` singleton |
| `dictionary`/scalar `struct` | `dict` |
| `table`/`timetable` | pandas `DataFrame` |
| `datetime` | `datetime.datetime` |
| `duration` | `datetime.timedelta` |

With NumPy available, numeric/logical MATLAB arrays convert to NumPy arrays
with corresponding precision/sign/complex dtype. Without NumPy, numeric arrays
use Python buffer/memoryview behavior. Since R2025a, array conversion behavior
changed; test code migrated from older vector `array.array` assumptions.

R2026a additions:

- MATLAB string vectors automatically convert to Python lists;
- `pystringarray` converts MATLAB string arrays to NumPy `StringDType`
  arrays;
- missing string entries need explicit round-trip tests.

The table above concerns Python called **from MATLAB**. Engine calls from
Python use their own conversion table and `matlab.*` array classes; do not
assume pandas, datetime, or dictionary conversions are symmetric. R2026b adds
GPU interchange through CuPy, DLPack, and PyTorch with Parallel Computing
Toolbox; those features are outside the R2026a planner's compatibility claim.

No automatic conversion is documented for multidimensional character/cell
arrays or M-by-N string arrays where both dimensions exceed one. Sparse
arrays, nonscalar structure arrays, categorical arrays, `containers.Map`,
MATLAB objects, and metadata classes are unsupported in the MATLAB-to-Python
interface.

## Python-to-MATLAB conversion

MATLAB automatically converts selected scalar Python returns. Other values use
explicit conversion:

| Python value | MATLAB conversion |
|---|---|
| `py.str` | `string`

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

