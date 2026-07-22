import { expect, test } from "@playwright/test";

type WebVitals = {
  domContentLoadedMs: number;
  transferBytes: number;
  lcpMs: number;
  cls: number;
  inpCandidateMs: number;
};

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
        (event) => {
          const startedAt = event.timeStamp;
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
    await page.getByRole("link", { name: "Product", exact: true }).click();
    await page.waitForTimeout(250);

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
});
