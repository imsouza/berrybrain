"use client";

import { useEffect, useMemo, useState } from "react";
import { GraphCanvas, useGraphData, type GraphLayoutMode } from "./graph-view";

const EDGE_COLORS: Record<string, string> = {
  semantic: "#D98A00",
  semantic_similarity: "#D98A00",
  shared_concept: "#C2185B",
  shared_context: "#8B6F9F",
  backlink: "#3C8F5A",
  prerequisite: "#3C8F5A",
  related: "#6B4A2D",
  duplicate: "#B85C4A",
  contrast: "#8B6F9F",
  example: "#4A8F6A",
  application: "#9F6B4A",
  default: "#B89B82",
};

type GraphNode = {
  id: string;
  recordId?: number;
  type: string;
  label: string;
  title?: string;
  summary?: string;
  path?: string;
  folder?: string;
  status?: string;
  sourceId?: number;
  confidence?: number;
  createdBy?: string;
  createdByModel?: string;
};

type GraphEdge = {
  id?: number;
  source: string;
  target: string;
  type: string;
  label?: string;
  confidence?: number;
  reason?: string;
  evidence?: string[];
  status?: string;
  provider?: string;
  model?: string;
};

type InferenceResult = {
  status: "answered" | "insufficient_evidence" | string;
  question: string;
  answer: string;
  relatedNodes?: string[];
  connections?: { id?: number; type: string; reason: string; confidence?: number }[];
  evidence?: string[];
  actions?: string[];
  provider?: string;
  model?: string;
};

type NodeSummary = {
  id: number;
  type: string;
  label: string;
  title: string;
  summary: string;
  source: string;
  sourceNoteIds: number[];
  confidence: number;
  createdBy: string;
  createdByModel: string;
  status: string;
  aiNotes?: string;
  userNotes?: string;
  notes: { id: number; title: string; path: string }[];
  connections: {
    id: number;
    type: string;
    label?: string;
    reason: string;
    evidence: string[];
    confidence: number;
    status: string;
    provider?: string;
    model?: string;
    aiNotes?: string;
    userNotes?: string;
  }[];
  whyThisExists: string;
};

export function GraphScreen({
  apiUrl,
  onClose,
  onNavigate,
}: {
  apiUrl: string;
  onClose: () => void;
  onNavigate: (path: string) => void;
}) {
  const { data, error, reload } = useGraphData(apiUrl);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [showDetail, setShowDetail] = useState(false);
  const [query, setQuery] = useState("");
  const [filterType, setFilterType] = useState("brain_view");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterConfidence, setFilterConfidence] = useState(0);
  const [showCognitivos, setShowCognitivos] = useState(false);
  const [layoutMode, setLayoutMode] = useState<GraphLayoutMode>(() => {
    if (typeof window === "undefined") return "brain";
    const saved = localStorage.getItem("bb_graph_layout");
    if (saved === "default") return "brain";
    return (saved as GraphLayoutMode) || "brain";
  });
  const [inference, setInference] = useState<InferenceResult | null>(null);
  const [inferLoading, setInferLoading] = useState(false);
  const [nodeSummary, setNodeSummary] = useState<NodeSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [manualNotes, setManualNotes] = useState("");

  const graphData = data as { nodes: GraphNode[]; edges: GraphEdge[]; stats?: any } | null;

  const filtered = useMemo(() => {
    const orphanFilter = typeof window !== "undefined" ? localStorage.getItem("bb_graph_filter_orphans") : null;
    if (orphanFilter) localStorage.removeItem("bb_graph_filter_orphans");
    if (!graphData) return { nodes: [], edges: [] };
    let nodes = graphData.nodes;
    let edges = graphData.edges;
    if (filterType === "brain_view") {
      const base = ["note", "concept", "topico", "entidade"];
      const cognitivos = showCognitivos ? ["contexto", "lacuna", "insight", "context"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitivos].includes(n.type));
    } else if (filterType === "topicos") {
      nodes = nodes.filter((n) => n.type === "topico");
    } else if (filterType !== "all") {
      nodes = nodes.filter((n) => n.type === filterType);
    } else if (layoutMode === "brain") {
      const base = ["note", "concept", "topico", "entidade"];
      const cognitivos = showCognitivos ? ["contexto", "lacuna", "insight", "context"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitivos].includes(n.type));
    }
    if (filterStatus !== "all") nodes = nodes.filter((n) => (n.status || "suggested") === filterStatus);
    else nodes = nodes.filter((n) => (n.status || "suggested") !== "ignored");
    if (filterProvider !== "all") nodes = nodes.filter((n) => {
      const p = (n.createdBy || "system").toLowerCase();
      if (filterProvider === "ai") return p === "ai" || p.startsWith("subagent");
      if (filterProvider === "deterministic") return p === "system" || p === "deterministic" || p === "backlink" || p === "metadata-parser";
      return p === filterProvider;
    });
    if (filterConfidence > 0) nodes = nodes.filter((n) => (n.confidence || 0) >= filterConfidence / 100);
    if (orphanFilter === "1") {
      const degree = new Map<string, number>();
      for (const n of graphData.nodes) degree.set(n.id, 0);
      for (const e of graphData.edges) {
        degree.set(e.source, (degree.get(e.source) || 0) + 1);
        degree.set(e.target, (degree.get(e.target) || 0) + 1);
      }
      nodes = nodes.filter((n) => (degree.get(n.id) || 0) === 0);
    }
    const nids = new Set(nodes.map((n) => n.id));
    edges = edges.filter((e) => nids.has(e.source) && nids.has(e.target));
    return { nodes, edges };
  }, [graphData, filterType, filterStatus, filterProvider, filterConfidence, layoutMode]);

  const selectedNode = selectedId
    ? graphData?.nodes.find((n) => n.id === selectedId) ?? null
    : null;
  const selectedEdges = selectedId
    ? graphData?.edges.filter((e) => e.source === selectedId || e.target === selectedId) ?? []
    : [];

  function changeLayout(mode: GraphLayoutMode) {
    setLayoutMode(mode);
    if (typeof window !== "undefined") localStorage.setItem("bb_graph_layout", mode);
    setPan({ x: 0, y: 0 });
    setZoom(1);
  }

  useEffect(() => {
    fetch(`${apiUrl}/api/v1/settings/graph/config`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((config) => {
        const mode = config.default_layout as GraphLayoutMode;
        if (!mode || typeof window === "undefined" || localStorage.getItem("bb_graph_layout")) return;
        setLayoutMode(mode);
      })
      .catch(() => {});
  }, [apiUrl]);

  useEffect(() => {
    if (!selectedNode?.recordId || !showDetail) {
      setNodeSummary(null);
      return;
    }
    let cancelled = false;
    setSummaryLoading(true);
    fetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/summary`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((payload) => {
        if (!cancelled) {
          setNodeSummary(payload);
          setManualNotes(payload.userNotes || "");
        }
      })
      .catch(() => {
        if (!cancelled) setNodeSummary(null);
      })
      .finally(() => {
        if (!cancelled) setSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiUrl, selectedNode?.recordId, showDetail]);

  function centerNode(id: string) {
    setSelectedId(id);
    setShowDetail(true);
  }

  async function expandGraph() {
    await fetch(`${apiUrl}/api/v1/graph/expand`, { method: "POST" });
    reload();
  }

  async function runInference() {
    const text = query.trim();
    if (!text) return;
    const found = graphData?.nodes.find((n) =>
      n.label.toLowerCase().includes(text.toLowerCase()),
    );
    if (found && text.split(/\s+/).length <= 3) {
      centerNode(found.id);
      return;
    }
    setInferLoading(true);
    setInference(null);
    try {
      const response = await fetch(`${apiUrl}/api/v1/graph/infer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      setInference(await response.json());
    } catch {
      setInference({
        status: "error",
        question: text,
        answer: "Nao foi possivel consultar o grafo agora.",
      });
    } finally {
      setInferLoading(false);
    }
  }

  async function saveInferenceAsInsight() {
    const text = query.trim();
    if (!text) return;
    const response = await fetch(`${apiUrl}/api/v1/insights/from-inference`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
    });
    const payload = await response.json();
    if (payload.status === "created") {
      setInference((current) => current ? { ...current, status: "saved_as_insight" } : current);
    }
  }

  async function createPermanentConceptNote() {
    if (!selectedNode?.sourceId || selectedNode.type !== "concept") return;
    const response = await fetch(`${apiUrl}/api/v1/concepts/${selectedNode.sourceId}/create-note`, { method: "POST" });
    const payload = await response.json();
    if (payload.note?.path) {
      onNavigate(payload.note.path);
    }
  }

  async function saveManualNodeNotes() {
    if (!selectedNode?.recordId) return;
    const response = await fetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/notes`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: manualNotes }),
    });
    if (!response.ok) return;
    setNodeSummary((current) => current ? { ...current, userNotes: manualNotes } : current);
  }

  async function updateNodeStatus(status: "confirmed" | "ignored") {
    if (!selectedNode?.recordId) return;
    const action = status === "confirmed" ? "confirm" : "ignore";
    const response = await fetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/${action}`, { method: "POST" });
    if (!response.ok) return;
    setNodeSummary((current) => current ? { ...current, status } : current);
    if (status === "ignored") {
      setSelectedId(null);
      setShowDetail(false);
    }
    reload();
  }

  async function updateEdgeStatus(edgeId: number, status: "confirmed" | "ignored") {
    const action = status === "confirmed" ? "confirm" : "ignore";
    const response = await fetch(`${apiUrl}/api/v1/graph/connections/${edgeId}/${action}`, { method: "POST" });
    if (!response.ok) return;
    setNodeSummary((current) => current ? {
      ...current,
      connections: status === "ignored"
        ? current.connections.filter((connection) => connection.id !== edgeId)
        : current.connections.map((connection) => connection.id === edgeId ? { ...connection, status } : connection),
    } : current);
    reload();
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-2 border-b border-border/50 bg-panel shrink-0 text-xs">
        <button className="rounded-lg p-1.5 text-muted hover:bg-surface shrink-0" onClick={onClose}>
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        </button>
        <div className="min-w-0">
          <h2 className="text-sm font-medium text-foreground">Grafo de conhecimento</h2>
          {graphData && (
            <div className="text-[10px] text-muted/60">
              {graphData.nodes.length} nos · {graphData.edges.length} conexoes · {graphData.stats?.orphan_count ?? 0} orfas
            </div>
          )}
        </div>
        <div className="flex-1" />
        <div className="flex min-w-[280px] max-w-[520px] flex-1 items-center gap-1">
          <input
            type="text"
            className="h-8 min-w-0 flex-1 rounded-lg border border-border/50 bg-surface px-3 text-[11px] outline-none focus:border-accent"
            placeholder="Busque ou pergunte ao seu grafo..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") runInference();
            }}
          />
          <button className="h-8 rounded-lg bg-accent px-3 text-[11px] text-white disabled:opacity-50" disabled={inferLoading} onClick={runInference}>
            {inferLoading ? "..." : "Perguntar"}
          </button>
        </div>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="brain_view">Brain View (tudo)</option>
          <option value="topicos">Topicos</option>
          <option value="note">Notas</option>
          <option value="concept">Conceitos</option>
          <option value="entidade">Entidades</option>
          <option value="contexto">Contextos</option>
          <option value="insight">Insights</option>
          <option value="lacuna">Lacunas</option>
          <option value="anexo">Anexos</option>
          <option value="trilha">Trilhas</option>
          <option value="cluster">Clusters</option>
          <option value="fonte">Fontes</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="all">Status</option>
          <option value="suggested">Sugerido</option>
          <option value="confirmed">Confirmado</option>
          <option value="ignored">Ignorado</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterProvider} onChange={(e) => setFilterProvider(e.target.value)}>
          <option value="all">Origem</option>
          <option value="ai">IA</option>
          <option value="deterministic">Sistema</option>
          <option value="backlink">Backlink</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterConfidence.toString()} onChange={(e) => setFilterConfidence(Number(e.target.value))}>
          <option value="0">Confianca</option>
          <option value="90">90%+</option>
          <option value="70">70%+</option>
          <option value="50">50%+</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={layoutMode} onChange={(e) => changeLayout(e.target.value as GraphLayoutMode)}>
          <option value="brain">Brain View padrão</option>
          <option value="radial">Radial</option>
          <option value="type">Por tipo</option>
          <option value="connections">Centralidade</option>
        </select>
        <button className="h-8 rounded-lg bg-surface px-2.5 text-[11px] text-muted hover:text-foreground" onClick={() => { setPan({ x: 0, y: 0 }); setZoom(1); setSelectedId(null); }}>Centralizar</button>
        <button className="h-8 rounded-lg bg-surface px-2.5 text-[11px] text-muted hover:text-foreground" onClick={expandGraph}>Expandir</button>
        <button className={`h-8 rounded-lg px-2.5 text-[11px] ${showLegend ? "bg-accent text-white" : "bg-surface text-muted hover:text-foreground"}`} onClick={() => setShowLegend(!showLegend)}>Legenda</button>
        <button className={`h-8 rounded-lg px-2.5 text-[11px] ${showCognitivos ? "bg-accent text-white" : "bg-surface text-muted hover:text-foreground"}`} onClick={() => setShowCognitivos(!showCognitivos)}>Nós cognitivos</button>
      </div>

      {inference && (
        <div className="border-b border-border/40 bg-panel/80 px-4 py-3">
          <div className="mx-auto max-w-5xl rounded-xl border border-border/50 bg-surface/70 p-3">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-accent">Inferencia do grafo</span>
              <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
            </div>
            <p className="text-sm text-foreground">{inference.answer}</p>
            {!!inference.relatedNodes?.length && (
              <div className="mt-2 flex flex-wrap gap-1">
                {inference.relatedNodes.map((node) => (
                  <button
                    key={node}
                    className="rounded-full bg-panel px-2 py-1 text-[10px] text-muted hover:text-foreground"
                    onClick={() => {
                      const found = graphData?.nodes.find((n) => n.label === node);
                      if (found) centerNode(found.id);
                    }}
                  >
                    {node}
                  </button>
                ))}
              </div>
            )}
            {!!inference.evidence?.length && (
              <div className="mt-2 text-[11px] text-muted">
                Evidencias: {inference.evidence.slice(0, 3).join(" · ")}
              </div>
            )}
            {(inference.provider || inference.model) && (
              <div className="mt-1 text-[10px] text-muted/60">
                IA: {inference.provider || "provider"} {inference.model ? `· ${inference.model}` : ""}
              </div>
            )}
            <div className="mt-2 flex flex-wrap gap-1">
              {inference.status === "answered" && (
                <button className="rounded-lg bg-accent px-3 py-1 text-[10px] text-white" onClick={saveInferenceAsInsight}>Salvar como insight</button>
              )}
              <button className="rounded-lg bg-panel px-3 py-1 text-[10px] text-muted hover:text-foreground" onClick={() => setInference(null)}>Fechar</button>
            </div>
          </div>
        </div>
      )}

      <div className="relative flex-1 overflow-hidden bg-[#FBF4EC]">
        {error ? (
          <div className="flex h-full items-center justify-center text-sm text-muted">Erro ao carregar grafo.</div>
        ) : graphData ? (
          <GraphCanvas
            data={filtered}
            onNavigate={(path) => {
              onClose();
              setTimeout(() => onNavigate(path), 100);
            }}
            onSelect={(id) => {
              setSelectedId(id);
              setShowDetail(Boolean(id));
            }}
            selectedId={selectedId}
            zoom={zoom}
            setZoom={setZoom}
            pan={pan}
            setPan={setPan}
            layoutMode={layoutMode}
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">Carregando grafo...</div>
        )}

        <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-1">
          <button className="size-8 rounded-lg bg-panel/90 backdrop-blur flex items-center justify-center text-muted hover:text-foreground shadow-sm ring-1 ring-border/30 text-xs" onClick={() => setZoom((z) => Math.min(3, z * 1.3))}>+</button>
          <button className="size-8 rounded-lg bg-panel/90 backdrop-blur flex items-center justify-center text-muted hover:text-foreground shadow-sm ring-1 ring-border/30 text-xs" onClick={() => setZoom((z) => Math.max(0.2, z / 1.3))}>-</button>
        </div>

        {showLegend && (
          <div className="absolute top-3 right-4 z-20 w-56 rounded-xl bg-panel/95 backdrop-blur shadow-lg ring-1 ring-border/30 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[11px] font-medium text-foreground">Legenda</span>
              <button className="text-[10px] text-muted hover:text-foreground" onClick={() => setShowLegend(false)}>X</button>
            </div>
            <div className="space-y-1 text-[10px]">
              {[
                ["note", "#C2185B"],
                ["concept", "#D98A00"],
                ["topico", "#96B55C"],
                ["entidade", "#2E9D68"],
                ["contexto/insight", "#8B6F9F"],
                ["lacuna", "#B85C4A"],
              ].map(([k, v]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="inline-block size-2.5 rounded-full" style={{ background: v }} />
                  <span className="text-muted/70">{k}</span>
                </div>
              ))}
              <div className="my-2 h-px bg-border/40" />
              {Object.entries(EDGE_COLORS).filter(([k]) => k !== "default").map(([k, v]) => (
                <div key={k} className="flex items-center gap-2">
                  <span className="inline-block h-0.5 w-4 rounded" style={{ background: v }} />
                  <span className="text-muted/70">{k}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {selectedNode && showDetail && (
        <div className="absolute right-0 top-[49px] bottom-0 z-30 w-[360px] border-l border-border/50 bg-panel/98 backdrop-blur overflow-y-auto p-4 shadow-lg">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-accent">{selectedNode.type}</div>
              <h3 className="truncate text-sm font-medium text-foreground">{nodeSummary?.title || selectedNode.label}</h3>
            </div>
            <button className="text-[10px] text-muted hover:text-foreground" onClick={() => setShowDetail(false)}>X</button>
          </div>

          {summaryLoading ? (
            <div className="text-xs text-muted">Carregando resumo do no...</div>
          ) : (
            <div className="space-y-3 text-[11px] text-muted/75">
              <p className="rounded-lg bg-surface p-3 text-foreground/80">
                {nodeSummary?.summary || selectedNode.summary || "Resumo ainda nao gerado para este no."}
              </p>
              <div>{nodeSummary?.whyThisExists || "Este no vem dos dados reais do grafo."}</div>
              <div className="grid grid-cols-2 gap-2">
                <Meta label="Status" value={nodeSummary?.status || selectedNode.status || "-"} />
                <Meta label="Confianca" value={formatConfidence(nodeSummary?.confidence ?? selectedNode.confidence)} />
                <Meta label="Origem" value={nodeSummary?.createdBy || selectedNode.createdBy || "-"} />
                <Meta label="Modelo" value={nodeSummary?.createdByModel || selectedNode.createdByModel || "-"} />
              </div>

              <section className="border-t border-border/30 pt-3">
                <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Notas do grafo</div>
                {nodeSummary?.aiNotes && (
                  <p className="mb-2 rounded-lg bg-surface p-2 text-[10px] text-muted/70">IA/subagent: {nodeSummary.aiNotes}</p>
                )}
                <textarea
                  className="min-h-20 w-full resize-none rounded-lg border border-border bg-surface p-2 text-[11px] text-foreground outline-none focus:border-accent"
                  placeholder="Adicione uma nota manual para complementar a IA..."
                  value={manualNotes}
                  onChange={(event) => setManualNotes(event.target.value)}
                />
                <button className="mt-2 rounded-lg bg-accent px-3 py-1.5 text-[10px] text-white" onClick={saveManualNodeNotes}>Salvar nota manual</button>
              </section>

              {!!nodeSummary?.notes?.length && (
                <section className="border-t border-border/30 pt-3">
                  <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Notas de origem</div>
                  <div className="space-y-1">
                    {nodeSummary.notes.slice(0, 5).map((note) => (
                      <button key={note.id} className="block w-full truncate rounded-lg bg-surface px-2 py-1.5 text-left text-[11px] text-muted hover:text-foreground" onClick={() => onNavigate(note.path)}>
                        {note.title}
                      </button>
                    ))}
                  </div>
                </section>
              )}

              <section className="border-t border-border/30 pt-3">
                <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Conexoes explicadas</div>
                <div className="space-y-2">
                  {(nodeSummary?.connections?.length ? nodeSummary.connections : selectedEdges).slice(0, 6).map((edge, index) => {
                    const simpleEdge = edge as GraphEdge;
                    const detailedEdge = edge as NodeSummary["connections"][number];
                    const other = simpleEdge.source === selectedId ? simpleEdge.target : simpleEdge.source;
                    const otherNode = graphData?.nodes.find((n) => n.id === other);
                    return (
                      <div key={`${detailedEdge.id || simpleEdge.id || index}`} className="rounded-lg bg-surface p-2">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="inline-block h-0.5 w-4 rounded" style={{ background: EDGE_COLORS[detailedEdge.type || simpleEdge.type] || EDGE_COLORS.default }} />
                          <span className="truncate text-[11px] font-medium text-foreground">{otherNode?.label || detailedEdge.label || simpleEdge.type}</span>
                        </div>
                        {(detailedEdge.reason || simpleEdge.reason) && <p>{detailedEdge.reason || simpleEdge.reason}</p>}
                        {!!(detailedEdge.evidence || simpleEdge.evidence)?.length && (
                          <div className="mt-1 text-[10px] text-muted/60">Evidencia: {(detailedEdge.evidence || simpleEdge.evidence || []).slice(0, 2).join(" · ")}</div>
                        )}
                        <div className="mt-2 flex flex-wrap items-center gap-1">
                          <span className="rounded-full bg-panel px-2 py-0.5 text-[9px] text-muted/60">{detailedEdge.status || simpleEdge.status || "suggested"}</span>
                          {!!detailedEdge.id && detailedEdge.status !== "confirmed" && (
                            <button className="rounded-md bg-accent px-2 py-0.5 text-[9px] text-white" onClick={() => updateEdgeStatus(detailedEdge.id, "confirmed")}>Confirmar</button>
                          )}
                          {!!detailedEdge.id && detailedEdge.status !== "ignored" && (
                            <button className="rounded-md bg-panel px-2 py-0.5 text-[9px] text-muted hover:text-foreground" onClick={() => updateEdgeStatus(detailedEdge.id, "ignored")}>Ignorar</button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              <div className="flex flex-wrap gap-1 pt-1">
                {selectedNode.path && (
                  <button className="rounded-lg bg-accent px-3 py-1.5 text-[10px] text-white" onClick={() => onNavigate(selectedNode.path!)}>Abrir nota</button>
                )}
                {selectedNode.status !== "confirmed" && (
                  <button className="rounded-lg bg-surface px-3 py-1.5 text-[10px] text-muted" onClick={() => updateNodeStatus("confirmed")}>Confirmar no</button>
                )}
                {selectedNode.status !== "ignored" && (
                  <button className="rounded-lg bg-surface px-3 py-1.5 text-[10px] text-muted" onClick={() => updateNodeStatus("ignored")}>Ignorar no</button>
                )}
                <button className="rounded-lg bg-surface px-3 py-1.5 text-[10px] text-muted" onClick={expandGraph}>Reprocessar grafo</button>
                {selectedNode.type === "concept" && selectedNode.sourceId && (
                  <button className="rounded-lg bg-surface px-3 py-1.5 text-[10px] text-muted" onClick={createPermanentConceptNote}>Criar nota permanente</button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface px-2 py-1.5">
      <div className="text-[9px] uppercase tracking-wide text-muted/60">{label}</div>
      <div className="truncate text-[11px] text-foreground/80">{value}</div>
    </div>
  );
}

function formatConfidence(value?: number) {
  if (value === undefined || value === null) return "-";
  return `${Math.round(value <= 1 ? value * 100 : value)}%`;
}
