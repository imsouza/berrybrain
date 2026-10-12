"use client";

type Snapshot = {
  notes: { total: number; unassimilated: number };
  concepts: { total: number };
  connections: { total: number };
  jobs: { total: number; pending: number; active: number; failed: number; byStatus?: Record<string, number> };
};

const colors = ["#96B55C", "#4F7CCB", "#D4A843", "#CC4168", "#8B6F9F", "#6B8FAF"];
const statusColors: Record<string, string> = {
  completed: "#96B55C", pending: "#D4A843", running: "#4F7CCB",
  failed: "#CC4168", dead_letter: "#CC4168", superseded: "#8B6F9F",
  cancelled: "#6B8FAF", cancel_requested: "#D4A843",
};
const number = (value: number) => value.toLocaleString();

export function WorkspaceCharts({ stats }: { stats: Snapshot }) {
  const assimilated = Math.max(0, stats.notes.total - stats.notes.unassimilated);
  const ratio = stats.notes.total ? Math.min(1, assimilated / stats.notes.total) : 0;
  const inventory = [
    { label: "Notes", value: stats.notes.total },
    { label: "Concepts", value: stats.concepts.total },
    { label: "Connections", value: stats.connections.total },
  ];
  const max = Math.max(1, ...inventory.map(item => item.value));
  const statuses = stats.jobs.byStatus || {
    pending: stats.jobs.pending, running: stats.jobs.active, failed: stats.jobs.failed,
    other: Math.max(0, stats.jobs.total - stats.jobs.pending - stats.jobs.active - stats.jobs.failed),
  };
  const jobs = Object.entries(statuses).filter(([, count]) => count > 0).sort(([a], [b]) => a.localeCompare(b));
  const total = jobs.reduce((sum, [, count]) => sum + count, 0);
  return <div className="mt-4 grid gap-4 lg:grid-cols-3" data-testid="workspace-charts">
    <figure className="rounded-xl border border-border/60 bg-surface/40 p-4">
      <figcaption className="text-xs font-semibold">Note assimilation</figcaption>
      <div className="mt-3 flex items-center gap-5">
        <svg className="size-28 shrink-0" viewBox="0 0 120 120" role="img" aria-label={`${assimilated} of ${stats.notes.total} notes assimilated`}>
          <circle cx="60" cy="60" r="44" fill="none" stroke="var(--color-border)" strokeWidth="10" />
          <circle cx="60" cy="60" r="44" fill="none" stroke="var(--color-accent)" strokeWidth="10" pathLength="100" strokeDasharray={`${ratio * 100} 100`} strokeLinecap={ratio ? "round" : "butt"} transform="rotate(-90 60 60)" />
          <text x="60" y="64" textAnchor="middle" fill="currentColor" fontSize="22" fontWeight="600">{stats.notes.total ? `${Math.round(ratio * 100)}%` : "—"}</text>
        </svg>
        <div className="space-y-2 text-xs text-muted">
          <p><strong className="text-foreground tabular-nums">{number(assimilated)}</strong> assimilated</p>
          <p><strong className="text-foreground tabular-nums">{number(stats.notes.unassimilated)}</strong> awaiting assimilation</p>
          <p className="text-[10px]">Current notes, not processing speed.</p>
        </div>
      </div>
    </figure>
    <figure className="rounded-xl border border-border/60 bg-surface/40 p-4">
      <figcaption className="text-xs font-semibold">Knowledge inventory</figcaption>
      <div className="mt-4 space-y-4">
        {inventory.map((item, index) => <div key={item.label}>
          <div className="mb-1 flex justify-between text-[11px]"><span className="text-muted">{item.label}</span><strong className="tabular-nums">{number(item.value)}</strong></div>
          <svg viewBox="0 0 240 8" className="h-2 w-full" preserveAspectRatio="none" role="img" aria-label={`${item.label}: ${item.value}`}>
            <rect width="240" height="8" rx="4" fill="var(--color-border)" />
            <rect width={240 * item.value / max} height="8" rx="4" fill={colors[index]} />
          </svg>
        </div>)}
      </div>
    </figure>
    <figure className="rounded-xl border border-border/60 bg-surface/40 p-4">
      <figcaption className="flex justify-between gap-2 text-xs font-semibold"><span>Job outcomes</span><span className="tabular-nums text-muted">{number(total)} total</span></figcaption>
      <div className="mt-4 flex h-3 overflow-hidden rounded-full bg-border" role="img" aria-label={jobs.map(([status, count]) => `${status}: ${count}`).join(", ") || "No jobs"}>
        {jobs.map(([status, count]) => <div key={status} style={{ width: `${total ? count / total * 100 : 0}%`, backgroundColor: statusColors[status] || "#6B8FAF" }} title={`${status}: ${number(count)}`} />)}
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
        {jobs.map(([status, count]) => <div key={status} className="flex min-w-0 items-center justify-between gap-2">
          <dt className="flex min-w-0 items-center gap-1.5 text-muted"><span className="size-1.5 shrink-0 rounded-full" style={{ backgroundColor: statusColors[status] || "#6B8FAF" }} /><span className="truncate">{status.replaceAll("_", " ")}</span></dt><dd className="tabular-nums">{number(count)}</dd>
        </div>)}
      </dl>
      <p className="mt-3 text-[10px] text-muted">Lifetime states. Superseded is not completed.</p>
    </figure>
  </div>;
}
