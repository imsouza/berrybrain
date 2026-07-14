import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("loads public landing", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) => route.fulfill({ status: 401, body: "{}" }));
    await page.goto("/");
    await expect(page).toHaveTitle(/BerryBrain/);
    await expect(page.locator("h1")).toContainText("knowledge you can navigate");
    await expect(page.locator("header").getByRole("link", { name: "Open BerryBrain", exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "GitHub", exact: true }).first()).toBeVisible();
    await expect(page.getByRole("heading", { name: /More than notes with an AI button/ })).toBeVisible();
  });

  test("shows maturity comparison", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=BerryBrain").first()).toBeVisible();
    await expect(page.getByText("Obsidian", { exact: true })).toBeVisible();
    await expect(page.getByText("Notion", { exact: true })).toBeVisible();
    await expect(page.getByText("Plain folders", { exact: true })).toBeVisible();
    await expect(page.getByText("Implemented", { exact: true }).first()).toBeVisible();
  });
});
