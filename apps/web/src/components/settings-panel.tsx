"use client";

import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { LangKind, getLang, t, tf } from "../i18n";
import { readCsrf } from "./public-site/user-menu";

type ThemeKind = "light" | "dark";

const SETTINGS_AREAS = [
  "General",
  "AI & execution",
  "Main provider",
  "Agents",
  "Judge",
  "HippoRAG",
  "Embeddings & KB",
  "Knowledge Graph",
  "Jobs & Worker",
  "Storage & vaults",
  "Performance",
  "Monitoring",
  "Security & data",
  "Maintenance",
] as const;
type SettingsArea = (typeof SETTINGS_AREAS)[number];
const SettingsFilterContext = createContext<{
  area: SettingsArea;
  query: string;
}>({ area: "General", query: "" });

const SECTION_AREAS: Record<string, SettingsArea[]> = {
  "Setup assistant": ["General", "Monitoring"],
  Appearance: ["General"],
  Font: ["General"],
  Editor: ["General"],
  "Attachment processing": ["General"],
  "AI / Provider": ["AI & execution"],
  "Cloud AI": ["Main provider"],
  "Cognitive Layer": [
    "Agents",
    "Judge",
    "HippoRAG",
    "Embeddings & KB",
    "Knowledge Graph",
  ],
  "Judge committee": ["Judge"],
  "Graph behavior": ["Knowledge Graph"],
  Local: ["Main provider"],
  Saving: ["General"],
  Maintenance: ["Maintenance"],
  Diagnostics: ["Jobs & Worker", "Performance", "Monitoring"],
  "Danger zone": ["Storage & vaults", "Security & data"],
};

const THEME_PRESETS: Record<ThemeKind, { bg: string; fg: string; mu: string; pn: string; bd: string }> = {
  light: { bg: "#FAF8F5", fg: "#1D1B18", mu: "#5C5C5C", pn: "#FFFFFF", bd: "#E4E0D8" },
  dark: { bg: "#121212", fg: "#E8E8E8", mu: "#B5AFA7", pn: "#1D1B19", bd: "#393530" },
};

const UI_FONTS: Record<string, string> = {
  inter: '"Inter", ui-sans-serif, system-ui, sans-serif',
  system: "ui-sans-serif, system-ui, -apple-system, sans-serif",
};

const EDITOR_FONTS: Record<string, string> = {
  mono: '"Geist Mono", "JetBrains Mono", ui-monospace, monospace',
  sans: "ui-sans-serif, system-ui, sans-serif",
};

const NVIDIA_NIM_URL = process.env.NEXT_PUBLIC_BERRYBRAIN_CLOUD_API_URL || "";
const DEFAULT_OLLAMA_BASE_URL = process.env.NEXT_PUBLIC_BERRYBRAIN_OLLAMA_BASE_URL || "";
const DEFAULT_LOCAL_MODEL = process.env.NEXT_PUBLIC_BERRYBRAIN_LOCAL_MODEL || "";

type Settings = {
  theme: ThemeKind;
  lang: LangKind;
  font_size: string;
  editor_font_size: string;
  ui_font: string;
  editor_font: string;
  display_name: string;
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
  graph_min_shared_concepts: string;
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
  insights_auto_interval_hours: string;
  research_mode_enabled: "true" | "false";
  remote_content_consent: "true" | "false";
  attachment_image_limit_mb: string;
  attachment_video_limit_mb: string;
  attachment_audio_limit_mb: string;
  attachment_other_limit_mb: string;
  attachment_ocr_language: string;
  attachment_transcription_executable: "faster-whisper" | "whisper";
  attachment_transcription_model: string;
  judge_provider: string;
  judge_model: string;
  judge_enabled: "true" | "false";
  hipporag_provider: string;
  hipporag_model: string;
  hipporag_enabled: "true" | "false";
  automatic_vault_organization: "true" | "false";
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

type StaleRunningJob = {
  id: string | number;
  type: string;
  started_at?: string | null;
};

type JobDiagnostics = {
  staleRunning: StaleRunningJob[];
  failedByType: Record<string, number>;
  status: string;
};

type JudgeMode = "deterministic" | "single_model" | "committee";
type JudgeCommitteeSlot = {
  slot: string;
  provider: string;
  model: string;
  role: string;
  focus: string;
};
type JudgeConfiguration = {
  mode: JudgeMode;
  committee: JudgeCommitteeSlot[];
  committee_size: number;
  consent_at: string | null;
};

const DEFAULT_JUDGE_CONFIGURATION: JudgeConfiguration = {
  mode: "single_model",
  committee: [],
  committee_size: 3,
  consent_at: null,
};

function defaults(): Settings {
  return {
    theme: "light",
    lang: "en",
    font_size: "15",
    editor_font_size: "15",
    ui_font: "inter",
    editor_font: "mono",
    display_name: "",
    ai_provider: "local",
    ai_api_url: NVIDIA_NIM_URL,
    ai_custom_url: "",
    ai_api_key: "",
    ai_model: "",
    graph_ai_provider: "local",
    graph_ai_api_url: NVIDIA_NIM_URL,
    graph_ai_api_key: "",
    graph_ai_model: "",
    ollama_base_url: DEFAULT_OLLAMA_BASE_URL,
    graph_ollama_model: DEFAULT_LOCAL_MODEL,
    graph_auto_confirm_confidence: "0.9",
    graph_default_layout: "brain",
    graph_min_shared_concepts: "2",
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
    insights_auto_interval_hours: "24",
    research_mode_enabled: "false",
    remote_content_consent: "false",
    attachment_image_limit_mb: "10",
    attachment_video_limit_mb: "200",
    attachment_audio_limit_mb: "50",
    attachment_other_limit_mb: "25",
    attachment_ocr_language: "eng",
    attachment_transcription_executable: "faster-whisper",
    attachment_transcription_model: "small",
    judge_provider: "",
    judge_model: "",
    judge_enabled: "true",
    hipporag_provider: "",
    hipporag_model: "",
    hipporag_enabled: "true",
    automatic_vault_organization: "true",
  };
}

function loadSettings(): Settings {
  if (typeof window === "undefined") return defaults();
  const d = defaults();
  [
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
    "kb_embedding_provider",
    "kb_embedding_model",
    "judge_provider",
    "judge_model",
    "judge_enabled",
    "hipporag_provider",
    "hipporag_model",
    "hipporag_enabled",
    "automatic_vault_organization",
    "remote_content_consent",
  ].forEach((key) => localStorage.removeItem(`bb_${key}`));
  return {
    theme: (localStorage.getItem("bb_theme") as ThemeKind) || d.theme,
    lang: "en",
    font_size: localStorage.getItem("bb_font_size") || d.font_size,
    editor_font_size: localStorage.getItem("bb_editor_font_size") || d.editor_font_size,
    ui_font: localStorage.getItem("bb_ui_font") || d.ui_font,
    editor_font: localStorage.getItem("bb_editor_font") || d.editor_font,
    display_name: localStorage.getItem("bb_display_name") || d.display_name,
    ai_provider: d.ai_provider,
    ai_api_url: d.ai_api_url,
    ai_custom_url: d.ai_custom_url,
    ai_api_key: d.ai_api_key,
    ai_model: d.ai_model,
    graph_ai_provider: d.graph_ai_provider,
    graph_ai_api_url: d.graph_ai_api_url,
    graph_ai_api_key: d.graph_ai_api_key,
    graph_ai_model: d.graph_ai_model,
    ollama_base_url: d.ollama_base_url,
    graph_ollama_model: d.graph_ollama_model,
    graph_auto_confirm_confidence: localStorage.getItem("bb_graph_auto_confirm_confidence") || d.graph_auto_confirm_confidence,
    graph_default_layout: (localStorage.getItem("bb_graph_default_layout") as Settings["graph_default_layout"]) || d.graph_default_layout,
    graph_min_shared_concepts: localStorage.getItem("bb_graph_min_shared_concepts") || d.graph_min_shared_concepts,
    kb_vector_store: (localStorage.getItem("bb_kb_vector_store") as Settings["kb_vector_store"]) || d.kb_vector_store,
    kb_embedding_provider: d.kb_embedding_provider,
    kb_embedding_model: d.kb_embedding_model,
    kb_chunk_size: localStorage.getItem("bb_kb_chunk_size") || d.kb_chunk_size,
    kb_chunk_overlap: localStorage.getItem("bb_kb_chunk_overlap") || d.kb_chunk_overlap,
    qdrant_url: localStorage.getItem("bb_qdrant_url") || d.qdrant_url,
    qdrant_collection: localStorage.getItem("bb_qdrant_collection") || d.qdrant_collection,
    chroma_url: localStorage.getItem("bb_chroma_url") || d.chroma_url,
    chroma_collection: localStorage.getItem("bb_chroma_collection") || d.chroma_collection,
    cognitive_retrieval_mode: (localStorage.getItem("bb_cognitive_retrieval_mode") as Settings["cognitive_retrieval_mode"]) || d.cognitive_retrieval_mode,
    semantic_data_enabled: (localStorage.getItem("bb_semantic_data_enabled") as Settings["semantic_data_enabled"]) || d.semantic_data_enabled,
    insights_auto_interval_hours: localStorage.getItem("bb_insights_auto_interval_hours") || d.insights_auto_interval_hours,
    research_mode_enabled: (localStorage.getItem("bb_research_mode_enabled") as Settings["research_mode_enabled"]) || d.research_mode_enabled,
    remote_content_consent: d.remote_content_consent,
    attachment_image_limit_mb: localStorage.getItem("bb_attachment_image_limit_mb") || d.attachment_image_limit_mb,
    attachment_video_limit_mb: localStorage.getItem("bb_attachment_video_limit_mb") || d.attachment_video_limit_mb,
    attachment_audio_limit_mb: localStorage.getItem("bb_attachment_audio_limit_mb") || d.attachment_audio_limit_mb,
    attachment_other_limit_mb: localStorage.getItem("bb_attachment_other_limit_mb") || d.attachment_other_limit_mb,
    attachment_ocr_language: localStorage.getItem("bb_attachment_ocr_language") || d.attachment_ocr_language,
    attachment_transcription_executable: (localStorage.getItem("bb_attachment_transcription_executable") as Settings["attachment_transcription_executable"]) || d.attachment_transcription_executable,
    attachment_transcription_model: localStorage.getItem("bb_attachment_transcription_model") || d.attachment_transcription_model,
    judge_provider: d.judge_provider,
    judge_model: d.judge_model,
    judge_enabled: d.judge_enabled,
    hipporag_provider: d.hipporag_provider,
    hipporag_model: d.hipporag_model,
    hipporag_enabled: d.hipporag_enabled,
    automatic_vault_organization: d.automatic_vault_organization,
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
  r.style.setProperty("--color-accent", "#CC4168");
  r.style.setProperty("--color-accent-hover", s.theme === "dark" ? "#E67592" : "#B33654");
  r.style.setProperty("--color-accent-soft", s.theme === "dark" ? "#422631" : "#E8D5DA");
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
  "display_name",
  "graph_auto_confirm_confidence",
  "graph_default_layout",
  "graph_min_shared_concepts",
  "kb_vector_store",
  "kb_chunk_size",
  "kb_chunk_overlap",
  "qdrant_url",
  "qdrant_collection",
  "chroma_url",
  "chroma_collection",
  "cognitive_retrieval_mode",
  "semantic_data_enabled",
  "insights_auto_interval_hours",
  "research_mode_enabled",
  "judge_enabled",
  "hipporag_enabled",
  "automatic_vault_organization",
  "attachment_image_limit_mb",
  "attachment_video_limit_mb",
  "attachment_audio_limit_mb",
  "attachment_other_limit_mb",
  "attachment_ocr_language",
  "attachment_transcription_executable",
  "attachment_transcription_model",
];

export function SettingsPanel({ open, onClose, apiUrl }: { open: boolean; onClose: () => void; apiUrl: string }) {
  const [s, setS] = useState<Settings>(loadSettings);
  const editedRef = useRef(false);
  const [saving, setSaving] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [saveStatus, setSaveStatus] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [providerStatus, setProviderStatus] = useState<AiProviderStatus | null>(null);
  const [judgeConfiguration, setJudgeConfiguration] = useState<JudgeConfiguration>(DEFAULT_JUDGE_CONFIGURATION);
  const [judgeModels, setJudgeModels] = useState<string[]>([]);
  const [judgeProvider, setJudgeProvider] = useState("");
  const [generatorModel, setGeneratorModel] = useState("");
  const [primaryJudgeModel, setPrimaryJudgeModel] = useState("");
  const [judgeStatus, setJudgeStatus] = useState("");
  const [judgeDirty, setJudgeDirty] = useState(false);
  const [maintenanceStatus, setMaintenanceStatus] = useState("");
  const [diagnostics, setDiagnostics] = useState<JobDiagnostics | null>(null);
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagClearing, setDiagClearing] = useState(false);
  const [diagClearResult, setDiagClearResult] = useState("");
  const [activeArea, setActiveAreaState] = useState<SettingsArea>("General");
  const [settingsQuery, setSettingsQuery] = useState("");
  const [dirtyAreas, setDirtyAreas] = useState<Set<SettingsArea>>(new Set());

  const setupItems = useMemo(() => {
    return [
      {
        title: "Ask and graph AI",
        ready: providerStatus?.state === "connected",
        detail: providerStatus?.state === "connected"
          ? `${providerStatus.provider} is validated.`
          : "Complete unified AI setup and validate all model slots.",
      },
      {
        title: "Knowledge search",
        ready: s.kb_vector_store === "sqlite" || Boolean(s.qdrant_url.trim() || s.chroma_url.trim()),
        detail: "SQLite works out of the box. External stores need a reachable URL.",
      },
      {
        title: "Automatic learning",
        ready: true,
        detail: "Enrichment, gap discovery, Judge evaluation, clustering, and insight agents run automatically.",
      },
      {
        title: "Online validation",
        ready: s.research_mode_enabled === "true",
        detail: "Optional. Enables node validation with external web sources.",
      },
    ];
  }, [providerStatus, s]);

  useEffect(() => {
    if (!open) return;
    editedRef.current = false;
    setDirtyAreas(new Set());
    const areaFromHash = new URLSearchParams(window.location.hash.slice(1)).get(
      "settings",
    );
    if (SETTINGS_AREAS.includes(areaFromHash as SettingsArea)) {
      setActiveAreaState(areaFromHash as SettingsArea);
    }
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
          fetch(`${apiUrl}/api/v1/judge/mode`, { credentials: "include" }),
          fetch(`${apiUrl}/api/v1/ai/configuration`, { credentials: "include" }),
        ]).then(async ([settingsResponse, statusResponse, judgeResponse, aiResponse]) => {
            if (!settingsResponse.ok) throw new Error("Settings could not be loaded.");
            const d = await settingsResponse.json();
            const loaded: Partial<Settings> = {};
            for (const item of d.settings || []) {
              const key = String(item.key) as keyof Settings;
              if (SETTING_KEYS.includes(key)) (loaded as Record<string, string>)[key] = item.value;
            }
            if (!cancelled && !editedRef.current) setS((prev) => ({ ...prev, ...loaded, lang: "en" }));
            if (statusResponse.ok && !cancelled) {
              const status = await statusResponse.json();
              setProviderStatus(status);
            }
            if (judgeResponse.ok && !cancelled) {
              const judge = await judgeResponse.json();
              setJudgeConfiguration({ ...DEFAULT_JUDGE_CONFIGURATION, ...judge });
              setJudgeDirty(false);
            }
            if (aiResponse.ok && !cancelled) {
              const ai = await aiResponse.json();
              const configuration = ai.configuration;
              const provider = String(configuration?.judge?.provider_id || "");
              setJudgeProvider(provider);
              setGeneratorModel(String(configuration?.main?.model_id || ""));
              setPrimaryJudgeModel(String(configuration?.judge?.model_id || ""));
              if (provider) {
                const modelResponse = await fetch(
                  `${apiUrl}/api/v1/ai/providers/${encodeURIComponent(provider)}/models`,
                  { credentials: "include" },
                );
                if (modelResponse.ok && !cancelled) {
                  const payload = await modelResponse.json();
                  setJudgeModels((payload.models || []).map((item: { id?: unknown }) => String(item.id || "")).filter(Boolean));
                }
              }
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
      .then((d: Partial<JobDiagnostics>) => setDiagnostics({ staleRunning: d.staleRunning || [], failedByType: d.failedByType || {}, status: d.status || "unknown" }))
      .catch(() => setDiagnostics(null))
      .finally(() => setDiagLoading(false));
  }, [open, apiUrl]);

  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    editedRef.current = true;
    setDirtyAreas((current) => new Set(current).add(activeArea));
    setSaveStatus("");
    setS((previous) => {
      const next: Settings = { ...previous, [key]: value, lang: "en" };
      if (["theme", "font_size", "ui_font", "editor_font"].includes(String(key))) applyTheme(next);
      return next;
    });
  }

  function updateJudge(next: JudgeConfiguration) {
    setJudgeConfiguration(next);
    setJudgeDirty(true);
    setDirtyAreas((current) => new Set(current).add("Judge"));
    setJudgeStatus("");
  }

  function updateJudgeSlot(index: number, values: Partial<JudgeCommitteeSlot>) {
    const committee = Array.from({ length: judgeConfiguration.committee_size }, (_, position) =>
      judgeConfiguration.committee[position] || {
        slot: `judge-${position + 1}`,
        provider: judgeProvider,
        model: "",
        role: "general",
        focus: "Evaluate the complete artifact rubric.",
      },
    );
    committee[index] = { ...committee[index], ...values, provider: judgeProvider };
    updateJudge({ ...judgeConfiguration, committee });
  }

  async function applyJudgeDefaults() {
    setJudgeStatus("Assigning available provider models...");
    try {
      const response = await fetch(`${apiUrl}/api/v1/judge/defaults`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
        body: JSON.stringify({
          provider: judgeProvider,
          models: judgeModels,
          generator_model: generatorModel,
          primary_judge_model: primaryJudgeModel,
          committee_size: judgeConfiguration.committee_size,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Judge defaults could not be assigned.");
      updateJudge({
        ...judgeConfiguration,
        mode: payload.mode,
        committee: payload.committee || [],
        committee_size: payload.committee_size,
      });
      setJudgeStatus(payload.message || "Judge defaults assigned.");
    } catch (error) {
      setJudgeStatus(error instanceof Error ? error.message : "Judge defaults could not be assigned.");
    }
  }

  async function persistJudgeConfiguration() {
    if (!judgeDirty || !isAdmin || apiUrl === "__demo__") return;
    const response = await fetch(`${apiUrl}/api/v1/judge/mode`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
      body: JSON.stringify({
        ...judgeConfiguration,
        consent_at: judgeConfiguration.mode === "committee"
          ? judgeConfiguration.consent_at || new Date().toISOString()
          : judgeConfiguration.consent_at,
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.status === "error") {
      throw new Error(payload.message || payload.detail || "Judge configuration could not be saved.");
    }
    setJudgeConfiguration({ ...DEFAULT_JUDGE_CONFIGURATION, ...payload });
    setJudgeDirty(false);
  }

  async function refreshProviderStatus() {
    if (apiUrl === "__demo__" || !isAdmin) return;
    const response = await fetch(`${apiUrl}/api/v1/settings/ai/status`, { credentials: "include" });
    if (response.ok) setProviderStatus(await response.json());
  }

  async function persist(next = s) {
    const values: Record<string, string> = {};
    SETTING_KEYS.forEach((key) => {
      localStorage.setItem(`bb_${key}`, String(next[key]));
      values[key] = String(next[key]);
    });
    if (!isAdmin || apiUrl === "__demo__") return;
    const response = await fetch(`${apiUrl}/api/v1/settings/batch`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
      credentials: "include",
      body: JSON.stringify({ values, aiTestRevision: "" }),
    });
    if (!response.ok) throw new Error("Settings could not be saved.");
  }

  async function save() {
    setSaving(true);
    setSaveStatus("");
    try {
      await persist(s);
      await persistJudgeConfiguration();
      applyTheme(s);
      editedRef.current = false;
      setDirtyAreas(new Set());
      setSaveStatus("Settings saved.");
      await refreshProviderStatus();
    } catch (error) {
      setSaveStatus(error instanceof Error ? error.message : "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
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
      setSaveStatus("Danger Zone actions are disabled in demo mode.");
      return;
    }
    const label = resetSettings
      ? "DELETE EVERYTHING and reset Settings to defaults"
      : "DELETE EVERYTHING but keep current Settings";
    const confirmed = window.confirm(
      `${label}?\n\nThis deletes notes, graph, embeddings, insights, jobs, notifications and vault files. This cannot be undone.`,
    );
    if (!confirmed) return;
    setSaveStatus("Wiping BerryBrain data...");
    const response = await fetch(`${apiUrl}/api/v1/settings/danger/wipe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reset_settings: resetSettings }),
    });
    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      setSaveStatus(payload.detail || "Wipe failed.");
      return;
    }
    if (resetSettings) resetLocalSettings();
    else preserveLocalSettings();
    setSaveStatus(resetSettings ? "Everything wiped. Settings reset. Reloading..." : "Everything wiped. Settings preserved. Reloading...");
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

  async function prepareSemanticGraph() {
    if (apiUrl === "__demo__") {
      setMaintenanceStatus("Maintenance actions are disabled in demo mode.");
      return;
    }
    setMaintenanceStatus("Inspecting semantic graph migration...");
    const previewResponse = await fetch(`${apiUrl}/api/v1/maintenance/prepare-semantic-graph`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dry_run: true, batch_size: 100 }),
    });
    const preview = await previewResponse.json().catch(() => ({}));
    if (!previewResponse.ok) {
      setMaintenanceStatus(preview.detail || "Semantic graph inspection failed.");
      return;
    }
    const summary = preview.clusterPreview || {};
    const confirmed = window.confirm(
      `Prepare semantic graph?\n\n${summary.nodeCount || 0} nodes inspected, ${summary.clusterCount || 0} clusters proposed, ${summary.unresolvedCount || 0} unresolved. Processing is bounded to 100 items per run.`,
    );
    if (!confirmed) {
      setMaintenanceStatus("Semantic graph preparation cancelled after dry run.");
      return;
    }
    setMaintenanceStatus("Preparing semantic graph...");
    const response = await fetch(`${apiUrl}/api/v1/maintenance/prepare-semantic-graph`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dry_run: false, confirm: true, batch_size: 100 }),
    });
    const result = await response.json().catch(() => ({}));
    setMaintenanceStatus(
      response.ok
        ? `Semantic graph prepared. ${result.enrichmentQueued || 0} analyses queued; ${result.clusterAssignmentsUpdated || 0} color assignments updated.`
        : result.detail || "Semantic graph preparation failed.",
    );
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

  function setActiveArea(area: SettingsArea) {
    setActiveAreaState(area);
    const params = new URLSearchParams(window.location.hash.slice(1));
    params.set("settings", area);
    window.history.replaceState(
      {},
      "",
      `${window.location.pathname}${window.location.search}#${params}`,
    );
  }

  function requestClose() {
    if (
      dirtyAreas.size > 0 &&
      !window.confirm("Discard unsaved settings changes?")
    ) {
      return;
    }
    onClose();
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-8">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" onClick={requestClose} />
      <div className="bb-card bb-card--elevated relative z-50 flex max-h-[calc(100dvh-4rem)] w-full max-w-[94vw] flex-col overflow-hidden text-foreground sm:w-[860px]" role="dialog" aria-label="Settings">
        <div className="flex items-center justify-between border-b border-border/45 px-6 py-4">
          <div>
            <h2 className="text-base font-semibold tracking-tight">Settings</h2>
            <p className="mt-0.5 text-xs text-muted/70">Configure appearance, editor, AI providers, and saving behavior.</p>
          </div>
          <button className="rounded-md p-1.5 text-muted hover:bg-surface hover:text-foreground" onClick={requestClose} aria-label="Close settings">x</button>
        </div>

        <div className="grid min-h-0 flex-1 grid-cols-1 overflow-hidden sm:grid-cols-[13rem_minmax(0,1fr)]">
          <nav className="overflow-y-auto border-b border-border bg-background/50 p-3 sm:border-b-0 sm:border-r" aria-label="Settings sections">
            <input
              type="search"
              value={settingsQuery}
              onChange={(event) => setSettingsQuery(event.target.value)}
              placeholder="Search settings"
              className="mb-3 w-full rounded-md border border-border bg-panel px-3 py-2 text-sm"
            />
            <div className="grid grid-cols-2 gap-1 sm:grid-cols-1">
              {SETTINGS_AREAS.map((area) => (
                <button
                  type="button"
                  key={area}
                  onClick={() => setActiveArea(area)}
                  className={`flex min-h-9 items-center justify-between rounded-md px-2.5 py-2 text-left text-xs ${
                    activeArea === area
                      ? "bg-accent-soft font-semibold text-foreground"
                      : "text-muted hover:bg-surface hover:text-foreground"
                  }`}
                >
                  <span>{area}</span>
                  {dirtyAreas.has(area) && (
                    <span className="text-accent" aria-label="Unsaved changes">
                      •
                    </span>
                  )}
                </button>
              ))}
            </div>
          </nav>
          <SettingsFilterContext.Provider
            value={{ area: activeArea, query: settingsQuery }}
          >
          <div className="min-h-0 space-y-1 overflow-y-auto overscroll-contain px-5 py-3">
          <Section title="Setup assistant" description="Start here when Ask, graph AI, or automatic processing does not behave as expected.">
            <div className="grid gap-2 sm:grid-cols-2">
              {setupItems.map((item) => (
                <SetupStep key={item.title} title={item.title} ready={item.ready} detail={item.detail} />
              ))}
            </div>
            <ReadOnlyValue value={providerStatus?.lastError ? `Last provider error: ${providerStatus.lastError}` : "Changes are saved only after clicking Save."} />
          </Section>

          <Section title="Appearance" description="Interface identity and theme.">
            <Field label="Display name" description="Used in the Home greeting.">
              <TextInput value={s.display_name} onChange={(value) => update("display_name", value)} placeholder="Your name" />
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
            <Field label="OCR language" description="Installed Tesseract code, such as eng, spa, or eng+spa. Settings do not download language packs; verify them with tesseract --list-langs in the API container.">
              <TextInput value={s.attachment_ocr_language} onChange={(value) => update("attachment_ocr_language", value)} placeholder="eng or eng+spa" />
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
            <ReadOnlyValue value={providerStatus ? `${providerStatus.providerMode === "cloud" ? "Cloud" : "Local"} · ${providerStatus.provider} · ${providerStatus.state}` : "Loading configuration status..."} />
            <button
              className="bb-action h-9 px-4 text-xs font-semibold"
              onClick={() => window.dispatchEvent(new Event("bb:open-ai-setup"))}
            >
              Configure AI providers and models
            </button>
            <p className="text-xs leading-relaxed text-muted">
              Main, embeddings, Judge, and HippoRAG are validated and saved together. BerryBrain never mixes Cloud and Local providers silently.
            </p>
          </Section>

          <Section title="Cloud AI" description="OpenAI-compatible provider used for graph inference, insights, and knowledge expansion.">
            <ProviderConnectionStatus status={providerStatus} loading={settingsLoading} />
            <button
              className="bb-action h-9 px-4 text-xs font-semibold"
              onClick={() => window.dispatchEvent(new Event("bb:open-ai-setup"))}
            >
              Open unified AI setup
            </button>
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
            <Field label="AI capabilities" description="Embedding, Judge, and HippoRAG models use the unified validated configuration.">
              <button
                className="bb-action h-9 px-4 text-xs font-semibold"
                onClick={() => window.dispatchEvent(new Event("bb:open-ai-setup"))}
              >
                Inspect AI capabilities
              </button>
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
              <Field label="Research Mode" description="Allow graph validation to query external web sources.">
                <Select value={s.research_mode_enabled} onChange={(value) => update("research_mode_enabled", value as Settings["research_mode_enabled"])}>
                  <option value="false">Disabled</option>
                  <option value="true">Enabled</option>
                </Select>
              </Field>
            </div>
            <Field label="Automatic insight interval (hours)" description="The active agent monitor queues evidence-based insight analysis at this interval. Minimum 1, maximum 168.">
              <TextInput value={s.insights_auto_interval_hours} onChange={(value) => update("insights_auto_interval_hours", value)} placeholder="24" />
            </Field>
            
            <div className="mt-4 border-t border-border/30 pt-4" />
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Automatic vault organization" description="Groups new content from semantic evidence. Disabling it stops future automatic moves and preserves existing folders.">
                <Select value={s.automatic_vault_organization} onChange={(value) => update("automatic_vault_organization", value as Settings["automatic_vault_organization"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
              <Field label="Judge" description="Evaluates generated artifacts against source evidence before they become trusted context.">
                <Select value={s.judge_enabled} onChange={(value) => update("judge_enabled", value as Settings["judge_enabled"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
              <Field label="HippoRAG" description="Adds multi-hop retrieval while canonical graph evidence remains authoritative.">
                <Select value={s.hipporag_enabled} onChange={(value) => update("hipporag_enabled", value as Settings["hipporag_enabled"])}>
                  <option value="true">Enabled</option>
                  <option value="false">Disabled</option>
                </Select>
              </Field>
            </div>
          </Section>

          <Section title="Judge committee" description="Evidence-grounded quality control for generated nodes, edges, and insights.">
            <div className="grid gap-3 sm:grid-cols-3">
              <Field label="Execution mode" description="Committee mode runs independent model verdicts for high-impact artifacts.">
                <Select
                  value={judgeConfiguration.mode}
                  onChange={(value) => updateJudge({ ...judgeConfiguration, mode: value as JudgeMode })}
                >
                  <option value="deterministic">Deterministic</option>
                  <option value="single_model">Single model</option>
                  <option value="committee">Committee</option>
                </Select>
              </Field>
              <Field label="Default Judge count" description="Three roles balance coverage and provider cost. Valid range: 2 to 5.">
                <Select
                  value={String(judgeConfiguration.committee_size)}
                  onChange={(value) => {
                    const committeeSize = Number(value);
                    updateJudge({
                      ...judgeConfiguration,
                      committee_size: committeeSize,
                      committee: judgeConfiguration.committee.slice(0, committeeSize),
                    });
                  }}
                >
                  {[2, 3, 4, 5].map((count) => <option key={count} value={count}>{count} models</option>)}
                </Select>
              </Field>
              <Field label="Provider" description="Inherited from the active validated AI configuration.">
                <ReadOnlyValue value={judgeProvider || "No provider configured"} />
              </Field>
            </div>

            <div className="flex flex-wrap items-center gap-3 border-y border-border py-3">
              <button
                type="button"
                className="bb-action h-9 px-4 text-xs font-semibold"
                onClick={applyJudgeDefaults}
                disabled={!judgeProvider || judgeModels.length < 2}
              >
                Apply provider defaults
              </button>
              <span className="text-[11px] text-muted">
                {judgeModels.length} available models · generator excluded: {generatorModel || "not configured"}
              </span>
            </div>

            {judgeConfiguration.mode === "single_model" && (
              <ReadOnlyValue value={`Single Judge: ${primaryJudgeModel || "not configured"}`} />
            )}

            {judgeConfiguration.mode === "committee" && (
              <div className="divide-y divide-border border-y border-border">
                {Array.from({ length: judgeConfiguration.committee_size }, (_, index) => {
                  const slot = judgeConfiguration.committee[index] || {
                    slot: `judge-${index + 1}`,
                    provider: judgeProvider,
                    model: "",
                    role: "general",
                    focus: "Evaluate the complete artifact rubric.",
                  };
                  return (
                    <div key={slot.slot || index} className="grid gap-3 py-4 lg:grid-cols-[minmax(9rem,0.7fr)_minmax(12rem,1fr)_minmax(16rem,1.6fr)]">
                      <Field label={`Judge ${index + 1} role`}>
                        <TextInput
                          value={slot.role}
                          onChange={(value) => updateJudgeSlot(index, { role: value })}
                          placeholder="faithfulness"
                        />
                      </Field>
                      <Field label="Model">
                        <input
                          list="judge-provider-models"
                          value={slot.model}
                          onChange={(event) => updateJudgeSlot(index, { model: event.target.value })}
                          placeholder="Select an available model"
                          className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs text-foreground outline-none focus:border-accent"
                        />
                      </Field>
                      <Field label="Evaluation focus">
                        <textarea
                          rows={3}
                          value={slot.focus}
                          onChange={(event) => updateJudgeSlot(index, { focus: event.target.value })}
                          className="w-full resize-y rounded-md border border-border bg-background px-3 py-2 text-xs leading-5 text-foreground outline-none focus:border-accent"
                        />
                      </Field>
                    </div>
                  );
                })}
                <datalist id="judge-provider-models">
                  {judgeModels.map((model) => <option key={model} value={model} />)}
                </datalist>
              </div>
            )}

            <ReadOnlyValue value={judgeStatus || (
              judgeConfiguration.mode === "committee"
                ? `${judgeConfiguration.committee.filter((slot) => slot.model && slot.model !== generatorModel).length} eligible independent models configured.`
                : "Committee assignments are retained when another mode is selected."
            )} />
          </Section>

          <Section title="Local" description="Local Ollama settings for offline processing.">
            <ReadOnlyValue value="Ollama URL and all four model slots are tested and saved through unified AI setup." />
            <button
              className="bb-action h-9 px-4 text-xs font-semibold"
              onClick={() => window.dispatchEvent(new Event("bb:open-ai-setup"))}
            >
              Configure local Ollama
            </button>
          </Section>

          <Section title="Graph behavior" description="Configure deterministic graph presentation and candidate generation rules.">
            <Field label="Auto-confirm confidence" description="Suggested graph connections above this confidence can be confirmed automatically after required validation.">
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
            <Field label="Minimum shared concepts" description="Single generic words never connect notes. Set how many independent shared concepts qualify a deterministic relationship.">
              <TextInput value={s.graph_min_shared_concepts} onChange={(value) => update("graph_min_shared_concepts", value)} placeholder="2" />
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
              <MaintenanceButton onClick={prepareSemanticGraph}>Prepare semantic graph</MaintenanceButton>
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
                      {diagnostics.staleRunning.slice(0, 10).map((j) => (
                        <li key={j.id} className="rounded-lg bg-surface px-2 py-1 text-[11px] text-muted ring-1 ring-border/30">
                          {j.type} — {String(j.id).slice(0, 8)}… {j.started_at ? `since ${new Date(j.started_at).toLocaleTimeString()}` : ""}
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
          </SettingsFilterContext.Provider>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border/50 px-6 py-3">
          <p className="text-xs text-muted" role="status">{settingsLoading ? "Loading settings..." : saveStatus}</p>
          <div className="flex gap-2">
          <button className="bb-action h-9 px-4 text-xs font-medium" onClick={requestClose}>Cancel</button>
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
  const { area, query } = useContext(SettingsFilterContext);
  const areas = SECTION_AREAS[title] || ["General"];
  const normalizedQuery = query.trim().toLowerCase();
  const searchable = `${title} ${description} ${reactNodeText(children)}`.toLowerCase();
  if (
    !areas.includes(area) ||
    (normalizedQuery && !searchable.includes(normalizedQuery))
  ) {
    return null;
  }
  return (
    <section className="border-b border-border py-4 last:border-b-0">
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      <p className="mt-1 text-xs text-muted/75">{description}</p>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function reactNodeText(node: React.ReactNode): string {
  if (typeof node === "string" || typeof node === "number") return String(node);
  if (Array.isArray(node)) return node.map(reactNodeText).join(" ");
  if (node && typeof node === "object" && "props" in node) {
    const props = (node as React.ReactElement<{ children?: React.ReactNode }>).props;
    return reactNodeText(props.children);
  }
  return "";
}

function SetupStep({ title, ready, detail }: { title: string; ready: boolean; detail: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-panel px-3 py-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-medium text-foreground">{title}</span>
        <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${ready ? "bg-emerald-500/10 text-emerald-700" : "bg-amber-500/10 text-amber-700"}`}>
          {ready ? "Ready" : "Needs setup"}
        </span>
      </div>
      <p className="mt-1 text-[11px] leading-4 text-muted/70">{detail}</p>
    </div>
  );
}

function Field({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <label className="block min-w-0">
      <span className="block text-xs font-medium text-foreground">{label}</span>
      {description && <span className="mb-1.5 mt-0.5 block break-words text-[11px] leading-4 text-muted/70">{description}</span>}
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
        <div className="flex flex-col items-end gap-0.5">
          {status.lastTestLatencyMs ? <span className="text-[10px] tabular-nums text-muted">{status.lastTestLatencyMs} ms</span> : null}
          {status.lastTestAt ? <span className="text-[10px] tabular-nums text-muted/60">{new Date(status.lastTestAt).toLocaleString()}</span> : null}
        </div>
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
