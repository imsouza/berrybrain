import { execFileSync } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium, devices } from "@playwright/test";

const baseUrl = (process.env.BENCHMARK_BASE_URL || "http://127.0.0.1:3000").replace(/\/$/, "");
const output = process.env.BENCHMARK_OUTPUT || "../../reports/browser-performance.json";
const routes = (process.env.BENCHMARK_ROUTES || "/berrybrain,/berrybrain/brain,/berrybrain/ask")
  .split(",")
  .map((route) => route.trim())
  .filter(Boolean);
const repetitions = Number.parseInt(process.env.BENCHMARK_REPETITIONS || "5", 10);
const ownerPassword = process.env.BENCHMARK_OWNER_PASSWORD || "";
if (!Number.isInteger(repetitions) || repetitions < 2) {
  throw new Error("BENCHMARK_REPETITIONS must be an integer greater than one");
}

const profiles = [
  { name: "desktop", context: { viewport: { width: 1440, height: 900 } } },
  { name: "mobile", context: { ...devices["Pixel 7"] } },
];

function percentile(values, quantile) {
  const ordered = [...values].sort((left, right) => left - right);
  const position = (ordered.length - 1) * quantile;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return ordered[lower];
  return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower);
}

const browser = await chromium.launch({ headless: true });
const observations = [];
try {
  let authenticatedState;
  if (ownerPassword) {
    const authenticationContext = await browser.newContext();
    const status = await authenticationContext.request.get(`${baseUrl}/api/v1/setup/status`);
    if (!status.ok()) throw new Error(`setup status failed with ${status.status()}`);
    const setup = await status.json();
    const login = await authenticationContext.request.post(`${baseUrl}/api/v1/auth/login`, {
      data: {
        email: String(setup.ownerUsername || "admin"),
        password: ownerPassword,
        remember_me: false,
      },
    });
    if (!login.ok()) throw new Error(`benchmark login failed with ${login.status()}`);
    authenticatedState = await authenticationContext.storageState();
    await authenticationContext.close();
  }
  for (const profile of profiles) {
    for (let repetition = 0; repetition < repetitions; repetition += 1) {
      const context = await browser.newContext({
        ...profile.context,
        storageState: authenticatedState,
      });
      const page = await context.newPage();
      await page.addInitScript(() => {
        window.__berrybrainBenchmark = { cls: 0, lcp: 0, longTaskMs: 0 };
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            window.__berrybrainBenchmark.lcp = Math.max(
              window.__berrybrainBenchmark.lcp,
              entry.startTime,
            );
          }
        }).observe({ type: "largest-contentful-paint", buffered: true });
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) window.__berrybrainBenchmark.cls += entry.value;
          }
        }).observe({ type: "layout-shift", buffered: true });
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            window.__berrybrainBenchmark.longTaskMs += entry.duration;
          }
        }).observe({ type: "longtask", buffered: true });
      });
      for (const route of routes) {
        const errors = [];
        const onPageError = (error) => errors.push(error.name);
        const onResponse = (response) => {
          if (response.status() >= 500) errors.push(`HTTP ${response.status()}`);
        };
        page.on("pageerror", onPageError);
        page.on("response", onResponse);
        const wallStarted = performance.now();
        const response = await page.goto(`${baseUrl}${route}`, { waitUntil: "networkidle" });
        await page.waitForTimeout(250);
        const measured = await page.evaluate(() => {
          const navigation = performance.getEntriesByType("navigation")[0];
          const resources = performance.getEntriesByType("resource");
          const memory = performance.memory;
          return {
            domContentLoadedMs: navigation?.domContentLoadedEventEnd || 0,
            loadMs: navigation?.loadEventEnd || 0,
            transferBytes: resources.reduce((total, item) => total + (item.transferSize || 0), 0),
            heapBytes: memory?.usedJSHeapSize || null,
            ...window.__berrybrainBenchmark,
          };
        });
        observations.push({
          profile: profile.name,
          repetition,
          route,
          statusCode: response?.status() || 0,
          wallMs: performance.now() - wallStarted,
          errors,
          ...measured,
        });
        page.off("pageerror", onPageError);
        page.off("response", onResponse);
      }
      await context.close();
    }
  }
} finally {
  await browser.close();
}

const groups = {};
for (const item of observations) {
  const key = `${item.profile}:${item.route}`;
  groups[key] ||= [];
  groups[key].push(item);
}
const summary = Object.fromEntries(
  Object.entries(groups).map(([key, rows]) => [
    key,
    {
      samples: rows.length,
      wallP50Ms: percentile(rows.map((item) => item.wallMs), 0.5),
      wallP95Ms: percentile(rows.map((item) => item.wallMs), 0.95),
      lcpP75Ms: percentile(rows.map((item) => item.lcp), 0.75),
      clsP75: percentile(rows.map((item) => item.cls), 0.75),
      longTaskP95Ms: percentile(rows.map((item) => item.longTaskMs), 0.95),
      transferP95Bytes: percentile(rows.map((item) => item.transferBytes), 0.95),
      heapP95Bytes: percentile(
        rows.map((item) => item.heapBytes).filter((value) => value !== null),
        0.95,
      ),
      errorCount: rows.reduce((total, item) => total + item.errors.length, 0),
    },
  ]),
);
const report = {
  schemaVersion: "berrybrain-browser-benchmark.v1",
  generatedAt: new Date().toISOString(),
  classification: "exploratory",
  gitCommit: execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim(),
  baseUrl,
  repetitions,
  summary,
  observations,
};
await mkdir(path.dirname(output), { recursive: true });
await writeFile(output, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(JSON.stringify({ output, summary }, null, 2));
