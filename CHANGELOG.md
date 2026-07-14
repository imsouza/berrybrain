# Changelog

All notable BerryBrain changes are documented here. The `v1.0.0` release candidate is in final remote validation.

## Unreleased — maturity program

### Added

- Chunk-based hybrid retrieval, embedding provenance, semantic and insight benchmarks.
- Canonical knowledge graph writes, evidence-bearing AI edges, deduplication, undo, list accessibility mode, and node/edge actions.
- Grounded cognitive reviews with scheduling and evidence validation.
- Cognitive attachments with content MIME detection, checksums, PDF page locations, Tesseract OCR confidence, Whisper timestamp adapter, extractor selection, and derived-data cleanup.
- Versioned additive schema migrations with future-schema startup blocking.
- Checksummed SQLite/vault backups, verified restore, JSONL portability exports, and GraphML.
- Explicit cloud-content consent and a shared prompt-injection trust policy.
- Managed API/Worker token rotation, secret redaction, and security audit documentation.
- Immutable API, Worker, and Web Docker build definitions with Trivy and SBOM CI steps.

### Changed

- Worker now starts in the default Compose stack.
- Progress uses the actual pipeline stages queued for a note.
- Fresh browser settings default to local providers; cloud processing requires explicit consent.
- Knowledge Insights exclude system diagnostics and require note/graph evidence.

### Removed

- Flashcard UI and flashcard-oriented review behavior. Reviews are evidence-grounded cognitive prompts.

### Remaining release gates

- Audio transcription requires an installed/configured local Whisper CLI.
- Extractor subprocesses are not yet isolated in a dedicated sandbox/container.
- Immutable multi-architecture images, signatures, and SBOM attestations must be published from the release tag.
