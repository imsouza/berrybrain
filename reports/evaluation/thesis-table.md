# BerryBrain Evaluation Table

**Caption:** Exploratory profile S results generated from the machine-readable
evaluation bundle. Synthetic retrieval results are internal regression evidence and must not be
interpreted as external comparative validity.

**Provenance:** `reports/evaluation/full-evaluation.json`, generated
`2026-08-14T04:48:50.140763+00:00`. Evidence manifests retain revision, dirty state, environment, seed,
configuration, observations, and checksums.

| Retrieval configuration | Recall@10 | MRR | NDCG@10 | p95 latency (ms) |
| --- | ---: | ---: | ---: | ---: |
| lexical_only | 0.050 | 0.017 | 0.025 | 8.00 |
| dense_only | 0.500 | 0.500 | 0.500 | 8.80 |
| standard_hybrid | 0.500 | 0.500 | 0.500 | 16.65 |
| graph_lexical | 0.500 | 0.250 | 0.315 | 24.86 |
| graph_hybrid | 1.000 | 0.750 | 0.815 | 38.12 |

## System Profile

- HTTP: 100 requests, 76.12 requests/s, p95 224.55 ms, error rate 0.000.
- On-disk graph: 500 nodes, 1000 edges, p95
  222.63 ms, payload 864092 bytes, peak traced memory
  3933306 bytes.
- Worker queue: enqueue 49.15 jobs/s, drain
  11.92 jobs/s, end-to-end p95
  8060.36 ms, duplicate claims 0.
- Maturity V3: incomplete-evidence, minimum Level
  0, median Level 2.
