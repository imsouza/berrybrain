# BerryBrain Evaluation Table

**Caption:** Exploratory profile S results generated from the machine-readable
evaluation bundle. Synthetic retrieval results are internal regression evidence and must not be
interpreted as external comparative validity.

**Provenance:** `reports/evaluation/full-evaluation.json`, generated
`2026-08-12T19:13:05.786163+00:00`. Evidence manifests retain revision, dirty state, environment, seed,
configuration, observations, and checksums.

| Retrieval configuration | Recall@10 | MRR | NDCG@10 | p95 latency (ms) |
| --- | ---: | ---: | ---: | ---: |
| lexical_only | 0.050 | 0.017 | 0.025 | 11.01 |
| dense_only | 0.500 | 0.500 | 0.500 | 9.70 |
| standard_hybrid | 0.500 | 0.500 | 0.500 | 18.27 |
| graph_lexical | 0.500 | 0.250 | 0.315 | 21.99 |
| graph_hybrid | 1.000 | 0.750 | 0.815 | 30.84 |

## System Profile

- HTTP: 100 requests, 67.98 requests/s, p95 248.62 ms, error rate 0.000.
- On-disk graph: 500 nodes, 1000 edges, p95
  306.76 ms, payload 541592 bytes, peak traced memory
  3181953 bytes.
- Worker queue: enqueue 52.39 jobs/s, drain
  12.48 jobs/s, end-to-end p95
  7693.75 ms, duplicate claims 0.
- Maturity V3: incomplete-evidence, minimum Level
  0, median Level 2.
