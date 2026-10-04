import assert from "node:assert/strict";
import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  TEST_CASES,
  buildManifest,
  deriveEffectiveStatus,
  deriveOverallStatus,
  evidenceCompletenessChecks,
  evaluateInteractionEvidence,
  evaluateObservations,
  redactText,
  renderReport,
  sanitizeUrl,
  summarizeBackendLog,
} from "./supervised-validation-core.mjs";

test("the protocol contains exactly twelve unique, ordered cases", () => {
  assert.equal(TEST_CASES.length, 12);
  assert.deepEqual(TEST_CASES.map((entry) => entry.id), Array.from({ length: 12 }, (_, index) => `SV-${String(index + 1).padStart(2, "0")}`));
  assert.equal(new Set(TEST_CASES.map((entry) => entry.id)).size, 12);
  assert.equal(TEST_CASES.filter((entry) => entry.mode === "browser").length, 11);
  assert.equal(TEST_CASES.at(-1).mode, "report");
});

test("URLs and diagnostic text are sanitized before persistence", () => {
  assert.equal(sanitizeUrl("https://user:pass@example.test/api/jobs?token=secret#result"), "https://example.test/api/jobs");
  const redacted = redactText("Authorization: Bearer abc.def.ghi email=user@example.test api_key=sk-1234567890123456"); // gitleaks:allow -- deliberate redaction fixture, not a credential
  assert.doesNotMatch(redacted, /abc\.def|user@example|sk-123/);
  assert.match(redacted, /REDACTED/);
});

test("backend summaries retain only configured cloud-provider evidence", () => {
  const summary = summarizeBackendLog(
    "Provider=openai model=gpt-test request completed\nUnrelated worker line\n",
    "openai",
    "gpt-test",
  );
  assert.equal(summary.scannedLineCount, 2);
  assert.equal(summary.configuredProviderMentionCount, 1);
  assert.equal(summary.providerSamples.length, 1);
  assert.deepEqual(Object.keys(summary).sort(), ["configuredProviderMentionCount", "providerSamples", "scannedLineCount"]);
});

test("contradictory observations force failure and missing evidence blocks a pass", () => {
  const lifecycle = TEST_CASES.find((entry) => entry.id === "SV-02");
  const valid = {
    noteReference: "sanitized-note-01",
    created: true,
    edited: true,
    renamed: true,
    deleted: true,
  };
  const validChecks = evaluateObservations(lifecycle, valid);
  assert.deepEqual(validChecks, { failures: [], gaps: [] });
  assert.equal(deriveEffectiveStatus("passed", validChecks), "passed");

  const contradiction = evaluateObservations(lifecycle, { ...valid, deleted: false });
  assert.equal(deriveEffectiveStatus("passed", contradiction), "failed");

  const missing = evaluateObservations(lifecycle, { ...valid, noteReference: null });
  assert.equal(deriveEffectiveStatus("passed", missing), "blocked");
});

test("evidence completeness requires all operational cases, rationale, and files", () => {
  const results = TEST_CASES.filter((entry) => entry.mode === "browser").map((entry) => ({
    id: entry.id,
    operatorStatus: "passed",
    effectiveStatus: "passed",
    rationale: `Observed ${entry.id} in the sanitized run.`,
    evidence: [{ path: `${entry.id}/after.png` }],
  }));
  assert.deepEqual(evidenceCompletenessChecks(results), { failures: [], gaps: [] });
  results[0].evidence = [];
  assert.match(evidenceCompletenessChecks(results).gaps[0], /SV-01/);
});

test("prospective interaction evidence rejects implausible or unauthenticated action windows", () => {
  const lifecycle = TEST_CASES.find((entry) => entry.id === "SV-02");
  const valid = evaluateInteractionEvidence({
    testCase: lifecycle,
    actionDurationSeconds: 30,
    minimumActionSeconds: 10,
    evidence: [
      { path: "before.png", sha256: "a".repeat(64) },
      { path: "after.png", sha256: "b".repeat(64) },
    ],
    networkEvents: ["POST", "PATCH", "PUT", "DELETE"].map((method) => ({ kind: "response", method, status: 200 })),
  });
  assert.deepEqual(valid, { failures: [], gaps: [] });

  const invalid = evaluateInteractionEvidence({
    testCase: lifecycle,
    actionDurationSeconds: 1,
    minimumActionSeconds: 10,
    evidence: [
      { path: "before.png", sha256: "a".repeat(64) },
      { path: "after.png", sha256: "a".repeat(64) },
    ],
    networkEvents: [{ kind: "response", method: "GET", status: 401 }],
  });
  assert.ok(invalid.failures.some((message) => /unauthorized/.test(message)));
  assert.ok(invalid.gaps.some((message) => /Action window/.test(message)));
  assert.ok(invalid.gaps.some((message) => /visual state change/.test(message)));
  assert.ok(invalid.gaps.some((message) => /mutation responses/.test(message)));
});

test("overall status never passes an incomplete, failed, or blocked run", () => {
  const complete = TEST_CASES.map((entry) => ({ id: entry.id, effectiveStatus: "passed" }));
  assert.equal(deriveOverallStatus(complete), "passed");
  assert.equal(deriveOverallStatus(complete.slice(0, 11)), "blocked");
  assert.equal(deriveOverallStatus(complete.map((entry, index) => index === 3 ? { ...entry, effectiveStatus: "failed" } : entry)), "failed");
});

test("the report states the evidence boundary and preserves explicit statuses", () => {
  const testCase = TEST_CASES[0];
  const state = {
    runId: "run-01",
    schemaVersion: "test-schema",
    startedAt: "2026-08-27T00:00:00Z",
    completedAt: "2026-08-27T00:10:00Z",
    overallStatus: "passed",
    environment: {
      revision: "abcdef0",
      dirty: false,
      baseUrl: "https://example.test/berrybrain",
      operatorId: "operator-01",
      corpusId: "corpus-01",
      provider: "cloud-provider",
      model: "cloud-model",
      backendEvidenceSource: "not supplied; operator attestation only",
    },
    results: [{
      id: testCase.id,
      title: testCase.title,
      operatorStatus: "passed",
      effectiveStatus: "passed",
      startedAt: "2026-08-27T00:00:00Z",
      completedAt: "2026-08-27T00:01:00Z",
      durationSeconds: 60,
      rationale: "Observed directly.",
      observations: Object.fromEntries(testCase.questions.map((question) => [question.key, question.expected ?? "reference"])),
      telemetry: { requestCount: 1, failedRequestCount: 0, serverErrorCount: 0, browserWarningCount: 0, browserErrorCount: 0 },
      backendEvidence: { configuredProviderMentionCount: 0 },
      automatedChecks: { failures: [], gaps: [] },
      evidence: [{ path: "evidence/SV-01/after.png", bytes: 10, sha256: "a".repeat(64) }],
    }],
  };
  const report = renderReport(state);
  assert.match(report, /author-supervised acceptance validation/i);
  assert.match(report, /not an independent, blinded, or participant-based evaluation/i);
  assert.match(report, /Operator status: \*\*passed\*\*/);
});

test("the evidence manifest hashes files and excludes its own circular records", async () => {
  const directory = await mkdtemp(path.join(os.tmpdir(), "berrybrain-supervised-test-"));
  try {
    await mkdir(path.join(directory, "evidence"));
    await writeFile(path.join(directory, "results.json"), "{}\n");
    await writeFile(path.join(directory, "evidence", "capture.txt"), "real evidence\n");
    await writeFile(path.join(directory, "manifest.json"), "stale\n");
    await writeFile(path.join(directory, "checksums.sha256"), "stale\n");
    const manifest = await buildManifest(directory);
    assert.deepEqual(manifest.files.map((entry) => entry.path), ["evidence/capture.txt", "results.json"]);
    assert.ok(manifest.files.every((entry) => /^[a-f0-9]{64}$/.test(entry.sha256)));
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
