"use client";

import { useEffect, useMemo, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";

const NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1";
const RECOMMENDED_MODEL = "qwen/qwen3.5-397b-instruct";

type MeResponse = {
  user?: { email?: string; displayName?: string };
  isAdmin?: boolean;
};

type TourStep = {
  title: string;
  eyebrow: string;
  body: string;
  bullets: string[];
};

const baseSteps: TourStep[] = [
  {
    eyebrow: "Start",
    title: "Capture first, organize later.",
    body: "BerryBrain starts from plain Markdown notes. Write quickly, link ideas with [[note links]], and let the system build structure around your material.",
    bullets: ["Use New note or Ctrl+K to create notes.", "Drafts are saved in the vault as real files.", "Your note language and wording stay untouched."],
  },
  {
    eyebrow: "Autopilot",
    title: "Watch the pipeline instead of guessing.",
    body: "After notes change, jobs parse, classify, extract concepts, build embeddings, find connections, and expand the graph.",
    bullets: ["Open Monitor to inspect queued and failed jobs.", "Use Activity for a readable history.", "Use Scan vault after importing files externally."],
  },
  {
    eyebrow: "Graph",
    title: "Use the graph as the working map.",
    body: "The graph is where notes, concepts, entities, topics, gaps, and insights become inspectable.",
    bullets: ["Ask the graph a question from the top bar.", "Click a node to review evidence and actions.", "Confirm good nodes and ignore weak suggestions."],
  },
  {
    eyebrow: "Insights",
    title: "Turn evidence into next actions.",
    body: "Insights surface gaps, patterns, hypotheses, and possible contradictions grounded in graph evidence.",
    bullets: ["Review confidence before applying.", "Create notes or reviews from useful insights.", "Ignore low-value suggestions to keep the graph clean."],
  },
  {
    eyebrow: "Account",
    title: "Keep identity and sessions under control.",
    body: "Account settings let you update profile data, change password, change email, manage 2FA, and revoke sessions.",
    bullets: ["Use the account button in the sidebar.", "Logout and sensitive updates require CSRF-protected requests.", "Admins get a dedicated user-management area."],
  },
];

const adminStep: TourStep = {
  eyebrow: "Admin",
  title: "Admin access follows the configured account.",
  body: "The admin panel only opens for the authenticated account whose email matches BERRYBRAIN_ADMIN_EMAIL.",
  bullets: ["Use /admin to review users and audit events.", "Lock, unlock, revoke sessions, and reset passwords from one place.", "Every admin mutation is audited and CSRF-protected."],
};

export function OnboardingModal({ demo = false }: { demo?: boolean }) {
  const [show, setShow] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [step, setStep] = useState(0);
  const [phase, setPhase] = useState<"tour" | "ai">("tour");
  const [mode, setMode] = useState<"local" | "cloud">("local");
  const [modeSelected, setModeSelected] = useState(false);
  const [help, setHelp] = useState<"local" | "cloud" | null>(null);
  const [apiUrl, setApiUrl] = useState(NVIDIA_NIM_URL);
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    let alive = true;

    function openTour() {
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then((me: MeResponse | null) => {
          if (!alive) return;
          setIsAdmin(Boolean(me?.isAdmin));
          setStep(0);
          setPhase("tour");
          setShow(true);
        })
        .catch(() => {
          if (alive) setShow(true);
        });
    }

    // Demo: the AI setup is mandatory on every refresh, exactly like a
    // normal non-admin login. The tour is shown only once (first visit).
    // Admins never auto-show — they open on demand via "bb:open-tour".
    if (demo) {
      const tourSeen = localStorage.getItem("bb_tour_seen") === "1";
      const startDemo = () => {
        if (!alive) return;
        setIsAdmin(false);
        if (tourSeen) {
          setPhase("ai");
        } else {
          localStorage.setItem("bb_tour_seen", "1");
          setPhase("tour");
        }
        setShow(true);
      };
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then(() => startDemo())
        .catch(() => startDemo());
    } else if (localStorage.getItem("bb_onboarded") !== "1") {
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then((me: MeResponse | null) => {
          if (!alive || !me?.user) return;
          if (me.isAdmin) return;
          setIsAdmin(false);
          setPhase("ai");
          setShow(true);
        })
        .catch(() => {});
    }
    window.addEventListener("bb:open-tour", openTour);
    return () => {
      alive = false;
      window.removeEventListener("bb:open-tour", openTour);
    };
  }, [demo]);

  const steps = useMemo(() => (isAdmin ? [...baseSteps, adminStep] : baseSteps), [isAdmin]);
  const isConfigStep = phase === "ai";
  const aiConfigured = modeSelected && (mode === "local" || (mode === "cloud" && Boolean(apiKey.trim()) && Boolean(model.trim())));
  const total = steps.length;
  const progress = isConfigStep ? 100 : Math.round(((step + 1) / total) * 100);
  const isLastTourStep = step === steps.length - 1;

  async function loadModels() {
    const url = apiUrl.trim() || NVIDIA_NIM_URL;
    setLoadingModels(true);
    setModelsError("");
    try {
      const params = new URLSearchParams({ url, key: apiKey.trim() });
      const r = await fetch(`${getApiUrl()}/api/v1/ai/models?${params}`);
      const data = await r.json();
      if (data.error) throw new Error(data.error);
      const ids: string[] = Array.isArray(data?.models)
        ? data.models.map((m: { id?: string }) => m?.id).filter(Boolean)
        : [];
      if (!ids.includes(RECOMMENDED_MODEL)) ids.unshift(RECOMMENDED_MODEL);
      setModels(ids);
      if (!model.trim()) setModel(RECOMMENDED_MODEL);
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : "Failed to load models");
    } finally {
      setLoadingModels(false);
    }
  }

  function finish(provider: "local" | "cloud" = mode) {
    localStorage.setItem("bb_ai_provider", provider);
    localStorage.setItem("bb_graph_ai_provider", provider);
    if (provider === "cloud") {
      const url = apiUrl.trim() || NVIDIA_NIM_URL;
      localStorage.setItem("bb_ai_api_url", url);
      localStorage.setItem("bb_graph_ai_api_url", url);
      localStorage.setItem("bb_ai_api_key", apiKey.trim());
      localStorage.setItem("bb_graph_ai_api_key", apiKey.trim());
      localStorage.setItem("bb_ai_model", model.trim());
      localStorage.setItem("bb_graph_ai_model", model.trim());
    }
    localStorage.setItem("bb_onboarded", "1");
    setShow(false);
  }

  function skip() {
    // Only admins can dismiss entirely. Every other user — real or demo —
    // must configure AI first: skipping the tour jumps straight to the
    // mandatory AI setup phase.
    if (!isAdmin) {
      setPhase("ai");
      return;
    }
    localStorage.setItem("bb_onboarded", "1");
    setShow(false);
  }

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
      <div className="flex max-h-[88vh] w-full max-w-[92vw] flex-col overflow-hidden rounded-lg border border-border bg-panel text-foreground shadow-2xl sm:max-w-2xl">
        <div className="border-b border-border px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">
                {isConfigStep ? "AI setup" : steps[step].eyebrow}
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight">
                {isConfigStep ? "Choose how BerryBrain uses AI." : steps[step].title}
              </h2>
            </div>
            {!isConfigStep && (
              <button onClick={skip} className="rounded-md px-2 py-1 text-xs text-muted hover:bg-surface hover:text-foreground">
                Skip
              </button>
            )}
          </div>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-surface">
            <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${progress}%` }} />
          </div>
        </div>

        <div className="overflow-y-auto px-6 py-5">
          {!isConfigStep ? (
            <div>
              <p className="max-w-xl text-sm leading-6 text-muted">{steps[step].body}</p>
              <div className="mt-5 grid gap-2">
                {steps[step].bullets.map((bullet) => (
                  <div key={bullet} className="flex gap-3 rounded-md border border-border bg-surface px-3 py-2 text-sm">
                    <span className="mt-1 size-1.5 shrink-0 rounded-full bg-accent" />
                    <span className="leading-6 text-muted">{bullet}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div>
              <p className="max-w-xl text-sm leading-6 text-muted">
                Local mode keeps processing on your machine through Ollama. Cloud mode uses an OpenAI-compatible provider for graph enrichment and insights.
              </p>
              <div className="mt-5 grid grid-cols-2 gap-2">
                <div className={`rounded-md border px-3 py-3 text-left text-sm ${mode === "local" ? "border-accent bg-surface" : "border-border"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <button onClick={() => { setMode("local"); setModeSelected(true); }} className="block flex-1 text-left font-medium">
                      Local
                    </button>
                    <button
                      type="button"
                      aria-label="How local mode works"
                      onClick={() => setHelp((h) => (h === "local" ? null : "local"))}
                      className="flex size-5 shrink-0 items-center justify-center rounded-full border border-border text-xs text-muted hover:text-foreground"
                    >
                      ?
                    </button>
                  </div>
                  <span className="mt-1 block text-xs leading-5 text-muted">Use Ollama and keep provider calls off by default.</span>
                  {help === "local" && (
                    <ul className="mt-2 grid gap-1 border-t border-border pt-2 text-[11px] leading-5 text-muted">
                      <li>1. Install Ollama and start it (ollama serve).</li>
                      <li>2. Pull a model, e.g. ollama pull qwen3:14b.</li>
                      <li>3. Nothing leaves your machine; no API key needed.</li>
                    </ul>
                  )}
                </div>
                <div className={`rounded-md border px-3 py-3 text-left text-sm ${mode === "cloud" ? "border-accent bg-surface" : "border-border"}`}>
                  <div className="flex items-center justify-between gap-2">
                    <button onClick={() => { setMode("cloud"); setModeSelected(true); }} className="block flex-1 text-left font-medium">
                      Cloud API
                    </button>
                    <button
                      type="button"
                      aria-label="How cloud mode works"
                      onClick={() => setHelp((h) => (h === "cloud" ? null : "cloud"))}
                      className="flex size-5 shrink-0 items-center justify-center rounded-full border border-border text-xs text-muted hover:text-foreground"
                    >
                      ?
                    </button>
                  </div>
                  <span className="mt-1 block text-xs leading-5 text-muted">Use NVIDIA NIM or another compatible provider.</span>
                  {help === "cloud" && (
                    <ul className="mt-2 grid gap-1 border-t border-border pt-2 text-[11px] leading-5 text-muted">
                      <li>1. Get an API key from your provider (e.g. NVIDIA NIM).</li>
                      <li>2. Paste the provider URL and key below.</li>
                      <li>3. Click Load models and pick the recommended one.</li>
                    </ul>
                  )}
                </div>
              </div>

              {mode === "cloud" && (
                <div className="mt-4 grid gap-3">
                  <label className="block text-xs text-muted">
                    Provider URL
                    <input
                      value={apiUrl}
                      onChange={(e) => setApiUrl(e.target.value)}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                      placeholder={NVIDIA_NIM_URL}
                    />
                  </label>
                  <label className="block text-xs text-muted">
                    API key
                    <input
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      type="password"
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                      placeholder="Paste your provider key"
                    />
                  </label>
                  <label className="block text-xs text-muted">
                    Model
                    <div className="mt-1 flex gap-2">
                      <select
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                        className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                      >
                        <option value="">Select a model…</option>
                        {models.map((m) => (
                          <option key={m} value={m}>
                            {m === RECOMMENDED_MODEL ? `${m} (recommended)` : m}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={loadModels}
                        disabled={loadingModels}
                        className="shrink-0 rounded-md border border-border px-3 py-2 text-xs text-muted hover:text-foreground disabled:opacity-50"
                      >
                        {loadingModels ? "Loading…" : "Load models"}
                      </button>
                    </div>
                    {modelsError && <span className="mt-1 block text-xs text-red-400">{modelsError}</span>}
                    <span className="mt-1 block text-[11px] text-muted">Recommended: {RECOMMENDED_MODEL}</span>
                  </label>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border px-6 py-4">
          <div className="text-xs text-muted">
            {isConfigStep ? "AI setup" : `Step ${step + 1} of ${total}`}
          </div>
          <div className="flex gap-2">
            <button
              disabled={!isConfigStep && step === 0}
              onClick={() => {
                if (isConfigStep) {
                  setPhase("tour");
                  setStep(steps.length - 1);
                } else {
                  setStep((current) => Math.max(0, current - 1));
                }
              }}
              className="rounded-md border border-border px-4 py-2 text-sm text-muted hover:text-foreground disabled:opacity-40"
            >
              Back
            </button>
            {!isConfigStep ? (
              <button
                onClick={() => (isLastTourStep ? setPhase("ai") : setStep((current) => current + 1))}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-black"
              >
                {isLastTourStep ? "Set up AI" : "Continue"}
              </button>
            ) : (
              <button
                onClick={() => finish(mode)}
                disabled={!isAdmin && !aiConfigured}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-50"
              >
                Finish
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
