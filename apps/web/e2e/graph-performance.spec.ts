import { expect, test } from "@playwright/test";

const NODE_COUNT = 10_000;
const EDGE_COUNT = 40_000;

test("renders and interacts with a 10k-node progressive graph inside runtime budgets", async ({
  page,
}) => {
  test.setTimeout(45_000);
  await page.route("**/api/v1/setup/status", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ needsSetup: false }),
  }));
  await page.route("**/api/v1/auth/me", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ user: { id: 1 }, isAdmin: true }),
  }));
  await page.route("**/api/v1/bootstrap", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ configurationGate: { required: false, valid: true } }),
  }));
  await page.route("**/api/v1/settings", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ settings: [{ key: "onboarding_completed", value: "true" }] }),
  }));
  await page.route("**/api/v1/graph/summary", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ nodes: NODE_COUNT, edges: EDGE_COUNT, orphans: 0, graphVersion: 10 }),
  }));
  await page.route("**/api/v1/graph/palette", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ colors: [] }),
  }));
  await page.route("**/api/v1/graph/nodes?*", (route) => {
    const url = new URL(route.request().url());
    const cursor = Number(url.searchParams.get("cursor") || 0);
    const limit = Number(url.searchParams.get("limit") || 500);
    const end = Math.min(NODE_COUNT, cursor + limit);
    const nodes = Array.from({ length: end - cursor }, (_, offset) => {
      const id = cursor + offset + 1;
      return {
        id: `note_${id}`,
        recordId: id,
        type: "note",
        label: `Scale node ${id}`,
        status: "confirmed",
        confidence: 0.9,
        semanticState: "completed",
        colorId: "pending",
      };
    });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes, nextCursor: end < NODE_COUNT ? end : null, graphVersion: 10 }),
    });
  });
  await page.route("**/api/v1/graph/edges?*", (route) => {
    const url = new URL(route.request().url());
    const cursor = Number(url.searchParams.get("cursor") || 0);
    const limit = Number(url.searchParams.get("limit") || 1_000);
    const end = Math.min(EDGE_COUNT, cursor + limit);
    const edges = Array.from({ length: end - cursor }, (_, offset) => {
      const id = cursor + offset + 1;
      const source = (id % NODE_COUNT) + 1;
      const target = ((id * 17) % NODE_COUNT) + 1;
      return {
        id,
        source: `note_${source}`,
        target: `note_${target}`,
        type: "semantic_similarity",
        status: "confirmed",
        confidence: 0.85,
      };
    });
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ edges, nextCursor: end < EDGE_COUNT ? end : null, graphVersion: 10 }),
    });
  });

  const coldStarted = performance.now();
  await page.goto("/brain?graph=open");
  const firstCanvas = page.locator("canvas[aria-label^='Knowledge graph with']");
  await expect(firstCanvas).toBeVisible();
  const coldFirstVisualMs = performance.now() - coldStarted;
  expect(coldFirstVisualMs).toBeLessThanOrEqual(5_000);

  const completeCanvas = page.getByRole("img", {
    name: `Knowledge graph with ${NODE_COUNT} nodes and ${EDGE_COUNT} connections`,
  });
  await expect(completeCanvas).toBeVisible({ timeout: 15_000 });
  const completeLoadMs = performance.now() - coldStarted;
  expect(completeLoadMs).toBeLessThanOrEqual(15_000);

  await page.waitForTimeout(1_000);
  const interactionSamples = await completeCanvas.evaluate(async (canvas) => {
    const samples = [];
    for (let index = 0; index < 8; index += 1) {
      const sampleStarted = performance.now();
      canvas.dispatchEvent(new WheelEvent("wheel", { deltaY: index % 2 ? 90 : -90, bubbles: true }));
      await new Promise<void>((resolve) => requestAnimationFrame(() => requestAnimationFrame(() => resolve())));
      samples.push(performance.now() - sampleStarted);
    }
    return samples;
  });
  const interactionP95 = [...interactionSamples].sort((left, right) => left - right)[
    Math.ceil(interactionSamples.length * 0.95) - 1
  ];
  console.log(`[graph-interaction-samples] ${JSON.stringify(interactionSamples)}`);
  expect(interactionP95).toBeLessThanOrEqual(200);

  const runtime = await page.evaluate(() => {
    const canvas = document.querySelector("canvas[aria-label^='Knowledge graph with']") as HTMLCanvasElement;
    const memory = performance as Performance & { memory?: { usedJSHeapSize: number } };
    return {
      width: canvas.width,
      height: canvas.height,
      usedJSHeapBytes: memory.memory?.usedJSHeapSize || 0,
    };
  });
  expect(runtime.width).toBeGreaterThan(0);
  expect(runtime.height).toBeGreaterThan(0);
  if (runtime.usedJSHeapBytes) expect(runtime.usedJSHeapBytes).toBeLessThanOrEqual(512 * 1024 * 1024);

  await page.getByRole("button", { name: "Back" }).click();
  const warmStarted = performance.now();
  await page.getByRole("button", { name: "Knowledge graph", exact: true }).click();
  await expect(page.locator("canvas[aria-label^='Knowledge graph with']")).toBeVisible();
  const warmFirstVisualMs = performance.now() - warmStarted;
  expect(warmFirstVisualMs).toBeLessThanOrEqual(1_500);

  console.log(`[graph-runtime-budget] ${JSON.stringify({ coldFirstVisualMs, warmFirstVisualMs, completeLoadMs, interactionP95, ...runtime })}`);
});
