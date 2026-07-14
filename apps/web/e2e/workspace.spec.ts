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
  if (me.ok()) return;
  const login = await context.request.post("/api/v1/auth/login", {
    data: {
      email: ownerUsername,
      password: OWNER_PASSWORD,
      remember_me: false,
    },
  });
  expect(login.ok(), await login.text()).toBeTruthy();
}

async function openWorkspace(page: Page, context: BrowserContext) {
  await page.addInitScript(() => {
    window.localStorage.setItem("bb_onboarded", "1");
  });
  await authenticate(context);
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
  test("opens the local owner login without a default password", async ({ page }) => {
    await page.goto("/");
    await page.locator("header").getByRole("link", { name: "Login", exact: true }).click();
    await expect(page.getByLabel("Username or owner email")).toHaveValue("");
    await expect(page.getByLabel("Password", { exact: true })).toHaveValue("");
    await expect(page.getByLabel("Username or owner email")).toHaveAttribute(
      "placeholder",
      "admin",
    );
  });
});

test.describe("Authenticated workspace quality", () => {
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
