import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const OWNER_PASSWORD = process.env.E2E_OWNER_PASSWORD || "BerryBrain123!";

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
  await page.route("**/api/v1/bootstrap", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      configurationGate: { required: false, valid: true },
    }),
  }));
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

async function mockCreatedNote(page: Page, content = "", suffix: string | number = Date.now()) {
  await page.route("**/api/v1/notes", async (route) => {
    if (route.request().method() !== "POST") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: Number(String(suffix).replace(/\D/g, "").slice(-6)) || 9002,
        title: "untitled note",
        path: `inbox/e2e-draft-${suffix}.md`,
        folder: "inbox",
        content,
        content_hash: `e2e-${suffix}`,
        links: [],
        frontmatter: {},
      }),
    });
  });
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
  test("does not report a recently active worker as offline", async ({ page, context }) => {
    await authenticate(context);
    const heartbeat = await context.request.post("/api/v1/worker/heartbeat", {
      data: { jobs_processed: 0, errors: 0, ollama_healthy: true },
    });
    expect(heartbeat.ok(), await heartbeat.text()).toBeTruthy();

    const statsLoaded = page.waitForResponse("**/api/v1/monitor/stats");
    await openWorkspace(page, context);
    await statsLoaded;
    await expect(page.getByText("No worker signal. Graph processing may be stalled.")).toHaveCount(0);
  });

  test("keeps quick capture local until explicit creation", async ({
    page,
    context,
  }) => {
    await openWorkspace(page, context);

    const quickNote = page.getByRole("textbox", { name: "Quick note draft" });
    await quickNote.fill("A short idea that is not a note yet.");
    await expect(quickNote).toHaveAttribute("maxlength", "2000");
    await expect(page.getByText("36/2000 characters")).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Editor" })).toHaveCount(0);

    await page.route("**/api/v1/notes", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await new Promise((resolve) => setTimeout(resolve, 250));
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: 9001,
          title: "untitled note",
          path: "inbox/e2e-quick-note.md",
          folder: "inbox",
          content: "A short idea that is not a note yet.",
          content_hash: "e2e",
          links: [],
          frontmatter: {},
        }),
      });
    });
    await page.getByRole("button", { name: "Create note" }).click();
    await expect(page.getByText("Creating note...").first()).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Editor" })).toHaveValue(
      "A short idea that is not a note yet.",
    );
  });

  test("requires provider setup even when the tour is skipped", async ({
    page,
    context,
  }) => {
    await page.route("**/api/v1/bootstrap", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        configurationGate: { required: true, valid: false },
      }),
    }));
    await page.route("**/api/v1/ai/providers", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        providers: [
          { id: "ollama", label: "Ollama", mode: "local", url: "http://ollama:11434" },
        ],
      }),
    }));
    const csrf = await authenticate(context);
    const reset = await context.request.put("/api/v1/settings/onboarding_completed", {
      data: { value: "false" },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(reset.ok(), await reset.text()).toBeTruthy();
    await page.route("**/api/v1/settings", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          settings: [{ key: "onboarding_completed", value: "false" }],
        }),
      });
    });

    await page.goto("/brain");
    await expect(
      page.getByRole("heading", { name: "Capture first, organize later." }),
    ).toBeVisible({ timeout: 10_000 });
    await page.getByRole("button", { name: "Skip" }).click();
    await expect(page.getByRole("heading", { name: "Mode" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Close" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Local / Ollama" })).toBeVisible();
  });

  test("loads cloud models from provider presets during setup", async ({
    page,
    context,
  }) => {
    let savedConfiguration: {
      mode?: string;
      endpoint_url?: string;
      main?: { model_id?: string };
      judge?: { model_id?: string };
    } = {};
    let configured = false;
    await page.route("**/api/v1/bootstrap", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        configurationGate: {
          required: !configured,
          valid: configured,
        },
      }),
    }));
    await page.route("**/api/v1/ai/providers", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        providers: [
          { id: "ollama", label: "Ollama", mode: "local", url: "http://ollama:11434" },
          { id: "nvidia-nim", label: "NVIDIA NIM", mode: "cloud", url: "https://integrate.api.nvidia.com/v1" },
        ],
      }),
    }));
    await page.route("**/api/v1/ai/providers/nvidia-nim/models", async (route) => {
      const payload = route.request().postDataJSON() as { endpoint_url?: string; api_key?: string };
      expect(payload.endpoint_url).toBe("https://integrate.api.nvidia.com/v1");
      expect(payload.api_key).toBe("cloud-e2e-key");
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          models: [{ id: "nvidia/e2e-model-a" }, { id: "nvidia/e2e-model-b" }],
        }),
      });
    });
    await page.route("**/api/v1/ai/configuration/validate", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        valid: true,
        capabilitySnapshot: {
          chat: true,
          embeddings: true,
          structuredOutput: true,
        },
      }),
    }));
    await page.route("**/api/v1/ai/configuration", async (route) => {
      if (route.request().method() !== "PUT") {
        await route.continue();
        return;
      }
      const payload = route.request().postDataJSON() as {
        configuration?: typeof savedConfiguration;
      };
      savedConfiguration = payload.configuration || {};
      configured = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          configurationGate: { required: false, valid: true },
        }),
      });
    });
    const csrf = await authenticate(context);
    const reset = await context.request.put("/api/v1/settings/onboarding_completed", {
      data: { value: "false" },
      headers: { "X-CSRF-Token": csrf },
    });
    expect(reset.ok(), await reset.text()).toBeTruthy();
    await page.route("**/api/v1/settings", async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          settings: [{ key: "onboarding_completed", value: "false" }],
        }),
      });
    });

    await page.goto("/brain");
    await expect(
      page.getByRole("heading", { name: "Capture first, organize later." }),
    ).toBeVisible({ timeout: 10_000 });
    await page.getByRole("button", { name: "Skip" }).click();
    await page.getByRole("button", {
      name: "Cloud Models run through one cloud provider.",
      exact: true,
    }).click();
    await page.getByRole("button", { name: "Continue" }).click();
    await page.getByRole("combobox", { name: /Provider/ }).selectOption("nvidia-nim");
    await expect(page.getByRole("textbox", { name: "Provider URL" })).toHaveValue("https://integrate.api.nvidia.com/v1");
    await page.getByRole("textbox", { name: "API key" }).fill("cloud-e2e-key");
    await page.getByRole("button", { name: "Load models" }).click();
    await expect(page.getByText("2 models available.")).toBeVisible();
    await page.getByRole("button", { name: "Continue" }).click();
    for (const label of ["Main model", "Embeddings", "Judge", "HippoRAG"]) {
      await page.getByRole("combobox", { name: label, exact: true }).fill("nvidia/e2e-model-a");
      await page.getByRole("button", { name: "Continue" }).click();
    }
    await page.getByRole("button", { name: "Run compatibility tests" }).click();
    await page.getByRole("button", { name: "Finish setup" }).click();

    expect(savedConfiguration.mode).toBe("cloud");
    expect(savedConfiguration.endpoint_url).toBe("https://integrate.api.nvidia.com/v1");
    expect(savedConfiguration.main?.model_id).toBe("nvidia/e2e-model-a");
    expect(savedConfiguration.judge?.model_id).toBe("nvidia/e2e-model-a");
  });

  test("opens the dedicated Ask workspace from Home and answers there", async ({ page, context }) => {
    await page.route("**/api/v1/ask/suggestions?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        questions: [{
          id: "deployment-graph",
          prompt: "How does Deployment connect to the rest of my graph?",
          topic: "Deployment",
          source: "ai_graph_structure",
          nodeIds: [17],
        }],
        topics: ["Deployment", "Automation"],
        graph: { nodes: 9, edges: 12, suggestedInsights: 1, gaps: 0 },
      }),
    }));
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "answered",
        question: "How do my deployment notes connect?",
        answer: "Your deployment notes connect through automation evidence.",
        evidence: [{ title: "Deployment", text: "Automation keeps releases repeatable." }],
        relatedNodes: [],
        inferenceId: "home-ask-e2e",
      }),
    }));
    await openWorkspace(page, context);
    await expect(page.getByRole("button", { name: "Use voice prompt" })).toBeVisible();
    const question = "How do my deployment notes connect?";
    await page.getByRole("textbox", { name: "Ask BerryBrain" }).fill(question);
    await page
      .getByLabel("Ask your knowledge graph")
      .getByRole("button", { name: "Ask", exact: true })
      .click();
    await expect(page).toHaveURL(/\/ask\?q=/);
    await expect(page.getByPlaceholder(/ask your graph/i)).toHaveValue(question);
    await expect(page.getByText("Your deployment notes connect through automation evidence.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Graph", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "How does Deployment connect to the rest of my graph?" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Automation", exact: true })).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(page.getByPlaceholder(/ask your graph/i)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });

  test("supports the main keyboard workflow", async ({ page, context }) => {
    await openWorkspace(page, context);
    await mockCreatedNote(page, "", "keyboard");

    await page.keyboard.press("Control+KeyK");
    const palette = page.getByRole("dialog", { name: "Command palette" });
    await expect(palette).toBeVisible();
    await expect(palette.getByRole("textbox")).toBeFocused();
    await expect(palette.getByRole("option", { name: /New note/ })).toBeVisible();

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

  test("shows functional note actions above the editor toolbar", async ({ page, context }) => {
    await openWorkspace(page, context);
    await mockCreatedNote(page, "Action note", "actions");
    await page.getByRole("button", { name: "New note", exact: true }).first().click();
    await expect(page.getByRole("textbox", { name: "Editor" })).toBeVisible();

    await page.getByRole("button", { name: "More actions" }).click();
    const menu = page.getByRole("menu", { name: "Note actions" });
    await expect(menu).toBeVisible();
    await expect(menu.getByRole("menuitem", { name: "Export Markdown" })).toBeVisible();
    await expect(menu.getByRole("menuitem", { name: "Rename note" })).toBeVisible();
    await expect(menu.getByRole("menuitem", { name: "Remove note" })).toBeVisible();

    const download = page.waitForEvent("download");
    await menu.getByRole("menuitem", { name: "Export Markdown" }).click();
    expect((await download).suggestedFilename()).toMatch(/\.md$/);

    await page.route("**/api/v1/notes/**", async (route) => {
      if (route.request().method() === "DELETE") {
        await route.fulfill({ status: 500, body: "{}" });
      } else {
        await route.continue();
      }
    });
    await page.getByRole("button", { name: "More actions" }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("menuitem", { name: "Remove note" }).click();
    await expect(page.getByText("Failed to remove note.")).toBeVisible();
    await expect(page.getByRole("textbox", { name: "Editor" })).toBeVisible();
  });

  test("supports controlled Markdown history and find replacement", async ({ page, context }) => {
    await openWorkspace(page, context);
    await mockCreatedNote(page, "Alpha beta Alpha", "editor-tools");
    await page.getByRole("button", { name: "New note", exact: true }).first().click();
    const editor = page.getByRole("textbox", { name: "Editor" });
    await expect(editor).toHaveValue("Alpha beta Alpha");

    await editor.fill("Alpha beta Alpha gamma");
    await page.getByRole("button", { name: "Undo" }).click();
    await expect(editor).toHaveValue("Alpha beta Alpha");
    await page.getByRole("button", { name: "Redo" }).click();
    await expect(editor).toHaveValue("Alpha beta Alpha gamma");

    await page.getByRole("button", { name: "Find and replace" }).click();
    await page.getByPlaceholder("Find in note").fill("Alpha");
    await page.getByPlaceholder("Replace with").fill("Omega");
    await page.getByRole("button", { name: "Replace all" }).click();
    await expect(editor).toHaveValue("Omega beta Omega gamma");
    await expect(page.getByLabel("Document statistics")).toContainText("4 words");

    await editor.press("Control+z");
    await expect(editor).toHaveValue("Alpha beta Alpha gamma");
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

  test("shows a current-queue ETA instead of historical Autopilot percent", async ({
    page,
    context,
  }) => {
    await page.route("**/api/v1/home/summary", async (route) => {
      const response = await route.fetch();
      const payload = await response.json();
      payload.progress = {
        ...payload.progress,
        mode: "indeterminate",
        percent: 0,
        active: 1,
        pending: 6,
        currentStep: "Enrich Graph Node",
        status: "running",
        estimatedRemainingSeconds: 848,
        remainingTasks: 26,
      };
      await route.fulfill({ response, json: payload });
    });
    await openWorkspace(page, context);

    const card = page.getByRole("button").filter({ hasText: "Autopilot processing" });
    await expect(card).toContainText("1 active job");
    await expect(card).toContainText("6 queued");
    await expect(card).toContainText("26 maintenance tasks remaining");
    await expect(card).toContainText("About 15 min until knowledge is up to date");
    await expect(card).not.toContainText("98% done");
  });

  test("shows evidence-based cognitive maturity in Monitor", async ({
    page,
    context,
  }) => {
    await openWorkspace(page, context);

    await page.getByRole("button", { name: "Monitor", exact: true }).first().click();
    const monitor = page.getByRole("heading", { name: "Monitor" }).locator("..").locator("..");
    await monitor.getByRole("button", { name: "Health", exact: true }).click();
    await expect(monitor.getByText("Queue SLO")).toBeVisible();
    await expect(monitor.getByText(/Within target|Approaching limit|Action required/)).toBeVisible();
    await expect(monitor.getByText("Cognitive maturity")).toBeVisible();
    await expect(monitor.getByText(/Measuring real outcomes|Mature/)).toBeVisible();
    await expect(monitor.getByText("Model reliability")).toBeVisible();
  });

  test("cancels an active job from Monitor", async ({ page, context }) => {
    let cancellationRequested = false;
    await page.route("**/api/v1/jobs?limit=50", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          jobs: [
            {
              id: 41,
              type: "EXPAND_KNOWLEDGE_GRAPH",
              status: "running",
              payload: { note_path: "notes/cancel.md" },
              attempts: 1,
              max_attempts: 3,
            },
          ],
        }),
      }),
    );
    await page.route("**/api/v1/jobs/41/cancel", (route) => {
      cancellationRequested = true;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ job: { id: 41, status: "cancel_requested" } }),
      });
    });
    await openWorkspace(page, context);

    await page.getByRole("button", { name: "Monitor", exact: true }).first().click();
    const monitor = page.getByRole("heading", { name: "Monitor" }).locator("..").locator("..");
    await monitor.getByRole("button", { name: "Cancel", exact: true }).click();

    await expect(monitor.getByText("Cancellation requested for job #41.")).toBeVisible();
    expect(cancellationRequested).toBe(true);
  });

  test("creates an insight from a persisted graph inference and refreshes the graph", async ({
    page,
    context,
  }) => {
    let graphRefreshes = 0;
    page.on("request", (request) => {
      const pathname = new URL(request.url()).pathname;
      if (
        pathname.endsWith("/api/v1/graph/summary")
        || pathname.endsWith("/api/v1/graph/nodes")
        || pathname.endsWith("/api/v1/graph/delta")
      ) {
        graphRefreshes += 1;
      }
    });
    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          inferenceId: 91,
          status: "answered",
          question: "How do deployment and automation connect?",
          answer: "Automation makes deployment repeatable.",
          evidence: ["Deployment note", "Automation note"],
          relatedNodes: [],
          confidence: 0.82,
          provider: "deterministic",
          model: "e2e-fixture",
        }),
      }),
    );
    await page.route("**/api/v1/insights/from-inference", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "created",
          insight: { id: 41, title: "Deployment relies on automation" },
        }),
      }),
    );

    await openWorkspace(page, context);
    await page.getByRole("button", { name: "View graph", exact: true }).first().click();
    await expect(page.getByRole("heading", { name: "Knowledge Graph" })).toBeVisible();
    const ask = page.getByRole("button", { name: "Ask", exact: true });
    await ask.locator("..").getByRole("textbox").fill(
      "How do deployment and automation connect?",
    );
    await ask.click();
    await expect(page.getByText("Automation makes deployment repeatable.")).toBeVisible();
    const graphRefreshesBeforeSave = graphRefreshes;
    await page.getByRole("button", { name: "Create insight" }).click();
    await expect(page.getByRole("button", { name: "Insight created" })).toBeVisible();
    await expect.poll(() => graphRefreshes).toBeGreaterThan(graphRefreshesBeforeSave);
  });
});
