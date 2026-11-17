"""Checkpointed Gemini reader study over frozen 2Wiki rankings and gold support.

The key is read with getpass and never saved. The path-guided prompt is copied
verbatim from same_corpus_generation_benchmark.py (evidence-path-json-v1).
"""

from __future__ import annotations

import getpass
import hashlib
import json
import re
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "external-corpus"
REPORT = DATA / "2wiki-retrieval-report.json"
CHECKPOINT = DATA / "2wiki-gemini-generation.checkpoint.json"
OUTPUT = DATA / "2wiki-gemini-generation-report.json"
REPO = Path("/mnt/HDD_1/Antigravity/berrybrain")
sys.path.insert(0, str(REPO / "apps/api/benchmarks"))

from same_corpus_rag_benchmark import answer_metrics, sha256_file  # noqa: E402
from semantic_rerank_benchmark import atomic_write  # noqa: E402
from external_2wiki_retrieval import load_data  # noqa: E402

MODEL = "gemini-3.6-flash"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
METHODS = ("hybrid", "berrybrain_rerank", "oracle")
MAX_OUTPUT_TOKENS = 2048
THINKING_LEVEL = "medium"
MAX_CONTEXT_CHARACTERS = 24_000
RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504}
INITIAL_REQUEST_INTERVAL_SECONDS = 15.0
_RATE_LOCK = threading.Lock()
_NEXT_REQUEST_AT = 0.0
_REQUEST_INTERVAL = INITIAL_REQUEST_INTERVAL_SECONDS


def pace_request() -> None:
    global _NEXT_REQUEST_AT
    with _RATE_LOCK:
        now = time.monotonic()
        when = max(now, _NEXT_REQUEST_AT)
        _NEXT_REQUEST_AT = when + _REQUEST_INTERVAL
    time.sleep(max(0.0, when - now))


def slow_after_rate_limit(pause: float) -> None:
    global _NEXT_REQUEST_AT, _REQUEST_INTERVAL
    with _RATE_LOCK:
        _REQUEST_INTERVAL = max(_REQUEST_INTERVAL, 30.0)
        _NEXT_REQUEST_AT = max(_NEXT_REQUEST_AT, time.monotonic() + pause)

SYSTEM_PROMPT = (
    "Act as a relation-path reader. Use only the numbered evidence blocks. First "
    "identify the type of value requested by the final clause of the question. Then "
    "resolve every hop from the named anchors to that value; ranking order is not "
    "logical order. Do not return an intermediate person, organization, event, date, "
    "or place. Resolve pronouns and aliases, reject contradictory paths, and preserve "
    "the answer wording and units found in evidence. Return one valid JSON object with "
    "keys steps, answer, support, and sufficient. steps must be a compact array of "
    "subject-relation-object strings. answer must be only the shortest final value. "
    "support must contain every numbered block required by the path. If any required "
    "hop is missing, set answer to NOT ENOUGH EVIDENCE, support to an empty array, and "
    "sufficient to false. Do not use prior knowledge or add prose."
)


def parse_prediction(raw: str, evidence: str) -> dict[str, Any]:
    normalized = raw.strip()
    if normalized.startswith("```"):
        normalized = re.sub(r"^```(?:json)?\s*", "", normalized, flags=re.I)
        normalized = re.sub(r"\s*```$", "", normalized)
    start, end = normalized.find("{"), normalized.rfind("}")
    if start < 0 or end <= start:
        return {"prediction": "NOT ENOUGH EVIDENCE", "structuredOutputValid": False, "supportBlockIds": []}
    try:
        payload = json.loads(normalized[start : end + 1])
    except (json.JSONDecodeError, TypeError):
        return {"prediction": "NOT ENOUGH EVIDENCE", "structuredOutputValid": False, "supportBlockIds": []}
    answer = str(payload.get("answer") or "").strip()
    sufficient = payload.get("sufficient") is True
    available = {int(item) for item in re.findall(r"(?m)^\[(\d+)\]", evidence)}
    support = []
    if isinstance(payload.get("support"), list):
        for item in payload["support"]:
            try:
                block_id = int(item)
            except (TypeError, ValueError):
                continue
            if block_id in available and block_id not in support:
                support.append(block_id)
    grounded = sufficient and bool(answer) and bool(support) and answer != "NOT ENOUGH EVIDENCE"
    return {
        "prediction": answer if grounded else "NOT ENOUGH EVIDENCE",
        "structuredOutputValid": True,
        "supportBlockIds": support if grounded else [],
    }


def fingerprint() -> dict[str, Any]:
    return {
        "scriptSha256": sha256_file(Path(__file__)),
        "retrievalReportSha256": sha256_file(REPORT),
        "model": MODEL,
        "promptSha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "promptVersion": "evidence-path-json-v1",
        "temperature": 0,
        "maxOutputTokens": MAX_OUTPUT_TOKENS,
        "thinkingLevel": THINKING_LEVEL,
        "initialRequestIntervalSeconds": INITIAL_REQUEST_INTERVAL_SECONDS,
        "rateLimitBackoffSeconds": 30.0,
        "maxContextCharacters": MAX_CONTEXT_CHARACTERS,
        "methods": list(METHODS),
        "readerDifference": "Gemini 3.6 Flash, not the original DeepSeek-v4-pro reader",
    }


def tasks() -> tuple[list[dict[str, Any]], list[Any]]:
    documents, queries = load_data()
    by_id = {item.id: item for item in documents}
    retrieval = json.loads(REPORT.read_text(encoding="utf-8"))
    if set(retrieval["queryIds"]) != {query.id for query in queries}:
        raise ValueError("Retrieval query coverage differs from fixed selection")
    result: list[dict[str, Any]] = []
    for index, query in enumerate(queries):
        order = METHODS[index % len(METHODS):] + METHODS[:index % len(METHODS)]
        for method in order:
            ids = (
                list(query.relevant_ids)
                if method == "oracle"
                else retrieval["rankings"][method][query.id]
            )
            evidence = "\n\n".join(
                f"[{rank}] {by_id[doc].title}\n{by_id[doc].text.strip()}"
                for rank, doc in enumerate(ids, start=1)
            )
            if len(evidence) > MAX_CONTEXT_CHARACTERS:
                raise ValueError(f"Evidence exceeds frozen character limit: {query.id}:{method}")
            result.append({
                "taskId": f"{query.id}:{method}",
                "queryId": query.id,
                "method": method,
                "question": query.question,
                "evidence": evidence,
                "contextDocumentIds": ids,
                "referenceAnswers": list(query.answers),
                "relevantDocumentIds": list(query.relevant_ids),
            })
    return result, queries


def call_gemini(key: str, task: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": f"Question: {task['question']}\n\nEvidence:\n{task['evidence']}"}]}],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": MAX_OUTPUT_TOKENS,
            "thinkingConfig": {"thinkingLevel": THINKING_LEVEL},
        },
    }
    request = urllib.request.Request(
        URL,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
    )
    started = time.perf_counter()
    errors: list[dict[str, Any]] = []
    for attempt in range(1, 4):
        try:
            pace_request()
            with urllib.request.urlopen(request, timeout=120) as response:
                body = json.load(response)
            candidate = (body.get("candidates") or [{}])[0]
            parts = candidate.get("content", {}).get("parts") or []
            raw = "".join(str(part.get("text", "")) for part in parts if not part.get("thought"))
            parsed = parse_prediction(raw, task["evidence"])
            prediction = parsed["prediction"]
            metrics = answer_metrics(prediction, task["referenceAnswers"])
            return {
                "taskId": task["taskId"],
                "queryId": task["queryId"],
                "method": task["method"],
                "status": "completed",
                "attempts": attempt,
                "priorErrors": errors,
                "prediction": prediction,
                "rawResponse": raw,
                "structuredOutputValid": parsed["structuredOutputValid"],
                "supportBlockIds": parsed["supportBlockIds"],
                "abstained": prediction == "NOT ENOUGH EVIDENCE",
                "latencyMs": (time.perf_counter() - started) * 1000,
                "usage": body.get("usageMetadata", {}),
                "finishReason": candidate.get("finishReason"),
                "contextDocumentIds": task["contextDocumentIds"],
                "relevantDocumentIds": task["relevantDocumentIds"],
                **metrics,
            }
        except urllib.error.HTTPError as exc:
            try:
                error_body = json.loads(exc.read().decode("utf-8"))
                provider_error = error_body.get("error", {})
            except (json.JSONDecodeError, UnicodeDecodeError, OSError):
                provider_error = {}
            errors.append({
                "attempt": attempt,
                "httpStatus": exc.code,
                "providerStatus": provider_error.get("status"),
                "providerMessage": str(provider_error.get("message", ""))[:500],
            })
            if exc.code not in RETRYABLE or attempt == 3:
                break
            retry_after = exc.headers.get("Retry-After")
            try:
                pause = min(60.0, max(1.0, float(retry_after))) if retry_after else 2.0 ** attempt
            except ValueError:
                pause = 2.0 ** attempt
            if exc.code == 429:
                slow_after_rate_limit(pause)
            time.sleep(pause)
        except (TimeoutError, OSError) as exc:
            errors.append({"attempt": attempt, "errorType": type(exc).__name__})
            if attempt == 3:
                break
            time.sleep(2.0 ** attempt)
    return {
        "taskId": task["taskId"],
        "queryId": task["queryId"],
        "method": task["method"],
        "status": "failed",
        "attempts": len(errors),
        "errors": errors,
        "prediction": "NOT ENOUGH EVIDENCE",
        "abstained": True,
        "latencyMs": (time.perf_counter() - started) * 1000,
        "contextDocumentIds": task["contextDocumentIds"],
        "relevantDocumentIds": task["relevantDocumentIds"],
        **answer_metrics("NOT ENOUGH EVIDENCE", task["referenceAnswers"]),
    }


def summarize(checkpoint: dict[str, Any], all_tasks: list[dict[str, Any]]) -> dict[str, Any]:
    rows = checkpoint["rows"]
    complete = len(rows) == len(all_tasks) and all(
        row["status"] == "completed" for row in rows.values()
    )
    method_rows = {
        method: [rows[task["taskId"]] for task in all_tasks if task["method"] == method and task["taskId"] in rows]
        for method in METHODS
    }
    summaries = {}
    for method, items in method_rows.items():
        valid = [item for item in items if item["status"] == "completed"]
        answered = [item for item in valid if not item["abstained"]]
        summaries[method] = {
            "attempted": len(items),
            "completed": len(valid),
            "failed": len(items) - len(valid),
            "exactMatch": statistics.fmean(float(item["exactMatch"]) for item in items) if items else None,
            "tokenF1": statistics.fmean(float(item["tokenF1"]) for item in items) if items else None,
            "abstentionRate": statistics.fmean(float(item["abstained"]) for item in items) if items else None,
            "selectiveEM": statistics.fmean(float(item["exactMatch"]) for item in answered) if answered else None,
            "selectiveF1": statistics.fmean(float(item["tokenF1"]) for item in answered) if answered else None,
            "structuredValidRate": statistics.fmean(float(item.get("structuredOutputValid", False)) for item in valid) if valid else None,
            "promptTokens": sum(int(item.get("usage", {}).get("promptTokenCount", 0)) for item in valid),
            "completionTokens": sum(int(item.get("usage", {}).get("candidatesTokenCount", 0)) for item in valid),
        }
    paired = None
    if complete:
        query_ids = list(dict.fromkeys(task["queryId"] for task in all_tasks))
        rng = np.random.default_rng(20261023)
        indices = rng.integers(0, len(query_ids), size=(10_000, len(query_ids)))
        paired = {}
        for metric in ("exactMatch", "tokenF1"):
            differences = np.array([
                float(rows[f"{query_id}:berrybrain_rerank"][metric])
                - float(rows[f"{query_id}:hybrid"][metric])
                for query_id in query_ids
            ])
            replicates = differences[indices].mean(axis=1)
            paired[metric] = {
                "fullMinusHybrid": round(float(differences.mean()), 6),
                "bootstrap95": [
                    round(float(np.quantile(replicates, 0.025)), 6),
                    round(float(np.quantile(replicates, 0.975)), 6),
                ],
                "seed": 20261023,
                "resamples": 10_000,
            }
    return {
        "classification": "exploratory Gemini reader study; original DeepSeek reader not reproduced",
        "fingerprint": checkpoint["fingerprint"],
        "status": "completed" if complete else "partial",
        "taskCount": len(all_tasks),
        "recordedTasks": len(rows),
        "summaries": summaries,
        "paired": paired,
        "observations": method_rows,
    }


def main() -> None:
    all_tasks, _ = tasks()
    fp = fingerprint()
    if CHECKPOINT.exists():
        checkpoint = json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        if checkpoint["fingerprint"] != fp:
            operational_fields = {
                "scriptSha256", "initialRequestIntervalSeconds", "rateLimitBackoffSeconds"
            }
            frozen_old = {key: value for key, value in checkpoint["fingerprint"].items()
                          if key not in operational_fields}
            frozen_new = {key: value for key, value in fp.items()
                          if key not in operational_fields}
            if frozen_old != frozen_new:
                raise ValueError("Generation checkpoint scientific fingerprint differs")
            checkpoint.setdefault("technicalAmendments", []).append({
                "reason": "Reduce request rate after first batch received HTTP 429; model, prompt, rankings and metrics unchanged",
                "previousFingerprint": checkpoint["fingerprint"],
                "currentFingerprint": fp,
            })
            checkpoint["fingerprint"] = fp
            atomic_write(CHECKPOINT, checkpoint)
    else:
        checkpoint = {"fingerprint": fp, "rows": {}}
    pending = [
        item for item in all_tasks
        if checkpoint["rows"].get(item["taskId"], {}).get("status") != "completed"
    ]
    if pending:
        key = getpass.getpass("Gemini API key: ")
        if not key:
            raise ValueError("Empty API key")
        for offset in range(0, len(pending), 6):
            batch = pending[offset : offset + 6]
            with ThreadPoolExecutor(max_workers=3) as pool:
                futures = [pool.submit(call_gemini, key, task) for task in batch]
                for future in as_completed(futures):
                    row = future.result()
                    checkpoint["rows"][row["taskId"]] = row
            atomic_write(CHECKPOINT, checkpoint)
            print(f"generation {len(checkpoint['rows'])}/{len(all_tasks)}", flush=True)
            if any(
                item["status"] == "failed" and any(error.get("httpStatus") == 429 for error in item.get("errors", []))
                for item in checkpoint["rows"].values()
            ):
                print("stopping after persistent rate-limit response", flush=True)
                break
    report = summarize(checkpoint, all_tasks)
    atomic_write(OUTPUT, report)
    print(json.dumps({"status": report["status"], "summaries": report["summaries"]}), flush=True)


if __name__ == "__main__":
    main()
