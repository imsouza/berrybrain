import { test, expect } from "@playwright/test";

test.describe("Auth entry points", () => {
  test("login page renders local instance form", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1")).toContainText("Sign in to this local instance");
    await expect(page.locator("label", { hasText: "Email" })).toBeVisible();
    await expect(page.locator("label", { hasText: "Password" })).toBeVisible();
  });

  test("setup page renders self-hosted setup", async ({ page }) => {
    await page.goto("/setup");
    await expect(page.locator("body")).toContainText("Self-hosted setup", { timeout: 10_000 });
  });
});
