"use client";

import { useWorkspace } from "@/contexts/workspace-context";
import { useEffect, useState } from "react";

type Step = { type: string; label: string; status: string; error: string | null; attempts: number; id: number | null };
type NoteConnection = {
  id: number;
  source_note: { id: number; title: string; path: string } | null;
  target_note: { id: number; title: string; path: string } | null;
  connection_type: string;
  confidence: number;
  reason: string;
  evidence?: string[];
  status?: string;
  provider?: string;
  model?: string;
};

export function RightPanel() {
  const w = useWorkspace();
  const [steps, setSteps] = useState<Step[]>([]);
  const [stepInfo, setStepInfo] = useState({ completed: 0, total: 0, running: 0, failed: 0 });
  const [connections, setConnections] = useState<NoteConnection[]>([]);

  useEffect(() => {
    if (!w.active || w.demo || w.api === "__browser__") { setSteps([]); return; }
    const fetchStatus = () => {
      fetch(`${w.api}/api/v1/notes/${w.active!.path.split("/").map(encodeURIComponent).join("/")}/status`)
        .then(r => r.json()).then(d => { setSteps(d.steps || []); setStepInfo(d); }).catch(() => {});
    };
    fetchStatus();
    const iv = setInterval(fetchStatus, 4000);
    return () => clearInterval(iv);
  }, [w.active?.path, w.api, w.demo]);

  useEffect(() => {
    if (!w.active || w.demo || w.api === "__browser__") { setConnections([]); return; }
    fetch(`${w.api}/api/v1/connections/${w.active.path.split("/").map(encodeURIComponent).join("/")}`)
      .then(r => r.json())
      .then(d => setConnections(d.connections || []))
      .catch(() => setConnections([]));
  }, [w.active?.path, w.api, w.demo]);

  const statusIcon = (s: string) => {
    if (s === "completed") return <span className="size-1.5 rounded-full bg-emerald-400 shrink-0" />;
    if (s === "running") return <span className="size-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />;
    if (s === "failed") return <span className="size-1.5 rounded-full bg-red-400 shrink-0" />;
    return <span className="size-1.5 rounded-full bg-zinc-300 shrink-0" />;
  };

  const updateConnection = async (id: number, action: "confirm" | "ignore") => {
    if (w.demo || w.api === "__browser__") return;
    await fetch(`${w.api}/api/v1/connections/id/${id}/${action}`, { method: "POST" });
    if (!w.active) return;
    const r = await fetch(`${w.api}/api/v1/connections/${w.active.path.split("/").map(encodeURIComponent).join("/")}`);
    const d = await r.json();
    setConnections(d.connections || []);
  };

  const reprocessNote = async () => {
    if (!w.active) return;
    if (w.demo) {
      w.toast("Reprocessing is disabled in demo mode.", "info");
      return;
    }
    if (w.api === "__browser__") {
      w.toast("Cognitive processing requires the self-hosted API and worker.", "info");
      return;
    }
    const encoded = w.active.path.split("/").map(encodeURIComponent).join("/");
    const response = await fetch(`${w.api}/api/v1/notes/${encoded}/reprocess`, { method: "POST" });
    if (!response.ok) {
      w.toast("Could not reprocess note.", "error");
      return;
    }
    w.toast("Note queued for reprocessing.", "success");
    setTimeout(() => w.active && fetch(`${w.api}/api/v1/notes/${encoded}/status`).then(r => r.json()).then(d => setSteps(d.steps || [])), 1500);
  };

  const expandGraph = async () => {
    if (w.demo) {
      w.toast("Graph expansion is disabled in demo mode.", "info");
      return;
    }
    if (w.api === "__browser__") {
      w.toast("Graph expansion requires the self-hosted API and worker.", "info");
      return;
    }
    await fetch(`${w.api}/api/v1/graph/expand`, { method: "POST" });
  };

  const relatedInsights = w.active
    ? w.insights.filter(i => {
        const haystack = [i.title, i.description, ...(i.evidence || [])].join(" ").toLowerCase();
        return haystack.includes(w.active!.title.toLowerCase()) || haystack.includes(w.active!.path.toLowerCase());
      }).slice(0, 3)
    : [];

  return (
    <aside className="bb-context-panel fixed inset-y-0 right-0 z-40 flex w-[min(88vw,20rem)] flex-col overflow-y-auto bg-panel lg:static lg:z-auto lg:w-72 lg:flex-shrink-0" aria-label="Context panel">
      <div className="flex items-center justify-between px-4 py-3.5 border-b border-border/50">
        <h2 className="text-xs font-semibold tracking-tight">{w.active ? w.active.title.slice(0, 18) : "Activity"}</h2>
        <button className="rounded-lg p-1 text-muted hover:bg-surface" onClick={() => w.setRightOpen(false)} aria-label="Close">
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <div className="p-4 space-y-4">
        {w.active ? (
          <>
            {steps.length > 0 && (
              <Section title="Processing">
                <div className="mb-1.5 flex items-center gap-2">
                  <div className="h-1.5 flex-1 rounded-full bg-border/50 overflow-hidden">
                    <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${stepInfo.total ? (stepInfo.completed / stepInfo.total) * 100 : 0}%` }} />
                  </div>
                  <span className="text-[10px] tabular-nums text-muted/50">{stepInfo.completed}/{stepInfo.total}</span>
                </div>
                <div className="space-y-1">
                  {steps.slice(0, 6).map(s => (
                    <div key={s.type} className="flex items-center gap-2 text-[11px]">
                      {statusIcon(s.status)}
                      <span className={s.status === "running" ? "text-foreground font-medium" : s.status === "failed" ? "text-red-400" : "text-muted/60"}>{s.label}</span>
                      {s.error && <span className="text-[10px] text-red-400/70 truncate ml-auto max-w-[120px]" title={s.error}>{s.error.slice(0, 25)}</span>}
                    </div>
                  ))}
                </div>
              </Section>
            )}

            <Section title="Status">
              <div className="text-xs text-muted space-y-1">
                <Row k="Words" v={w.draft.split(/\s+/).filter(Boolean).length} />
                <Row k="Characters" v={w.draft.length} />
                <Row k="Reading time" v={`~${Math.max(1, Math.ceil(w.draft.split(/\s+/).filter(Boolean).length / 200))} min`} />
                <Row k="Saved" v={w.autosave === "saved" ? "Yes" : "No"} />
              </div>
            </Section>

            <Section title="Connections">
              <div className="space-y-2">
                {connections.slice(0, 4).map(c => {
                  const other = c.source_note?.path === w.active?.path ? c.target_note : c.source_note;
                  return (
                    <div key={c.id} className="rounded-xl bg-surface p-2">
                      <div className="mb-1 flex items-center gap-2">
                        <span className="size-1.5 rounded-full bg-accent shrink-0" />
                        <button className="truncate text-left text-[11px] font-medium text-foreground hover:text-accent" onClick={() => other?.path && w.openNote(other.path)}>
                          {other?.title || "Connection"}
                        </button>
                        <span className="ml-auto text-[10px] text-muted/50">{formatConfidence(c.confidence)}</span>
                      </div>
                      <p className="line-clamp-3 text-[10px] text-muted/70">{c.reason || "Connection has no explanation."}</p>
                      {!!c.evidence?.length && <p className="mt-1 truncate text-[10px] text-muted/45">Evidence: {c.evidence.slice(0, 2).map(formatEvidenceLabel).join(" · ")}</p>}
                      <div className="mt-1.5 flex items-center gap-1">
                        <span className="rounded-full bg-panel px-1.5 py-0.5 text-[9px] text-muted/60">{c.connection_type}</span>
                        <span className="rounded-full bg-panel px-1.5 py-0.5 text-[9px] text-muted/60">{c.status || "suggested"}</span>
                        {c.status !== "confirmed" && <button className="ml-auto text-[10px] text-accent" onClick={() => updateConnection(c.id, "confirm")}>Confirm</button>}
                        {c.status !== "ignored" && <button className="text-[10px] text-muted/60" onClick={() => updateConnection(c.id, "ignore")}>Ignore</button>}
                      </div>
                    </div>
                  );
                })}
                {connections.length === 0 && <p className="text-[11px] text-muted/50">No real connections found for this note.</p>}
              </div>
            </Section>

            <Section title="Actions">
              <div className="flex flex-wrap gap-1.5">
                <button className="bb-action px-2.5 py-1.5 text-[10px]" onClick={reprocessNote}>Reprocess</button>
                <button className="bb-action px-2.5 py-1.5 text-[10px]" onClick={expandGraph}>Expand graph</button>
                <button className="bb-action px-2.5 py-1.5 text-[10px] text-amber-600" onClick={() => w.setGraphOpen(true)}>View in graph</button>
              </div>
            </Section>

            <Section title="Related insights">
              <div className="space-y-2">
                {relatedInsights.map(i => (
                  <div key={i.id} className="rounded-xl bg-surface p-2">
                    <div className="mb-1 flex items-center gap-2">
                      <span className="text-[10px] font-medium text-accent">{i.type}</span>
                      <span className="ml-auto text-[10px] text-muted/50">{i.status || "suggested"}</span>
                    </div>
                    <div className="text-[11px] font-medium text-foreground">{i.title}</div>
                    <p className="mt-0.5 line-clamp-3 text-[10px] text-muted/70">{i.description}</p>
                    {i.suggested_action && <p className="mt-1 text-[10px] text-muted/55">Action: {i.suggested_action}</p>}
                  </div>
                ))}
                {relatedInsights.length === 0 && <p className="text-[11px] text-muted/50">No related insight saved yet.</p>}
              </div>
            </Section>

            <Section title="Activity">
              {w.jobs.filter(j => j.payload?.note_path === w.active?.path).slice(0, 5).map(j => (
                <div key={j.id} className="flex items-center gap-2 text-[11px] text-muted">
                  {statusIcon(j.status)}
                  {j.type} · {j.status}
                </div>
              ))}
              {!w.jobs.some(j => j.payload?.note_path === w.active?.path) && <p className="text-[11px] text-muted/50">No jobs.</p>}
            </Section>
          </>
        ) : (
          <>
            <Section title="Processing now">
              {w.jobs.filter(j => j.status === "running").slice(0, 3).map(j => (
                <div key={j.id} className="flex items-center gap-2 text-[11px]">
                  <span className="size-1.5 rounded-full bg-amber-400 animate-pulse shrink-0" />
                  <span className="truncate text-foreground/70">{j.type}</span>
                  <span className="text-muted/40 ml-auto text-[10px]">{j.payload?.note_path?.split("/").pop()}</span>
                </div>
              ))}
              {!w.jobs.some(j => j.status === "running") && (
                <p className="text-[11px] text-muted/50">{w.jobs.filter(j => j.status === "pending").length ? `${w.jobs.filter(j => j.status === "pending").length} pending` : "Up to date"}</p>
              )}
            </Section>

            <Section title="Stats">
              <div className="grid grid-cols-2 gap-2">
                <Stat label="Notes" val={w.stats?.notes ?? w.notes.length} />
                <Stat label="Connections" val={w.stats?.connections ?? 0} />
                <Stat label="AI" val={w.stats?.metadata ?? 0} />
              </div>
            </Section>

            <Section title="Recent jobs">
              {w.jobs.slice(0, 6).map(j => (
                <div key={j.id} className="flex items-center gap-2 text-[11px] text-muted">
                  {statusIcon(j.status)}
                  <span className="truncate">{j.type}</span>
                </div>
              ))}
              {w.jobs.length === 0 && <p className="text-[11px] text-muted/50">No jobs.</p>}
            </Section>
          </>
        )}
      </div>
    </aside>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><div className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted/40">{title}</div>{children}</div>;
}

function Stat({ label, val }: { label: string; val: number }) {
  return <div className="rounded-xl bg-surface px-3 py-2 text-center"><div className="text-lg font-semibold tabular-nums">{val}</div><div className="text-[10px] text-muted/50">{label}</div></div>;
}

function Row({ k, v }: { k: string; v: string | number }) {
  return <div className="flex justify-between"><span className="text-muted/50">{k}</span><span className="tabular-nums">{v}</span></div>;
}

function formatConfidence(value?: number) {
  if (value === undefined || value === null) return "-";
  return `${Math.round(value <= 1 ? value * 100 : value)}%`;
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
  return [
    record.title || record.label || record.source || "",
    record.text || record.reference || record.path || record.reason || "",
  ].filter(Boolean).join(": ");
}
