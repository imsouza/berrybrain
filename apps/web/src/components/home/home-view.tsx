"use client";

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useWorkspace } from "@/contexts/workspace-context";
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
    jobs: { pending: number; active: number; failed: number; completedToday: number; total: number };
    ai: { provider: string; model: string; metadata: number; embeddings: number; jobsProcessed: number; errors: number };
  };
  recentNotes: NoteItem[];
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

export function HomeView() {
  const w = useWorkspace();
  const [summary, setSummary] = useState<HomeSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [starterText, setStarterText] = useState("");
  const [creatingDraft, setCreatingDraft] = useState(false);

  const loadSummary = useCallback(() => {
    setLoading(true);
    setError(false);
    fetch(`${w.api}/api/v1/home/summary`)
      .then((r) => {
        if (!r.ok) throw new Error("home-summary");
        return r.json();
      })
      .then(setSummary)
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, [w.api]);

  const updateConnectionStatus = useCallback(
    async (id: number, action: "confirm" | "ignore") => {
      const response = await fetch(`${w.api}/api/v1/connections/id/${id}/${action}`, {
        method: "POST",
      });
      if (!response.ok) {
        w.toast("Não foi possível atualizar a conexão.", "error");
        return;
      }
      w.toast(action === "confirm" ? "Conexão confirmada." : "Conexão ignorada.", "success");
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
        <div className="text-sm text-muted/40 animate-pulse-soft">Carregando resumo do BerryBrain...</div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="flex-1 flex items-center justify-center px-6">
        <div className="text-center">
          <div className="text-sm font-medium">Não foi possível carregar a Home.</div>
          <button className="mt-3 h-9 rounded-xl bg-accent px-4 text-xs font-medium text-white" onClick={loadSummary}>Tentar novamente</button>
        </div>
      </div>
    );
  }

  const nome = typeof window !== "undefined" ? localStorage.getItem("bb_nome") || "Mateus" : "Mateus";
  const noNotes = summary.stats.notes.total === 0 && w.notes.length === 0;
  const progressStatus = normalizeStatus(summary.progress.status);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto max-w-5xl px-6 py-10 lg:px-8">
        <HomeHeader summary={summary} nome={nome} onGraph={() => w.setGraphOpen(true)} />

        <div className="py-6">
          <textarea
            autoFocus
            className="min-h-40 w-full resize-none rounded-3xl border border-border bg-panel px-5 py-4 text-sm leading-7 shadow-sm outline-none transition placeholder:text-muted/35 focus:border-accent"
            disabled={creatingDraft}
            onChange={(event) => startWriting(event.target.value)}
            placeholder={noNotes ? "Comece escrevendo sua primeira nota." : "Comece a escrever. O BerryBrain cria a nota, salva no vault e aciona o Autopilot."}
            value={starterText}
          />
          <div className="mt-2 flex items-center justify-between text-[11px] text-muted/45">
            <span>{creatingDraft ? "Criando nota..." : "Sem título necessário"}</span>
            <button className="rounded-lg px-2 py-1 hover:bg-surface hover:text-muted" onClick={() => w.createDraft()}>
              Criar rascunho vazio
            </button>
          </div>
        </div>

        <AutopilotProgressCard summary={summary} status={progressStatus} onOpenMonitor={() => w.setMonitorOpen(true)} />

        <div className="mt-8 grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)]">
          <div className="space-y-6">
            <InsightsPreview insights={summary.recentInsights} apiUrl={w.api} onUpdate={loadSummary} />
          </div>
          <div className="space-y-6">
            <ActiveJobsPanel jobs={summary.activeJobs} onOpenMonitor={() => w.setMonitorOpen(true)} />
            <GraphSummaryCard summary={summary} onOpenGraph={() => w.setGraphOpen(true)} apiUrl={w.api} onToast={w.toast} />
            {summary.needsAttention.length > 0 && (
            <NeedsAttentionCard items={summary.needsAttention} onOpenMonitor={() => w.setMonitorOpen(true)} />
          )}
          </div>
        </div>

        <StatsGrid summary={summary} />
        <RecentConnectionsList connections={summary.recentConnections} onOpenGraph={() => w.setGraphOpen(true)} onUpdateStatus={updateConnectionStatus} />
        <RecentActivityTimeline activity={summary.recentActivity} completed={summary.recentlyCompleted} />

        <div className="mt-8 flex flex-wrap gap-2">
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={() => w.setGraphOpen(true)}>Ver grafo</button>
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={() => w.setMonitorOpen(true)}>Monitor</button>
          <button className="h-9 rounded-xl bg-surface px-3 text-xs font-medium text-muted hover:bg-border/50" onClick={w.scanVault}>Scan vault</button>
        </div>
      </div>
    </div>
  );
}

function HomeHeader({ summary, nome, onGraph }: { summary: HomeSummary; nome: string; onGraph: () => void }) {
  return (
    <header className="mb-8">
      <h1 className="text-lg font-semibold tracking-tight">Bom estudo, {nome}.</h1>
      <p className="mt-1 text-sm text-muted/60">Continue escrevendo. O BerryBrain organiza, conecta e assimila automaticamente.</p>
      <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] text-muted/55">
        <StatusBadge label={`Worker ${summary.status.worker}`} status={summary.status.worker === "running" ? "ok" : "bad"} />
        <StatusBadge label={`Ollama ${summary.status.ollama}`} status={summary.status.ollama === "online" ? "ok" : "bad"} />
        <StatusBadge label={`Cloud: ${providerLabel(summary.status.cloudProvider)}${summary.status.cloudModel ? ` · ${summary.status.cloudModel}` : ""}`} status={summary.status.cloudProvider === "local" ? "muted" : "ok"} />
        <span>{summary.status.activeJobs} ativos · {summary.status.pendingJobs} na fila</span>
        {summary.status.lastProcessingAt && <span>Último processamento {formatTime(summary.status.lastProcessingAt)}</span>}
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        <HeaderLink onClick={() => (window.location.href = "/activity")}>Ver atividade</HeaderLink>
        <HeaderLink onClick={() => (window.location.href = "/insights")}>Ver insights</HeaderLink>
        <HeaderLink onClick={onGraph}>Ver grafo</HeaderLink>
      </div>
    </header>
  );
}

function AutopilotProgressCard({ summary, status, onOpenMonitor }: { summary: HomeSummary; status: StatusKind; onOpenMonitor: () => void }) {
  const running = status === "running";
  const waiting = status === "waiting_provider" || status === "queued";
  return (
    <button className="w-full rounded-2xl bg-surface p-5 text-left ring-1 ring-border/40 transition hover:ring-accent/30" onClick={onOpenMonitor}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">{status === "completed" ? "Autopilot em dia" : "Autopilot processando"}</div>
          <p className="mt-1 text-xs text-muted/60">
            {summary.progress.active} ativos · {summary.progress.pending} na fila · {summary.progress.percent}% concluído
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
        <div><span className="text-muted/45">Etapa atual:</span> {summary.progress.currentStep}</div>
        <div><span className="text-muted/45">Último resultado:</span> {summary.progress.lastResult}</div>
      </div>
      {running && <div className="mt-3 text-[11px] text-muted/45">Clique para abrir detalhes dos jobs ativos.</div>}
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
    <Section title="Insights da IA">
      {insights.length === 0 ? (
        <EmptyState title="Nenhum insight ainda." text="Continue escrevendo para o BerryBrain detectar padrões." />
      ) : (
        <div className="space-y-2">
          {insights.slice(0, 4).map((insight) => (
            <div key={insight.id} className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-medium uppercase text-accent">{insightTypeLabel(insight.type)}</span>
                {insight.priority > 0 && <span className="text-[10px] text-muted/40">prioridade {insight.priority}</span>}
                <span className="text-[10px] text-muted/40 ml-auto">{Math.round((insight.confidence || 0) * 100)}%</span>
              </div>
              <p className="mt-1 text-xs font-medium">{insight.title}</p>
              {insight.description && <p className="mt-1 text-[11px] leading-5 text-muted/65 line-clamp-2">{insight.description}</p>}
              <div className="mt-3 flex flex-wrap gap-2 text-[11px]">
                <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-foreground" onClick={() => window.location.href = "/insights"}>Ver detalhes</button>
                <button className="rounded-lg bg-panel px-2.5 py-1 text-emerald-600 hover:text-emerald-700" onClick={() => dismissInsight(insight.id, "dismiss")}>Aplicar</button>
                <button className="rounded-lg bg-panel px-2.5 py-1 text-muted hover:text-red-500" onClick={() => dismissInsight(insight.id, "ignore")}>Ignorar</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}

function ActiveJobsPanel({ jobs, onOpenMonitor }: { jobs: ActiveJob[]; onOpenMonitor: () => void }) {
  return (
    <Section title="Processando agora">
      {jobs.length === 0 ? (
        <EmptyState title="Tudo pronto." text="Nenhuma tarefa ativa no momento." />
      ) : (
        <div className="space-y-2">
          {jobs.slice(0, 5).map((job) => (
            <button key={job.id} className="w-full rounded-xl bg-surface p-3 text-left ring-1 ring-border/35 hover:ring-accent/30" onClick={onOpenMonitor}>
              <div className="flex items-center justify-between gap-2">
                <span className="text-xs font-medium">{job.label}</span>
                <span className="text-[10px] text-muted/45">{formatElapsed(job.elapsedSeconds || 0)}</span>
              </div>
              <p className="mt-1 truncate text-[11px] text-muted/60">{job.noteTitle || job.notePath || "Sistema"}</p>
              <p className="mt-1 text-[10px] text-muted/45">{providerLabel(job.provider || "")}{job.model ? ` · ${job.model}` : ""}</p>
            </button>
          ))}
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
      onToast("Expansao do grafo iniciada.", "success");
    } catch {
      onToast("Erro ao expandir grafo.", "error");
    }
  };
  return (
    <Section title="Grafo de conhecimento">
      <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
        <div className="text-sm font-semibold">{graph.nodes} nós · {graph.edges} conexões</div>
        <p className="mt-1 text-xs text-muted/60">{graph.orphans} órfãs · {graph.clusters} clusters</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={onOpenGraph}>Abrir grafo</button>
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={() => { if (typeof window !== "undefined") localStorage.setItem("bb_graph_filter_orphans", "1"); onOpenGraph(); }}>Ver órfãs</button>
          <button className="rounded-lg bg-panel px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={recalcular}>Recalcular conexões</button>
        </div>
      </div>
    </Section>
  );
}

function NeedsAttentionCard({ items, onOpenMonitor }: { items: AttentionItem[]; onOpenMonitor: () => void }) {
  if (items.length === 0) {
    return (
      <Section title="Precisa de atenção">
        <div className="rounded-xl bg-surface p-4 text-xs text-muted/60 ring-1 ring-border/35">Tudo certo.</div>
      </Section>
    );
  }
  return (
    <Section title="Precisa de atenção">
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
    <Section title="Estatísticas" className="mt-8">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        <StatCard label="Notas" value={s.notes.total} detail={`+${s.notes.createdToday} hoje · ${s.notes.unassimilated} não assimiladas`} />
        <StatCard label="Conexões" value={s.connections.total} detail={`${s.connections.createdToday} novas · ${percent(s.connections.averageConfidence)} confiança`} />
        <StatCard label="Conceitos" value={s.concepts.total} detail={`${s.concepts.newToday} novos · ${s.concepts.withoutPermanentNote} sem nota`} />
        <StatCard label="Jobs" value={s.jobs.pending} detail={`${s.jobs.active} ativos · ${s.jobs.failed} erros`} />
        <StatCard label={providerLabel(s.ai.provider)} value={s.ai.model ? "Online" : "Local"} detail={`${s.ai.embeddings} embeddings · ${s.ai.metadata} metadados`} />
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
    <Section title="Conexões recentes" className="mt-8">
      {connections.length === 0 ? (
        <EmptyState title="Nenhuma conexão encontrada ainda." text="O Autopilot criará relações conforme assimilar suas notas." />
      ) : (
        <div className="space-y-2">
          {connections.slice(0, 5).map((connection) => (
            <div key={connection.id} className="rounded-xl bg-surface p-4 ring-1 ring-border/35">
              <div className="text-xs font-medium">
                {connection.source?.title || "Origem"} ↔ {connection.target?.title || "Destino"}
              </div>
              <p className="mt-1 text-[11px] leading-5 text-muted/65">{connection.reason || "Conexão sem motivo registrado."}</p>
              <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-muted/55">
                <span>Confiança: {connection.confidencePercent}%</span>
                <span className="rounded-full bg-panel px-2 py-1">{connection.status || "suggested"}</span>
                <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={onOpenGraph}>Ver no grafo</button>
                {connection.status !== "confirmed" && (
                  <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={() => onUpdateStatus(connection.id, "confirm")}>Confirmar</button>
                )}
                {connection.status !== "ignored" && (
                  <button className="rounded-lg bg-panel px-2.5 py-1 hover:text-foreground" onClick={() => onUpdateStatus(connection.id, "ignore")}>Ignorar</button>
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
    <Section title="Atividade recente" className="mt-8">
      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">Pronto recentemente</div>
          {completed.length === 0 ? <p className="text-xs text-muted/50">Nenhum resultado concluído recentemente.</p> : completed.slice(0, 5).map((item) => (
            <RowLine key={item.id} left={item.label} right={formatTime(item.completedAt)} />
          ))}
        </div>
        <div className="rounded-2xl bg-surface p-4 ring-1 ring-border/35">
          <div className="mb-2 text-[10px] font-medium uppercase tracking-[0.12em] text-muted/40">Fila automática</div>
          {activity.length === 0 ? <p className="text-xs text-muted/50">Nenhuma atividade recente.</p> : activity.slice(0, 5).map((item, index) => (
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

function HeaderLink({ children, onClick }: { children: ReactNode; onClick: () => void }) {
  return <button className="rounded-lg bg-surface px-2.5 py-1 text-[11px] text-muted hover:text-foreground" onClick={onClick}>{children}</button>;
}

function normalizeStatus(status: string): StatusKind {
  if (status === "failed" || status === "offline" || status === "queued" || status === "waiting_provider" || status === "completed") return status;
  return "running";
}

function providerLabel(provider: string) {
  if (provider === "nvidia-nim") return "NVIDIA NIM";
  if (provider === "cloud") return "Cloud";
  if (provider === "local") return "Local";
  return provider || "IA";
}

function insightTypeLabel(type: string) {
  return {
    context: "Contexto",
    conclusion: "Conclusão",
    hypothesis: "Hipótese",
    premise: "Premissa",
    assertion: "Afirmação",
    knowledge_gap: "Lacuna",
    new_connection: "Nova conexão",
    study_path: "Trilha de estudo",
    possible_contradiction: "Possível contradição",
    deepening_opportunity: "Aprofundamento",
    recurring_concept: "Conceito recorrente",
    review_opportunity: "Revisão sugerida",
    permanent_note_candidate: "Nota permanente",
    emerging_context: "Contexto emergente",
    isolated_note: "Nota isolada",
    isolated_concept: "Conceito isolado",
    weak_note: "Nota a fortalecer",
    duplicate_content: "Duplicidade",
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
