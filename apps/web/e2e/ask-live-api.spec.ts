import { expect, test } from "@playwright/test";

const liveApiUrl = process.env.E2E_LIVE_API_URL?.replace(/\/+$/, "") || "";
const allowIsolatedSetup = process.env.E2E_LIVE_API_ALLOW_SETUP === "1";

test("approved Ask note creates a real named vault and persisted draft", async ({ page }) => {
  test.setTimeout(120_000);
  test.skip(
    !allowIsolatedSetup || !/^http:\/\/127\.0\.0\.1:\d+$/.test(liveApiUrl),
    "Requires explicit setup permission for a fresh, isolated localhost API",
  );

  const setupStatus = await page.request.get(`${liveApiUrl}/api/v1/setup/status`);
  expect(setupStatus.ok()).toBeTruthy();
  expect((await setupStatus.json()).needsSetup).toBe(true);
  const setup = await page.request.post(`${liveApiUrl}/api/v1/setup/admin`, {
    data: {
      password: `IsolatedBrowser-${crypto.randomUUID()}-Strong`,
      display_name: "Isolated Browser Tester",
    },
  });
  expect(setup.status()).toBe(201);
  expect((await page.request.get(`${liveApiUrl}/api/v1/auth/me`)).ok()).toBeTruthy();

  await page.route("**/api/v1/**", async (route) => {
    const requested = new URL(route.request().url());
    const response = await route.fetch({
      url: `${liveApiUrl}${requested.pathname}${requested.search}`,
    });
    await route.fulfill({ response });
  });
  // Only the model and first-run UI gate are controlled. Auth, action plan,
  // vault registration, note writes, and review use the actual isolated API.
  await page.route("**/api/v1/bootstrap", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ configurationGate: { required: false, valid: true } }),
  }));
  await page.route("**/api/v1/settings", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ settings: [{ key: "onboarding_completed", value: "true" }] }),
  }));
  await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      status: "answered",
      question: "Rascunhe um artigo",
      answer: "# Feira de ciências\n\nUm artigo fundamentado.",
      evidence: [],
      relatedNodes: [],
    }),
  }));

  await page.goto("/ask", { waitUntil: "domcontentloaded" });
  expect(await page.evaluate(() => document.cookie.includes("bb_csrf="))).toBe(true);
  await page.getByPlaceholder(/ask your graph/i).fill("Rascunhe um artigo");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await page.getByRole("button", { name: "Save answer as note" }).click();
  await page.getByRole("textbox", { name: "Note filename" }).fill("Feira");
  await page.getByLabel("Destination").selectOption("new_vault");
  await page.getByRole("textbox", { name: "New vault name" }).fill("Projetos da feira");
  await page.getByRole("button", { name: "Review exact preview" }).click();
  await expect(page.getByText("Projetos da feira · shared workspace")).toBeVisible();
  const beforeApprovalVaults = await page.request.get(`${liveApiUrl}/api/v1/vault/namespaces`);
  expect((await beforeApprovalVaults.json()).vaults.some(
    (vault: { name: string }) => vault.name === "Projetos da feira",
  )).toBe(false);
  const beforeApprovalNotes = await page.request.get(`${liveApiUrl}/api/v1/notes?limit=200`);
  expect((await beforeApprovalNotes.json()).total).toBe(0);
  const approvalResponse = page.waitForResponse((response) =>
    /\/api\/v1\/ask\/action-plans\/[^/]+\/approve$/.test(response.url()) && response.status() === 200,
  );
  await page.getByRole("button", { name: "Approve vault and note" }).click();
  const approvedPlan = await (await approvalResponse).json() as { id: string };
  const savedLink = page.getByRole("link", { name: "Open saved note" });
  await expect(savedLink).toHaveAttribute("href", /vaults%2Fprojetos-da-feira/);

  const namespaces = await page.request.get(`${liveApiUrl}/api/v1/vault/namespaces`);
  expect(namespaces.ok()).toBeTruthy();
  const vaults = (await namespaces.json()).vaults as Array<{ id: string; name: string }>;
  expect(vaults.some((vault) => vault.name === "Projetos da feira" && vault.id !== "default")).toBe(true);
  const href = await savedLink.getAttribute("href");
  const notePath = new URL(href!, page.url()).searchParams.get("note");
  expect(notePath).toMatch(/^vaults\/projetos-da-feira--ask-/);
  const note = await page.request.get(`${liveApiUrl}/api/v1/notes/${notePath}`);
  expect(note.ok()).toBeTruthy();
  expect((await note.json()).content).toContain("Um artigo fundamentado.");
  const release = page.getByRole("button", { name: "Release to graph and Ask" });
  await expect(release).toBeDisabled();
  await page.getByRole("checkbox", { name: /I reviewed the claims/ }).check();
  await release.click();
  await expect(page.getByText("Reviewed note released for processing and Ask evidence.")).toBeVisible();
  const finalPlan = await page.request.get(`${liveApiUrl}/api/v1/ask/action-plans/${approvedPlan.id}`);
  expect(finalPlan.ok()).toBeTruthy();
  expect((await finalPlan.json()).evidenceStatus).toBe("eligible");
});
