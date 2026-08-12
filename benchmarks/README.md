# BerryBrain Benchmark Assets

This directory contains configuration, schemas, dataset manifests, workload definitions, and
baseline declarations. Executable Python runners live in `apps/api/benchmarks` so they use the
same pinned environment as the API while remaining isolated from production startup paths.

## Evidence Contract

Every measured run emits an immutable directory containing:

- `manifest.json`: revision, dirty state, environment, seed, dataset checksum, and configuration;
- `summary.json`: aggregate metrics and gate outcomes;
- `raw/observations.jsonl`: query, request, job, or sample-level observations;
- `checksums.txt`: SHA-256 checksums for the bundle.

Raw user content, prompts, note bodies, secrets, and access tokens are prohibited in metric labels
and evidence bundles. Dataset manifests identify source, license, version, checksum, split, and
acquisition procedure. Missing external data remains missing; runners never substitute mock scores.

## Classification

- `ci-regression`: deterministic, isolated evidence suitable for regressions only.
- `exploratory`: performance or quality evidence collected before preregistration.
- `confirmatory`: frozen protocol, clean revision, preregistered hypotheses, and retained artifacts.

Synthetic fixtures can support causal regression tests but cannot establish external validity or
award Maturity V3 Levels 4-5.
