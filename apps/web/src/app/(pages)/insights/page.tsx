"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";

type InsightItem = {
  id: number;
  type: string;
  title: string;
  description: string;
  relatedNotes: Array<{ id: number; title: string; path: string } | string>;
  relatedConcepts: string[];
  priority: string;
  suggestedAction?: string;
  whyItMatters?: string;
  reasoning?: string;
  evidence?: any[];
  graphImpact?: string;
  confidence: number;
  status: string;
  provider: string;
  model: string;
  promptVersion?: string;
  createdAt: string;
  appliedAt?: string | null;
  ignoredAt?: string | null;
};

const TYPE_LABELS: Record<string, string> = {
  knowledge_gap: "Falta explorar",
  new_connection: "Nova conexão",
  recurring_concept: "Conceito recorrente",
  weak_concept: "Conceito fraco",
  isolated_note: "Nota isolada",
  duplicate_content: "Duplicidade",
  permanent_note_candidate: "Nota sugerida",
  study_path: "Trilha de estudo",
  review_opportunity: "Revisão sugerida",
  possible_contradiction: "Possível conflito",
  emerging_context: "Contexto emergente",
  context: "Tema central",
  conclusion: "Relação confirmada",
  hypothesis: "Possível conexão",
  premise: "Padrão recorrente",
  assertion: "Evidência forte",
  weak_note: "Nota a fortalecer",
};

const FILTERS = [
  { key: "all", label: "Todos" },
  { key: "knowledge_gap", label: "Lacunas" },
  { key: "new_connection", label: "Conexões" },
  { key: "review_opportunity", label: "Revisão" },
  { key: "context", label: "Contexto" },
  { key: "high", label: "Alta prior" },
  { key: "applied", label: "Aplicados" },
  { key: "ignored", label: "Ignorados" },
];

export default function InsightsPage() {
  const api = getApiUrl();
  const [insights, setInsights] = useState<InsightItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");
  const [generating, setGenerating] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadInsights = useCallback(async () => {
    setLoading(true);
    try {
      const r = await fetch(`${api}/api/v1/insights?limit=50`);
      if (r.ok) {
        const data = await r.json();
        const raw = data.insights || [];
        setInsights(raw.map(normalizeInsight));
      }
    } catch {}
    setLoading(false);
  }, [api]);

  useEffect(() => { loadInsights(); }, [loadInsights]);

  const generateNow = async () => {
    setGenerating(true);
    setFeedback(null);
    try {
      const r = await fetch(`${api}/api/v1/insights/generate`, { method: "POST" });
      if (r.ok) {
        const data = await r.json();
        setFeedback(`Job #${data.job_id} criado. O worker processará e os insights aparecerão aqui em instantes.`);
      } else {
        setFeedback("Erro ao criar job de insights.");
      }
    } catch {
      setFeedback("Erro de conexão ao gerar insights.");
    }
    setGenerating(false);
    setTimeout(() => loadInsights(), 3000);
    setTimeout(() => loadInsights(), 10000);
    setTimeout(() => loadInsights(), 30000);
  };

  const dismissInsight = async (id: number, action: "apply" | "ignore") => {
    try {
      const r = await fetch(`${api}/api/v1/insights/${id}/${action}`, { method: "POST" });
      if (r.ok) setFeedback(action === "apply" ? "Insight aplicado." : "Insight ignorado.");
      setTimeout(() => setFeedback(null), 3000);
      await loadInsights();
    } catch {}
  };

  const createNote = async (insight: InsightItem) => {
    try {
      await fetch(`${api}/api/v1/insights/${insight.id}/create-note`, { method: "POST" });
      setFeedback("Job de criação de nota enviado.");
      setTimeout(() => setFeedback(null), 3000);
    } catch {}
  };

  const createReview = async (insight: InsightItem) => {
    try {
      await fetch(`${api}/api/v1/insights/${insight.id}/create-review`, { method: "POST" });
      setFeedback("Job de criação de revisão enviado.");
      setTimeout(() => setFeedback(null), 3000);
    } catch {}
  };

  const openNote = (path: string) => {
    window.location.href = `/?note=${encodeURIComponent(path)}`;
  };

  const filtered = insights.filter((i) => {
    if (filter === "all") return true;
    if (filter === "high") return i.priority === "high";
    if (filter === "applied") return i.status === "applied";
    if (filter === "ignored") return i.status === "ignored";
    return i.type === filter;
  });

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8 text-center text-sm text-muted/40 animate-pulse-soft">Carregando insights...</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <header className="mb-6">
          <h1 className="text-xl font-semibold">Insights da IA</h1>
          <p className="mt-1 text-sm text-muted/60">
            Descobertas, lacunas, críticas e sugestões geradas automaticamente pela IA.
          </p>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-xs text-muted/60">{filtered.length} de {insights.length} insights</span>
            <button
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
              onClick={generateNow}
              disabled={generating}
            >
              {generating ? "Enviando..." : "Forçar geração agora"}
            </button>
            <span className="text-[11px] text-muted/40">(os insights já são gerados automaticamente)</span>
          </div>
          {feedback && (
            <div className="mt-3 rounded-lg bg-accent/10 px-3 py-2 text-xs text-accent">{feedback}</div>
          )}
        </header>

        <div className="mb-4 flex items-center gap-1 text-xs">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`rounded-lg px-2.5 py-1 transition ${
                filter === f.key ? "bg-accent/10 text-accent font-medium" : "text-muted hover:bg-surface hover:text-foreground"
              }`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <div className="rounded-xl bg-surface p-8 text-center ring-1 ring-border/35">
            <p className="text-sm font-medium text-muted/60">Nenhum insight disponível.</p>
            <p className="mt-2 text-xs text-muted/40">
              O BerryBrain gera insights automaticamente ao encontrar padrões entre suas notas.
              Escreva mais notas, execute a assimilação e os insights surgirão.
            </p>
            <button
              className="mt-4 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
              onClick={generateNow}
              disabled={generating}
            >
              {generating ? "Enviando..." : "Gerar primeiro insight"}
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {filtered.map((insight) => (
              <InsightCard
                key={insight.id}
                insight={insight}
                onDismiss={dismissInsight}
                onCreateNote={() => createNote(insight)}
                onCreateReview={() => createReview(insight)}
                onOpenNote={openNote}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function normalizeInsight(raw: any): InsightItem {
  return {
    id: raw.id,
    type: raw.type || "",
    title: raw.title || "",
    description: raw.description || "",
    relatedNotes: Array.isArray(raw.relatedNotes) ? raw.relatedNotes : [],
    relatedConcepts: raw.relatedConcepts || [],
    priority: raw.priority || "medium",
    suggestedAction: raw.suggestedAction || raw.suggested_action || "",
    whyItMatters: raw.whyItMatters || raw.why_it_matters || "",
    reasoning: raw.reasoning || "",
    evidence: typeof raw.evidence === "string" ? safeParse(raw.evidence) : (raw.evidence || []),
    graphImpact: raw.graphImpact || raw.graph_impact || "",
    confidence: raw.confidence || 0,
    status: raw.status || "new",
    provider: raw.provider || "",
    model: raw.model || "",
    promptVersion: raw.promptVersion || raw.prompt_version || "",
    createdAt: raw.createdAt || raw.created_at || "",
    appliedAt: raw.appliedAt || raw.applied_at || null,
    ignoredAt: raw.ignoredAt || raw.ignored_at || null,
  };
}

function safeParse(v: string): any[] {
  try { const p = JSON.parse(v); return Array.isArray(p) ? p : []; } catch { return []; }
}

function InsightCard({
  insight,
  onDismiss,
  onCreateNote,
  onCreateReview,
  onOpenNote,
}: {
  insight: InsightItem;
  onDismiss: (id: number, action: "apply" | "ignore") => void;
  onCreateNote: () => void;
  onCreateReview: () => void;
  onOpenNote: (path: string) => void;
}) {
  const typeLabel = TYPE_LABELS[insight.type] || insight.type;
  const priorityColor =
    insight.priority === "high" ? "text-red-500" : insight.priority === "medium" ? "text-amber-500" : "text-emerald-500";
  const confidencePct = Math.round((insight.confidence || 0) * 100);

  return (
    <article className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[10px] font-semibold uppercase text-accent">{typeLabel}</span>
        <span className={`text-[10px] ${priorityColor}`}>
          {insight.priority === "high" ? "Alta" : insight.priority === "medium" ? "Média" : "Baixa"} prioridade
        </span>
        {confidencePct > 0 && (
          <span className="text-[10px] text-muted/50">{confidencePct}% confiança</span>
        )}
        {insight.status !== "new" && (
          <span className="text-[10px] text-muted/40 ml-auto">{insight.status === "applied" ? "Aplicado" : "Ignorado"}</span>
        )}
      </div>

      <h3 className="text-sm font-medium">{insight.title}</h3>
      {insight.description && <p className="mt-1 text-xs text-muted/60">{insight.description}</p>}

      {insight.reasoning && (
        <div className="mt-2 rounded-lg bg-black/[0.03] px-3 py-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-0.5">Raciocínio</div>
          <p className="text-xs text-muted/60">{insight.reasoning}</p>
        </div>
      )}

      {insight.whyItMatters && (
        <div className="mt-2 rounded-lg bg-accent/[0.04] px-3 py-2">
          <div className="text-[10px] font-medium uppercase text-accent/60 mb-0.5">Por que importa</div>
          <p className="text-xs text-accent/70">{insight.whyItMatters}</p>
        </div>
      )}

      {insight.evidence && insight.evidence.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-1">Evidências</div>
          <div className="flex flex-wrap gap-1.5">
            {insight.evidence.map((e, i) => {
              const text = typeof e === "string" ? e : e?.quoteOrSummary || e?.whyRelevant || JSON.stringify(e).slice(0, 80);
              return (
                <span key={i} className="rounded-lg bg-black/[0.04] px-2 py-0.5 text-[11px] text-muted/55">
                  {text.length > 100 ? text.slice(0, 100) + "…" : text}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {insight.suggestedAction && (
        <div className="mt-2 text-xs text-accent">
          Ação sugerida: {insight.suggestedAction}
        </div>
      )}

      {insight.relatedNotes && insight.relatedNotes.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-1">Notas relacionadas</div>
          <div className="flex flex-wrap gap-1">
            {insight.relatedNotes.map((n, i) => {
              const path = typeof n === "string" ? n : n.path;
              const title = typeof n === "string" ? path?.split("/").pop()?.replace(".md", "") || n : n.title || n.path;
              if (!path) return null;
              return (
                <button
                  key={i}
                  className="rounded-full bg-panel px-2.5 py-0.5 text-[11px] text-muted hover:text-accent hover:underline transition"
                  onClick={() => onOpenNote(path)}
                >
                  {title}
                </button>
              );
            })}
          </div>
        </div>
      )}

      <div className="mt-3 flex items-center gap-2 text-[10px] text-muted/40">
        {insight.provider && <span>{insight.provider}</span>}
        {insight.model && <span>· {insight.model}</span>}
        {insight.promptVersion && <span>· {insight.promptVersion}</span>}
        {insight.createdAt && (
          <span className="ml-auto">{new Date(insight.createdAt).toLocaleString("pt-BR")}</span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={onCreateNote}>
          Criar nota permanente
        </button>
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={onCreateReview}>
          Gerar revisão
        </button>
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={() => window.location.href = "/?graph=open"}>
          Ver no grafo
        </button>
        {insight.status === "new" && (
          <>
            <button className="rounded-lg bg-panel px-2.5 py-1 text-emerald-600 hover:text-emerald-700" onClick={() => onDismiss(insight.id, "apply")}>
              Aplicar
            </button>
            <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-red-500" onClick={() => onDismiss(insight.id, "ignore")}>
              Ignorar
            </button>
          </>
        )}
      </div>
    </article>
  );
}