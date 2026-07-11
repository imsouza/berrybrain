import { test, expect } from "@playwright/test";

test.describe("Insights page", () => {
  test("loads and shows header", async ({ page }) => {
    await page.goto("/insights");
    await expect(page.locator("h1")).toContainText("Insights", { timeout: 10_000 });
  });

  test("shows filter buttons", async ({ page }) => {
    await page.goto("/insights");
    const allFilter = page.locator("button", { hasText: "All" }).first();
    await expect(allFilter).toBeVisible({ timeout: 10_000 });
  });

  test("shows empty state when no insights", async ({ page }) => {
    await page.goto("/insights");
    const emptyOrList = page.locator("text=No insights").or(page.locator("[class*='insight']"));
    await expect(emptyOrList.first()).toBeVisible({ timeout: 10_000 });
  });
});
