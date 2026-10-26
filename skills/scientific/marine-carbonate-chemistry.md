---
id: sci-marine-carbonate-chemistry
name: "Scientific: marine-carbonate-chemistry"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Solves seawater carbonate chemistry with PyCO2SYS for chemical oceanography, ocean acidification, and marine carbon-cycle research. Use for paired total alkalinity, dissolved inorganic carbon, pH, or seawater pCO2/fCO2 measurements; carbonate speciation; aragonite and calcite sat"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "marine carbonate chemistry"
  - "marine-carbonate-chemistry"
keywords:
  - "marine"
  - "carbonate"
  - "chemistry"
  - "solves"
  - "seawater"
  - "pyco"
  - "chemical"
---

# Marine Carbonate Chemistry

Turn two independent seawater carbonate measurements into a reproducible speciation
table, mineral saturation estimates, and a record of the calculation assumptions.
Targets **PyCO2SYS 1.8.3.4**, tested with Python 3.13 and NumPy 2.5.3. As reviewed on
2026-10-01, this remains the stable PyPI release. The [v2 documentation](https://mvdh.xyz/PyCO2SYS/)
is for a beta with breaking changes; use the v1 documentation for this pin.

## When to use

- Analyze bottle samples, shipboard carbonate measurements, or acidification experiments.
- Calculate total-scale pH, seawater pCO2/fCO2, carbonate ion, aragonite/calcite
  saturation state, or the Revelle factor from a valid measured pair.
- Convert a system determined at laboratory conditions to specified ocean conditions.
- Quantify how stated measurement uncertainties affect the calculated results.

This workflow concerns seawater carbonate equilibria. Freshwater, porewaters with
substantial uncharacterized alkalinity, brines outside the selected calibration range,
and reaction/transport models require additional chemistry and validation. Do not
infer an air-sea flux or atmospheric carbon removal from a carbonate equilibrium alone.

## Establish the measurement contract

Before running a solver, identify the two measured variables, their units, quality flags,
and their temperature/pressure basis. Retain a separate source table containing station,
depth, timestamps, methods, reference materials, and original QC codes, joined by sample ID.
Do not turn missing values or rejected measurements into zero.

| Quantity | Required convention |
|---|---|
| Total alkalinity (TA), DIC, nutrients | micromol per **kg seawater**, not per litre or kg water |
| Salinity | Practical Salinity, not Absolute Salinity in g/kg |
| Temperature | In-situ/measurement temperature in degrees Celsius, not potential or Conservative Temperature |
| Pressure | Sea pressure in dbar; surface sample is 0, not 1 atmosphere |
| pH | Declared total, seawater, free, or NBS scale, at the declared measurement conditions |
| pCO2 / fCO2 | Seawater partial pressure / fugacity in microatm; these are distinct quantities |

TA and DIC remain constant during the solver's temperature/pressure conversion for a
closed sample. pH and gas parameters change. Two inputs measured at different conditions
cannot simply share one `temperature` value. Establish a consistent measurement basis
first. Temperature correction does not repair sample changes caused by gas exchange,
biology, evaporation, or mineral dissolution/precipitation.

Use two independent carbonate parameters. pCO2 plus fCO2 is not an independent pair.
Three or more measurements enable an overdetermination check: solve independent pairs
and compare predicted versus measured third parameters, including their uncertainty.
Do not average inconsistent solutions to hide a calibration or scale mismatch.

## Install

Create a dedicated environment in the user's working directory:

```bash
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python "PyCO2SYS==1.8.3.4" "numpy==2.5.3"
```

On Windows the environment's interpreter is `.venv/Scripts/python.exe`. The commands
below use the POSIX interpreter path. Set the shell variable `SKILL_DIR` to this installed
skill's directory. Keep inputs and generated outputs in the working directory.

## Workflow

1. **Prepare paired measurements.** Use the schema in
   [references/input-and-results.md](references/input-and-results.md). Resolve units and
   quality flags before creating the input file. Supply phosphate and silicate explicitly;
   zero is an assumption to justify, not a missing-data code.
2. **Choose equilibrium constants.** Read
   [references/chemistry-decisions.md](references/chemistry-decisions.md) for pH scales,
   carbonic-acid constants, borate, saturation interpretation, and uncertainty limits.
   Match the study's validated convention and report it. The helper supports carbonic-acid
   options 10 and 15; other systems require a separately verified direct PyCO2SYS call.
3. **Solve with `scripts/solve_carbonate.py`.** It validates the full input table, solves
   the pair, checks finite outputs and DIC species balance, then writes `carbonate.csv`
   and `provenance.json` into a new output directory.
4. **Review flags and consistency.** Inspect calibration-range and gas-pressure flags,
   carbonate balance, measured-third-parameter residuals when available, and controls.
   A successful solve does not validate the sample, constants, or measurement method.
5. **Report at the intended conditions.** Results ending `_out` describe the supplied
   output temperature/pressure. Unsuffixed results describe input conditions. Gas results
   retain the helper's uncorrected hydrostatic gas convention (see below). Include
   parameter pair, pH scale, units, constants, nutrient assumptions, uncertainty scope,
   software versions, and excluded/flagged samples with the result table.

## Worked example: closed-sample condition correction

The following values are synthetic, not field observations. Save this as `samples.csv`
in a working directory. The two samples differ only in DIC; the second represents a
fixed-alkalinity CO2-addition comparison. Their measurements are at 25 C and 0 dbar;
results are also requested at 10 C and 1000 dbar.

```csv
sample_id,par1,par2,salinity,temperature,pressure,total_phosphate,total_silicate,temperature_out,pressure_out,u_par1,u_par2
baseline,2300,2000,35,25,0,0,0,10,1000,2,2
added_co2,2300,2100,35,25,0,0,0,10,1000,2,2
```

Run from that working directory:

```bash
.venv/bin/python "$SKILL_DIR/scripts/solve_carbonate.py" samples.csv \
  --par1-type alkalinity --par2-type dic --k-carbonic 10 \
  --output-dir carbonate-results
```

For the baseline, the tested version gives input-condition total pH **8.045886**,
pCO2 **396.958 microatm**, and aragonite saturation **3.386201**. At the specified output
conditions, total pH is **8.241241** and aragonite saturation **2.605691**. These rounded
values are regression checks for this exact setup, not universal seawater benchmarks.
With independent 2 micromol/kg uncertainties in TA and DIC only, `u_pH_total` is about
**0.004580**. This excludes equilibrium-constant and other input uncertainty.
Both rows carry `gas_pressure_correction_disabled_output`: the output pH and mineral
saturation include pressure effects, but the reported pCO2/fCO2 do not include the
hydrostatic corrections 

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

