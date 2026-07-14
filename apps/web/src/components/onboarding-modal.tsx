"use client";

import { useEffect, useMemo, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";
import {
  BROWSER_STORAGE_MODE,
  getBrowserCloudConfig,
  saveBrowserCloudConfig,
} from "@/lib/browser-storage";
import { testBrowserCloudConnection } from "@/lib/browser-ai";

const NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1";
const CLOUD_PROVIDERS: Record<string, string> = {
  [NVIDIA_NIM_URL]: "NVIDIA NIM",
  "https://api.openai.com/v1": "OpenAI",
  "https://api.deepseek.com/v1": "DeepSeek",
  "https://api.groq.com/openai/v1": "Groq",
  "https://openrouter.ai/api/v1": "OpenRouter",
  "": "Custom OpenAI-compatible provider",
};

type MeResponse = {
  user?: { email?: string; displayName?: string };
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
    body: "Account settings let the local owner update profile data, change password, and revoke sessions.",
    bullets: ["Use the account button in the sidebar.", "Logout and sensitive updates require CSRF-protected requests.", "Danger operations stay behind authenticated owner controls."],
  },
];

export function OnboardingModal({ demo = false }: { demo?: boolean }) {
  const [show, setShow] = useState(false);
  const [step, setStep] = useState(0);
  const [phase, setPhase] = useState<"tour" | "ai">("tour");
  const [mode, setMode] = useState<"local" | "cloud">(() => BROWSER_STORAGE_MODE ? "cloud" : "local");
  const [modeSelected, setModeSelected] = useState(BROWSER_STORAGE_MODE);
  const [help, setHelp] = useState<"local" | "cloud" | null>(null);
  const [apiUrl, setApiUrl] = useState(NVIDIA_NIM_URL);
  const [customApiUrl, setCustomApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [localUrl, setLocalUrl] = useState("http://host.docker.internal:11434");
  const [localModel, setLocalModel] = useState("qwen3:8b");
  const [models, setModels] = useState<string[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [modelsError, setModelsError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    let alive = true;

    if (BROWSER_STORAGE_MODE) {
      getBrowserCloudConfig()
        .then((config) => {
          if (!alive) return;
          const tourSeen = localStorage.getItem("bb_tour_seen") === "1";
          if (config) {
            if (CLOUD_PROVIDERS[config.apiUrl]) setApiUrl(config.apiUrl);
            else {
              setApiUrl("");
              setCustomApiUrl(config.apiUrl);
            }
            setApiKey(config.apiKey);
            setModel(config.model);
            setModels([config.model]);
          }
          setStep(0);
          setPhase(tourSeen ? "ai" : "tour");
          setShow(!tourSeen || !config);
        })
        .catch(() => {
          if (!alive) return;
          setStep(0);
          setPhase("tour");
          setShow(true);
        });
      const openBrowserTour = () => {
        setStep(0);
        setPhase("tour");
        setShow(true);
      };
      window.addEventListener("bb:open-tour", openBrowserTour);
      return () => {
        alive = false;
        window.removeEventListener("bb:open-tour", openBrowserTour);
      };
    }

    function openTour() {
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then(() => {
          if (!alive) return;
          setStep(0);
          setPhase("tour");
          setShow(true);
        })
        .catch(() => {
          if (alive) setShow(true);
        });
    }

    // Legacy demo path can still open the guided flow, but the public demo route redirects.
    if (demo) {
      const tourSeen = localStorage.getItem("bb_tour_seen") === "1";
      const startDemo = () => {
        if (!alive) return;
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
    } else {
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then((r) => (r.ok ? r.json() : null))
        .then(async (me: MeResponse | null) => {
          if (!alive || !me?.user) return;
          const response = await fetch(`${getApiUrl()}/api/v1/settings`, {
            credentials: "include",
          });
          if (response.ok) {
            const data = await response.json();
            const completed = data?.settings?.some(
              (setting: { key?: string; value?: string }) =>
                setting.key === "onboarding_completed" && setting.value === "true",
            );
            if (completed) return;
          }
          setStep(0);
          setPhase("tour");
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

  const steps = useMemo(() => baseSteps, []);
  const isConfigStep = phase === "ai";
  const cloudUrl = (apiUrl || customApiUrl).trim();
  const aiConfigured =
    modeSelected &&
      (mode === "local"
        ? Boolean(localUrl.trim()) && Boolean(localModel.trim())
        : Boolean(cloudUrl) && Boolean(apiKey.trim()) && Boolean(model.trim()));
  const total = steps.length;
  const progress = isConfigStep ? 100 : Math.round(((step + 1) / total) * 100);
  const isLastTourStep = step === steps.length - 1;

  async function loadModels() {
    const url = cloudUrl;
    setLoadingModels(true);
    setModelsError("");
    try {
      if (BROWSER_STORAGE_MODE) {
        const data = await testBrowserCloudConnection(url, apiKey.trim());
        const ids = data.models;
        setModels(ids);
        if (!model.trim()) setModel(ids[0] || "");
        return;
      }
      const r = await fetch(`${getApiUrl()}/api/v1/settings/ai/models`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, key: apiKey.trim() }),
      });
      const data = await r.json();
      if (!r.ok || !data.connected) throw new Error(data.error || data.detail || "Provider connection failed");
      const ids: string[] = Array.isArray(data?.models)
        ? data.models.map((m: { id?: string }) => m?.id).filter(Boolean)
        : [];
      setModels(ids);
      if (!model.trim()) setModel(ids[0] || "");
    } catch (err) {
      setModelsError(err instanceof Error ? err.message : "Failed to load models");
    } finally {
      setLoadingModels(false);
    }
  }

  async function finish(provider: "local" | "cloud" = mode) {
    setSaving(true);
    setSaveError("");
    if (BROWSER_STORAGE_MODE) {
      try {
        const connection = await testBrowserCloudConnection(cloudUrl, apiKey.trim());
        await saveBrowserCloudConfig({
          provider: CLOUD_PROVIDERS[cloudUrl] || connection.provider,
          apiUrl: connection.providerUrl,
          apiKey,
          model,
        });
        localStorage.setItem("bb_ai_provider", "cloud");
        localStorage.setItem("bb_graph_ai_provider", "cloud");
        localStorage.setItem("bb_ai_api_url", connection.providerUrl);
        localStorage.setItem("bb_graph_ai_api_url", connection.providerUrl);
        localStorage.setItem("bb_ai_model", model.trim());
        localStorage.setItem("bb_graph_ai_model", model.trim());
        localStorage.setItem("bb_remote_content_consent", "true");
        localStorage.setItem("bb_tour_seen", "1");
        localStorage.setItem("bb_onboarding_completed", "true");
        window.dispatchEvent(new CustomEvent("bb:cloud-configured"));
        setShow(false);
      } catch (error) {
        setSaveError(error instanceof Error ? error.message : "The cloud provider could not be configured.");
      } finally {
        setSaving(false);
      }
      return;
    }
    const url = apiUrl.trim() || NVIDIA_NIM_URL;
    const values: Record<string, string> = {
      ai_provider: provider,
      graph_ai_provider: provider,
      ai_api_url: provider === "cloud" ? url : "",
      graph_ai_api_url: provider === "cloud" ? url : "",
      ai_api_key: provider === "cloud" ? apiKey.trim() : "",
      graph_ai_api_key: provider === "cloud" ? apiKey.trim() : "",
      ai_model: provider === "cloud" ? model.trim() : "",
      graph_ai_model: provider === "cloud" ? model.trim() : "",
      ollama_base_url: provider === "local" ? localUrl.trim() : "",
      ollama_model: provider === "local" ? localModel.trim() : "",
      graph_ollama_model: provider === "local" ? localModel.trim() : "",
      remote_content_consent: provider === "cloud" ? "true" : "false",
      onboarding_completed: "true",
    };
    try {
      const response = await fetch(`${getApiUrl()}/api/v1/settings/batch`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ values }),
      });
      if (!response.ok) throw new Error("Settings could not be saved.");
      localStorage.setItem("bb_ai_provider", provider);
      localStorage.setItem("bb_graph_ai_provider", provider);
      if (provider === "cloud") {
        localStorage.setItem("bb_ai_api_url", url);
        localStorage.setItem("bb_graph_ai_api_url", url);
        localStorage.setItem("bb_ai_model", model.trim());
        localStorage.setItem("bb_graph_ai_model", model.trim());
      } else {
        localStorage.setItem("bb_graph_ollama_model", localModel.trim());
      }
      localStorage.removeItem("bb_ai_api_key");
      localStorage.removeItem("bb_graph_ai_api_key");
      localStorage.removeItem("bb_onboarded");
      setShow(false);
    } catch (error) {
      setSaveError(error instanceof Error ? error.message : "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  function skip() {
    setPhase("ai");
  }

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
      <div className="bb-card bb-card--elevated flex max-h-[88vh] w-full max-w-[92vw] flex-col overflow-hidden text-foreground sm:max-w-2xl">
        <div className="border-b border-border px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">
                {isConfigStep ? (BROWSER_STORAGE_MODE ? "Required cloud setup" : "AI setup") : steps[step].eyebrow}
              </p>
              <h2 className="mt-1 text-xl font-semibold tracking-tight">
                {isConfigStep
                  ? BROWSER_STORAGE_MODE
                    ? "Connect a cloud AI provider to continue."
                    : "Choose how BerryBrain uses AI."
                  : steps[step].title}
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
                {BROWSER_STORAGE_MODE
                  ? "Your notes stay in IndexedDB in this browser. Your chosen cloud provider supplies cognitive processing while the tab is open; its API key stays in this browser and is excluded from exports."
                  : "Local mode keeps processing on your machine through Ollama. Cloud mode uses an OpenAI-compatible provider for graph enrichment and insights."}
              </p>
              {!BROWSER_STORAGE_MODE && <div className="mt-5 grid grid-cols-2 gap-2">
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
              </div>}

              {BROWSER_STORAGE_MODE && (
                <div className="mt-4 rounded-md border border-accent/40 bg-surface px-3 py-3 text-xs leading-5 text-muted">
                  Cloud AI is mandatory in the hosted web app. Processing resumes when BerryBrain is open; no note database or provider key is stored by BerryBrain servers.
                </div>
              )}

              {mode === "local" && modeSelected && (
                <div className="mt-4 grid gap-3">
                  <label className="block text-xs text-muted">
                    Ollama URL
                    <input
                      value={localUrl}
                      onChange={(event) => setLocalUrl(event.target.value)}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                      placeholder="http://host.docker.internal:11434"
                    />
                  </label>
                  <label className="block text-xs text-muted">
                    Ollama model
                    <input
                      value={localModel}
                      onChange={(event) => setLocalModel(event.target.value)}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                      placeholder="Select or enter an installed model"
                    />
                    <span className="mt-1 block text-[11px] text-muted">
                      The model must already be available in your Ollama installation.
                    </span>
                  </label>
                </div>
              )}

              {(mode === "cloud" || BROWSER_STORAGE_MODE) && (
                <div className="mt-4 grid gap-3">
                  <label className="block text-xs text-muted">
                    Cloud provider
                    <select
                      value={apiUrl}
                      onChange={(e) => { setApiUrl(e.target.value); setModels([]); setModel(""); }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                    >
                      {Object.entries(CLOUD_PROVIDERS).map(([url, label]) => (
                        <option key={url || "custom"} value={url}>{label}</option>
                      ))}
                    </select>
                  </label>
                  {apiUrl === "" && (
                    <label className="block text-xs text-muted">
                      Custom API base URL
                      <input
                        value={customApiUrl}
                        onChange={(e) => { setCustomApiUrl(e.target.value); setModels([]); setModel(""); }}
                        className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent"
                        placeholder="https://provider.example/v1"
                      />
                    </label>
                  )}
                  <label className="block text-xs text-muted">
                    Cloud API Key
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
                            {m}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={loadModels}
                        disabled={loadingModels}
                        className="bb-action shrink-0 px-3 py-2 text-xs"
                      >
                        {loadingModels ? "Loading…" : "Load models"}
                      </button>
                    </div>
                    {modelsError && <span className="mt-1 block text-xs text-red-400">{modelsError}</span>}
                    <span className="mt-1 block text-[11px] text-muted">Models are loaded from your cloud provider account.</span>
                  </label>
                </div>
              )}
              {saveError && (
                <p role="alert" className="mt-4 rounded-md border border-red-400/30 bg-red-400/10 px-3 py-2 text-xs text-red-400">
                  {saveError}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t border-border px-6 py-4">
          <div className="text-xs text-muted">
            {isConfigStep ? (BROWSER_STORAGE_MODE ? "Cloud AI required" : "AI setup") : `Step ${step + 1} of ${total}`}
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
              className="bb-action px-4 py-2 text-sm"
            >
              Back
            </button>
            {!isConfigStep ? (
              <button
                onClick={() => (isLastTourStep ? setPhase("ai") : setStep((current) => current + 1))}
                className="bb-action px-4 py-2 text-sm font-medium"
              >
                {isLastTourStep ? "Set up AI" : "Continue"}
              </button>
            ) : (
              <button
                onClick={() => finish(mode)}
                disabled={!aiConfigured || saving}
                className="bb-action px-4 py-2 text-sm font-medium"
              >
                {saving ? "Connecting…" : BROWSER_STORAGE_MODE ? "Connect and open workspace" : "Finish"}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
