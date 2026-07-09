import asyncio
import json
import os
import re
import time
from pathlib import Path

import httpx

from berrybrain_worker.cloud_gateway import (
    CloudError,
    cloud_generate,
    cloud_generate_embedding,
    cloud_generate_json,
)
from berrybrain_worker.config import WorkerSettings
from berrybrain_worker.ollama_gateway import (
    OllamaError,
    check_health,
    generate,
    generate_embedding,
    generate_json,
    log_ai_call,
)

PROMPT_DIR = Path(__file__).resolve().parents[3] / "prompts"
PROMPT_CACHE: dict[str, str] = {}
_ai_config: dict = {"provider": "local"}  # cached from API
_last_config_fetch = 0.0


def load_prompt(name: str) -> str:
    if name not in PROMPT_CACHE:
        path = PROMPT_DIR / name
        if path.exists():
            PROMPT_CACHE[name] = path.read_text(encoding="utf-8")
        else:
            PROMPT_CACHE[name] = ""
    return PROMPT_CACHE[name]


def fallback_terms(note: dict, limit: int = 8) -> list[str]:
    title = str(note.get("title") or Path(str(note.get("path", ""))).stem).replace(
        "-", " "
    )
    content = str(note.get("content") or "")
    candidates: list[str] = []
    candidates.extend(re.findall(r"^#{1,3}\\s+(.+)$", content, flags=re.MULTILINE))
    candidates.extend(re.findall(r"\\b[A-Z][A-Za-z0-9_+.-]{2,}\\b", content))
    candidates.extend(
        [part.strip() for part in re.split(r"[:/\\-|]", title) if part.strip()]
    )
    candidates.append(title.strip())
    seen: set[str] = set()
    terms: list[str] = []
    for item in candidates:
        clean = " ".join(str(item).strip().split())
        key = clean.lower()
        if len(clean) < 3 or len(clean) > 80 or key in seen:
            continue
        seen.add(key)
        terms.append(clean)
        if len(terms) >= limit:
            break
    return terms


def fallback_classification(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "note_type": "study",
        "topics": terms[:5],
        "tags": [normalize_slug(term) for term in terms[:5]],
        "concepts": terms,
        "source": "deterministic_fallback",
    }


def fallback_assimilation(note: dict) -> dict:
    content = str(note.get("content") or "")
    terms = fallback_terms(note)
    summary = " ".join(content.replace("#", " ").split())[:360]
    return {
        "summary": summary or f"Nota sobre {note.get('title') or note.get('path')}.",
        "concepts": terms,
        "gaps": [],
        "questions": [],
        "source": "deterministic_fallback",
    }


def fallback_concepts(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "concepts": [
            {
                "name": term,
                "description": "",
                "confidence": 0.35,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_entities(note: dict) -> dict:
    terms = fallback_terms(note)
    return {
        "entities": [
            {
                "name": term,
                "type": "term",
                "confidence": 0.3,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_topics(note: dict) -> dict:
    terms = fallback_terms(note, limit=5)
    return {
        "topics": [
            {
                "name": term,
                "confidence": 0.3,
                "source": "deterministic_fallback",
            }
            for term in terms
        ],
        "source": "deterministic_fallback",
    }


def fallback_context(note: dict) -> dict:
    title = note.get("title") or Path(str(note.get("path", ""))).stem
    return {
        "contexts": [
            {
                "name": str(title).replace("-", " "),
                "description": "Contexto inferido localmente porque a IA nao retornou JSON valido.",
                "confidence": 0.25,
                "source": "deterministic_fallback",
            }
        ],
        "source": "deterministic_fallback",
    }


def normalize_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


async def main() -> None:
    settings = WorkerSettings()
    async with httpx.AsyncClient(timeout=10) as client:
        await assert_api_ready(client, settings.api_url)
        ollama_ok = await check_health(settings.ollama_base_url, timeout=5)
        if ollama_ok:
            print(f"Ollama ready: {settings.ollama_base_url}")
        else:
            print(f"WARNING: Ollama not reachable at {settings.ollama_base_url}")
        await send_heartbeat(client, settings.api_url, 0, 0, ollama_ok)
        await run_loop(client, settings, ollama_ok)


async def run_loop(
    client: httpx.AsyncClient, settings: WorkerSettings, ollama_ok: bool = False
) -> None:
    empty_count = 0
    jobs_processed = 0
    errors = 0

    await fetch_ai_config(client, settings.api_url)

    while True:
        jobs = []
        for _ in range(4):
            try:
                j = await claim_next_job(client, settings.api_url)
            except httpx.HTTPError as exc:
                print(f"API unavailable while claiming job: {exc}")
                await asyncio.sleep(settings.loop_interval_seconds)
                break
            if j:
                jobs.append(j)
        if not jobs:
            empty_count += 1
            ollama_ok = await check_health(settings.ollama_base_url, timeout=5)
            await send_heartbeat(
                client, settings.api_url, jobs_processed, errors, ollama_ok
            )
            sleep_time = min(
                settings.loop_interval_seconds
                * (1 + empty_count // settings.max_consecutive_empty),
                settings.loop_interval_seconds * 4,
            )
            await asyncio.sleep(sleep_time)
            continue

        empty_count = 0
        if time.time() - _last_config_fetch > 60:
            await fetch_ai_config(client, settings.api_url)

        async def handle(job):
            nonlocal jobs_processed, errors
            attempts = getattr(job, "attempts", 0) or 0
            for retry in range(3):
                try:
                    await process_job(client, settings, job)
                    jobs_processed += 1
                    print(f"completed job {job['id']} ({job['type']})")
                    return
                except Exception as exc:
                    if retry < 2:
                        print(
                            f"retrying job {job['id']} ({job['type']}) — attempt {retry + 1}/2: {exc}"
                        )
                        await asyncio.sleep(2 * (retry + 1))
                        continue
                    errors += 1
                    error_msg = str(exc)[:2000]
                    await fail_job(client, settings.api_url, int(job["id"]), error_msg)
                    print(f"failed job {job['id']} ({job['type']}): {error_msg}")

        await asyncio.gather(*(handle(j) for j in jobs))
        ollama_ok = await check_health(settings.ollama_base_url, timeout=5)
        await send_heartbeat(
            client, settings.api_url, jobs_processed, errors, ollama_ok
        )
        await asyncio.sleep(settings.loop_interval_seconds)


async def assert_api_ready(client: httpx.AsyncClient, api_url: str) -> None:
    last_error = None
    for attempt in range(30):
        try:
            response = await client.get(f"{api_url}/health")
            response.raise_for_status()
            print(f"API ready: {api_url}")
            return
        except httpx.HTTPError as exc:
            last_error = exc
            await asyncio.sleep(min(2 + attempt // 5, 8))
    raise RuntimeError(f"API not ready at {api_url}: {last_error}")


async def claim_next_job(client: httpx.AsyncClient, api_url: str) -> dict | None:
    response = await client.post(f"{api_url}/api/v1/jobs/claim")
    response.raise_for_status()
    payload = response.json()
    return payload.get("job")


async def process_job(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict
) -> None:
    job_type = job["type"]
    payload = job.get("payload", {})

    if job_type == "PARSE_NOTE":
        await process_parse_note(client, settings, job, payload)
    elif job_type == "CLASSIFY_NOTE":
        await process_classify_note(client, settings, job, payload)
    elif job_type == "ASSIMILATE_NOTE":
        await process_assimilate_note(client, settings, job, payload)
    elif job_type == "EXTRACT_CONCEPTS":
        await process_extract_concepts(client, settings, job, payload)
    elif job_type == "EXTRACT_ENTITIES":
        await process_extract_entities(client, settings, job, payload)
    elif job_type == "DETECT_TOPICS":
        await process_detect_topics(client, settings, job, payload)
    elif job_type == "EXTRACT_CONTEXT":
        await process_extract_context(client, settings, job, payload)
    elif job_type == "GENERATE_EMBEDDING":
        await process_generate_embedding(client, settings, job, payload)
    elif job_type == "FIND_CONNECTIONS":
        await process_find_connections(client, settings, job, payload)
    elif job_type == "GENERATE_FLASHCARDS":
        raise ValueError(
            "GENERATE_FLASHCARDS is disabled; flashcards/review removed from product"
        )
    elif job_type == "GENERATE_INSIGHTS":
        await process_generate_insights(client, settings, job, payload)
    elif job_type == "GENERATE_GRAPH_INSIGHTS":
        await process_generate_graph_insights(client, settings, job, payload)
    elif job_type == "GENERATE_NOTE_TITLE":
        await process_generate_note_title(client, settings, job, payload)
    elif job_type == "EXPAND_KNOWLEDGE_GRAPH":
        await process_expand_knowledge_graph(client, settings, job, payload)
    elif job_type == "GENERATE_INFERRED_CONNECTIONS":
        await process_generate_inferred_connections(client, settings, job, payload)
    elif job_type == "GENERATE_NODE_SUMMARY":
        await process_generate_node_summary(client, settings, job, payload)
    elif job_type == "UPDATE_GRAPH_CLUSTERS":
        await process_update_graph_clusters(client, settings, job, payload)
    elif job_type == "UPDATE_GRAPH_STATS":
        await process_update_graph_stats(client, settings, job, payload)
    elif job_type == "EXPAND_CONCEPT_TO_NOTE":
        await process_expand_concept_to_note(client, settings, job, payload)
    elif job_type == "CREATE_NOTE_FROM_INSIGHT":
        await process_create_note_from_insight(client, settings, job, payload)
    elif job_type == "CREATE_REVIEW_FROM_INSIGHT":
        await process_create_review_from_insight(client, settings, job, payload)
    else:
        raise ValueError(f"Unsupported job type: {job_type}")


async def fetch_note(client: httpx.AsyncClient, api_url: str, note_path: str) -> dict:
    encoded = "/".join(part for part in note_path.split("/"))
    response = await client.get(f"{api_url}/api/v1/notes/{encoded}")
    response.raise_for_status()
    return response.json()


async def upsert_metadata(
    client: httpx.AsyncClient,
    api_url: str,
    note_path: str,
    generation_type: str,
    content: dict,
    content_hash: str,
    model_used: str,
) -> None:
    encoded = "/".join(part for part in note_path.split("/"))
    response = await client.put(
        f"{api_url}/api/v1/metadata/{generation_type}?note_path={encoded}",
        json={
            "content": content,
            "content_hash": content_hash,
            "model_used": model_used,
        },
    )
    response.raise_for_status()


async def fetch_ai_config(client: httpx.AsyncClient, api_url: str) -> dict:
    global _ai_config, _last_config_fetch
    try:
        r = await client.get(f"{api_url}/api/v1/settings/ai/config", timeout=5)
        if r.status_code == 200:
            _ai_config = r.json()
            _last_config_fetch = time.time()
    except Exception:
        pass
    return _ai_config


async def ollama_call(
    client: httpx.AsyncClient,
    api_url: str,
    settings: WorkerSettings,
    note_path: str,
    model: str,
    prompt: str,
    system: str | None = None,
    json_mode: bool = True,
) -> dict | str:
    start = time.time()
    cfg = _ai_config
    try:
        provider = cfg.get("provider") or "local"
        is_cloud = provider != "local"
        if is_cloud and cfg.get("cloud_api_url") and cfg.get("cloud_api_key"):
            cloud_model = cfg.get("cloud_model") or model
            if json_mode:
                result = await cloud_generate_json(
                    cfg["cloud_api_url"],
                    cfg["cloud_api_key"],
                    cloud_model,
                    prompt,
                    system,
                    settings.ollama_timeout,
                )
            else:
                result = await cloud_generate(
                    cfg["cloud_api_url"],
                    cfg["cloud_api_key"],
                    cloud_model,
                    prompt,
                    system,
                    settings.ollama_timeout,
                )
        else:
            if json_mode:
                result = await generate_json(
                    settings.ollama_base_url,
                    model,
                    prompt,
                    system,
                    settings.ollama_timeout,
                )
            else:
                result = await generate(
                    settings.ollama_base_url,
                    model,
                    prompt,
                    system,
                    settings.ollama_timeout,
                )
    except (OllamaError, CloudError):
        raise

    duration_ms = (time.time() - start) * 1000
    response_text = (
        result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
    )
    await log_ai_call(
        client,
        api_url,
        model,
        prompt,
        response_text,
        duration_ms,
        target_type="note",
        target_id=note_path,
    )
    return result


def effective_generation_model(local_model: str) -> str:
    cfg = _ai_config
    if (
        cfg.get("provider") == "cloud"
        and cfg.get("cloud_api_url")
        and cfg.get("cloud_api_key")
    ):
        return cfg.get("cloud_model") or local_model
    return local_model


def effective_generation_provider() -> str:
    cfg = _ai_config
    if cfg.get("provider") == "cloud":
        url = str(cfg.get("cloud_api_url") or "").lower()
        model = str(cfg.get("cloud_model") or "").lower()
        if "nvidia" in url or "nvidia" in model or "nemotron" in model:
            return "nvidia-nim"
        return "cloud"
    return "ollama"


async def process_parse_note(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    import re, json as _json

    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")

    frontmatter = {}
    links = []
    headings = []
    word_count = 0
    language = note.get("language", "pt-BR")

    fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", note_content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        try:
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    frontmatter[k.strip().lower()] = v.strip()
        except Exception:
            pass

    links = re.findall(r"\[\[([^\]]+)\]\]", note_content)
    headings = re.findall(r"^(#{1,6})\s+(.+)$", note_content, re.MULTILINE)
    words = re.findall(r"\b\w+\b", note_content)
    word_count = len(words)
    if word_count > 0:
        en_cnt = sum(1 for w in words if w.isascii())
        language = "pt-BR" if en_cnt / word_count < 0.6 else "en"

    parsed = {
        "frontmatter": frontmatter,
        "links": links,
        "headings": [{"level": len(h[0]), "text": h[1].strip()} for h in headings],
        "word_count": word_count,
        "reading_time_min": max(1, word_count // 200),
        "language": language,
    }

    await upsert_metadata(
        client,
        settings.api_url,
        note_path,
        "parse",
        parsed,
        content_hash,
        "parser-v1",
    )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_classify_note(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")
    model_used = effective_generation_model(settings.fast_model)

    system_prompt = load_prompt("classify-note.v1.md")
    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.fast_model,
            note_content,
            system_prompt,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_classification(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_classification(note)

    await upsert_metadata(
        client,
        settings.api_url,
        note_path,
        "classification",
        result,
        content_hash,
        model_used,
    )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_assimilate_note(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")
    frontmatter = note.get("frontmatter", {})
    model_used = effective_generation_model(settings.main_model)

    system_prompt = load_prompt("assimilation.v1.md")
    prompt_text = f"""# Nota: {note.get("title", note_path)}

## Frontmatter
{json.dumps(frontmatter, ensure_ascii=False, indent=2)}

## Conteudo
{note_content}"""

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system_prompt,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_assimilation(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_assimilation(note)

    summary = result.get("summary", "")
    if summary:
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "summary",
            {"summary": summary},
            content_hash,
            model_used,
        )

    concepts = result.get("concepts", [])
    if concepts:
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "concepts",
            {"concepts": concepts},
            content_hash,
            model_used,
        )

    gaps = result.get("gaps", [])
    if gaps:
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "gaps",
            {"gaps": gaps},
            content_hash,
            model_used,
        )

    questions = result.get("questions", [])
    if questions:
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "questions",
            {"questions": questions},
            content_hash,
            model_used,
        )

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_generate_embedding(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")

    clean_text = note_content.replace("*", " ").replace("#", " ").replace("`", " ")
    cfg = _ai_config
    vec = None
    embedding_provider = "ollama"
    embedding_model = settings.embedding_model
    cloud_embedding_model = cfg.get("cloud_embedding_model") or cfg.get(
        "embedding_model"
    )
    if (
        cfg.get("provider") == "cloud"
        and cfg.get("cloud_api_url")
        and cfg.get("cloud_api_key")
        and cloud_embedding_model
    ):
        try:
            vec = await cloud_generate_embedding(
                cfg["cloud_api_url"],
                cfg["cloud_api_key"],
                cloud_embedding_model,
                clean_text[:4000],
                settings.ollama_timeout,
            )
            embedding_provider = "cloud"
            embedding_model = cloud_embedding_model
        except CloudError as e:
            print(f"Cloud embedding failed ({e}), falling back to Ollama")
    if vec is None:
        ollama_embedding_available = await check_health(
            settings.ollama_base_url, timeout=2
        )
        if not ollama_embedding_available:
            await upsert_metadata(
                client,
                settings.api_url,
                note_path,
                "embedding_status",
                {
                    "status": "skipped",
                    "reason": "No embedding provider available",
                    "provider": "ollama",
                    "model": settings.embedding_model,
                },
                content_hash,
                settings.embedding_model,
            )
            await complete_job(client, settings.api_url, int(job["id"]))
            return
        try:
            vec = await generate_embedding(
                settings.ollama_base_url,
                settings.embedding_model,
                clean_text[:4000],
                settings.ollama_timeout,
            )
        except OllamaError as e:
            await upsert_metadata(
                client,
                settings.api_url,
                note_path,
                "embedding_status",
                {
                    "status": "skipped",
                    "reason": str(e)[:500],
                    "provider": "ollama",
                    "model": settings.embedding_model,
                },
                content_hash,
                settings.embedding_model,
            )
            await complete_job(client, settings.api_url, int(job["id"]))
            return
    encoded = "/".join(part for part in note_path.split("/"))
    try:
        r = await client.get(f"{settings.api_url}/api/v1/notes/{encoded}")
        r.raise_for_status()
        note_data = r.json() if r.status_code == 200 else {}
    except Exception:
        note_data = {}

    note_id = note_data.get("id", 0)
    if not note_id:
        raise ValueError(f"Note id not found for {note_path}")

    response = await client.post(
        f"{settings.api_url}/api/v1/embeddings",
        json={
            "note_id": note_id,
            "content_hash": content_hash,
            "vector": vec,
            "provider": embedding_provider,
            "model": embedding_model,
        },
    )
    response.raise_for_status()

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_find_connections(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")

    try:
        search_response = await client.get(
            f"{settings.api_url}/api/v1/search",
            params={"q": note.get("title", ""), "limit": 10, "mode": "hybrid"},
        )
        if search_response.status_code == 200:
            candidates = search_response.json().get("results", [])
        else:
            candidates = []
    except Exception:
        candidates = []

    candidate_texts = []
    for c in candidates:
        c_path = c.get("path", "")
        if c_path == note_path:
            continue
        candidate_texts.append(
            f"- [{c.get('title', c_path)}] (path: {c_path})\n  snippet: {c.get('snippet', '')[:200]}"
        )

    if not candidate_texts:
        await complete_job(client, settings.api_url, int(job["id"]))
        return

    system_prompt = load_prompt("connections.v1.md")
    prompt_text = f"""Nota fonte: {note.get("title", note_path)}
path: {note_path}

Conteudo da nota fonte:
{note_content[:3000]}

Candidatos a conexoes:
{chr(10).join(candidate_texts[:5])}"""

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system_prompt,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = {"connections": [], "source": "deterministic_fallback"}

    connections = result.get("connections", [])
    if connections:
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "connections",
            {"connections": connections},
            content_hash,
            settings.main_model,
        )
        response = await client.post(
            f"{settings.api_url}/api/v1/connections/sync",
            json={"note_path": note_path, "connections": connections},
        )
        response.raise_for_status()

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_generate_insights(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    scope = payload.get("scope", "daily")
    content_hash = payload.get("content_hash", "")

    status_response = await client.get(f"{settings.api_url}/api/v1/status")
    status_response.raise_for_status()
    status_data = status_response.json()
    system_prompt = load_prompt("daily-insights.v1.md")
    prompt_text = f"Scope: {scope}\nTotal notes: {status_data.get('notes', 0)}"

    result = await ollama_call(
        client,
        settings.api_url,
        settings,
        "system",
        settings.main_model,
        prompt_text,
        system_prompt,
        json_mode=True,
    )

    if isinstance(result, str):
        result = {"raw": result}

    await upsert_metadata(
        client,
        settings.api_url,
        "system",
        f"insights/{scope}",
        result,
        content_hash,
        settings.main_model,
    )
    response = await client.post(
        f"{settings.api_url}/api/v1/insights/sync",
        json={"payload": result},
    )
    response.raise_for_status()

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_expand_knowledge_graph(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    response = await client.post(f"{settings.api_url}/api/v1/graph/expand")
    response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def complete_job(client: httpx.AsyncClient, api_url: str, job_id: int) -> None:
    response = await client.post(f"{api_url}/api/v1/jobs/{job_id}/complete")
    response.raise_for_status()


async def fail_job(
    client: httpx.AsyncClient,
    api_url: str,
    job_id: int,
    error_message: str,
) -> None:
    response = await client.post(
        f"{api_url}/api/v1/jobs/{job_id}/fail",
        json={"error_message": error_message},
    )
    response.raise_for_status()


async def send_heartbeat(
    client: httpx.AsyncClient,
    api_url: str,
    jobs_processed: int,
    errors: int,
    ollama_healthy: bool = False,
) -> None:
    try:
        await client.post(
            f"{api_url}/api/v1/worker/heartbeat",
            json={
                "jobs_processed": jobs_processed,
                "errors": errors,
                "ollama_healthy": ollama_healthy,
            },
        )
    except Exception:
        pass


async def process_generate_note_title(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    import re

    note_path = payload.get("note_path", "")
    note = await fetch_note(client, settings.api_url, note_path)
    content = note.get("content", "")
    default_title = "Rascunho"

    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        default_title = h1_match.group(1).strip()[:80]
    elif len(content) > 20:
        first_line = content.strip().split("\n")[0][:80]
        if first_line and not first_line.startswith("#"):
            default_title = first_line

    try:
        system = "Voce e um gerador de titulos. Retorne APENAS o titulo. Nada mais. Sem aspas, sem explicacao, sem prefixos como 'Aqui esta'. Apenas o titulo puro."
        result = await generate(
            settings.ollama_base_url,
            settings.fast_model,
            f"Titulo (max 10 palavras, pt-BR):\n\n{content[:800]}",
            system=system,
            ollama_timeout=settings.ollama_timeout,
        )
        ai_title = result.strip()[:120]
        garbage_prefixes = [
            "aqui estao",
            "aqui esta",
            "segue o titulo",
            "titulo:",
            "título:",
            "opcoes de titulo",
            "opcao de titulo",
            "sugestoes de titulo",
            "por favor",
            "claro",
            "certamente",
        ]
        for prefix in garbage_prefixes:
            if ai_title.lower().startswith(prefix):
                ai_title = ai_title[len(prefix) :].strip(" :\n-")
        if ai_title and len(ai_title) > 3 and len(ai_title) <= 80:
            default_title = ai_title.replace("\n", " ").strip()
    except Exception:
        pass

    slug = re.sub(r"[^\w\-]", "-", default_title.lower())[:60].strip("-") or "rascunho"
    try:
        await client.put(
            f"{settings.api_url}/api/v1/notes/{'/'.join(note_path.split('/'))}/rename",
            json={"title": default_title},
        )
        print(f"renamed {note_path} -> {slug}")
    except Exception as e:
        print(f"failed to rename {note_path}: {e}")

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_extract_concepts(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    model_used = effective_generation_model(settings.main_model)
    system = load_prompt("concept-extract.v1.md")
    prompt_text = f"Conteudo da nota:\n\n{note.get('content', '')[:3000]}"

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_concepts(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_concepts(note)
    if isinstance(result, dict):
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "concepts",
            result,
            content_hash,
            model_used,
        )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_extract_entities(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    model_used = effective_generation_model(settings.main_model)
    system = load_prompt("concept-extract.v1.md")
    prompt_text = f"Extraia APENAS entidades (tecnologias, ferramentas, pessoas, organizacoes):\n\n{note.get('content', '')[:3000]}"

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_entities(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_entities(note)
    if isinstance(result, dict):
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "entities",
            result,
            content_hash,
            model_used,
        )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_detect_topics(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    model_used = effective_generation_model(settings.main_model)
    system = load_prompt("concept-extract.v1.md")
    prompt_text = f"Extraia APENAS os topicos (areas tematicas amplas):\n\n{note.get('content', '')[:3000]}"

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_topics(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_topics(note)
    if isinstance(result, dict):
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "topics",
            result,
            content_hash,
            model_used,
        )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_extract_context(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    model_used = effective_generation_model(settings.main_model)
    system = load_prompt("concept-extract.v1.md")
    prompt_text = f"Extraia APENAS o contexto (dominio, pre-requisitos, aplicacoes):\n\n{note.get('content', '')[:3000]}"

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.main_model,
            prompt_text,
            system,
            json_mode=True,
        )
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            result = fallback_context(note)
    except (OllamaError, CloudError, json.JSONDecodeError, ValueError):
        result = fallback_context(note)
    if isinstance(result, dict):
        await upsert_metadata(
            client,
            settings.api_url,
            note_path,
            "context",
            result,
            content_hash,
            model_used,
        )
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_generate_graph_insights(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    summary_r = await client.get(f"{settings.api_url}/api/v1/graph/summary")
    summary_r.raise_for_status()
    graph_r = await client.get(f"{settings.api_url}/api/v1/graph")
    graph_r.raise_for_status()
    notes_r = await client.get(f"{settings.api_url}/api/v1/notes")
    notes_r.raise_for_status()
    graph_summary = summary_r.json()
    graph_data = graph_r.json()
    notes_data = notes_r.json()
    system = load_prompt("insight-generate.v1.md")
    graph_nodes = graph_data.get("nodes", []) if isinstance(graph_data, dict) else []
    graph_edges = graph_data.get("edges", []) if isinstance(graph_data, dict) else []
    notes = notes_data.get("notes", []) if isinstance(notes_data, dict) else []
    note_items = []
    for note in notes[:30]:
        if not isinstance(note, dict):
            continue
        content = str(note.get("content") or "")
        note_items.append(
            {
                "title": note.get("title") or note.get("path"),
                "path": note.get("path"),
                "snippet": content[:900],
            }
        )
    prompt_text = json.dumps(
        {
            "task": "Gerar insights reais do segundo cerebro com contexto, conclusoes, hipoteses, premissas, afirmacoes e lacunas.",
            "rules": [
                "Use somente as notas, vertices e conexoes fornecidos.",
                "Nao gere insights sem evidencia concreta.",
                "Nao transforme contadores em insight.",
                "Cada insight precisa citar evidencia em notas, vertices ou conexoes.",
            ],
            "graphSummary": graph_summary,
            "nodes": graph_nodes[:120],
            "edges": graph_edges[:160],
            "notes": note_items,
        },
        ensure_ascii=False,
    )

    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            "system",
            settings.main_model,
            prompt_text,
            system,
            json_mode=True,
        )
    except OllamaError:
        await fail_job(
            client,
            settings.api_url,
            int(job["id"]),
            f"Ollama nao esta disponivel. Verifique se o Ollama esta rodando em {settings.ollama_url}",
        )
        return
    except CloudError as ce:
        await fail_job(
            client,
            settings.api_url,
            int(job["id"]),
            f"Cloud provider indisponivel: {str(ce)[:200]}",
        )
        return
    except CloudError:
        await fail_job(
            client,
            settings.api_url,
            int(job["id"]),
            "Cloud provider indisponível. Verifique a configuração ou tente novamente.",
        )
        return
    if isinstance(result, dict):
        provider = effective_generation_provider()
        model = effective_generation_model(settings.main_model)
        insights = result.get("insights", [])
        if isinstance(insights, list):
            for item in insights:
                if not isinstance(item, dict):
                    continue
                item.setdefault("provider", provider)
                item.setdefault("model", model)
                item.setdefault("status", "suggested")
        response = await client.post(
            f"{settings.api_url}/api/v1/insights/sync",
            json={"payload": result},
        )
        response.raise_for_status()
        expand_response = await client.post(f"{settings.api_url}/api/v1/graph/expand")
        expand_response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_generate_inferred_connections(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    response = await client.post(
        f"{settings.api_url}/api/v1/connections/sync",
        json={"note_path": note_path, "connections": []},
    )
    response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_generate_node_summary(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    response = await client.post(f"{settings.api_url}/api/v1/graph/expand")
    response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_update_graph_clusters(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    response = await client.post(f"{settings.api_url}/api/v1/graph/expand")
    response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_update_graph_stats(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    response = await client.get(f"{settings.api_url}/api/v1/graph/summary")
    response.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_expand_concept_to_note(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    note_path = payload.get("note_path", "")
    content_hash = payload.get("content_hash", "")
    note = await fetch_note(client, settings.api_url, note_path)
    note_content = note.get("content", "")
    frontmatter = note.get("frontmatter", {})

    concepts_resp = await client.get(
        f"{settings.api_url}/api/v1/metadata/concepts?note_path={note_path}"
    )
    concepts_resp.raise_for_status()
    concepts_data = concepts_resp.json().get("content", {}).get("concepts", [])
    if not concepts_data:
        await complete_job(client, settings.api_url, int(job["id"]))
        return

    system = load_prompt("expand-concept.v1.md")
    for concept in concepts_data[:3]:
        name = concept.get("name") or concept.get("concept", "")
        if not name:
            continue
        prompt_text = f"Nota origem: {note.get('title', note_path)}\nConceito: {name}\nContexto: {frontmatter}\n\n{note_content[:3000]}"
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            note_path,
            settings.fast_model,
            prompt_text,
            system,
            json_mode=False,
        )
        if isinstance(result, dict):
            text = result.get("content") or result.get("text", "")
        else:
            text = str(result)
        if not text.strip():
            continue
        title = name if not name.startswith("#") else name.lstrip("#").strip()
        create_resp = await client.post(
            f"{settings.api_url}/api/v1/notes",
            json={"title": title, "content": text, "folder": "estudos"},
        )
        create_resp.raise_for_status()

    await complete_job(client, settings.api_url, int(job["id"]))


async def process_create_note_from_insight(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    insight_id = payload.get("insight_id") or _extract_insight_id_from_payload(payload)
    if not insight_id:
        await fail_job(client, settings.api_url, int(job["id"]), "insight_id missing")
        return
    r = await client.get(f"{settings.api_url}/api/v1/insights?limit=50")
    r.raise_for_status()
    items = r.json().get("insights", [])
    insight = next((i for i in items if i.get("id") == insight_id), None)
    if not insight:
        await fail_job(
            client, settings.api_url, int(job["id"]), f"insight {insight_id} not found"
        )
        return
    title = insight.get("title", "Nota de insight")
    body_parts = [f"# {title}\n"]
    if insight.get("description"):
        body_parts.append(insight["description"] + "\n")
    if insight.get("whyItMatters"):
        body_parts.append(f"\n## Por que importa\n\n{insight['whyItMatters']}\n")
    evidence = insight.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        body_parts.append("\n## Evidências\n\n")
        for e in evidence:
            body_parts.append(f"- {str(e)}\n")
    if insight.get("suggestedAction"):
        body_parts.append(f"\n## Ação sugerida\n\n{insight['suggestedAction']}\n")
    body_parts.append(
        f"\n---\n*Nota gerada a partir do insight da IA [{insight.get('provider', '')} / {insight.get('model', '')}]*\n"
    )
    resp = await client.post(
        f"{settings.api_url}/api/v1/notes",
        json={"title": title, "content": "".join(body_parts), "folder": "insights"},
    )
    resp.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


async def process_create_review_from_insight(
    client: httpx.AsyncClient, settings: WorkerSettings, job: dict, payload: dict
) -> None:
    insight_id = payload.get("insight_id") or _extract_insight_id_from_payload(payload)
    if not insight_id:
        await fail_job(client, settings.api_url, int(job["id"]), "insight_id missing")
        return
    r = await client.get(f"{settings.api_url}/api/v1/insights?limit=50")
    r.raise_for_status()
    items = r.json().get("insights", [])
    insight = next((i for i in items if i.get("id") == insight_id), None)
    if not insight:
        await fail_job(
            client, settings.api_url, int(job["id"]), f"insight {insight_id} not found"
        )
        return
    title = insight.get("title", "Revisão")
    prompt_text = json.dumps(
        {
            "task": "Gere 3 perguntas de revisão baseadas neste insight.",
            "insight_title": title,
            "insight_description": insight.get("description", ""),
            "evidence": insight.get("evidence", []),
        },
        ensure_ascii=False,
    )
    system = "Gere perguntas de revisão com resposta curta. Responda apenas com 3 perguntas, uma por linha, começando com 'Q: '."
    try:
        result = await ollama_call(
            client,
            settings.api_url,
            settings,
            "review",
            settings.main_model,
            prompt_text,
            system,
            json_mode=False,
        )
    except (OllamaError, CloudError) as e:
        await fail_job(client, settings.api_url, int(job["id"]), str(e)[:200])
        return
    questions = str(result or "")
    body = f"# Revisão: {title}\n\n## Perguntas\n\n{questions}\n\n---\n*Revisão gerada do insight [{insight.get('provider', '')} / {insight.get('model', '')}]*\n"
    resp = await client.post(
        f"{settings.api_url}/api/v1/notes",
        json={"title": f"Revisão: {title[:50]}", "content": body, "folder": "revisoes"},
    )
    resp.raise_for_status()
    await complete_job(client, settings.api_url, int(job["id"]))


def _extract_insight_id_from_payload(payload: dict) -> int | None:
    raw = payload if isinstance(payload, dict) else {}
    if isinstance(raw.get("payload"), str):
        try:
            raw = json.loads(raw["payload"])
        except:
            pass
    vid = raw.get("insight_id")
    return int(vid) if vid is not None else None


if __name__ == "__main__":
    asyncio.run(main())
