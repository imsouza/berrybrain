import { expect, test } from "@playwright/test";

test.describe("Hosted landing-only deployment", () => {
  test.skip(
    process.env.E2E_LANDING_ONLY !== "true",
    "Requires a build with NEXT_PUBLIC_BERRYBRAIN_LANDING_ONLY=true.",
  );

  test("offers self-hosted downloads without exposing the workspace", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("heading", { name: /knowledge you can navigate/i })).toBeVisible();
    await expect(page.getByText("Web app in development", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open BerryBrain", exact: true })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Download", exact: true }).first()).toHaveAttribute("href", "/#download");
    await expect(page.getByRole("heading", { name: "Run BerryBrain on infrastructure you control." })).toBeVisible();
    await expect(page.getByRole("link", { name: "Download .tar.gz" })).toHaveAttribute("href", /main\.tar\.gz$/);
    await expect(page.getByRole("link", { name: "Download .zip" })).toHaveAttribute("href", /main\.zip$/);
    await expect(page.locator('link[rel="manifest"]')).toHaveCount(0);
  });

  test("redirects workspace routes and blocks browser AI", async ({ page, request }) => {
    await page.goto("/brain");
    await expect(page).toHaveURL(/\/#download$/);
    await expect(page.getByRole("heading", { name: "Run BerryBrain on infrastructure you control." })).toBeVisible();

    const aiResponse = await request.post("/api/browser-ai/chat", { data: {} });
    expect(aiResponse.status()).toBe(404);
  });
});
