import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("loads and renders workspace", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/BerryBrain/);
    await expect(page.locator("body")).toBeVisible();
  });

  test("has sidebar navigation", async ({ page }) => {
    await page.goto("/");
    const sidebar = page.locator("nav, [class*='sidebar'], [role='navigation']");
    await expect(sidebar.first()).toBeVisible({ timeout: 10_000 });
  });
});
