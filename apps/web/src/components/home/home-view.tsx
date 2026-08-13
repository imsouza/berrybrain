"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useWorkspace, appPath } from "@/contexts/workspace-context";
import { t, tf } from "@/i18n";
import { VoicePromptButton } from "@/components/voice-prompt-button";
import { ThemedProgressBar } from "./themed-progress-bar";
import { CircleHelp, ExternalLink } from "lucide-react";

type StatusKind = "running" | "completed" | "failed" | "offline" | "queued" | "waiting_provider";

const QUICK_NOTE_MAX_LENGTH = 2_000;

type HomeSummary = {
  status: {
    worker: string;
    workerLastHeartbeat?: string | null;
    ollama: string;
    cloudProvider: string;
    cloudModel: string;
    cloudStatus: StatusKind | string;
    cloudConfigured?: boolean;
    cloudLastTestAt?: string | null;
    remoteContentConsent?: boolean;
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
    knowledge: { weakConcepts: number; openGaps: number };
    jobs: { pending: number; active: number; failed: number; completedToday: number; total: number };
    ai: { provider: string; model: string; metadata: number; embeddings: number; jobsProcessed: number; errors: number };
  };
  recentNotes: NoteItem[];
  activeJobs: ActiveJob[];
  recentlyCompleted: CompletionItem[];
  recentActivity: ActivityItem[];
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
type ConnectionItem = { id: number; type: string; confidence: number; confidencePercent: number; reason: string; source?: NoteRef | null; target?: NoteRef | null; status?: string };
type NoteRef = { title: string; path: string };
type AttentionItem = { kind: string; title: string; description: string; action: string };

export function HomeView() {
  const w = useWorkspace();
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [starterText, setStarterText] = useState("");
  const [askText, setAskText] = useState("");
  const [creatingDraft, setCreatingDraft] = useState(false);
  const [pipelineProgress, setPipelineProgress] = useState<{ notePath: string; completed: number; total: number; percent: number; currentStep?: string | null; estimatedRemainingSeconds?: number | null; graphState?: string }[]>([]);

  const loadSummary = useCallback(() => {
    setLoading(true);
    setError(false);
    if (w.demo) {
      setSummary(null);
      setError(true);
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

  function updateStarterText(value: string) {
    setStarterText(value.slice(0, QUICK_NOTE_MAX_LENGTH));
  }

  async function createNote(content = "") {
    if (creatingDraft || (content.length > 0 && !content.trim())) return;
    setCreatingDraft(true);
    try {
      const created = await w.createDraft(content);
      if (created) {
        setStarterText("");
        loadSummary();
      }
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
          <button className="bb-action mt-3 h-9 px-4 text-xs font-medium" onClick={loadSummary}>{t("retry")}</button>
        </div>
      </div>
    );
  }

  const displayName = w.demo ? "" : (typeof window !== "undefined" ? localStorage.getItem("bb_display_name") || "Owner" : "Owner");
  const noNotes = summary.stats.notes.total === 0 && w.notes.length === 0;
  const progressStatus = normalizeStatus(summary.progress.status);

  return (
    <div className="bb-brain-view flex-1 overflow-y-auto">
      <div className="bb-page-shell px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <HomeHeader summary={summary} displayName={displayName} onGraph={() => w.setGraphOpen(true)} />
        <HomeAskBar
          value={askText}
          onChange={setAskText}
          onSubmit={() => {
            if (!askText.trim()) return;
            window.location.href = appPath(`/ask?q=${encodeURIComponent(askText.trim())}`);
          }}
          onOpenWorkspace={() => { window.location.href = appPath("/ask"); }}
        />

        <div className="mt-5 grid items-stretch gap-5 xl:grid-cols-[minmax(0,1.2fr)_minmax(340px,0.8fr)]">
          <ComposeCard
            noNotes={noNotes}
            value={starterText}
            disabled={creatingDraft}
            onChange={updateStarterText}
            onSubmit={() => createNote(starterText)}
            onCreateEmpty={() => createNote()}
            creating={creatingDraft}
          />
          <AutopilotProgressCard summary={summary} status={progressStatus} onOpenMonitor={() => w.setMonitorOpen(true)} />
        </div>

        {noNotes && (
          <FirstRunGuide
            onCreate={() => createNote()}
            onScan={w.scanVault}
            onGraph={() => w.setGraphOpen(true)}
            onSettings={() => w.setSettingsOpen(true)}
          />
        )}

        <StatsGrid summary={summary} />

        <section className="mt-8 border-y border-border py-6" aria-label="Operational workspace">
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Knowledge operations</h2>
              <p className="mt-1 text-xs text-muted">Live processing, new relationships, and recent system decisions.</p>
            </div>
            <button className="bb-action h-8 px-3 text-[11px]" onClick={() => w.setMonitorOpen(true)}>{t("monitor")}</button>
          </div>
          <div className="grid auto-rows-fr gap-0 overflow-hidden rounded-lg border border-border bg-panel md:grid-cols-3">
            <div className="h-full border-b border-border p-5 md:border-b-0 md:border-r">
              <ActiveJobsPanel jobs={summary.activeJobs} pipelineProgress={pipelineProgress} onOpenMonitor={() => w.setMonitorOpen(true)} />
            </div>
            <div className="h-full border-b border-border p-5 md:border-b-0 md:border-r">
              <RecentConnectionsList connections={summary.recentConnections} onOpenGraph={() => w.setGraphOpen(true)} onUpdateStatus={updateConnectionStatus} />
            </div>
            <div className="h-full p-5">
              <RecentActivityTimeline activity={summary.recentActivity} completed={summary.recentlyCompleted} />
            </div>
          </div>
        </section>

        {summary.needsAttention.length > 0 && <div className="mt-8 border-b border-border pb-8">
          <NeedsAttentionCard items={summary.needsAttention} onOpenMonitor={() => w.setMonitorOpen(true)} />
        </div>}

        <div className="mt-8 flex justify-end"><button className="bb-action h-9 px-3 text-xs font-medium text-foreground" onClick={w.scanVault}>{t("scanVault")}</button></div>
      </div>
    </div>
  );
}

function FirstRunGuide({
  onCreate,
  onScan,
  onGraph,
  onSettings,
}: {
  onCreate: () => void;
  onScan: () => void;
  onGraph: () => void;
  onSettings: () => void;
}) {
  const steps = [
    {
      title: "Capture",
      text: "Write a quick thought or create an empty note.",
      action: "New note",
      onClick: onCreate,
    },
    {
      title: "Import",
      text: "Already have Markdown files? Scan the vault.",
      action: "Scan vault",
      onClick: onScan,
    },
    {
      title: "Connect",
      text: "Open the graph after notes are processed.",
      action: "Open graph",
      onClick: onGraph,
    },
    {
      title: "Configure",
      text: "Set local or cloud AI before using Ask.",
      action: "Settings",
      onClick: onSettings,
    },
  ];

  return (
    <section className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-label="First steps">
      {steps.map((step, index) => (
        <button
          key={step.title}
          type="button"
          className="bb-card bb-card--interactive p-4 text-left"
          onClick={step.onClick}
        >
          <div className="flex items-center gap-2">
            <span className="grid size-6 place-items-center rounded-full bg-accent-soft text-[11px] font-semibold text-accent">{index + 1}</span>
            <span className="text-sm font-semibold text-foreground">{step.title}</span>
          </div>
          <p className="mt-2 min-h-10 text-xs leading-5 text-muted/65">{step.text}</p>
          <span className="mt-3 inline-flex text-[11px] font-medium text-accent">{step.action}</span>
        </button>
      ))}
    </section>
  );
}

function HomeHeader({ summary, displayName, onGraph }: { summary: HomeSummary; displayName: string; onGraph: () => void }) {
  const usingCloud = Boolean(summary.status.cloudProvider && summary.status.cloudProvider !== "local");
  const providerState = summary.status.cloudStatus;
  const providerStatus = usingCloud
    ? cloudStatusLabel(summary.status.cloudProvider, providerState)
    : "AI · Local";
  const providerTone = usingCloud
    ? providerState === "connected" ? "ok" : providerState === "failed" || providerState === "incomplete" ? "bad" : "muted"
    : summary.status.ollama === "online" ? "ok" : "muted";
  return (
    <header className="bb-brain-hero">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-accent">{t("home")}</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight lg:text-3xl">{displayName ? `${t("homeGreeting")}, ${displayName}.` : `${t("homeGreeting")}.`}</h1>
          <p className="mt-2 text-sm leading-6 text-muted/70">{t("keepWriting")}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <HeaderLink onClick={() => (window.location.href = appPath("/activity"))}>{t("viewActivity")}</HeaderLink>
          <HeaderLink onClick={() => (window.location.href = appPath("/ask"))}>Ask</HeaderLink>
          <HeaderLink onClick={onGraph}>{t("viewGraph")}</HeaderLink>
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">
          <StatusBadge label={`Worker ${summary.status.worker}`} status={summary.status.worker === "running" || summary.status.worker === "online" ? "ok" : "bad"} />
        </span>
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">
          <StatusBadge label={providerStatus} status={providerTone} />
        </span>
        <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">{tf("activeJobsCount", { count: summary.status.activeJobs })} · {tf("queuedCount", { count: summary.status.pendingJobs })}</span>
        {summary.status.lastProcessingAt && (
          <span className="inline-flex items-center gap-2 rounded-full bg-surface/80 px-3 py-1.5 text-[11px] text-muted/70 ring-1 ring-border/40">{t("lastProcessing")} {formatTime(summary.status.lastProcessingAt)}</span>
        )}
      </div>
    </header>
  );
}

function HomeAskBar({
  value,
  onChange,
  onSubmit,
  onOpenWorkspace,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onOpenWorkspace: () => void;
}) {
  return (
    <form
      className="bb-card mt-4 flex flex-col gap-3 p-3 sm:flex-row sm:items-center sm:p-4"
      aria-label="Ask your knowledge graph"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <span className="grid size-9 shrink-0 place-items-center rounded-full bg-accent-soft text-accent" aria-hidden="true">
          <CircleHelp className="size-4" />
        </span>
        <div className="min-w-0 flex-1">
          <label htmlFor="home-ask" className="block text-[10px] font-semibold uppercase tracking-[0.16em] text-muted">Ask BerryBrain</label>
          <input
            id="home-ask"
            value={value}
            onChange={(event) => onChange(event.target.value)}
            className="mt-1 w-full border-0 bg-transparent p-0 text-sm text-foreground outline-none placeholder:text-muted/50"
            placeholder="Ask a question about your notes, concepts, or connections..."
          />
        </div>
      </div>
      <VoicePromptButton value={value} onChange={onChange} />
      <button type="button" className="bb-action grid h-10 w-10 shrink-0 place-items-center" aria-label="Open Ask workspace" title="Open Ask workspace" onClick={onOpenWorkspace}><ExternalLink className="size-4" /></button>
      <button type="submit" disabled={!value.trim()} className="bb-action bb-action--primary h-10 shrink-0 px-5 text-sm font-semibold">
        Ask
      </button>
    </form>
  );
}

function ComposeCard({ noNotes, value, disabled, onChange, onSubmit, onCreateEmpty, creating }: { noNotes: boolean; value: string; disabled: boolean; onChange: (value: string) => void; onSubmit: () => void; onCreateEmpty: () => void; creating: boolean }) {
  const canSubmit = Boolean(value.trim()) && !disabled;

  return (
    <div className="bb-card bb-brain-compose h-full p-5 transition focus-within:border-accent">
      <div className="mb-3 flex items-center gap-2">
        <span className="size-2 rounded-full bg-accent" />
        <span className="text-[11px] font-semibold uppercase tracking-[0.15em] text-muted/50">{t("startWriting")}</span>
      </div>
      <textarea
        aria-label={t("quickNoteLabel")}
        autoFocus
        className="min-h-36 w-full resize-none bg-transparent text-sm leading-7 outline-none placeholder:text-muted/40"
        disabled={disabled}
        maxLength={QUICK_NOTE_MAX_LENGTH}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && canSubmit) {
            event.preventDefault();
            onSubmit();
          }
        }}
        placeholder={noNotes ? t("startFirstNote") : t("startNote")}
        value={value}
      />
      <div className="mt-3 flex flex-col gap-3 border-t border-border/40 pt-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted/50">
          <span>{tf("noteCharacterCount", { count: value.length, max: QUICK_NOTE_MAX_LENGTH })}</span>
        </div>
        <div className="flex items-center justify-end gap-2">
          <button type="button" className="bb-action px-3 py-2 text-xs" disabled={disabled} onClick={onCreateEmpty}>
            {t("createEmptyDraft")}
          </button>
          <button
            type="button"
            className="bb-action bb-action--primary px-4 py-2 text-xs font-semibold"
            disabled={!canSubmit}
            onClick={onSubmit}
          >
            {creating ? t("creatingNote") : t("createNote")}
          </button>
        </div>
      </div>
    </div>
  );
}

function AutopilotProgressCard({ summary, status, onOpenMonitor }: { summary: HomeSummary; status: StatusKind; onOpenMonitor: () => void }) {
  const running = status === "running";
  const waiting = status === "waiting_provider" || status === "queued";
  return (
    <button className="bb-card bb-card--interactive h-full w-full p-5 text-left" onClick={onOpenMonitor}>
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

function ActiveJobsPanel({ jobs, pipelineProgress, onOpenMonitor }: { jobs: ActiveJob[]; pipelineProgress: { notePath: string; completed: number; total: number; percent: number; currentStep?: string | null; estimatedRemainingSeconds?: number | null; graphState?: string }[]; onOpenMonitor: () => void }) {
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
              <button key={job.id} className="bb-subcard w-full p-3 text-left transition hover:border-accent" onClick={onOpenMonitor}>
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
                {pp && <p className="mt-1 text-[10px] text-muted/50">Graph {pp.graphState || "waiting"}{pp.estimatedRemainingSeconds != null ? ` · about ${formatEta(pp.estimatedRemainingSeconds)} remaining` : " · estimating"}</p>}
                <p className="mt-1 text-[10px] text-muted/45">{providerLabel(job.provider || "")}{job.model ? ` · ${job.model}` : ""}</p>
              </button>
            );
          })}
        </div>
      )}
    </Section>
  );
}

function NeedsAttentionCard({ items, onOpenMonitor }: { items: AttentionItem[]; onOpenMonitor: () => void }) {
  if (items.length === 0) {
    return (
      <Section title={t("needsAttention")}>
        <div className="bb-subcard p-4 text-xs text-muted/70">{t("allGood")}</div>
      </Section>
    );
  }
  return (
    <Section title={t("needsAttention")}>
      <div className="space-y-2">
        {items.map((item) => (
          <button key={item.kind} className="bb-subcard w-full p-3 text-left transition hover:border-danger" onClick={onOpenMonitor}>
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
      <div className="grid auto-rows-fr gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard label={t("notes")} value={s.notes.total} detail={`+${s.notes.createdToday} ${t("oneCreatedToday")} · ${s.notes.unassimilated} ${t("notAssimilated")}`} />
        <StatCard label={t("connections")} value={s.connections.total} detail={`${s.connections.createdToday} ${t("newConnections")} · ${percent(s.connections.averageConfidence)} ${t("confidence")}`} />
        <StatCard label={t("concepts")} value={s.concepts.total} detail={`${s.concepts.newToday} ${t("newToday")} · ${s.concepts.withoutPermanentNote} ${t("withoutNote")}`} />
        <StatCard label={t("jobs")} value={s.jobs.total} detail={`${s.jobs.pending} ${t("pending")} · ${tf("activeJobsCount", { count: s.jobs.active })} · ${s.jobs.failed} ${t("errors")}`} />
        <StatCard label={providerLabel(s.ai.provider)} value={s.ai.model ? t("online") : t("local")} detail={`${s.ai.embeddings} ${t("embeddings")} · ${s.ai.metadata} ${t("metadata")}`} />
      </div>
    </Section>
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
            <div key={connection.id} className="bb-subcard p-4">
              <div className="text-xs font-medium">
                {connection.source?.title || t("origin")} ↔ {connection.target?.title || t("destination")}
              </div>
              <p className="mt-1 text-[11px] leading-5 text-muted/65">{connection.reason || t("noReason")}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-muted/55">
                <span>{t("connectionConfidence")}: {connection.confidencePercent}%</span>
                <span className="rounded-full bg-panel px-2 py-1">{connection.status || t("suggested")}</span>
                <button className="bb-action px-2.5 py-1" onClick={onOpenGraph}>{t("viewInGraph")}</button>
                {connection.status !== "confirmed" && (
                  <button className="bb-action px-2.5 py-1" onClick={() => onUpdateStatus(connection.id, "confirm")}>{t("confirm")}</button>
                )}
                {connection.status !== "ignored" && (
                  <button className="bb-action bb-action--danger px-2.5 py-1" onClick={() => onUpdateStatus(connection.id, "ignore")}>{t("ignore")}</button>
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
    <Section title={t("recentActivity")}>
      <div className="grid gap-3">
        <div className="bb-subcard p-4">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">{t("doneRecently")}</div>
          {completed.length === 0 ? <p className="text-xs text-muted/50">{t("noRecentResults")}</p> : completed.slice(0, 5).map((item) => (
            <RowLine key={item.id} left={item.label} right={formatTime(item.completedAt)} />
          ))}
        </div>
        <div className="bb-subcard p-4">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">{t("autoQueue")}</div>
          {activity.length === 0 ? <p className="text-xs text-muted/50">{t("noRecentActivity")}</p> : activity.slice(0, 5).map((item, index) => (
            <RowLine key={item.id || index} left={item.description} right={formatTime(item.when)} />
          ))}
        </div>
      </div>
    </Section>
  );
}

function Section({ title, children, className = "", elevated = false }: { title: string; children: ReactNode; className?: string; elevated?: boolean }) {
  return (
    <section className={`${elevated ? "border-t-2 border-accent pt-4" : ""} ${className}`}>
      <h2 className="bb-section-title mb-4 text-[11px] font-semibold uppercase">{title}</h2>
      {children}
    </section>
  );
}

function StatCard({ label, value, detail }: { label: string; value: number | string; detail?: string }) {
  return (
    <div className="bb-subcard h-full px-4 py-3 text-left">
      <div className="text-xl font-semibold tabular-nums">{value}</div>
      <div className="mt-0.5 text-[10px] font-semibold uppercase tracking-wide text-muted/70">{label}</div>
      {detail && <div className="mt-2 text-[10px] leading-4 text-muted/60">{detail}</div>}
    </div>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="bb-subcard p-4 text-xs">
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

function HeaderLink({ children, onClick, primary }: { children: ReactNode; onClick: () => void; primary?: boolean }) {
  const cls = primary
    ? "bb-action bb-action--primary px-3 py-1.5 text-[11px] font-semibold"
    : "bb-action px-2.5 py-1.5 text-[11px] font-medium";
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

function cloudStatusLabel(provider: string, status: string) {
  const name = providerLabel(provider);
  const suffix: Record<string, string> = {
    connected: "connected",
    configured: "configured, not tested",
    disabled: "disabled by privacy setting",
    incomplete: "setup incomplete",
    failed: "connection failed",
  };
  return `AI · ${name} ${suffix[status] || status}`;
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

function formatEta(seconds: number) {
  if (seconds < 60) return `${Math.max(1, Math.round(seconds))} sec`;
  const minutes = Math.ceil(seconds / 60);
  return minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)} hr ${minutes % 60} min`;
}
