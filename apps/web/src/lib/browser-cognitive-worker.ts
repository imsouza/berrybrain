import { askBrowserCloud } from "@/lib/browser-ai";
import {
  getBrowserCloudConfig,
  getBrowserNote,
  listBrowserNotes,
  nextBrowserCognitiveJob,
  queueUnprocessedBrowserNotes,
  recoverInterruptedBrowserCognitiveJobs,
  saveBrowserCognitiveAnalysis,
  updateBrowserCognitiveJob,
  type BrowserCognitiveAnalysis,
} from "@/lib/browser-storage";

let running = false;
let rerunRequested = false;

function boundedConfidence(value: unknown) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.max(0, Math.min(1, number)) : 0.5;
}

function cleanText(value: unknown, max: number) {
  return typeof value === "string" ? value.trim().slice(0, max) : "";
}

function parseAnalysis(raw: string, validPaths: Set<string>): BrowserCognitiveAnalysis {
  const jsonText = raw
    .trim()
    .replace(/^```(?:json)?\s*/i, "")
    .replace(/\s*```$/, "");
  const value = JSON.parse(jsonText) as Record<string, unknown>;
  const concepts = Array.isArray(value.concepts) ? value.concepts : [];
  const insights = Array.isArray(value.insights) ? value.insights : [];
  const connections = Array.isArray(value.connections) ? value.connections : [];
  return {
    summary: cleanText(value.summary, 2_000),
    concepts: concepts
      .map((item) => item as Record<string, unknown>)
      .map((item) => ({
        name: cleanText(item.name, 120),
        description: cleanText(item.description, 1_000),
        confidence: boundedConfidence(item.confidence),
      }))
      .filter((item) => item.name && item.description)
      .slice(0, 12),
    insights: insights
      .map((item) => item as Record<string, unknown>)
      .map((item) => ({
        title: cleanText(item.title, 160),
        description: cleanText(item.description, 2_000),
        type: cleanText(item.type, 80) || "knowledge insight",
        confidence: boundedConfidence(item.confidence),
        evidence: (Array.isArray(item.evidence) ? item.evidence : [])
          .map((evidence) => cleanText(evidence, 500))
          .filter(Boolean)
          .slice(0, 6),
      }))
      .filter((item) => item.title && item.description && item.evidence.length > 0)
      .slice(0, 8),
    connections: connections
      .map((item) => item as Record<string, unknown>)
      .map((item) => ({
        targetPath: cleanText(item.targetPath, 2_048),
        reason: cleanText(item.reason, 1_000),
        confidence: boundedConfidence(item.confidence),
        evidence: (Array.isArray(item.evidence) ? item.evidence : [])
          .map((evidence) => cleanText(evidence, 500))
          .filter(Boolean)
          .slice(0, 6),
      }))
      .filter((item) => validPaths.has(item.targetPath) && item.reason && item.evidence.length > 0)
      .slice(0, 8),
  };
}

async function processQueue() {
  const config = await getBrowserCloudConfig();
  if (!config) return false;
  for (let processed = 0; processed < 4; processed += 1) {
    const job = await nextBrowserCognitiveJob();
    if (!job) return false;
    await updateBrowserCognitiveJob(job.id, { status: "running", progress: 15, error: undefined });
    window.dispatchEvent(new CustomEvent("bb:browser-worker-updated"));
    try {
      const note = await getBrowserNote(job.notePath);
      if (!note) throw new Error("The source note no longer exists.");
      const summaries = await Promise.all(
        (await listBrowserNotes())
          .filter((item) => item.path !== job.notePath)
          .slice(0, 16)
          .map(async (item) => {
            const detail = await getBrowserNote(item.path);
            return { path: item.path, title: item.title, excerpt: detail?.content.slice(0, 2_000) || "" };
          }),
      );
      const validPaths = new Set(summaries.map((item) => item.path));
      await updateBrowserCognitiveJob(job.id, { progress: 35 });
      const response = await askBrowserCloud([
        {
          role: "system",
          content: [
            "You are BerryBrain's evidence-grounded cognitive worker.",
            "Analyze user knowledge, never pipeline health or internal jobs.",
            "Return JSON only with: summary, concepts[], insights[], connections[].",
            "Each concept needs name, description, confidence (0..1).",
            "Each insight needs title, description, type, confidence, evidence[] with short quotes or precise paraphrases from supplied notes.",
            "Each connection needs targetPath copied exactly from AVAILABLE NOTES, reason, confidence, evidence[].",
            "Do not invent sources. Omit weak claims. Do not emit generic productivity advice or technical diagnostics.",
          ].join(" "),
        },
        {
          role: "user",
          content: JSON.stringify({
            task: "Extract useful concepts, contextual conclusions, hypotheses, premises, knowledge gaps, and evidence-based connections.",
            sourceNote: { path: note.path, title: note.title, content: note.content.slice(0, 24_000) },
            availableNotes: summaries,
          }),
        },
      ], config);
      await updateBrowserCognitiveJob(job.id, { progress: 75 });
      const analysis = parseAnalysis(response.content, validPaths);
      await saveBrowserCognitiveAnalysis(note.path, config.provider, config.model, analysis);
      await updateBrowserCognitiveJob(job.id, { status: "completed", progress: 100, error: undefined });
      window.dispatchEvent(new CustomEvent("bb:browser-knowledge-updated"));
      window.dispatchEvent(new CustomEvent("bb:browser-worker-updated"));
    } catch (error) {
      await updateBrowserCognitiveJob(job.id, {
        status: "failed",
        progress: 0,
        error: error instanceof Error ? error.message.slice(0, 500) : "Cognitive processing failed.",
      });
      window.dispatchEvent(new CustomEvent("bb:browser-worker-updated"));
    }
  }
  return Boolean(await nextBrowserCognitiveJob());
}

export async function runBrowserCognitiveWorker() {
  if (typeof window === "undefined") return;
  if (running) {
    rerunRequested = true;
    return;
  }
  running = true;
  rerunRequested = false;
  let hasRemainingJobs = false;
  let lockUnavailable = false;
  const runQueue = async () => {
    await recoverInterruptedBrowserCognitiveJobs();
    await queueUnprocessedBrowserNotes();
    hasRemainingJobs = await processQueue();
  };
  try {
    if (navigator.locks?.request) {
      await navigator.locks.request("berrybrain-cognitive-worker", { ifAvailable: true }, async (lock) => {
        if (lock) await runQueue();
        else lockUnavailable = true;
      });
    } else {
      await runQueue();
    }
  } finally {
    running = false;
  }
  if (hasRemainingJobs || lockUnavailable || rerunRequested) {
    rerunRequested = false;
    window.setTimeout(() => { void runBrowserCognitiveWorker(); }, lockUnavailable ? 1_000 : 250);
  }
}
