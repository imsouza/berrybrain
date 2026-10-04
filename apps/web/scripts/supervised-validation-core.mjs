import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

export const SCHEMA_VERSION = "berrybrain-human-supervised-validation.v2";
export const VALID_STATUSES = new Set(["passed", "failed", "blocked"]);

export const INTERACTION_REQUIREMENTS = Object.freeze({
  "SV-01": { minimumResponses: 1, minimumMutations: 1 },
  "SV-02": { minimumResponses: 4, minimumMutations: 4 },
  "SV-03": { minimumResponses: 2, minimumMutations: 1 },
  "SV-04": { minimumResponses: 1, minimumMutations: 1 },
  "SV-05": { minimumResponses: 1, minimumMutations: 1 },
  "SV-06": { minimumResponses: 0, minimumMutations: 0 },
  "SV-07": { minimumResponses: 2, minimumMutations: 2 },
  "SV-08": { minimumResponses: 2, minimumMutations: 2 },
  "SV-09": { minimumResponses: 4, minimumMutations: 4 },
  "SV-10": { minimumResponses: 1, minimumMutations: 1, allowServerError: true },
  "SV-11": { minimumResponses: 1, minimumMutations: 0 },
});

const booleanQuestion = (key, label, expected) => ({
  key,
  label,
  kind: "boolean",
  required: true,
  expected,
});

const textQuestion = (key, label) => ({
  key,
  label,
  kind: "text",
  required: true,
});

export const TEST_CASES = Object.freeze([
  {
    id: "SV-01",
    title: "Cloud-provider routing",
    mode: "browser",
    objective: "Verify that cloud mode uses the configured provider and completes model-backed work.",
    actions: [
      "Open Settings and select cloud mode with exactly one configured provider.",
      "Save the configuration without entering any key in this terminal.",
      "Trigger note processing and one grounded Ask request.",
      "Inspect Activity or Monitor and, when available, the backend evidence source.",
    ],
    passCriteria: [
      "The configured cloud provider handles the model requests.",
      "The cloud request completes through the configured provider.",
    ],
    questions: [
      textQuestion("requestReference", "Job, request, or timestamp reference"),
      booleanQuestion("cloudProviderConfigured", "Cloud mode was saved successfully", true),
      booleanQuestion("activityShowsCloudOnly", "Activity or Monitor shows only the cloud provider", true),
      booleanQuestion("cloudRequestCompleted", "The cloud-backed request completed", true),
    ],
  },
  {
    id: "SV-02",
    title: "Note lifecycle",
    mode: "browser",
    objective: "Verify create, edit, rename, and delete behavior against a real sanitized note.",
    actions: [
      "Create a note with sanitized, unique content.",
      "Edit its body and save it.",
      "Rename it and verify the vault entry.",
      "Delete it and confirm that it no longer appears in the vault.",
    ],
    passCriteria: ["Every lifecycle operation persists after navigation or refresh."],
    questions: [
      textQuestion("noteReference", "Sanitized note identifier or title"),
      booleanQuestion("created", "Create persisted", true),
      booleanQuestion("edited", "Edit persisted", true),
      booleanQuestion("renamed", "Rename persisted", true),
      booleanQuestion("deleted", "Delete persisted", true),
    ],
  },
  {
    id: "SV-03",
    title: "Processing visibility and graph arrival",
    mode: "browser",
    objective: "Verify progress, ETA, completion, and eventual graph visibility for a processed note.",
    actions: [
      "Create or update one sanitized note that requires graph processing.",
      "Observe the visible job state, progress, and ETA.",
      "Wait for completion and locate the note and derived artifacts in the graph.",
    ],
    passCriteria: [
      "Progress and an operational estimate remain visible while work is pending.",
      "The completed note appears in the graph without manual enrichment.",
    ],
    questions: [
      textQuestion("jobReference", "Job or note reference"),
      booleanQuestion("progressVisible", "Processing progress was visible", true),
      booleanQuestion("etaVisible", "An ETA or operational estimate was visible", true),
      booleanQuestion("graphAppeared", "The processed note appeared in the graph", true),
      { key: "elapsedSeconds", label: "Observed save-to-graph time in seconds", kind: "number", required: true, min: 0 },
    ],
  },
  {
    id: "SV-04",
    title: "Persistent node deletion",
    mode: "browser",
    objective: "Verify that a deleted graph node remains deleted after refresh.",
    actions: [
      "Open a disposable graph node and record its identifier.",
      "Delete the node and wait for the affected work to settle.",
      "Refresh the graph and search for the same identifier and label.",
    ],
    passCriteria: ["The node is absent immediately and remains absent after refresh."],
    questions: [
      textQuestion("nodeReference", "Deleted node identifier and label"),
      booleanQuestion("absentAfterDelete", "The node disappeared after deletion", true),
      booleanQuestion("absentAfterRefresh", "The node remained absent after refresh", true),
    ],
  },
  {
    id: "SV-05",
    title: "Scoped graph recomputation",
    mode: "browser",
    objective: "Verify that deletion or editing recomputes affected relationships without rebuilding unrelated graph regions.",
    actions: [
      "Record the affected cluster, direct neighbors, relationships, and related insights.",
      "Edit or delete the target artifact.",
      "Observe the visible working state and compare the affected and unrelated regions after completion.",
    ],
    passCriteria: [
      "The affected cluster and dependent artifacts are recomputed.",
      "Unrelated clusters retain stable identities and relationships.",
    ],
    questions: [
      textQuestion("clusterReference", "Affected cluster and target reference"),
      booleanQuestion("workingStateVisible", "A recalculation state was visible", true),
      booleanQuestion("affectedScopeRecomputed", "Affected relationships and insights were recomputed", true),
      booleanQuestion("unrelatedScopeStable", "Unrelated graph regions remained stable", true),
    ],
  },
  {
    id: "SV-06",
    title: "Node and edge semantic inspection",
    mode: "browser",
    objective: "Inspect graph naming, typing, context, predicates, direction, evidence, and derived confidence.",
    actions: [
      "Select nodes and edges across different clusters and ontology types.",
      "Check canonical naming, node type, context, predicate, direction, and cited evidence.",
      "Confirm that confidence is derived and cannot be edited directly.",
    ],
    passCriteria: ["Every sampled artifact is meaningful, evidence-backed, and ontology-valid."],
    questions: [
      { key: "sampledNodes", label: "Number of inspected nodes", kind: "integer", required: true, min: 5 },
      { key: "sampledEdges", label: "Number of inspected edges", kind: "integer", required: true, min: 5 },
      booleanQuestion("namesMeaningful", "Node names were meaningful and non-duplicated", true),
      booleanQuestion("typesValid", "Node types matched their semantics", true),
      booleanQuestion("contextsValid", "Cluster context was coherent", true),
      booleanQuestion("predicatesValid", "Edge predicates were meaningful", true),
      booleanQuestion("directionsValid", "Edge directions were correct", true),
      booleanQuestion("evidenceValid", "Relationships exposed supporting evidence", true),
      booleanQuestion("confidenceReadOnly", "Confidence was derived and read-only", true),
    ],
  },
  {
    id: "SV-07",
    title: "Unsupported-association rejection",
    mode: "browser",
    objective: "Verify that an isolated ambiguous term cannot connect contextually unrelated notes.",
    actions: [
      "Use two sanitized notes from unrelated domains that share one ambiguous fragment or isolated term.",
      "Process both notes and wait for graph and Judge work to settle.",
      "Search for a direct relationship, shared concept, or derived insight based only on that fragment.",
    ],
    passCriteria: ["No unsupported relationship or insight is admitted from the isolated fragment."],
    questions: [
      textQuestion("ambiguousTerm", "Ambiguous term or fragment used"),
      textQuestion("sourceA", "First sanitized source reference"),
      textQuestion("sourceB", "Second sanitized source reference"),
      booleanQuestion("unsupportedRelationshipCreated", "An unsupported relationship was created", false),
      booleanQuestion("unsupportedInsightCreated", "An unsupported insight was created", false),
      booleanQuestion("unsupportedAssociationPrevented", "The unsupported association was rejected or suppressed", true),
    ],
  },
  {
    id: "SV-08",
    title: "Feedback persistence and reuse",
    mode: "browser",
    objective: "Verify that rejection, editing, and deletion remain effective when similar content is processed again.",
    actions: [
      "Reject, edit, or delete one disposable generated artifact.",
      "Wait for the affected graph work to complete.",
      "Process new sanitized content containing the same problematic pattern.",
      "Verify policy reuse, scoped recomputation, and reversibility.",
    ],
    passCriteria: ["The prior decision is respected without suppressing unrelated valid content."],
    questions: [
      textQuestion("artifactReference", "Original artifact and action reference"),
      textQuestion("reprocessReference", "Reprocessed content or job reference"),
      booleanQuestion("decisionRespected", "The prior user decision was respected", true),
      booleanQuestion("rejectedArtifactRecurred", "The rejected artifact recurred unchanged", false),
      booleanQuestion("validContentSuppressed", "Unrelated valid content was suppressed", false),
      booleanQuestion("affectedScopeRecomputed", "The affected scope was recomputed", true),
    ],
  },
  {
    id: "SV-09",
    title: "Ask intent and grounding",
    mode: "browser",
    objective: "Verify factual, multi-hop, topology, and no-answer behavior with traceable evidence.",
    actions: [
      "Submit one factual question grounded in the sanitized vault.",
      "Submit one multi-hop question requiring at least two artifacts.",
      "Submit one question about graph structure or node types.",
      "Submit one question that the graph cannot answer.",
    ],
    passCriteria: [
      "Supported answers cite relevant graph evidence.",
      "The no-answer case does not fabricate an answer-like fallback.",
    ],
    questions: [
      textQuestion("queryReferences", "Redacted query identifiers or timestamps"),
      booleanQuestion("factualGrounded", "The factual answer was correct and grounded", true),
      booleanQuestion("multiHopGrounded", "The multi-hop answer used the required evidence", true),
      booleanQuestion("topologyGrounded", "The topology answer reflected the graph itself", true),
      booleanQuestion("noAnswerHandled", "The unsupported question returned a truthful no-answer state", true),
      booleanQuestion("citationsTraceable", "Answer citations resolved to the displayed evidence", true),
    ],
  },
  {
    id: "SV-10",
    title: "Provider-unavailable Ask behavior",
    mode: "browser",
    objective: "Verify that Ask exposes a recoverable error without generating an answer-like fallback when no provider is available.",
    actions: [
      "Disable or invalidate the active provider without deleting credentials from the test record.",
      "Submit a question that normally has graph evidence.",
      "Inspect the waiting or error state and the available recovery actions.",
      "Restore the provider after evidence capture.",
    ],
    passCriteria: ["Ask shows Retry and configuration recovery actions and does not fabricate an answer."],
    questions: [
      booleanQuestion("providerUnavailable", "The provider was unavailable for this request", true),
      booleanQuestion("errorStateVisible", "A waiting or error state was visible", true),
      booleanQuestion("retryVisible", "A Retry action was visible", true),
      booleanQuestion("configurationVisible", "A provider configuration action was visible", true),
      booleanQuestion("answerLikeFallbackVisible", "An answer-like fallback was displayed", false),
      booleanQuestion("providerRestored", "The provider was restored after capture", true),
    ],
  },
  {
    id: "SV-11",
    title: "Accessibility and constrained-client behavior",
    mode: "browser",
    objective: "Verify keyboard, 200% zoom, screen-reader, mobile, and throttled-network operation.",
    actions: [
      "Navigate the core flow with keyboard only and inspect visible focus.",
      "Repeat the core flow at 200% browser zoom.",
      "Inspect landmarks, names, state, and reading order with a screen reader.",
      "Repeat the relevant flow in the runner-provided mobile viewport.",
      "Repeat the relevant flow under the runner-provided network throttle.",
    ],
    passCriteria: ["Core commands remain reachable, readable, and understandable in every mode."],
    questions: [
      booleanQuestion("keyboardPassed", "Keyboard-only operation passed", true),
      booleanQuestion("zoomPassed", "The 200% zoom check passed", true),
      booleanQuestion("screenReaderPassed", "The screen-reader check passed", true),
      booleanQuestion("mobilePassed", "The mobile viewport check passed", true),
      booleanQuestion("slowNetworkPassed", "The throttled-network check passed", true),
      booleanQuestion("overlapOrClippingObserved", "Blocking overlap or clipping was observed", false),
    ],
  },
  {
    id: "SV-12",
    title: "Evidence-record integrity",
    mode: "report",
    objective: "Verify that every case has an explicit status, rationale, and checksummed evidence record.",
    actions: [
      "Review the generated draft report and every status.",
      "Confirm that attachments and screenshots contain sanitized data only.",
      "Confirm that no API key, token, password, or personal vault content is present.",
    ],
    passCriteria: ["The report is complete, internally consistent, sanitized, and checksummed."],
    questions: [
      booleanQuestion("allStatusesReviewed", "All case statuses and rationales were reviewed", true),
      booleanQuestion("evidenceReviewed", "All evidence files were reviewed", true),
      booleanQuestion("secretsAbsent", "The evidence contains no secrets or personal vault content", true),
    ],
  },
]);

export function sanitizeUrl(value) {
  try {
    const parsed = new URL(value);
    parsed.username = "";
    parsed.password = "";
    parsed.search = "";
    parsed.hash = "";
    return parsed.toString();
  } catch {
    return "[invalid-url]";
  }
}

export function redactText(value, maxLength = 500) {
  const redacted = String(value ?? "")
    .replace(/\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b/g, "[REDACTED_EMAIL]")
    .replace(/\b(?:sk|gsk|ghp|glpat|xox[baprs])[-_][A-Za-z0-9_-]{12,}\b/g, "[REDACTED_TOKEN]")
    .replace(/\bBearer\s+[A-Za-z0-9._~+/-]+=*/gi, "Bearer [REDACTED]")
    .replace(/\b(api[_ -]?key|authorization|bearer|password|secret|token)(\s*[:=]\s*)([^\s,;]+)/gi, "$1$2[REDACTED]");
  return redacted.length > maxLength ? `${redacted.slice(0, maxLength)}...[TRUNCATED]` : redacted;
}

export function summarizeBackendLog(text, provider = "", model = "") {
  const lines = String(text ?? "").split(/\r?\n/).filter(Boolean);
  const providerNeedle = provider.trim().toLowerCase();
  const modelNeedle = model.trim().toLowerCase();
  const providerLines = lines.filter((line) => {
    const normalized = line.toLowerCase();
    return (providerNeedle && normalized.includes(providerNeedle))
      || (modelNeedle && normalized.includes(modelNeedle));
  });
  return {
    scannedLineCount: lines.length,
    configuredProviderMentionCount: providerLines.length,
    providerSamples: providerLines.slice(0, 10).map((line) => redactText(line)),
  };
}

export function evaluateObservations(testCase, observations) {
  const failures = [];
  const gaps = [];

  for (const question of testCase.questions) {
    const value = observations[question.key];
    const missing = value === undefined || value === null || value === "";
    if (missing) {
      if (question.required) gaps.push(`${question.label}: no observation recorded`);
      continue;
    }
    if (Object.hasOwn(question, "expected") && value !== question.expected) {
      failures.push(`${question.label}: expected ${question.expected}, observed ${value}`);
    }
    if (typeof question.min === "number" && (!(typeof value === "number") || value < question.min)) {
      failures.push(`${question.label}: expected a value >= ${question.min}, observed ${value}`);
    }
  }

  return { failures, gaps };
}

export function deriveEffectiveStatus(operatorStatus, automatedChecks) {
  if (!VALID_STATUSES.has(operatorStatus)) throw new Error(`Invalid operator status: ${operatorStatus}`);
  if ((automatedChecks.failures?.length ?? 0) > 0) return "failed";
  if ((automatedChecks.gaps?.length ?? 0) > 0) return "blocked";
  return operatorStatus;
}

export function deriveOverallStatus(results) {
  const statuses = results.map((result) => result.effectiveStatus);
  if (statuses.includes("failed")) return "failed";
  if (statuses.includes("blocked") || results.length !== TEST_CASES.length) return "blocked";
  return "passed";
}

export function evidenceCompletenessChecks(results) {
  const operational = TEST_CASES.filter((testCase) => testCase.mode === "browser");
  const byId = new Map(results.map((result) => [result.id, result]));
  const failures = [];
  const gaps = [];

  for (const testCase of operational) {
    const result = byId.get(testCase.id);
    if (!result) {
      gaps.push(`${testCase.id}: no result`);
      continue;
    }
    if (!VALID_STATUSES.has(result.operatorStatus) || !VALID_STATUSES.has(result.effectiveStatus)) {
      failures.push(`${testCase.id}: invalid status`);
    }
    if (!String(result.rationale ?? "").trim()) gaps.push(`${testCase.id}: no rationale`);
    if ((result.evidence ?? []).length === 0) gaps.push(`${testCase.id}: no evidence file`);
  }
  const rationaleOwners = new Map();
  for (const result of results.filter((entry) => entry.id !== "SV-12")) {
    const normalized = String(result.rationale ?? "").trim().toLowerCase().replace(/\s+/g, " ");
    if (!normalized) continue;
    const owners = rationaleOwners.get(normalized) ?? [];
    owners.push(result.id);
    rationaleOwners.set(normalized, owners);
  }
  for (const owners of rationaleOwners.values()) {
    if (owners.length > 1) gaps.push(`Case-specific rationale required; identical text used by ${owners.join(", ")}`);
  }
  return { failures, gaps };
}

export function evaluateInteractionEvidence({
  testCase,
  actionDurationSeconds,
  evidence,
  networkEvents,
  minimumActionSeconds,
}) {
  const requirements = INTERACTION_REQUIREMENTS[testCase.id] ?? { minimumResponses: 0, minimumMutations: 0 };
  const failures = [];
  const gaps = [];
  const responses = networkEvents.filter((event) => event.kind === "response");
  const mutations = responses.filter((event) => ["POST", "PUT", "PATCH", "DELETE"].includes(event.method));
  const unauthorized = responses.filter((event) => [401, 403].includes(Number(event.status)));
  const serverErrors = responses.filter((event) => Number(event.status) >= 500);
  const requestFailures = networkEvents.filter((event) => event.kind === "failure");
  const uniqueImages = new Set((evidence ?? []).filter((entry) => entry.path.endsWith(".png")).map((entry) => entry.sha256));

  if (actionDurationSeconds < minimumActionSeconds) {
    gaps.push(`Action window was ${actionDurationSeconds}s; required minimum is ${minimumActionSeconds}s`);
  }
  if (uniqueImages.size < 2) gaps.push("Captured screenshots do not show a visual state change");
  if (responses.length < requirements.minimumResponses) {
    gaps.push(`Observed ${responses.length} responses; this case requires at least ${requirements.minimumResponses}`);
  }
  if (mutations.length < requirements.minimumMutations) {
    gaps.push(`Observed ${mutations.length} mutation responses; this case requires at least ${requirements.minimumMutations}`);
  }
  if (unauthorized.length > 0) failures.push(`Observed ${unauthorized.length} unauthorized response(s)`);
  if (!requirements.allowServerError && serverErrors.length > 0) failures.push(`Observed ${serverErrors.length} HTTP 5xx response(s)`);
  if (requestFailures.length > 0) gaps.push(`Observed ${requestFailures.length} failed browser request(s)`);

  return { failures, gaps };
}

export function summarizeTelemetry(networkEvents, consoleEvents, testId) {
  const network = networkEvents.filter((event) => event.testId === testId);
  const console = consoleEvents.filter((event) => event.testId === testId);
  return {
    requestCount: network.filter((event) => event.kind === "response").length,
    failedRequestCount: network.filter((event) => event.kind === "failure").length,
    serverErrorCount: network.filter((event) => Number(event.status) >= 500).length,
    browserWarningCount: console.filter((event) => event.level === "warning").length,
    browserErrorCount: console.filter((event) => event.level === "error" || event.level === "pageerror").length,
  };
}

function markdownValue(value) {
  if (value === null || value === undefined || value === "") return "not recorded";
  if (Array.isArray(value)) return value.map(markdownValue).join(", ");
  if (typeof value === "object") return `\`${redactText(JSON.stringify(value), 1_000).replace(/`/g, "'")}\``;
  return String(value).replace(/\|/g, "\\|").replace(/\r?\n/g, " ");
}

export function renderProtocolMarkdown() {
  const lines = ["# BerryBrain Human-Supervised Validation Protocol", ""];
  for (const testCase of TEST_CASES) {
    lines.push(`## ${testCase.id}: ${testCase.title}`, "", testCase.objective, "", "Actions:");
    testCase.actions.forEach((action, index) => lines.push(`${index + 1}. ${action}`));
    lines.push("", "Pass criteria:");
    testCase.passCriteria.forEach((criterion) => lines.push(`- ${criterion}`));
    lines.push("");
  }
  return `${lines.join("\n")}\n`;
}

export function renderReport(state) {
  const counts = { passed: 0, failed: 0, blocked: 0 };
  for (const result of state.results) counts[result.effectiveStatus] += 1;
  const lines = [
    "# BerryBrain Human-Supervised Validation Report",
    "",
    `Run ID: \`${state.runId}\`  `,
    `Schema: \`${state.schemaVersion}\`  `,
    `Started: \`${state.startedAt}\`  `,
    `Completed: \`${state.completedAt ?? "in progress"}\`  `,
    `Overall status: **${state.overallStatus}**`,
    "",
    "> Evidence classification: author-supervised acceptance validation. This report is not an independent, blinded, or participant-based evaluation.",
    "",
    "## Environment",
    "",
    `- Revision: \`${markdownValue(state.environment.revision)}\` (${state.environment.dirty ? "dirty" : "clean"} worktree)` ,
    `- Base URL: \`${markdownValue(state.environment.baseUrl)}\``,
    `- Operator pseudonym: \`${markdownValue(state.environment.operatorId)}\``,
    `- Corpus snapshot: \`${markdownValue(state.environment.corpusId)}\``,
    `- Cloud provider label: \`${markdownValue(state.environment.provider)}\``,
    `- Cloud model label: \`${markdownValue(state.environment.model)}\``,
    `- Backend evidence source: \`${markdownValue(state.environment.backendEvidenceSource)}\``,
    "",
    "## Summary",
    "",
    `- Passed: ${counts.passed}`,
    `- Failed: ${counts.failed}`,
    `- Blocked: ${counts.blocked}`,
    "",
    "| Case | Title | Operator | Effective | Duration |",
    "| --- | --- | --- | --- | ---: |",
  ];

  for (const result of state.results) {
    lines.push(`| ${result.id} | ${result.title} | ${result.operatorStatus} | ${result.effectiveStatus} | ${result.durationSeconds ?? 0}s |`);
  }

  lines.push("", "## Cases", "");
  for (const result of state.results) {
    lines.push(
      `### ${result.id}: ${result.title}`,
      "",
      `- Operator status: **${result.operatorStatus}**`,
      `- Effective status: **${result.effectiveStatus}**`,
      `- Started: \`${result.startedAt}\``,
      `- Completed: \`${result.completedAt}\``,
      `- Prospective action window: ${result.actionDurationSeconds ?? 0}s`,
      `- Rationale: ${markdownValue(result.rationale)}`,
      `- Network: ${result.telemetry.requestCount} responses, ${result.telemetry.failedRequestCount} failures, ${result.telemetry.serverErrorCount} HTTP 5xx`,
      `- Browser: ${result.telemetry.browserWarningCount} warnings, ${result.telemetry.browserErrorCount} errors`,
      `- Backend log: ${result.backendEvidence.configuredProviderMentionCount} configured-provider or model mentions`,
      "",
      "Observations:",
    );
    const testCase = TEST_CASES.find((entry) => entry.id === result.id);
    for (const question of testCase?.questions ?? []) {
      lines.push(`- ${question.label}: ${markdownValue(result.observations[question.key])}`);
    }
    lines.push("", "Automated checks:");
    if (result.automatedChecks.failures.length === 0 && result.automatedChecks.gaps.length === 0) {
      lines.push("- No contradiction or required-evidence gap detected.");
    } else {
      result.automatedChecks.failures.forEach((failure) => lines.push(`- Failure: ${markdownValue(failure)}`));
      result.automatedChecks.gaps.forEach((gap) => lines.push(`- Gap: ${markdownValue(gap)}`));
    }
    lines.push("", "Evidence:");
    if ((result.evidence ?? []).length === 0) lines.push("- No evidence file recorded.");
    for (const evidence of result.evidence ?? []) {
      lines.push(`- \`${evidence.path}\` (${evidence.bytes} bytes; SHA-256 \`${evidence.sha256}\`)`);
    }
    lines.push("");
  }

  lines.push(
    "## Interpretation Boundary",
    "",
    "A passed run supports the listed acceptance behaviors on this revision, environment, corpus, and operator session. It does not establish comparative superiority, population usability, Judge accuracy against independent humans, calibrated factual confidence, or longitudinal learning effectiveness.",
    "",
  );
  return lines.join("\n");
}

export async function sha256File(filePath) {
  return createHash("sha256").update(await readFile(filePath)).digest("hex");
}

async function walkFiles(root, current = root) {
  const entries = await readdir(current, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const absolute = path.join(current, entry.name);
    if (entry.isDirectory()) files.push(...await walkFiles(root, absolute));
    else if (entry.isFile()) files.push(path.relative(root, absolute).split(path.sep).join("/"));
  }
  return files;
}

export async function buildManifest(runDirectory, excluded = new Set(["manifest.json", "checksums.sha256"])) {
  const files = (await walkFiles(runDirectory)).filter((relative) => !excluded.has(relative)).sort();
  const records = [];
  for (const relative of files) {
    const absolute = path.join(runDirectory, relative);
    const metadata = await stat(absolute);
    records.push({ path: relative, bytes: metadata.size, sha256: await sha256File(absolute) });
  }
  return { schemaVersion: `${SCHEMA_VERSION}.manifest`, generatedAt: new Date().toISOString(), files: records };
}
