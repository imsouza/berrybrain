# Maturity Model V3

BerryBrain maturity is reported as evidence levels per capability, replacing static percentages.

| Level | Required evidence |
| ---: | --- |
| 0 | Absent, contradicted, missing, or stale evidence |
| 1 | Implementation artifact without verification |
| 2 | Current unit/integration or deterministic CI regression evidence |
| 3 | Representative reproducible benchmark evidence |
| 4 | Independent comparison plus fault evidence |
| 5 | Longitudinal field or approved human-study evidence |

Capabilities cover capture/extraction, durable memory, grounded retrieval, graph/ontology, insights
and agents, transparency and user control, scalability, reliability, security/privacy, interaction
quality, and maintainability/governance.

Every level links to a current artifact and expiry date. Synthetic evidence cannot award Levels 4-5.
Level 5 requires real field or participant evidence. Missing evidence remains Level 0. A failed
mandatory safety, privacy, authorization, backup, or integrity gate sets readiness to `blocked`
regardless of median level.

`apps/api/benchmarks/maturity_v3.py` computes the assessment and rejects missing, stale, unknown, or
overclaimed evidence. The report publishes minimum and median levels, not a misleading percentage.
