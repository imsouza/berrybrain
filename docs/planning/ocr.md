# OCR and Attachment Processing Plan

## Summary
Turn attachments into real BerryBrain knowledge. Images, PDFs, documents, audio, and video should produce extracted or transcribed text, chunks, embeddings, graph nodes, graph edges, evidence, and useful insights.

## Scope
- Add a `PROCESS_ATTACHMENT` job triggered after upload and manual reprocess.
- Store per-attachment extraction state: attachment id, status, extracted text, summary, language, provider, model, confidence, error, timestamps.
- Keep local-first processing as default. Cloud processing only when explicitly enabled in Settings.

## Processing
- PDF/document: extract native text first; OCR fallback for scanned pages.
- Image: OCR.
- Audio: transcription.
- Video: extract audio and transcribe; optional OCR for key frames later.
- Unsupported files: mark as unsupported without breaking note processing.

## Cognitive Layer
- Index extracted text into the Knowledge Base.
- Create `attachment` nodes in the Knowledge Graph.
- Connect `attachment` to source note, concepts, topics, entities, and insights.
- Allow graph inference to cite attachments only when extracted/transcribed evidence exists.

## UI
- In the editor, show each attachment status: `Queued`, `Processing`, `Processed`, `Failed`, `Unsupported`.
- Add actions: `Reprocess attachment`, `View extracted text`, `View in graph`.
- In Activity/Home, show human results such as `PDF processed`, `Audio transcribed`, `Attachment added 3 concepts`.

## Settings
- Keep existing MB limits by category.
- Add `Attachment Processing` settings:
  - enable attachment processing;
  - OCR provider;
  - transcription provider;
  - process attachments automatically;
  - max pages per PDF;
  - max audio/video duration;
  - allow cloud processing for attachments.

## Tests
- Upload image, PDF with text, scanned PDF, audio, video, oversized file, and unsupported file.
- Verify extraction state, Activity events, graph nodes, graph edges, retrieval evidence, and cleanup on delete.

