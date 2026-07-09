"use client";

import { useEffect, useState } from "react";

type ThemeKind = "light" | "dark" | "oled" | "sepia" | "rose" | "sky" | "mint" | "graphite";

const THEME_PRESETS: Record<ThemeKind, { bg: string; fg: string; mu: string; pn: string; bd: string }> = {
  light:    { bg: "#F7F1E8", fg: "#3E3024", mu: "#7A6A5C", pn: "#FFF9EF", bd: "#E6D8C6" },
  dark:     { bg: "#1a1816", fg: "#e8e4df", mu: "#8b8580", pn: "#252320", bd: "#35312c" },
  oled:     { bg: "#000000", fg: "#d4d4d4", mu: "#555555", pn: "#0a0a0a", bd: "#1a1a1a" },
  sepia:    { bg: "#f8f1e4", fg: "#4a3b2c", mu: "#8b7765", pn: "#fef9f0", bd: "#d6c8b8" },
  rose:     { bg: "#fdf2f3", fg: "#3d2123", mu: "#a07a7d", pn: "#fff8f9", bd: "#eed5d8" },
  sky:      { bg: "#f0f5fb", fg: "#1e3349", mu: "#6a8aa3", pn: "#f8fbfe", bd: "#d4e2f2" },
  mint:     { bg: "#f0f9f3", fg: "#1a3d28", mu: "#5c8a6a", pn: "#f6fcf8", bd: "#c8e6d3" },
  graphite: { bg: "#f4f4f5", fg: "#1f1f21", mu: "#6b6b6e", pn: "#fafafa", bd: "#e4e4e7" },
};

const ACCENT_PRESETS = [
  "#D98A00", "#C51A4A", "#e05d44", "#db2777",
  "#a855f7", "#6366f1", "#3b82f6", "#0ea5e9",
  "#14b8a6", "#10b981", "#22c55e", "#65a30d",
  "#eab308",
];

const UI_FONTS: Record<string, string> = {
  inter:  '"Inter", ui-sans-serif, system-ui, sans-serif',
  system: 'ui-sans-serif, system-ui, -apple-system, sans-serif',
  serif:  '"Georgia", "Times New Roman", serif',
  roboto: '"Roboto", ui-sans-serif, system-ui, sans-serif',
};

const EDITOR_FONTS: Record<string, string> = {
  mono:   '"JetBrains Mono", "Fira Code", ui-monospace, monospace',
  sans:   'ui-sans-serif, system-ui, sans-serif',
  serif:  '"Georgia", "Times New Roman", serif',
};

const CLOUD_PROVIDERS: Record<string, string> = {
  "": "Custom (cole a URL)",
  "https://api.openai.com/v1": "OpenAI",
  "https://api.deepseek.com/v1": "DeepSeek",
  "https://integrate.api.nvidia.com/v1": "NVIDIA NIM",
  "https://api.z.ai/v1": "Z.AI",
  "https://api.groq.com/openai/v1": "Groq",
  "https://api.mistral.ai/v1": "Mistral",
  "https://api.together.xyz/v1": "Together AI",
  "https://api.fireworks.ai/inference/v1": "Fireworks",
  "https://openrouter.ai/api/v1": "OpenRouter",
  "https://api.anthropic.com/v1": "Anthropic (OpenAI compat)",
};

type Settings = {
  theme: ThemeKind;
  accent: string;
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
  graph_ollama_model: string;
  graph_auto_confirm_confidence: string;
  graph_default_layout: "brain" | "radial" | "type" | "connections";
};

function defaults(): Settings {
  return { theme: "light", accent: "#D98A00", font_size: "15", editor_font_size: "15", ui_font: "inter", editor_font: "mono", nome: "Mateus", ai_provider: "local", ai_api_url: "", ai_custom_url: "", ai_api_key: "", ai_model: "", graph_ai_provider: "local", graph_ai_api_url: "", graph_ai_api_key: "", graph_ai_model: "", graph_ollama_model: "qwen3:8b", graph_auto_confirm_confidence: "0.9", graph_default_layout: "brain" };
}

function loadSettings(): Settings {
  if (typeof window === "undefined") return defaults();
  return {
    theme: (localStorage.getItem("bb_theme") as ThemeKind) || "light",
    accent: localStorage.getItem("bb_accent") || "#D98A00",
    font_size: localStorage.getItem("bb_font_size") || "15",
    editor_font_size: localStorage.getItem("bb_editor_font_size") || "15",
    ui_font: localStorage.getItem("bb_ui_font") || "inter",
    editor_font: localStorage.getItem("bb_editor_font") || "mono",
    nome: localStorage.getItem("bb_nome") || "Mateus",
    ai_provider: (localStorage.getItem("bb_ai_provider") as "local" | "cloud") || "local",
    ai_api_url: localStorage.getItem("bb_ai_api_url") || "",
    ai_custom_url: localStorage.getItem("bb_ai_custom_url") || "",
    ai_api_key: localStorage.getItem("bb_ai_api_key") || "",
    ai_model: localStorage.getItem("bb_ai_model") || "",
    graph_ai_provider: (localStorage.getItem("bb_graph_ai_provider") as "local" | "cloud") || "local",
    graph_ai_api_url: localStorage.getItem("bb_graph_ai_api_url") || "",
    graph_ai_api_key: localStorage.getItem("bb_graph_ai_api_key") || "",
    graph_ai_model: localStorage.getItem("bb_graph_ai_model") || "",
    graph_ollama_model: localStorage.getItem("bb_graph_ollama_model") || "qwen3:8b",
    graph_auto_confirm_confidence: localStorage.getItem("bb_graph_auto_confirm_confidence") || "0.9",
    graph_default_layout: (localStorage.getItem("bb_graph_default_layout") as Settings["graph_default_layout"]) || "brain",
  };
}

function applyTheme(s: Settings) {
  const r = document.documentElement;
  const p = THEME_PRESETS[s.theme] || THEME_PRESETS.light;
  r.style.setProperty("--color-background", p.bg);
  r.style.setProperty("--color-foreground", p.fg);
  r.style.setProperty("--color-muted", p.mu);
  r.style.setProperty("--color-panel", p.pn);
  r.style.setProperty("--color-border", p.bd);
  r.style.setProperty("--color-accent", s.accent);
  document.body.style.fontSize = `${s.font_size}px`;
  r.style.setProperty("--font-ui", UI_FONTS[s.ui_font] || UI_FONTS.inter);
  r.style.setProperty("--font-editor", EDITOR_FONTS[s.editor_font] || EDITOR_FONTS.mono);
  document.body.style.fontFamily = `var(--font-ui)`;
}

export function initTheme() { applyTheme(loadSettings()); }

export function SettingsPanel({ open, onClose, apiUrl }: { open: boolean; onClose: () => void; apiUrl: string }) {
  const [s, setS] = useState<Settings>(loadSettings);
  const [saving, setSaving] = useState(false);
  const [cloudModels, setCloudModels] = useState<{ id: string }[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);

  const [cloudError, setCloudError] = useState("");

  async function fetchModels() {
    const baseUrl = s.ai_api_url || s.ai_custom_url;
    setLoadingModels(true);
    setCloudError("");
    try {
      const r = await fetch(`${apiUrl}/api/v1/settings/ai/models?url=${encodeURIComponent(baseUrl)}&key=${encodeURIComponent(s.ai_api_key)}`);
      const d = await r.json();
      if (d.error) { setCloudError(d.error); setCloudModels([]); }
      else { setCloudModels(d.models || []); }
      if (!d.error && !d.models?.length) setCloudError("Nenhum modelo encontrado.");
    } catch (e: any) { setCloudError(`Falha: ${e.message}`); }
    finally { setLoadingModels(false); }
  }

  useEffect(() => {
    if (!open) return;
    fetch(`${apiUrl}/api/v1/settings`).then(r => r.json()).then(d => {
      const map: Record<string, keyof Settings> = { theme: "theme", accent: "accent", font_size: "font_size", editor_font_size: "editor_font_size", ui_font: "ui_font", editor_font: "editor_font", nome: "nome", ai_provider: "ai_provider", ai_api_url: "ai_api_url", ai_custom_url: "ai_custom_url", ai_api_key: "ai_api_key", ai_model: "ai_model", graph_ai_provider: "graph_ai_provider", graph_ai_api_url: "graph_ai_api_url", graph_ai_api_key: "graph_ai_api_key", graph_ai_model: "graph_ai_model", graph_ollama_model: "graph_ollama_model", graph_auto_confirm_confidence: "graph_auto_confirm_confidence", graph_default_layout: "graph_default_layout" };
      for (const item of d.settings || []) {
        const k = map[item.key] as keyof Settings;
        if (k) setS(prev => ({ ...prev, [k]: item.value }));
      }
    }).catch(() => {});
  }, [open, apiUrl]);

  function update<K extends keyof Settings>(key: K, value: Settings[K]) {
    const n = { ...s, [key]: value };
    setS(n); applyTheme(n);
    localStorage.setItem(`bb_${key}`, String(value));
  }

  async function save() {
    setSaving(true);
    try {
      const keys: (keyof Settings)[] = ["theme", "accent", "font_size", "editor_font_size", "ui_font", "editor_font", "nome", "ai_provider", "ai_api_url", "ai_custom_url", "ai_api_key", "ai_model", "graph_ai_provider", "graph_ai_api_url", "graph_ai_api_key", "graph_ai_model", "graph_ollama_model", "graph_auto_confirm_confidence", "graph_default_layout"];
      await Promise.all(keys.map(k => fetch(`${apiUrl}/api/v1/settings/${k}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ value: String(s[k]) }) })));
    } catch {}
    setSaving(false); onClose();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-16">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px]" onClick={e => { e.stopPropagation(); onClose(); }} />
      <div className="relative z-50 w-[440px] overflow-hidden rounded-2xl bg-panel shadow-2xl ring-1 ring-black/5" role="dialog" aria-label="Configuracoes">
        <div className="flex items-center justify-between px-6 py-4">
          <h2 className="text-base font-semibold tracking-tight">Aparencia</h2>
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface hover:text-foreground" onClick={onClose} aria-label="Fechar">
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="max-h-[62vh] space-y-5 overflow-y-auto px-6 pb-6">
          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Nome</legend>
            <input
              type="text"
              className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent"
              value={s.nome}
              onChange={e => update("nome", e.target.value)}
              placeholder="Seu nome"
              maxLength={40}
            />
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Tema</legend>
            <div className="grid grid-cols-4 gap-1.5">
              {(Object.keys(THEME_PRESETS) as ThemeKind[]).map(t => {
                const p = THEME_PRESETS[t];
                return (
                  <button key={t} className={`rounded-xl border p-2 text-center text-[11px] transition ${s.theme === t ? "border-foreground/30 bg-surface" : "border-transparent hover:bg-surface/50"}`} onClick={() => update("theme", t)}>
                    <div className="mx-auto mb-1 size-5 rounded-md ring-1 ring-black/10" style={{ background: p.bg }} />
                    <span className="capitalize text-[10px]">{t}</span>
                  </button>
                );
              })}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Cor de destaque</legend>
            <div className="flex flex-wrap gap-1.5">
              {ACCENT_PRESETS.map(c => (
                <button key={c} className={`size-7 rounded-full transition ${s.accent === c ? "ring-2 ring-offset-1 ring-offset-panel ring-foreground" : ""}`} style={{ background: c }} onClick={() => update("accent", c)} aria-label={c} />
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Fonte da interface</legend>
            <div className="grid grid-cols-2 gap-1.5">
              {Object.entries(UI_FONTS).map(([k, v]) => (
                <button key={k} className={`rounded-lg px-3 py-2 text-xs text-left truncate transition ${s.ui_font === k ? "bg-surface font-medium text-foreground" : "text-muted hover:bg-surface/50"}`} onClick={() => update("ui_font", k)}>
                  <span className="block" style={{ fontFamily: v }}>{k.charAt(0).toUpperCase() + k.slice(1)}</span>
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Fonte do editor</legend>
            <div className="grid grid-cols-3 gap-1.5">
              {Object.entries(EDITOR_FONTS).map(([k, v]) => (
                <button key={k} className={`rounded-lg px-3 py-2 text-xs text-center transition ${s.editor_font === k ? "bg-surface font-medium text-foreground" : "text-muted hover:bg-surface/50"}`} style={{ fontFamily: v }} onClick={() => update("editor_font", k)}>
                  {k}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Tamanho da interface &mdash; <span className="tabular-nums">{s.font_size}px</span></legend>
            <input type="range" min="12" max="20" value={s.font_size} onChange={e => update("font_size", e.target.value)} className="h-1 w-full cursor-pointer appearance-none rounded-full bg-border accent-accent" />
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-medium text-muted">Tamanho do editor &mdash; <span className="tabular-nums">{s.editor_font_size}px</span></legend>
            <input type="range" min="13" max="22" value={s.editor_font_size} onChange={e => update("editor_font_size", e.target.value)} className="h-1 w-full cursor-pointer appearance-none rounded-full bg-border accent-accent" />
          </fieldset>

          <div className="border-t border-border/30 pt-4">
            <h3 className="mb-3 text-xs font-medium text-muted">Provedor de IA</h3>
            <div className="grid grid-cols-2 gap-1.5 mb-3">
              {(["local", "cloud"] as const).map(p => (
                <button key={p} className={`rounded-lg px-3 py-2 text-xs transition ${s.ai_provider === p ? "bg-accent-soft text-accent font-medium ring-1 ring-accent/20" : "text-muted hover:bg-surface/50 bg-surface"}`}
                  onClick={() => update("ai_provider", p)}>
                  {p === "local" ? "Local (Ollama)" : "Cloud (API)"}
                </button>
              ))}
            </div>
            {s.ai_provider === "cloud" && (
              <div className="space-y-2">
                <div className="flex gap-1.5">
                  <select className="h-9 flex-1 rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent"
                    value={s.ai_api_url}
                    onChange={e => { update("ai_api_url", e.target.value); setCloudModels([]); }}>
                    {Object.entries(CLOUD_PROVIDERS).map(([url, label]) => <option key={url} value={url}>{label}</option>)}
                  </select>
                </div>
                {s.ai_api_url === "" && (
                  <input type="url" className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.ai_custom_url || ""} onChange={e => update("ai_custom_url", e.target.value)} placeholder="https://api.exemplo.com/v1" />
                )}
                <input type="password" className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.ai_api_key} onChange={e => update("ai_api_key", e.target.value)} placeholder="API Key" />
                <div className="flex gap-1.5">
                  <select className="h-9 flex-1 rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.ai_model} onChange={e => update("ai_model", e.target.value)}>
                    <option value="">{loadingModels ? "Carregando..." : cloudModels.length ? "Selecionar modelo..." : "Carregue os modelos"}</option>
                    {cloudModels.map(m => <option key={m.id} value={m.id}>{m.id}</option>)}
                  </select>
                  <button className="h-9 shrink-0 rounded-xl bg-surface px-3 text-xs text-muted hover:text-foreground disabled:opacity-30"
                    disabled={!s.ai_api_key || loadingModels}
                    onClick={fetchModels}>
                    {loadingModels ? "..." : "Carregar"}
                  </button>
                </div>
                {cloudError && <p className="text-[11px] text-red-400">{cloudError}</p>}
              </div>
            )}
          </div>

          <div className="border-t border-border/30 pt-4">
            <h3 className="mb-3 text-xs font-medium text-muted">IA do grafo</h3>
            <p className="mb-3 text-[11px] text-muted/60">Usada para inferencia, conexoes explicadas e expansao do segundo cerebro.</p>
            <div className="grid grid-cols-2 gap-1.5 mb-3">
              {(["local", "cloud"] as const).map(p => (
                <button key={p} className={`rounded-lg px-3 py-2 text-xs transition ${s.graph_ai_provider === p ? "bg-accent-soft text-accent font-medium ring-1 ring-accent/20" : "text-muted hover:bg-surface/50 bg-surface"}`}
                  onClick={() => update("graph_ai_provider", p)}>
                  {p === "local" ? "Local" : "Cloud"}
                </button>
              ))}
            </div>
            {s.graph_ai_provider === "cloud" ? (
              <div className="space-y-2">
                <input type="url" className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_ai_api_url || ""} onChange={e => update("graph_ai_api_url", e.target.value)} placeholder="URL OpenAI-compatible para o grafo" />
                <input type="password" className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_ai_api_key || ""} onChange={e => update("graph_ai_api_key", e.target.value)} placeholder="API Key do grafo" />
                <input className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_ai_model || ""} onChange={e => update("graph_ai_model", e.target.value)} placeholder="Modelo para inferencia do grafo" />
              </div>
            ) : (
              <input className="h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_ollama_model || ""} onChange={e => update("graph_ollama_model", e.target.value)} placeholder="Modelo Ollama para o grafo" />
            )}
            <div className="mt-3 grid grid-cols-2 gap-2">
              <label className="text-[11px] text-muted">
                Auto-confirmar acima de
                <input className="mt-1 h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_auto_confirm_confidence} onChange={e => update("graph_auto_confirm_confidence", e.target.value)} placeholder="0.9" />
              </label>
              <label className="text-[11px] text-muted">
                Layout padrao
                <select className="mt-1 h-9 w-full rounded-xl border border-border bg-surface px-3 text-sm outline-none focus:border-accent" value={s.graph_default_layout} onChange={e => update("graph_default_layout", e.target.value as Settings["graph_default_layout"])}>
                  <option value="brain">Brain View</option>
                  <option value="radial">Radial</option>
                  <option value="type">Por tipo</option>
                  <option value="connections">Centralidade</option>
                </select>
              </label>
            </div>
          </div>

          <div className="border-t border-border/30 pt-4">
            <h3 className="mb-2 text-xs font-medium text-red-500">Zona de perigo</h3>
            <p className="text-[11px] text-muted/60 mb-2">Apaga todos os dados. Irreversivel.</p>
            <button className="h-9 w-full rounded-xl border border-red-200 bg-red-50 px-3 text-xs font-medium text-red-600 hover:bg-red-100" onClick={() => {
              const c = window.prompt('Digite "berrybrain-reset-all":');
              if (c !== "berrybrain-reset-all") return;
              fetch(`${apiUrl}/api/v1/system/reset`, { method: "POST", headers: { "Content-Type": "application/json", "Authorization": `Bearer ${localStorage.getItem("bb_token") || ""}` }, body: JSON.stringify({ confirm: "berrybrain-reset-all" }) }).then(async r => { if (!r.ok) { const e = await r.json().catch(() => ({})); alert(`Erro ${r.status}: ${e.detail || "falha ao resetar"}`); return; } onClose(); location.reload(); }).catch(e => alert(`Erro: ${e.message}`));
            }}>Apagar todos os dados</button>
          </div>
        </div>

        <div className="flex justify-end gap-2 border-t border-border/50 px-6 py-3">
          <button className="h-9 rounded-lg px-4 text-xs font-medium text-muted hover:text-foreground" onClick={onClose}>Cancelar</button>
          <button className="h-9 rounded-lg bg-foreground px-4 text-xs font-medium text-background hover:opacity-90 disabled:opacity-40" onClick={save} disabled={saving}>{saving ? "Salvando..." : "Salvar"}</button>
        </div>
      </div>
    </div>
  );
}
