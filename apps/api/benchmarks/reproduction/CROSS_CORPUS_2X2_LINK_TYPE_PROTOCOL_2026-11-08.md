# Cross-corpus 2x2 corpus x link-type retrieval control — protocol frozen 08/11/2026

Frozen **before** running the two missing cells (`MuSiQue x Title-mention` and
`2WikiMultiHopQA x OpenIE`). Because both question sets (`600` MuSiQue
confirmatory-split questions and `200` initial hash-selected 2WikiMultiHopQA
questions `0..199`) were previously observed, this 2x2 factorial comparison is
classified as **post-hoc exploratory** (with prospective confirmation of the
2Wiki comparison preregistered separately on disjoint questions `200..399` in
`PROSPECTIVE_2WIKI_CONFIRMATION_PROTOCOL_2026-11-08.md`).

## Motivation

In the 03/11/2026 manuscript, automated OpenIE triples were evaluated only on
MuSiQue and explicit document-title mentions only on 2WikiMultiHopQA,
confounding corpus with link type. Completing the 2x2 matrix tests whether
explicit title-mention links outperform automated OpenIE triples *within* each
corpus under equal-budget cross-encoder controls.

## Fixed hyperparameters (unchanged from August 2026 MuSiQue code)

All hyperparameters remain fixed at the values originally committed in
`same_corpus_rag_benchmark.py` (August 2026, prior to any 2WikiMultiHopQA
experiment) and `external_2wiki_retrieval.py` (23/10/2026):

- Source depth per route: `TOP_K = 10`; deeper Hybrid pool: `DEPTH = 40`.
- Reciprocal rank fusion constant: `RRF_K = 60`.
- Graph propagation dense seed count: `GRAPH_SEEDS = 20`.
- Entity/title document-frequency band: `2 <= df <= 64` (`MAX_ENTITY_DF = 64`).
- `TitleMentionGraph` (unmodified from `external_2wiki_retrieval.py`):
  casefolded corpus titles with `len(title) >= 4`, non-alphanumeric boundary
  matching via Aho-Corasick over `f"{title}. {text}".casefold()`.
- `OpenIeGraph` (unmodified from `reproduction-src/same_corpus_rag_benchmark.py`):
  token-normalized `extracted_entities` and subject/object of 3-element
  `extracted_triples` with `len(entity) >= 2`.
- Local models: `all-MiniLM-L6-v2` ONNX arm64 qint8
  (`4278337fd0ff3c68bfb6291042cad8ab363e1d9fbc43dcb499fe91c871902474`) and
  `cross-encoder/ms-marco-MiniLM-L-6-v2` ONNX INT8
  (`e2202924a088770398d9af3ff66b307d0a849b4b080d60e628a6b2749a14d507`,
  tokenizer snapshot `233902d25c440f23af6f7d6e94d2946bac0bee0a`,
  `max_length = 512`, `batch_size = 8`, `intra_op_threads = 2`).

## Pinned inputs

### Cell 1 (new): 2WikiMultiHopQA x OpenIE (`0..199`, 200 questions)
- Corpus (`6,119` docs): `external-corpus/2wikimultihopqa_corpus.json`
  (`9d6e352952aafb18dab22bf8195039461321a44a949df902ae83bce134ad238a`).
- Questions (`0..199` by ascending `(sha256(_id), _id)`):
  `external-corpus/2wikimultihopqa.json`
  (`895cba294064df0c3302c76847b1fc08d99b5619f7663dfaa3b65cd780f1cac4`).
- Published OpenIE artifact (`OSU-NLP-Group/HippoRAG` commit
  `b144c46df14cabe5f5822d8caded4bec5f709461`):
  `external-corpus/openie-legacy/openie_2wikimultihopqa_results_ner_gpt-3.5-turbo-1106_6119.json`
  (`128bfbf5a2f3f4282285072dedbdbab4e2167097434f37d4f8a7efffdb79e036`).
- Single-pass cross-encoder scoring over the deduplicated union of
  `four_route_openie`, `four_route_title`, and `hybrid40` for each question, so
  `four_route_openie_ce`, `hybrid_matched_openie_ce` ($N_{\text{openie}}(q)$),
  `four_route_title_ce`, `hybrid_matched_title_ce` ($N_{\text{title}}(q)$),
  `nonstructural_ce`, and `hybrid40_ce` share identical per-pair logits.

### Cell 2 (new): MuSiQue x Title-mention (`600` confirmatory-split questions)
- Corpus (`11,656` passages): `artifact/inputs/musique_corpus.json`
  (`73157a03ce3f0b1a5673dd5dc12bb970c24976dbffc688af9eecdd758c97ffcb`).
- Questions: `artifact/inputs/musique.json`
  (`98ed4e21d3076532f6388d42320fb809599c63a0d8dffca8ece5e41922be6b46`) and
  `frozen-evaluation/comparative-split-v1.json`
  (`422880aef761dd38a0a01d9bdea57f7cb9745360a630b6d598ebfccb62654b62`).
- Clean depth-40 source rankings: `clean-rerun/musique-source-depth40.json`
  (`8c3d26fed548f70e470a2b8aa37d3181dec67f46065d32b7771a28fb9f2289e2`).
- Build `title_graph_proxy` with unmodified `TitleMentionGraph` over the 11,656
  MuSiQue passages and clean MiniLM embeddings. Score the deduplicated union of
  `four_route_title` and `hybrid_matched_title` ($N_{\text{title}}(q)$ first
  candidates of clean `hybrid` depth-40) in a single cross-encoder pass so
  `four_route_title_ce`, `hybrid_matched_title_ce`, `nonstructural_ce`, and
  `hybrid_top10_ce` share identical per-pair logits. Also audit source-only
  `openie_graphrag` on MuSiQue using HippoRAG's `gpt-3.5-turbo-1106` OpenIE
  artifact (`0c2d543028a3b24ab600f6b812f54eafb057b9935fcc632875427a30816f9b92`)
  against `gpt-4o-mini` (`8540fb7f20bc38ee037e285411b73d9be910e7304f4a4585daee369238040f54`)
  to check whether extractor model version alters unreranked OpenIE recall.

## Statistical analysis

10,000 paired question-bootstrap resamples, seed `20261108`. Primary endpoints
within each corpus:
1. `four_route_title_ce` minus `hybrid_matched_title_ce` (Recall@10, Full@10);
2. `four_route_openie_ce` minus `hybrid_matched_openie_ce` (Recall@10, Full@10);
3. `four_route_title_ce` minus `four_route_openie_ce` (Recall@10, Full@10).
