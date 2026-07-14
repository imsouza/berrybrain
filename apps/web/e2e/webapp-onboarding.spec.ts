import { expect, test } from "@playwright/test";

test.describe("Hosted web app onboarding", () => {
  test.skip(
    process.env.E2E_BROWSER_STORAGE_MODE !== "browser",
    "Requires a build with NEXT_PUBLIC_BERRYBRAIN_STORAGE_MODE=browser.",
  );

  test("allows skipping the tour but requires a verified cloud provider", async ({ page }) => {
    await page.route("**/api/browser-ai/models", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ connected: true, provider: "NVIDIA NIM", providerUrl: "https://integrate.api.nvidia.com/v1", models: ["qwen/test-model"] }),
    }));
    await page.goto("/brain");

    await expect(page.getByRole("heading", { name: "Capture first, organize later." })).toBeVisible();
    await page.getByRole("button", { name: "Skip" }).click();
    await expect(page.getByRole("heading", { name: "Connect a cloud AI provider to continue." })).toBeVisible();
    await expect(page.getByRole("button", { name: "Connect and open workspace" })).toBeDisabled();

    await page.getByLabel("Cloud API Key").fill("nvapi-test-key-that-is-long-enough");
    await page.getByRole("button", { name: "Load models" }).click();
    await page.getByLabel("Model").selectOption("qwen/test-model");
    await page.getByRole("button", { name: "Connect and open workspace" }).click();

    await expect(page.getByRole("heading", { name: "Connect a cloud AI provider to continue." })).toHaveCount(0);
    await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Donate to BerryBrain on Ko-fi" })).toContainText("♥ Donate");
    const stored = await page.evaluate(async () => new Promise<Record<string, string>>((resolve, reject) => {
      const request = indexedDB.open("berrybrain-webapp", 1);
      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        const database = request.result;
        const get = database.transaction("settings", "readonly").objectStore("settings").get("cloud-provider");
        get.onsuccess = () => {
          database.close();
          resolve(get.result);
        };
        get.onerror = () => reject(get.error);
      };
    }));
    expect(stored.provider).toBe("NVIDIA NIM");
    expect(stored.model).toBe("qwen/test-model");

    await page.getByRole("button", { name: "Settings", exact: true }).click();
    await expect(page.getByText("Cloud API (required)", { exact: true })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Local", exact: true })).toHaveCount(0);
    await expect(page.getByText("Local Ollama", { exact: true })).toHaveCount(0);
  });
});
