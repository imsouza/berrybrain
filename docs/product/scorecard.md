# BerryBrain 100-Point Scorecard

| Pillar | Weight | Verified points | Remaining evidence |
|---|---:|---:|---|
| Capture and Markdown Vault | 10 | 8 | External clean-install and concurrent-edit acceptance |
| Autopilot and Jobs | 15 | 13 | Soak evidence on protected main |
| Semantic Search and Memory | 15 | 13 | Larger real-vault evaluation |
| Knowledge Graph | 15 | 13 | Extended visual/E2E quality audit |
| Explainable Insights | 10 | 8 | Longitudinal usefulness feedback |
| Review and Assimilation | 10 | 8 | Learning-outcome evaluation |
| Cognitive Attachments | 5 | 5 | Complete for the 1.0 formats; larger multilingual models remain configurable |
| UX and Observability | 8 | 6 | Full keyboard/accessibility and Core Web Vitals gate |
| Security, Data, Self-Hosting | 7 | 5 | Image signing and sandbox hardening |
| Quality and Release | 5 | 2 | Protected-main history, tag, external audit |
| **Total** | **100** | **81** | **Not release-ready** |

## Current Blocking Rules

- Required CI checks and review policy must protect `main`.
- Ten consecutive protected-main runs must pass.
- Images and SBOMs must be signed for `v1.0.0`.
- An external user must reproduce clean install, pipeline, backup, and restore.
