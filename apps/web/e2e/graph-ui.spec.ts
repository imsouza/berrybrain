import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

async function mockPagedGraph(page: Page, nodes: Record<string, unknown>[], edges: Record<string, unknown>[] = []) {
  await page.route("**/api/v1/graph/summary", (route) => route.fulfill({
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
    await page.route("**/api/v1/settings", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ settings: [{ key: "onboarding_completed", value: "true" }] }),
      }),
    );
  });

  test("settles a 42-node D3 bubble graph from a compact animated start", async ({ page }) => {
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
    await page.route("**/api/v1/graph", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes, edges, graphVersion: 42, stats: { orphan_count: 0 } }),
    }));

    await page.goto("/brain?graph=open");
    const canvas = page.getByRole("img", { name: /Knowledge graph with 42 nodes/i });
    await expect(canvas).toBeVisible();
    await expect(canvas).toHaveAttribute("data-layout-engine", "d3-force-v7");
    await expect(canvas).toHaveAttribute("data-velocity-decay", "0.15");
    await expect(canvas).toHaveAttribute("data-collision-padding", "11");
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

    await page.route("**/api/v1/graph", (route) =>
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
    await expect(canvas).toHaveAttribute("data-node-label-max-lines", "3");
    await expect(canvas).toHaveAttribute("data-node-label-max-characters", "58");
    await page.waitForTimeout(900);
    const box = await canvas.boundingBox();
    expect(box).not.toBeNull();
    const center = { x: box!.x + box!.width / 2, y: box!.y + box!.height / 2 };

    await page.mouse.move(center.x, center.y);
    const tooltip = page.getByRole("tooltip");
    await expect(tooltip).toContainText("Semantic state");
    await expect(tooltip).toContainText("Confidence");
    const tooltipBox = await tooltip.boundingBox();
    expect(Math.abs((tooltipBox?.x || 0) - center.x)).toBeLessThan(380);

    await page.mouse.move(center.x, center.y);
    await page.mouse.down();
    await page.mouse.move(center.x + 70, center.y + 40, { steps: 5 });
    await page.mouse.up();
    await page.waitForTimeout(750);
    await expect(page).toHaveURL(/\/brain\?graph=open$/);

    await page.mouse.click(center.x + 70, center.y + 40);
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
    await page.route("**/api/v1/graph", (route) =>
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

    await page.route("**/api/v1/graph", (route) =>
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

    await page.route("**/api/v1/vault/scan*", (route) => {
      notesCreated = true;
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ created: 1, updated: 0 }),
      });
    });

    await page.route("**/api/v1/graph", (route) =>
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

    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
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
    await page.getByRole("button", { name: "List view" }).click();
    await expect(page.getByText("Test Note")).toBeVisible({ timeout: 10_000 });
  });

  test("graph list view mirrors API nodes and connections", async ({ page }) => {
    await page.route("**/api/v1/graph", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nodes: [
            { id: "note_1", type: "note", label: "Docker and Linux Shell", connectionsCount: 1 },
            { id: "concept_2", type: "concept", label: "Linux namespaces", connectionsCount: 1 },
          ],
          edges: [
            {
              id: 10,
              source: "note_1",
              target: "concept_2",
              type: "mentions",
              confidence: 0.92,
              reason: "The note explicitly mentions Linux namespaces.",
              evidence: ["Docker containers depend on Linux namespaces."],
            },
          ],
          stats: { node_count: 2, edge_count: 1, orphan_count: 0 },
        }),
      }),
    );
    await page.route("**/api/v1/debug/vault-graph-pipeline", (route) =>
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
      timeout: 10_000,
    });
    await page.getByRole("button", { name: "List view" }).click();

    const listView = page.getByLabel("Knowledge graph list view");
    const nodesSection = listView.locator("section").filter({ hasText: "Nodes" });
    await expect(nodesSection.getByRole("listitem")).toHaveCount(2);
    await expect(nodesSection.getByText("Docker and Linux Shell")).toBeVisible();
    await expect(nodesSection.getByText("Linux namespaces")).toBeVisible();
    await expect(listView.getByText("Docker and Linux Shell → Linux namespaces")).toBeVisible();
  });

  test("continues a grounded answer in Flow and can cancel an active turn", async ({ page }) => {
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
    await page.route("**/api/v1/ask/sessions/session-e2e/turns", async (route) => {
      turnCount += 1;
      if (turnCount === 2) await new Promise((resolve) => setTimeout(resolve, 700));
      const content = (await route.request().postDataJSON()).content;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          userTurn: { id: 2 + turnCount * 2 - 1, role: "user", content, evidenceIds: [] },
          assistantTurn: { id: 2 + turnCount * 2, role: "assistant", content: "They isolate process views.", evidenceIds: ["docker.md"], status: "completed", provider: "fixture", model: "fixture-model" },
        }),
      });
    });
    let cancellationRequested = false;
    await page.route("**/api/v1/ask/sessions/session-e2e/cancel", (route) => {
      cancellationRequested = true;
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "cancelling" }) });
    });
    await page.route("**/api/v1/graph", (route) => route.fulfill({
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
    await expect(page.getByRole("button", { name: "Exit Flow · 1 turns" })).toBeVisible();

    await askInput.fill("What does that isolate?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await expect(page.getByText("They isolate process views.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Exit Flow · 2 turns" })).toBeVisible();

    await askInput.fill("Can this request be cancelled?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(page.getByText("Flow request cancellation requested.")).toBeVisible();
    expect(cancellationRequested).toBeTruthy();
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
    await page.route("**/api/v1/graph", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: [], edges: [], stats: { orphan_count: 0 } }),
    }));

    await page.goto("/brain?graph=open");
    const researchGaps = page.getByRole("button", { name: "Research gaps" });
    await expect(researchGaps).toBeEnabled();
    await researchGaps.click();
    await expect(page.getByRole("button", { name: "Researching gaps 10%" })).toBeVisible();
    await expect(page.getByText("Research completed. 2 queries checked.")).toBeVisible({ timeout: 5_000 });
  });

  test("opens the node page and queues a failed semantic analysis retry", async ({ page }) => {
    test.setTimeout(60_000);
    await page.route("**/api/v1/graph/summary", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ node_count: 1, edge_count: 0, orphan_count: 1, graphVersion: 5 }),
    }));
    await page.route("**/api/v1/graph/palette", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ colors: [] }),
    }));
    await page.route("**/api/v1/graph/nodes?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ nodes: [{ id: "note_11", recordId: 11, type: "note", label: "Docker", status: "suggested", semanticState: "failed" }], nextCursor: null, graphVersion: 5 }),
    }));
    await page.route("**/api/v1/graph/edges?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ edges: [], nextCursor: null, graphVersion: 5 }),
    }));
    await page.route("**/api/v1/graph/delta?*", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ graphVersion: 5, nodes: [], nodeCount: 1, edgeCount: 0, requiresEdgeRefresh: false, requiresFullRefresh: false }),
    }));
    await page.route("**/api/v1/graph/nodes/11/summary", (route) => route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ id: 11, type: "note", label: "Docker", title: "Docker", summary: "Container platform", status: "suggested", semanticState: "failed", confidenceInterval: { score: 0.8, lower: 0.6, upper: 0.9, sampleSize: 2, method: "wilson-evidence-v1" }, userNotes: "" }),
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

    await page.goto("/brain?graph=open");
    await page.getByRole("button", { name: "List view" }).click();
    const dockerNode = page.getByRole("listitem", { name: /Docker/ });
    await expect(dockerNode).toHaveAttribute("href", /\/graph\/nodes\/11$/);
    await dockerNode.click();
    await expect(page).toHaveURL(/\/graph\/nodes\/11$/, { timeout: 15_000 });
    await expect(page.getByText("The last analysis failed.")).toBeVisible({ timeout: 15_000 });
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
  });
});
