import { expect, test } from "@playwright/test";

test.describe("Vault-to-graph E2E - fix-new-version.md §5.4", () => {
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
    await page.route("**/api/v1/settings/ai/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({}) }),
    );
    await page.route("**/api/v1/jobs/health", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", staleRunning: [] }) }),
    );
  });

  test("new vault appears in graph after scan", async ({ page }) => {
    let notesCreated = false;

    await page.route("**/api/v1/vault/scan*", (route) => {
      notesCreated = true;
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ created: 1, updated: 0, deleted: 0 }),
      });
    });

    await page.route("**/api/v1/graph", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: notesCreated
          ? JSON.stringify({
              nodes: [
                { id: "note_1", type: "note", label: "Docker and Linux Shell", status: "confirmed" },
                { id: "concept_docker", type: "concept", label: "Docker", status: "suggested" },
                { id: "concept_linux", type: "concept", label: "Linux", status: "suggested" },
              ],
              edges: [
                { source: "note_1", target: "concept_docker", type: "mentions", confidence: 0.95 },
                { source: "note_1", target: "concept_linux", type: "mentions", confidence: 0.92 },
              ],
              stats: { orphan_count: 0 },
            })
          : JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      });
    });

    await page.route("**/api/v1/vault/debug/vault-graph-pipeline", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          notes_total: notesCreated ? 1 : 0,
          graph_nodes: { note: notesCreated ? 1 : 0, concept: notesCreated ? 2 : 0, all: notesCreated ? 3 : 0 },
          diagnostics: notesCreated ? [] : [{ code: "NO_NOTES_SCANNED", message: "No notes present." }],
        }),
      });
    });

    await page.route("**/api/v1/worker/runtime", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          api: { notes_total: notesCreated ? 1 : 0, graph_nodes_active: notesCreated ? 3 : 0, graph_jobs_pending: 0 },
          worker: {},
          diagnostics: [],
        }),
      }),
    );

    await page.route("**/api/v1/monitor/stats", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ notes: notesCreated ? 1 : 0, jobs: { total: notesCreated ? 1 : 0, completed: notesCreated ? 1 : 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.evaluate(async () => {
      await fetch("/api/v1/vault/scan-and-rebuild", { method: "POST" });
    });
    await page.reload();
    await page.getByRole("button", { name: "Graph list" }).click();

    const nodes = page.locator('[aria-label="Knowledge graph list view"]').getByRole("list").first();
    await expect(nodes.getByText("Docker and Linux Shell", { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(nodes.getByText("Docker", { exact: true })).toBeVisible();
    await expect(nodes.getByText("Linux", { exact: true })).toBeVisible();
  });

  test("pipeline diagnostics show correct state before scan", async ({ page }) => {
    await page.route("**/api/v1/vault/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          notes_total: 0,
          graph_nodes: { all: 0 },
          diagnostics: [{ code: "NO_NOTES_SCANNED", message: "No notes scanned yet." }],
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
    await expect(page.getByText("No notes scanned yet", { exact: false })).toBeVisible({ timeout: 10_000 });
  });
});
