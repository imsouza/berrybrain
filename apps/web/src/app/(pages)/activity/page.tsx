"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";
import { t, tf, locale } from "@/i18n";

type ActivityKind = "log" | "completed" | "failed" | "running" | "pending";

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
  CREATE_REVIEW_FROM_INSIGHT: "Review created from insight",
};

type Job = { id: number; type: string; status: string; payload: any; attempts: number; max_attempts: number; error_message?: string; created_at?: string; completed_at?: string; started_at?: string };
type Log = { id: number; action_type: string; target_type: string; target_id: string; description: string; created_at: string };

function parseJobPayload(payload: any): { note_path?: string } {
  if (typeof payload === "string") try { return JSON.parse(payload); } catch { return {}; }
  return payload || {};
}

function humanizeJob(job: Job): { human: string; noteRef?: string; detail?: string } {
  const { note_path } = parseJobPayload(job.payload);
  const noteName = (note_path || "").split("/").pop()?.replace(/\.md$/, "") || "";
  const type = job.type;
  const label = JOB_LABELS[type] || type.replace(/_/g, " ").toLowerCase();

  const forNote = noteName ? tf("act_forNote", { name: noteName }) : "";

  if (job.status === "completed") {
    if (type === "ASSIMILATE_NOTE") return { human: t("act_assimilated") + forNote, noteRef: note_path };
    if (type === "GENERATE_NOTE_TITLE") return { human: t("act_titleGenerated") + forNote, noteRef: note_path };
    if (type === "GENERATE_EMBEDDING") return { human: t("act_embeddingCreated") + forNote, noteRef: note_path };
    if (type === "FIND_CONNECTIONS") return { human: t("act_connectionsAnalyzed") + forNote };
    if (type === "GENERATE_INSIGHTS") return { human: t("act_insightsGenerated") };
    if (type === "GENERATE_GRAPH_INSIGHTS") return { human: t("act_graphInsightsGenerated") };
    if (type === "EXPAND_KNOWLEDGE_GRAPH") return { human: t("act_graphExpanded") };
    if (type === "UPDATE_GRAPH_STATS") return { human: t("act_graphStatsUpdated") };
    if (type === "EXTRACT_CONTEXT") return { human: t("act_contextExtracted") + forNote, noteRef: note_path };
    if (type === "CONSOLIDATE_CONCEPTS") return { human: t("act_conceptsConsolidated") + forNote };
    if (type === "CLASSIFY_NOTE") return { human: t("act_noteClassified") + forNote, noteRef: note_path };
    if (type === "PARSE_NOTE") return { human: t("act_noteParsed") + forNote, noteRef: note_path };
    if (type === "AGGREGATE_CONCEPTS") return { human: t("act_conceptsAggregated") };
    return { human: t("act_completedFor") + " " + label + forNote };
  }

  if (job.status === "failed") {
    return { human: t("act_failedAt") + label + forNote, detail: job.error_message };
  }

  if (job.status === "running") {
    return { human: label + t("act_runningAt") + forNote };
  }

  return { human: label + t("act_queued") };
}

function humanizeLog(log: Log): { human: string; noteRef?: string } {
  const desc = log.description || "";
  for (const [key, label] of Object.entries(JOB_LABELS)) {
    if (desc.includes(key)) return { human: label };
  }
  return { human: desc || log.action_type };
}

export default function ActivityPage() {
  const api = getApiUrl();
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [technicalMode, setTechnicalMode] = useState(false);
  const [filter, setFilter] = useState<ActivityKind | "all">("all");
  const [summary, setSummary] = useState({ completed: 0, failed: 0, running: 0, pending: 0 });

  const loadActivity = useCallback(async () => {
    setLoading(true);
    if (api === "__browser__") {
      setActivity([]);
      setSummary({ completed: 0, failed: 0, running: 0, pending: 0 });
      setLoading(false);
      return;
    }
    try {
      const [logsRes, jobsRes] = await Promise.all([
        fetch(`${api}/api/v1/automation-logs?limit=100`),
        fetch(`${api}/api/v1/jobs?limit=100`),
      ]);

      const logsData = logsRes.ok ? await logsRes.json() : { logs: [] };
      const jobsData = jobsRes.ok ? await jobsRes.json() : { jobs: [] };

      const items: ActivityItem[] = [];
      let completed = 0, failed = 0, running = 0, pending = 0;

      for (const job of (jobsData.jobs || []) as Job[]) {
        const h = humanizeJob(job);
        const ts = new Date(job.completed_at || job.created_at || Date.now()).getTime();

        if (job.status === "completed") {
          completed++;
          items.push({
            id: `job-${job.id}`,
            when: job.completed_at || job.created_at || null,
            whenTs: ts,
            human: h.human,
            technical: `${job.type} · job #${job.id} · ${job.attempts || 1}/${job.max_attempts || 3} attempts`,
            kind: "completed",
            noteRef: h.noteRef,
          });
        } else if (job.status === "failed") {
          failed++;
          items.push({
            id: `job-${job.id}`,
            when: job.created_at || null,
            whenTs: ts,
            human: h.human,
            technical: `${job.type} · job #${job.id} · ${(job.error_message || "unknown error").slice(0, 150)}`,
            kind: "failed",
            detail: job.error_message,
          });
        } else if (job.status === "running") {
          running++;
          items.push({
            id: `job-${job.id}`,
            when: job.started_at || job.created_at || null,
            whenTs: ts,
            human: h.human,
            technical: `${job.type} · job #${job.id} · attempt ${job.attempts || 1}/${job.max_attempts || 3}`,
            kind: "running",
          });
        } else {
          pending++;
          items.push({
            id: `job-${job.id}`,
            when: job.created_at || null,
            whenTs: ts,
            human: h.human,
            technical: `${job.type} · job #${job.id} · waiting`,
            kind: "pending",
          });
        }
      }

      for (const log of (logsData.logs || []) as Log[]) {
        const h = humanizeLog(log);
        const ts = new Date(log.created_at || Date.now()).getTime();
        items.push({
          id: `log-${log.id}`,
          when: log.created_at || null,
          whenTs: ts,
          human: h.human,
          technical: `${log.action_type} · ${log.target_type}:${log.target_id}${log.description ? ` · ${log.description.slice(0, 120)}` : ""}`,
          kind: "log",
        });
      }

      items.sort((a, b) => b.whenTs - a.whenTs);
      setActivity(items);
      setSummary({ completed, failed, running, pending });
    } catch {}
    setLoading(false);
  }, [api]);

  useEffect(() => { loadActivity(); }, [loadActivity]);

  const filtered = filter === "all" ? activity : activity.filter((a) => a.kind === filter);

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
           <div className="text-center text-sm text-muted/40 animate-pulse-soft">{t("loadingActivity")}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-10">
        <header className="mb-7 border-b border-border/60 pb-5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">Knowledge processing</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">{t("activityTitle")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted/65">{t("activityDesc")}</p>
        </header>

        <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          <StatCard label={t("completedLabel")} value={summary.completed} color="emerald" />
          <StatCard label={t("runningLabel")} value={summary.running} color="blue" />
          <StatCard label={t("pendingLabel")} value={summary.pending} color="amber" />
          <StatCard label={t("failedLabel")} value={summary.failed} color="red" />
        </div>

        <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            {(["all", "completed", "running", "pending", "failed"] as const).map((f) => (
              <button
                key={f}
                className={`bb-action px-3 py-1.5 font-medium ${filter === f ? "bb-action--active" : ""}`}
                onClick={() => setFilter(f)}
              >
                 {f === "all" ? t("allFilter") : f === "completed" ? t("completedLabel") : f === "running" ? t("runningLabel") : f === "pending" ? t("pendingLabel") : t("failedLabel")}
               </button>
             ))}
           </div>
           <button
             className={`bb-action self-start px-3 py-1.5 text-xs sm:self-auto ${technicalMode ? "bb-action--active" : ""}`}
             onClick={() => setTechnicalMode(!technicalMode)}
           >
             {technicalMode ? t("normalView") : t("technicalView")}
           </button>
        </div>

        {filtered.length === 0 ? (
          <div className="bb-card p-8 text-center text-xs text-muted/60">
             <p className="font-medium">{t("noActivity")}</p>
             <p className="mt-1">{t("writeNotesActivity")}</p>
          </div>
        ) : (
          <section className="bb-card overflow-hidden" aria-label="Activity stream">
            {filtered.map((item) => (
              <div
                key={item.id}
                className={`flex items-start gap-3 border-b border-border/35 px-4 py-3.5 text-sm transition last:border-b-0 sm:px-5 ${
                  item.kind === "failed" ? "bg-danger/[0.025] hover:bg-danger/[0.05]" : "hover:bg-surface/70"
                }`}
              >
                <span
                  className={`mt-1.5 inline-block size-1.5 shrink-0 rounded-full ${
                    item.kind === "failed" ? "bg-red-400" :
                    item.kind === "running" ? "bg-blue-400 animate-pulse" :
                    item.kind === "pending" ? "bg-amber-400" :
                    item.kind === "completed" ? "bg-emerald-400" :
                    "bg-zinc-300"
                  }`}
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-3">
                    <span className={`font-medium ${item.kind === "failed" ? "text-red-500" : ""}`}>
                      {item.human}
                    </span>
                    <span className="shrink-0 rounded-md bg-surface px-2 py-0.5 text-[10px] tabular-nums text-muted/55">
                       {item.when ? new Date(item.when).toLocaleTimeString(locale()) : ""}
                    </span>
                  </div>
                  {technicalMode && (
                    <div className="bb-subcard mt-2 break-all px-3 py-2 font-mono text-[10px] leading-5 text-muted/60">{item.technical}</div>
                  )}
                  {!technicalMode && item.kind === "failed" && item.detail && (
                    <div className="mt-0.5 text-xs text-red-500/70 line-clamp-1">{item.detail}</div>
                  )}
                </div>
              </div>
            ))}
          </section>
        )}
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    emerald: "text-emerald-500",
    blue: "text-blue-500",
    amber: "text-amber-500",
    red: "text-red-500",
  };
  return (
    <div className="bb-card relative overflow-hidden px-4 py-4 text-left">
      <span className={`absolute inset-y-0 left-0 w-1 ${color === "emerald" ? "bg-emerald-500" : color === "blue" ? "bg-blue-500" : color === "amber" ? "bg-amber-500" : "bg-danger"}`} />
      <div className={`text-2xl font-semibold tabular-nums ${colors[color]}`}>{value}</div>
      <div className="mt-1 text-[11px] font-medium uppercase tracking-[0.1em] text-muted/65">{label}</div>
    </div>
  );
}
