import { expect, test } from "@playwright/test";

test.describe("Graph empty-state diagnostics (mocked API)", () => {
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

  test("renders NO_NOTES_SCANNED badge when pipeline reports it", async ({ page }) => {
    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          diagnostics: [{ code: "NO_NOTES_SCANNED", severity: "warn", detail: "no scan yet" }],
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
    await expect(page.getByText("No notes scanned yet.", { exact: false })).toBeVisible({ timeout: 10_000 });
  });

  test("renders GRAPH_HIDDEN_BY_FILTERS badge when pipeline reports it", async ({ page }) => {
    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          diagnostics: [{ code: "GRAPH_HIDDEN_BY_FILTERS", severity: "warn", detail: "filters hiding" }],
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
    await expect(page.getByText("Graph has nodes, but the current filters are hiding them.", { exact: false })).toBeVisible({
      timeout: 10_000,
    });
  });
});
