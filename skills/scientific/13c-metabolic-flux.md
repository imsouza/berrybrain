---
id: sci-13c-metabolic-flux
name: "Scientific: 13c-metabolic-flux"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Estimates intracellular metabolic fluxes from steady-state carbon-13 isotope-tracing measurements using validated atom maps, mfapy isotope simulation, constrained multistart fitting, and flux-profile diagnostics. Use for 13C-MFA, carbon tracing, mass isotopomer distributions (MDV"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "13c metabolic flux"
  - "13c-metabolic-flux"
keywords:
  - "13c"
  - "metabolic"
  - "flux"
  - "estimates"
  - "intracellular"
  - "fluxes"
  - "steady"
  - "state"
---

# Carbon-13 metabolic flux inference

Turn reviewed carbon maps, explicit tracer mixtures, and corrected labeling measurements
into feasible flux estimates and evidence about which fluxes the experiment constrains.
Use the bundled solver rather than reconstructing isotope balances or fitting each
reaction independently. It runs mfapy's EMU forward simulator and fits fluxes in the
mass-balanced feasible space with SciPy. It does not use an FBA objective.

## Scope and required evidence

This implementation supports **metabolic and isotopic steady state**, a single shared
flux state across one or more tracer experiments, nonnegative one-way reaction fluxes,
and carbon-subset mass distributions. Reversible reactions are two separately mapped
directions. Measurement error is Gaussian with a supplied covariance or a disclosed
diagonal approximation.

Before fitting, obtain:

- The carbon network and the source of each atom assignment. Stoichiometry alone does
  not specify where labeled atoms go. Record compartments as separate metabolite IDs.
- Evidence for both steady-state assumptions. Stable metabolite abundance does not
  establish isotopic steady state. Time-course labeling requires INST-MFA with pool
  sizes and initial labeling; do not average it into this solver.
- Every carbon input's positional isotopomer distribution, including unlabeled
  supplements, bicarbonate/CO2 when assimilated, and tracer impurity.
- Fragment carbon assignments, natural-abundance correction history, and uncertainty
  of the **reported mean**. Raw peak intensities, derivatized spectra, and MS/MS
  transitions require validated preprocessing before these inputs can be constructed.
- Flux units, extracellular rate measurements or a stated relative-flux reference,
  and biologically justified bounds. Label fractions alone cannot set an absolute rate.

If necessary information is missing, name it and prepare the input template; do not
invent a fragment assignment, atom map, isotope correction, or measurement error.
Read [references/input-contract.md](references/input-contract.md) when preparing inputs.
Read [references/inference.md](references/inference.md) before interpreting an actual fit.

## Install the tested engine

Run in the user's analysis directory. Set `SKILL_DIR` to this skill's installed directory,
using the actual resolved path. Keep environments and generated results outside the skill.

```bash
uv venv --python 3.12 .venv-mfa
uv pip install --python .venv-mfa/bin/python -r "$SKILL_DIR/assets/requirements.txt"
```

The following commands use `.venv-mfa/bin/python`; on Windows use the environment's
`Scripts/python.exe`. mfapy is installed from an immutable Git revision because it is
not distributed on PyPI. Installation executes dependency build code; model inputs
are data, not user-supplied Python. The adapter restricts identifiers and atom-map
syntax before they reach mfapy's internally generated numerical functions.

The pinned commit matched upstream `master` on 2026-09-30. Its README labels the
latest change "064", but its installed distribution still reports `0.6.3`; retain
the Git commit alongside the package version in an analysis record. The refreshed
NumPy/SciPy pins require Python 3.12 or later; the commands above use the tested 3.12
environment. See the reviewed forward-model contract in
[references/inference.md](references/inference.md).

## Workflow

1. **Prepare explicit inputs.** Copy a relevant model asset into the analysis directory,
   then replace its scientific content only from reviewed evidence. The bundled models
   are demonstrations, not validated organism-specific reconstructions. Use a separate
   dataset for each biological condition; jointly fit tracer replicates only when their
   biological flux state is defensibly shared.
2. **Check the contract and feasibility.**

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" check \
     --model model.json --data measurements.json --output input-check.json
   ```

   This checks atom counts and conservation, fragments, tracer sums, uncertainty
   matrices, bounds, and steady-state mass-balance feasibility. It cannot verify that a
   chemically consistent atom map is biologically correct or that a sample reached steady state.
3. **Exercise the forward model.** Supply one mass-balanced flux vector in the declared
   units. Compare predicted labeling with a reference or independently derived limits.

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" simulate \
     --model model.json --data measurements.json --fluxes fluxes.json \
     --output simulated-mdvs.json
   ```

4. **Fit and profile the fluxes relevant to the question.**

   ```bash
   .venv-mfa/bin/python "$SKILL_DIR/scripts/mfa.py" fit \
     --model model.json --data measurements.json --starts 12 --seed 2026 \
     --profile v3 --profile v7 --profile-points 31 --profile-starts 6 \
     --output fit.json
   ```

   Replace `v3` and `v7` with actual reaction IDs. Each profile point fixes that reaction
   and reoptimizes nuisance fluxes. For nonlinear networks, repeat with a different seed
   and more starts before interpreting a profile. A small residual is not an
   identifiability result.
5. **Inspect the evidence.** Check failed starts, residual patterns, mass balance,
   active bounds, local sensitivity rank, and profile status. Report threshold-crossing
   brackets at their actual grid resolution. Refine the grid if they are too coarse.
   Each requested profile gives a one-flux interval under the stated error model;
   multiple 95% profiles are not a simultaneous 95% region for the whole network.
   If a profile finds a better solution than the baseline, rerun the fit; do not publish
   the stale intervals. A failed profile point is unknown, not excluded by the data.
6. **Deliver a bounded scientific result.** Include model and data hashes, package
   versions, source/correction provenance, units and reference flux, fitted predictions,
   residual diagnostics, profile plots or a table, and the unresolved flux combinations.
   Retain the JSON artifact. Separate point estimates supported by the data from arbitrary
   optimizer choices along a flat direction. Suggest additional measurements only after
   testing that their predicted labeling changes along that direction.

## Worked examples

These executable examples use synthetic, tracer-only data. There is no hidden natural-
abundance correction, and the tracer proportions alrea

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

