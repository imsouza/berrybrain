/**
 * Zero-dependency Node.js 20+ / ESM reference client for trusted BerryBrain backends.
 *
 * Set BERRYBRAIN_URL to the origin/mount (without /api/v1) and
 * BERRYBRAIN_SERVICE_TOKEN to an owner-issued service token.
 * Running this file directly only lists notes; it never writes data or calls a model.
 */

export class BerryBrainApiError extends Error {
  constructor(status, detail, correlationId = "") {
    super(`BerryBrain HTTP ${status}; correlation=${correlationId || "unavailable"}`);
    this.name = "BerryBrainApiError";
    this.status = status;
    this.detail = detail;
    this.correlationId = correlationId;
  }
}

function encodeNotePath(notePath) {
  return String(notePath)
    .split("/")
    .map((segment) => encodeURIComponent(segment))
    .join("/");
}

export class BerryBrainClient {
  constructor(baseUrl, token, { timeoutMs = 30_000, fetchImpl = globalThis.fetch } = {}) {
    let parsed;
    try {
      parsed = new URL(baseUrl);
    } catch {
      throw new Error("A valid HTTP(S) BerryBrain origin/mount is required");
    }
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      throw new Error("A valid HTTP(S) BerryBrain origin/mount is required");
    }
    if (parsed.username || parsed.password || parsed.search || parsed.hash) {
      throw new Error("Do not put credentials, queries, or fragments in the base URL");
    }
    if (!token || !String(token).trim()) {
      throw new Error("A service token is required");
    }
    if (typeof fetchImpl !== "function") {
      throw new Error("A standards-compatible fetch implementation is required");
    }
    this.apiUrl = `${baseUrl.replace(/\/+$/, "")}/api/v1`;
    this.token = String(token).trim();
    this.timeoutMs = timeoutMs;
    this.fetchImpl = fetchImpl;
  }

  async request(
    method,
    endpoint,
    { payload = undefined, params = undefined, timeoutMs = undefined, accept = "application/json" } = {},
  ) {
    if (
      typeof endpoint !== "string" ||
      !endpoint.startsWith("/") ||
      endpoint.startsWith("//") ||
      endpoint.split("/").includes("..")
    ) {
      throw new Error("Use an API-relative endpoint, without parent traversal");
    }

    let url = `${this.apiUrl}${endpoint}`;
    if (params) {
      const search = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          search.set(key, String(value));
        }
      }
      const qs = search.toString();
      if (qs) url += `?${qs}`;
    }

    const headers = {
      Authorization: `Bearer ${this.token}`,
      Accept: accept,
    };
    let body;
    if (payload !== undefined) {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(payload);
    }

    const response = await this.fetchImpl(url, {
      method,
      headers,
      body,
      // Never forward a workspace service token across HTTP redirects.
      redirect: "error",
      signal: AbortSignal.timeout(timeoutMs ?? this.timeoutMs),
    });

    if (!response.ok) {
      let detail = "Non-JSON response";
      try {
        const parsedError = await response.json();
        detail = parsedError?.detail ?? parsedError;
      } catch {
        // Keep fallback detail string.
      }
      throw new BerryBrainApiError(
        response.status,
        detail,
        response.headers.get("x-correlation-id") || "",
      );
    }

    const text = await response.text();
    if (!text) return null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/turtle") || accept === "text/turtle") {
      return text;
    }
    return JSON.parse(text);
  }

  listVaults() {
    return this.request("GET", "/vault/namespaces");
  }

  listNotes({ limit = 50, offset = 0, vaultId = undefined } = {}) {
    return this.request("GET", "/notes", {
      params: { limit, offset, vault_id: vaultId },
    });
  }

  readNote(notePath) {
    return this.request("GET", `/notes/${encodeNotePath(notePath)}`);
  }

  createNote(title, content, { folder = "inbox", vaultId = undefined } = {}) {
    const payload = { title, content, folder };
    if (vaultId !== undefined) payload.vault_id = vaultId;
    return this.request("POST", "/notes", { payload });
  }

  updateNote(notePath, content, baseContentHash) {
    // Never silently retry HTTP 409 conflicts; callers must reload and reconcile.
    return this.request("PUT", `/notes/${encodeNotePath(notePath)}`, {
      payload: { content, base_content_hash: baseContentHash },
    });
  }

  noteStatus(notePath) {
    return this.request("GET", `/notes/${encodeNotePath(notePath)}/status`);
  }

  async waitUntilReady(
    notePath,
    { timeoutMs = 90_000, pollIntervalsMs = [2_000, 4_000, 8_000, 15_000] } = {},
  ) {
    const deadline = Date.now() + timeoutMs;
    let step = 0;
    let lastStatus = null;
    while (true) {
      lastStatus = await this.noteStatus(notePath);
      if (
        lastStatus &&
        (lastStatus.graphReady === true ||
          ["completed", "ready", "failed"].includes(lastStatus.status))
      ) {
        return lastStatus;
      }
      const remaining = deadline - Date.now();
      if (remaining <= 0) return lastStatus;
      const delay = pollIntervalsMs[Math.min(step, pollIntervalsMs.length - 1)];
      await new Promise((resolve) => setTimeout(resolve, Math.min(delay, remaining)));
      step += 1;
    }
  }

  search(query, { limit = 10 } = {}) {
    return this.request("GET", "/search", { params: { q: query, limit } });
  }

  ask(question) {
    return this.request("POST", "/graph/infer", {
      payload: { question },
      timeoutMs: 180_000,
    });
  }

  inferenceFeedback(inferenceId, action, correction = "") {
    if (!["upvoted", "downvoted", "corrected"].includes(action)) {
      throw new Error("action must be 'upvoted', 'downvoted', or 'corrected'");
    }
    return this.request(
      "POST",
      `/graph/inferences/${encodeURIComponent(String(inferenceId))}/feedback`,
      { payload: { action, correction } },
    );
  }

  graphNodes({ limit = 250, cursor = undefined, includeProvisional = false } = {}) {
    return this.request("GET", "/graph/nodes", {
      params: {
        limit,
        cursor,
        includeProvisional: includeProvisional ? "true" : "false",
      },
    });
  }

  graphEdges({
    limit = 500,
    cursor = undefined,
    compact = true,
    includeProvisional = false,
  } = {}) {
    return this.request("GET", "/graph/edges", {
      params: {
        limit,
        cursor,
        compact: compact ? "true" : "false",
        includeProvisional: includeProvisional ? "true" : "false",
      },
    });
  }

  graphDelta(sinceVersion, { includeProvisional = false } = {}) {
    return this.request("GET", "/graph/delta", {
      params: {
        since_version: sinceVersion,
        includeProvisional: includeProvisional ? "true" : "false",
      },
    });
  }

  exportOntology({ format = "json-ld", includeProvisional = false } = {}) {
    if (format !== "json-ld" && format !== "turtle") {
      throw new Error("format must be 'json-ld' or 'turtle'");
    }
    return this.request("GET", "/graph/ontology/export", {
      params: {
        format,
        includeProvisional: includeProvisional ? "true" : "false",
      },
      accept: format === "json-ld" ? "application/ld+json" : "text/turtle",
    });
  }

  matchSkills(query = "", { taskType = "ask" } = {}) {
    return this.request("GET", "/ai/skills", {
      params: { query, task_type: taskType },
    });
  }
}

const isDirectExecution =
  typeof process !== "undefined" &&
  process.argv?.[1] &&
  import.meta.url.endsWith(process.argv[1].replace(/\\/g, "/"));

if (isDirectExecution) {
  const client = new BerryBrainClient(
    process.env.BERRYBRAIN_URL,
    process.env.BERRYBRAIN_SERVICE_TOKEN,
  );
  const notes = await client.listNotes();
  console.log(JSON.stringify(notes, null, 2));
}
