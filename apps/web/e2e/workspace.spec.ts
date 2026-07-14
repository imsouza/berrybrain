import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const OWNER_PASSWORD = "E2eOwnerPass123";

async function authenticate(context: BrowserContext) {
  const status = await context.request.get("/api/v1/setup/status");
  expect(status.ok()).toBeTruthy();
  const setup = await status.json();
  const ownerUsername = String(setup.ownerUsername || "admin");
  if (setup.needsSetup) {
    const configured = await context.request.post("/api/v1/setup/admin", {
      data: {
        password: OWNER_PASSWORD,
        display_name: "E2E Owner",
      },
    });
    if (configured.status() !== 409) expect(configured.status()).toBe(201);
  }
  const me = await context.request.get("/api/v1/auth/me");
  if (!me.ok()) {
    const login = await context.request.post("/api/v1/auth/login", {
      data: {
        email: ownerUsername,
        password: OWNER_PASSWORD,
        remember_me: false,
      },
    });
    expect(login.ok(), await login.text()).toBeTruthy();
  }
  const state = await context.storageState();
  const csrf = state.cookies.find((cookie) => cookie.name === "bb_csrf")?.value || "";
  expect(csrf).not.toBe("");
  return csrf;
}

async function openWorkspace(page: Page, context: BrowserContext) {
  const csrf = await authenticate(context);
  const completed = await context.request.put("/api/v1/settings/onboarding_completed", {
    data: { value: "true" },
    headers: { "X-CSRF-Token": csrf },
  });
  expect(completed.ok(), await completed.text()).toBeTruthy();
  await page.goto("/brain");
  if ((page.viewportSize()?.width || 1280) < 1024) {
    await expect(page.getByRole("button", { name: "Open navigation" })).toBeVisible({
      timeout: 15_000,
    });
  } else {
    await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible({
      timeout: 15_000,
    });
  }
}

test.describe("Public owner entry", () => {
  test("publishes a brain-scoped PWA without private navigation caching", async ({
    request,
  }) => {
    const manifestResponse = await request.get("/manifest.webmanifest");
    expect(manifestResponse.ok()).toBeTruthy();
    const manifest = await manifestResponse.json();
    expect(manifest.start_url).toBe("brain");
    expect(manifest.scope).toBe("./");

    const workerResponse = await request.get("/sw.js");
    expect(workerResponse.ok()).toBeTruthy();
    const worker = await workerResponse.text();
    const navigationHandler = worker.split("if (request.mode === \"navigate\")")[1].split("const staticAsset")[0];
    expect(navigationHandler).not.toContain("cache.put");
    expect(worker).toContain('caches.match(BASE + "/offline.html")');
  });

  test("offers setup only before the local owner exists", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: true }) }),
    );
    await page.goto("/");
    await expect(page.locator("header").getByRole("link", { name: "Setup", exact: true })).toHaveAttribute(
      "href",
      /\/setup$/,
    );
    await expect(page.locator("header").getByRole("link", { name: "Login", exact: true })).toHaveCount(0);
  });

  test("opens the configured system and lets its auth guard request login", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) => route.fulfill({ status: 401, body: "{}" }));
    await page.goto("/");
    const openSystem = page.locator("header").getByRole("link", { name: "Open BerryBrain", exact: true });
    await expect(openSystem).toHaveAttribute("href", /\/brain$/);
    await expect(page.locator("header").getByRole("link", { name: "Login", exact: true })).toHaveCount(0);
    await openSystem.click();
    await page.waitForURL(/\/login(?:\?|$)/);
    await expect(page.getByLabel("Username or owner email")).toHaveValue("");
    await expect(page.getByLabel("Password", { exact: true })).toHaveValue("");
    await expect(page.getByLabel("Username or owner email")).toHaveAttribute(
      "placeholder",
      "admin",
    );
  });

  test("shows logout when the owner session is active", async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: { id: 1 } }) }),
    );
    await page.goto("/");
    await expect(page.locator("header").getByRole("button", { name: "Logout", exact: true })).toBeVisible();
    await expect(page.locator("header").getByRole("link", { name: "Login", exact: true })).toHaveCount(0);
  });
});

test.describe("Authenticated workspace quality", () => {
  test("requires provider setup even when the tour is skipped", async ({
    page,
    context,
  }) => {
    const csrf = await authenticate(context);
    const reset = await context.request.put("/api/v1/settings/onboarding_completed", {
      data: { value: "false" },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(reset.ok(), await reset.text()).toBeTruthy();

    await page.goto("/brain");
    await expect(page.getByRole("heading", { name: "Capture first, organize later." })).toBeVisible();
    await page.getByRole("button", { name: "Skip" }).click();
    await expect(page.getByRole("heading", { name: "Choose how BerryBrain uses AI." })).toBeVisible();

    const finish = page.getByRole("button", { name: "Finish" });
    await expect(finish).toBeDisabled();
    await page.getByRole("button", { name: "Local", exact: true }).click();
    await expect(page.getByLabel("Ollama model")).toHaveValue("qwen3:8b");
    await expect(finish).toBeEnabled();
    await finish.click();
    await expect(page.getByRole("heading", { name: "Choose how BerryBrain uses AI." })).toBeHidden();
  });

  test("supports the main keyboard workflow", async ({ page, context }) => {
    await openWorkspace(page, context);

    await page.keyboard.press("Control+KeyK");
    const palette = page.getByRole("dialog", { name: "Command palette" });
    await expect(palette).toBeVisible();
    await expect(palette.getByRole("textbox")).toBeFocused();

    await page.keyboard.press("Enter");
    await expect(palette).toBeHidden();
    await expect(page.getByRole("textbox", { name: "Editor" })).toBeFocused({
      timeout: 15_000,
    });

    await page.keyboard.press("Control+KeyK");
    await expect(palette).toBeVisible();
    await expect(palette.getByRole("textbox")).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(palette).toBeHidden();
  });

  test("keeps the workspace usable without horizontal overflow on mobile", async ({
    page,
    context,
  }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openWorkspace(page, context);

    await expect(page.getByRole("button", { name: "Open navigation" })).toBeVisible();
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - window.innerWidth,
    );
    expect(overflow).toBeLessThanOrEqual(1);
  });

  test("shows an actionable degraded state when Home cannot load", async ({
    page,
    context,
  }) => {
    await page.route("**/api/v1/home/summary", (route) =>
      route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
    );
    await openWorkspace(page, context);

    await expect(page.getByText("Error loading Home data.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  });
});
