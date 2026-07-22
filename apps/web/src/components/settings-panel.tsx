"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { LangKind, getLang, t, tf } from "../i18n";
import { readCsrf } from "./public-site/user-menu";

type ThemeKind = "light" | "dark";

const THEME_PRESETS: Record<ThemeKind, { bg: string; fg: string; mu: string; pn: string; bd: string }> = {
  light: { bg: "#F7F6F3", fg: "#1A1A1A", mu: "#6B6B6B", pn: "#FFFFFF", bd: "#E0E0E0" },
  dark: { bg: "#121212", fg: "#E8E8E8", mu: "#9A9A9A", pn: "#1E1E1E", bd: "#333333" },
};

const UI_FONTS: Record<string, string> = {
  inter: '"Inter", ui-sans-serif, system-ui, sans-serif',
  system: "ui-sans-serif, system-ui, -apple-system, sans-serif",
};

const EDITOR_FONTS: Record<string, string> = {
  mono: '"JetBrains Mono", "Fira Code", ui-monospace, monospace',
  sans: "ui-sans-serif, system-ui, sans-serif",
};

const NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1";

const CLOUD_PROVIDERS: Record<string, string> = {
  [NVIDIA_NIM_URL]: "NVIDIA NIM",
  "https://api.openai.com/v1": "OpenAI",
  "https://api.deepseek.com/v1": "DeepSeek",
  "https://api.groq.com/openai/v1": "Groq",
  "https://openrouter.ai/api/v1": "OpenRouter",
  "": "Custom provider URL",
};

type Settings = {
  theme: ThemeKind;
  lang: LangKind;
  font_size: string;
  editor_font_size: string;
  ui_font: string;
  editor_font: string;
  nome: string;
  ai_provider: "local" | "cloud";
  ai_api_url: string;
  ai_custom_url: string;
  ai_api_key: string;
  ai_model: string;
  graph_ai_provider: "local" | "cloud";
  graph_ai_api_url: string;
  graph_ai_api_key: string;
  graph_ai_model: string;
  ollama_base_url: string;
  graph_ollama_model: string;
  graph_auto_confirm_confidence: string;
  graph_default_layout: "brain" | "radial" | "type" | "connections";
  kb_vector_store: "sqlite" | "qdrant" | "chroma";
  kb_embedding_provider: "local" | "cloud";
  kb_embedding_model: string;
  kb_chunk_size: string;
  kb_chunk_overlap: string;
  qdrant_url: string;
  qdrant_collection: string;
  chroma_url: string;
  chroma_collection: string;
  cognitive_retrieval_mode: "hybrid" | "kb_first" | "graph_first";
  semantic_data_enabled: "true" | "false";
  cognitive_enrich_on_save: "true" | "false";
  cognitive_insights_on_save: "true" | "false";
  research_mode_enabled: "true" | "false";
  remote_content_consent: "true" | "false";
  attachment_image_limit_mb: string;
  attachment_video_limit_mb: string;
  attachment_audio_limit_mb: string;
  attachment_other_limit_mb: string;
  attachment_ocr_language: string;
  attachment_transcription_executable: "faster-whisper" | "whisper";
  attachment_transcription_model: string;
};

type AiProviderStatus = {
  state: "local" | "incomplete" | "disabled" | "configured" | "connected" | "failed";
  provider: string;
  providerMode: "local" | "cloud";
  keyConfigured: boolean;
  modelConfigured: boolean;
  model: string;
  graphProviderMode: "local" | "cloud";
  graphKeyConfigured: boolean;
  graphModelConfigured: boolean;
  graphModel: string;
  remoteContentConsent: boolean;
  lastTestStatus: string;
  lastTestAt?: string | null;
  lastTestLatencyMs?: number | null;
  lastError?: string;
};

function defaults(): Settings {
  return {
    theme: "light",
    lang: "en",
    font_size: "15",
    editor_font_size: "15",
    ui_font: "inter",
    editor_font: "mono",
    nome: "Owner",
    ai_provider: "local",
    ai_api_url: NVIDIA_NIM_URL,
    ai_custom_url: "",
    ai_api_key: "",
    ai_model: "",
    graph_ai_provider: "local",
    graph_ai_api_url: NVIDIA_NIM_URL,
    graph_ai_api_key: "",
    graph_ai_model: "",
    ollama_base_url: "http://host.docker.internal:11434",
    graph_ollama_model: "qwen3:8b",
    graph_auto_confirm_confidence: "0.9",
    graph_default_layout: "brain",
    kb_vector_store: "sqlite",
    kb_embedding_provider: "local",
    kb_embedding_model: "",
    kb_chunk_size: "900",
    kb_chunk_overlap: "120",
    qdrant_url: "",
    qdrant_collection: "berrybrain",
    chroma_url: "",
    chroma_collection: "berrybrain",
    cognitive_retrieval_mode: "hybrid",
    semantic_data_enabled: "true",
    cognitive_enrich_on_save: "true",
    cognitive_insights_on_save: "true",
    research_mode_enabled: "false",
    remote_content_consent: "false",
    attachment_image_limit_mb: "10",
    attachment_video_limit_mb: "200",
    attachment_audio_limit_mb: "50",
    attachment_other_limit_mb: "25",
    attachment_ocr_language: "eng",
    attachment_transcription_executable: "faster-whisper",
    attachment_transcription_model: "/opt/berrybrain/models/faster-whisper-tiny.en",
  };
}

function loadSettings(): Settings {
  if (typeof window === "undefined") return defaults();
  const d = defaults();
  return {
    theme: (localStorage.getItem("bb_theme") as ThemeKind) || d.theme,
    lang: "en",
    font_size: localStorage.getItem("bb_font_size") || d.font_size,
    editor_font_size: localStorage.getItem("bb_editor_font_size") || d.editor_font_size,
    ui_font: localStorage.getItem("bb_ui_font") || d.ui_font,
    editor_font: localStorage.getItem("bb_editor_font") || d.editor_font,
    nome: localStorage.getItem("bb_nome") || d.nome,
    ai_provider: (localStorage.getItem("bb_ai_provider") as Settings["ai_provider"]) || d.ai_provider,
    ai_api_url: localStorage.getItem("bb_ai_api_url") || d.ai_api_url,
    ai_custom_url: localStorage.getItem("bb_ai_custom_url") || d.ai_custom_url,
    ai_api_key: d.ai_api_key,
    ai_model: localStorage.getItem("bb_ai_model") || d.ai_model,
    graph_ai_provider: (localStorage.getItem("bb_graph_ai_provider") as Settings["graph_ai_provider"]) || d.graph_ai_provider,
    graph_ai_api_url: localStorage.getItem("bb_graph_ai_api_url") || d.graph_ai_api_url,
    graph_ai_api_key: d.graph_ai_api_key,
    graph_ai_model: localStorage.getItem("bb_graph_ai_model") || d.graph_ai_model,
    ollama_base_url: localStorage.getItem("bb_ollama_base_url") || d.ollama_base_url,
    graph_ollama_model: localStorage.getItem("bb_graph_ollama_model") || d.graph_ollama_model,
    graph_auto_confirm_confidence: localStorage.getItem("bb_graph_auto_confirm_confidence") || d.graph_auto_confirm_confidence,
    graph_default_layout: (localStorage.getItem("bb_graph_default_layout") as Settings["graph_default_layout"]) || d.graph_default_layout,
    kb_vector_store: (localStorage.getItem("bb_kb_vector_store") as Settings["kb_vector_store"]) || d.kb_vector_store,
    kb_embedding_provider: (localStorage.getItem("bb_kb_embedding_provider") as Settings["kb_embedding_provider"]) || d.kb_embedding_provider,
    kb_embedding_model: localStorage.getItem("bb_kb_embedding_model") || d.kb_embedding_model,
    kb_chunk_size: localStorage.getItem("bb_kb_chunk_size") || d.kb_chunk_size,
    kb_chunk_overlap: localStorage.getItem("bb_kb_chunk_overlap") || d.kb_chunk_overlap,
    qdrant_url: localStorage.getItem("bb_qdrant_url") || d.qdrant_url,
    qdrant_collection: localStorage.getItem("bb_qdrant_collection") || d.qdrant_collection,
    chroma_url: localStorage.getItem("bb_chroma_url") || d.chroma_url,
    chroma_collection: localStorage.getItem("bb_chroma_collection") || d.chroma_collection,
    cognitive_retrieval_mode: (localStorage.getItem("bb_cognitive_retrieval_mode") as Settings["cognitive_retrieval_mode"]) || d.cognitive_retrieval_mode,
    semantic_data_enabled: (localStorage.getItem("bb_semantic_data_enabled") as Settings["semantic_data_enabled"]) || d.semantic_data_enabled,
    cognitive_enrich_on_save: (localStorage.getItem("bb_cognitive_enrich_on_save") as Settings["cognitive_enrich_on_save"]) || d.cognitive_enrich_on_save,
    cognitive_insights_on_save: (localStorage.getItem("bb_cognitive_insights_on_save") as Settings["cognitive_insights_on_save"]) || d.cognitive_insights_on_save,
    research_mode_enabled: (localStorage.getItem("bb_research_mode_enabled") as Settings["research_mode_enabled"]) || d.research_mode_enabled,
    remote_content_consent: (localStorage.getItem("bb_remote_content_consent") as Settings["remote_content_consent"]) || d.remote_content_consent,
    attachment_image_limit_mb: localStorage.getItem("bb_attachment_image_limit_mb") || d.attachment_image_limit_mb,
    attachment_video_limit_mb: localStorage.getItem("bb_attachment_video_limit_mb") || d.attachment_video_limit_mb,
    attachment_audio_limit_mb: localStorage.getItem("bb_attachment_audio_limit_mb") || d.attachment_audio_limit_mb,
    attachment_other_limit_mb: localStorage.getItem("bb_attachment_other_limit_mb") || d.attachment_other_limit_mb,
    attachment_ocr_language: localStorage.getItem("bb_attachment_ocr_language") || d.attachment_ocr_language,
    attachment_transcription_executable: (localStorage.getItem("bb_attachment_transcription_executable") as Settings["attachment_transcription_executable"]) || d.attachment_transcription_executable,
    attachment_transcription_model: localStorage.getItem("bb_attachment_transcription_model") || d.attachment_transcription_model,
  };
}

function applyTheme(s: Settings) {
  const r = document.documentElement;
  const p = THEME_PRESETS[s.theme] || THEME_PRESETS.light;
  r.setAttribute("data-theme", s.theme);
  r.style.setProperty("--color-background", p.bg);
  r.style.setProperty("--color-foreground", p.fg);
  r.style.setProperty("--color-muted", p.mu);
  r.style.setProperty("--color-panel", p.pn);
  r.style.setProperty("--color-border", p.bd);
  r.style.setProperty("--color-accent", "#96B55C");
  r.style.setProperty("--color-brand-green", "#96B55C");
  r.style.setProperty("--color-brand-red", "#CC4168");
  r.style.setProperty("--color-danger", "#CC4168");
  r.style.setProperty("--font-ui", UI_FONTS[s.ui_font] || UI_FONTS.inter);
  r.style.setProperty("--font-editor", EDITOR_FONTS[s.editor_font] || EDITOR_FONTS.mono);
  document.body.style.fontSize = `${s.font_size}px`;
  document.body.style.fontFamily = "var(--font-ui)";
  document.documentElement.lang = "en";
}

export function initTheme() {
  applyTheme(loadSettings());
}
export { getLang, t };

const SETTING_KEYS: (keyof Settings)[] = [
  "theme",
  "lang",
  "font_size",
  "editor_font_size",
  "ui_font",
  "editor_font",
  "nome",
  "ai_provider",
  "ai_api_url",
  "ai_custom_url",
  "ai_api_key",
  "ai_model",
  "graph_ai_provider",
  "graph_ai_api_url",
  "graph_ai_api_key",
  "graph_ai_model",
  "ollama_base_url",
  "graph_ollama_model",
  "graph_auto_confirm_confidence",
  "graph_default_layout",
  "kb_vector_store",
  "kb_embedding_provider",
  "kb_embedding_model",
  "kb_chunk_size",
  "kb_chunk_overlap",
  "qdrant_url",
  "qdrant_collection",
  "chroma_url",
  "chroma_collection",
  "cognitive_retrieval_mode",
  "semantic_data_enabled",
  "cognitive_enrich_on_save",
  "cognitive_insights_on_save",
  "research_mode_enabled",
  "remote_content_consent",
  "attachment_image_limit_mb",
  "attachment_video_limit_mb",
  "attachment_audio_limit_mb",
  "attachment_other_limit_mb",
  "attachment_ocr_language",
  "attachment_transcription_executable",
  "attachment_transcription_model",
];

const SECRET_SETTING_KEYS = new Set<keyof Settings>(["ai_api_key", "graph_ai_api_key"]);

export function SettingsPanel({ open, onClose, apiUrl }: { open: boolean; onClose: () => void; apiUrl: string }) {
  const [s, setS] = useState<Settings>(loadSettings);
  const editedRef = useRef(false);
  const providerChoiceRef = useRef<Settings["ai_provider"] | null>(null);
  const cloudConnectionEditedRef = useRef(false);
  const cloudConnectionVerifiedRef = useRef(false);
  const cloudTestRevisionRef = useRef("");
  const [saving, setSaving] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [isAdmin, setIsAdmin] = useState(false);
  const [apiKeyConfigured, setApiKeyConfigured] = useState(false);
  const [graphApiKeyConfigured, setGraphApiKeyConfigured] = useState(false);
  const [providerStatus, setProviderStatus] = useState<AiProviderStatus | null>(null);
  const [cloudModels, setCloudModels] = useState<{ id: string }[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState("");
  const [maintenanceStatus, setMaintenanceStatus] = useState("");
  const [diagnostics, setDiagnostics] = useState<{ staleRunning: any[]; failedByType: Record<string, number>; status: string } | null>(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagClearing, setDiagClearing] = useState(false);
  const [diagClearResult, setDiagClearResult] = useState("");

  const selectedProviderLabel = useMemo(() => CLOUD_PROVIDERS[s.ai_api_url] || "Custom provider", [s.ai_api_url]);

  useEffect(() => {
    if (!open) return;
    editedRef.current = false;
    providerChoiceRef.current = null;
    cloudConnectionEditedRef.current = false;
    cloudConnectionVerifiedRef.current = false;
    cloudTestRevisionRef.current = "";
    setSaveStatus("");
    if (apiUrl === "__demo__") {
      setIsAdmin(false);
      return;
    }
    let cancelled = false;
    setSettingsLoading(true);
    fetch(`${apiUrl}/api/v1/auth/me`, { credentials: "include" })
      .then((r) => (r.ok ? r.json() : null))
      .then((me) => {
        const admin = Boolean(me?.isAdmin);
        if (cancelled) return;
        setIsAdmin(admin);
        if (!admin) return;
        return Promise.all([
          fetch(`${apiUrl}/api/v1/settings`, { credentials: "include" }),
          fetch(`${apiUrl}/api/v1/settings/ai/status`, { credentials: "include" }),
        ]).then(async ([settingsResponse, statusResponse]) => {
            if (!settingsResponse.ok) throw new Error("Settings could not be loaded.");
            const d = await settingsResponse.json();
            const loaded: Partial<Settings> = {};
            for (const item of d.settings || []) {
              const key = String(item.key) as keyof Settings;
              if (key === "ai_api_key") setApiKeyConfigured(Boolean(item.configured));
              else if (key === "graph_ai_api_key") setGraphApiKeyConfigured(Boolean(item.configured));
              else if (SETTING_KEYS.includes(key)) (loaded as Record<string, string>)[key] = item.value;
            }
            if (!cancelled && !editedRef.current) setS((prev) => ({ ...prev, ...loaded, lang: "en" }));
            if (statusResponse.ok && !cancelled) {
              const status = await statusResponse.json();
              setProviderStatus(status);
              cloudConnectionVerifiedRef.current = status.lastTestStatus === "connected";
            }
          });
      })
      .catch((error) => {
        if (!cancelled) setSaveStatus(error instanceof Error ? error.message : "Settings could not be loaded.");
      })
      .finally(() => {
        if (!cancelled) setSettingsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [open, apiUrl]);

  useEffect(() => {
    if (!open) return;
    if (apiUrl === "__demo__") {
      setDiagnostics(null);
      return;
    }
    setDiagLoading(true);
    fetch(`${apiUrl}/api/v1/jobs/health`)
      .then((r) => r.json())
      .then((d) => setDiagnostics({ staleRunning: d.staleRunning || [], failedByType: d.failedByType || {}, status: d.status || "unknown" }))
      .catch(() => setDiagnostics(null))
      .finally(() => setDiagLoading(false));
  }, [open, apiUrl]);

  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    editedRef.current = true;
    setSaveStatus("");
    if (["ai_api_url", "ai_custom_url", "ai_api_key", "ai_model"].includes(String(key))) {
      cloudConnectionEditedRef.current = true;
      cloudConnectionVerifiedRef.current = false;
      cloudTestRevisionRef.current = "";
    }
    setS((previous) => {
      const next: Settings = { ...previous, [key]: value, lang: "en" };
      if (key === "ai_api_key" && String(value)) next.graph_ai_api_key = String(value);
      if (key === "ai_provider") {
        providerChoiceRef.current = value as Settings["ai_provider"];
        next.graph_ai_provider = value as Settings["graph_ai_provider"];
        if (value === "local") next.remote_content_consent = "false";
      }
      if (key === "ai_model" && (!previous.graph_ai_model || previous.graph_ai_model === previous.ai_model)) next.graph_ai_model = String(value);
      if (key === "ai_api_url" && (!previous.graph_ai_api_url || previous.graph_ai_api_url === previous.ai_api_url)) next.graph_ai_api_url = String(value);
      if (key === "ai_custom_url" && !previous.ai_api_url) next.graph_ai_api_url = String(value);
      if (["theme", "font_size", "ui_font", "editor_font"].includes(String(key))) applyTheme(next);
      return next;
    });
  }

  async function refreshProviderStatus() {
    if (apiUrl === "__demo__" || !isAdmin) return;
    const response = await fetch(`${apiUrl}/api/v1/settings/ai/status`, { credentials: "include" });
    if (response.ok) setProviderStatus(await response.json());
  }

  async function persist(next = s) {
    const values: Record<string, string> = {};
    SETTING_KEYS.forEach((key) => {
      if (SECRET_SETTING_KEYS.has(key)) localStorage.removeItem(`bb_${key}`);
      else localStorage.setItem(`bb_${key}`, String(next[key]));
      if (!SECRET_SETTING_KEYS.has(key) || String(next[key]).trim()) values[key] = String(next[key]);
    });
    if (!isAdmin || apiUrl === "__demo__") return;
    const response = await fetch(`${apiUrl}/api/v1/settings/batch`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
      credentials: "include",
      body: JSON.stringify({ values, aiTestRevision: cloudTestRevisionRef.current }),
    });
    if (!response.ok) throw new Error("Settings could not be saved.");
  }

  async function save() {
    setSaving(true);
    setSaveStatus("");
    try {
      const baseUrl = (s.ai_api_url || s.ai_custom_url).trim();
      const hasCloudKey = Boolean(s.ai_api_key.trim()) || apiKeyConfigured;
      const hasCloudModel = Boolean(s.ai_model.trim());
      const wantsCloud = s.ai_provider === "cloud";
      let next = s;

      if (wantsCloud && (!baseUrl || !hasCloudKey || !hasCloudModel)) {
        setSaveStatus("Cloud setup is incomplete. Add an API URL, API key, and model before saving.");
        return;
      }

      const needsConsent = wantsCloud && s.remote_content_consent !== "true";
      if (needsConsent) {
        const confirmed = window.confirm(
          `Enable ${selectedProviderLabel} processing?\n\nBerryBrain will send note, attachment, and graph content to the configured cloud API for AI processing. This consent is saved and will not be requested again unless cloud processing is disabled.`,
        );
        if (!confirmed) {
          setSaveStatus("Save cancelled. Cloud AI was not enabled.");
          return;
        }
        next = {
          ...s,
          ai_provider: "cloud",
          graph_ai_provider: "cloud",
          graph_ai_api_url: baseUrl,
          graph_ai_model: s.graph_ai_model || s.ai_model,
          remote_content_consent: "true",
        };
      }

      const needsConnectionTest = wantsCloud && !cloudConnectionVerifiedRef.current && (
        needsConsent || cloudConnectionEditedRef.current || providerStatus?.lastTestStatus !== "connected"
      );
      if (needsConnectionTest && !(await testCloudConnection(next, false))) return;

      await persist(next);
      applyTheme(next);
      if (next.ai_api_key) setApiKeyConfigured(true);
      if (next.graph_ai_api_key) setGraphApiKeyConfigured(true);
      setS({ ...next, ai_api_key: "", graph_ai_api_key: "" });
      editedRef.current = false;
      providerChoiceRef.current = null;
      cloudConnectionEditedRef.current = false;
      cloudTestRevisionRef.current = "";
      setSaveStatus(wantsCloud ? `Settings saved. ${selectedProviderLabel} is active.` : "Settings saved.");
      await refreshProviderStatus();
    } catch (error) {
      setSaveStatus(error instanceof Error ? error.message : "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function fetchModels() {
    await testCloudConnection(s, true);
  }

  async function testCloudConnection(next: Settings, announceSuccess: boolean): Promise<boolean> {
    if (apiUrl === "__demo__") {
      setConnectionStatus("Provider testing is disabled in demo mode.");
      return false;
    }
    const baseUrl = next.ai_api_url || next.ai_custom_url;
    setLoadingModels(true);
    setConnectionStatus("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/settings/ai/models`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
        body: JSON.stringify({ url: baseUrl, key: next.ai_api_key, model: next.ai_model }),
      });
      const payload = await response.json();
      if (!response.ok || !payload.connected) {
        setCloudModels(payload.models || []);
        if (payload.requiresModel) {
          setConnectionStatus(payload.error || "Models loaded. Select a model, then test again.");
          setSaveStatus("");
          return false;
        }
        setConnectionStatus(`Connection failed: ${payload.error || payload.detail || "Provider unavailable."}`);
        setSaveStatus("Settings were not saved because the cloud connection could not be verified.");
        return false;
      } else {
        setCloudModels(payload.models || []);
        const latency = payload.latencyMs ? ` (${payload.latencyMs} ms)` : "";
        if (announceSuccess) {
          setConnectionStatus((payload.models || []).length ? `Connection verified${latency}. Select a model, then click Save to activate it.` : `Connection verified${latency}, but no models were returned.`);
        }
        await refreshProviderStatus();
        cloudConnectionVerifiedRef.current = true;
        cloudTestRevisionRef.current = String(payload.keyRevision || "");
        return true;
      }
    } catch (error: any) {
      setCloudModels([]);
      setConnectionStatus(`Connection failed: ${error.message}`);
      setSaveStatus("Settings were not saved because the cloud connection could not be verified.");
      return false;
    } finally {
      setLoadingModels(false);
    }
  }

  async function clearCloudKey() {
    if (!window.confirm("Clear the saved cloud API key? AI cloud processing will stop until a new key is configured.")) return;
    const response = await fetch(`${apiUrl}/api/v1/settings/ai/key`, {
      method: "DELETE",
      credentials: "include",
      headers: { "X-CSRF-Token": readCsrf() },
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      setConnectionStatus(payload.detail || "The API key could not be cleared.");
      return;
    }
    setApiKeyConfigured(false);
    setGraphApiKeyConfigured(false);
    cloudConnectionVerifiedRef.current = false;
    setS((previous) => ({ ...previous, ai_api_key: "", graph_ai_api_key: "" }));
    setCloudModels([]);
    setConnectionStatus("Cloud API key cleared.");
    await refreshProviderStatus();
  }

  function preserveLocalSettings() {
    const preserved = new Map<string, string>();
    for (const key of SETTING_KEYS) {
      const storageKey = `bb_${key}`;
      const value = localStorage.getItem(storageKey);
      if (value !== null) preserved.set(storageKey, value);
    }
    localStorage.clear();
    for (const [key, value] of preserved) localStorage.setItem(key, value);
    sessionStorage.clear();
  }

  function resetLocalSettings() {
    localStorage.clear();
    sessionStorage.clear();
    const next = defaults();
    setS(next);
    applyTheme(next);
  }

  async function wipeAll(resetSettings: boolean) {
    if (apiUrl === "__demo__") {
      setConnectionStatus("Danger Zone actions are disabled in demo mode.");
      return;
    }
    const label = resetSettings
      ? "DELETE EVERYTHING and reset Settings to defaults"
      : "DELETE EVERYTHING but keep current Settings";
    const confirmed = window.confirm(
      `${label}?\n\nThis deletes notes, graph, embeddings, insights, jobs, notifications and vault files. This cannot be undone.`,
    );
    if (!confirmed) return;
    setConnectionStatus("Wiping BerryBrain data...");
    const response = await fetch(`${apiUrl}/api/v1/settings/danger/wipe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reset_settings: resetSettings }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      setConnectionStatus(payload.detail || "Wipe failed.");
      return;
    }
    if (resetSettings) resetLocalSettings();
    else preserveLocalSettings();
    setConnectionStatus(resetSettings ? "Everything wiped. Settings reset. Reloading..." : "Everything wiped. Settings preserved. Reloading...");
    window.setTimeout(() => window.location.reload(), 700);
  }

  async function runMaintenance(action: "rebuild-brain" | "cleanup-legacy-insights" | "validate-graph" | "reindex-knowledge-base") {
    if (apiUrl === "__demo__") {
      setMaintenanceStatus("Maintenance actions are disabled in demo mode.");
      return;
    }
    const labels: Record<typeof action, string> = {
      "rebuild-brain": "Rebuild second brain",
      "cleanup-legacy-insights": "Cleanup legacy technical insights",
      "validate-graph": "Validate graph consistency",
      "reindex-knowledge-base": "Reindex knowledge base",
    };
    const confirmed = window.confirm(`${labels[action]}?\n\nThis does not delete note files. It may queue processing jobs and update graph/insight metadata.`);
    if (!confirmed) return;
    setMaintenanceStatus(`${labels[action]} running...`);
    try {
      const response = await fetch(`${apiUrl}/api/v1/maintenance/${action}`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setMaintenanceStatus(payload.detail || `${labels[action]} failed.`);
        return;
      }
      const counts = Object.entries(payload)
        .filter(([, value]) => typeof value === "number")
        .map(([key, value]) => `${key}: ${value}`)
        .join(" · ");
      setMaintenanceStatus(`${labels[action]} completed.${counts ? ` ${counts}` : ""}`);
    } catch (error: any) {
      setMaintenanceStatus(error.message || `${labels[action]} failed.`);
    }
  }

  async function clearStuckJobs() {
    if (apiUrl === "__demo__") {
      setDiagClearResult("Diagnostics are disabled in demo mode.");
      return;
    }
    setDiagClearing(true);
    setDiagClearResult("");
    try {
      const r = await fetch(`${apiUrl}/api/v1/jobs/recover-stale`, { method: "POST" });
      const d = await r.json().catch(() => ({}));
      if (!r.ok) { setDiagClearResult(t("clearedFail")); return; }
      setDiagClearResult(tf("clearedOk", { count: d.recovered ?? 0 }));
      setDiagnostics((prev) => prev ? { ...prev, staleRunning: [] } : prev);
    } catch { setDiagClearResult(t("clearedFail")); }
    finally { setDiagClearing(false); }
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-8">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" onClick={onClose} />
      <div className="bb-card bb-card--elevated relative z-50 w-full max-w-[92vw] overflow-hidden text-foreground sm:w-[560px]" role="dialog" aria-label="Settings">
        <div className="flex items-center justify-between border-b border-border/45 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold tracking-tight">Settings</h2>
            <p className="mt-0.5 text-xs text-muted/70">Configure appearance, editor, AI providers, and saving behavior.</p>
          </div>
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface hover:text-foreground" onClick={onClose} aria-label="Close settings">x</button>
        </div>

        <div className="max-h-[72vh] space-y-5 overflow-y-auto px-6 py-5">
          <Section title="Appearance" description="Interface identity and theme.">
            <Field label="Display name" description="Used in the Home greeting.">
              <TextInput value={s.nome} onChange={(value) => update("nome", value)} placeholder="Your name" />
            </Field>
            <Field label="Theme" description="Current visual mode.">
              <Select value={s.theme} onChange={(value) => update("theme", value as ThemeKind)}>
                <option value="">Select a theme</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </Select>
            </Field>
            <Field label="Language" description="The application UI is English-only. User notes keep their original language.">
              <ReadOnlyValue value="English" />
            </Field>
          </Section>

          <Section title="Font" description="Readable text across the application.">
            <Field label="UI font" description="Used by menus, cards, and navigation.">
              <Select value={s.ui_font} onChange={(value) => update("ui_font", value)}>
                <option value="">Select a font</option>
                {Object.keys(UI_FONTS).map((font) => <option key={font} value={font}>{labelize(font)}</option>)}
              </Select>
            </Field>
            <Field label={`UI font size: ${s.font_size}px`} description="Controls the base interface size.">
              <Range value={s.font_size} min="12" max="20" onChange={(value) => update("font_size", value)} />
            </Field>
          </Section>

          <Section title="Editor" description="Writing surface and markdown editing.">
            <Field label="Editor font" description="Used inside the markdown editor.">
              <Select value={s.editor_font} onChange={(value) => update("editor_font", value)}>
                <option value="">Select an editor font</option>
                {Object.keys(EDITOR_FONTS).map((font) => <option key={font} value={font}>{labelize(font)}</option>)}
              </Select>
            </Field>
            <Field label={`Editor font size: ${s.editor_font_size}px`} description="Controls markdown editor text size.">
              <Range value={s.editor_font_size} min="13" max="22" onChange={(value) => update("editor_font_size", value)} />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Image attachment limit (MB)" description="Maximum size for images attached to notes.">
                <TextInput value={s.attachment_image_limit_mb} onChange={(value) => update("attachment_image_limit_mb", value)} placeholder="10" />
              </Field>
              <Field label="Video attachment limit (MB)" description="Maximum size for videos attached to notes.">
                <TextInput value={s.attachment_video_limit_mb} onChange={(value) => update("attachment_video_limit_mb", value)} placeholder="200" />
              </Field>
              <Field label="Audio attachment limit (MB)" description="Maximum size for audio files attached to notes.">
                <TextInput value={s.attachment_audio_limit_mb} onChange={(value) => update("attachment_audio_limit_mb", value)} placeholder="50" />
              </Field>
              <Field label="Other attachment limit (MB)" description="Maximum size for PDFs, archives, documents, and any other file type.">
                <TextInput value={s.attachment_other_limit_mb} onChange={(value) => update("attachment_other_limit_mb", value)} placeholder="25" />
              </Field>
            </div>
            <ReadOnlyValue value="Markdown toolbar and split preview are enabled." />
          </Section>

          <Section title="Attachment processing" description="Local OCR and transcription used to turn files into evidence.">
            <Field label="OCR language" description="Installed Tesseract code, such as eng, por, or por+eng. Settings do not download language packs; verify them with tesseract --list-langs in the API container.">
              <TextInput value={s.attachment_ocr_language} onChange={(value) => update("attachment_ocr_language", value)} placeholder="eng or por+eng" />
            </Field>
            <Field label="Transcription engine" description="Faster Whisper is bundled and local. Custom CLI requires a compatible executable in the API image.">
              <Select value={s.attachment_transcription_executable} onChange={(value) => update("attachment_transcription_executable", value as Settings["attachment_transcription_executable"])}>
                <option value="faster-whisper">Faster Whisper (bundled, local)</option>
                <option value="whisper">Whisper CLI (custom)</option>
              </Select>
            </Field>
            <Field label="Transcription model" description="Local Faster Whisper model path or model name used by the configured engine.">
              <TextInput value={s.attachment_transcription_model} onChange={(value) => update("attachment_transcription_model", value)} placeholder="/opt/berrybrain/models/faster-whisper-tiny.en" />
            </Field>
          </Section>

          <Section title="AI / Provider" description="Choose which provider BerryBrain uses for AI processing.">
            <Field label="AI provider" description="Cloud uses NVIDIA NIM or another compatible API. Local uses Ollama.">
              <Select value={s.ai_provider} onChange={(value) => update("ai_provider", value as Settings["ai_provider"])}>
                <option value="">Select a provider</option>
                <option value="cloud">Cloud provider</option>
                <option value="local">Local Ollama</option>
              </Select>
            </Field>
            <Field label="Graph inference provider" description="Controls AI answers in the graph screen.">
              <Select value={s.graph_ai_provider} onChange={(value) => update("graph_ai_provider", value as Settings["graph_ai_provider"])}>
                <option value="">Select a graph provider</option>
                <option value="cloud">Cloud provider</option>
                <option value="local">Local Ollama</option>
              </Select>
            </Field>
            <Field label="Cloud processing consent" description="Requested once when Save activates a cloud provider. Selecting Local Ollama disables it.">
              <ReadOnlyValue value={s.remote_content_consent === "true" ? "Enabled — configured cloud processing is allowed" : "Not granted — confirmation will appear when cloud settings are saved"} />
            </Field>
          </Section>

          <Section title="Cloud AI" description="OpenAI-compatible provider used for graph inference, insights, and knowledge expansion.">
            <ProviderConnectionStatus status={providerStatus} loading={settingsLoading} />
            <Field label="Cloud API provider" description={`Current provider: ${selectedProviderLabel}.`}>
              <Select value={s.ai_api_url} onChange={(value) => update("ai_api_url", value)}>
                <option value="">Select a provider</option>
                {Object.entries(CLOUD_PROVIDERS).map(([url, label]) => <option key={url || "custom"} value={url}>{label}</option>)}
              </Select>
            </Field>
            {s.ai_api_url === "" && (
              <Field label="Custom API base URL" description="OpenAI-compatible endpoint.">
                <TextInput value={s.ai_custom_url} onChange={(value) => update("ai_custom_url", value)} placeholder="https://example.com/v1" />
              </Field>
            )}
            <Field
              label={`${selectedProviderLabel} API Key`}
              description={apiKeyConfigured ? "A key is saved securely. Enter a new key only to replace it." : "The key is stored by the BerryBrain API and is never returned to the browser."}
            >
              <div className="flex flex-wrap gap-2">
                <TextInput
                  type={showKey ? "text" : "password"}
                  value={s.ai_api_key}
                  onChange={(value) => update("ai_api_key", value)}
                  placeholder={apiKeyConfigured ? "Saved securely — enter a new key to replace it" : `Paste your ${selectedProviderLabel} API key`}
                />
                <button className="bb-action h-9 px-3 text-xs" onClick={() => setShowKey((value) => !value)}>
                  {showKey ? "Hide" : "Show"}
                </button>
                <button className="bb-action h-9 px-3 text-xs font-medium" disabled={(!s.ai_api_key && !apiKeyConfigured) || loadingModels} onClick={fetchModels}>
                  {loadingModels ? "Testing..." : "Test connection"}
                </button>
                {(apiKeyConfigured || graphApiKeyConfigured) && (
                  <button className="bb-action h-9 px-3 text-xs" onClick={clearCloudKey}>Clear key</button>
                )}
              </div>
            </Field>
            <Field label="Cloud model" description="Model used by the main AI pipeline.">
              <Select value={s.ai_model} onChange={(value) => update("ai_model", value)}>
                <option value="">Select a model</option>
                {cloudModels.map((model) => <option key={model.id} value={model.id}>{model.id}</option>)}
                {s.ai_model && !cloudModels.some((model) => model.id === s.ai_model) && <option value={s.ai_model}>{s.ai_model}</option>}
              </Select>
            </Field>
            <Field label="Graph cloud model" description="Model used by graph questions and graph insight generation.">
              <TextInput value={s.graph_ai_model} onChange={(value) => update("graph_ai_model", value)} placeholder="Select or type a graph model" />
            </Field>
            {connectionStatus && <p className="rounded-xl bg-surface px-3 py-2 text-xs text-muted ring-1 ring-border/40">{connectionStatus}</p>}
          </Section>

          <Section title="Cognitive Layer" description="Configure the BerryBrain Knowledge System: Knowledge Base, Knowledge Graph, semantic state, and retrieval orchestration.">
            <Field label="Knowledge Base vector store" description="SQLite is local fallback. Qdrant and Chroma are supported as configurable external stores.">
              <Select value={s.kb_vector_store} onChange={(value) => update("kb_vector_store", value as Settings["kb_vector_store"])}>
                <option value="">Select a vector store</option>
                <option value="sqlite">SQLite local fallback</option>
                <option value="qdrant">Qdrant</option>
                <option value="chroma">Chroma</option>
              </Select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Qdrant URL" description="Used when the vector store is Qdrant.">
                <TextInput value={s.qdrant_url} onChange={(value) => update("qdrant_url", value)} placeholder="http://localhost:6333" />
              </Field>
              <Field label="Qdrant collection" description="Collection for BerryBrain chunks.">
                <TextInput value={s.qdrant_collection} onChange={(value) => update("qdrant_collection", value)} placeholder="berrybrain" />
              </Field>
              <Field label="Chroma URL" description="Used when the vector store is Chroma.">
                <TextInput value={s.chroma_url} onChange={(value) => update("chroma_url", value)} placeholder="http://localhost:8001" />
              </Field>
              <Field label="Chroma collection" description="Collection for BerryBrain chunks.">
                <TextInput value={s.chroma_collection} onChange={(value) => update("chroma_collection", value)} placeholder="berrybrain" />
              </Field>
            </div>
            <Field label="Embedding provider" description="Cloud uses the configured compatible API. Local uses Ollama.">
              <Select value={s.kb_embedding_provider} onChange={(value) => update("kb_embedding_provider", value as Settings["kb_embedding_provider"])}>
                <option value="">Select an embedding provider</option>
                <option value="cloud">Cloud provider</option>
                <option value="local">Local Ollama</option>
              </Select>
            </Field>
            <Field label="Embedding model" description="Model used for semantic search chunks. Required to move embeddings above zero.">
              <TextInput value={s.kb_embedding_model} onChange={(value) => update("kb_embedding_model", value)} placeholder="Example: nvidia/llama-3.2-nv-embedqa-1b-v2 or bge-m3" />
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Chunk size" description="Maximum characters per markdown chunk.">
                <TextInput value={s.kb_chunk_size} onChange={(value) => update("kb_chunk_size", value)} placeholder="900" />
              </Field>
              <Field label="Chunk overlap" description="Reserved for vector stores that support overlapping chunks.">
                <TextInput value={s.kb_chunk_overlap} onChange={(value) => update("kb_chunk_overlap", value)} placeholder="120" />
              </Field>
            </div>
            <Field label="Retrieval mode" description="Hybrid uses Knowledge Base, Knowledge Graph, and Semantic Data together.">
              <Select value={s.cognitive_retrieval_mode} onChange={(value) => update("cognitive_retrieval_mode", value as Settings["cognitive_retrieval_mode"])}>
                <option value="">Select retrieval mode</option>
                <option value="hybrid">Hybrid: KB + Graph + Semantic</option>
                <option value="kb_first">Knowledge Base first</option>
                <option value="graph_first">Knowledge Graph first</option>
              </Select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Semantic Data Layer" description="Allow questions about jobs, errors, queues, and status.">
                <Select value={s.semantic_data_enabled} onChange={(value) => update("semantic_data_enabled", value as Settings["semantic_data_enabled"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
              <Field label="Enrich graph on save" description="Queue node enrichment when notes are processed.">
                <Select value={s.cognitive_enrich_on_save} onChange={(value) => update("cognitive_enrich_on_save", value as Settings["cognitive_enrich_on_save"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
              <Field label="Generate insights on save" description="Queue evidence-based insights after graph expansion.">
                <Select value={s.cognitive_insights_on_save} onChange={(value) => update("cognitive_insights_on_save", value as Settings["cognitive_insights_on_save"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
              <Field label="Research Mode" description="Allow graph validation to query external web sources.">
                <Select value={s.research_mode_enabled} onChange={(value) => update("research_mode_enabled", value as Settings["research_mode_enabled"])}>
                  <option value="false">Disabled</option>
                  <option value="true">Enabled</option>
                </Select>
              </Field>
            </div>
          </Section>

          <Section title="Local" description="Local Ollama settings for offline processing.">
            <Field label="Ollama URL" description="Address reachable from the API and Worker containers.">
              <TextInput value={s.ollama_base_url} onChange={(value) => update("ollama_base_url", value)} placeholder="http://host.docker.internal:11434" />
            </Field>
            <Field label="Ollama graph model" description="Used when graph provider is Local Ollama.">
              <TextInput value={s.graph_ollama_model} onChange={(value) => update("graph_ollama_model", value)} placeholder="qwen3:8b" />
            </Field>
            <Field label="Auto-confirm confidence" description="Suggested graph connections above this confidence can be confirmed automatically.">
              <TextInput value={s.graph_auto_confirm_confidence} onChange={(value) => update("graph_auto_confirm_confidence", value)} placeholder="0.9" />
            </Field>
            <Field label="Default graph layout" description="Initial visual layout used by the graph screen.">
              <Select value={s.graph_default_layout} onChange={(value) => update("graph_default_layout", value as Settings["graph_default_layout"])}>
                <option value="">Select a default layout</option>
                <option value="brain">Brain View</option>
                <option value="radial">Radial</option>
                <option value="type">By type</option>
                <option value="connections">Centrality</option>
              </Select>
            </Field>
          </Section>

          <Section title="Saving" description="Settings are persisted only after clicking Save.">
            <ReadOnlyValue value="Click Save to write these values to local storage and the BerryBrain API." />
          </Section>

          <Section title="Maintenance" description="Repair and rebuild BerryBrain without deleting note files.">
            <div className="grid gap-2 sm:grid-cols-2">
              <MaintenanceButton onClick={() => runMaintenance("rebuild-brain")}>Rebuild second brain</MaintenanceButton>
              <MaintenanceButton onClick={() => runMaintenance("cleanup-legacy-insights")}>Cleanup legacy insights</MaintenanceButton>
              <MaintenanceButton onClick={() => runMaintenance("validate-graph")}>Validate graph consistency</MaintenanceButton>
              <MaintenanceButton onClick={() => runMaintenance("reindex-knowledge-base")}>Reindex knowledge base</MaintenanceButton>
            </div>
            {maintenanceStatus && <p className="rounded-xl bg-surface px-3 py-2 text-xs text-muted ring-1 ring-border/40">{maintenanceStatus}</p>}
          </Section>

          <Section title={t("diagnostics")} description={t("diagnosticsDesc")}>
            {diagLoading ? (
              <p className="text-xs text-muted">{t("loadingDiagnostics")}</p>
            ) : diagnostics ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium">{t("healthStatus")}:</span>
                  <span className={`rounded-lg px-2 py-0.5 text-[11px] font-medium ring-1 ${diagnostics.status === "ok" ? "bg-emerald-500/10 text-emerald-600 ring-emerald-500/20" : diagnostics.status === "degraded" ? "bg-amber-500/10 text-amber-600 ring-amber-500/20" : "bg-danger/10 text-danger ring-danger/20"}`}>{diagnostics.status}</span>
                </div>
                {diagnostics.staleRunning.length > 0 ? (
                  <div>
                    <p className="text-xs font-medium text-foreground">{t("stuckJobs")} ({diagnostics.staleRunning.length})</p>
                    <ul className="mt-1 space-y-1">
                      {diagnostics.staleRunning.slice(0, 10).map((j: any) => (
                        <li key={j.id} className="rounded-lg bg-surface px-2 py-1 text-[11px] text-muted ring-1 ring-border/30">
                          {j.type} — {j.id.slice(0, 8)}… {j.started_at ? `since ${new Date(j.started_at).toLocaleTimeString()}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p className="text-xs text-muted">{t("noStuckJobs")}</p>
                )}
                {Object.keys(diagnostics.failedByType).length > 0 ? (
                  <p className="text-xs text-muted">{tf("failedJobCount", { count: Object.values(diagnostics.failedByType).reduce((a: number, b: number) => a + b, 0) })}</p>
                ) : (
                  <p className="text-xs text-muted">{t("noFailedJobs")}</p>
                )}
                <MaintenanceButton onClick={clearStuckJobs} >{diagClearing ? t("clearing") : t("clearStuckJobs")}</MaintenanceButton>
                {diagClearResult && <p className="text-xs text-muted">{diagClearResult}</p>}
              </div>
            ) : (
              <p className="text-xs text-muted">{t("loadingDiagnostics")}</p>
            )}
          </Section>

          <Section title="Danger zone" description="Permanent destructive actions. Confirmations are required.">
            <div className="grid gap-2 sm:grid-cols-2">
              <DangerButton onClick={() => wipeAll(false)}>Wipe all, keep Settings</DangerButton>
              <DangerButton onClick={() => wipeAll(true)}>Wipe all and reset Settings</DangerButton>
            </div>
          </Section>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/50 px-6 py-3">
          <p className="text-xs text-muted" role="status">{settingsLoading ? "Loading settings..." : saveStatus}</p>
          <div className="flex gap-2">
          <button className="bb-action h-9 px-4 text-xs font-medium" onClick={onClose}>Cancel</button>
          <button className="bb-action h-9 px-4 text-xs font-medium" onClick={save} disabled={saving || settingsLoading}>
            {saving ? "Saving..." : "Save"}
          </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return (
    <section className="bb-subcard p-4">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-xs text-muted/75">{description}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function Field({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="block text-xs font-medium text-foreground">{label}</span>
      {description && <span className="mb-1.5 mt-0.5 block text-[11px] leading-4 text-muted/70">{description}</span>}
      {children}
    </label>
  );
}

function TextInput({ value, onChange, placeholder, type = "text" }: { value: string; onChange: (value: string) => void; placeholder: string; type?: string }) {
  return (
    <input
      type={type}
      className="h-9 w-full rounded-xl border border-border bg-panel px-3 text-sm text-foreground outline-none placeholder:text-muted/55 focus:border-accent"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder}
    />
  );
}

function Select({ value, onChange, children }: { value: string; onChange: (value: string) => void; children: React.ReactNode }) {
  return (
    <select
      className="h-9 w-full rounded-xl border border-border bg-panel px-3 text-sm text-foreground outline-none focus:border-accent"
      value={value}
      onChange={(event) => onChange(event.target.value)}
    >
      {children}
    </select>
  );
}

function Range({ value, min, max, onChange }: { value: string; min: string; max: string; onChange: (value: string) => void }) {
  return (
    <input
      type="range"
      min={min}
      max={max}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className="h-1 w-full cursor-pointer appearance-none rounded-full bg-border accent-accent"
    />
  );
}

function ReadOnlyValue({ value }: { value: string }) {
  return <div className="rounded-xl bg-panel px-3 py-2 text-sm text-foreground ring-1 ring-border/45">{value}</div>;
}

function ProviderConnectionStatus({ status, loading }: { status: AiProviderStatus | null; loading: boolean }) {
  if (loading) return <ReadOnlyValue value="Checking provider configuration..." />;
  if (!status) return <ReadOnlyValue value="Provider status is unavailable." />;
  const labels: Record<AiProviderStatus["state"], { title: string; description: string; tone: string }> = {
    connected: { title: "Connected", description: "The cloud provider was verified and is enabled for the main pipeline and graph.", tone: "text-emerald-700" },
    configured: { title: "Configured, not tested", description: "Credentials and model are saved. Test the connection before relying on cloud processing.", tone: "text-amber-700" },
    disabled: { title: "Disabled by privacy setting", description: "Credentials are saved, but remote content processing is disabled.", tone: "text-amber-700" },
    incomplete: { title: "Setup incomplete", description: "A provider URL, API key, and model are required.", tone: "text-danger" },
    failed: { title: "Connection failed", description: status.lastError || "Test the connection and review the provider configuration.", tone: "text-danger" },
    local: { title: "Local processing selected", description: "The worker is configured to use Ollama, even if a cloud key is saved.", tone: "text-muted" },
  };
  const current = labels[status.state];
  const checks = [
    `${status.providerMode === "cloud" ? "✓" : "○"} Main pipeline: ${status.providerMode}`,
    `${status.graphProviderMode === "cloud" ? "✓" : "○"} Graph inference: ${status.graphProviderMode}`,
    `${status.keyConfigured ? "✓" : "○"} API key`,
    `${status.modelConfigured ? "✓" : "○"} Model`,
    `${status.remoteContentConsent ? "✓" : "○"} Remote processing consent`,
  ];
  return (
    <div className="rounded-xl border border-border bg-panel p-3">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className={`text-xs font-semibold ${current.tone}`}>{current.title}</p>
          <p className="mt-1 text-[11px] leading-4 text-muted">{current.description}</p>
        </div>
        {status.lastTestLatencyMs ? <span className="text-[10px] tabular-nums text-muted">{status.lastTestLatencyMs} ms</span> : null}
      </div>
      <div className="mt-3 grid gap-1 text-[10px] text-muted sm:grid-cols-2">{checks.map((check) => <span key={check}>{check}</span>)}</div>
    </div>
  );
}

function MaintenanceButton({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button className="bb-action h-9 px-3 text-xs font-medium" onClick={onClick}>
      {children}
    </button>
  );
}

function DangerButton({ children, onClick }: { children: React.ReactNode; onClick: () => void }) {
  return (
    <button className="bb-action bb-action--danger h-9 px-3 text-xs font-medium" onClick={onClick}>
      {children}
    </button>
  );
}

function labelize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1);
}
