import { expect, test } from "@playwright/test";

const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || "BerryBrain123!";

type WebVitals = {
  domContentLoadedMs: number;
  transferBytes: number;
  lcpMs: number;
  cls: number;
  inpCandidateMs: number;
};

async function navigationMetrics(page: import("@playwright/test").Page, route: string) {
  const started = performance.now();
  await page.goto(route, { waitUntil: "load" });
  const secureSession = page.getByText("Checking secure session...", { exact: true });
  if (await secureSession.isVisible().catch(() => false)) {
    await secureSession.waitFor({ state: "hidden", timeout: 10_000 });
  }
  await page.waitForTimeout(150);
  await page.waitForLoadState("load");
  const wallMs = performance.now() - started;
  return page.evaluate((measuredWallMs) => {
    const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
    const scripts = performance.getEntriesByType("resource") as PerformanceResourceTiming[];
    return {
      route: window.location.pathname,
      wallMs: measuredWallMs,
      domContentLoadedMs: navigation.domContentLoadedEventEnd - navigation.startTime,
      scriptTransferBytes: scripts
        .filter((resource) => resource.initiatorType === "script")
        .reduce((total, resource) => total + resource.transferSize, 0),
    };
  }, wallMs);
}

async function authenticate(context: import("@playwright/test").BrowserContext) {
  const status = await context.request.get("/api/v1/setup/status");
  expect(status.ok()).toBeTruthy();
  const setup = await status.json();
  if (setup.needsSetup) {
    const configured = await context.request.post("/api/v1/setup/admin", {
      data: {
        password: OWNER_PASSWORD,
        display_name: "E2E Owner",
      },
    });
    if (configured.status() !== 409) expect(configured.status()).toBe(201);
  }
  const me = await context.request.get("/api/v1/auth/me");
  if (!me.ok()) {
    const login = await context.request.post("/api/v1/auth/login", {
      data: {
        email: String(setup.ownerUsername || "admin"),
        password: OWNER_PASSWORD,
        remember_me: false,
      },
    });
    expect(login.ok(), await login.text()).toBeTruthy();
  }
  const state = await context.storageState();
  const csrf = state.cookies.find((cookie) => cookie.name === "bb_csrf")?.value || "";
  expect(csrf).not.toBe("");
  return csrf;
}

test.describe("Public performance budgets", () => {
  test("landing page stays inside the production budget", async ({ page }) => {
    await page.addInitScript(() => {
      const metrics = { lcp: 0, cls: 0, inp: 0 };
      Object.defineProperty(window, "__bbVitals", { value: metrics });
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        metrics.lcp = entries.at(-1)?.startTime || metrics.lcp;
      }).observe({ type: "largest-contentful-paint", buffered: true });
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const shift = entry as PerformanceEntry & {
            value: number;
            hadRecentInput: boolean;
          };
          if (!shift.hadRecentInput) metrics.cls += shift.value;
        }
      }).observe({ type: "layout-shift", buffered: true });
      if (PerformanceObserver.supportedEntryTypes.includes("event")) {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            const event = entry as PerformanceEntry & { interactionId: number };
            if (event.interactionId > 0) {
              metrics.inp = Math.max(metrics.inp, event.duration);
            }
          }
        }).observe({
          type: "event",
          buffered: true,
          durationThreshold: 16,
        } as PerformanceObserverInit & { durationThreshold: number });
      }
      window.addEventListener(
        "click",
        () => {
          const startedAt = performance.now();
          requestAnimationFrame(() => {
            requestAnimationFrame(() => {
              metrics.inp = Math.max(metrics.inp, performance.now() - startedAt);
            });
          });
        },
        { capture: true },
      );
    });
    await page.goto("/", { waitUntil: "networkidle" });
    await page.waitForFunction(
      () => (
        window as typeof window & { __bbVitals?: { lcp: number } }
      ).__bbVitals?.lcp,
      undefined,
      { timeout: 3_000 },
    );
    await page.getByRole("heading", { level: 1 }).click();
    await page.waitForFunction(
      () => (
        window as typeof window & { __bbVitals?: { inp: number } }
      ).__bbVitals?.inp,
      undefined,
      { timeout: 1_000 },
    );

    const metrics = await page.evaluate<WebVitals>(() => {
      const navigation = performance.getEntriesByType(
        "navigation",
      )[0] as PerformanceNavigationTiming;
      const resources = performance.getEntriesByType(
        "resource",
      ) as PerformanceResourceTiming[];
      const vitals = (
        window as typeof window & {
          __bbVitals?: { lcp: number; cls: number; inp: number };
        }
      ).__bbVitals || { lcp: 0, cls: 0, inp: 0 };
      return {
        domContentLoadedMs:
          navigation.domContentLoadedEventEnd - navigation.startTime,
        transferBytes: resources
          .filter((resource) => resource.initiatorType === "script")
          .reduce((total, resource) => total + resource.transferSize, 0),
        lcpMs: vitals.lcp,
        cls: vitals.cls,
        inpCandidateMs: vitals.inp,
      };
    });

    expect(metrics.domContentLoadedMs).toBeLessThanOrEqual(2_500);
    expect(metrics.lcpMs).toBeGreaterThan(0);
    expect(metrics.lcpMs).toBeLessThanOrEqual(2_500);
    expect(metrics.cls).toBeLessThanOrEqual(0.1);
    expect(metrics.inpCandidateMs).toBeGreaterThan(0);
    expect(metrics.inpCandidateMs).toBeLessThanOrEqual(200);
    expect(metrics.transferBytes).toBeLessThanOrEqual(400_000);
  });

  test("all public pages stay inside navigation and script budgets", async ({ page }) => {
    test.setTimeout(90_000);
    const routes = [
      "/",
      "/docs",
      "/faq",
      "/contact",
      "/privacy",
      "/security",
      "/terms",
      "/gdpr-lgpd",
      "/login",
      "/setup",
      "/signup",
      "/welcome",
    ];
    const results = [];
    for (const route of routes) results.push(await navigationMetrics(page, route));

    for (const result of results) {
      expect(result.domContentLoadedMs, result.route).toBeLessThanOrEqual(2_500);
      expect(result.scriptTransferBytes, result.route).toBeLessThanOrEqual(400_000);
    }
    console.log(`[public-page-budgets] ${JSON.stringify(results)}`);
  });

  test("all authenticated pages and lazy workspace panels stay inside budgets", async ({
    page,
    context,
  }) => {
    test.setTimeout(90_000);
    const pageErrors: string[] = [];
    page.on("pageerror", (error) => {
      pageErrors.push(error.stack || error.message);
      console.error(`[browser-page-error] ${error.stack || error.message}`);
    });
    page.on("console", (message) => {
      if (message.type() === "error") console.error(`[browser-console-error] ${message.text()}`);
    });
    const csrf = await authenticate(context);
    const completed = await context.request.put("/api/v1/settings/onboarding_completed", {
      data: { value: "true" },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(completed.ok(), await completed.text()).toBeTruthy();
    const routes = [
      "/brain",
      "/account",
      "/activity",
      "/admin",
      "/insights",
      "/notifications",
      "/reviews",
    ];
    const results = [];
    for (const route of routes) results.push(await navigationMetrics(page, route));
    for (const result of results) {
      expect(result.domContentLoadedMs, result.route).toBeLessThanOrEqual(3_000);
      expect(result.scriptTransferBytes, result.route).toBeLessThanOrEqual(400_000);
    }

    await page.goto("/brain");
    const settingsButton = page.getByRole("button", { name: "Settings", exact: true });
    await expect(settingsButton).toBeEnabled({ timeout: 10_000 });
    await settingsButton.hover();
    await page.waitForTimeout(5_000);
    const settingsStarted = performance.now();
    await settingsButton.click();
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    const settingsMs = performance.now() - settingsStarted;
    expect(settingsMs).toBeLessThanOrEqual(300);
    await page.getByRole("button", { name: "Close settings" }).click();

    const graphStarted = performance.now();
    await page.getByRole("button", { name: "View graph", exact: true }).first().click();
    await expect(page.getByRole("heading", { name: "Knowledge Graph" })).toBeVisible();
    const graphMs = performance.now() - graphStarted;
    expect(graphMs).toBeLessThanOrEqual(1_500);
    expect(pageErrors, "authenticated navigation must not trigger client exceptions").toEqual([]);
    console.log(`[authenticated-page-budgets] ${JSON.stringify({ results, settingsMs, graphMs })}`);
  });
});
