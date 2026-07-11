import { test, expect } from "@playwright/test";

test.describe("Activity page", () => {
  test("loads with stat cards", async ({ page }) => {
    await page.goto("/activity");
    await expect(page.locator("text=Completed").first()).toBeVisible({ timeout: 10_000 });
    await expect(page.locator("text=Running").first()).toBeVisible();
    await expect(page.locator("text=Pending").first()).toBeVisible();
    await expect(page.locator("text=Failed").first()).toBeVisible();
  });

  test("has filter buttons", async ({ page }) => {
    await page.goto("/activity");
    const allBtn = page.locator("button", { hasText: "All" }).first();
    await expect(allBtn).toBeVisible({ timeout: 10_000 });
  });
});
