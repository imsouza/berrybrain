import { test, expect } from "@playwright/test";

test.describe("Home page", () => {
  test("loads public landing", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/BerryBrain/);
    await expect(page.locator("h1")).toContainText("evidence-backed knowledge graph");
    await expect(page.locator("text=View on GitHub")).toBeVisible();
  });

  test("shows maturity comparison", async ({ page }) => {
    await page.goto("/");
    await expect(page.locator("text=BerryBrain").first()).toBeVisible();
    await expect(page.locator("text=Obsidian")).toBeVisible();
    await expect(page.locator("text=Conditional").first()).toBeVisible();
  });
});
