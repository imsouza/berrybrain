# Thesis Research Protocol

## Candidate Theme

**Evaluating ontology-aware graph-augmented retrieval and continuous knowledge enrichment in a
local-first personal knowledge system.** The final theme and primary outcome must be frozen with the
academic supervisor before confirmatory collection.

## Design

Use a mixed-method evaluation. Study 1 is a paired technical experiment across A0-A6 and G0-G3 on
controlled, curated, and public datasets. Study 2 is a counterbalanced within-subject task study
comparing search-only, non-graph RAG, and full BerryBrain. Study 3 is an opt-in longitudinal field
study measuring reliability, accepted insights, corrections, and task reuse over multiple weeks.

## Hypotheses

- H1: graph expansion increases multi-hop Recall@10 with a positive paired 95% interval and no more
  than two percentage points factual-recall regression.
- H2: Judge/provenance gating reduces unsupported promoted claims.
- H3: full BerryBrain improves task success and evidence coverage relative to search-only.
- H4: graph and continuous-agent benefits have measurable latency/cost overhead.
- H5: confidence lower bounds are positively calibrated with human correctness labels.
- H6: feedback-guided adaptation reduces recurrence of previously rejected artifacts within the
  same source context without increasing false suppression in unrelated contexts.

## Participant Study

Recruit according to an approved power analysis based on the smallest effect of interest and pilot
variance. Define inclusion/exclusion before recruitment. Counterbalance condition order with a Latin
square. Tasks cover factual retrieval, multi-hop synthesis, graph-structure questions, contradiction
detection, update/delete correction, and insight review. Measure completion, time, source coverage,
corrections, NASA-TLX, trust calibration, and qualitative rationale.
The longitudinal study additionally measures rejected-pattern recurrence, correction effort,
policy reversals, unrelated-context spillover, accepted insight precision, and Judge disagreement.

Do not collect participant or private-vault data before ethics/LGPD review, consent, retention and
deletion policy, incident procedure, and supervisor approval. Pseudonymize identifiers; separate the
key; encrypt exports; minimize note content; never publish raw private notes.

## Analysis

Use paired bootstrap intervals for technical query metrics. Use a preregistered mixed-effects model
or paired nonparametric test for repeated participant outcomes, with participant and task effects.
Report effect sizes and uncertainty. Correct primary hypothesis families. Analyze qualitative data
with a documented codebook and dual coding subset. Keep pilot and confirmatory analyses separate.

## Required External Work

The following cannot be completed by repository code: final academic theme approval, ethics/LGPD
approval, participant recruitment, informed consent, real annotation, longitudinal collection, and
independent replication. These remain explicitly open until documentary evidence exists.
