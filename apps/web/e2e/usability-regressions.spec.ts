import { expect, test, type Page } from "@playwright/test";

const home = {
  status: { worker: "running", cloudStatus: "configured", pendingJobs: 0, activeJobs: 0 },
  progress: { mode: "determinate", percent: 100, active: 0, pending: 0, completed: 100, failed: 2, status: "completed", currentStep: "Ready", lastResult: "Ready" },
  stats: { notes: { total: 1, createdToday: 1, unassimilated: 0 }, connections: { total: 0, createdToday: 0 }, concepts: { total: 0, newToday: 0, withoutPermanentNote: 0 }, knowledge: { weakConcepts: 0, openGaps: 0 }, jobs: { pending: 0, active: 0, failed: 2, completedToday: 100, total: 102, byStatus: { completed: 100, dead_letter: 2 } }, ai: { provider: "cloud", model: "fixture-model", embeddings: 1, metadata: 1 } },
  recentNotes: [], activeJobs: [], recentlyCompleted: [], recentActivity: [], recentConnections: [],
  graphSummary: { nodes: 3, edges: 2, orphans: 0, clusters: 1, centralNotes: [] }, needsAttention: [], jobsByType: {},
};
const note = { id: 1, path: "inbox/test.md", title: "Test note", folder: "inbox", content: "# Test\n\nInline $x^2$ and display math:\n\n$$\n\\frac{1}{2}\n$$\n\n```mermaid\ngraph TD\nA[Notes] --> B[Insights]\n```", content_hash: "test-hash", links: [], frontmatter: {} };

async function mockWorkspace(page: Page) {
  await page.route("**/api/v1/**", route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    let body: unknown = {};
    if (path.endsWith("/auth/me")) body = { user: { id: 1 } };
    else if (path.endsWith("/bootstrap")) body = { configurationGate: { required: false, valid: true } };
    else if (path.endsWith("/setup/status")) body = { needsSetup: false };
    else if (path.endsWith("/settings")) body = { settings: [{ key: "onboarding_completed", value: "true" }] };
    else if (path.endsWith("/home/summary")) body = home;
    else if (path.endsWith("/notes")) body = route.request().method() === "POST" ? note : { notes: [note], nextOffset: null, total: 1 };
    else if (path.endsWith("/notes/inbox/test.md")) body = note;
    else if (path.endsWith("/jobs")) body = { jobs: url.searchParams.get("status") === "failed" ? [{ id: 1, type: "TEST", status: "dead_letter", payload: {}, attempts: 3, max_attempts: 3, error_message: "Model not found" }] : [], counts: { total: 102, failed: 2, completed: 100 }, nextCursor: null };
    else if (path.endsWith("/automation-logs")) body = { logs: [{ id: 1, action_type: "test", description: "Event visible", created_at: "2026-10-08T00:00:00Z" }], nextCursor: null };
    else if (path.endsWith("/folders")) body = { folders: [] };
    else if (path.endsWith("/insights")) body = { insights: [] };
    else if (path.endsWith("/pipeline-progress")) body = { notes: [] };
    else if (path.endsWith("/ask/suggestions")) body = { questions: [{ id: "study", topic: "Study", prompt: "Create a study guide", source: "graph_context" }], topics: [], graph: { nodes: 3, edges: 2 } };
    else if (path.endsWith("/graph/summary")) body = { node_count: 3, edge_count: 2, graphVersion: 1 };
    else if (path.endsWith("/graph/nodes")) body = { nodes: [0, 1, 2].map(id => ({ id: `note_${id}`, type: "note", label: `Node ${id}` })), nextCursor: null, graphVersion: 1 };
    else if (path.endsWith("/graph/edges")) body = { edges: [{ source: "note_0", target: "note_1", type: "related" }, { source: "note_1", target: "note_2", type: "related" }], nextCursor: null, graphVersion: 1 };
    else if (path.endsWith("/graph/palette")) body = { colors: [] };
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
}

test.beforeEach(async ({ page }) => { await mockWorkspace(page); });

test("Alerts counts unread items and opening does not dismiss them", async ({ page }) => {
  let unread = 7;
  await page.route("**/api/v1/notifications**", route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/read-all")) unread = 0;
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
      unreadCount: unread,
      notifications: [{ id: 1, title: "Retry needs attention", description: "Temporary provider error", action: "Open Monitor", read: unread === 0 }],
    }) });
  });
  await page.goto("/brain");
  const badge = page.getByRole("button", { name: "Notifications", exact: true });
  await expect(badge).toContainText("7");
  await badge.click();
  await expect(page.getByRole("heading", { name: "Alerts 7 unread" })).toBeVisible();
  await expect(badge).toContainText("7");
  await page.getByRole("button", { name: "Mark all as read" }).click();
  await expect(page.getByRole("heading", { name: "Alerts 0 unread" })).toBeVisible();
  await expect(badge).not.toContainText("7");
});

test("Notifications page sends CSRF and keeps unread state after a rejected write", async ({ page }) => {
  let rejectWrite = true;
  await page.addInitScript(() => { document.cookie = "bb_csrf=fixture-csrf; path=/"; });
  await page.route("**/api/v1/notifications**", (route) => {
    const request = route.request();
    if (request.method() === "POST") {
      expect(request.headers()["x-csrf-token"]).toBe("fixture-csrf");
      return route.fulfill({ status: rejectWrite ? 403 : 200, contentType: "application/json", body: "{}" });
    }
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
      unreadCount: 1,
      notifications: [{ id: 7, type: "job_failed", title: "Retry needs attention", description: "Provider unavailable", action: "Open Monitor", read: false }],
    }) });
  });
  await page.goto("/notifications");
  const markAll = page.getByRole("button", { name: "Mark all as read" });
  await expect(markAll).toBeVisible();
  await markAll.click();
  await expect(page.getByRole("status")).toContainText("Could not mark notifications as read.");
  await expect(markAll).toBeVisible();
  rejectWrite = false;
  await markAll.click();
  await expect(markAll).toHaveCount(0);
});

test("Home charts use real counts and operations switch compact views", async ({ page }) => {
  await page.goto("/brain");
  const charts = page.getByTestId("workspace-charts");
  await expect(charts.getByRole("img", { name: "1 of 1 notes assimilated" })).toBeVisible();
  await expect(charts.getByRole("img", { name: "Notes: 1", exact: true })).toBeVisible();
  await expect(page.getByText("Knowledge operations", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Connections 0", exact: true }).click();
  await expect(page.getByRole("button", { name: "Connections 0", exact: true })).toHaveAttribute("aria-pressed", "true");
  await page.getByRole("button", { name: "Activity 0", exact: true }).click();
  await expect(page.getByRole("button", { name: "Activity 0", exact: true })).toHaveAttribute("aria-pressed", "true");
  await page.screenshot({ path: test.info().outputPath("home-charts-desktop.png"), fullPage: true });
  await page.setViewportSize({ width: 600, height: 800 });
  await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toBeVisible();
  await page.waitForTimeout(350); // allow the responsive sidebar transition to settle
  await charts.scrollIntoViewIfNeeded();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBeTruthy();
  await page.screenshot({ path: test.info().outputPath("home-charts-mobile.png"), fullPage: true });
});

test("activity loads; monitor finds old dead letters independently of optional endpoints", async ({ page }) => {
  await page.goto("/activity");
  await expect(page.getByText("Event visible", { exact: true })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();
  await page.goto("/brain?monitor=open");
  await page.getByRole("button", { name: /Failed/ }).click();
  await expect(page.getByText("Model not found", { exact: false })).toBeVisible();
});

test("Ask keeps sidebar and does not download full graph", async ({ page }) => {
  let graphPages = 0;
  page.on("request", request => { if (/\/graph\/(nodes|edges)\?/.test(request.url())) graphPages++; });
  await page.goto("/ask");
  await expect(page.getByRole("heading", { name: "Ask BerryBrain" })).toBeVisible();
  await expect(page.getByRole("complementary", { name: "Navigation" })).toBeVisible();
  expect(graphPages).toBe(0);
  await page.setViewportSize({ width: 600, height: 800 });
  await expect(page.getByRole("navigation", { name: "Workspace navigation" })).toBeVisible();
});

test("manual insight highlight waits for the graph and consumes only a visible insight", async ({ page }) => {
  await page.goto("/ask");
  const key = "bb_manual_insight_highlights:";
  await page.evaluate(key => localStorage.setItem(key, JSON.stringify([42, 99])), key);
  await page.reload();
  await expect(page.getByRole("heading", { name: "Ask BerryBrain" })).toBeVisible();
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!), key)).toEqual([42, 99]);
  await page.route("**/api/v1/graph/nodes?**", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify({
      nodes: [{ id: "insight_42", sourceId: 42, type: "insight", label: "Manual insight" }],
      nextCursor: null, graphVersion: 1,
    }),
  }));
  await page.route("**/api/v1/graph/edges?**", route => route.fulfill({
    status: 200, contentType: "application/json", body: JSON.stringify({ edges: [], nextCursor: null, graphVersion: 1 }),
  }));
  await page.goto("/brain?graph=open");
  await expect(page.getByRole("img", { name: /Knowledge graph with 1 nodes/ })).toBeVisible();
  await expect.poll(() => page.evaluate(key => JSON.parse(localStorage.getItem(key)!), key)).toEqual([99]);
  await page.reload();
  await expect(page.getByRole("img", { name: /Knowledge graph with 1 nodes/ })).toBeVisible();
  expect(await page.evaluate(key => JSON.parse(localStorage.getItem(key)!), key)).toEqual([99]);
});

test("voice is disabled on insecure HTTP and suggests HTTPS", async ({ page }) => {
  await page.addInitScript(() => Object.defineProperty(window, "isSecureContext", { value: false }));
  await page.goto("/ask");
  await expect(page.getByRole("button", { name: /HTTPS/i })).toBeDisabled();
});

test("partial graph failure keeps loaded nodes and exposes retry", async ({ page }) => {
  await page.route("**/api/v1/graph/edges?**", route => route.fulfill({ status: 503, body: "Unavailable" }));
  await page.goto("/brain?graph=open");
  await expect(page.getByRole("img", { name: /Knowledge graph with 3 nodes/ })).toBeVisible();
  await expect(page.getByRole("alert").filter({ hasText: "Graph loading is incomplete" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Retry", exact: true })).toBeVisible();
});

test("graph uses the compact projection and follows edge cursors", async ({ page }) => {
  const cursors: string[] = [];
  await page.route("**/api/v1/graph/edges?**", route => {
    const query = new URL(route.request().url()).searchParams;
    expect(query.get("compact")).toBe("true");
    expect(query.get("limit")).toBe("1000");
    const cursor = query.get("cursor") || "";
    cursors.push(cursor);
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
      edges: [{ id: cursor === "0" ? 1 : 2, source: "note_0", target: cursor === "0" ? "note_1" : "note_2", type: "related" }],
      nextCursor: cursor === "0" ? 1 : null,
      graphVersion: 1,
    }) });
  });
  await page.goto("/brain?graph=open");
  await expect(page.getByRole("img", { name: /Knowledge graph with 3 nodes/ })).toBeVisible();
  await expect.poll(() => cursors).toEqual(["0", "1"]);
  await expect(page.getByRole("alert").filter({ hasText: "Graph loading is incomplete" })).toHaveCount(0);
});

test("logo leaves new-note editor; Markdown preview renders math and Mermaid", async ({ page }) => {
  await page.goto("/brain?newNote=1");
  await expect(page.getByText("Test note", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: /Preview/i, exact: true }).click();
  await expect(page.locator(".katex").first()).toBeVisible();
  await expect(page.getByRole("img", { name: "Mermaid diagram" })).toBeVisible({ timeout: 30_000 });
  await page.getByRole("button", { name: "Go to Brain" }).click();
  await expect(page.locator(".bb-brain-view")).toBeVisible();
});

test("dragged graph node stays pinned after physics settles", async ({ page }) => {
  await page.goto("/brain?graph=open");
  const canvas = page.getByRole("img", { name: /Knowledge graph with 3 nodes/ });
  await expect(canvas).toBeVisible();
  await expect.poll(() => page.evaluate(() => Boolean(sessionStorage.getItem("bb_graph_layout:stable:brain")))).toBeTruthy();
  const point = await canvas.evaluate(element => {
    const canvas = element as HTMLCanvasElement & { __zoom: { x: number; y: number; k: number } };
    const positions = JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!);
    const [x, y] = positions.note_0;
    const bounds = canvas.getBoundingClientRect();
    return { x: bounds.left + canvas.__zoom.x + x * canvas.__zoom.k, y: bounds.top + canvas.__zoom.y + y * canvas.__zoom.k };
  });
  await page.mouse.move(point.x, point.y);
  await page.mouse.down();
  await page.mouse.move(point.x + 55, point.y + 35, { steps: 12 });
  await page.mouse.up();
  const pinned = await page.evaluate(() => JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!).note_0);
  expect(pinned[2]).toBe(1);
  await page.waitForTimeout(1000);
  const settled = await page.evaluate(() => JSON.parse(sessionStorage.getItem("bb_graph_layout:stable:brain")!).note_0);
  expect(settled).toEqual(pinned);
});

test("editor Ask panel captures selection context, blocks stale diff on concurrent edit, and integrates with Undo", async ({ page }) => {
  await page.route("**/api/v1/graph/infer", route => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({
      inferenceId: 91,
      status: "answered",
      question: "Summarize selection",
      answer: "## Resumo verificado\n\nVeja o [Vault da Feira](bbref:resolved:vault:feira-1).",
      references: [
        {
          kind: "vault",
          id: "feira-1",
          stableId: "vault:feira-1:vaults/feira--ask-1",
          title: "Projetos da Feira",
          path: "vaults/feira--ask-1",
          vaultId: "feira-1",
          vaultName: "Projetos da Feira",
          vaultPath: "vaults/feira--ask-1",
          current: true,
          evidenceIds: ["vault:feira-1"],
        },
      ],
    }),
  }));

  await page.goto("/brain?note=inbox%2Ftest.md");
  const editor = page.getByRole("textbox", { name: "Editor" });
  await expect(editor).toBeVisible();
  const initialDraft = await editor.inputValue();

  // Select the first line in the editor and open Ask beside note
  await editor.evaluate((el: HTMLTextAreaElement) => {
    el.focus();
    el.setSelectionRange(0, 6);
    el.dispatchEvent(new Event("select", { bubbles: true }));
  });
  await page.getByRole("button", { name: "Ask BerryBrain about this note" }).click();

  const panel = page.getByRole("complementary", { name: "Ask BerryBrain beside note" });
  await expect(panel).toBeVisible();
  await expect(panel.getByText("Suggested next questions")).toHaveCount(0);
  await expect(panel.getByRole("button", { name: /Selection \(6 chars/ })).toHaveAttribute("aria-pressed", "true");

  await panel.getByRole("button", { name: "Summarize", exact: true }).click();
  await panel.getByRole("button", { name: "Ask", exact: true }).click();

  const vaultLink = panel.getByRole("link", { name: "Open Vault: Projetos da Feira", exact: true });
  await expect(vaultLink).toBeVisible();
  await expect(vaultLink).toHaveAttribute("href", /\/brain\?vault=vaults%2Ffeira--ask-1$/);

  await panel.getByRole("button", { name: "Review diff for editor" }).click();
  const diffSection = panel.getByRole("region", { name: "Review editor diff" });
  await expect(diffSection).toBeVisible();
  await diffSection.getByLabel("Diff placement mode").selectOption("append");

  // Edit the note concurrently while the diff preview is open: approval must block
  await editor.fill(`${initialDraft}\n\nConcurrent edit.`);
  const approveButton = diffSection.getByRole("button", { name: "Approve and apply to editor" });
  await expect(approveButton).toBeDisabled();
  await expect(diffSection.getByRole("alert")).toContainText("The editor draft or saved note changed since this diff was prepared.");

  // Refresh the diff preview against the updated editor state and approve
  await diffSection.getByRole("button", { name: "Refresh diff preview" }).click();
  await expect(approveButton).toBeEnabled();
  await approveButton.click();

  await expect(editor).toHaveValue(/## Resumo verificado/);
  await expect(editor).toHaveValue(/\[Vault da Feira\]\((?:\/berrybrain)?\/brain\?vault=vaults%2Ffeira--ask-1\)/);

  // Undo in the editor toolbar must revert the applied Ask diff cleanly
  await page.getByRole("button", { name: "Undo", exact: true }).click();
  await expect(editor).toHaveValue(`${initialDraft}\n\nConcurrent edit.`);
});

test("focusNode selects and centers an out-of-page graph_node in the visual graph and Ask supports step-by-step approval", async ({ page }) => {
  await page.route("**/api/v1/graph/nodes/99/summary", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: 99,
        type: "concept",
        label: "Linux Namespaces",
        title: "Linux Namespaces",
        summary: "Kernel isolation mechanism",
        status: "confirmed",
        semanticState: "ready",
        confidenceInterval: { score: 0.92, lower: 0.85, upper: 0.97, sampleSize: 4, method: "mean" },
      }),
    });
  });

  await page.goto("/brain?graph=open&focusNode=99", { waitUntil: "domcontentloaded" });
  const canvas = page.getByRole("img", { name: /Knowledge graph/ });
  await expect(canvas).toBeVisible();
  await expect(canvas).toHaveAttribute("data-selected-node", "concept_99");
  await expect(page.getByRole("status", { name: "Focused graph node" })).toContainText("Focused node: Linux Namespaces");

  // Clear focus and verify the node is unselected without leaving the visual graph
  await page.getByRole("button", { name: "Clear focus" }).click();
  await expect(canvas).toHaveAttribute("data-selected-node", "");

  // Verify supervised step-by-step approval (create_vault -> create_note) in /ask
  const stepsExecuted: string[] = [];
  const expiresAt = new Date(Date.now() + 600_000).toISOString();
  const argumentsValue = {
    title: "Artigo",
    folder: "study",
    content: "# Artigo\n\nConteúdo supervisionado.",
    newVaultName: "Vault Supervisionado",
  };
  await page.route("**/api/v1/graph/infer", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "answered",
        question: "Elabore um artigo",
        answer: argumentsValue.content,
        evidence: [],
        references: [
          {
            evidenceId: "ev-node-99",
            kind: "graph_node",
            id: 99,
            stableId: "node-stable-99",
            title: "Linux Namespaces",
            nodeType: "concept",
            current: true,
          },
        ],
      }),
    });
  });
  await page.route("**/api/v1/ask/action-plans", async (route) => {
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: "plan-step",
        action: "create_note",
        approvalMode: "ask_for_approval",
        steps: [
          { id: "create_vault", action: "create_vault", target: "vaults/vault-supervisionado--ask-plan-step", status: "pending" },
          { id: "create_note", action: "create_note", target: "vaults/vault-supervisionado--ask-plan-step/study/artigo--ask-plan-step.md", status: "pending" },
        ],
        arguments: argumentsValue,
        argumentsHash: "a".repeat(64),
        status: "proposed",
        expiresAt,
        approvedAt: null,
        resultPath: null,
        vaultId: null,
        evidenceStatus: null,
      }),
    });
  });
  await page.route("**/api/v1/ask/action-plans/plan-step/approve", async (route) => {
    const body = route.request().postDataJSON() as { step?: string };
    stepsExecuted.push(body.step || "all");
    if (body.step === "create_vault") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: "plan-step",
          action: "create_note",
          approvalMode: "ask_for_approval",
          steps: [
            { id: "create_vault", action: "create_vault", target: "vaults/vault-supervisionado--ask-plan-step", status: "completed" },
            { id: "create_note", action: "create_note", target: "vaults/vault-supervisionado--ask-plan-step/study/artigo--ask-plan-step.md", status: "pending" },
          ],
          arguments: argumentsValue,
          argumentsHash: "a".repeat(64),
          status: "proposed",
          expiresAt,
          approvedAt: null,
          resultPath: null,
          vaultId: "plan-step",
          evidenceStatus: null,
        }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "plan-step",
        action: "create_note",
        approvalMode: "ask_for_approval",
        steps: [
          { id: "create_vault", action: "create_vault", target: "vaults/vault-supervisionado--ask-plan-step", status: "completed" },
          { id: "create_note", action: "create_note", target: "vaults/vault-supervisionado--ask-plan-step/study/artigo--ask-plan-step.md", status: "completed" },
        ],
        arguments: argumentsValue,
        argumentsHash: "a".repeat(64),
        status: "completed",
        expiresAt,
        approvedAt: new Date().toISOString(),
        resultPath: "vaults/vault-supervisionado--ask-plan-step/study/artigo--ask-plan-step.md",
        vaultId: "plan-step",
        evidenceStatus: "draft",
      }),
    });
  });
  await page.route("**/api/v1/notes/vaults/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ content: argumentsValue.content, content_hash: "b".repeat(64) }),
    });
  });

  await page.goto("/ask", { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder(/ask your graph/i).fill("Elabore um artigo");
  await page.getByRole("button", { name: "Ask", exact: true }).click();
  await expect(page.getByRole("link", { name: "Focus in Graph: Linux Namespaces" })).toHaveAttribute(
    "href",
    /\/brain\?graph=open&focusNode=99$/,
  );

  await page.getByRole("button", { name: "Save answer as note" }).click();
  await page.getByRole("textbox", { name: "Note filename" }).fill("Artigo");
  await page.getByLabel("Destination").selectOption("new_vault");
  await page.getByRole("textbox", { name: "New vault name" }).fill("Vault Supervisionado");
  await page.getByRole("button", { name: "Review exact preview" }).click();

  await expect(page.getByRole("list", { name: "Action plan steps" })).toBeVisible();
  await page.getByRole("button", { name: "Approve step 1: Create vault" }).click();
  await expect(page.getByRole("button", { name: "Approve step 2: Save note" })).toBeVisible();
  await page.getByRole("button", { name: "Approve step 2: Save note" }).click();
  await expect(page.getByRole("link", { name: "Open saved note" })).toBeVisible();
  expect(stepsExecuted).toEqual(["create_vault", "create_note"]);
});

test("AI setup shows progress bar during compatibility test and Settings supports API-key-only Auto Config", async ({ page }) => {
  await page.route("**/api/v1/ai/providers", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        providers: [
          {
            id: "gemini",
            label: "Google Gemini",
            mode: "cloud",
            url: "https://generativelanguage.googleapis.com/v1beta/openai",
            capabilities: ["chat", "embeddings", "judge", "hipporag"],
          },
          {
            id: "custom-cloud",
            label: "Custom OpenAI-compatible",
            mode: "cloud",
            url: "",
            capabilities: ["chat", "embeddings", "judge", "hipporag"],
          },
          {
            id: "ollama",
            label: "Ollama",
            mode: "local",
            url: "http://localhost:11434",
            capabilities: ["chat", "embeddings", "judge", "hipporag"],
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/ai/configuration", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          configuration: {
            schema_version: 2,
            mode: "cloud",
            endpoint_url: "https://generativelanguage.googleapis.com/v1beta/openai",
            main: { provider_id: "custom-cloud", model_id: "models/gemini-4-argon" },
            embedding: { provider_id: "custom-cloud", model_id: "models/gemini-embedding-2" },
            judge: { provider_id: "custom-cloud", model_id: "models/gemini-3.8-flash", enabled: true, mode: "single_model" },
            hipporag: { provider_id: "custom-cloud", model_id: "models/gemini-3.1-pro-preview", enabled: true },
          },
          configurationGate: { required: false, valid: true },
          credentialProviders: ["custom-cloud"],
        }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        configurationGate: { required: false, valid: true },
      }),
    });
  });

  await page.route("**/api/v1/ai/configuration/validate", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 450));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        valid: true,
        configuration: {
          schema_version: 2,
          mode: "cloud",
          endpoint_url: "https://generativelanguage.googleapis.com/v1beta/openai",
          main: { provider_id: "custom-cloud", model_id: "models/gemini-2.5-flash" },
          embedding: { provider_id: "custom-cloud", model_id: "models/gemini-embedding-2" },
          judge: { provider_id: "custom-cloud", model_id: "models/gemini-2.5-flash", enabled: true, mode: "single_model" },
          hipporag: { provider_id: "custom-cloud", model_id: "models/gemini-2.5-flash", enabled: true },
        },
        autoResolvedSlots: {
          main: "models/gemini-2.5-flash",
          judge: "models/gemini-2.5-flash",
          hipporag: "models/gemini-2.5-flash",
        },
        capabilitySnapshot: {
          chat: true,
          embeddings: true,
          validated: true,
        },
      }),
    });
  });

  await page.route("**/api/v1/ai/configuration/auto", async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 450));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        valid: true,
        saved: true,
        configuration: {
          schema_version: 2,
          mode: "cloud",
          endpoint_url: "https://generativelanguage.googleapis.com/v1beta/openai",
          main: { provider_id: "gemini", model_id: "models/gemini-2.5-flash" },
          embedding: { provider_id: "gemini", model_id: "models/gemini-embedding-001" },
          judge: { provider_id: "gemini", model_id: "models/gemini-2.5-flash", enabled: true, mode: "single_model" },
          hipporag: { provider_id: "gemini", model_id: "models/gemini-2.5-flash", enabled: true },
        },
        configurationGate: { required: false, valid: true },
        capabilitySnapshot: { validated: true },
        catalogModels: ["models/gemini-2.5-flash", "models/gemini-embedding-001"],
      }),
    });
  });

  await page.goto("/brain", { waitUntil: "domcontentloaded" });
  await page.getByRole("button", { name: "Settings" }).click();
  const settingsDialog = page.getByRole("dialog", { name: "Settings" });
  await expect(settingsDialog).toBeVisible();

  await settingsDialog.getByRole("button", { name: "AI & execution" }).click();
  await settingsDialog.getByPlaceholder("Paste API key for automatic setup").fill("AIzaSyTestAutoConfigKey");
  await settingsDialog.getByRole("button", { name: "Auto Config & Test" }).click();
  await expect(settingsDialog.getByRole("progressbar", { name: "Auto configuration compatibility progress" })).toBeVisible();
  await expect(settingsDialog.getByText(/Auto Config completed \(100% compatibility pass\)/)).toBeVisible();

  await settingsDialog.getByRole("button", { name: "Configure AI providers and models" }).click();
  await expect(page.getByRole("dialog", { name: "Mode" })).toBeVisible();
  for (let i = 0; i < 6; i += 1) {
    await page.getByRole("button", { name: "Continue" }).click();
  }
  await page.getByRole("button", { name: "Run compatibility tests" }).click();
  await expect(page.getByRole("progressbar", { name: "Configuration compatibility progress", exact: true })).toBeVisible();
  await expect(page.getByText("Provider and model compatibility verified.")).toBeVisible();
  await expect(page.getByText(/Auto-adjusted rate-limited or unavailable slots/)).toBeVisible();
});

test("Review exact preview works over HTTP non-secure contexts without crypto.randomUUID and shows active Skill badge", async ({ page }) => {
  await page.addInitScript(() => {
    try {
      Object.defineProperty(window.crypto, "randomUUID", {
        value: undefined,
        configurable: true,
        writable: true,
      });
    } catch {}
  });

  await page.route("**/api/v1/graph/infer", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        inferenceId: 301,
        status: "answered",
        question: "Crie um artigo científico sobre Fotossíntese",
        answer: "# Estudo Experimental da Fotossíntese\n\n## Resumo\nSíntese fundamentada em [Test note](bbref:ev-1).",
        evidence: [{ evidenceId: "ev-1", source: "knowledge_base", title: "Test note", text: "Clorofila" }],
        references: [{ kind: "note", id: 1, stableId: "note-1", title: "Test note", path: "inbox/test.md", current: true, evidenceIds: ["ev-1"] }],
        activeSkills: [
          {
            id: "scientific-article",
            name: "Scientific Article & Academic Paper (IMRaD / ABNT / IEEE / SBC)",
            category: "academic",
          },
        ],
      }),
    });
  });

  let receivedRequestKey = "";
  await page.route("**/api/v1/ask/action-plans", async (route) => {
    if (route.request().method() === "POST") {
      const payload = JSON.parse(route.request().postData() || "{}") as {
        title?: string;
        folder?: string;
        content?: string;
        request_key?: string;
      };
      receivedRequestKey = payload.request_key || "";
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          id: "plan-http-lan",
          approvalMode: "approve_full",
          steps: [{ id: "create_note", action: "create_note", target: "study/artigo-fotossintese.md", status: "pending" }],
          arguments: {
            title: payload.title || "Artigo Fotossintese",
            folder: payload.folder || "study",
            content: payload.content || "# Estudo",
          },
          argumentsHash: "f".repeat(64),
          status: "proposed",
          expiresAt: "2099-01-01T00:00:00Z",
          approvedAt: null,
          resultPath: null,
          evidenceStatus: null,
        }),
      });
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [], total: 0 }),
    });
  });

  await page.goto("/ask", { waitUntil: "domcontentloaded" });
  await page.getByPlaceholder(/ask your graph/i).fill("Crie um artigo científico sobre Fotossíntese");
  await page.getByRole("button", { name: "Ask", exact: true }).click();

  await expect(page.getByTestId("active-skill-badge")).toContainText("Skill: Scientific Article & Academic Paper");

  await page.getByRole("button", { name: "Save answer as note" }).click();
  await page.getByRole("textbox", { name: "Note filename" }).fill("Artigo Fotossintese");
  await page.getByRole("button", { name: "Review exact preview" }).click();

  await expect(page.getByText("Original approved preview")).toBeVisible();
  await expect(page.getByRole("button", { name: "Approve and save note" })).toBeVisible();
  expect(receivedRequestKey).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
});

test("Vault sidebar sort arrow icon cycles sort modes for folders, subfolders, and notes", async ({ page }) => {
  await page.route("**/api/v1/folders", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        folders: [
          {
            name: "alpha",
            path: "alpha",
            parent_path: "",
            depth: 0,
            note_count: 1,
            total_note_count: 1,
            total_size_bytes: 120,
            updated_at: "2026-01-10T10:00:00Z",
            has_subfolders: false,
          },
          {
            name: "zeta",
            path: "zeta",
            parent_path: "",
            depth: 0,
            note_count: 2,
            total_note_count: 3,
            total_size_bytes: 9500,
            updated_at: "2026-10-25T18:00:00Z",
            has_subfolders: true,
          },
          {
            name: "lab",
            path: "zeta/lab",
            parent_path: "zeta",
            depth: 1,
            note_count: 1,
            total_note_count: 1,
            total_size_bytes: 4000,
            updated_at: "2026-10-25T18:00:00Z",
            has_subfolders: false,
          },
        ],
      }),
    });
  });

  await page.route("**/api/v1/notes**", async (route) => {
    const reqUrl = new URL(route.request().url());
    if (reqUrl.pathname.endsWith("/notes")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          notes: [
            {
              title: "Older Alpha Note",
              path: "alpha/older.md",
              folder: "alpha",
              updatedAt: "2026-01-10T10:00:00Z",
              sizeBytes: 120,
            },
            {
              title: "Zeta Older Note",
              path: "zeta/z-old.md",
              folder: "zeta",
              updatedAt: "2026-05-01T10:00:00Z",
              sizeBytes: 500,
            },
            {
              title: "Zeta Newest Note",
              path: "zeta/a-new.md",
              folder: "zeta",
              updatedAt: "2026-10-25T18:00:00Z",
              sizeBytes: 5000,
            },
            {
              title: "Subfolder Lab Note",
              path: "zeta/lab/exp.md",
              folder: "zeta/lab",
              updatedAt: "2026-10-25T18:00:00Z",
              sizeBytes: 4000,
            },
          ],
          total: 4,
          nextOffset: null,
        }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/brain", { waitUntil: "domcontentloaded" });
  const sortBtn = page.getByTestId("vault-sort-toggle");
  await expect(sortBtn).toBeVisible();
  await expect(sortBtn).toHaveAttribute("data-sort-mode", "recent_desc");

  const sidebar = page.getByRole("complementary", { name: "Navigation" });
  await expect(sidebar.getByText("Zeta Newest Note")).toBeVisible();
  await expect(sidebar.getByText("Older Alpha Note")).toBeVisible();
  const textRecentDesc = (await sidebar.textContent()) ?? "";
  expect(textRecentDesc.indexOf("Zeta Newest Note")).toBeGreaterThan(-1);
  expect(textRecentDesc.indexOf("zeta")).toBeLessThan(textRecentDesc.indexOf("alpha"));
  expect(textRecentDesc.indexOf("Zeta Newest Note")).toBeLessThan(textRecentDesc.indexOf("Zeta Older Note"));

  await sortBtn.click();
  await expect(sortBtn).toHaveAttribute("data-sort-mode", "recent_asc");
  const textRecentAsc = (await sidebar.textContent()) ?? "";
  expect(textRecentAsc.indexOf("alpha")).toBeLessThan(textRecentAsc.indexOf("zeta"));
  expect(textRecentAsc.indexOf("Zeta Older Note")).toBeLessThan(textRecentAsc.indexOf("Zeta Newest Note"));

  await sortBtn.click();
  await expect(sortBtn).toHaveAttribute("data-sort-mode", "content_desc");
  await sortBtn.click();
  await expect(sortBtn).toHaveAttribute("data-sort-mode", "alpha_asc");
  await sortBtn.click();
  await expect(sortBtn).toHaveAttribute("data-sort-mode", "alpha_desc");
});
