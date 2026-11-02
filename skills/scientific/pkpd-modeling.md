---
id: sci-pkpd-modeling
name: "Scientific: pkpd-modeling"
category: scientific
source_repo: K-Dense-AI/claude-scientific-skills
description: "Pharmacokinetic and pharmacodynamic modelling and simulation - non-compartmental analysis, compartmental and population PK, PK/PD and exposure-response, TMDD, PBPK orientation, bioequivalence, allometric scaling and first-in-human dose, drug interaction prediction, and Bayesian t"
priority_tier: 2
recommended_max_tokens: 4096
task_types:
  - ask
  - synthesis
triggers:
  - "pkpd modeling"
  - "pkpd-modeling"
keywords:
  - "pkpd"
  - "modeling"
  - "pharmacokinetic"
  - "pharmacodynamic"
  - "modelling"
  - "simulation"
  - "compartmental"
  - "analysis"
---

# Pharmacokinetic and Pharmacodynamic Modelling

## When to use

Use for concentration-time analysis, structural and population PK workflows, exposure-response,
regimen simulation, bioequivalence planning, DDI screening, and research TDM calculations.
Version 2.0 rejects unsupported replicate/scaled BE and oral/infusion closed-form summaries;
model-target dose and lowest-HED output labels replace clinical recommendation labels.
This skill computes exploratory quantities and documents assumptions; it does not establish
clinical safety, recommend a patient dose, or certify a regulatory submission.

## Fix the question and conventions first

1. Record the analyte (free/total drug, metabolite or complex), matrix, dose history, actual times,
   units, population, and assay/LLOQ. With dose in mg, volume in L and time in h, concentrations
   are mg/L and CL is L/h. Convert before fitting; mg/L equals micrograms/mL, not ng/mL.
2. Pre-specify the exposure metric: AUC(0-t), AUC(0-inf), and steady-state AUC(0-tau) differ.
   State BLQ handling, missing-data rules, terminal selection and observed/predicted Clast.
3. Separate structural, residual-variability and covariate models. Convergence and a small residual
   sum of squares do not establish identifiability. Inspect sensitivity rank, local uncertainty,
   correlations, plausible bounds, multiple starts and profile likelihoods when needed.
4. Match validation to intended use. Analytical recovery and synthetic tests verify numerical
   behavior; they do not validate a model in a patient population or establish clinical evidence.

## Environment and output

The bundled scripts were exercised with NumPy 2.5.3 and SciPy 1.18.1 on Python 3.13.
Use an isolated environment; no network, credentials or proprietary engine is needed at runtime.

```bash
cd skills/pkpd-modeling/scripts
```

All scripts accept `--format table|tsv|json`. Table/TSV data go to stdout and notes/findings to
stderr; JSON includes all four components on stdout and uses `null` for unavailable diagnostics.
Exit 0 means no findings, 1 means findings, and 2 means invalid input. Dataset validation defaults
to failing on errors; `--strict` also fails on warnings. Inspect findings even when exit 0.

Commands below using CSV inputs are invocation templates; supply the indicated columns and a
suitable study design. Tests under `tests/pkpd-modeling/` execute the numerical paths with small
synthetic fixtures. Do not copy the illustrative doses or targets into clinical care.

## Workflow

### 1. Non-compartmental analysis

```bash
python3 nca.py -i profile.csv --dose 100 --route extravascular --partial-auc 0-24
```

Input: `id,time,conc` (id optional), plus optional `dose,tau,tinf,blq`. Times must be non-negative
and distinct per profile. `BLQ`, `<LLOQ`, a blank concentration, or `blq=1` invokes the chosen
BLQ convention; blanks are therefore not a general missing-sample code. Preprocess missing
samples separately. `--blq-rule zero|half-lloq|missing` applies globally, not separately by position.

Choose `--auc-method linear|linup-logdown|log`. The log rule accepts positive increasing or
decreasing endpoints, with linear fallback for zeros/equal values. AUC starts at the first
retained sample; no dose-time extrapolation is added. Late first draws therefore bias reported
CL/volume; inspect the finding. Partial AUC boundaries must be within the sampled range.

The helper's automatic lambda_z selection extends backwards from at least three positive,
non-BLQ points strictly after Tmax, keeping a larger window only when adjusted R² improves by
more than 0.0001. This is **not Phoenix Best Fit**, which favors longer windows within its
0.0001 tolerance. Manual windows also require at least three post-Tmax points and a declining
slope. An IV bolus C0 could be eligible in other software; this helper deliberately excludes Tmax.

Inspect the selected time range, span in half-lives, residuals and percent extrapolation. The
20% extrapolation, 0.8 adjusted R² and two-half-life flags are screening conventions, not universal
acceptance rules. For a manual tail ending early, predicted Clast is evaluated at the actual last
quantifiable time. Report AUCinf_obs or AUCinf_pred explicitly.

`--tau` requires a sampled single interval [0,tau] and assumes demonstrated steady state. It
reports AUCtau, Cavg and CLss(/F), withholds single-dose AUCinf/CL/Vz/Vss, and emits a finding
about that assumption. A good terminal regression cannot demonstrate steady state by itself.
See [NCA conventions](references/nca-conventions.md) and [report checklist](assets/nca-reporting-checklist.md).

### 2. Individual compartmental fitting

```bash
python3 fit_compartmental.py -i profile.csv --dose 500 --route iv-bolus --compare 1cmt,2cmt,3cmt
```

Input: `time,conc`, optional `id` for separate individual fits. This is not NLME estimation.
Oral fits identify apparent CL/F and volumes/F; F cannot be separated without external information.
Positive parameters are fitted on the log scale. The default `1/y2` uses observed concentrations
and can bias estimates when noisy low observations receive extreme weight. Compare against
`uniform`/other justified fixed weights; prediction-dependent WLS options are rejected because
the omitted variance-normalization term is needed for a full likelihood.

The weighted-SSR AIC/BIC scores are conditional on the same records and fixed weights. The
compartment F p-values are exploratory: an absent compartment lies on a boundary with nuisance
parameters unidentified, so a nominal F test is not a confirmatory compartment-selection rule.
Prefer residual inspection, physiological plausibility, sensitivity/profile checks and suitable
bootstrap or simulation-based comparisons. Rank-deficient fits cannot return reliable covariance.

Nonrandom residual signs can reflect structure, serial dependence or timing errors. A runs test
does not identify the cause. The local Gauss-Newton intervals are not profile likelihoods.
See [structural models](references/structural-models.md).

### 3. Population PK

```bash
python3 check_popk_dataset.py -i nmdata.csv --covariates WT,CRCL --time-varying WT
```

Keep numeric IDs contiguous, preserve actual event order, and use TIME from a common subject or
occasion origin, with TAD as a separate derived variable. Do not reset TIME after each dose.
NONMEM `RATE=-1` uses modelled **rate** Rn; `RATE=-2` uses modelled **duration** Dn.
A constant steady-state infusion (AMT=0, positive RA

*(Instruções condensadas para caber no orçamento de contexto do BerryBrain)*

---
## Protocolo Epistêmico Obrigatório do BerryBrain (Vault-First & Enrich AI 24h)
1. **Soberania do Próprio Conteúdo (Vault & Grafo):** Aplique a metodologia e estrutura desta skill utilizando **exclusivamente** os fatos, trechos, conceitos e conexões presentes nas notas do usuário e no Grafo de Conhecimento fornecidos no pacote de evidências.
2. **Integração com Enrich AI 24h & Fontes Web Verificadas:** Caso o pacote de evidências contenha nós validados ou expandidos pelo monitoramento contínuo 24h (`source_supports`, `source_expands`, `source_contradicts`, `externalResearch`), incorpore essas fontes verificadas com transparência.
3. **Citação Verificável Obrigatória:** Toda afirmação factual extraída das evidências deve conter o link canônico `[Título da Fonte](bbref:<evidenceId>)`. Nunca invente citações ou dados fora das evidências fornecidas.

