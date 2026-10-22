import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { mockGraphPages } from "./graph-mocks";

async function mockPagedGraph(page: Page, nodes: Record<string, unknown>[], edges: Record<string, unknown>[] = []) {
  await page.route("**/api/v1/graph/summary?*", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ node_count: nodes.length, edge_count: edges.length, orphan_count: edges.length ? 0 : nodes.length, graphVersion: 91 }),
  }));
  await page.route("**/api/v1/graph/palette", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ colors: [] }),
  }));
  await page.route("**/api/v1/graph/nodes?*", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ nodes, nextCursor: null, graphVersion: 91 }),
  }));
  await page.route("**/api/v1/graph/edges?*", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ edges, nextCursor: null, graphVersion: 91 }),
  }));
}

test.describe("Graph UI tests - fix-new-version.md §11.4", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/setup/status", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ needsSetup: false }) }),
    );
    await page.route("**/api/v1/auth/me", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ user: { id: 1 } }) }),
    );
    await page.route("**/api/v1/bootstrap", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ configurationGate: { required: false, valid: true } }),
      }),
    );
    await page.route("**/api/v1/settings", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ settings: [{ key: "onboarding_completed", value: "true" }] }),
      }),
    );
  });

  test("Home keeps Ask and quick capture usable while overview is slow", async ({ page }) => {
    test.setTimeout(120_000);
    let finishSummary: (() => void) | undefined;
    await page.route("**/api/v1/home/summary", async (route) => {
      await new Promise<void>((resolve) => { finishSummary = resolve; });
      await route.fulfill({ status: 503, contentType: "application/json", body: "{}" });
    });
    await page.goto("/brain", { waitUntil: "domcontentloaded" });
    const quickNote = page.getByRole("textbox", { name: "Quick note draft" });
    await expect(quickNote).toBeVisible({ timeout: 60_000 });
    await quickNote.fill("An idea retained while the overview loads.");
    await expect(page.getByRole("region", { name: "Knowledge overview loading" })).toBeVisible();
    const askInput = page.getByPlaceholder("Ask a question about your notes, concepts, or connections...");
    await askInput.fill("What can I write next?");
    await expect(askInput).toHaveValue("What can I write next?");
    await expect.poll(() => Boolean(finishSummary)).toBe(true);
    finishSummary?.();
    await expect(page.getByText("Error loading Home data.")).toBeVisible({ timeout: 15_000 });
    await expect(quickNote).toHaveValue("An idea retained while the overview loads.");
    await expect(askInput).toHaveValue("What can I write next?");
    await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  });

  test("settles a 42-node worker-driven graph from a compact animated start", async ({ page }) => {
    const nodes = Array.from({ length: 42 }, (_, index) => ({
      id: `bubble_${index}`,
      type: index % 4 === 0 ? "concept" : "note",
      label: `Knowledge ${index + 1}`,
      connectionsCount: index % 6,
    }));
    const edges = Array.from({ length: 68 }, (_, index) => ({
      source: `bubble_${index % nodes.length}`,
      target: `bubble_${(index * 7 + 3) % nodes.length}`,
      type: index % 2 === 0 ? "semantic_relation" : "explicit_link",
      confidence: 0.78,
    })).filter((edge) => edge.source !== edge.target);
    await mockPagedGraph(page, nodes, edges);

    await page.goto("/brain?graph=open");
    const canvas = page.getByRole("img", { name: /Knowledge graph with 42 nodes/i });
    // This visual-physics check may start from a cold lazy-loaded GraphScreen;
    // the separate graph-performance spec enforces the first-visual budget.
    await expect(canvas).toBeVisible({ timeout: 30_000 });
    await expect(canvas).toHaveAttribute("data-layout-engine", "d3-force-v7-worker");
    await expect(canvas).toHaveAttribute("data-velocity-decay", "0.32");
    await expect(canvas).toHaveAttribute("data-collision-padding", "5");
    await expect(canvas).toHaveAttribute("data-node-border", "none");
    await expect(canvas).toHaveAttribute("data-edge-policy", "all-visible");
    await expect(canvas).toHaveAttribute("data-drag-physics", "linked-neighbors");
    const compactFrame = await canvas.screenshot();
    await page.waitForTimeout(900);
    const settlingFrame = await canvas.screenshot();
    expect(compactFrame.equals(settlingFrame)).toBeFalsy();
  });

  test("graph ask success returns grounded answer", async ({ page }) => {
    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "answered",
          question: "What is Docker?",
          answer: "Docker is a containerization platform.",
          evidence: [{ title: "Docker and Linux Shell", text: "Docker containers depend on Linux..." }],
          relatedNodes: [{ id: 1, title: "Docker" }],
        }),
      }),
    );

    await page.route("**/api/v1/graph?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("What is Docker?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect(page.getByText("Docker is a containerization platform")).toBeVisible({ timeout: 10_000 });
  });

  test("Ask note draft requires preview and explicit approval", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    let approvals = 0;
    let reviews = 0;
    let currentPath = "study/feira.md";
    const expiresAt = new Date(Date.now() + 15 * 60_000).toISOString();
    const approvedAt = new Date().toISOString();
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({
        status: "answered", question: "Rascunhe um artigo", inferenceId: 42,
        answer: "## Artigo\n\nUse [Ciência](bbref:ev-1) como fonte.",
        references: [{ kind: "note", id: 53, stableId: "note-53", title: "Ciência", path: "study/ciencia.md", current: true, evidenceIds: ["ev-1"] }],
        evidence: [{ evidenceId: "ev-1", noteId: 53 }], relatedNodes: [],
      }),
    }));
    await page.route("**/api/v1/ask/action-plans", async (route) => {
      const body = route.request().postDataJSON() as { title: string; folder: string; content: string };
      expect(body.content).toContain("/brain?note=study%2Fciencia.md");
      await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: body, argumentsHash: "plan-hash",
        status: "proposed", expiresAt, approvedAt: null, resultPath: null, errorCode: null,
      }) });
    });
    await page.route("**/api/v1/ask/action-plans/plan-42/approve", async (route) => {
      approvals += 1;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: { title: "Feira", folder: "study", content: "## Artigo\n\nUse [Ciência](/berrybrain/brain?note=study%2Fciencia.md) como fonte." },
        argumentsHash: "plan-hash", status: "completed", expiresAt, approvedAt, resultPath: "study/feira.md", errorCode: null, evidenceStatus: "draft",
      }) });
    });
    await page.route("**/api/v1/ask/action-plans/plan-42/review-draft", async (route) => {
      reviews += 1;
      expect(route.request().postDataJSON()).toEqual({ reviewed: true, content_hash: "b".repeat(64) });
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: { title: "Feira", folder: "study", content: "## Artigo" },
        argumentsHash: "plan-hash", status: "completed", expiresAt, approvedAt, resultPath: currentPath, errorCode: null, evidenceStatus: "eligible",
      }) });
    });
    await page.route("**/api/v1/ask/action-plans/plan-42", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: { title: "Feira", folder: "study", content: "## Artigo" },
        argumentsHash: "plan-hash", status: "completed", expiresAt, approvedAt, resultPath: currentPath, errorCode: null, evidenceStatus: "draft",
      }),
    }));
    await page.route("**/api/v1/notes/study/feira.md", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ content: "## Artigo\n\nUse [Ciência](/berrybrain/brain?note=study%2Fciencia.md) como fonte.", content_hash: "a".repeat(64) }),
    }));
    await page.route("**/api/v1/notes/permanent/feira.md", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ content: "## Artigo\n\nMoved safely.", content_hash: "b".repeat(64) }),
    }));
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder(/ask your graph/i).fill("Rascunhe um artigo");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Save answer as note" }).click();
    await page.getByRole("textbox", { name: "Note filename" }).fill("Feira");
    await expect(page.getByText("No note or new vault is created until you approve this exact preview.", { exact: false })).toBeVisible();
    expect(approvals).toBe(0);
    await page.getByRole("button", { name: "Review exact preview" }).click();
    await expect(page.getByRole("button", { name: "Approve and save note" })).toBeVisible();
    expect(approvals).toBe(0);
    await page.getByRole("button", { name: "Approve and save note" }).click();
    await expect(page.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /study%2Ffeira\.md/);
    expect(approvals).toBe(1);
    currentPath = "permanent/feira.md";
    await page.getByRole("button", { name: "Refresh draft" }).click();
    await expect(page.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /permanent%2Ffeira\.md/);
    await expect(page.getByText("Moved safely.")).toBeVisible();
    const release = page.getByRole("button", { name: "Release to graph and Ask" });
    await expect(release).toBeDisabled();
    await page.getByRole("checkbox", { name: /I reviewed the claims/ }).check();
    await release.click();
    await expect(page.getByText("Reviewed note released for processing and Ask evidence.")).toBeVisible();
    expect(reviews).toBe(1);
  });

  test("Ask offers an approved named vault with the first note", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    let proposed = false;
    let approved = false;
    const expiresAt = new Date(Date.now() + 15 * 60_000).toISOString();
    const argumentsValue = {
      title: "Feira",
      folder: "study",
      content: "# Feira\n\nUm artigo fundamentado.",
      newVaultName: "Projetos da feira",
    };
    const resultPath = "vaults/projetos-da-feira--ask-plan-42/study/feira--ask-plan-42.md";
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ status: "answered", question: "Rascunhe um artigo", answer: argumentsValue.content, evidence: [], relatedNodes: [] }),
    }));
    await page.route("**/api/v1/ask/action-plans", async (route) => {
      const body = route.request().postDataJSON() as { new_vault_name?: string; title: string };
      expect(body.new_vault_name).toBe("Projetos da feira");
      expect(body.title).toBe("Feira");
      proposed = true;
      await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: argumentsValue,
        argumentsHash: "plan-hash", status: "proposed", expiresAt, approvedAt: null,
        resultPath: null, vaultId: null, evidenceStatus: null,
      }) });
    });
    await page.route("**/api/v1/ask/action-plans/plan-42/approve", async (route) => {
      expect(route.request().postDataJSON()).toEqual({ arguments_hash: "plan-hash" });
      approved = true;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({
        id: "plan-42", action: "create_note", arguments: argumentsValue,
        argumentsHash: "plan-hash", status: "completed", expiresAt,
        approvedAt: new Date().toISOString(), resultPath, vaultId: "plan-42", evidenceStatus: "draft",
      }) });
    });
    await page.route(`**/api/v1/notes/${resultPath}`, (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ content: argumentsValue.content, content_hash: "a".repeat(64) }),
    }));
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder(/ask your graph/i).fill("Rascunhe um artigo");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Save answer as note" }).click();
    await page.getByRole("textbox", { name: "Note filename" }).fill("Feira");
    await page.getByLabel("Destination").selectOption("new_vault");
    await page.getByRole("textbox", { name: "New vault name" }).fill("Projetos da feira");
    await page.getByRole("button", { name: "Review exact preview" }).click();
    expect(proposed).toBe(true);
    await expect(page.getByText("Projetos da feira · shared workspace")).toBeVisible();
    await expect(page.getByRole("button", { name: "Approve vault and note" })).toBeVisible();
    expect(approved).toBe(false);
    await page.getByRole("button", { name: "Approve vault and note" }).click();
    await expect(page.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /vaults%2Fprojetos-da-feira/);
    expect(approved).toBe(true);
  });

  test("Ask can target a registered named vault for a later note", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    let targetId = "";
    await page.route("**/api/v1/vault/namespaces", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ workspaceModel: "shared", vaults: [
        { id: "default", name: "Default", path: "" },
        { id: "vault-42", name: "Projetos da feira", path: "vaults/projetos-da-feira--ask-42" },
      ] }),
    }));
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ status: "answered", question: "Explique o experimento", answer: "# Experimento\n\nDados observados.", evidence: [], relatedNodes: [] }),
    }));
    await page.route("**/api/v1/ask/action-plans", async (route) => {
      const body = route.request().postDataJSON() as { vault_id?: string };
      targetId = body.vault_id || "";
      await route.fulfill({ status: 201, contentType: "application/json", body: JSON.stringify({
        id: "plan-existing", action: "create_note",
        arguments: { title: "Experimento", folder: "study", content: "# Experimento\n\nDados observados.", targetVaultId: "vault-42", targetVaultName: "Projetos da feira" },
        argumentsHash: "plan-hash", status: "proposed", expiresAt: new Date(Date.now() + 60_000).toISOString(),
        approvedAt: null, resultPath: null, vaultId: null, evidenceStatus: null,
      }) });
    });
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder(/ask your graph/i).fill("Explique o experimento");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Save answer as note" }).click();
    await page.getByRole("textbox", { name: "Note filename" }).fill("Experimento");
    await expect(page.getByLabel("Destination")).toContainText("Existing named vault");
    await page.getByLabel("Destination").selectOption("existing_vault");
    await page.getByRole("combobox", { name: "Named vault", exact: true }).selectOption("vault-42");
    await page.getByRole("button", { name: "Review exact preview" }).click();
    expect(targetId).toBe("vault-42");
    await expect(page.getByText("Projetos da feira · shared workspace")).toBeVisible();
    await expect(page.getByRole("button", { name: "Approve and save note" })).toBeVisible();
  });

  test("Ask recovers a failed save as a reviewable draft without overwriting it", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    const expiresAt = new Date(Date.now() + 15 * 60_000).toISOString();
    const approvedAt = new Date().toISOString();
    const argumentsForPlan = { title: "Study article", folder: "study", content: "# Draft" };
    const basePlan = {
      id: "plan-partial", action: "create_note", arguments: argumentsForPlan,
      argumentsHash: "a".repeat(64), expiresAt, approvedAt,
      resultPath: "study/study-article--ask-plan-partia.md", errorCode: "content_changed_before_sync",
      evidenceStatus: "draft",
    };
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ status: "answered", question: "Study article", inferenceId: 7, answer: "# Draft", references: [], evidence: [], relatedNodes: [] }),
    }));
    await page.route("**/api/v1/ask/action-plans", (route) => route.fulfill({
      status: 201, contentType: "application/json",
      body: JSON.stringify({ ...basePlan, status: "proposed", approvedAt: null, resultPath: null, errorCode: null, evidenceStatus: null }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-partial/approve", (route) => route.fulfill({
      status: 409, contentType: "application/json", body: JSON.stringify({ detail: "Saved note changed before sync; current content was preserved for review" }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-partial/reconcile", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ ...basePlan, status: "partial", recoveryPath: null }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-partial/review-draft", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ ...basePlan, status: "completed", evidenceStatus: "eligible", errorCode: null }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-partial", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ ...basePlan, status: "failed", recoveryPath: basePlan.resultPath }),
    }));
    await page.route("**/api/v1/notes/study/study-article--ask-plan-partia.md", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ content: "# Edited by user", content_hash: "b".repeat(64) }),
    }));
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder(/ask your graph/i).fill("Study article");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Save answer as note" }).click();
    await page.getByRole("button", { name: "Review exact preview" }).click();
    await page.getByRole("button", { name: "Approve and save note" }).click();
    await expect(page.getByRole("button", { name: "Recover saved file as draft" })).toBeVisible();
    await page.getByRole("button", { name: "Recover saved file as draft" }).click();
    await expect(page.getByText(/saved note changed during processing/i)).toBeVisible();
    await expect(page.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /study-article--ask-plan-partia/);
    await expect(page.getByText("# Edited by user")).toBeVisible();
    await page.getByRole("checkbox", { name: /I reviewed the claims/ }).check();
    await page.getByRole("button", { name: "Release to graph and Ask" }).click();
    await expect(page.getByText("Reviewed note released for processing and Ask evidence.")).toBeVisible();
  });

  test("Ask previews an edited orphan before attaching it as an uncitable draft", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    const path = "study/edited--ask-plan-edited.md";
    const basePlan = {
      id: "plan-edited", action: "create_note", arguments: { title: "Edited", folder: "study", content: "# Original" },
      argumentsHash: "a".repeat(64), expiresAt: new Date(Date.now() + 900_000).toISOString(),
      approvedAt: new Date().toISOString(), resultPath: null, recoveryPath: null,
      orphanPath: path, errorCode: "execution_attempts_exhausted", evidenceStatus: null,
    };
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ status: "answered", question: "Edited", inferenceId: 7, answer: "# Original", references: [], evidence: [], relatedNodes: [] }),
    }));
    await page.route("**/api/v1/ask/action-plans", (route) => route.fulfill({
      status: 201, contentType: "application/json",
      body: JSON.stringify({ ...basePlan, status: "proposed", approvedAt: null, orphanPath: null, errorCode: null }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-edited/approve", (route) => route.fulfill({
      status: 409, contentType: "application/json", body: JSON.stringify({ detail: "Interrupted save" }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-edited", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ ...basePlan, status: "failed" }),
    }));
    await page.route("**/api/v1/notes/study/edited--ask-plan-edited.md", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ content: "# Changed by user", content_hash: "b".repeat(64) }),
    }));
    await page.route("**/api/v1/ask/action-plans/plan-edited/reconcile", async (route) => {
      expect(route.request().postDataJSON()).toEqual({ reviewed: true, content_hash: "b".repeat(64) });
      await route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ ...basePlan, status: "partial", resultPath: path, orphanPath: null, evidenceStatus: "draft", errorCode: "recovered_changed_file" }),
      });
    });
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await page.getByPlaceholder(/ask your graph/i).fill("Edited");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Save answer as note" }).click();
    await page.getByRole("button", { name: "Review exact preview" }).click();
    await page.getByRole("button", { name: "Approve and save note" }).click();
    const attach = page.getByRole("button", { name: "Attach changed file as draft" });
    await expect(attach).toBeDisabled();
    await expect(page.getByText("# Changed by user")).toBeVisible();
    await page.getByRole("checkbox", { name: /I reviewed this exact saved file/ }).check();
    await attach.click();
    await expect(page.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /edited--ask-plan-edited/);
    await expect(page.getByText(/saved note changed during processing/i)).toBeVisible();
  });

  test("Ask reopens a failed save from the owner's paginated list", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    const path = "study/edited--ask-reopen-plan.md";
    const plan = {
      id: "reopen-plan", action: "create_note", arguments: { title: "Edited plan", folder: "study", content: "# Original" },
      argumentsHash: "a".repeat(64), status: "failed", expiresAt: new Date().toISOString(),
      approvedAt: new Date().toISOString(), resultPath: null, recoveryPath: null,
      orphanPath: path, errorCode: "execution_attempts_exhausted", evidenceStatus: null,
    };
    await page.route("**/api/v1/ask/action-plans/failed?*", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify([{ id: plan.id, title: "Edited plan", orphanPath: path, errorCode: plan.errorCode, createdAt: new Date().toISOString() }]),
    }));
    await page.route("**/api/v1/ask/action-plans/reopen-plan", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify(plan),
    }));
    await page.route("**/api/v1/notes/study/edited--ask-reopen-plan.md", (route) => route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ content: "# Edited after failure", content_hash: "c".repeat(64) }),
    }));
    await page.route("**/api/v1/ask/action-plans/reopen-plan/reconcile", async (route) => {
      expect(route.request().postDataJSON()).toEqual({ reviewed: true, content_hash: "c".repeat(64) });
      await route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ ...plan, status: "partial", resultPath: path, orphanPath: null, evidenceStatus: "draft" }),
      });
    });
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    const section = page.getByRole("region", { name: "Ask failed saves" });
    await expect(section.getByRole("button", { name: /Edited plan/ })).toBeVisible({ timeout: 60_000 });
    await section.getByRole("button", { name: /Edited plan/ }).click();
    await expect(section.getByText("# Edited after failure")).toBeVisible();
    await section.getByRole("checkbox", { name: /I reviewed this exact saved file/ }).check();
    await section.getByRole("button", { name: "Attach changed file as draft" }).click();
    await expect(section.getByRole("link", { name: "Open saved note" })).toHaveAttribute("href", /edited--ask-reopen-plan/);
  });

  test("Ask reopens an older saved draft after a browser session change", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    let released = false;
    const plan = {
      id: "saved-plan", action: "create_note", arguments: { title: "Feira", folder: "study", content: "# Feira" },
      argumentsHash: "a".repeat(64), status: "completed", expiresAt: new Date().toISOString(),
      approvedAt: new Date().toISOString(), resultPath: "study/feira.md", errorCode: null,
      evidenceStatus: "draft",
    };
    await page.route("**/api/v1/ask/action-plans/reviewable?*", (route) => {
      const offset = Number(new URL(route.request().url()).searchParams.get("offset"));
      const pageItems = offset === 0
        ? Array.from({ length: 20 }, (_, index) => ({ id: `other-${index}`, title: `Draft ${index}`, resultPath: `study/other-${index}.md`, createdAt: new Date().toISOString() }))
        : [{ id: "saved-plan", title: "Feira", resultPath: "study/feira.md", createdAt: new Date().toISOString() }];
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(released ? [] : pageItems) });
    });
    await page.route("**/api/v1/ask/action-plans/saved-plan", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify(plan),
    }));
    await page.route("**/api/v1/notes/study/feira.md", (route) => route.fulfill({
      status: 200, contentType: "application/json", body: JSON.stringify({ content: "# Feira\n\nCurrent saved text", content_hash: "b".repeat(64) }),
    }));
    await page.route("**/api/v1/ask/action-plans/saved-plan/review-draft", async (route) => {
      expect(route.request().postDataJSON()).toEqual({ reviewed: true, content_hash: "b".repeat(64) });
      released = true;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ...plan, evidenceStatus: "eligible" }) });
    });
    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    await expect(page.getByPlaceholder(/ask your graph/i)).toBeVisible({ timeout: 60_000 });
    const section = page.getByRole("region", { name: "Ask drafts awaiting review" });
    await expect(section.getByRole("button", { name: "Load more drafts" })).toBeVisible({ timeout: 30_000 });
    await section.getByRole("button", { name: "Load more drafts" }).click();
    await expect(section.getByRole("button", { name: /Feira/ })).toBeVisible({ timeout: 30_000 });
    await section.getByRole("button", { name: /Feira/ }).click();
    await expect(section.getByText("Current saved text")).toBeVisible();
    await section.getByRole("checkbox", { name: /I reviewed the claims/ }).check();
    await section.getByRole("button", { name: "Release to graph and Ask" }).click();
    await expect(section).toHaveCount(0);
    expect(released).toBe(true);
  });

  test("Ask links verified sources and entering Flow clears only the old question", async ({ page }) => {
    test.setTimeout(120_000);
    await mockPagedGraph(page, []);
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "answered",
        question: "Quais notas usar?",
        answer: "Use [Ciência de dados](bbref:ev-note), [Grafos](bbref:ev-node) e [texto enganoso](bbref:ev-pdf) como fontes.",
        evidence: [{ evidenceId: "ev-note", noteId: 53 }],
        references: [{
          kind: "note", id: 53, stableId: "stable-note-53", title: "Ciência de dados",
          path: "Feira/Ciência de dados.md", current: true, evidenceIds: ["ev-note"],
        }, {
          kind: "attachment", id: 7, stableId: "stable-attachment-7", title: "dados.pdf",
          path: "Feira/Ciência de dados.md", current: true, evidenceIds: ["ev-pdf"],
        }, {
          kind: "graph_node", id: 6, stableId: "stable-node-6", title: "Grafos",
          nodeType: "concept", current: true, evidenceIds: ["ev-node"],
          sourceNotes: [{ id: 53, title: "Ciência de dados", path: "Feira/Ciência de dados.md", vaultId: "default" }],
        }],
        relatedNodes: [],
      }),
    }));
    await page.route("**/api/v1/ask/sessions", (route) => route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ session: { id: "flow-53" }, turns: [] }),
    }));

    await page.goto("/ask", { waitUntil: "domcontentloaded" });
    const question = page.getByPlaceholder(/ask your graph/i);
    await question.fill("Quais notas usar?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    const source = page.getByRole("link", { name: "Open note: Ciência de dados" }).first();
    await expect(source).toHaveAttribute("href", /\/brain\?note=Feira%2FCi/);
    const attachment = page.getByRole("link", { name: "Open attachment in note: dados.pdf" }).first();
    await expect(attachment).toHaveAttribute("href", /\/brain\?note=Feira%2FCi/);
    await expect(attachment).toHaveText("dados.pdf");
    await expect(page.getByRole("link", { name: "Open graph node: Grafos" }).first()).toHaveAttribute("href", /\/graph\/nodes\/6$/);
    await expect(page.getByRole("link", { name: "Open source note: Ciência de dados" })).toHaveAttribute("href", /\/brain\?note=Feira%2FCi/);
    await expect(page.getByText("texto enganoso")).toHaveCount(0);
    await page.getByRole("button", { name: "Continue in Flow" }).click();
    await expect(question).toHaveValue("");
    await expect(question).toBeFocused();
  });

  test("provider failure offers retry and settings without rendering an answer", async ({ page }) => {
    await mockPagedGraph(page, []);
    let attempts = 0;
    await page.route("**/api/v1/graph/infer", (route) => {
      attempts += 1;
      if (attempts === 1) {
        return route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            detail: {
              code: "provider_unavailable",
              message: "The configured AI provider did not return an answer.",
            },
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "answered",
          question: "What connects these notes?",
          answer: "The notes share container orchestration evidence.",
          evidence: [{ title: "Container notes", text: "Shared orchestration evidence." }],
          relatedNodes: [],
        }),
      });
    });

    await page.goto("/ask");
    await page.getByPlaceholder(/ask your graph/i).fill("What connects these notes?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();

    await expect(page.getByRole("region", { name: "Ask unavailable" })).toBeVisible();
    await expect(page.getByText("BerryBrain answer")).toHaveCount(0);
    await expect(page.getByText(/Strongest evidence/i)).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Retry" })).toBeVisible();
    await page.getByRole("button", { name: "Open Settings" }).click();
    await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
    await page.getByRole("button", { name: "Close settings" }).click();

    await page.getByRole("button", { name: "Retry" }).click();
    await expect(page.getByText("The notes share container orchestration evidence.")).toBeVisible();
    expect(attempts).toBe(2);
  });

  test("voice prompt shows a live waveform and writes recognized speech", async ({ page }) => {
    await page.addInitScript(() => {
      class MockRecognition {
        lang = "";
        continuous = false;
        interimResults = false;
        maxAlternatives = 1;
        onstart: (() => void) | null = null;
        onerror: ((event: { error?: string }) => void) | null = null;
        onend: (() => void) | null = null;
        onresult: ((event: unknown) => void) | null = null;
        start() {
          (window as typeof window & { __mockRecognition?: MockRecognition }).__mockRecognition = this;
          this.onstart?.();
        }
        stop() { this.onend?.(); }
        abort() { this.onend?.(); }
      }
      class MockAudioContext {
        state = "running";
        createAnalyser() {
          return { fftSize: 0, smoothingTimeConstant: 0, frequencyBinCount: 8, getByteFrequencyData: (values: Uint8Array) => values.fill(24) };
        }
        createMediaStreamSource() { return { connect: () => undefined }; }
        close() { this.state = "closed"; return Promise.resolve(); }
      }
      Object.defineProperty(window, "isSecureContext", { configurable: true, value: true });
      Object.defineProperty(window, "SpeechRecognition", { configurable: true, value: MockRecognition });
      Object.defineProperty(window, "webkitSpeechRecognition", { configurable: true, value: MockRecognition });
      Object.defineProperty(window, "AudioContext", { configurable: true, value: MockAudioContext });
      Object.defineProperty(navigator.mediaDevices, "getUserMedia", {
        configurable: true,
        value: async () => ({ getTracks: () => [{ stop: () => undefined }] }),
      });
    });
    await mockPagedGraph(page, []);
    await page.goto("/brain?graph=open");

    await page.getByRole("button", { name: "Use voice prompt" }).click();
    const stopButton = page.getByRole("button", { name: "Stop voice input" });
    await expect(stopButton).toBeVisible();
    await expect(stopButton.locator("span > span")).toHaveCount(5);
    const recognitionState = await page.evaluate(() => {
      const recognition = (window as typeof window & { __mockRecognition?: { onresult?: ((event: unknown) => void) | null; onend?: (() => void) | null } }).__mockRecognition;
      const state = { exists: Boolean(recognition), onresult: typeof recognition?.onresult, onend: typeof recognition?.onend };
      recognition?.onresult?.({ results: [[{ transcript: "show temporal series nodes" }]] });
      recognition?.onend?.();
      return state;
    });
    expect(recognitionState).toEqual({ exists: true, onresult: "function", onend: "function" });
    await expect(page.getByPlaceholder(/ask your graph/i)).toHaveValue("show temporal series nodes", { timeout: 3_000 });
  });

  test("node hover stays anchored, drag does not open, and click zooms before navigation", async ({ page }) => {
    test.setTimeout(60_000);
    const node = {
      id: "concept_11",
      recordId: 11,
      type: "concept",
      label: "A deliberately long temporal series forecasting concept label for responsive rendering",
      summary: "Forecasting methods connect temporal observations with predictive evidence.",
      status: "confirmed",
      semanticState: "ready",
      clusterId: 4,
      confidence: 0.88,
      createdBy: "ai",
    };
    await mockPagedGraph(page, [node]);
    await page.goto("/brain?graph=open");
    const canvas = page.getByRole("img", { name: /Knowledge graph with 1 nodes/i });
    await expect(canvas).toHaveAttribute("data-node-label-policy", "hover-selection-filter", { timeout: 30_000 });
    await expect(canvas).toHaveAttribute("data-node-border", "none");
    await expect(canvas).toHaveAttribute("data-drag-physics", "linked-neighbors");
    const tooltip = page.getByRole("tooltip");
    let hitPoint = { x: 0, y: 0 };
    // The single-node fixture is centered after layout. Re-read the canvas
    // bounds as the workspace settles; fixed sleeps can sample stale geometry.
    await expect(async () => {
      const box = await canvas.boundingBox();
      expect(box).not.toBeNull();
      hitPoint = { x: box!.x + box!.width / 2, y: box!.y + box!.height / 2 };
      await page.mouse.move(box!.x + 5, box!.y + 5);
      await page.mouse.move(hitPoint.x, hitPoint.y);
      await expect(tooltip).toBeVisible({ timeout: 750 });
    }).toPass({ timeout: 10_000 });
    await expect(tooltip).toContainText("Semantic state");
    await expect(tooltip).toContainText("Evidence support");
    await expect(tooltip).toContainText("88%");
    const tooltipBox = await tooltip.boundingBox();
    expect(Math.abs((tooltipBox?.x || 0) - hitPoint.x)).toBeLessThan(380);

    await page.mouse.move(hitPoint.x, hitPoint.y);
    await page.mouse.down();
    await page.mouse.move(hitPoint.x + 70, hitPoint.y + 40, { steps: 5 });
    await page.mouse.up();
    await expect(page).toHaveURL(/\/brain\?graph=open$/);

    // Wait for the drag click-suppression window; the released node stays pinned.
    await page.waitForTimeout(340);
    const releasedPoint = { x: hitPoint.x + 70, y: hitPoint.y + 40 };
    await page.mouse.move(releasedPoint.x, releasedPoint.y);
    await expect(tooltip).toBeVisible();
    await page.mouse.click(releasedPoint.x, releasedPoint.y);
    await expect(canvas).toHaveAttribute("data-selected-node", "concept_11");
    await page.waitForTimeout(180);
    await expect(page).toHaveURL(/\/brain\?graph=open$/);
    await expect(page).toHaveURL(/\/graph\/nodes\/11$/, { timeout: 15_000 });
  });

  test("graph ask can be saved as a graph insight proposal", async ({ page }) => {
    const insight = {
      id: 42,
      type: "new_connection",
      title: "Docker depends on Linux namespaces",
      description: "Docker evidence connects container isolation to Linux namespaces.",
      relatedNotes: [{ id: 1, title: "Docker and Linux Shell", path: "docker.md" }],
      relatedConcepts: ["Docker", "Linux namespaces"],
      priority: "high",
      suggestedAction: "Review the namespace evidence.",
      whyItMatters: "It explains the container boundary.",
      confidence: 0.91,
      status: "suggested",
      provider: "fixture",
      model: "fixture-model",
      createdAt: new Date().toISOString(),
    };

    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "answered",
          inferenceId: 99,
          question: "How does Docker isolate processes?",
          answer: "Docker uses Linux namespaces as part of process isolation.",
          evidence: [{ title: "Docker and Linux Shell", text: "Docker containers depend on Linux namespaces." }],
          relatedNodes: [{ id: 1, title: "Docker" }],
        }),
      }),
    );
    await page.route("**/api/v1/insights/from-inference", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ status: "created", insight }),
      }),
    );
    await page.route("**/api/v1/graph?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("How does Docker isolate processes?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Create insight" }).click();
    await expect(page.getByText("Saved as insight: Docker depends on Linux namespaces")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "Insight created" })).toBeVisible();
  });

  test("graph ask no evidence refusal", async ({ page }) => {
    await page.route("**/api/v1/graph/infer", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "insufficient_evidence",
          question: "Unknown topic",
          answer: "No evidence found to answer this question.",
          evidence: [],
        }),
      }),
    );

    await page.route("**/api/v1/graph?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
      }),
    );

    await page.goto("/brain?graph=open");
    await page.getByPlaceholder(/ask your graph/i).fill("Unknown topic");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect(page.getByText("No evidence", { exact: false })).toBeVisible({ timeout: 10_000 });
  });

  test("scan vault then graph appears", async ({ page }) => {
    let notesCreated = false;
    await mockGraphPages(page, () => ({
      nodes: notesCreated ? [{ id: "note_1", type: "note", label: "Test Note" }] : [],
      edges: [],
    }));

    await page.route("**/api/v1/vault/scan*", (route) => {
      notesCreated = true;
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ created: 1, updated: 0 }),
      });
    });

    await page.route("**/api/v1/graph?*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nodes: notesCreated ? [{ id: "note_1", type: "note", label: "Test Note" }] : [],
          edges: [],
          stats: { orphan_count: 0 },
        }),
      }),
    );

    await page.route("**/api/v1/vault/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ notes_total: notesCreated ? 1 : 0, graph_nodes: { all: notesCreated ? 1 : 0 }, diagnostics: notesCreated ? [] : [{ code: "NO_NOTES_SCANNED" }] }),
      }),
    );

    await page.route("**/api/v1/jobs/health", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", staleRunning: [] }) }),
    );

    await page.goto("/brain?graph=open");
    await page.evaluate(async () => {
      await fetch("/api/v1/vault/scan-and-rebuild", { method: "POST" });
    });
    await page.reload();
    await page.getByRole("button", { name: "Graph list" }).click();
    await expect(page.getByText("Test Note")).toBeVisible({ timeout: 10_000 });
  });

  test("graph list view mirrors API nodes and connections", async ({ page }) => {
    await mockPagedGraph(page, [
      { id: "note_1", type: "note", label: "Docker and Linux Shell", connectionsCount: 1 },
      { id: "concept_2", type: "concept", label: "Linux namespaces", connectionsCount: 1 },
    ], [
      {
        id: 10,
        source: "note_1",
        target: "concept_2",
        type: "mentions",
        confidence: 0.92,
        reason: "The note explicitly mentions Linux namespaces.",
        evidence: ["Docker containers depend on Linux namespaces."],
      },
    ]);
    await page.route("**/api/v1/vault/debug/vault-graph-pipeline", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ notes_total: 1, graph_nodes: { all: 2 }, diagnostics: [] }),
      }),
    );
    await page.route("**/api/v1/jobs/health", (route) =>
      route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", staleRunning: [] }) }),
    );

    await page.goto("/brain?graph=open");
    await expect(page.getByText(/2 Nodes · 1 Connections/i)).toBeVisible({
      timeout: 30_000,
    });
    await page.getByRole("button", { name: "Graph list" }).click();

    const listView = page.getByLabel("Knowledge graph list view");
    const nodesSection = listView.locator("section").filter({ hasText: "Nodes" });
    await expect(nodesSection.getByRole("listitem")).toHaveCount(2);
    await expect(nodesSection.getByText("Docker and Linux Shell")).toBeVisible();
    await expect(nodesSection.getByText("Linux namespaces")).toBeVisible();
    await expect(listView.getByText("Docker and Linux Shell → Linux namespaces")).toBeVisible();
  });

  test("continues a grounded answer in Flow and can cancel an active turn", async ({ page }) => {
    test.setTimeout(60_000);
    await mockPagedGraph(page, []);
    await page.route("**/api/v1/graph/infer", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        inferenceId: 71,
        status: "answered",
        question: "How are Docker and namespaces connected?",
        answer: "Docker uses Linux namespaces for isolation.",
        evidence: ["docker.md"],
      }),
    }));
    await page.route("**/api/v1/ask/sessions", async (route) => {
      expect((await route.request().postDataJSON()).inference_id).toBe(71);
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          session: { id: "session-e2e", active: true },
          turns: [
            { id: 1, role: "user", content: "How are Docker and namespaces connected?", evidenceIds: [] },
            { id: 2, role: "assistant", content: "Docker uses Linux namespaces for isolation.", evidenceIds: ["docker.md"], status: "completed" },
          ],
        }),
      });
    });
    let turnCount = 0;
    let releaseExitTurn: (() => void) | undefined;
    await page.route("**/api/v1/ask/sessions/session-e2e/turns", async (route) => {
      turnCount += 1;
      if (turnCount === 2) await new Promise((resolve) => setTimeout(resolve, 700));
      if (turnCount === 3) await new Promise<void>((resolve) => { releaseExitTurn = resolve; });
      const content = (await route.request().postDataJSON()).content;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          userTurn: { id: 2 + turnCount * 2 - 1, role: "user", content, evidenceIds: [] },
          assistantTurn: { id: 2 + turnCount * 2, role: "assistant", content: turnCount === 2 ? "Late answer must be ignored." : turnCount === 3 ? "Late exit answer must be ignored." : "They isolate process views.", evidenceIds: ["docker.md"], status: "completed", provider: "fixture", model: "fixture-model" },
        }),
      });
    });
    let cancellationRequested = false;
    await page.route("**/api/v1/ask/sessions/session-e2e/cancel", (route) => {
      cancellationRequested = true;
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "cancelling" }) });
    });
    let closeRequested = false;
    await page.route("**/api/v1/ask/sessions/session-e2e/close", (route) => {
      closeRequested = true;
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "closed" }) });
    });
    await page.route("**/api/v1/graph?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
    }));

    await page.goto("/brain?graph=open");
    const askInput = page.getByPlaceholder(/ask your graph/i);
    await askInput.fill("How are Docker and namespaces connected?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect(page.getByText("Docker uses Linux namespaces for isolation.")).toBeVisible();
    await page.getByRole("button", { name: "Continue in Flow" }).click();
    await expect(page.getByRole("button", { name: "Exit Flow · 1", exact: true })).toBeVisible();

    await askInput.fill("What does that isolate?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect(page.getByText("They isolate process views.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Exit Flow · 2", exact: true })).toBeVisible();

    await askInput.fill("Can this request be cancelled?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(page.getByText("Flow request cancelled.")).toBeVisible();
    expect(cancellationRequested).toBeTruthy();
    await page.waitForTimeout(800);
    await expect(page.getByText("Late answer must be ignored.")).toHaveCount(0);

    await askInput.fill("Exit while the provider is answering.");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect.poll(() => Boolean(releaseExitTurn)).toBe(true);
    await expect(page.getByRole("button", { name: "Cancel", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Exit Flow · 2", exact: true }).click();
    await expect(page.getByRole("button", { name: "Exit Flow · 2", exact: true })).toHaveCount(0);
    expect(closeRequested).toBeTruthy();
    releaseExitTurn?.();
    await page.waitForTimeout(800);
    await expect(page.getByText("Late exit answer must be ignored.")).toHaveCount(0);
  });

  test("runs graph gap research and reports completion", async ({ page }) => {
    await page.unroute("**/api/v1/settings");
    await page.route("**/api/v1/settings", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ settings: [
        { key: "onboarding_completed", value: "true" },
        { key: "research_mode_enabled", value: "true" },
      ] }),
    }));
    await page.route("**/api/v1/graph/research-runs", (route) => route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({ run: { id: 8, status: "running", progress: 10, completedQueries: 0 } }),
    }));
    await page.route("**/api/v1/graph/research-runs/8", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ run: { id: 8, status: "completed", progress: 100, completedQueries: 2 } }),
    }));
    await page.route("**/api/v1/graph?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
    }));

    await page.goto("/brain?graph=open");
    await page.getByRole("button", { name: "Knowledge", exact: true }).click();
    const researchGaps = page.getByRole("menuitem", { name: /Research Gaps/ });
    await expect(researchGaps).toBeEnabled();
    await researchGaps.click();
    await expect(page.getByText("Research completed. 2 queries checked.")).toBeVisible({ timeout: 5_000 });
  });

  test("opens the node page and queues a failed semantic analysis retry", async ({ page }) => {
    test.setTimeout(120_000);
    let deleted = false;
    await page.route("**/api/v1/graph/summary?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ node_count: deleted ? 0 : 1, edge_count: 0, orphan_count: deleted ? 0 : 1, graphVersion: deleted ? 6 : 5 }),
    }));
    await page.route("**/api/v1/graph/palette", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ colors: [] }),
    }));
    await page.route("**/api/v1/graph/nodes?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: deleted ? [] : [{ id: "concept_11", recordId: 11, type: "concept", label: "Docker", status: "suggested", semanticState: "failed" }], nextCursor: null, graphVersion: deleted ? 6 : 5 }),
    }));
    await page.route("**/api/v1/graph/edges?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ edges: [], nextCursor: null, graphVersion: 5 }),
    }));
    await page.route("**/api/v1/graph/delta?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ graphVersion: deleted ? 6 : 5, nodes: [], nodeCount: deleted ? 0 : 1, edgeCount: 0, requiresEdgeRefresh: false, requiresFullRefresh: deleted }),
    }));
    await page.route("**/api/v1/graph/nodes/11/summary", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 11, type: "concept", label: "Docker", title: "Docker", summary: "Container platform", status: "suggested", semanticState: "failed", confidenceInterval: { score: 0.8, lower: 0.6, upper: 0.9, sampleSize: 2, method: "empirical-bernstein-bounded-signals-v1" }, userNotes: "" }),
    }));
    await page.route("**/api/v1/graph/nodes/11/semantic-analysis", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ state: "failed", analysis: null, historyCount: 1, profileVersion: 1, sourceFingerprint: "fixture" }),
    }));
    await page.route("**/api/v1/graph/nodes/11/semantic-analysis/retry", (route) => route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ jobId: 404, status: "queued" }),
    }));
    let deleteCalls = 0;
    await page.route("**/api/v1/graph/nodes/11", (route) => {
      if (route.request().method() !== "DELETE") return route.fallback();
      deleteCalls += 1;
      deleted = true;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "deleted",
          jobs: { stats: 501, clusters: 502, insights: 503, retrieval: 504 },
          impact: { scope: "incident_subgraph", invalidatedInsights: 1 },
          message: "Node deleted. Dependent insights were invalidated and the affected subgraph is being recalculated.",
        }),
      });
    });
    await page.route("**/api/v1/jobs*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        jobs: [501, 502, 503, 504].map((id) => ({ id, status: "completed" })),
      }),
    }));

    await page.goto("/brain?graph=open");
    await page.getByRole("button", { name: "Graph list" }).click();
    const dockerNode = page.getByRole("listitem", { name: /Docker/ });
    await expect(dockerNode).toHaveAttribute("href", /\/graph\/nodes\/11$/);
    await dockerNode.click();
    await expect(page).toHaveURL(/\/graph\/nodes\/11$/, { timeout: 15_000 });
    await expect(page.getByText("The last analysis failed.")).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/Legacy interval midpoint/)).toBeVisible();
    await expect(page.getByRole("button", { name: "Back to Home" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Back to graph/i })).toBeVisible();
    const navigation = page.getByRole("complementary", { name: "Navigation" });
    await expect(navigation).toBeVisible();
    await expect(navigation.getByAltText("BerryBrain")).toBeVisible();
    const visibleText = await page.locator("body").innerText();
    for (const internalKey of [
      "layoutBrain",
      "filterBrainView",
      "manualNotePlaceholder",
      "saveManualNote",
      "sourceNotes",
      "loadingNodeSummary",
    ]) {
      expect(visibleText).not.toContain(internalKey);
    }
    await page.getByRole("button", { name: "Retry analysis" }).click();
    await expect(page.getByText("Semantic analysis queued. Job 404")).toBeVisible();
    await page.getByRole("button", { name: /Back to graph/i }).click();
    await expect(page).toHaveURL(/\/brain\?graph=open$/, { timeout: 15_000 });

    await page.goto("/graph/nodes/11");
    page.once("dialog", (dialog) => dialog.accept());
    await page.getByRole("button", { name: "Delete node" }).click();
    await expect(page).toHaveURL(/\/brain\?graph=open&refresh=node-deleted$/, { timeout: 15_000 });
    await expect(page.getByText("Node deletion and affected-subgraph recalculation completed.")).toBeVisible({ timeout: 45_000 });
    await page.reload();
    await page.getByRole("button", { name: "Graph list" }).click({ timeout: 45_000 });
    await expect(page.getByRole("listitem", { name: /Docker/ })).toHaveCount(0);
    expect(deleteCalls).toBe(1);
  });
});
