# Reproducibility

## Reproduction Levels

- **Engineering reproduction:** clone, build pinned dependencies, run deterministic tests and S
  profile on equivalent architecture.
- **Representative reproduction:** install verified datasets and models, run M/L profiles on the
  declared hardware class, and regenerate all evidence bundles.
- **Independent replication:** evaluator chooses a separate environment, follows the frozen protocol,
  records deviations, and compares effect directions and confidence intervals.

## Environment Record

Retain revision and dirty state, Docker image digests, lockfiles, environment-variable names with
secrets redacted, CPU topology, RAM, filesystem, free disk, kernel, power profile, container limits,
model identifiers and digests, prompt versions, dataset checksums, timezone, and start/end times.

## Determinism

Synthetic corpus generation, query sampling, bootstrapping, and annotation selection use recorded
seeds. Cache mode is explicit. SQLite benchmark databases are isolated and recreated per run.
Production data is never copied implicitly. Nondeterministic model output is repeated and retained.

## Independent Evaluator Checklist

1. Verify source revision, signatures when published, lockfiles, and image digests.
2. Verify every dataset checksum and license before execution.
3. Confirm no private production vault is mounted.
4. Run schema validation and S gates without changing thresholds.
5. Run the frozen representative profile and retain raw evidence.
6. Recompute aggregates from JSONL instead of trusting copied tables.
7. Compare outputs with the declared report and document every deviation.
8. Report failures and missing dependencies without substituting synthetic values.

## Publication Rule

A README or thesis number must identify its run bundle. Generated summaries are authoritative;
manually copied values are descriptive only. Commit, tag, push, registry publication, and main
deployment require explicit owner authorization after all local gates pass.
