# ADR 001: Model Router and Separate RAG Judge

## Context
As BerryBrain evolves, relying on a single AI provider or model for all cognitive tasks (embeddings, generating graph nodes, evaluating quality, answering queries) is insufficient. Some models are good at extraction (e.g., Qwen), some are better at judging (e.g., Claude/Gemma), and some are better at embeddings. Hardcoding a single provider creates bottlenecks and single points of failure.

Furthermore, we need a mechanism to prevent "auto-confirmation bias", where the model that generates a graph insight evaluates its own work.

## Decision
1. **Model Router**: We implemented a `ModelRouter` in `ai_gateway.py` that routes requests based on `ModelCapability` (e.g., `GENERATION`, `EMBEDDING`, `JUDGE`, `HIPPORAG`).
2. **Capability Fallbacks**: The router supports a fallback chain. If the preferred local model fails or times out, it gracefully downgrades or errors out, avoiding hanging jobs.
3. **Separate Judge**: We introduced a distinct capability `ModelCapability.JUDGE` and the `JUDGE_ARTIFACT` background job. The Judge evaluates new knowledge graph artifacts asynchronously. It logs evaluations to `ArtifactEvaluationRecord` and prevents low-quality concepts or insights from poisoning the graph.

## Consequences
- **Positive**: We can mix and match local Ollama models with cloud providers based on cost and capability. The quality of the graph is guarded by an independent evaluator.
- **Negative**: Increased configuration complexity for users (they need to configure multiple models if they want full enforcement).
- **Mitigation**: We provide sensible defaults (e.g., falling back to the generation model if no judge is configured, but logging this in shadow mode).
