# Prospective 2WikiMultiHopQA confirmation — preregistered protocol frozen 08/11/2026

Frozen and SHA-256 hashed **before** inspecting, selecting, or scoring any
question in the prospective slice (`indices 200..399`).

## Preregistered status and disjoint sample definition

The exploratory 2WikiMultiHopQA study (`external_2wiki_retrieval.py` and
`BUDGET_CONTROL_2WIKI_PROTOCOL_2026-10-30.md`) evaluated the first 200
questions (`indices 0..199`) of `external-corpus/2wikimultihopqa.json` ordered
deterministically by `(sha256(_id), _id)`.

This prospective confirmation evaluates the **next 200 questions** (`indices
200..399` under the identical `(sha256(_id), _id)` ordering), enforcing exact
disjointness (`set(ids_0_199).isdisjoint(ids_200_399)`) before any retrieval
runs. No question text, supporting fact, or answer from `200..399` has been
inspected prior to freezing this protocol.

## Fixed inputs and frozen model stack

- Corpus (`6,119` documents): `external-corpus/2wikimultihopqa_corpus.json`
  (`9d6e352952aafb18dab22bf8195039461321a44a949df902ae83bce134ad238a`).
- Questions (`indices 200..399` of `1,000`):
  `external-corpus/2wikimultihopqa.json`
  (`895cba294064df0c3302c76847b1fc08d99b5619f7663dfaa3b65cd780f1cac4`).
- Published OpenIE artifact (`OSU-NLP-Group/HippoRAG` commit
  `b144c46df14cabe5f5822d8caded4bec5f709461`):
  `external-corpus/openie-legacy/openie_2wikimultihopqa_results_ner_gpt-3.5-turbo-1106_6119.json`
  (`128bfbf5a2f3f4282285072dedbdbab4e2167097434f37d4f8a7efffdb79e036`).
- Dense embedder: `all-MiniLM-L6-v2` ONNX arm64 qint8
  (`4278337fd0ff3c68bfb6291042cad8ab363e1d9fbc43dcb499fe91c871902474`).
- Cross-encoder reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` ONNX INT8
  (`e2202924a088770398d9af3ff66b307d0a849b4b080d60e628a6b2749a14d507`),
  tokenizer revision `233902d25c440f23af6f7d6e94d2946bac0bee0a`,
  `max_length = 512`, `batch_size = 8`, `intra_op_threads = 2`.
- Route parameters (fixed without tuning): `TOP_K = 10` per source route,
  `DEPTH = 40` for deeper Hybrid-RRF, `RRF_K = 60`, `GRAPH_SEEDS = 20`,
  `MAX_ENTITY_DF = 64` (`2 <= df <= 64`), unmodified `TitleMentionGraph`
  (`len(title) >= 4`, non-alphanumeric boundaries) and unmodified `OpenIeGraph`.

## Candidate pools and single-pass scoring rule

For each prospective question $q$:
- `four_route_title(q)`: deduplicated union of top-10 `bm25`, `dense`,
  `hybrid`, and `title_graph_proxy`, size $N_{\text{title}}(q) \le 40$.
- `hybrid_matched_title(q)`: first $N_{\text{title}}(q)$ candidates of
  `hybrid40(q)` (computed without relevance labels).
- `four_route_openie(q)`: deduplicated union of top-10 `bm25`, `dense`,
  `hybrid`, and `openie_graph_proxy`, size $N_{\text{openie}}(q) \le 40$.
- `hybrid_matched_openie(q)`: first $N_{\text{openie}}(q)$ candidates of
  `hybrid40(q)` (computed without relevance labels).
- `nonstructural(q)`: deduplicated union of top-10 `bm25`, `dense`, `hybrid`.

One cross-encoder pass scores `union(four_route_title(q), four_route_openie(q),
hybrid40(q))` in 8-question chunks (`batch_size = 8`). Every reranked arm is
ranked from these identical per-pair scores, breaking ties by pool order. All
200 prospective questions must complete; no early stopping is permitted.

## Preregistered hypotheses and decision rule

Paired 10,000-resample question bootstrap, seed `20261108`:

- **Primary confirmatory test (H1 — explicit-link gain at equal budget):**
  `four_route_title_ce` minus `hybrid_matched_title_ce` on `Recall@10` (co-primary
  `completeSupport@10`). Confirmed if the two-sided 95% bootstrap CI for
  `Recall@10` excludes zero above zero.
- **Secondary preregistered tests:**
  - **H2 (link-type contrast):** `four_route_title_ce` minus
    `four_route_openie_ce`, and `four_route_openie_ce` minus
    `hybrid_matched_openie_ce` on `Recall@10` and `completeSupport@10`.
  - **H3 (deeper non-structural pool & unreranked baseline):**
    `four_route_title_ce` minus `hybrid40_ce`, and `four_route_title_ce` minus
    `hybrid`.

If H1 fails (95% CI includes zero or is negative), report the null/negative
prospective outcome prominently in the Abstract, Table 4, §5.1, and Conclusion
and retain the exploratory 2Wiki finding only as a non-replicated exploratory
observation. Regardless of outcome, note in Limitations that 2WikiMultiHopQA
questions are constructed from Wikipedia/Wikidata entity bridges, which favors
article-title links by dataset design.
