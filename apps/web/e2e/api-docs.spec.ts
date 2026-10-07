import { expect, test } from "@playwright/test";

// Read-only checks: no authenticated workspace access or model requests.
const mount = process.env.E2E_APP_MOUNT ?? "/berrybrain";

test("public documentation explains external API integration", async ({ page }) => {
  await page.goto(`${mount}/docs`);
  await expect(page.getByRole("heading", { name: "API & external applications", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "complete integration guide" })).toHaveAttribute("href", /\/docs\/api\.md$/);
  await expect(page.locator("body")).toContainText("shared workspace");
});

test("versioned OpenAPI and Swagger work through the application proxy", async ({ page, request }) => {
  const response = await request.get(`${mount}/api/v1/openapi.json`);
  expect(response.status()).toBe(200);
  const schema = await response.json();
  expect(schema.servers).toEqual([{ url: "../.." }]);
  expect(schema.paths["/api/v1/notes"].get.security).toContainEqual({ ServiceBearer: [] });
  expect(schema.paths["/api/v1/ai/configuration"].put.security).not.toContainEqual({ ServiceBearer: [] });
  const docs = await page.goto(`${mount}/api/v1/docs`);
  expect(docs?.status()).toBe(200);
  await expect(page.locator(".swagger-ui .info .title")).toContainText("BerryBrain", { timeout: 20_000 });
  await expect(page.locator(".swagger-ui")).not.toContainText("Failed to load API definition");
});
