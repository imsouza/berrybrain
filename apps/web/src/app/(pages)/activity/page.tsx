"use client";

import type { Route } from "next";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  CircleDashed,
  Clock3,
  FileText,
  RefreshCw,
  Wrench,
} from "lucide-react";
import { apiFetch, appPath, getApiUrl } from "@/contexts/workspace-context";
import { locale, t, tf } from "@/i18n";

type ActivityKind = "log" | "completed" | "failed" | "running" | "pending";
type ActivityFilter = ActivityKind | "all";

type ActivityItem = {
  id: string;
  when: string | null;
  whenTs: number;
  human: string;
  technical: string;
  kind: ActivityKind;
  noteRef?: string;
  detail?: string;
};

type Job = {
  id: number;
  type: string;
  status: string;
  payload: unknown;
  attempts: number;
  max_attempts: number;
  error_message?: string;
  created_at?: string;
  completed_at?: string;
  started_at?: string;
};

type Log = {
  id: number;
  action_type: string;
  target_type: string;
  target_id: string;
  description: string;
  created_at: string;
};

type ActivitySummary = {
  completed: number;
  failed: number;
  running: number;
  pending: number;
};

type ActivitySnapshot = {
  activity: ActivityItem[];
  summary: ActivitySummary;
  updatedAt: number;
};

const EMPTY_SUMMARY: ActivitySummary = { completed: 0, failed: 0, running: 0, pending: 0 };
const ACTIVITY_CACHE_TTL_MS = 15_000;
const activityCache = new Map<string, ActivitySnapshot>();

const JOB_LABELS: Record<string, string> = {
  PARSE_NOTE: "Note analysis",
  CLASSIFY_NOTE: "Classification",
  ASSIMILATE_NOTE: "Assimilation",
  GENERATE_EMBEDDING: "Embedding generation",
  FIND_CONNECTIONS: "Connection search",
  GENERATE_INSIGHTS: "Insight generation",
  EXPAND_KNOWLEDGE_GRAPH: "Graph expansion",
  GENERATE_NOTE_TITLE: "Automatic title",
  GENERATE_GRAPH_INSIGHTS: "Graph insights",
  UPDATE_GRAPH_STATS: "Graph stats",
  EXTRACT_CONTEXT: "Context extraction",
  CONSOLIDATE_CONCEPTS: "Concept consolidation",
  GENERATE_AGENDA: "Agenda generation",
  AGGREGATE_CONCEPTS: "Concept aggregation",
  CREATE_NOTE_FROM_INSIGHT: "Note created from insight",
};

function parseJobPayload(payload: unknown): { note_path?: string } {
  if (typeof payload === "string") {
    try {
      const parsed = JSON.parse(payload) as unknown;
      return typeof parsed === "object" && parsed !== null
        ? parsed as { note_path?: string }
        : {};
    } catch {
      return {};
    }
  }
  return typeof payload === "object" && payload !== null
    ? payload as { note_path?: string }
    : {};
}

function humanizeJob(job: Job): { human: string; noteRef?: string; detail?: string } {
  const { note_path: notePath } = parseJobPayload(job.payload);
  const noteName = (notePath || "").split("/").pop()?.replace(/\.md$/, "") || "";
  const label = JOB_LABELS[job.type] || job.type.replace(/_/g, " ").toLowerCase();
  const forNote = noteName ? tf("act_forNote", { name: noteName }) : "";

  if (job.status === "completed") {
    if (job.type === "ASSIMILATE_NOTE") return { human: t("act_assimilated") + forNote, noteRef: notePath };
    if (job.type === "GENERATE_NOTE_TITLE") return { human: t("act_titleGenerated") + forNote, noteRef: notePath };
    if (job.type === "GENERATE_EMBEDDING") return { human: t("act_embeddingCreated") + forNote, noteRef: notePath };
    if (job.type === "FIND_CONNECTIONS") return { human: t("act_connectionsAnalyzed") + forNote, noteRef: notePath };
    if (job.type === "GENERATE_INSIGHTS") return { human: t("act_insightsGenerated") };
    if (job.type === "GENERATE_GRAPH_INSIGHTS") return { human: t("act_graphInsightsGenerated") };
    if (job.type === "EXPAND_KNOWLEDGE_GRAPH") return { human: t("act_graphExpanded") };
    if (job.type === "UPDATE_GRAPH_STATS") return { human: t("act_graphStatsUpdated") };
    if (job.type === "EXTRACT_CONTEXT") return { human: t("act_contextExtracted") + forNote, noteRef: notePath };
    if (job.type === "CONSOLIDATE_CONCEPTS") return { human: t("act_conceptsConsolidated") + forNote };
    if (job.type === "CLASSIFY_NOTE") return { human: t("act_noteClassified") + forNote, noteRef: notePath };
    if (job.type === "PARSE_NOTE") return { human: t("act_noteParsed") + forNote, noteRef: notePath };
    if (job.type === "AGGREGATE_CONCEPTS") return { human: t("act_conceptsAggregated") };
    return { human: `${t("act_completedFor")} ${label}${forNote}`, noteRef: notePath };
  }
  if (job.status === "failed") {
    return { human: `${t("act_failedAt")}${label}${forNote}`, noteRef: notePath, detail: job.error_message };
  }
  if (job.status === "running") return { human: `${label}${t("act_runningAt")}${forNote}`, noteRef: notePath };
  return { human: `${label}${t("act_queued")}`, noteRef: notePath };
}

function humanizeLog(log: Log): string {
  const description = log.description || "";
  for (const [key, label] of Object.entries(JOB_LABELS)) {
    if (description.includes(key)) return label;
  }
  return description || log.action_type;
}

function timestamp(value?: string): number {
  const parsed = value ? Date.parse(value) : Number.NaN;
  return Number.isFinite(parsed) ? parsed : Date.now();
}

function buildSnapshot(jobs: Job[], logs: Log[]): ActivitySnapshot {
  const activity: ActivityItem[] = [];
  const summary = { ...EMPTY_SUMMARY };

  for (const job of jobs) {
    const humanized = humanizeJob(job);
    const kind: ActivityKind = job.status === "completed"
      ? "completed"
      : job.status === "failed"
        ? "failed"
        : job.status === "running"
          ? "running"
          : "pending";
    summary[kind] += 1;
    const when = job.completed_at || job.started_at || job.created_at || null;
    activity.push({
      id: `job-${job.id}`,
      when,
      whenTs: timestamp(when || undefined),
      human: humanized.human,
      technical: `${job.type} · job #${job.id} · ${job.attempts || 1}/${job.max_attempts || 3} attempts${job.error_message ? ` · ${job.error_message.slice(0, 150)}` : ""}`,
      kind,
      noteRef: humanized.noteRef,
      detail: humanized.detail,
    });
  }

  for (const log of logs) {
    activity.push({
      id: `log-${log.id}`,
      when: log.created_at || null,
      whenTs: timestamp(log.created_at),
      human: humanizeLog(log),
      technical: `${log.action_type} · ${log.target_type}:${log.target_id}${log.description ? ` · ${log.description.slice(0, 120)}` : ""}`,
      kind: "log",
    });
  }

  activity.sort((left, right) => right.whenTs - left.whenTs);
  return { activity, summary, updatedAt: Date.now() };
}

export default function ActivityPage() {
  const api = getApiUrl();
  const router = useRouter();
  const initial = activityCache.get(api);
  const [activity, setActivity] = useState<ActivityItem[]>(() => initial?.activity || []);
  const [summary, setSummary] = useState<ActivitySummary>(() => initial?.summary || EMPTY_SUMMARY);
  const [loading, setLoading] = useState(() => !initial);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<number | null>(() => initial?.updatedAt || null);
  const [technicalMode, setTechnicalMode] = useState(false);
  const [filter, setFilter] = useState<ActivityFilter>("all");
  const requestRef = useRef<Promise<void> | null>(null);

  const loadActivity = useCallback(async () => {
    if (requestRef.current) return requestRef.current;
    const hasCachedData = activityCache.has(api);
    setError("");
    if (hasCachedData) setRefreshing(true);
    else setLoading(true);

    const request = (async () => {
      try {
        const [logsResponse, jobsResponse] = await Promise.all([
          apiFetch(`${api}/api/v1/automation-logs?limit=100`),
          apiFetch(`${api}/api/v1/jobs?limit=100`),
        ]);
        if (!logsResponse.ok || !jobsResponse.ok) throw new Error("Activity could not be loaded.");
        const [logsPayload, jobsPayload] = await Promise.all([
          logsResponse.json(),
          jobsResponse.json(),
        ]);
        const snapshot = buildSnapshot(
          (jobsPayload.jobs || []) as Job[],
          (logsPayload.logs || []) as Log[],
        );
        activityCache.set(api, snapshot);
        setActivity(snapshot.activity);
        setSummary(snapshot.summary);
        setUpdatedAt(snapshot.updatedAt);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Activity could not be loaded.");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    })();
    requestRef.current = request;
    await request;
    requestRef.current = null;
  }, [api]);

  useEffect(() => {
    const cached = activityCache.get(api);
    if (!cached || Date.now() - cached.updatedAt >= ACTIVITY_CACHE_TTL_MS) {
      void loadActivity();
    }
    const interval = window.setInterval(() => { void loadActivity(); }, ACTIVITY_CACHE_TTL_MS);
    return () => window.clearInterval(interval);
  }, [api, loadActivity]);

  const filtered = useMemo(
    () => filter === "all" ? activity : activity.filter((item) => item.kind === filter),
    [activity, filter],
  );

  if (loading) return <ActivitySkeleton />;

  return (
    <div className="flex-1 overflow-y-auto bg-background">
      <div className="mx-auto w-full max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <header className="flex flex-col gap-4 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-xs font-semibold text-accent"><Activity className="size-4" />Knowledge processing</p>
            <h1 className="mt-2 text-2xl font-semibold text-foreground">{t("activityTitle")}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">{t("activityDesc")}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <span className="text-xs text-muted" aria-live="polite">
              {updatedAt ? `Updated ${new Date(updatedAt).toLocaleTimeString(locale())}` : "Not updated"}
            </span>
            <button type="button" className="bb-action inline-flex h-9 items-center gap-2 px-3 text-xs font-semibold" onClick={() => void loadActivity()} disabled={refreshing}>
              <RefreshCw className={`size-4 ${refreshing ? "animate-spin" : ""}`} />
              {refreshing ? "Refreshing" : "Refresh"}
            </button>
          </div>
        </header>

        <section className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4" aria-label="Activity overview">
          <Metric label={t("completedLabel")} value={summary.completed} kind="completed" />
          <Metric label={t("runningLabel")} value={summary.running} kind="running" />
          <Metric label={t("pendingLabel")} value={summary.pending} kind="pending" />
          <Metric label={t("failedLabel")} value={summary.failed} kind="failed" />
        </section>

        <div className="mt-6 flex flex-col gap-3 border-y border-border py-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex max-w-full gap-1 overflow-x-auto" aria-label="Activity filter">
            {(["all", "completed", "running", "pending", "failed", "log"] as const).map((value) => (
              <button
                type="button"
                key={value}
                className={`bb-action h-8 shrink-0 px-3 text-xs font-medium ${filter === value ? "bb-action--active" : ""}`}
                onClick={() => setFilter(value)}
                aria-pressed={filter === value}
              >
                {filterLabel(value)}
              </button>
            ))}
          </div>
          <label className="inline-flex shrink-0 cursor-pointer items-center gap-2 text-xs font-medium text-muted">
            <input type="checkbox" className="peer sr-only" checked={technicalMode} onChange={(event) => setTechnicalMode(event.target.checked)} />
            <span className="relative h-5 w-9 rounded-full border border-border bg-surface transition peer-checked:border-accent peer-checked:bg-accent-soft peer-focus-visible:outline peer-focus-visible:outline-3 peer-focus-visible:outline-accent/30 after:absolute after:left-0.5 after:top-0.5 after:size-3.5 after:rounded-full after:bg-muted after:transition-transform peer-checked:after:translate-x-4 peer-checked:after:bg-accent" aria-hidden="true" />
            <Wrench className="size-4" />Technical details
          </label>
        </div>

        {error && (
          <div className="mt-4 flex flex-wrap items-center gap-3 border border-danger/40 bg-danger/10 px-4 py-3 text-sm text-danger" role="alert">
            <AlertCircle className="size-4 shrink-0" />
            <span className="flex-1">{error}</span>
            <button type="button" className="bb-action h-8 px-3 text-xs" onClick={() => void loadActivity()}>Retry</button>
          </div>
        )}

        {filtered.length === 0 ? (
          <section className="py-16 text-center" aria-label="Empty activity">
            <CircleDashed className="mx-auto size-8 text-muted" />
            <h2 className="mt-4 text-sm font-semibold text-foreground">{t("noActivity")}</h2>
            <p className="mt-1 text-sm text-muted">{t("writeNotesActivity")}</p>
          </section>
        ) : (
          <section className="divide-y divide-border" aria-label="Activity stream">
            {filtered.map((item) => {
              const meta = activityMeta(item.kind);
              const Icon = meta.Icon;
              return (
                <article key={item.id} className="grid grid-cols-[2rem_minmax(0,1fr)] gap-3 py-4 sm:grid-cols-[2rem_minmax(0,1fr)_auto]">
                  <span className={`grid size-8 place-items-center rounded-md border ${meta.iconClass}`} aria-hidden="true"><Icon className={`size-4 ${item.kind === "running" ? "animate-pulse" : ""}`} /></span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="text-sm font-semibold text-foreground">{item.human}</h2>
                      <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${meta.badgeClass}`}>{meta.label}</span>
                    </div>
                    {item.noteRef && (
                      <button type="button" className="mt-1 inline-flex max-w-full items-center gap-1.5 text-xs text-accent hover:text-accent-hover" onClick={() => router.push(appPath(`/brain?note=${encodeURIComponent(item.noteRef || "")}`) as Route)}>
                        <FileText className="size-3.5 shrink-0" /><span className="truncate">Open source note</span>
                      </button>
                    )}
                    {technicalMode && <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words border-l-2 border-border pl-3 font-mono text-[11px] leading-5 text-muted">{item.technical}</pre>}
                    {!technicalMode && item.kind === "failed" && item.detail && <p className="mt-1 line-clamp-2 text-xs leading-5 text-danger">{item.detail}</p>}
                  </div>
                  <time className="col-start-2 text-xs tabular-nums text-muted sm:col-start-3 sm:row-start-1" dateTime={item.when || undefined}>{formatActivityTime(item.when)}</time>
                </article>
              );
            })}
          </section>
        )}
      </div>
    </div>
  );
}

function ActivitySkeleton() {
  return (
    <div className="flex-1 overflow-y-auto bg-background" aria-busy="true" aria-label="Loading activity">
      <div className="mx-auto w-full max-w-6xl animate-pulse px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <div className="h-6 w-44 rounded-md bg-surface" />
        <div className="mt-3 h-4 w-full max-w-xl rounded-md bg-surface" />
        <div className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((item) => <div key={item} className="h-24 rounded-md border border-border bg-panel" />)}</div>
        <div className="mt-8 space-y-1 border-y border-border">{[0, 1, 2, 3, 4].map((item) => <div key={item} className="h-16 border-b border-border bg-panel last:border-0" />)}</div>
      </div>
    </div>
  );
}

function Metric({ label, value, kind }: { label: string; value: number; kind: Exclude<ActivityKind, "log"> }) {
  const meta = activityMeta(kind);
  const Icon = meta.Icon;
  return (
    <article className="bb-card flex min-h-24 items-center gap-3 p-4">
      <span className={`grid size-9 shrink-0 place-items-center rounded-md border ${meta.iconClass}`}><Icon className="size-4" /></span>
      <div className="min-w-0"><strong className="block text-2xl font-semibold tabular-nums text-foreground">{value}</strong><span className="block truncate text-xs font-medium text-muted">{label}</span></div>
    </article>
  );
}

function activityMeta(kind: ActivityKind) {
  if (kind === "completed") return { label: "Completed", Icon: CheckCircle2, iconClass: "border-success/40 bg-success/10 text-success", badgeClass: "bg-success/10 text-foreground" };
  if (kind === "running") return { label: "Running", Icon: RefreshCw, iconClass: "border-accent/40 bg-accent-soft text-accent", badgeClass: "bg-accent-soft text-accent" };
  if (kind === "pending") return { label: "Pending", Icon: Clock3, iconClass: "border-border bg-surface text-muted", badgeClass: "bg-surface text-muted" };
  if (kind === "failed") return { label: "Failed", Icon: AlertCircle, iconClass: "border-danger/40 bg-danger/10 text-danger", badgeClass: "bg-danger/10 text-danger" };
  return { label: "System", Icon: Activity, iconClass: "border-border bg-panel text-muted", badgeClass: "bg-surface text-muted" };
}

function filterLabel(filter: ActivityFilter): string {
  if (filter === "all") return t("allFilter");
  if (filter === "completed") return t("completedLabel");
  if (filter === "running") return t("runningLabel");
  if (filter === "pending") return t("pendingLabel");
  if (filter === "failed") return t("failedLabel");
  return "System";
}

function formatActivityTime(value: string | null): string {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  const today = new Date();
  return date.toDateString() === today.toDateString()
    ? date.toLocaleTimeString(locale(), { hour: "2-digit", minute: "2-digit" })
    : date.toLocaleString(locale(), { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}
