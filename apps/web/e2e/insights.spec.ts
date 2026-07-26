import { test, expect } from "@playwright/test";

test.describe("Documentation pages", () => {
  test("loads docs page", async ({ page }) => {
    await page.goto("/docs");
    await expect(page.locator("body")).toContainText("What is BerryBrain", { timeout: 10_000 });
    await expect(page.locator("body")).toContainText("RAG Judge");
    await expect(page.locator("body")).toContainText("HippoRAG");
  });

  test("loads FAQ page", async ({ page }) => {
    await page.goto("/faq");
    await expect(page.locator("body")).toContainText("Can I self-host?", { timeout: 10_000 });
  });

  test("loads security legal page", async ({ page }) => {
    await page.goto("/security");
    await expect(page.locator("h1")).toContainText("Security", { timeout: 10_000 });
  });
});
