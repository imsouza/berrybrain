#!/usr/bin/env node

import { randomBytes } from "node:crypto";
import { copyFile, mkdir, open, readFile, realpath, stat, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { createInterface } from "node:readline/promises";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { stdin as input, stdout as output } from "node:process";
import { chromium } from "@playwright/test";
import {
  SCHEMA_VERSION,
  TEST_CASES,
  buildManifest,
  deriveEffectiveStatus,
  deriveOverallStatus,
  evidenceCompletenessChecks,
  evaluateInteractionEvidence,
  evaluateObservations,
  redactText,
  renderProtocolMarkdown,
  renderReport,
  sanitizeUrl,
  sha256File,
  summarizeBackendLog,
  summarizeTelemetry,
} from "./supervised-validation-core.mjs";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const repositoryRoot = path.resolve(scriptDirectory, "../../..");
const defaultReportsRoot = path.join(repositoryRoot, "reports/evaluation/human-supervised");
const MAX_LOG_SEGMENT_BYTES = 8 * 1024 * 1024;

function usage() {
  return `BerryBrain human-supervised validation

Usage:
  npm run validate:supervised -- [options]

Options:
  --base-url <url>             BerryBrain URL (default: http://localhost:3000/berrybrain)
  --provider <label>           Active cloud provider label; never provide a key
  --model <label>              Active cloud model label
  --operator-id <id>           Pseudonymous operator identifier
  --corpus-id <id>             Sanitized corpus snapshot identifier
  --backend-log <path>         Optional API/Worker log file for provider-route evidence
  --docker-container <name>    Optional container read through docker logs
  --output-dir <path>          New run directory
  --resume <run-directory>     Resume an interrupted run
  --browser-executable <path>  Chromium executable override
  --ignore-https-errors        Allow a self-signed test endpoint
  --headless                   Run without a visible browser (not valid for human supervision)
  --no-archive                 Do not create the final .tar.gz bundle
  --mobile-width <px>          Mobile evidence width (default: 390)
  --mobile-height <px>         Mobile evidence height (default: 844)
  --latency-ms <ms>            Throttled profile latency (default: 300)
  --download-kbps <kbps>       Throttled download rate (default: 1500)
  --upload-kbps <kbps>         Throttled upload rate (default: 750)
  --minimum-action-seconds <s> Minimum prospective action window (default: 10)
  --protocol-only              Print the protocol without creating a run
  --help                       Show this help

The runner never asks for or records an API key. Use only sanitized test content.
`;
}

function parseArguments(argv) {
  const options = {
    baseUrl: process.env.SUPERVISED_BASE_URL ?? null,
    provider: null,
    model: null,
    operatorId: null,
    corpusId: null,
    backendLog: null,
    dockerContainer: null,
    outputDirectory: null,
    resumeDirectory: null,
    browserExecutable: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH ?? null,
    ignoreHTTPSErrors: false,
    headless: false,
    archive: true,
    protocolOnly: false,
    help: false,
    mobileWidth: 390,
    mobileHeight: 844,
    latencyMs: 300,
    downloadKbps: 1500,
    uploadKbps: 750,
    minimumActionSeconds: 10,
  };
  const valueOptions = new Map([
    ["--base-url", "baseUrl"],
    ["--provider", "provider"],
    ["--model", "model"],
    ["--operator-id", "operatorId"],
    ["--corpus-id", "corpusId"],
    ["--backend-log", "backendLog"],
    ["--docker-container", "dockerContainer"],
    ["--output-dir", "outputDirectory"],
    ["--resume", "resumeDirectory"],
    ["--browser-executable", "browserExecutable"],
    ["--mobile-width", "mobileWidth"],
    ["--mobile-height", "mobileHeight"],
    ["--latency-ms", "latencyMs"],
    ["--download-kbps", "downloadKbps"],
    ["--upload-kbps", "uploadKbps"],
    ["--minimum-action-seconds", "minimumActionSeconds"],
  ]);
  const numericKeys = new Set(["mobileWidth", "mobileHeight", "latencyMs", "downloadKbps", "uploadKbps", "minimumActionSeconds"]);

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (argument === "--help") options.help = true;
    else if (argument === "--protocol-only") options.protocolOnly = true;
    else if (argument === "--ignore-https-errors") options.ignoreHTTPSErrors = true;
    else if (argument === "--headless") options.headless = true;
    else if (argument === "--no-archive") options.archive = false;
    else if (valueOptions.has(argument)) {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`${argument} requires a value`);
      const key = valueOptions.get(argument);
      options[key] = numericKeys.has(key) ? Number(value) : value;
      index += 1;
    } else {
      throw new Error(`Unknown option: ${argument}`);
    }
  }

  if (options.backendLog && options.dockerContainer) {
    throw new Error("Use either --backend-log or --docker-container, not both");
  }
  if (options.dockerContainer && !/^[A-Za-z0-9_.-]+$/.test(options.dockerContainer)) {
    throw new Error("--docker-container contains unsupported characters");
  }
  for (const key of numericKeys) {
    if (!Number.isFinite(options[key]) || options[key] <= 0) throw new Error(`Invalid numeric option: ${key}`);
  }
  return options;
}

function commandOutput(command, args) {
  const result = spawnSync(command, args, { cwd: repositoryRoot, encoding: "utf8", maxBuffer: 2 * 1024 * 1024 });
  return result.status === 0 ? result.stdout.trim() : null;
}

function createRunId() {
  const timestamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z");
  return `${timestamp}-${randomBytes(5).toString("hex")}`;
}

async function askRequired(readline, label, defaultValue = "") {
  while (true) {
    const suffix = defaultValue ? ` [${defaultValue}]` : "";
    const answer = (await readline.question(`${label}${suffix}: `)).trim();
    const value = answer || defaultValue;
    if (value) return value;
    output.write("A value is required.\n");
  }
}

async function askBoolean(readline, label) {
  while (true) {
    const answer = (await readline.question(`${label} [y/n/u]: `)).trim().toLowerCase();
    if (["y", "yes"].includes(answer)) return true;
    if (["n", "no"].includes(answer)) return false;
    if (["u", "unknown"].includes(answer)) return null;
    output.write("Enter y, n, or u for unknown.\n");
  }
}

async function askNumber(readline, question) {
  while (true) {
    const answer = (await readline.question(`${question.label}: `)).trim();
    if (!answer) return null;
    const value = question.kind === "integer" ? Number.parseInt(answer, 10) : Number(answer);
    if (Number.isFinite(value) && (question.kind !== "integer" || Number.isInteger(value))) return value;
    output.write("Enter a valid number or leave blank for an evidence gap.\n");
  }
}

async function askStatus(readline) {
  while (true) {
    const answer = (await readline.question("Operator status [passed/failed/blocked]: ")).trim().toLowerCase();
    if (["passed", "failed", "blocked"].includes(answer)) return answer;
    output.write("Enter passed, failed, or blocked.\n");
  }
}

async function collectObservations(readline, testCase) {
  output.write("\nStructured observations\n");
  const observations = {};
  for (const question of testCase.questions) {
    if (question.kind === "boolean") observations[question.key] = await askBoolean(readline, question.label);
    else if (question.kind === "number" || question.kind === "integer") observations[question.key] = await askNumber(readline, question);
    else observations[question.key] = (await readline.question(`${question.label}: `)).trim() || null;
  }
  return observations;
}

async function authenticatedSessionStatus(page) {
  try {
    return await page.evaluate(async () => {
      const response = await fetch(new URL("/api/v1/auth/me", window.location.origin), {
        credentials: "include",
        cache: "no-store",
      });
      return response.status;
    });
  } catch {
    return null;
  }
}

function displayCase(testCase) {
  output.write(`\n${"=".repeat(72)}\n${testCase.id}: ${testCase.title}\n${testCase.objective}\n\nActions:\n`);
  testCase.actions.forEach((action, index) => output.write(`  ${index + 1}. ${action}\n`));
  output.write("\nPass criteria:\n");
  testCase.passCriteria.forEach((criterion) => output.write(`  - ${criterion}\n`));
}

async function evidenceRecord(runDirectory, absolutePath) {
  const metadata = await stat(absolutePath);
  return {
    path: path.relative(runDirectory, absolutePath).split(path.sep).join("/"),
    bytes: metadata.size,
    sha256: await sha256File(absolutePath),
  };
}

function safeFileName(value) {
  const normalized = path.basename(value).replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return normalized || "evidence.bin";
}

async function captureScreenshot(page, runDirectory, testId, label) {
  const directory = path.join(runDirectory, "evidence", testId);
  await mkdir(directory, { recursive: true });
  const absolute = path.join(directory, `${label}.png`);
  try {
    await page.screenshot({ path: absolute, fullPage: false, animations: "disabled" });
    return { record: await evidenceRecord(runDirectory, absolute), error: null };
  } catch (error) {
    return { record: null, error: redactText(error.message) };
  }
}

async function collectAttachments(readline, runDirectory, testId) {
  const records = [];
  let index = 1;
  while (true) {
    const answer = (await readline.question("Additional evidence file path (blank to finish): ")).trim();
    if (!answer) break;
    try {
      const source = await realpath(answer);
      const metadata = await stat(source);
      if (!metadata.isFile()) throw new Error("Only regular files can be attached");
      if (metadata.size > 50 * 1024 * 1024) throw new Error("Attachment exceeds the 50 MiB safety limit");
      const destinationDirectory = path.join(runDirectory, "evidence", testId, "attachments");
      await mkdir(destinationDirectory, { recursive: true });
      const destination = path.join(destinationDirectory, `${String(index).padStart(2, "0")}-${safeFileName(source)}`);
      await copyFile(source, destination);
      records.push(await evidenceRecord(runDirectory, destination));
      index += 1;
    } catch (error) {
      output.write(`Attachment rejected: ${redactText(error.message)}\n`);
    }
  }
  return records;
}

async function createBackendCheckpoint(options) {
  if (options.backendLog) {
    try {
      const metadata = await stat(options.backendLog);
      return { kind: "file", offset: metadata.size };
    } catch (error) {
      return { kind: "file", offset: 0, checkpointError: redactText(error.message) };
    }
  }
  if (options.dockerContainer) return { kind: "docker", since: new Date().toISOString() };
  return { kind: "none" };
}

async function readFileSegment(filePath, offset) {
  const metadata = await stat(filePath);
  const rotated = metadata.size < offset;
  const effectiveOffset = rotated ? 0 : offset;
  const available = metadata.size - effectiveOffset;
  const bytesToRead = Math.min(available, MAX_LOG_SEGMENT_BYTES);
  const start = metadata.size - bytesToRead;
  const handle = await open(filePath, "r");
  try {
    const buffer = Buffer.alloc(bytesToRead);
    if (bytesToRead > 0) await handle.read(buffer, 0, bytesToRead, start);
    return { text: buffer.toString("utf8"), truncated: available > bytesToRead, rotated };
  } finally {
    await handle.close();
  }
}

async function collectBackendEvidence(options, checkpoint, provider, model) {
  const empty = {
    sourceAvailable: false,
    sourceKind: checkpoint.kind,
    scannedLineCount: 0,
    configuredProviderMentionCount: 0,
    providerSamples: [],
    truncated: false,
    rotated: false,
    error: checkpoint.checkpointError ?? null,
  };
  if (checkpoint.kind === "none") return empty;
  try {
    let text;
    let truncated = false;
    let rotated = false;
    if (checkpoint.kind === "file") {
      const segment = await readFileSegment(options.backendLog, checkpoint.offset);
      ({ text, truncated, rotated } = segment);
    } else {
      const result = spawnSync(
        "docker",
        ["logs", "--since", checkpoint.since, "--timestamps", options.dockerContainer],
        { encoding: "utf8", maxBuffer: MAX_LOG_SEGMENT_BYTES },
      );
      if (result.error) throw result.error;
      if (result.status !== 0) throw new Error(result.stderr || `docker logs exited with ${result.status}`);
      text = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
    }
    return {
      sourceAvailable: true,
      sourceKind: checkpoint.kind,
      ...summarizeBackendLog(text, provider, model),
      truncated,
      rotated,
      error: null,
    };
  } catch (error) {
    return { ...empty, error: redactText(error.message) };
  }
}

async function captureConstrainedProfiles(page, context, readline, runDirectory, testId, options) {
  const evidence = [];
  const warnings = [];
  const desktopViewport = page.viewportSize() ?? { width: 1440, height: 1000 };

  try {
    await page.setViewportSize({ width: options.mobileWidth, height: options.mobileHeight });
    await readline.question(`Mobile viewport ${options.mobileWidth}x${options.mobileHeight} is active. Exercise the relevant flow, then press Enter: `);
    const mobile = await captureScreenshot(page, runDirectory, testId, "mobile");
    if (mobile.record) evidence.push(mobile.record);
    if (mobile.error) warnings.push(`Mobile screenshot: ${mobile.error}`);
  } catch (error) {
    warnings.push(`Mobile profile: ${redactText(error.message)}`);
  } finally {
    await page.setViewportSize(desktopViewport).catch(() => {});
  }

  let cdp;
  try {
    cdp = await context.newCDPSession(page);
    await cdp.send("Network.enable");
    await cdp.send("Network.emulateNetworkConditions", {
      offline: false,
      latency: options.latencyMs,
      downloadThroughput: options.downloadKbps * 1024 / 8,
      uploadThroughput: options.uploadKbps * 1024 / 8,
      connectionType: "cellular3g",
    });
    await readline.question(`Network profile ${options.latencyMs} ms/${options.downloadKbps} kbps is active. Exercise the relevant flow, then press Enter: `);
    const throttled = await captureScreenshot(page, runDirectory, testId, "throttled-network");
    if (throttled.record) evidence.push(throttled.record);
    if (throttled.error) warnings.push(`Throttled screenshot: ${throttled.error}`);
  } catch (error) {
    warnings.push(`Network profile: ${redactText(error.message)}`);
  } finally {
    if (cdp) {
      await cdp.send("Network.emulateNetworkConditions", {
        offline: false,
        latency: 0,
        downloadThroughput: -1,
        uploadThroughput: -1,
        connectionType: "none",
      }).catch(() => {});
      await cdp.detach().catch(() => {});
    }
  }
  return { evidence, warnings };
}

async function writeSession(runDirectory, state, networkEvents, consoleEvents) {
  state.overallStatus = deriveOverallStatus(state.results);
  await writeFile(path.join(runDirectory, "results.json"), `${JSON.stringify(state, null, 2)}\n`, "utf8");
  await writeFile(path.join(runDirectory, "network-events.json"), `${JSON.stringify(networkEvents, null, 2)}\n`, "utf8");
  await writeFile(path.join(runDirectory, "browser-events.json"), `${JSON.stringify(consoleEvents, null, 2)}\n`, "utf8");
  await writeFile(path.join(runDirectory, "report.md"), `${renderReport(state)}\n`, "utf8");
}

async function finalizeBundle(runDirectory, state, networkEvents, consoleEvents, createArchive) {
  state.completedAt = new Date().toISOString();
  await writeSession(runDirectory, state, networkEvents, consoleEvents);
  const manifest = await buildManifest(runDirectory);
  await writeFile(path.join(runDirectory, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  const checksumFiles = [...manifest.files, {
    path: "manifest.json",
    sha256: await sha256File(path.join(runDirectory, "manifest.json")),
  }].sort((left, right) => left.path.localeCompare(right.path));
  await writeFile(
    path.join(runDirectory, "checksums.sha256"),
    `${checksumFiles.map((entry) => `${entry.sha256}  ${entry.path}`).join("\n")}\n`,
    "utf8",
  );

  let archive = null;
  if (createArchive) {
    const archivePath = `${runDirectory}.tar.gz`;
    const result = spawnSync("tar", ["-czf", archivePath, "-C", path.dirname(runDirectory), path.basename(runDirectory)], {
      encoding: "utf8",
      maxBuffer: 2 * 1024 * 1024,
    });
    if (result.status === 0) archive = { path: archivePath, sha256: await sha256File(archivePath) };
    else output.write(`Archive creation failed: ${redactText(result.stderr || result.error?.message)}\n`);
  }
  return { manifest, archive };
}

async function loadOrCreateState(options, readline) {
  if (options.resumeDirectory) {
    const runDirectory = path.resolve(options.resumeDirectory);
    const state = JSON.parse(await readFile(path.join(runDirectory, "results.json"), "utf8"));
    if (state.schemaVersion !== SCHEMA_VERSION) throw new Error(`Unsupported resume schema: ${state.schemaVersion}`);
    state.results = state.results.filter((result) => result.id !== "SV-12");
    state.completedAt = null;
    options.baseUrl ||= state.environment.baseUrl;
    options.provider ||= state.environment.provider;
    options.model ||= state.environment.model;
    return { runDirectory, state };
  }

  output.write("\nThis runner records screenshots and copied attachments. Use a sanitized test vault only.\n");
  output.write("Never enter API keys, passwords, personal notes, or participant identifiers.\n");
  const confirmation = await askRequired(readline, "Type SANITIZED to confirm");
  if (confirmation !== "SANITIZED") throw new Error("Sanitized-data confirmation was not provided");

  options.baseUrl ||= "http://localhost:3000/berrybrain";
  const parsedBaseUrl = new URL(options.baseUrl);
  if (!["http:", "https:"].includes(parsedBaseUrl.protocol) || parsedBaseUrl.username || parsedBaseUrl.password) {
    throw new Error("--base-url must be an HTTP(S) URL without embedded credentials");
  }
  options.operatorId ||= await askRequired(readline, "Operator pseudonym");
  options.corpusId ||= await askRequired(readline, "Sanitized corpus snapshot identifier");
  options.provider ||= await askRequired(readline, "Configured cloud provider label");
  options.model ||= await askRequired(readline, "Configured cloud model label");

  const runId = createRunId();
  const runDirectory = path.resolve(options.outputDirectory ?? path.join(defaultReportsRoot, runId));
  await mkdir(path.dirname(runDirectory), { recursive: true });
  await mkdir(runDirectory, { recursive: false });
  const revision = commandOutput("git", ["rev-parse", "--short", "HEAD"]) ?? "unknown";
  const dirty = Boolean(commandOutput("git", ["status", "--porcelain"]));
  const backendEvidenceSource = options.backendLog
    ? `file:${path.basename(options.backendLog)}`
    : options.dockerContainer
      ? `docker:${options.dockerContainer}`
      : "not supplied; operator attestation only";
  const state = {
    schemaVersion: SCHEMA_VERSION,
    runId,
    startedAt: new Date().toISOString(),
    completedAt: null,
    overallStatus: "blocked",
    evidenceClassification: "author-supervised acceptance validation",
    environment: {
      revision,
      dirty,
      baseUrl: sanitizeUrl(options.baseUrl),
      operatorId: options.operatorId,
      corpusId: options.corpusId,
      provider: options.provider,
      model: options.model,
      backendEvidenceSource,
      platform: `${os.platform()} ${os.release()} ${os.arch()}`,
      node: process.version,
      mobileProfile: { width: options.mobileWidth, height: options.mobileHeight },
      networkProfile: {
        latencyMs: options.latencyMs,
        downloadKbps: options.downloadKbps,
        uploadKbps: options.uploadKbps,
      },
      minimumActionSeconds: options.minimumActionSeconds,
    },
    setupNavigationError: null,
    results: [],
  };
  return { runDirectory, state };
}

async function run() {
  const options = parseArguments(process.argv.slice(2));
  if (options.help) {
    output.write(usage());
    return;
  }
  if (options.protocolOnly) {
    output.write(renderProtocolMarkdown());
    return;
  }
  if (!input.isTTY || !output.isTTY) throw new Error("Interactive validation requires a TTY");
  if (options.headless) output.write("Warning: headless mode cannot support valid human visual supervision.\n");

  const readline = createInterface({ input, output });
  let browser;
  let context;
  let state;
  let runDirectory;
  let networkEvents = [];
  let consoleEvents = [];
  let activeTestId = "setup";
  const requestStarts = new WeakMap();

  try {
    ({ runDirectory, state } = await loadOrCreateState(options, readline));
    if (options.resumeDirectory) {
      networkEvents = JSON.parse(await readFile(path.join(runDirectory, "network-events.json"), "utf8").catch(() => "[]"));
      consoleEvents = JSON.parse(await readFile(path.join(runDirectory, "browser-events.json"), "utf8").catch(() => "[]"));
    }
    await writeSession(runDirectory, state, networkEvents, consoleEvents);

    browser = await chromium.launch({
      headless: options.headless,
      executablePath: options.browserExecutable ?? undefined,
    });
    context = await browser.newContext({
      ignoreHTTPSErrors: options.ignoreHTTPSErrors,
      viewport: { width: 1440, height: 1000 },
    });
    const page = await context.newPage();

    page.on("request", (request) => requestStarts.set(request, Date.now()));
    page.on("response", (response) => {
      const request = response.request();
      networkEvents.push({
        kind: "response",
        testId: activeTestId,
        at: new Date().toISOString(),
        method: request.method(),
        url: sanitizeUrl(request.url()),
        resourceType: request.resourceType(),
        status: response.status(),
        durationMs: Math.max(0, Date.now() - (requestStarts.get(request) ?? Date.now())),
      });
    });
    page.on("requestfailed", (request) => {
      networkEvents.push({
        kind: "failure",
        testId: activeTestId,
        at: new Date().toISOString(),
        method: request.method(),
        url: sanitizeUrl(request.url()),
        resourceType: request.resourceType(),
        error: redactText(request.failure()?.errorText ?? "request failed"),
      });
    });
    page.on("console", (message) => {
      if (!["warning", "error"].includes(message.type())) return;
      consoleEvents.push({
        testId: activeTestId,
        at: new Date().toISOString(),
        level: message.type(),
        message: redactText(message.text()),
      });
    });
    page.on("pageerror", (error) => {
      consoleEvents.push({ testId: activeTestId, at: new Date().toISOString(), level: "pageerror", message: redactText(error.message) });
    });

    try {
      await page.goto(options.baseUrl, { waitUntil: "domcontentloaded", timeout: 60_000 });
    } catch (error) {
      state.setupNavigationError = redactText(error.message);
      output.write(`Initial navigation did not complete: ${state.setupNavigationError}\n`);
    }
    while (true) {
      const answer = await readline.question("Log in and prepare the sanitized test vault, then press Enter to verify authentication or type ABORT: ");
      if (answer.trim().toUpperCase() === "ABORT") throw new Error("Operator aborted before authentication");
      const authStatus = await authenticatedSessionStatus(page);
      if (authStatus === 200) break;
      output.write(`Authentication check failed (${authStatus ?? "unreachable"}). The operational cases cannot start yet.\n`);
    }

    const completedIds = new Set(state.results.map((result) => result.id));
    for (const testCase of TEST_CASES.filter((entry) => entry.mode === "browser")) {
      if (completedIds.has(testCase.id)) continue;
      displayCase(testCase);
      await readline.question("Navigate to the relevant starting state, then press Enter to begin evidence capture: ");
      activeTestId = testCase.id;
      const startedAt = new Date().toISOString();
      const startedMs = Date.now();
      const actionNetworkStart = networkEvents.length;
      const checkpoint = await createBackendCheckpoint(options);
      const evidence = [];
      const evidenceWarnings = [];

      const before = await captureScreenshot(page, runDirectory, testCase.id, "before");
      if (before.record) evidence.push(before.record);
      if (before.error) evidenceWarnings.push(`Before screenshot: ${before.error}`);

      await readline.question("Perform the listed actions in the browser. Press Enter only after the observable state has settled: ");
      const after = await captureScreenshot(page, runDirectory, testCase.id, "after");
      if (after.record) evidence.push(after.record);
      if (after.error) evidenceWarnings.push(`After screenshot: ${after.error}`);

      if (testCase.id === "SV-11") {
        output.write("Restore browser zoom to 100% before the automated mobile and network profiles.\n");
        const constrained = await captureConstrainedProfiles(page, context, readline, runDirectory, testCase.id, options);
        evidence.push(...constrained.evidence);
        evidenceWarnings.push(...constrained.warnings);
      }

      const actionDurationSeconds = Number(((Date.now() - startedMs) / 1_000).toFixed(3));
      const actionNetworkEvents = networkEvents.slice(actionNetworkStart);

      const observations = await collectObservations(readline, testCase);
      const operatorStatus = await askStatus(readline);
      const rationale = await askRequired(readline, "Evidence-based rationale");
      evidence.push(...await collectAttachments(readline, runDirectory, testCase.id));
      const backendEvidence = await collectBackendEvidence(options, checkpoint, state.environment.provider, state.environment.model);
      const automatedChecks = evaluateObservations(testCase, observations);
      const durationSeconds = Number(((Date.now() - startedMs) / 1_000).toFixed(3));
      const interactionChecks = evaluateInteractionEvidence({
        testCase,
        actionDurationSeconds,
        evidence,
        networkEvents: actionNetworkEvents,
        minimumActionSeconds: options.minimumActionSeconds,
      });
      automatedChecks.failures.push(...interactionChecks.failures);
      automatedChecks.gaps.push(...interactionChecks.gaps);
      if (evidence.length === 0) automatedChecks.gaps.push("No screenshot or attachment was captured");
      automatedChecks.gaps.push(...evidenceWarnings);
      if (backendEvidence.error) automatedChecks.gaps.push(`Backend evidence unavailable: ${backendEvidence.error}`);
      const effectiveStatus = deriveEffectiveStatus(operatorStatus, automatedChecks);
      const completedAt = new Date().toISOString();
      state.results.push({
        id: testCase.id,
        title: testCase.title,
        startedAt,
        completedAt,
        durationSeconds,
        actionDurationSeconds,
        operatorStatus,
        effectiveStatus,
        observations,
        rationale,
        evidence,
        automatedChecks,
        telemetry: summarizeTelemetry(networkEvents, consoleEvents, testCase.id),
        actionTelemetry: summarizeTelemetry(actionNetworkEvents, [], testCase.id),
        backendEvidence,
      });
      activeTestId = "between-cases";
      await writeSession(runDirectory, state, networkEvents, consoleEvents);
      output.write(`${testCase.id} recorded as ${effectiveStatus}. Partial report: ${path.join(runDirectory, "report.md")}\n`);
    }

    const recordCase = TEST_CASES.find((entry) => entry.id === "SV-12");
    displayCase(recordCase);
    await writeSession(runDirectory, state, networkEvents, consoleEvents);
    output.write(`Review the draft report now: ${path.join(runDirectory, "report.md")}\n`);
    const observations = await collectObservations(readline, recordCase);
    const operatorStatus = await askStatus(readline);
    const rationale = await askRequired(readline, "Final evidence-integrity rationale");
    const automatedChecks = evaluateObservations(recordCase, observations);
    const completeness = evidenceCompletenessChecks(state.results);
    automatedChecks.failures.push(...completeness.failures);
    automatedChecks.gaps.push(...completeness.gaps);
    state.results.push({
      id: recordCase.id,
      title: recordCase.title,
      startedAt: new Date().toISOString(),
      completedAt: new Date().toISOString(),
      durationSeconds: 0,
      operatorStatus,
      effectiveStatus: deriveEffectiveStatus(operatorStatus, automatedChecks),
      observations,
      rationale,
      evidence: [],
      automatedChecks,
      telemetry: summarizeTelemetry(networkEvents, consoleEvents, recordCase.id),
      backendEvidence: {
        sourceAvailable: false,
        sourceKind: "not-applicable",
        scannedLineCount: 0,
        configuredProviderMentionCount: 0,
        providerSamples: [],
        truncated: false,
        rotated: false,
        error: null,
      },
    });

    const finalized = await finalizeBundle(runDirectory, state, networkEvents, consoleEvents, options.archive);
    output.write(`\nValidation complete: ${state.overallStatus}\n`);
    output.write(`Report: ${path.join(runDirectory, "report.md")}\n`);
    output.write(`Manifest: ${path.join(runDirectory, "manifest.json")} (${finalized.manifest.files.length} files)\n`);
    if (finalized.archive) output.write(`Archive: ${finalized.archive.path}\nArchive SHA-256: ${finalized.archive.sha256}\n`);
  } catch (error) {
    if (state && runDirectory) {
      state.completedAt = null;
      state.interruptedAt = new Date().toISOString();
      state.interruptionReason = redactText(error.message);
      await writeSession(runDirectory, state, networkEvents, consoleEvents).catch(() => {});
      output.write(`Partial evidence preserved at ${runDirectory}. Resume with --resume ${runDirectory}\n`);
    }
    throw error;
  } finally {
    await context?.close().catch(() => {});
    await browser?.close().catch(() => {});
    readline.close();
  }
}

run().catch((error) => {
  process.stderr.write(`Supervised validation failed: ${redactText(error.message)}\n`);
  process.exitCode = 1;
});
