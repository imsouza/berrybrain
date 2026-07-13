import { test, expect } from "@playwright/test";

test.describe("Legacy public routes", () => {
  test("demo route redirects to docs", async ({ page }) => {
    await page.goto("/demo");
    await expect(page).toHaveURL(/\/docs$/);
    await expect(page.locator("body")).toContainText("BerryBrain");
  });

  test("admin route redirects to account page", async ({ page }) => {
    await page.goto("/admin");
    await expect(page).toHaveURL(/\/account$/);
    await expect(page.locator("h1")).toContainText("Control identity");
  });
});
