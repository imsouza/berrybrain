"use client";

import { useEffect, useState } from "react";

type LogEntry = {
  id: number;
  action_type: string;
  target_type: string;
  target_id: string;
  description: string;
  created_at: string;
};

type WorkerInfo = {
  status: string;
  last_heartbeat: string;
  jobs_processed: number;
  errors: number;
  ollama_healthy: boolean;
} | null;

type Props = {
  open: boolean;
  apiUrl: string;
  onClose: () => void;
};

type Tab = "jobs" | "health" | "logs" | "stats";

export function ObservabilityPanel({ open, apiUrl, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("jobs");
  const [jobs, setJobs] = useState<any[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [worker, setWorker] = useState<WorkerInfo>(null);
  const [stats, setStats] = useState<any>(null);
  const [filter, setFilter] = useState("");
  const [retryingJobId, setRetryingJobId] = useState<number | null>(null);
  const [jobActionStatus, setJobActionStatus] = useState("");

  useEffect(() => {
    if (!open) return;
    if (apiUrl === "__demo__") {
      setJobs([]);
      setLogs([]);
      setWorker(null);
      setStats(null);
      return;
    }
    async function load() {
      try {
        const [jRes, lRes, wRes, sRes] = await Promise.all([
          fetch(`${apiUrl}/api/v1/jobs?limit=50`),
          fetch(`${apiUrl}/api/v1/automation-logs?limit=50`),
          fetch(`${apiUrl}/api/v1/worker/status`),
          fetch(`${apiUrl}/api/v1/monitor/stats`),
        ]);
        const j = await jRes.json();
        const l = await lRes.json();
        const w = await wRes.json();
        const s = await sRes.json();
        setJobs(j.jobs || []);
        setLogs(l.logs || []);
        setWorker(w.worker);
        setStats(s);
      } catch {}
    }
    load();
    const iv = setInterval(load, 8000);
    return () => clearInterval(iv);
  }, [apiUrl, open]);

  const isFailedJob = (job: any) => job.status === "failed" || job.status === "dead_letter";
  const loadData = async () => {
    const [jRes, lRes, wRes, sRes] = await Promise.all([
      fetch(`${apiUrl}/api/v1/jobs?limit=50`),
      fetch(`${apiUrl}/api/v1/automation-logs?limit=50`),
      fetch(`${apiUrl}/api/v1/worker/status`),
      fetch(`${apiUrl}/api/v1/monitor/stats`),
    ]);
    const j = await jRes.json();
    const l = await lRes.json();
    const w = await wRes.json();
    const s = await sRes.json();
    setJobs(j.jobs || []);
    setLogs(l.logs || []);
    setWorker(w.worker);
    setStats(s);
  };

  async function retryJob(jobId: number) {
    setRetryingJobId(jobId);
    setJobActionStatus("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/jobs/${jobId}/retry`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Retry failed.");
      await loadData();
      setJobActionStatus(`Job #${jobId} queued again.`);
    } catch (error) {
      setJobActionStatus(error instanceof Error ? error.message : "Retry failed.");
    } finally {
      setRetryingJobId(null);
    }
  }

  const filtered = filter
    ? jobs.filter(
        (j) =>
          (filter === "failed" ? isFailedJob(j) : j.status === filter) ||
          j.type.toLowerCase().includes(filter.toLowerCase())
      )
    : jobs;

  const counts = {
    pending: jobs.filter((j) => j.status === "pending").length,
    running: jobs.filter((j) => j.status === "running").length,
    completed: jobs.filter((j) => j.status === "completed").length,
    failed: jobs.filter(isFailedJob).length,
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        onClick={(e) => { e.stopPropagation(); onClose(); }}
      />
      <div className="bb-card bb-card--elevated relative z-50 flex max-h-[70vh] w-full max-w-[92vw] flex-col overflow-hidden sm:w-[720px]">
        <div className="flex items-center justify-between px-6 py-4">
          <h2 className="text-base font-semibold tracking-tight">Monitor</h2>
          <button
            className="rounded-lg p-1.5 text-muted transition hover:bg-black/5 hover:text-foreground"
            onClick={onClose}
            aria-label="Close"
          >
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="flex gap-1 px-6 pb-1">
          {([
            { key: "jobs", label: "Jobs" },
            { key: "health", label: "Health" },
            { key: "logs", label: "Logs" },
            { key: "stats", label: "Stats" },
          ] as { key: Tab; label: string }[]).map(({ key, label }) => (
            <button
              key={key}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                tab === key
                  ? "bg-black/5 text-foreground"
                  : "text-muted hover:text-foreground"
              }`}
              onClick={() => setTab(key)}
            >
              {label}
            </button>
          ))}
        </div>

        <div className="min-h-0 flex-1 overflow-y-auto px-6 pb-6">
          {tab === "jobs" && (
            <div>
              <div className="sticky top-0 z-10 -mx-6 flex gap-1 bg-panel px-6 pb-3 pt-2">
                {[
                  { key: "", label: "All" },
                  { key: "pending", label: "Pending" },
                  { key: "running", label: "Running" },
                  { key: "completed", label: "OK" },
                  { key: "failed", label: "Failed" },
                ].map(({ key, label }) => (
                  <button
                    key={key}
                    className={`rounded-lg px-2.5 py-1 text-[11px] font-medium transition ${
                      filter === key
                        ? "bg-foreground text-background"
                        : "bg-black/5 text-muted hover:bg-black/10"
                    }`}
                    onClick={() => setFilter(key)}
                  >
                    {label}
                    {jobs.length > 0 && (
                      <span className="ml-1 opacity-60">
                        {key === "" ? jobs.length : key === "failed" ? jobs.filter(isFailedJob).length : jobs.filter((j) => j.status === key).length}
                      </span>
                    )}
                  </button>
                ))}
              </div>
              {jobActionStatus && (
                <div className="mb-2 rounded-lg bg-accent/10 px-3 py-2 text-[11px] text-foreground ring-1 ring-accent/20">
                  {jobActionStatus}
                </div>
              )}

              <div className="mt-2 space-y-1.5">
                {filtered.length === 0 ? (
                  <div className="py-12 text-center text-xs text-muted">
                    No jobs.
                  </div>
                ) : (
                  filtered.map((job: any) => {
                    const dot =
                      job.status === "completed" ? "bg-emerald-400" :
                      isFailedJob(job) ? "bg-red-400" :
                      job.status === "running" ? "bg-blue-400" : "bg-zinc-300";
                    return (
                      <div key={job.id} className="group rounded-xl bg-black/[0.02] px-4 py-3 transition hover:bg-black/[0.04]">
                        <div className="flex items-center gap-3">
                          <span className={`inline-block size-1.5 shrink-0 rounded-full ${dot}`} />
                          <span className="min-w-0 flex-1 truncate text-xs font-medium">{job.type}</span>
                          {job.status === "dead_letter" && (
                            <span className="rounded-md bg-red-500/10 px-1.5 py-0.5 text-[10px] font-medium text-red-500 ring-1 ring-red-500/20">
                              dead letter
                            </span>
                          )}
                          <span className="shrink-0 text-[11px] tabular-nums text-muted">
                            {job.attempts}/{job.max_attempts}
                          </span>
                          {isFailedJob(job) && (
                            <button
                              className="bb-action shrink-0 px-2.5 py-1 text-[11px] font-medium"
                              disabled={retryingJobId === job.id}
                              onClick={() => retryJob(job.id)}
                            >
                              {retryingJobId === job.id ? "Retrying..." : "Retry"}
                            </button>
                          )}
                        </div>
                        <div className="mt-1.5 pl-[18px]">
                          <span className="text-[11px] text-muted">
                            {job.payload?.note_path ?? "—"}
                          </span>
                        </div>
                        {job.error_message && (
                          <div className="mt-2 pl-[18px] text-[11px] leading-relaxed text-red-500">
                            {job.error_message.slice(0, 200)}
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          {tab === "health" && (
            <div className="space-y-4 pt-2">
              <div className="rounded-2xl bg-black/[0.02] p-5">
                <div className="text-xs font-medium text-muted">Worker</div>
                {worker ? (
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className={`inline-block size-2 rounded-full ${worker.status === "running" ? "bg-emerald-400" : "bg-red-400"}`} />
                      <span className="text-sm font-medium">{worker.status}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs text-muted">
                      <div>Processed: <span className="tabular-nums text-foreground">{worker.jobs_processed}</span></div>
                      <div>Errors: <span className="tabular-nums text-foreground">{worker.errors}</span></div>
                      <div className="col-span-2">
                        Heartbeat: <span className="text-foreground">{new Date(worker.last_heartbeat).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="mt-3 text-xs text-muted">Offline. No heartbeat received.</p>
                )}
              </div>

              <div className="rounded-2xl bg-black/[0.02] p-5">
                <div className="text-xs font-medium text-muted">Ollama</div>
                <div className="mt-3 flex items-center gap-2">
                  <span className={`inline-block size-2 rounded-full ${worker?.ollama_healthy ? "bg-emerald-400" : "bg-red-400"}`} />
                  <span className="text-sm font-medium">{worker?.ollama_healthy ? "Online" : "Offline"}</span>
                </div>
              </div>

              <div className="rounded-2xl bg-black/[0.02] p-5">
                <div className="mb-3 text-xs font-medium text-muted">Summary</div>
                <div className="grid grid-cols-4 gap-4">
                  {[
                    { label: "Pending", value: counts.pending, color: "text-muted" },
                    { label: "Active", value: counts.running, color: "text-blue-500" },
                    { label: "OK", value: counts.completed, color: "text-emerald-500" },
                    { label: "Failed", value: counts.failed, color: "text-red-500" },
                  ].map(({ label, value, color }) => (
                    <div key={label} className="text-center">
                      <div className={`text-2xl font-semibold tabular-nums ${color}`}>{value}</div>
                      <div className="mt-0.5 text-[10px] text-muted">{label}</div>
                    </div>
                  ))}
                </div>
              </div>

              {stats?.running_jobs && stats.running_jobs.length > 0 && (
                <div className="rounded-2xl bg-black/[0.02] p-5">
                  <div className="mb-3 text-xs font-medium text-muted">Running sub-agents</div>
                  <div className="space-y-2">
                    {stats.running_jobs.map((rj: any) => (
                      <div key={rj.id} className="flex items-center justify-between rounded-lg bg-black/[0.03] px-3 py-2">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="inline-block size-1.5 rounded-full bg-blue-400 animate-pulse" />
                            <span className="text-xs font-medium">{rj.type.replace(/_/g, " ")}</span>
                          </div>
                          <div className="mt-0.5 text-[10px] text-muted truncate">{rj.note_path}</div>
                        </div>
                        <span className="shrink-0 text-[11px] tabular-nums text-muted">
                          {Math.floor(rj.elapsed_s)}s
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {tab === "logs" && (
            <div className="space-y-1.5 pt-2">
              {logs.length === 0 ? (
                <div className="py-12 text-center text-xs text-muted">No AI logs.</div>
              ) : (
                logs.map((log) => (
                  <div key={log.id} className="rounded-xl bg-black/[0.02] px-4 py-3 transition hover:bg-black/[0.04]">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium">{log.action_type}</span>
                      <span className="text-[11px] tabular-nums text-muted">
                        {new Date(log.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="mt-1 text-[11px] text-muted">
                      {log.target_type}: {log.target_id}
                    </div>
                    {log.description && (
                      <div className="mt-1 text-[11px] text-muted">{log.description.slice(0, 150)}</div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {tab === "stats" && stats && (
            <div className="space-y-4 pt-2">
              <div className="rounded-2xl bg-black/[0.02] p-5">
                <div className="text-xs font-medium text-muted">Vault</div>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <StatBlock label="Notes" value={stats.notes} />
                  <StatBlock label="Connections" value={stats.connections} />
                  <StatBlock label="Insights" value={stats.insights} />
                  <StatBlock label="AI metadata" value={stats.metadata} />
                  <StatBlock label="Embeddings" value={stats.embeddings ?? 0} />
                </div>
              </div>

              <div className="rounded-2xl bg-black/[0.02] p-5">
                <div className="text-xs font-medium text-muted">Jobs</div>
                <div className="mt-3 grid grid-cols-3 gap-3">
                  <StatBlock label="Total" value={stats.jobs?.total ?? 0} />
                  <StatBlock label="Completed" value={stats.jobs?.completed ?? 0} />
                  <StatBlock label="Failed" value={stats.jobs?.failed ?? 0} />
                  <StatBlock label="Pending" value={stats.jobs?.pending ?? 0} />
                  <StatBlock label="Per hour" value={stats.jobs?.per_hour ?? 0} />
                </div>
                {stats.job_types && Object.keys(stats.job_types).length > 0 && (
                  <div className="mt-4">
                    <div className="text-[11px] text-muted/60 mb-2">By type</div>
                    <div className="space-y-2">
                      {Object.entries(stats.job_types as Record<string, number>).map(([type, count]) => (
                        <div key={type} className="flex items-center justify-between">
                          <span className="text-xs text-muted">{type.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}</span>
                          <div className="flex items-center gap-2">
                            <div className="h-2 rounded-full bg-black/[0.05]" style={{ width: Math.max(20, count * 6) }}>
                              <div className="h-full rounded-full bg-accent/60" style={{ width: `${Math.min(100, count / (stats.jobs?.completed || 1) * 100)}%` }} />
                            </div>
                            <span className="text-xs tabular-nums font-medium">{count as number}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {stats.recent_completions && stats.recent_completions.length > 0 && (
                  <div className="mt-4">
                    <div className="text-[11px] text-muted/60 mb-2">Recent ({stats.recent_completions.length})</div>
                    <div className="space-y-1">
                      {stats.recent_completions.slice(0, 8).map((c: any, i: number) => (
                        <div key={i} className="flex items-center justify-between text-[11px] text-muted">
                          <span>{c.type?.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase())}</span>
                          <span className="tabular-nums">{c.when?.slice(11, 19)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          {tab === "stats" && !stats && (
            <div className="py-12 text-center text-xs text-muted">Loading...</div>
          )}
        </div>
      </div>
    </div>
  );
}

function StatBlock({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-black/[0.03] px-3 py-2 text-center">
      <div className="text-lg font-semibold tabular-nums">{value}</div>
      <div className="text-[10px] text-muted/60">{label}</div>
    </div>
  );
}
