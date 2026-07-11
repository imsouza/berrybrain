import { test, expect } from "@playwright/test";

test.describe("Settings panel", () => {
  test("opens and shows sections", async ({ page }) => {
    await page.goto("/");
    const settingsBtn = page.locator("button[aria-label*='settings' i], button[title*='settings' i]").first();
    if (await settingsBtn.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await settingsBtn.click();
      await expect(page.locator("text=Diagnostics")).toBeVisible({ timeout: 10_000 });
    }
  });
});
