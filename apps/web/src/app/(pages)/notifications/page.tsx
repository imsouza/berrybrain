"use client";

import { useCallback, useEffect, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";
import { t, locale } from "@/i18n";

type Alert = {
  kind: string;
  title: string;
  description: string;
  action: string;
};

type JobBrief = {
  id: number;
  type: string;
  status: string;
  error_message?: string;
  created_at: string;
};

function humanizeJobType(type: string): string {
  const labels: Record<string, string> = {
    GENERATE_GRAPH_INSIGHTS: "Graph insights",
    GENERATE_INSIGHTS: "Insights",
    UPDATE_GRAPH_STATS: "Graph stats",
    EXPAND_KNOWLEDGE_GRAPH: "Graph expansion",
    ASSIMILATE_NOTE: "Note assimilation",
    GENERATE_EMBEDDING: "Embedding",
    FIND_CONNECTIONS: "Connections",
    GENERATE_NOTE_TITLE: "Automatic title",
    EXTRACT_CONTEXT: "Context extraction",
  };
  return labels[type] || type.replace(/_/g, " ").toLowerCase();
}

export default function NotificationsPage() {
  const api = getApiUrl();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [failedJobs, setFailedJobs] = useState<JobBrief[]>([]);
  const [loading, setLoading] = useState(true);
  const [retryingJobId, setRetryingJobId] = useState<number | null>(null);
  const [actionStatus, setActionStatus] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryRes, jobsRes] = await Promise.all([
        fetch(`${api}/api/v1/home/summary`),
        fetch(`${api}/api/v1/jobs?limit=20`),
      ]);
      if (summaryRes.ok) {
        const d = await summaryRes.json();
        setAlerts(d.needsAttention || []);
      }
      if (jobsRes.ok) {
        const d = await jobsRes.json();
        setFailedJobs((d.jobs || []).filter((j: JobBrief) => j.status === "failed" || j.status === "dead_letter"));
      }
    } catch {}
    setLoading(false);
  }, [api]);

  useEffect(() => { load(); }, [load]);

  async function retryJob(jobId: number) {
    setRetryingJobId(jobId);
    setActionStatus("");
    try {
      const response = await fetch(`${api}/api/v1/jobs/${jobId}/retry`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Retry failed.");
      await load();
      setActionStatus(`Job #${jobId} queued again.`);
    } catch (error) {
      setActionStatus(error instanceof Error ? error.message : "Retry failed.");
    } finally {
      setRetryingJobId(null);
    }
  }

  if (loading) {
    return (
      <div className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8 text-center text-sm text-muted/40 animate-pulse-soft">{t("loadingAlerts")}</div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <header className="mb-6">
          <h1 className="text-xl font-semibold">{t("alertsAndStatus")}</h1>
          <p className="mt-1 text-sm text-muted/60">{t("alertsAndStatusDesc")}</p>
        </header>

        {alerts.length === 0 && failedJobs.length === 0 ? (
          <div className="rounded-xl bg-surface p-6 text-center text-xs text-muted/60 ring-1 ring-border/35">
            <p className="font-medium">{t("allGoodState")}</p>
            <p className="mt-1">{t("noAlertsSystem")}</p>
          </div>
        ) : (
          <div className="space-y-6">
            {alerts.length > 0 && (
              <section>
                <h2 className="mb-3 text-sm font-semibold">{t("needsAttentionSection")}</h2>
                <div className="space-y-2">
                  {alerts.map((a, i) => (
                    <div key={a.kind + i} className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
                      <div className="text-xs font-medium uppercase text-muted/50">{a.kind.replace(/_/g, " ")}</div>
                      <h3 className="mt-0.5 text-sm font-medium">{a.title}</h3>
                      <p className="mt-0.5 text-xs text-muted/60">{a.description}</p>
                      <a
                        href={a.kind === "failed_jobs" || a.kind === "ollama_offline" ? "/brain?monitor=open" : "/activity"}
                        className="mt-2 inline-block rounded-lg bg-accent px-3 py-1 text-[11px] font-medium text-white"
                      >
                        {a.action}
                      </a>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {failedJobs.length > 0 && (
              <section>
                <h2 className="mb-3 text-sm font-semibold">{t("failedJobsSection")}</h2>
                {actionStatus && (
                  <div className="mb-3 rounded-lg bg-accent/10 px-3 py-2 text-xs text-foreground ring-1 ring-accent/20">
                    {actionStatus}
                  </div>
                )}
                <div className="space-y-1">
                  {failedJobs.map((j) => (
                    <div key={j.id} className="rounded-lg bg-red-500/5 px-3 py-2 text-xs ring-1 ring-red-500/15">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="font-medium text-red-500">{humanizeJobType(j.type)}</span>
                          <span className="text-muted/50 ml-1">· job #{j.id}</span>
                          {j.status === "dead_letter" && (
                            <span className="ml-2 rounded-md bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-500 ring-1 ring-red-500/20">dead letter</span>
                          )}
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <span className="text-muted/50">{new Date(j.created_at).toLocaleTimeString(locale())}</span>
                          <button
                            className="rounded-lg bg-accent px-2.5 py-1 text-[11px] font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                            disabled={retryingJobId === j.id}
                            onClick={() => retryJob(j.id)}
                          >
                            {retryingJobId === j.id ? "Retrying..." : "Retry"}
                          </button>
                        </div>
                      </div>
                      {j.error_message && (
                        <div className="mt-0.5 text-red-500/70">{j.error_message}</div>
                      )}
                    </div>
                  ))}
                </div>
              </section>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
