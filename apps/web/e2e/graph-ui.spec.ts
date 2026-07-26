import { expect, test } from "@playwright/test";

test.describe("Graph UI tests - fix-new-version.md §11.4", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: { id: 1 } }) }),
    );
    await page.route("**/api/v1/settings", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ settings: [{ key: "onboarding_completed", value: "true" }] }),
      }),
    );
  });

  test("graph ask success returns grounded answer", async ({ page }) => {
    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "answered",
          question: "What is Docker?",
          answer: "Docker is a containerization platform.",
          evidence: [{ title: "Docker and Linux Shell", text: "Docker containers depend on Linux..." }],
          relatedNodes: [{ id: 1, title: "Docker" }],
        }),
      }),
    );

    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("What is Docker?");
    await page.getByRole("button", { name: "Ask" }).click();
    await expect(page.getByText("Docker is a containerization platform")).toBeVisible({ timeout: 10_000 });
  });

  test("graph ask can be saved as an insight and shown in Insights", async ({ page }) => {
    const insight = {
      id: 42,
      type: "new_connection",
      title: "Docker depends on Linux namespaces",
      description: "Docker evidence connects container isolation to Linux namespaces.",
      relatedNotes: [{ id: 1, title: "Docker and Linux Shell", path: "docker.md" }],
      relatedConcepts: ["Docker", "Linux namespaces"],
      priority: "high",
      suggestedAction: "Review the namespace evidence.",
      whyItMatters: "It explains the container boundary.",
      confidence: 0.91,
      status: "suggested",
      provider: "fixture",
      model: "fixture-model",
      createdAt: new Date().toISOString(),
    };

    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "answered",
          inferenceId: 99,
          question: "How does Docker isolate processes?",
          answer: "Docker uses Linux namespaces as part of process isolation.",
          evidence: [{ title: "Docker and Linux Shell", text: "Docker containers depend on Linux namespaces." }],
          relatedNodes: [{ id: 1, title: "Docker" }],
        }),
      }),
    );
    await page.route("**/api/v1/insights/from-inference", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "created", insight }),
      }),
    );
    await page.route("**/api/v1/insights?limit=50", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ insights: [insight] }),
      }),
    );
    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("How does Docker isolate processes?");
    await page.getByRole("button", { name: "Ask" }).click();
    await page.getByRole("button", { name: "Create insight" }).click();
    await expect(page.getByText("Saved as insight: Docker depends on Linux namespaces")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Insight created" })).toBeVisible();

    await page.goto("/insights");
    await expect(page.getByText("Docker depends on Linux namespaces")).toBeVisible({ timeout: 10_000 });
  });

  test("graph ask no evidence refusal", async ({ page }) => {
    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "insufficient_evidence",
          question: "Unknown topic",
          answer: "No evidence found to answer this question.",
          evidence: [],
        }),
      }),
    );

    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("Unknown topic");
    await page.getByRole("button", { name: "Ask" }).click();
    await expect(page.getByText("No evidence", { exact: false })).toBeVisible({ timeout: 10_000 });
  });

  test("scan vault then graph appears", async ({ page }) => {
    let notesCreated = false;

    await page.route("**/api/v1/vault/scan*", (route) => {
      notesCreated = true;
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ created: 1, updated: 0 }),
      });
    });

    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nodes: notesCreated ? [{ id: "note_1", type: "note", label: "Test Note" }] : [],
          edges: [],
          stats: { orphan_count: 0 },
        }),
      }),
    );

    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ notes_total: notesCreated ? 1 : 0, graph_nodes: { all: notesCreated ? 1 : 0 }, diagnostics: notesCreated ? [] : [{ code: "NO_NOTES_SCANNED" }] }),
      }),
    );

    await page.route("**/api/v1/jobs/health", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", staleRunning: [] }) }),
    );

    await page.goto("/brain?graph=open");
    await page.evaluate(async () => {
      await fetch("/api/v1/vault/scan-and-rebuild", { method: "POST" });
    });
    await page.reload();
    await page.getByRole("button", { name: "List view" }).click();
    await expect(page.getByText("Test Note")).toBeVisible({ timeout: 10_000 });
  });

  test("graph list view mirrors API nodes and connections", async ({ page }) => {
    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nodes: [
            { id: "note_1", type: "note", label: "Docker and Linux Shell", connectionsCount: 1 },
            { id: "concept_2", type: "concept", label: "Linux namespaces", connectionsCount: 1 },
          ],
          edges: [
            {
              id: 10,
              source: "note_1",
              target: "concept_2",
              type: "mentions",
              confidence: 0.92,
              reason: "The note explicitly mentions Linux namespaces.",
              evidence: ["Docker containers depend on Linux namespaces."],
            },
          ],
          stats: { node_count: 2, edge_count: 1, orphan_count: 0 },
        }),
      }),
    );
    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ notes_total: 1, graph_nodes: { all: 2 }, diagnostics: [] }),
      }),
    );
    await page.route("**/api/v1/jobs/health", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", staleRunning: [] }) }),
    );

    await page.goto("/brain?graph=open");
    await expect(page.getByText(/2 nodes · 1 edges/i)).toBeVisible({ timeout: 10_000 });
    await page.getByRole("button", { name: "List view" }).click();

    const listView = page.getByLabel("Knowledge graph list view");
    const nodesSection = listView.locator("section").filter({ hasText: "Nodes" });
    await expect(nodesSection.getByRole("listitem")).toHaveCount(2);
    await expect(nodesSection.getByText("Docker and Linux Shell")).toBeVisible();
    await expect(nodesSection.getByText("Linux namespaces")).toBeVisible();
    await expect(listView.getByText("Docker and Linux Shell → Linux namespaces")).toBeVisible();
  });
});
