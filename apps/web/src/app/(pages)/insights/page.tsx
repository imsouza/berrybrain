"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiUrl, appPath } from "@/contexts/workspace-context";
import { getLang, t, tf } from "@/i18n";

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
  knowledge_gap: "ins_knowledge_gap",
  new_connection: "ins_new_connection",
  recurring_concept: "ins_recurring_concept",
  weak_concept: "ins_weak_concept",
  isolated_note: "ins_isolated_note",
  duplicate_content: "ins_duplicate_content",
  permanent_note_candidate: "ins_permanent_note_candidate",
  study_path: "ins_study_path",
  review_opportunity: "ins_review_opportunity",
  possible_contradiction: "ins_possible_contradiction",
  emerging_context: "ins_emerging_context",
  context: "ins_context",
  conclusion: "ins_conclusion",
  hypothesis: "ins_hypothesis",
  premise: "ins_premise",
  assertion: "ins_assertion",
  weak_note: "ins_weak_note",
};

const FILTERS = [
  { key: "all", label: "filterAll" },
  { key: "knowledge_gap", label: "filterLacunas" },
  { key: "new_connection", label: "filterConexoes" },
  { key: "review_opportunity", label: "filterRevisao" },
  { key: "context", label: "filterContexto" },
  { key: "high", label: "filterAltaPrioridade" },
  { key: "applied", label: "filterAplicados" },
  { key: "ignored", label: "filterIgnorados" },
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
        setFeedback(`${t("jobCreated")} #${data.job_id} ${t("jobCreatedTail")}`);
      } else {
        setFeedback(t("errorCreateJob"));
      }
    } catch {
      setFeedback(t("connectionErrorInsights"));
    }
    setGenerating(false);
    setTimeout(() => loadInsights(), 3000);
    setTimeout(() => loadInsights(), 10000);
    setTimeout(() => loadInsights(), 30000);
  };

  const dismissInsight = async (id: number, action: "apply" | "ignore") => {
    try {
      const r = await fetch(`${api}/api/v1/insights/${id}/${action}`, { method: "POST" });
      if (r.ok) setFeedback(action === "apply" ? t("insightApplied") : t("insightIgnored"));
      setTimeout(() => setFeedback(null), 3000);
      await loadInsights();
    } catch {}
  };

  const createNote = async (insight: InsightItem) => {
    try {
      await fetch(`${api}/api/v1/insights/${insight.id}/create-note`, { method: "POST" });
      setFeedback(t("createNoteJobSent"));
      setTimeout(() => setFeedback(null), 3000);
    } catch {}
  };

  const createReview = async (insight: InsightItem) => {
    try {
      await fetch(`${api}/api/v1/insights/${insight.id}/create-review`, { method: "POST" });
      setFeedback(t("createReviewJobSent"));
      setTimeout(() => setFeedback(null), 3000);
    } catch {}
  };

  const openNote = (path: string) => {
    window.location.href = appPath(`/brain?note=${encodeURIComponent(path)}`);
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
        <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8 text-center text-sm text-muted/40 animate-pulse-soft">{t("loadingInsights")}</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <header className="mb-6">
          <h1 className="text-xl font-semibold">{t("insightsTitle")}</h1>
          <p className="mt-1 text-sm text-muted/60">
            {t("insightsDesc")}
          </p>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-xs text-muted/60">{tf("insightsCount", { filtered: filtered.length, total: insights.length })}</span>
            <button
              className="rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
              onClick={generateNow}
              disabled={generating}
            >
              {generating ? t("sending") : t("forceGenerate")}
            </button>
            <span className="text-[11px] text-muted/40">{t("autoGeneratedNote")}</span>
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
            <p className="text-sm font-medium text-muted/60">{t("noInsights")}</p>
            <p className="mt-2 text-xs text-muted/40">
              {t("noInsightsDesc")}
            </p>
            <button
              className="mt-4 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
              onClick={generateNow}
              disabled={generating}
            >
              {generating ? t("sending") : t("generateFirstInsight")}
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

function parseMaybeJson(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return value;
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

function formatEvidenceLabel(item: unknown): string {
  const parsed = typeof item === "string" ? parseMaybeJson(item) : item;
  if (typeof parsed === "string") {
    return parsed
      .replace(/\bexplainedConnections\b/g, "explained connections")
      .replace(/\bgraphNotes\b/g, "graph notes")
      .replace(/\bjobsByType\.[A-Z0-9_]+\b/g, "system activity")
      .replace(/\bGENERATE_NOTE_TITLE\b/g, "automatic title generation");
  }
  if (!parsed || typeof parsed !== "object") return "";
  const record = parsed as Record<string, unknown>;
  const parts = [
    record.title || record.label || record.source || "",
    record.text || record.reference || record.path || record.reason || "",
    record.whyRelevant || record.quoteOrSummary || "",
  ].filter(Boolean);
  return parts.join(": ") || "Evidence available in technical details.";
}

function hasTechnicalEvidence(items?: unknown[]): boolean {
  return !!items?.some((item) => {
    if (typeof item !== "string") return true;
    const trimmed = item.trim();
    return trimmed.startsWith("{") || trimmed.startsWith("[");
  });
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
        <span className="text-[10px] font-semibold uppercase text-accent">{t(typeLabel)}</span>
        <span className={`text-[10px] ${priorityColor}`}>
          {insight.priority === "high" ? t("highPriority") : insight.priority === "medium" ? t("mediumPriority") : t("lowPriority")}
        </span>
        {confidencePct > 0 && (
          <span className="text-[10px] text-muted/50">{confidencePct}% {t("confidence")}</span>
        )}
        {insight.status !== "new" && (
          <span className="text-[10px] text-muted/40 ml-auto">{insight.status === "applied" ? t("appliedLabel") : t("ignoredLabel")}</span>
        )}
      </div>

      <h3 className="text-sm font-medium">{insight.title}</h3>
      {insight.description && <p className="mt-1 text-xs text-muted/60">{insight.description}</p>}

      {insight.reasoning && (
        <div className="mt-2 rounded-lg bg-black/[0.03] px-3 py-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-0.5">{t("reasoning")}</div>
          <p className="text-xs text-muted/60">{insight.reasoning}</p>
        </div>
      )}

      {insight.whyItMatters && (
        <div className="mt-2 rounded-lg bg-accent/[0.04] px-3 py-2">
          <div className="text-[10px] font-medium uppercase text-accent/60 mb-0.5">{t("whyItMatters")}</div>
          <p className="text-xs text-accent/70">{insight.whyItMatters}</p>
        </div>
      )}

      {insight.evidence && insight.evidence.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-1">{t("evidences")}</div>
          <div className="flex flex-wrap gap-1.5">
            {insight.evidence.map((e, i) => {
              const text = formatEvidenceLabel(e);
              return (
                <span key={i} className="rounded-lg bg-black/[0.04] px-2 py-0.5 text-[11px] text-muted/55">
                  {text.length > 100 ? text.slice(0, 100) + "…" : text}
                </span>
              );
            })}
          </div>
          {hasTechnicalEvidence(insight.evidence) && (
            <details className="mt-2 rounded-lg bg-black/[0.03] px-3 py-2 text-[10px] text-muted/50">
              <summary className="cursor-pointer text-muted/60">Technical details</summary>
              <pre className="mt-2 max-h-40 overflow-auto whitespace-pre-wrap break-words">
                {JSON.stringify(insight.evidence, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}

      {insight.suggestedAction && (
        <div className="mt-2 text-xs text-accent">
          {t("suggestedActionLabel")} {insight.suggestedAction}
        </div>
      )}

      {insight.relatedNotes && insight.relatedNotes.length > 0 && (
        <div className="mt-2">
          <div className="text-[10px] font-medium uppercase text-muted/50 mb-1">{t("relatedNotes")}</div>
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
          <span className="ml-auto">{new Date(insight.createdAt).toLocaleString(getLang() === "en" ? "en-US" : "pt-BR")}</span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={onCreateNote}>
          {t("createPermanentNote")}
        </button>
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={onCreateReview}>
          {t("generateReview")}
        </button>
        <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={() => window.location.href = appPath("/brain?graph=open")}>
          {t("viewInGraph")}
        </button>
        {insight.status === "new" && (
          <>
            <button className="rounded-lg bg-panel px-2.5 py-1 text-emerald-600 hover:text-emerald-700" onClick={() => onDismiss(insight.id, "apply")}>
              {t("applyBtn")}
            </button>
            <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-red-500" onClick={() => onDismiss(insight.id, "ignore")}>
              {t("ignoreBtn")}
            </button>
          </>
        )}
      </div>
    </article>
  );
}
