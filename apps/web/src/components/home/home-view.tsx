"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useWorkspace, appPath } from "@/contexts/workspace-context";
import { t, tf } from "@/i18n";
import { ThemedProgressBar } from "./themed-progress-bar";

type StatusKind = "running" | "completed" | "failed" | "offline" | "queued" | "waiting_provider";

type HomeSummary = {
  status: {
    worker: string;
    workerLastHeartbeat?: string | null;
    ollama: string;
    cloudProvider: string;
    cloudModel: string;
    cloudStatus: StatusKind | string;
    pendingJobs: number;
    activeJobs: number;
    lastProcessingAt?: string | null;
  };
  progress: {
    mode: "determinate" | "indeterminate";
    percent: number;
    active: number;
    pending: number;
    completed: number;
    failed: number;
    currentStep: string;
    lastResult: string;
    status: StatusKind | string;
  };
  stats: {
    notes: { total: number; createdToday: number; unassimilated: number };
    connections: { total: number; createdToday: number; averageConfidence: number };
    concepts: { total: number; newToday: number; withoutPermanentNote: number };
    study: { dueReviews: number; activeReviews: number; suggestedReviews: number; weakConcepts: number; openGaps: number };
    jobs: { pending: number; active: number; failed: number; completedToday: number; total: number };
    ai: { provider: string; model: string; metadata: number; embeddings: number; jobsProcessed: number; errors: number };
  };
  recentNotes: NoteItem[];
  dueReviews: ReviewItem[];
  activeJobs: ActiveJob[];
  recentlyCompleted: CompletionItem[];
  recentActivity: ActivityItem[];
  recentInsights: InsightItem[];
  recentConnections: ConnectionItem[];
  graphSummary: {
    nodes: number;
    edges: number;
    orphans: number;
    clusters: number;
    centralNotes: { title: string; path: string; degree: number }[];
    updatedAt?: string | null;
  };
  needsAttention: AttentionItem[];
  jobsByType: Record<string, number>;
};

type NoteItem = { title: string; path: string; folder?: string; status?: string };
type ActiveJob = { id: number; type: string; label: string; notePath?: string; noteTitle?: string; provider?: string; model?: string; elapsedSeconds?: number; progress?: number | null };
type CompletionItem = { id: number; type: string; label: string; noteTitle?: string; completedAt?: string | null };
type ActivityItem = { id?: number; action: string; description: string; technicalDescription?: string; when?: string | null };
type InsightItem = { id: number; type: string; title: string; description: string; priority: number; relatedNotes?: string[]; suggestedAction?: string; confidence?: number; provider?: string; model?: string; reasoning?: string; evidence?: any[]; status?: string; whyItMatters?: string };
type ConnectionItem = { id: number; type: string; confidence: number; confidencePercent: number; reason: string; source?: NoteRef | null; target?: NoteRef | null; status?: string };
type NoteRef = { title: string; path: string };
type AttentionItem = { kind: string; title: string; description: string; action: string };
type ReviewItem = { id: number; reviewType: string; prompt: string; dueAt?: string | null; intervalDays: number };

const DEMO_HOME_SUMMARY: HomeSummary = {
  status: {
    worker: "online",
    workerLastHeartbeat: new Date().toISOString(),
    ollama: "offline",
    cloudProvider: "local-demo",
    cloudModel: "demo",
    cloudStatus: "completed",
    pendingJobs: 0,
    activeJobs: 0,
    lastProcessingAt: new Date().toISOString(),
  },
  progress: {
    mode: "determinate",
    percent: 100,
    active: 0,
    pending: 0,
    completed: 2,
    failed: 0,
    currentStep: "",
    lastResult: "GENERATE_GRAPH_INSIGHTS",
    status: "completed",
  },
  stats: {
    notes: { total: 3, createdToday: 3, unassimilated: 0 },
    connections: { total: 4, createdToday: 4, averageConfidence: 0.82 },
    concepts: { total: 8, newToday: 8, withoutPermanentNote: 2 },
    study: { dueReviews: 0, activeReviews: 0, suggestedReviews: 0, weakConcepts: 0, openGaps: 0 },
    jobs: { pending: 0, active: 0, failed: 0, completedToday: 2, total: 2 },
    ai: { provider: "local-demo", model: "demo", metadata: 3, embeddings: 3, jobsProcessed: 2, errors: 0 },
  },
  recentNotes: [],
  dueReviews: [],
  activeJobs: [],
  recentlyCompleted: [],
  recentActivity: [],
  recentInsights: [],
  recentConnections: [],
  graphSummary: { nodes: 8, edges: 4, orphans: 0, clusters: 2, centralNotes: [], updatedAt: new Date().toISOString() },
  needsAttention: [],
  jobsByType: {},
};

function homeJobLabel(type: string): string {
  const labels: Record<string, string> = {
    PARSE_NOTE: "Read note",
    CLASSIFY_NOTE: "Classify note",
    ASSIMILATE_NOTE: "Assimilate concepts",
    EXTRACT_CONCEPTS: "Extract concepts",
    EXTRACT_ENTITIES: "Extract entities",
    DETECT_TOPICS: "Detect topics",
    EXTRACT_CONTEXT: "Detect context",
    GENERATE_EMBEDDING: "Generate embedding",
    FIND_CONNECTIONS: "Find connections",
    EXPAND_KNOWLEDGE_GRAPH: "Expand graph",
    GENERATE_INFERRED_CONNECTIONS: "Infer connections",
    EXPAND_CONCEPT_TO_NOTE: "Expand concepts",
    GENERATE_GRAPH_INSIGHTS: "Generate graph insights",
    UPDATE_GRAPH_STATS: "Update graph stats",
    GENERATE_NOTE_TITLE: "Apply title",
  };
  return labels[type] || type;
}

export function HomeView() {
  const w = useWorkspace();
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [starterText, setStarterText] = useState("");
  const [creatingDraft, setCreatingDraft] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState<{ notePath: string; completed: number; total: number; percent: number; currentStep?: string | null }[]>([]);

  const loadSummary = useCallback(() => {
    setLoading(true);
    setError(false);
    if (w.demo) {
      // ponytail: reflect the cloud provider the user configured in the demo
      const provider = localStorage.getItem("bb_ai_provider") || "local";
      const model = localStorage.getItem("bb_ai_model") || "";
      setSummary({
        ...DEMO_HOME_SUMMARY,
        status: { ...DEMO_HOME_SUMMARY.status, cloudProvider: provider, cloudModel: model },
      });
      setLoading(false);
      return;
    }
    fetch(`${w.api}/api/v1/home/summary`)
      .then((r) => {
        if (!r.ok) throw new Error("home-summary");
        return r.json();
      })
      .then(setSummary)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
    fetch(`${w.api}/api/v1/jobs/pipeline-progress`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => { if (d?.notes) setPipelineProgress(d.notes); })
      .catch(() => {});
  }, [w.api, w.demo]);

  const updateConnectionStatus = useCallback(
    async (id: number, action: "confirm" | "ignore") => {
      const response = await fetch(`${w.api}/api/v1/connections/id/${id}/${action}`, {
        method: "POST",
      });
      if (!response.ok) {
        w.toast("Could not update the connection.", "error");
        return;
      }
      w.toast(action === "confirm" ? "Connection confirmed." : "Connection ignored.", "success");
      loadSummary();
    },
    [loadSummary, w],
  );

  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  async function startWriting(value: string) {
    setStarterText(value);
    if (creatingDraft || !value.trim()) return;
    setCreatingDraft(true);
    try {
      await w.createDraft(value);
      loadSummary();
    } finally {
      setCreatingDraft(false);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-sm text-muted/40 animate-pulse-soft">{t("loadingSummary")}</div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-sm font-medium">{t("loadHomeFailed")}</div>
          <button className="mt-3 h-9 rounded-xl bg-accent px-4 text-xs font-medium text-white" onClick={loadSummary}>{t("retry")}</button>
        </div>
      </div>
    );
  }

  const nome = w.demo ? "" : (typeof window !== "undefined" ? localStorage.getItem("bb_nome") || "Owner" : "Owner");
  const noNotes = summary.stats.notes.total === 0 && w.notes.length === 0;
  const progressStatus = normalizeStatus(summary.progress.status);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <HomeHeader summary={summary} nome={nome} onGraph={() => w.setGraphOpen(true)} />

        <div className="mt-6 grid items-start gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)]">
          <ComposeCard
            noNotes={noNotes}
            value={starterText}
            disabled={creatingDraft}
            onChange={(value) => startWriting(value)}
            onCreateEmpty={() => w.createDraft()}
            creating={creatingDraft}
          />
          <AutopilotProgressCard summary={summary} status={progressStatus} onOpenMonitor={() => w.setMonitorOpen(true)} />
        </div>

        <StatsGrid summary={summary} />

        <div className="mt-8 grid items-start gap-8 lg:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)]">
          <div className="space-y-8">
            <InsightsPreview insights={summary.recentInsights} apiUrl={w.api} onUpdate={loadSummary} />
            <RecentConnectionsList connections={summary.recentConnections} onOpenGraph={() => w.setGraphOpen(true)} onUpdateStatus={updateConnectionStatus} />
          </div>
          <aside className="space-y-8">
            <ReviewTodayCard reviews={summary.dueReviews || []} total={summary.stats.study?.dueReviews || 0} />
            <GraphSummaryCard summary={summary} onOpenGraph={() => w.setGraphOpen(true)} apiUrl={w.api} onToast={w.toast} />
            <ActiveJobsPanel jobs={summary.activeJobs} pipelineProgress={pipelineProgress} onOpenMonitor={() => w.setMonitorOpen(true)} />
            {summary.needsAttention.length > 0 && (
              <NeedsAttentionCard items={summary.needsAttention} onOpenMonitor={() => w.setMonitorOpen(true)} />
            )}
          </aside>
        </div>

        <RecentActivityTimeline activity={summary.recentActivity} completed={summary.recentlyCompleted} />
        <InfographicsGrid summary={summary} />

        <div className="mt-8 flex flex-wrap gap-2">
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={() => w.setGraphOpen(true)}>{t("viewGraph")}</button>
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={() => (window.location.href = appPath("/reviews"))}>Review today</button>
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={() => w.setMonitorOpen(true)}>{t("monitor")}</button>
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={w.scanVault}>{t("scanVault")}</button>
        </div>
      </div>
    </div>
  );
}

function ReviewTodayCard({ reviews, total }: { reviews: ReviewItem[]; total: number }) {
  return (
    <section className="rounded-2xl bg-surface p-5 ring-1 ring-border/40">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-muted/50">Review today</p>
          <p className="mt-1 text-2xl font-semibold tabular-nums">{total}</p>
        </div>
        <button
          className="rounded-lg bg-accent px-3 py-2 text-xs font-medium text-white disabled:cursor-not-allowed disabled:opacity-45"
          disabled={total === 0}
          onClick={() => (window.location.href = appPath("/reviews"))}
        >
          Start review
        </button>
      </div>
      {reviews.length > 0 ? (
        <div className="mt-4 space-y-2">
          {reviews.slice(0, 2).map((review) => (
            <div key={review.id} className="rounded-lg bg-panel px-3 py-2 ring-1 ring-border/30">
              <p className="line-clamp-2 text-xs text-foreground/85">{review.prompt}</p>
              <p className="mt-1 text-[10px] uppercase tracking-wide text-muted/45">{review.reviewType.replaceAll("_", " ")}</p>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-3 text-xs text-muted/55">Nothing due. Your active review schedule is up to date.</p>
      )}
    </section>
  );
}

function HomeHeader({ summary, nome, onGraph }: { summary: HomeSummary; nome: string; onGraph: () => void }) {
  const usingCloud = Boolean(summary.status.cloudProvider && summary.status.cloudProvider !== "local");
  const providerStatus = usingCloud
    ? `AI · ${providerLabel(summary.status.cloudProvider)}`
    : `AI · Local${summary.status.ollama === "online" ? " ready" : " unavailable"}`;
  return (
    <header className="border-b border-border/60 pb-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent">{t("home")}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight lg:text-3xl">{nome ? `${t("homeGreeting")}, ${nome}.` : `${t("homeGreeting")}.`}</h1>
          <p className="mt-2 text-sm leading-6 text-muted/70">{t("keepWriting")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <HeaderLink accent onClick={() => (window.location.href = appPath("/activity"))}>{t("viewActivity")}</HeaderLink>
          <HeaderLink accent onClick={() => (window.location.href = appPath("/insights"))}>{t("viewInsights")}</HeaderLink>
          <HeaderLink accent onClick={onGraph}>{t("viewGraph")}</HeaderLink>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">
          <StatusBadge label={`Worker ${summary.status.worker}`} status={summary.status.worker === "running" || summary.status.worker === "online" ? "ok" : "bad"} />
        </span>
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">
          <StatusBadge label={providerStatus} status={usingCloud || summary.status.ollama === "online" ? "ok" : "muted"} />
        </span>
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">{tf("activeJobsCount", { count: summary.status.activeJobs })} · {tf("queuedCount", { count: summary.status.pendingJobs })}</span>
        {summary.status.lastProcessingAt && (
          <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">{t("lastProcessing")} {formatTime(summary.status.lastProcessingAt)}</span>
        )}
      </div>
    </header>
  );
}

function ComposeCard({ noNotes, value, disabled, onChange, onCreateEmpty, creating }: { noNotes: boolean; value: string; disabled: boolean; onChange: (value: string) => void; onCreateEmpty: () => void; creating: boolean }) {
  return (
    <div className="rounded-3xl border border-border/60 bg-panel p-5 shadow-sm ring-1 ring-border/30 transition focus-within:border-accent focus-within:ring-accent/30">
      <div className="mb-3 flex items-center gap-2">
        <span className="size-2 rounded-full bg-accent" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted/50">{t("startWriting")}</span>
      </div>
      <textarea
        autoFocus
        className="min-h-36 w-full resize-none bg-transparent text-sm leading-7 outline-none placeholder:text-muted/40"
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        placeholder={noNotes ? t("startFirstNote") : t("startNote")}
        value={value}
      />
      <div className="mt-2 flex items-center justify-between text-[11px] text-muted/45">
        <span>{creating ? t("creatingNote") : t("noTitleNeeded")}</span>
        <button className="rounded-lg px-2 py-1 hover:bg-surface hover:text-muted" onClick={onCreateEmpty}>
          {t("createEmptyDraft")}
        </button>
      </div>
    </div>
  );
}

function AutopilotProgressCard({ summary, status, onOpenMonitor }: { summary: HomeSummary; status: StatusKind; onOpenMonitor: () => void }) {
  const running = status === "running";
  const waiting = status === "waiting_provider" || status === "queued";
  return (
    <button className="w-full rounded-2xl bg-surface p-5 text-left ring-1 ring-border/40 transition hover:ring-accent/30" onClick={onOpenMonitor}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{status === "completed" ? t("autopilotUpToDate") : t("autopilotProcessing")}</div>
          <p className="mt-1 text-xs text-muted/60">
            {tf("activeJobsCount", { count: summary.progress.active })} · {tf("queuedCount", { count: summary.progress.pending })} · {tf("percentDone", { percent: summary.progress.percent })}
          </p>
        </div>
        <span className="rounded-full bg-panel px-2.5 py-1 text-[11px] text-muted/60">{summary.progress.currentStep}</span>
      </div>
      <div className="mt-4">
        <ThemedProgressBar
          value={summary.progress.percent}
          indeterminate={summary.progress.mode === "indeterminate" || waiting}
          status={status}
          description={`${summary.progress.percent}%`}
        />
      </div>
      <div className="mt-4 grid gap-3 text-xs text-muted/65 sm:grid-cols-2">
        <div><span className="text-muted/45">{t("currentStep")}:</span> {summary.progress.currentStep}</div>
        <div><span className="text-muted/45">{t("lastResult")}:</span> {summary.progress.lastResult}</div>
      </div>
      {running && <div className="mt-3 text-[11px] text-muted/45">{t("clickForJobDetails")}</div>}
    </button>
  );
}

function InsightsPreview({ insights, apiUrl, onUpdate }: { insights: InsightItem[]; apiUrl: string; onUpdate: () => void }) {
  const dismissInsight = async (id: number, action: "dismiss" | "ignore") => {
    try {
      await fetch(`${apiUrl}/api/v1/insights/${id}/${action}`, { method: "POST" });
      onUpdate();
    } catch {}
  };

  return (
    <Section title={t("aiInsights")}>
      {insights.length === 0 ? (
        <EmptyState title={t("noInsightsYet")} text={t("keepWritingForInsights")} />
      ) : (
        <div className="space-y-2">
          {insights.slice(0, 4).map((insight) => (
            <div key={insight.id} className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-medium uppercase text-accent">{insightTypeLabel(insight.type)}</span>
                {insight.priority > 0 && <span className="text-[10px] text-muted/40">Priority {insight.priority}</span>}
                <span className="text-[10px] text-muted/40 ml-auto">{Math.round((insight.confidence || 0) * 100)}%</span>
              </div>
              <p className="mt-1 text-xs font-medium">{insight.title}</p>
              {insight.description && <p className="mt-1 text-[11px] leading-5 text-muted/65 line-clamp-2">{insight.description}</p>}
              <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={() => window.location.href = appPath("/insights")}>{t("viewDetails")}</button>
                <button className="rounded-lg bg-panel px-2.5 py-1 text-emerald-600 hover:text-emerald-700" onClick={() => dismissInsight(insight.id, "dismiss")}>{t("apply")}</button>
                <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-red-500" onClick={() => dismissInsight(insight.id, "ignore")}>{t("ignore")}</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

function ActiveJobsPanel({ jobs, pipelineProgress, onOpenMonitor }: { jobs: ActiveJob[]; pipelineProgress: { notePath: string; completed: number; total: number; percent: number; currentStep?: string | null }[]; onOpenMonitor: () => void }) {
  const progressByPath = new Map(pipelineProgress.map((p) => [p.notePath, p]));
  return (
    <Section title={t("processingNow")}>
      {jobs.length === 0 ? (
        <EmptyState title={t("allReady")} text={t("noActiveTasks")} />
      ) : (
        <div className="space-y-2">
          {jobs.slice(0, 5).map((job) => {
            const pp = job.notePath ? progressByPath.get(job.notePath) : undefined;
            return (
              <button key={job.id} className="w-full rounded-xl bg-surface p-3 text-left ring-1 ring-border/35 hover:ring-accent/30" onClick={onOpenMonitor}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium">{job.label}</span>
                  <span className="text-[10px] text-muted/45">{formatElapsed(job.elapsedSeconds || 0)}</span>
                </div>
                <p className="mt-1 truncate text-[11px] text-muted/60">{job.noteTitle || job.notePath || "System"}</p>
                {pp && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="h-1 flex-1 overflow-hidden rounded-full bg-border/30">
                      <div className="h-full rounded-full bg-accent/70" style={{ width: `${pp.percent}%` }} />
                    </div>
                    <span className="text-[10px] text-muted/50">{tf("pipelineStep", { step: String(pp.completed), total: String(pp.total) })}</span>
                  </div>
                )}
                <p className="mt-1 text-[10px] text-muted/45">{providerLabel(job.provider || "")}{job.model ? ` · ${job.model}` : ""}</p>
              </button>
            );
          })}
        </div>
      )}
    </Section>
  );
}

function GraphSummaryCard({ summary, onOpenGraph, apiUrl, onToast }: { summary: HomeSummary; onOpenGraph: () => void; apiUrl: string; onToast: (msg: string, kind: "success" | "error") => void }) {
  const graph = summary.graphSummary;
  const recalcular = async () => {
    try {
      const r = await fetch(`${apiUrl}/api/v1/graph/expand`, { method: "POST" });
      if (!r.ok) throw new Error("expand-fail");
      onToast("Graph expansion started.", "success");
    } catch {
      onToast("Could not expand the graph.", "error");
    }
  };
  return (
    <Section title={t("knowledgeGraph")}>
      <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
        <div className="text-sm font-semibold">{graph.nodes} nodes · {graph.edges} connections</div>
        <p className="mt-1 text-xs text-muted/60">{graph.orphans} {t("orphans")} · {graph.clusters} {t("clusters")}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={onOpenGraph}>{t("openGraph")}</button>
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={() => { if (typeof window !== "undefined") localStorage.setItem("bb_graph_filter_orphans", "1"); onOpenGraph(); }}>{t("viewOrphans")}</button>
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={recalcular}>{t("recalcConnections")}</button>
        </div>
      </div>
    </Section>
  );
}

function NeedsAttentionCard({ items, onOpenMonitor }: { items: AttentionItem[]; onOpenMonitor: () => void }) {
  if (items.length === 0) {
    return (
      <Section title={t("needsAttention")}>
        <div className="rounded-xl bg-surface p-4 text-xs text-muted/60 ring-1 ring-border/35">{t("allGood")}</div>
      </Section>
    );
  }
  return (
    <Section title={t("needsAttention")}>
      <div className="space-y-2">
        {items.map((item) => (
          <button key={item.kind} className="w-full rounded-xl bg-surface p-3 text-left ring-1 ring-border/35 hover:ring-accent/30" onClick={onOpenMonitor}>
            <div className="text-xs font-medium">{item.title}</div>
            <p className="mt-1 text-[11px] text-muted/60">{item.description}</p>
          </button>
        ))}
      </div>
    </Section>
  );
}

function StatsGrid({ summary }: { summary: HomeSummary }) {
  const s = summary.stats;
  return (
    <Section title={t("stats")} className="mt-8">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label={t("notes")} value={s.notes.total} detail={`+${s.notes.createdToday} ${t("oneCreatedToday")} · ${s.notes.unassimilated} ${t("notAssimilated")}`} />
        <StatCard label={t("connections")} value={s.connections.total} detail={`${s.connections.createdToday} ${t("newConnections")} · ${percent(s.connections.averageConfidence)} ${t("confidence")}`} />
        <StatCard label={t("concepts")} value={s.concepts.total} detail={`${s.concepts.newToday} ${t("newToday")} · ${s.concepts.withoutPermanentNote} ${t("withoutNote")}`} />
        <StatCard label={t("jobs")} value={s.jobs.pending} detail={`${tf("activeJobsCount", { count: s.jobs.active })} · ${s.jobs.failed} ${t("errors")}`} />
        <StatCard label={providerLabel(s.ai.provider)} value={s.ai.model ? t("online") : t("local")} detail={`${s.ai.embeddings} ${t("embeddings")} · ${s.ai.metadata} ${t("metadata")}`} />
      </div>
    </Section>
  );
}

function InfographicsGrid({ summary }: { summary: HomeSummary }) {
  const s = summary.stats;
  const g = summary.graphSummary;
  const assimilated = s.notes.total > 0 ? (s.notes.total - s.notes.unassimilated) / s.notes.total : 0;
  const graphHealth = g.nodes > 0 ? (g.nodes - g.orphans) / g.nodes : 0;
  const jobEntries = Object.entries(summary.jobsByType || {})
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6);
  return (
    <Section title={t("overview")} className="mt-8">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Donut label={t("assimilation")} value={assimilated} caption={`${s.notes.total - s.notes.unassimilated}/${s.notes.total} ${t("notes")}`} />
        <Donut label={t("avgConfidence")} value={s.connections.averageConfidence} caption={`${s.connections.total} ${t("connections")}`} />
        <Donut label={t("graphHealth")} value={graphHealth} caption={`${g.orphans} ${t("orphans")} ${t("of")} ${g.nodes}`} />
        <div className="rounded-xl bg-surface px-4 py-3 ring-1 ring-border/30">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-wider text-muted/40">{t("jobsByType")}</div>
          {jobEntries.length === 0 ? (
            <p className="text-[11px] text-muted/50">{t("noJobsRecorded")}</p>
          ) : (
            <BarList entries={jobEntries} />
          )}
        </div>
      </div>
    </Section>
  );
}

function Donut({ label, value, caption }: { label: string; value: number; caption?: string }) {
  const pct = Math.max(0, Math.min(1, value || 0));
  const r = 26;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - pct);
  return (
    <div className="flex items-center gap-3 rounded-xl bg-surface px-4 py-3 ring-1 ring-border/30">
      <svg width="64" height="64" viewBox="0 0 64 64" className="shrink-0 -rotate-90">
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--color-border)" strokeWidth="7" />
        <circle cx="32" cy="32" r={r} fill="none" stroke="var(--color-accent)" strokeWidth="7" strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} />
      </svg>
      <div className="min-w-0">
        <div className="text-lg font-semibold tabular-nums">{Math.round(pct * 100)}%</div>
        <div className="text-[10px] text-muted/50">{label}</div>
        {caption && <div className="mt-0.5 truncate text-[10px] text-muted/45">{caption}</div>}
      </div>
    </div>
  );
}

function BarList({ entries }: { entries: [string, number][] }) {
  const max = Math.max(...entries.map(([, v]) => v), 1);
  return (
    <div className="space-y-1.5">
      {entries.map(([type, count]) => (
        <div key={type}>
          <div className="flex items-center justify-between text-[10px] text-muted/60">
            <span className="min-w-0 truncate">{homeJobLabel(type)}</span>
            <span className="ml-2 rounded-full bg-panel px-1.5 py-0.5 tabular-nums text-muted/55">{count}</span>
          </div>
          <div className="mt-0.5 h-1.5 rounded-full bg-panel">
            <div className="h-full rounded-full bg-accent" style={{ width: `${(count / max) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

function RecentConnectionsList({
  connections,
  onOpenGraph,
  onUpdateStatus,
}: {
  connections: ConnectionItem[];
  onOpenGraph: () => void;
  onUpdateStatus: (id: number, action: "confirm" | "ignore") => void;
}) {
  return (
    <Section title={t("recentConnections")}>
      {connections.length === 0 ? (
        <EmptyState title={t("noConnectionsYet")} text={t("autopilotCreatesRelations")} />
      ) : (
        <div className="space-y-2">
          {connections.slice(0, 5).map((connection) => (
            <div key={connection.id} className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
              <div className="text-xs font-medium">
                {connection.source?.title || t("origin")} ↔ {connection.target?.title || t("destination")}
              </div>
              <p className="mt-1 text-[11px] leading-5 text-muted/65">{connection.reason || t("noReason")}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-muted/55">
                <span>{t("connectionConfidence")}: {connection.confidencePercent}%</span>
                <span className="rounded-full bg-panel px-2 py-1">{connection.status || t("suggested")}</span>
                <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={onOpenGraph}>{t("viewInGraph")}</button>
                {connection.status !== "confirmed" && (
                  <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={() => onUpdateStatus(connection.id, "confirm")}>{t("confirm")}</button>
                )}
                {connection.status !== "ignored" && (
                  <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={() => onUpdateStatus(connection.id, "ignore")}>{t("ignore")}</button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

function RecentActivityTimeline({ activity, completed }: { activity: ActivityItem[]; completed: CompletionItem[] }) {
  return (
    <Section title={t("recentActivity")} className="mt-8">
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">{t("doneRecently")}</div>
          {completed.length === 0 ? <p className="text-xs text-muted/50">{t("noRecentResults")}</p> : completed.slice(0, 5).map((item) => (
            <RowLine key={item.id} left={item.label} right={formatTime(item.completedAt)} />
          ))}
        </div>
        <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">{t("autoQueue")}</div>
          {activity.length === 0 ? <p className="text-xs text-muted/50">{t("noRecentActivity")}</p> : activity.slice(0, 5).map((item, index) => (
            <RowLine key={item.id || index} left={item.description} right={formatTime(item.when)} />
          ))}
        </div>
      </div>
    </Section>
  );
}

function Section({ title, children, className = "" }: { title: string; children: ReactNode; className?: string }) {
  return (
    <section className={className}>
      <h2 className="mb-3 text-[11px] font-semibold uppercase tracking-[0.15em] text-muted/40">{title}</h2>
      {children}
    </section>
  );
}

function StatCard({ label, value, detail }: { label: string; value: number | string; detail?: string }) {
  return (
    <div className="rounded-xl bg-surface px-3 py-3 text-center ring-1 ring-border/30">
      <div className="text-lg font-semibold tabular-nums">{value}</div>
      <div className="text-[10px] text-muted/50">{label}</div>
      {detail && <div className="mt-1 text-[10px] leading-4 text-muted/45">{detail}</div>}
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-xl bg-surface p-4 text-xs ring-1 ring-border/35">
      <div className="font-medium">{title}</div>
      <p className="mt-1 text-muted/55">{text}</p>
    </div>
  );
}

function RowLine({ left, right }: { left: string; right?: string }) {
  return (
    <div className="flex items-center justify-between gap-3 py-1.5 text-[11px] text-muted/65">
      <span className="min-w-0 truncate">{left}</span>
      {right && <span className="shrink-0 tabular-nums text-muted/40">{right}</span>}
    </div>
  );
}

function StatusBadge({ label, status }: { label: string; status: "ok" | "bad" | "muted" }) {
  const color = status === "ok" ? "var(--color-success)" : status === "bad" ? "var(--color-danger)" : "var(--color-muted)";
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="size-1.5 rounded-full" style={{ background: color }} />
      {label}
    </span>
  );
}

function HeaderLink({ children, onClick, accent }: { children: ReactNode; onClick: () => void; accent?: boolean }) {
  const cls = accent
    ? "rounded-lg bg-accent px-2.5 py-1 text-[11px] font-medium text-black hover:opacity-90"
    : "rounded-lg bg-surface px-2.5 py-1 text-[11px] text-muted hover:text-foreground";
  return <button className={cls} onClick={onClick}>{children}</button>;
}

function normalizeStatus(status: string): StatusKind {
  if (status === "failed" || status === "offline" || status === "queued" || status === "waiting_provider" || status === "completed") return status;
  return "running";
}

function providerLabel(provider: string) {
  if (provider === "nvidia-nim") return "NVIDIA NIM";
  if (provider === "cloud") return "Cloud";
  if (provider === "local") return "Local";
  return provider || "AI";
}

function insightTypeLabel(type: string) {
  return {
    context: "Central theme",
    conclusion: "Confirmed relationship",
    hypothesis: "Possible connection",
    premise: "Recurring pattern",
    assertion: "Strong evidence",
    knowledge_gap: "Gap to explore",
    new_connection: "New connection",
    study_path: "Study path",
    possible_contradiction: "Possible conflict",
    deepening_opportunity: "Deepening opportunity",
    recurring_concept: "Recurring concept",
    review_opportunity: "Suggested review",
    permanent_note_candidate: "Suggested note",
    emerging_context: "Emerging context",
    isolated_note: "Isolated note",
    isolated_concept: "Isolated concept",
    weak_note: "Weak note",
    duplicate_content: "Duplicate content",
  }[type] || type.replace(/_/g, " ");
}

function percent(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatTime(value?: string | null) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatElapsed(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}min`;
}
