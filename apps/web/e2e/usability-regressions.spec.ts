import { expect, test, type Page } from "@playwright/test";

const home = {
  status: { worker: "running", cloudStatus: "configured", pendingJobs: 0, activeJobs: 0 },
  progress: { mode: "determinate", percent: 100, active: 0, pending: 0, completed: 100, failed: 2, status: "completed", currentStep: "Ready", lastResult: "Ready" },
  stats: { notes: { total: 1, createdToday: 1, unassimilated: 0 }, connections: { total: 0 }, concepts: { total: 0 }, knowledge: { weakConcepts: 0, openGaps: 0 }, jobs: { pending: 0, active: 0, failed: 2, completedToday: 100, total: 102 }, ai: {} },
  recentNotes: [], activeJobs: [], recentlyCompleted: [], recentActivity: [], recentConnections: [],
  graphSummary: { nodes: 3, edges: 2, orphans: 0, clusters: 1, centralNotes: [] }, needsAttention: [], jobsByType: {},
};
const note = { id: 1, path: "inbox/test.md", title: "Test note", folder: "inbox", content: "# Test\n\nInline $x^2$ and display math:\n\n$$\n\\frac{1}{2}\n$$\n\n```mermaid\ngraph TD\nA[Notes] --> B[Insights]\n```", content_hash: "test-hash", links: [], frontmatter: {} };

async function mockWorkspace(page: Page) {
  await page.route("**/api/v1/**", route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body: unknown = {};
    if (path.endsWith("/auth/me")) body = { user: { id: 1 } };
    else if (path.endsWith("/bootstrap")) body = { configurationGate: { required: false, valid: true } };
    else if (path.endsWith("/setup/status")) body = { needsSetup: false };
    else if (path.endsWith("/settings")) body = { settings: [{ key: "onboarding_completed", value: "true" }] };
    else if (path.endsWith("/home/summary")) body = home;
    else if (path.endsWith("/notes")) body = route.request().method() === "POST" ? note : { notes: [note], nextOffset: null, total: 1 };
    else if (path.endsWith("/notes/inbox/test.md")) body = note;
    else if (path.endsWith("/jobs")) body = { jobs: url.searchParams.get("status") === "failed" ? [{ id: 1, type: "TEST", status: "dead_letter", payload: {}, attempts: 3, max_attempts: 3, error_message: "Model not found" }] : [], counts: { total: 102, failed: 2, completed: 100 }, nextCursor: null };
    else if (path.endsWith("/automation-logs")) body = { logs: [{ id: 1, action_type: "test", description: "Event visible", created_at: "2026-10-08T00:00:00Z" }], nextCursor: null };
    else if (path.endsWith("/folders")) body = { folders: [] };
    else if (path.endsWith("/insights")) body = { insights: [] };
    else if (path.endsWith("/pipeline-progress")) body = { notes: [] };
    else if (path.endsWith("/ask/suggestions")) body = { questions: [{ id: "study", topic: "Study", prompt: "Create a study guide", source: "graph_context" }], topics: [], graph: { nodes: 3, edges: 2 } };
    else if (path.endsWith("/graph/summary")) body = { node_count: 3, edge_count: 2, graphVersion: 1 };
    else if (path.endsWith("/graph/nodes")) body = { nodes: [0, 1, 2].map(id => ({ id: `note_${id}`, type: "note", label: `Node ${id}` })), nextCursor: null, graphVersion: 1 };
    else if (path.endsWith("/graph/edges")) body = { edges: [{ source: "note_0", target: "note_1", type: "related" }, { source: "note_1", target: "note_2", type: "related" }], nextCursor: null, graphVersion: 1 };
    else if (path.endsWith("/graph/palette")) body = { colors: [] };
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
}

test.beforeEach(async ({ page }) => { await mockWorkspace(page); });

test("activity loads; monitor finds old dead letters independently of optional endpoints", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByText("Event visible", { exact: true })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();
  await page.goto("/brain?monitor=open");
  await page.getByRole("button", { name: /Failed/ }).click();
  await expect(page.getByText("Model not found", { exact: false })).toBeVisible();
});

test("Ask keeps sidebar and does not download full graph", async ({ page }) => {
  let graphPages = 0;
  page.on("request", request => { if (/\/graph\/(nodes|edges)\?/.test(request.url())) graphPages++; });
  await page.goto("/ask");
  await expect(page.getByRole("heading", { name: "Ask BerryBrain" })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();
  expect(graphPages).toBe(0);
  await page.setViewportSize({ width: 600, height: 800 });
  await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toBeVisible();
});

test("voice is disabled on insecure HTTP and suggests HTTPS", async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(window, "isSecureContext", { value: false }));
  await page.goto("/ask");
  await expect(page.getByRole("button", { name: /HTTPS/i })).toBeDisabled();
});

test("partial graph failure keeps loaded nodes and exposes retry", async ({ page }) => {
  await page.route("**/api/v1/graph/edges?**", route => route.fulfill({ status: 503, body: "Unavailable" }));
  await page.goto("/brain?graph=open");
  await expect(page.getByRole("img", { name: /Knowledge graph with 3 nodes/ })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "Graph loading is incomplete" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry", exact: true })).toBeVisible();
});

test("logo leaves new-note editor; Markdown preview renders math and Mermaid", async ({ page }) => {
  await page.goto("/brain?newNote=1");
  await expect(page.getByText("Test note", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: /Preview/i, exact: true }).click();
  await expect(page.locator(".katex").first()).toBeVisible();
  await expect(page.getByRole("img", { name: "Mermaid diagram" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Go to Brain" }).click();
  await expect(page.locator(".bb-brain-view")).toBeVisible();
});

test("dragged graph node stays pinned after physics settles", async ({ page }) => {
  await page.goto("/brain?graph=open");
  const canvas = page.getByRole("img", { name: /Knowledge graph with 3 nodes/ });
  await expect(canvas).toBeVisible();
  await expect.poll(() => page.evaluate(() => Boolean(sessionStorage.getItem("bb_graph_layout:stable:brain")))).toBeTruthy();
  const point = await canvas.evaluate(element => {
    const canvas = element as HTMLCanvasElement & { __zoom: { x: number; y: number; k: number } };
    const positions = JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!);
    const [x, y] = positions.note_0;
    const bounds = canvas.getBoundingClientRect();
    return { x: bounds.left + canvas.__zoom.x + x * canvas.__zoom.k, y: bounds.top + canvas.__zoom.y + y * canvas.__zoom.k };
  });
  await page.mouse.move(point.x, point.y);
  await page.mouse.down();
  await page.mouse.move(point.x + 55, point.y + 35, { steps: 12 });
  await page.mouse.up();
  const pinned = await page.evaluate(() => JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!).note_0);
  expect(pinned[2]).toBe(1);
  await page.waitForTimeout(1000);
  const settled = await page.evaluate(() => JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!).note_0);
  expect(settled).toEqual(pinned);
});
