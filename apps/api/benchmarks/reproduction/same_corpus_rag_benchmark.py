"""Same-corpus retrieval and RAG benchmark with auditable evidence.

Relevance labels come only from MuSiQue's published supporting passages. Every
method receives the same corpus, questions, ranking depth, and optional reader.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import os
import platform
import re
import statistics
import subprocess
import time
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
METHODS = ("bm25", "dense", "hybrid", "openie_graphrag", "berrybrain")
SCHEMA_VERSION = "berrybrain.same-corpus-rag.v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_document_id(title: str, text: str) -> str:
    payload = f"{title.strip()}\0{text.strip()}".encode()
    return hashlib.sha256(payload).hexdigest()[:24]


def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def select_by_hash(items: Sequence[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if limit <= 0 or limit >= len(items):
        return list(items)
    return sorted(
        items,
        key=lambda item: hashlib.sha256(str(item["id"]).encode()).hexdigest(),
    )[:limit]


@dataclass(frozen=True)
class CorpusDocument:
    id: str
    title: str
    text: str

    @property
    def searchable_text(self) -> str:
        return f"{self.title}. {self.text}"


@dataclass(frozen=True)
class QueryCase:
    id: str
    question: str
    answers: tuple[str, ...]
    relevant_ids: tuple[str, ...]
    hops: int


class Bm25Index:
    def __init__(
        self, texts: Sequence[str], *, k1: float = 1.2, b: float = 0.75
    ) -> None:
        self.k1 = k1
        self.b = b
        self.term_frequencies = [Counter(tokens(text)) for text in texts]
        self.lengths = np.asarray([sum(row.values()) for row in self.term_frequencies])
        self.average_length = float(np.mean(self.lengths)) if len(self.lengths) else 1.0
        document_frequency: Counter[str] = Counter()
        for row in self.term_frequencies:
            document_frequency.update(row.keys())
        count = len(texts)
        self.idf = {
            term: math.log(1.0 + (count - frequency + 0.5) / (frequency + 0.5))
            for term, frequency in document_frequency.items()
        }
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for index, row in enumerate(self.term_frequencies):
            for term, frequency in row.items():
                postings[term].append((index, frequency))
        self.postings = dict(postings)

    def scores(self, query: str) -> np.ndarray:
        scores = np.zeros(len(self.term_frequencies), dtype=np.float32)
        for term in set(tokens(query)):
            idf = self.idf.get(term)
            if idf is None:
                continue
            for index, frequency in self.postings.get(term, ()):
                denominator = frequency + self.k1 * (
                    1.0 - self.b + self.b * self.lengths[index] / self.average_length
                )
                scores[index] += idf * frequency * (self.k1 + 1.0) / denominator
        return scores


class MiniLmEncoder:
    def __init__(self, model_path: Path, *, batch_size: int = 16) -> None:
        from transformers import AutoTokenizer

        self.batch_size = batch_size
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True
        )
        self.model_file = model_path / "onnx" / "model_qint8_arm64.onnx"
        if self.model_file.exists():
            import onnxruntime

            self.backend = f"onnxruntime-{onnxruntime.__version__}"
            session_options = onnxruntime.SessionOptions()
            session_options.enable_cpu_mem_arena = False
            session_options.enable_mem_pattern = False
            session_options.intra_op_num_threads = min(4, os.cpu_count() or 1)
            session_options.inter_op_num_threads = 1
            self.session = onnxruntime.InferenceSession(
                self.model_file,
                sess_options=session_options,
                providers=["CPUExecutionProvider"],
            )
            self.torch = None
            self.model = None
        else:
            import torch
            from transformers import AutoModel

            self.backend = f"torch-{torch.__version__}"
            self.model_file = model_path / "model.safetensors"
            self.torch = torch
            self.model = AutoModel.from_pretrained(model_path, local_files_only=True)
            self.model.eval()
            self.session = None

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        rows: list[np.ndarray] = []
        for start in range(0, len(texts), self.batch_size):
            rows.append(self._encode_batch(texts[start : start + self.batch_size]))
        return np.concatenate(rows)

    def encode_cached(
        self,
        texts: Sequence[str],
        cache_path: Path,
    ) -> tuple[np.ndarray, bool, bool]:
        if cache_path.exists():
            return np.load(cache_path), True, False
        partial_path = cache_path.with_suffix(cache_path.suffix + ".partial")
        progress_path = cache_path.with_suffix(cache_path.suffix + ".progress.json")
        identity = sha256_file(self.model_file)
        completed = 0
        resumed = False
        matrix: np.memmap | None = None
        if partial_path.exists() and progress_path.exists():
            try:
                progress = json.loads(progress_path.read_text(encoding="utf-8"))
                if (
                    progress.get("modelSha256") == identity
                    and int(progress.get("textCount", -1)) == len(texts)
                    and 0 < int(progress.get("completed", 0)) <= len(texts)
                ):
                    matrix = np.load(partial_path, mmap_mode="r+")
                    completed = int(progress["completed"])
                    resumed = True
            except (OSError, ValueError, json.JSONDecodeError):
                matrix = None
        for start in range(completed, len(texts), self.batch_size):
            batch = self._encode_batch(texts[start : start + self.batch_size])
            if matrix is None:
                matrix = np.lib.format.open_memmap(
                    partial_path,
                    mode="w+",
                    dtype=np.float32,
                    shape=(len(texts), batch.shape[1]),
                )
            end = start + len(batch)
            matrix[start:end] = batch
            matrix.flush()
            temporary_progress = progress_path.with_suffix(
                progress_path.suffix + ".tmp"
            )
            temporary_progress.write_text(
                json.dumps(
                    {
                        "schemaVersion": 1,
                        "modelSha256": identity,
                        "textCount": len(texts),
                        "completed": end,
                    },
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
            temporary_progress.replace(progress_path)
        if matrix is None:
            raise ValueError("cannot encode an empty corpus")
        matrix.flush()
        del matrix
        partial_path.replace(cache_path)
        progress_path.unlink(missing_ok=True)
        return np.load(cache_path), False, resumed

    def _encode_batch(self, texts: Sequence[str]) -> np.ndarray:
        encoded = self.tokenizer(
            list(texts),
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="np" if self.session is not None else "pt",
        )
        if self.session is not None:
            inputs = {
                name: np.asarray(encoded[name], dtype=np.int64)
                for name in ("input_ids", "attention_mask", "token_type_ids")
            }
            hidden = self.session.run(["last_hidden_state"], inputs)[0]
            mask = inputs["attention_mask"][..., None].astype(np.float32)
            pooled = (hidden * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1e-9)
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            return (pooled / np.maximum(norms, 1e-9)).astype(np.float32)
        assert self.torch is not None and self.model is not None
        with self.torch.inference_mode():
            hidden = self.model(**encoded).last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).expand(hidden.size()).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            pooled = self.torch.nn.functional.normalize(pooled, p=2, dim=1)
        return pooled.cpu().numpy().astype(np.float32)

    def close(self) -> None:
        self.session = None
        self.model = None
        gc.collect()


def load_musique(
    corpus_path: Path, queries_path: Path
) -> tuple[list[CorpusDocument], list[QueryCase]]:
    corpus_payload = json.loads(corpus_path.read_text(encoding="utf-8"))
    query_payload = json.loads(queries_path.read_text(encoding="utf-8"))
    documents = [
        CorpusDocument(
            id=stable_document_id(str(row["title"]), str(row["text"])),
            title=str(row["title"]),
            text=str(row["text"]),
        )
        for row in corpus_payload
    ]
    by_content = {(row.title, row.text): row.id for row in documents}
    if len(by_content) != len(documents):
        raise ValueError("MuSiQue corpus contains duplicate title-text pairs")
    queries: list[QueryCase] = []
    for row in query_payload:
        relevant: list[str] = []
        for paragraph in row.get("paragraphs", []):
            if paragraph.get("is_supporting"):
                key = (str(paragraph["title"]), str(paragraph["paragraph_text"]))
                document_id = by_content.get(key)
                if document_id is None:
                    raise ValueError(
                        f"supporting passage absent from corpus: {row['id']}"
                    )
                relevant.append(document_id)
        aliases = [str(row["answer"]), *map(str, row.get("answer_aliases", []))]
        answers = tuple(
            dict.fromkeys(value.strip() for value in aliases if value.strip())
        )
        if relevant and answers:
            queries.append(
                QueryCase(
                    id=str(row["id"]),
                    question=str(row["question"]),
                    answers=answers,
                    relevant_ids=tuple(dict.fromkeys(relevant)),
                    hops=max(1, len(row.get("question_decomposition", []))),
                )
            )
    return documents, queries


def normalized_entity(value: str) -> str:
    return " ".join(tokens(value))


class OpenIeGraph:
    """Deterministic document-entity-document graph propagation."""

    def __init__(
        self,
        openie_path: Path,
        documents: Sequence[CorpusDocument],
        *,
        max_entity_document_frequency: int,
    ) -> None:
        source_rows = json.loads(openie_path.read_text(encoding="utf-8")).get("docs")
        if not isinstance(source_rows, list):
            raise ValueError("OpenIE payload must contain a docs list")
        index_by_id = {row.id: index for index, row in enumerate(documents)}
        entity_documents: dict[str, set[int]] = defaultdict(set)
        document_entities: list[set[str]] = [set() for _ in documents]
        for row in source_rows:
            document_index = index_by_id.get(
                stable_document_id(str(row["title"]), str(row["text"]))
            )
            if document_index is None:
                raise ValueError("OpenIE document does not match benchmark corpus")
            raw_entities = list(row.get("extracted_entities", []))
            for triple in row.get("extracted_triples", []):
                if isinstance(triple, list) and len(triple) == 3:
                    raw_entities.extend((triple[0], triple[2]))
            for raw_entity in raw_entities:
                entity = normalized_entity(str(raw_entity))
                if len(entity) >= 2:
                    document_entities[document_index].add(entity)
                    entity_documents[entity].add(document_index)
        retained = {
            entity: sorted(indices)
            for entity, indices in entity_documents.items()
            if 2 <= len(indices) <= max_entity_document_frequency
        }
        self.document_entities = [
            entities.intersection(retained) for entities in document_entities
        ]
        self.entity_documents = retained
        count = len(documents)
        self.entity_weight = {
            entity: math.log((count + 1.0) / (len(indices) + 1.0)) + 1.0
            for entity, indices in retained.items()
        }

    def propagate(self, seed_scores: np.ndarray, *, seed_count: int = 20) -> np.ndarray:
        graph_scores = np.zeros_like(seed_scores, dtype=np.float32)
        count = min(seed_count, len(seed_scores))
        if count == 0:
            return graph_scores
        seed_indices = np.argpartition(seed_scores, -count)[-count:]
        for seed_index in seed_indices:
            seed_score = max(0.0, float(seed_scores[seed_index]))
            for entity in self.document_entities[int(seed_index)]:
                targets = self.entity_documents[entity]
                contribution = seed_score * self.entity_weight[entity] / len(targets)
                for target in targets:
                    if target != seed_index:
                        graph_scores[target] += contribution
        return graph_scores


def reciprocal_rank_fusion(
    rankings: Sequence[np.ndarray], *, constant: int = 60
) -> np.ndarray:
    count = len(rankings[0])
    result = np.zeros(count, dtype=np.float32)
    for ranking in rankings:
        if np.any(ranking < 0) or np.any(ranking >= count):
            raise ValueError("Ranking contains an invalid document index")
        result[ranking] += 1.0 / (constant + np.arange(len(ranking)) + 1.0)
    return result


def top_indices(scores: np.ndarray, limit: int) -> np.ndarray:
    count = min(limit, len(scores))
    if count == 0:
        return np.asarray([], dtype=np.int32)
    candidates = np.argpartition(scores, -count)[-count:]
    return candidates[np.argsort(scores[candidates], kind="stable")[::-1]]


def retrieval_metrics(
    ranking: Sequence[str], relevant: Sequence[str]
) -> dict[str, float]:
    relevant_set = set(relevant)
    positions = [
        index + 1 for index, item in enumerate(ranking) if item in relevant_set
    ]
    ideal = len(relevant_set)
    result = {
        f"recallAt{cutoff}": sum(position <= cutoff for position in positions) / ideal
        for cutoff in (1, 5, 10)
    }
    first = min(positions, default=0)
    result["mrrAt10"] = 1.0 / first if first and first <= 10 else 0.0
    dcg = sum(1.0 / math.log2(position + 1) for position in positions if position <= 10)
    ideal_dcg = sum(
        1.0 / math.log2(position + 1) for position in range(1, min(10, ideal) + 1)
    )
    result["ndcgAt10"] = dcg / ideal_dcg if ideal_dcg else 0.0
    result["completeSupportAt10"] = float(
        len(positions) == ideal and all(position <= 10 for position in positions)
    )
    return result


def bootstrap_difference(
    left: Sequence[float], right: Sequence[float], *, seed: int, resamples: int
) -> dict[str, float]:
    if len(left) != len(right) or not left:
        raise ValueError("paired bootstrap requires equal non-empty samples")
    differences = np.asarray(left, dtype=np.float64) - np.asarray(
        right, dtype=np.float64
    )
    generator = np.random.default_rng(seed)
    estimates = np.empty(resamples)
    for index in range(resamples):
        estimates[index] = np.mean(
            generator.choice(differences, len(differences), replace=True)
        )
    return {
        "meanDifference": float(np.mean(differences)),
        "lower95": float(np.quantile(estimates, 0.025)),
        "upper95": float(np.quantile(estimates, 0.975)),
        "resamples": resamples,
    }


def normalized_answer(text: str) -> str:
    return " ".join(tokens(text))


def answer_metrics(prediction: str, answers: Sequence[str]) -> dict[str, float]:
    predicted_tokens = normalized_answer(prediction).split()
    exact = best_f1 = containment = 0.0
    for answer in answers:
        normalized_gold = normalized_answer(answer)
        gold_tokens = normalized_gold.split()
        exact = max(exact, float(predicted_tokens == gold_tokens))
        containment = max(
            containment, float(normalized_gold in normalized_answer(prediction))
        )
        shared = sum((Counter(predicted_tokens) & Counter(gold_tokens)).values())
        if shared and predicted_tokens and gold_tokens:
            precision = shared / len(predicted_tokens)
            recall = shared / len(gold_tokens)
            best_f1 = max(best_f1, 2 * precision * recall / (precision + recall))
    return {"exactMatch": exact, "tokenF1": best_f1, "answerContainment": containment}


class FlanReader:
    def __init__(self, model_path: Path) -> None:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path, local_files_only=True
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            model_path, local_files_only=True
        )
        self.model.eval()

    def answer(self, question: str, contexts: Sequence[CorpusDocument]) -> str:
        evidence = "\n".join(
            f"[{index + 1}] {document.title}: {document.text}"
            for index, document in enumerate(contexts)
        )
        prompt = (
            "Answer using only the evidence. Return only the short answer. "
            "If evidence is insufficient, return NOT ENOUGH EVIDENCE.\n"
            f"Question: {question}\nEvidence:\n{evidence}"
        )
        encoded = self.tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=512
        )
        with self.torch.inference_mode():
            output = self.model.generate(**encoded, max_new_tokens=32, do_sample=False)
        return self.tokenizer.decode(output[0], skip_special_tokens=True).strip()


def aggregate(rows: Sequence[dict[str, Any]], field: str) -> float:
    return statistics.fmean(float(row[field]) for row in rows)


def git_state(root: Path) -> dict[str, Any]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=root,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
    )
    return {"revision": revision, "dirty": dirty}


def run(args: argparse.Namespace) -> dict[str, Any]:
    started = time.perf_counter()
    documents, all_queries = load_musique(args.corpus, args.queries)
    selected = select_by_hash(
        [asdict(query) for query in all_queries], args.query_limit
    )
    queries = [QueryCase(**row) for row in selected]
    document_ids = [document.id for document in documents]
    document_index = {item: index for index, item in enumerate(document_ids)}

    phase_started = time.perf_counter()
    bm25 = Bm25Index([document.searchable_text for document in documents])
    bm25_index_seconds = time.perf_counter() - phase_started
    encoder = MiniLmEncoder(args.embedding_model, batch_size=args.embedding_batch_size)
    cache_path = args.cache_dir / f"musique-{sha256_file(args.corpus)[:16]}-minilm.npy"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    phase_started = time.perf_counter()
    document_embeddings, cache_hit, cache_resumed = encoder.encode_cached(
        [document.searchable_text for document in documents],
        cache_path,
    )
    if document_embeddings.shape[0] != len(documents):
        raise ValueError("embedding cache does not match corpus")
    dense_index_seconds = time.perf_counter() - phase_started
    query_embeddings = encoder.encode([query.question for query in queries])
    embedding_backend = encoder.backend
    embedding_model_sha256 = sha256_file(encoder.model_file)
    encoder.close()
    phase_started = time.perf_counter()
    graph = OpenIeGraph(
        args.openie,
        documents,
        max_entity_document_frequency=args.max_entity_document_frequency,
    )
    graph_index_seconds = time.perf_counter() - phase_started

    observations: dict[str, list[dict[str, Any]]] = {method: [] for method in METHODS}
    rankings: dict[str, dict[str, list[str]]] = {method: {} for method in METHODS}
    for query_index, query in enumerate(queries):
        phase_started = time.perf_counter()
        lexical_scores = bm25.scores(query.question)
        lexical_latency = time.perf_counter() - phase_started
        phase_started = time.perf_counter()
        dense_scores = document_embeddings @ query_embeddings[query_index]
        dense_latency = time.perf_counter() - phase_started
        lexical_ranking = top_indices(lexical_scores, len(documents))
        dense_ranking = top_indices(dense_scores, len(documents))
        phase_started = time.perf_counter()
        hybrid_scores = reciprocal_rank_fusion((lexical_ranking, dense_ranking))
        hybrid_latency = time.perf_counter() - phase_started
        phase_started = time.perf_counter()
        graph_scores = graph.propagate(dense_scores, seed_count=args.graph_seed_count)
        graph_latency = time.perf_counter() - phase_started
        reached_indices = np.flatnonzero(graph_scores > 0)
        graph_ranking = reached_indices[
            np.argsort(graph_scores[reached_indices], kind="stable")[::-1]
        ]
        openie_proxy_scores = reciprocal_rank_fusion((dense_ranking, graph_ranking))
        berrybrain_scores = reciprocal_rank_fusion(
            (lexical_ranking, dense_ranking, graph_ranking)
        )
        method_scores = {
            "bm25": (lexical_scores, lexical_latency),
            "dense": (dense_scores, dense_latency),
            "hybrid": (hybrid_scores, lexical_latency + dense_latency + hybrid_latency),
            "openie_graphrag": (openie_proxy_scores, dense_latency + graph_latency),
            "berrybrain": (
                berrybrain_scores,
                lexical_latency + dense_latency + graph_latency,
            ),
        }
        for method, (scores, latency) in method_scores.items():
            ranking = [
                document_ids[int(index)]
                for index in top_indices(scores, args.ranking_depth)
            ]
            rankings[method][query.id] = ranking
            observations[method].append(
                {
                    "queryId": query.id,
                    "hops": query.hops,
                    "latencyMs": latency * 1000.0,
                    **retrieval_metrics(ranking, query.relevant_ids),
                }
            )

    summaries: dict[str, dict[str, float]] = {}
    metric_fields = (
        "recallAt1",
        "recallAt5",
        "recallAt10",
        "mrrAt10",
        "ndcgAt10",
        "completeSupportAt10",
    )
    for method, rows in observations.items():
        latency = [float(row["latencyMs"]) for row in rows]
        summaries[method] = {field: aggregate(rows, field) for field in metric_fields}
        summaries[method].update(
            latencyMedianMs=float(np.median(latency)),
            latencyP95Ms=float(np.quantile(latency, 0.95)),
        )
    comparisons = {
        method: bootstrap_difference(
            [row["recallAt10"] for row in observations["berrybrain"]],
            [row["recallAt10"] for row in observations[method]],
            seed=args.bootstrap_seed,
            resamples=args.bootstrap_resamples,
        )
        for method in METHODS
        if method != "berrybrain"
    }

    generation: dict[str, Any] = {"status": "not-run", "sampleSize": 0, "methods": {}}
    if args.reader_model and args.qa_limit:
        reader = FlanReader(args.reader_model)
        qa_cases = select_by_hash([asdict(query) for query in queries], args.qa_limit)
        generation = {"status": "completed", "sampleSize": len(qa_cases), "methods": {}}
        query_by_id = {query.id: query for query in queries}
        for method in METHODS:
            rows = []
            for raw_case in qa_cases:
                query = query_by_id[str(raw_case["id"])]
                context = [
                    documents[document_index[item]]
                    for item in rankings[method][query.id][: args.context_documents]
                ]
                phase_started = time.perf_counter()
                prediction = reader.answer(query.question, context)
                rows.append(
                    {
                        "queryId": query.id,
                        "prediction": prediction,
                        "latencyMs": (time.perf_counter() - phase_started) * 1000.0,
                        **answer_metrics(prediction, query.answers),
                    }
                )
            generation["methods"][method] = {
                "summary": {
                    metric: aggregate(rows, metric)
                    for metric in ("exactMatch", "tokenF1", "answerContainment")
                },
                "observations": rows,
            }

    # This research snapshot places benchmark scripts one directory below
    # the Git root, unlike the original product repository layout.
    root = Path(__file__).resolve().parents[1]
    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "completed",
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git": git_state(root),
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "processor": platform.processor(),
            "pid": os.getpid(),
        },
        "protocol": {
            "dataset": "MuSiQue",
            "corpusDocuments": len(documents),
            "eligibleQueries": len(all_queries),
            "evaluatedQueries": len(queries),
            "querySelection": "ascending SHA-256(query id)"
            if len(queries) < len(all_queries)
            else "all eligible queries",
            "rankingDepth": args.ranking_depth,
            "contextDocuments": args.context_documents,
            "bootstrapSeed": args.bootstrap_seed,
            "bootstrapResamples": args.bootstrap_resamples,
            "embeddingModel": str(args.embedding_model),
            "embeddingBackend": embedding_backend,
            "embeddingModelSha256": embedding_model_sha256,
            "readerModel": str(args.reader_model) if args.reader_model else None,
            "graphSeedCount": args.graph_seed_count,
            "fusion": {
                "hybrid": "RRF(BM25, Dense)",
                "openieGraphProxy": "RRF(Dense, OpenIE graph propagation)",
                "berrybrain": "RRF(BM25, Dense, OpenIE graph propagation)",
                "rrfConstant": 60,
            },
            "maxEntityDocumentFrequency": args.max_entity_document_frequency,
            "methods": list(METHODS),
            "methodLabels": {
                "bm25": "BM25",
                "dense": "Dense retrieval",
                "hybrid": "Hybrid RRF",
                "openie_graphrag": "OpenIE graph-assisted proxy",
                "berrybrain": "BerryBrain RRF",
            },
        },
        "inputs": {
            "corpus": {"path": str(args.corpus), "sha256": sha256_file(args.corpus)},
            "queries": {"path": str(args.queries), "sha256": sha256_file(args.queries)},
            "openie": {"path": str(args.openie), "sha256": sha256_file(args.openie)},
        },
        "indexing": {
            "bm25Seconds": bm25_index_seconds,
            "denseSeconds": dense_index_seconds,
            "denseCacheHit": cache_hit,
            "denseCacheResumed": cache_resumed,
            "graphSeconds": graph_index_seconds,
            "retainedEntities": len(graph.entity_documents),
        },
        "retrieval": {
            "summaries": summaries,
            "berrybrainRecallAt10PairedBootstrap": comparisons,
            "observations": observations,
            "rankings": rankings,
        },
        "generation": generation,
        "elapsedSeconds": time.perf_counter() - started,
        "limitations": [
            "The OpenIE graph-assisted proxy uses deterministic two-step document-entity-document propagation; it is not Microsoft GraphRAG or HippoRAG 2.",
            "The BerryBrain configuration isolates retrieval scoring over shared published OpenIE output; it excludes extraction, Judge review, and asynchronous ingestion time.",
            "Per-query retrieval latency excludes query embedding and one-time index construction.",
            *(
                [
                    "The frozen local reader controls generation variance and does not estimate cloud-provider quality."
                ]
                if args.reader_model and args.qa_limit
                else ["Generation quality was not evaluated in this run."]
            ),
        ],
    }


def markdown_summary(report: dict[str, Any]) -> str:
    protocol = report["protocol"]
    lines = [
        "# Same-Corpus RAG Benchmark",
        "",
        f"Generated: {report['generatedAt']}",
        "",
        "## Protocol",
        "",
        f"- Dataset: MuSiQue ({protocol['corpusDocuments']:,} documents; {protocol['evaluatedQueries']:,} queries)",
        f"- Selection: {protocol['querySelection']}",
        f"- Bootstrap: {protocol['bootstrapResamples']:,} paired resamples, seed {protocol['bootstrapSeed']}",
        "",
        "## Retrieval",
        "",
        "| Method | R@1 | R@5 | R@10 | MRR@10 | nDCG@10 | Full support@10 | Median ms | p95 ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method in METHODS:
        row = report["retrieval"]["summaries"][method]
        lines.append(
            f"| {protocol['methodLabels'][method]} | {row['recallAt1']:.4f} | {row['recallAt5']:.4f} | {row['recallAt10']:.4f} | "
            f"{row['mrrAt10']:.4f} | {row['ndcgAt10']:.4f} | {row['completeSupportAt10']:.4f} | "
            f"{row['latencyMedianMs']:.2f} | {row['latencyP95Ms']:.2f} |"
        )
    lines.extend(["", "## Generation", ""])
    generation = report["generation"]
    if generation["status"] == "completed":
        lines.extend(
            [
                f"Common-reader sample: {generation['sampleSize']} queries.",
                "",
                "| Method | Exact match | Token F1 | Answer containment |",
                "| --- | ---: | ---: | ---: |",
            ]
        )
        for method in METHODS:
            row = generation["methods"][method]["summary"]
            lines.append(
                f"| {method} | {row['exactMatch']:.4f} | {row['tokenF1']:.4f} | {row['answerContainment']:.4f} |"
            )
    else:
        lines.append("Not run; no reader model was supplied.")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--queries", type=Path, required=True)
    parser.add_argument("--openie", type=Path, required=True)
    parser.add_argument("--embedding-model", type=Path, required=True)
    parser.add_argument("--reader-model", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path)
    parser.add_argument("--cache-dir", type=Path, default=Path(".benchmark-cache"))
    parser.add_argument("--query-limit", type=int, default=0)
    parser.add_argument("--qa-limit", type=int, default=0)
    parser.add_argument("--ranking-depth", type=int, default=10)
    parser.add_argument("--context-documents", type=int, default=5)
    parser.add_argument("--embedding-batch-size", type=int, default=24)
    parser.add_argument("--graph-seed-count", type=int, default=20)
    parser.add_argument("--max-entity-document-frequency", type=int, default=64)
    parser.add_argument("--bootstrap-seed", type=int, default=20260827)
    parser.add_argument("--bootstrap-resamples", type=int, default=10_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(markdown_summary(report))
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
