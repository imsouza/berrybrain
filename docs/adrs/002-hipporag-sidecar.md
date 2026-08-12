# ADR 002: HippoRAG as an Optional Sidecar

## Context
Standard semantic retrieval (Vector/RAG) and Lexical retrieval often fail at multi-hop queries, where the answer requires connecting concepts across disjoint documents. HippoRAG aims to solve this by simulating hippocampal memory over knowledge graphs. However, the official HippoRAG library depends on massive data science packages (`torch`, `vLLM`, `igraph`), which would bloat the core BerryBrain API and severely impact its capability to run on low-end hardware.

## Decision
1. **Sidecar Architecture**: HippoRAG is integrated into BerryBrain solely as a Docker Sidecar (`apps/hipporag`). It is strictly decoupled from the core API.
2. **Optional**: It is disabled by default. Users must opt-in via a specific Docker profile or setting.
3. **HTTP Integration**: The core API communicates with the sidecar over HTTP (`/index`, `/retrieve`, `/reconcile`). If the sidecar is offline, the API gracefully degrades to normal vector/graph retrieval.
4. **Shared Capabilities**: The sidecar doesn't configure its own LLM. It routes its generation and embedding requests back to the BerryBrain Model Router via the `HIPPORAG` capability.

## Consequences
- **Positive**: The core API remains lightweight. Users without GPUs or enough RAM are not penalized. Multi-hop queries are significantly improved for power users.
- **Negative**: Increased deployment complexity for power users. Inter-service HTTP overhead.
- **Mitigation**: We provide a pre-configured docker-compose profile to spin up the sidecar alongside the API effortlessly.
