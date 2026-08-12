# Known limitations

## Release gates

- BerryBrain is not tagged `v1.0.0` and must not be described as 100% mature yet.
- Branch protection, required reviews, ten consecutive main-branch CI runs, image signing, and an external clean-install audit require repository/release operations outside the local worktree.

## Attachments

- Tesseract English OCR is included in the API image. Additional OCR languages require matching language packs and `BERRYBRAIN_ATTACHMENT_OCR_LANGUAGE`.
- Audio/video transcription uses bundled Faster Whisper with a commit-pinned `tiny.en` model. Accuracy is intentionally lower than larger models; Settings can point to another local model or custom Whisper CLI.
- Extractors run with fixed arguments, no shell, bounded timeout/output, `no_new_privs`, resource limits, and local-only defaults. They do not run in a dedicated microVM/container.
- The legacy JSON/base64 upload route is constrained by the global request-body limit; very large media needs a future streaming upload route.

## Providers and privacy

- Cloud generation and cloud embeddings do nothing until explicit remote-content consent is enabled.
- Research/web validation can send graph queries to configured external search infrastructure.
- A host administrator can read environment variables, SQLite, the vault, and process memory.

## Quality

- Semantic and insight benchmarks use curated fixtures; they do not replace evaluation against a large personal vault.
- OCR quality depends on image resolution, orientation, language, and Tesseract support.
- Transcription quality depends on audio quality, language, and model size; the bundled model is English-oriented.
- Graph clustering and confidence remain heuristic and should be reviewed for domain-specific vaults.

## Operations

- SQLite is the supported primary database. Neo4j remains a future optional backend.
- Legacy backups without a manifest are reported as unverified.
- Existing running containers are not hot-swapped by source changes; rebuild and restart during a maintenance window.
