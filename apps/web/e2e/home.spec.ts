import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("loads public landing", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) => route.fulfill({ status: 401, body: "{}" }));
    await page.goto("/");
    await expect(page).toHaveTitle(/BerryBrain/);
    await expect(page.locator("h1")).toHaveText("BerryBrain");
    await expect(page.getByText("Turn the Markdown you own into an explainable knowledge system.")).toBeVisible();
    await expect(page.locator("header").getByRole("link", { name: "Open BerryBrain", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "GitHub", exact: true }).first()).toBeVisible();
    const donate = page.getByRole("link", { name: "♥ Donate" });
    await expect(donate).toBeVisible();
    await expect(donate).toHaveAttribute("href", "https://ko-fi.com/berrybrain");
    await expect(donate).toContainText("♥ Donate");
    await expect(page.locator('script[src*="storage.ko-fi.com"]')).toHaveCount(0);
    await expect(page.getByRole("heading", { name: /Knowledge that can explain how it got there/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /From source change to scoped knowledge repair/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Separate sources, inference, policy, and presentation/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Automation with evidence, limits, and a visible state/ })).toBeVisible();
    await expect(page.getByRole("heading", { name: /Compare defaults, not plugin potential/ })).toBeVisible();
  });

  test("shows maturity comparison", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=BerryBrain").first()).toBeVisible();
    await expect(page.getByText("Obsidian", { exact: true })).toBeVisible();
    await expect(page.getByText("Notion", { exact: true })).toBeVisible();
    await expect(page.getByText("Plain folders", { exact: true })).toBeVisible();
    await expect(page.getByText("Implemented", { exact: true }).first()).toBeVisible();
  });

  test("labels @-- note references as a future capability", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.goto("/docs");
    await expect(page.getByRole("heading", { name: "Planned: searchable note references with @--" })).toBeVisible();
    await expect(page.getByText(/not available in the current release/i)).toBeVisible();
  });
});
