# Evaluation Datasets

## Registry Contract

Each dataset has an English manifest with identifier, source, license, citation, version, acquisition
procedure, split, file paths, and SHA-256 checksums. The verifier reports missing or mismatched files
and never downloads or replaces them silently.

## Dataset Families

- **Controlled vault:** deterministic chains, stale/deleted evidence, ignored edges, contradictions,
  duplicates, secrets, and exact topology. Used only for regression and fault attribution.
- **Curated personal-knowledge set:** realistic notes with qrels, answers, facts, nodes, edges, and
  insight labels. Requires consent and reviewer protocol.
- **BEIR subsets:** heterogeneous retrieval generalization with official qrels and per-dataset license.
- **HotpotQA:** multi-hop answer and supporting-fact evaluation.
- **MuSiQue:** compositional multi-hop chains resistant to shortcut reasoning.
- **Attachments:** ground-truth PDF/document text, OCR images, and transcription media.
- **Adversarial set:** prompt injection, unsafe URLs, secrets, malformed metadata, and unsupported
  claims with expected quarantine/refusal behavior.
- **Longitudinal stream:** create/update/delete/rebuild events with expected state after each event.

## Leakage Prevention

Split by source document before chunking. Keep evaluation qrels and supporting facts out of prompts
except where the protocol explicitly provides retrieved evidence. Record whether an embedding or
generation model may have seen public benchmark data during pretraining. Use the curated set as the
primary ecological-validity check and public datasets as complementary evidence.

## Annotation

Two reviewers independently label relevance, answer support, ontology type, edge relation, insight
usefulness, and confidence correctness. Disagreements are adjudicated without revealing model
identity. Report Cohen's kappa for categorical labels and an appropriate agreement coefficient for
graded relevance. Annotation files follow `benchmarks/schemas/annotation.schema.json`.

## Current Installation State

The repository includes manifests for BEIR, HotpotQA, and MuSiQue. Their payloads are intentionally
not vendored and remain `not-installed` until upstream terms are checked and checksums recorded.
No external benchmark result may be claimed before verification succeeds.
