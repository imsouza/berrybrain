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
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <header className="mb-6">
          <h1 className="text-xl font-semibold">{t("activityTitle")}</h1>
          <p className="mt-1 text-sm text-muted/60">{t("activityDesc")}</p>
        </header>

        <div className="mb-6 grid grid-cols-4 gap-3">
          <StatCard label={t("completedLabel")} value={summary.completed} color="emerald" />
          <StatCard label={t("runningLabel")} value={summary.running} color="blue" />
          <StatCard label={t("pendingLabel")} value={summary.pending} color="amber" />
          <StatCard label={t("failedLabel")} value={summary.failed} color="red" />
        </div>

        <div className="mb-4 flex items-center justify-between gap-3">
          <div className="flex items-center gap-1 text-xs">
            {(["all", "completed", "running", "pending", "failed"] as const).map((f) => (
              <button
                key={f}
                className={`rounded-lg px-2.5 py-1 font-medium transition ${
                  filter === f ? "bg-accent/10 text-accent" : "text-muted hover:bg-surface hover:text-foreground"
                }`}
                onClick={() => setFilter(f)}
              >
                 {f === "all" ? t("allFilter") : f === "completed" ? t("completedLabel") : f === "running" ? t("runningLabel") : f === "pending" ? t("pendingLabel") : t("failedLabel")}
               </button>
             ))}
           </div>
           <button
             className={`rounded-lg px-3 py-1 text-xs transition ${
               technicalMode ? "bg-surface text-accent font-medium" : "text-muted hover:bg-surface hover:text-foreground"
             }`}
             onClick={() => setTechnicalMode(!technicalMode)}
           >
             {technicalMode ? t("normalView") : t("technicalView")}
           </button>
        </div>

        {filtered.length === 0 ? (
          <div className="rounded-xl bg-surface p-6 text-center text-xs text-muted/60 ring-1 ring-border/35">
             <p className="font-medium">{t("noActivity")}</p>
             <p className="mt-1">{t("writeNotesActivity")}</p>
          </div>
        ) : (
          <div className="space-y-1">
            {filtered.map((item) => (
              <div
                key={item.id}
                className={`flex items-start gap-3 rounded-lg px-3 py-2 text-sm transition ${
                  item.kind === "failed" ? "hover:bg-red-500/5" : "hover:bg-surface"
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
                    <span className="shrink-0 text-xs tabular-nums text-muted/55">
                       {item.when ? new Date(item.when).toLocaleTimeString(locale()) : ""}
                    </span>
                  </div>
                  {technicalMode && (
                    <div className="mt-0.5 text-xs text-muted/50 break-all">{item.technical}</div>
                  )}
                  {!technicalMode && item.kind === "failed" && item.detail && (
                    <div className="mt-0.5 text-xs text-red-500/70 line-clamp-1">{item.detail}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
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
    <div className="rounded-xl bg-surface p-3 text-center ring-1 ring-border/35">
      <div className={`text-2xl font-semibold tabular-nums ${colors[color]}`}>{value}</div>
      <div className="mt-0.5 text-[11px] text-muted">{label}</div>
    </div>
  );
}
