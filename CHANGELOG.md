# Changelog

All notable BerryBrain changes are documented here.

## 1.0.0 - 2026-07-14

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

### Known limitations

- Audio transcription requires an installed/configured local Whisper CLI.
- Extractor subprocesses are not yet isolated in a dedicated sandbox/container.

### Release evidence

- Protected CI and 12 consecutive green container smokes.
- Immutable AMD64/ARM64 API, Worker, and Web images on GHCR.
- Keyless OIDC signatures and SPDX JSON attestations verified with Cosign.
- Final audit and downloadable SBOMs published with the GitHub release.
