"use client";

import { useEffect, useMemo, useState } from "react";
import { GraphCanvas, useGraphData, type GraphLayoutMode } from "./graph-view";
import { t } from "@/i18n";
import { apiFetch, appPath } from "@/contexts/workspace-context";
import { askBrowserNvidia } from "@/lib/browser-ai";
import { saveBrowserInferenceInsight } from "@/lib/browser-storage";

const EDGE_COLORS: Record<string, string> = {
  explicit_link: "#3C8F5A",
  semantic_relation: "#D98A00",
  derived_from: "#4F7CCB",
  mentions: "#96B55C",
  supports: "#4A8F6A",
  contradicts: "#B85C4A",
  contrasts_with: "#8B6F9F",
  duplicates: "#B85C4A",
  example_of: "#4A8F6A",
  applies_to: "#9F6B4A",
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
  aiContext?: string;
  aiSummary?: string;
  sourceEvidence?: string;
  learningValue?: string;
  sourceQuality?: string;
  validationStatus?: string;
  provider?: string;
  model?: string;
};

type GraphEdge = {
  id?: number | string;
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
  status: "answered" | "success" | "sufficient_evidence" | "insufficient_evidence" | string;
  question: string;
  answer: string;
  relatedNodes?: Array<string | { id?: number | string; title?: string; label?: string; type?: string; path?: string }>;
  connections?: { id?: number; type: string; reason: string; confidence?: number }[];
  evidence?: Array<string | { source?: string; title?: string; text?: string; reference?: string; data?: unknown; metadata?: Record<string, unknown> }>;
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
  aiContext?: string;
  aiSummary?: string;
  sourceEvidence?: string;
  learningValue?: string;
  sourceQuality?: string;
  validationStatus?: string;
  provider?: string;
  model?: string;
  promptVersion?: string;
  generatedAt?: string | null;
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

type GraphActionId =
  | "confirm-node"
  | "ignore-node"
  | "reprocess-node"
  | "enrich-node-ai"
  | "validate-node-web";

type GraphAction = {
  id: GraphActionId;
  label: string;
  variant: "primary" | "secondary" | "danger";
  visible: boolean;
  disabled: boolean;
  requiresConfirmation: boolean;
  reasonDisabled?: string;
};

function getAvailableGraphActions(
  item: GraphNode | null,
  options: { researchModeEnabled: boolean },
): GraphAction[] {
  if (!item) return [];
  const status = item.status || "suggested";
  return [
    {
      id: "confirm-node",
      label: item.type === "insight" ? "Apply Insight" : "Confirm Node",
      variant: "primary",
      visible: status === "suggested",
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "ignore-node",
      label: item.type === "insight" ? "Ignore Insight" : "Ignore Node",
      variant: "secondary",
      visible: status === "suggested",
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "reprocess-node",
      label: "Reprocess node",
      variant: "secondary",
      visible: true,
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "enrich-node-ai",
      label: "Enrich with AI",
      variant: "secondary",
      visible: true,
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "validate-node-web",
      label: "Validate with web",
      variant: "secondary",
      visible: options.researchModeEnabled,
      disabled: !options.researchModeEnabled,
      requiresConfirmation: true,
      reasonDisabled: "Research Mode is disabled in Settings.",
    },
  ];
}

function relatedNodeLabel(item: NonNullable<InferenceResult["relatedNodes"]>[number]): string {
  if (typeof item === "string") return item;
  return item.title || item.label || String(item.id || "Related node");
}

function resolveRelatedInferenceNodes(
  inference: InferenceResult | null,
  graphData: { nodes: GraphNode[]; edges: GraphEdge[]; stats?: any } | null,
): Array<{ id: string; label: string }> {
  if (!inference?.relatedNodes?.length || !graphData) return [];
  const resolved = new Map<string, { id: string; label: string }>();
  for (const item of inference.relatedNodes) {
    const label = relatedNodeLabel(item);
    const objectId = typeof item === "object" ? item.id : undefined;
    const objectType = typeof item === "object" ? item.type : undefined;
    const objectPath = typeof item === "object" ? item.path : undefined;
    const found = graphData.nodes.find((node) => {
      if (objectId && node.recordId === Number(objectId)) return true;
      if (objectId && node.sourceId === Number(objectId)) return true;
      if (objectId && objectType && node.id === `${objectType}_${objectId}`) return true;
      if (objectPath && node.path === objectPath) return true;
      return node.label === label || node.title === label;
    });
    if (found) resolved.set(found.id, { id: found.id, label: found.label });
  }
  return [...resolved.values()];
}

function formatInferenceEvidence(
  item: NonNullable<InferenceResult["evidence"]>[number],
): string {
  return formatEvidenceLabel(item);
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
  const parts = [
    record.title || record.label || record.source || "",
    record.text || record.reference || record.path || record.reason || "",
    record.whyRelevant || record.quoteOrSummary || "",
  ].filter(Boolean);
  return parts.join(": ") || "Evidence available in technical details.";
}

function GraphListView({
  data,
  selectedId,
  onSelect,
}: {
  data: { nodes: GraphNode[]; edges: GraphEdge[] };
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  const nodeById = new Map(data.nodes.map((node) => [node.id, node]));
  const degree = new Map(data.nodes.map((node) => [node.id, 0]));
  for (const edge of data.edges) {
    degree.set(edge.source, (degree.get(edge.source) || 0) + 1);
    degree.set(edge.target, (degree.get(edge.target) || 0) + 1);
  }
  const nodes = [...data.nodes].sort((left, right) =>
    `${left.type}:${left.label}`.localeCompare(`${right.type}:${right.label}`),
  );

  return (
    <div className="h-full overflow-y-auto bg-background px-4 py-4" aria-label="Knowledge graph list view">
      <div className="mx-auto grid max-w-6xl gap-6 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)]">
        <section aria-labelledby="graph-list-nodes">
          <h2 id="graph-list-nodes" className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Nodes</h2>
          <div className="divide-y divide-border/50 overflow-hidden rounded-lg border border-border/60 bg-panel" role="list">
            {nodes.map((node) => (
              <button
                key={node.id}
                type="button"
                role="listitem"
                aria-current={selectedId === node.id ? "true" : undefined}
                className={`flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-surface ${selectedId === node.id ? "bg-surface" : ""}`}
                onClick={() => onSelect(node.id)}
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm text-foreground">{node.label}</span>
                  <span className="block text-[10px] uppercase text-muted">{node.type} · {node.status || "suggested"}</span>
                </span>
                <span className="text-xs tabular-nums text-muted" aria-label={`${degree.get(node.id) || 0} connections`}>
                  {degree.get(node.id) || 0}
                </span>
              </button>
            ))}
          </div>
        </section>
        <section aria-labelledby="graph-list-connections">
          <h2 id="graph-list-connections" className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Connections</h2>
          <div className="divide-y divide-border/50 overflow-hidden rounded-lg border border-border/60 bg-panel" role="list">
            {data.edges.map((edge, index) => {
              const source = nodeById.get(edge.source);
              const target = nodeById.get(edge.target);
              return (
                <button
                  key={edge.id || `${edge.source}:${edge.target}:${edge.type}:${index}`}
                  type="button"
                  role="listitem"
                  className="block w-full px-3 py-2.5 text-left hover:bg-surface"
                  onClick={() => onSelect(edge.source)}
                >
                  <span className="block text-sm text-foreground">{source?.label || edge.source} → {target?.label || edge.target}</span>
                  <span className="block text-[10px] uppercase text-muted">{edge.type} · {edge.status || "suggested"} · {Math.round((edge.confidence || 0) * 100)}%</span>
                  {edge.reason && <span className="mt-1 block text-xs text-muted">{edge.reason}</span>}
                </button>
              );
            })}
          </div>
        </section>
      </div>
    </div>
  );
}

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
  const [viewMode, setViewMode] = useState<"visual" | "list">(() => {
    if (typeof window === "undefined") return "visual";
    return localStorage.getItem("bb_graph_view_mode") === "list" ? "list" : "visual";
  });
  const [showDetail, setShowDetail] = useState(false);
  const [query, setQuery] = useState("");
  const [filterType, setFilterType] = useState("brain_view");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterConfidence, setFilterConfidence] = useState(0);
  const [showInsightNodes, setShowInsightNodes] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("bb_graph_show_insight_nodes") !== "0";
  });
  const showCognitivos = true;
  const [layoutMode, setLayoutMode] = useState<GraphLayoutMode>(() => {
    if (typeof window === "undefined") return "brain";
    const saved = localStorage.getItem("bb_graph_layout");
    if (saved === "default") return "brain";
    return (saved as GraphLayoutMode) || "brain";
  });
  const [inference, setInference] = useState<InferenceResult | null>(null);
  const [inferLoading, setInferLoading] = useState(false);
  const [inferenceSaveStatus, setInferenceSaveStatus] = useState("");
  const [inferenceSaving, setInferenceSaving] = useState(false);
  const [nodeSummary, setNodeSummary] = useState<NodeSummary | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [manualNotes, setManualNotes] = useState("");
  const [nodeActionStatus, setNodeActionStatus] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [researchModeEnabled, setResearchModeEnabled] = useState(false);

  const graphData = data as { nodes: GraphNode[]; edges: GraphEdge[]; stats?: any } | null;
  const relatedInferenceNodes = useMemo(() => resolveRelatedInferenceNodes(inference, graphData), [inference, graphData]);
  const highlightedIds = useMemo(() => relatedInferenceNodes.map((node) => node.id), [relatedInferenceNodes]);

  const filtered = useMemo(() => {
    const orphanFilter = typeof window !== "undefined" ? localStorage.getItem("bb_graph_filter_orphans") : null;
    if (orphanFilter) localStorage.removeItem("bb_graph_filter_orphans");
    if (!graphData) return { nodes: [], edges: [] };
    let nodes = graphData.nodes;
    let edges = graphData.edges;
    if (filterType === "brain_view") {
      const base = ["note", "concept", "topic", "topico", "entity", "entidade"];
      const cognitivos = showCognitivos ? ["context", "contexto", "gap", "lacuna", "insight"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitivos].includes(n.type));
    } else if (filterType === "topicos") {
      nodes = nodes.filter((n) => n.type === "topic" || n.type === "topico");
    } else if (filterType !== "all") {
      const typeAliases: Record<string, string[]> = {
        entidade: ["entity", "entidade"],
        contexto: ["context", "contexto"],
        lacuna: ["gap", "lacuna"],
        anexo: ["attachment", "anexo"],
        trilha: ["study_path", "trilha"],
        fonte: ["source", "fonte", "web_source"],
      };
      nodes = nodes.filter((n) => (typeAliases[filterType] || [filterType]).includes(n.type));
    } else if (layoutMode === "brain") {
      const base = ["note", "concept", "topic", "topico", "entity", "entidade"];
      const cognitivos = showCognitivos ? ["context", "contexto", "gap", "lacuna", "insight"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitivos].includes(n.type));
    }
    if (filterStatus !== "all") nodes = nodes.filter((n) => (n.status || "suggested") === filterStatus);
    else nodes = nodes.filter((n) => (n.status || "suggested") !== "ignored");
    if (!showInsightNodes && filterType !== "insight") {
      nodes = nodes.filter((n) => n.type !== "insight");
    }
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
  }, [graphData, filterType, filterStatus, filterProvider, filterConfidence, layoutMode, showCognitivos, showInsightNodes]);

  const selectedNode = selectedId
    ? graphData?.nodes.find((n) => n.id === selectedId) ?? null
    : null;
  const selectedEdges = selectedId
    ? graphData?.edges.filter((e) => e.source === selectedId || e.target === selectedId) ?? []
      : [];
  const actionNode = selectedNode
    ? { ...selectedNode, status: nodeSummary?.status || selectedNode.status }
    : null;
  const nodeActions = getAvailableGraphActions(actionNode, { researchModeEnabled });

  function changeLayout(mode: GraphLayoutMode) {
    setLayoutMode(mode);
    if (typeof window !== "undefined") localStorage.setItem("bb_graph_layout", mode);
    setPan({ x: 0, y: 0 });
    setZoom(1);
  }

  function toggleInsightNodes() {
    if (showInsightNodes && selectedNode?.type === "insight") {
      setSelectedId(null);
      setShowDetail(false);
    }
    setShowInsightNodes((value) => {
      const next = !value;
      if (typeof window !== "undefined") {
        localStorage.setItem("bb_graph_show_insight_nodes", next ? "1" : "0");
      }
      return next;
    });
  }

  useEffect(() => {
    if (apiUrl === "__demo__" || apiUrl === "__browser__") return;
    apiFetch(`${apiUrl}/api/v1/settings/graph/config`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((config) => {
        const mode = config.default_layout as GraphLayoutMode;
        if (!mode || typeof window === "undefined" || localStorage.getItem("bb_graph_layout")) return;
        setLayoutMode(mode);
      })
      .catch(() => {});
  }, [apiUrl]);

  useEffect(() => {
    if (apiUrl === "__demo__" || apiUrl === "__browser__" || !selectedNode?.recordId || !showDetail) {
      setNodeSummary(null);
      return;
    }
    let cancelled = false;
    setSummaryLoading(true);
    apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/summary`)
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

  useEffect(() => {
    if (apiUrl === "__demo__" || apiUrl === "__browser__") {
      setResearchModeEnabled(false);
      return;
    }
    apiFetch(`${apiUrl}/api/v1/settings`)
      .then((r) => r.json())
      .then((payload) => {
        const item = (payload.settings || []).find((setting: { key: string; value: string }) => setting.key === "research_mode_enabled");
        setResearchModeEnabled(item?.value === "true");
      })
      .catch(() => setResearchModeEnabled(false));
  }, [apiUrl]);

  function centerNode(id: string) {
    setSelectedId(id);
    setShowDetail(true);
  }

  async function expandGraph() {
    if (apiUrl === "__demo__" || apiUrl === "__browser__") return;
    await apiFetch(`${apiUrl}/api/v1/graph/expand`, { method: "POST" });
    reload();
  }

  async function runInference() {
    const text = query.trim();
    if (!text) return;
    if (apiUrl === "__demo__") return;
    if (apiUrl === "__browser__") {
      setInferLoading(true);
      setInference(null);
      setInferenceSaveStatus("");
      try {
        const nodes = (graphData?.nodes || []).slice(0, 120).map((node) => ({
          id: node.id,
          type: node.type,
          label: node.label,
          summary: node.summary || "",
          path: node.path || "",
        }));
        const edges = (graphData?.edges || []).slice(0, 180).map((edge) => ({
          source: edge.source,
          target: edge.target,
          type: edge.type,
          reason: edge.reason || "",
          evidence: edge.evidence || [],
          confidence: edge.confidence || 0,
        }));
        const response = await askBrowserNvidia([
          {
            role: "system",
            content: "Answer only from the supplied BerryBrain graph. Return JSON only: {status,answer,relatedNodeIds,evidence}. status must be answered or insufficient_evidence. Evidence must cite node labels or edge reasons. Never invent a relation.",
          },
          { role: "user", content: JSON.stringify({ question: text, nodes, edges }) },
        ]);
        const parsed = JSON.parse(response.content.trim().replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "")) as {
          status?: string;
          answer?: string;
          relatedNodeIds?: string[];
          evidence?: string[];
        };
        const relatedIds = new Set(Array.isArray(parsed.relatedNodeIds) ? parsed.relatedNodeIds : []);
        const relatedNodes = (graphData?.nodes || []).filter((node) => relatedIds.has(node.id));
        setInference({
          status: parsed.status === "answered" ? "answered" : "insufficient_evidence",
          question: text,
          answer: parsed.answer || "There is not enough evidence in this graph to answer that question.",
          relatedNodes: relatedNodes.map((node) => ({ id: node.id, title: node.title, label: node.label, type: node.type, path: node.path })),
          evidence: (Array.isArray(parsed.evidence) ? parsed.evidence : []).slice(0, 8),
          provider: response.provider,
          model: response.model,
        });
      } catch (error) {
        setInference({
          status: "error",
          question: text,
          answer: error instanceof Error ? error.message : "Could not query NVIDIA NIM.",
        });
      } finally {
        setInferLoading(false);
      }
      return;
    }
    setInferLoading(true);
    setInference(null);
    setInferenceSaveStatus("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/infer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = typeof payload.detail === "string"
          ? payload.detail
          : `Graph inference failed (HTTP ${response.status}).`;
        throw new Error(message);
      }
      setInference(payload as InferenceResult);
    } catch (error) {
      setInference({
        status: "error",
        question: text,
        answer: error instanceof Error ? error.message : "Could not query the graph right now.",
      });
    } finally {
      setInferLoading(false);
    }
  }

  async function saveInferenceAsInsight() {
    const text = query.trim();
    if (!text || !inference) return;
    if (apiUrl === "__demo__") return;
    setInferenceSaving(true);
    setInferenceSaveStatus("Saving inference as insight...");
    try {
      if (apiUrl === "__browser__") {
        if (inference.status === "insufficient_evidence" || !inference.evidence?.length) {
          setInferenceSaveStatus("Not saved: this answer does not have enough evidence.");
          return;
        }
        const insight = await saveBrowserInferenceInsight({
          question: text,
          answer: inference.answer,
          relatedNodeIds: relatedInferenceNodes.map((node) => node.id),
          evidence: inference.evidence.map(formatInferenceEvidence).filter(Boolean),
          model: inference.model || "nvidia-nim",
        });
        setInference((current) => current ? { ...current, status: "saved_as_insight" } : current);
        setInferenceSaveStatus(`Saved as insight: ${insight.title}`);
        window.dispatchEvent(new CustomEvent("bb:browser-knowledge-updated"));
        reload();
        return;
      }
      const response = await apiFetch(`${apiUrl}/api/v1/insights/from-inference`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: text, inference }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setInferenceSaveStatus(payload.detail || "Could not save this inference.");
        return;
      }
      if (payload.status === "created") {
        setInference((current) => current ? { ...current, status: "saved_as_insight" } : current);
        setInferenceSaveStatus(`Saved as insight: ${payload.insight?.title || text}`);
        reload();
        return;
      }
      if (payload.status === "insufficient_evidence") {
        setInferenceSaveStatus("Not saved: this answer does not have enough evidence.");
        return;
      }
      setInferenceSaveStatus(payload.status ? `Save result: ${payload.status}` : "Could not save this inference.");
    } catch {
      setInferenceSaveStatus("Could not save this inference.");
    } finally {
      setInferenceSaving(false);
    }
  }

  async function createPermanentConceptNote() {
    if (!selectedNode?.sourceId || selectedNode.type !== "concept") return;
    if (apiUrl === "__demo__") return;
    const response = await apiFetch(`${apiUrl}/api/v1/concepts/${selectedNode.sourceId}/create-note`, { method: "POST" });
    const payload = await response.json();
    if (payload.note?.path) {
      onNavigate(payload.note.path);
    }
  }

  async function saveManualNodeNotes() {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/notes`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ notes: manualNotes }),
    });
    if (!response.ok) return;
    setNodeSummary((current) => current ? { ...current, userNotes: manualNotes } : current);
  }

  async function validateSelectedNodeWithWeb() {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    if (!researchModeEnabled) {
      setNodeActionStatus("Research Mode is disabled in Settings.");
      return;
    }
    if (!window.confirm("This action may query external sources. Continue?")) return;
    setActionLoading("validate-node-web");
    setNodeActionStatus("Validating with web...");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/validate-web`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok || payload.error) {
        setNodeActionStatus(payload.detail || payload.error || "Web validation failed.");
        return;
      }
      setNodeActionStatus(
        payload.status === "no_results"
          ? "No web evidence found."
          : `Web validation: ${payload.validation_status || payload.status}. ${payload.web_results || 0} sources checked.`,
      );
      reload();
      if (selectedNode.recordId) {
        const summaryResponse = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/summary`);
        if (summaryResponse.ok) setNodeSummary(await summaryResponse.json());
      }
    } finally {
      setActionLoading("");
    }
  }

  async function enrichSelectedNodeWithAI() {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    setActionLoading("enrich-node-ai");
    setNodeActionStatus("Enriching node with configured AI...");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/enrich-ai`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setNodeActionStatus(payload.detail || "AI enrichment failed.");
        return;
      }
      setNodeSummary(payload);
      setNodeActionStatus("Node enriched with AI context and source evidence.");
      reload();
    } finally {
      setActionLoading("");
    }
  }

  async function updateNodeStatus(status: "confirmed" | "ignored") {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    if (selectedNode.type === "insight" && selectedNode.sourceId) {
      await updateInsightStatus(status);
      return;
    }
    setActionLoading(status === "confirmed" ? "confirm-node" : "ignore-node");
    const action = status === "confirmed" ? "confirm" : "ignore";
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/${action}`, { method: "POST" });
      if (!response.ok) {
        setNodeActionStatus(`${status === "confirmed" ? "Confirm Node" : "Ignore Node"} failed.`);
        return;
      }
      setNodeSummary((current) => current ? { ...current, status } : current);
      setNodeActionStatus(status === "confirmed" ? "Node confirmed." : "Node ignored.");
      if (status === "ignored") {
        setSelectedId(null);
        setShowDetail(false);
      }
      reload();
    } finally {
      setActionLoading("");
    }
  }

  async function updateInsightStatus(status: "confirmed" | "ignored") {
    if (!selectedNode?.recordId || !selectedNode.sourceId) return;
    if (apiUrl === "__demo__") return;
    const isApply = status === "confirmed";
    setActionLoading(isApply ? "confirm-node" : "ignore-node");
    try {
      const insightAction = isApply ? "apply" : "ignore";
      const insightResponse = await apiFetch(`${apiUrl}/api/v1/insights/${selectedNode.sourceId}/${insightAction}`, { method: "POST" });
      if (!insightResponse.ok) {
        setNodeActionStatus(isApply ? "Apply Insight failed." : "Ignore Insight failed.");
        return;
      }
      const nodeAction = isApply ? "confirm" : "ignore";
      await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/${nodeAction}`, { method: "POST" });
      setNodeSummary((current) => current ? { ...current, status } : current);
      setNodeActionStatus(isApply ? "Insight applied." : "Insight ignored.");
      if (!isApply) {
        setSelectedId(null);
        setShowDetail(false);
      }
      reload();
    } finally {
      setActionLoading("");
    }
  }

  async function updateEdgeStatus(edgeId: number, status: "confirmed" | "ignored") {
    if (apiUrl === "__demo__") return;
    const action = status === "confirmed" ? "confirm" : "ignore";
    setActionLoading(`${action}-connection-${edgeId}`);
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/connections/${edgeId}/${action}`, { method: "POST" });
      if (!response.ok) {
        setNodeActionStatus(`${status === "confirmed" ? "Confirm Connection" : "Ignore Connection"} failed.`);
        return;
      }
      setNodeSummary((current) => current ? {
        ...current,
        connections: status === "ignored"
          ? current.connections.filter((connection) => connection.id !== edgeId)
          : current.connections.map((connection) => connection.id === edgeId ? { ...connection, status } : connection),
      } : current);
      setNodeActionStatus(status === "confirmed" ? "Connection confirmed." : "Connection ignored.");
      reload();
    } finally {
      setActionLoading("");
    }
  }

  async function generateConnectionInsight(edgeId: number) {
    if (apiUrl === "__demo__") return;
    setActionLoading(`save-insight-${edgeId}`);
    setNodeActionStatus("Generating connection insight with configured AI...");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/connections/${edgeId}/generate-insight`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setNodeActionStatus(payload.detail || "Connection insight generation failed.");
        return;
      }
      const insight = payload.insight;
      setNodeActionStatus(
        insight?.title
          ? `Insight ${payload.status === "exists" ? "already exists" : "created"}: ${insight.title}`
          : "Connection insight created.",
      );
      reload();
    } finally {
      setActionLoading("");
    }
  }

  async function reprocessSelectedNode() {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    setActionLoading("reprocess-node");
    setNodeActionStatus("Node reprocess queued.");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/reprocess`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setNodeActionStatus(payload.detail || "Reprocess node failed.");
        return;
      }
      setNodeActionStatus(`Node reprocess queued. Job ${payload.job_id || ""}`.trim());
    } finally {
      setActionLoading("");
    }
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="relative z-40 flex flex-wrap items-center gap-2 px-4 py-2 border-b border-border/50 bg-panel shrink-0 text-xs">
        <button className="rounded-lg p-1.5 text-muted hover:bg-surface shrink-0" onClick={onClose}>
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        </button>
        <div className="min-w-0">
          <h2 className="text-sm font-medium text-foreground">{t("graphTitle")}</h2>
          {graphData && (
            <div className="text-[10px] text-muted/60">
              {graphData.nodes.length} {t("nodes")} · {graphData.edges.length} {t("edges")} · {graphData.stats?.orphan_count ?? 0} {t("orphans")}
            </div>
          )}
        </div>
        <div className="flex-1" />
        <form
          className="relative z-50 flex min-w-[240px] flex-1 basis-[320px] items-center gap-1 sm:min-w-[280px] lg:max-w-[520px]"
          onSubmit={(e) => {
            e.preventDefault();
            runInference();
          }}
        >
          <input
            type="text"
            className="h-8 min-w-0 flex-1 rounded-lg border border-border/50 bg-surface px-3 text-[11px] outline-none focus:border-accent"
            placeholder={t("graphSearchPlaceholder")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            type="submit"
            className="bb-action h-8 min-w-14 shrink-0 px-3 text-[11px] font-medium"
            disabled={inferLoading || !query.trim()}
          >
            {inferLoading ? "..." : t("ask")}
          </button>
        </form>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="brain_view">{t("filterBrainView")}</option>
          <option value="topicos">{t("filterTopicos")}</option>
          <option value="note">{t("filterNote")}</option>
          <option value="concept">{t("filterConcept")}</option>
          <option value="entidade">{t("filterEntidade")}</option>
          <option value="contexto">{t("filterContexto")}</option>
          <option value="insight">{t("filterInsight")}</option>
          <option value="lacuna">{t("filterLacuna")}</option>
          <option value="anexo">{t("filterAnexo")}</option>
          <option value="trilha">{t("filterTrilha")}</option>
          <option value="cluster">{t("filterCluster")}</option>
          <option value="fonte">{t("filterFonte")}</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
          <option value="all">{t("status")}</option>
          <option value="suggested">{t("suggested")}</option>
          <option value="confirmed">{t("confirmed")}</option>
          <option value="ignored">{t("ignored")}</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterProvider} onChange={(e) => setFilterProvider(e.target.value)}>
          <option value="all">{t("origin")}</option>
          <option value="ai">{t("ai")}</option>
          <option value="deterministic">{t("system")}</option>
          <option value="backlink">{t("backlink")}</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterConfidence.toString()} onChange={(e) => setFilterConfidence(Number(e.target.value))}>
          <option value="0">{t("confidence")}</option>
          <option value="90">90%+</option>
          <option value="70">70%+</option>
          <option value="50">50%+</option>
        </select>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={layoutMode} onChange={(e) => changeLayout(e.target.value as GraphLayoutMode)}>
          <option value="brain">{t("layoutBrain")}</option>
          <option value="radial">{t("layoutRadial")}</option>
          <option value="type">{t("layoutType")}</option>
          <option value="connections">{t("layoutConnections")}</option>
        </select>
        <button
          className={`bb-action h-8 px-2.5 text-[11px] ${viewMode === "list" ? "bb-action--active" : ""}`}
          aria-pressed={viewMode === "list"}
          onClick={() => {
            const next = viewMode === "visual" ? "list" : "visual";
            setViewMode(next);
            localStorage.setItem("bb_graph_view_mode", next);
          }}
        >
          {viewMode === "visual" ? "List view" : "Visual view"}
        </button>
        <button className="bb-action h-8 px-2.5 text-[11px]" onClick={() => { setPan({ x: 0, y: 0 }); setZoom(1); setSelectedId(null); }}>{t("center")}</button>
        <button className="bb-action h-8 px-2.5 text-[11px]" onClick={expandGraph}>{t("expand")}</button>
        <button className={`bb-action h-8 px-2.5 text-[11px] ${showInsightNodes ? "bb-action--active" : ""}`} onClick={toggleInsightNodes}>
          {showInsightNodes ? t("hideInsightNodes") : t("showInsightNodes")}
        </button>
        <button className={`bb-action h-8 px-2.5 text-[11px] ${showLegend ? "bb-action--active" : ""}`} onClick={() => setShowLegend(!showLegend)}>{t("legend")}</button>
      </div>

      {inference && (
        <div className="border-b border-border/40 bg-panel/80 px-4 py-3">
          <div className="mx-auto max-w-5xl rounded-xl border border-border/50 bg-surface/70 p-3">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-accent">{t("graphInference")}</span>
              <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
            </div>
            <p className="text-sm text-foreground">{inference.answer}</p>
            {!!inference.relatedNodes?.length && (
              <div className="mt-2 flex flex-wrap gap-1">
                {relatedInferenceNodes.map((node) => (
                  <button
                    key={node.id}
                    className="rounded-full bg-panel px-2 py-1 text-[10px] text-muted hover:text-foreground"
                    onClick={() => {
                      centerNode(node.id);
                    }}
                  >
                    {node.label}
                  </button>
                ))}
              </div>
            )}
            {!!inference.evidence?.length && (
              <div className="mt-2 space-y-1 text-[11px] text-muted">
                <div className="text-[10px] font-medium uppercase tracking-wide text-muted/70">{t("evidence")}</div>
                {inference.evidence.slice(0, 4).map((item, index) => (
                  <div key={index} className="rounded-lg bg-panel/70 px-2 py-1">
                    {formatInferenceEvidence(item)}
                  </div>
                ))}
              </div>
            )}
            {(inference.provider || inference.model) && (
              <div className="mt-1 text-[10px] text-muted/60">
                {t("ai")}: {inference.provider || "provider"} {inference.model ? `· ${inference.model}` : ""}
              </div>
            )}
            <div className="mt-2 flex flex-wrap gap-1">
              {((inference.status === "answered" || inference.status === "success" || inference.status === "sufficient_evidence" || inference.status === "saved_as_insight")) && (
                <button
                  className="bb-action px-3 py-1 text-[10px]"
                  disabled={inferenceSaving || inference.status === "saved_as_insight"}
                  onClick={saveInferenceAsInsight}
                >
                  {inferenceSaving ? "Saving..." : inference.status === "saved_as_insight" ? "Saved" : t("saveAsInsight")}
                </button>
              )}
              <button className="bb-action px-3 py-1 text-[10px]" onClick={() => setInference(null)}>{t("close")}</button>
            </div>
            {inferenceSaveStatus && (
              <div className="mt-2 rounded-lg bg-panel/70 px-2 py-1 text-[10px] text-muted">
                {inferenceSaveStatus}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="relative flex-1 overflow-hidden bg-[#FBF4EC]">
      {error ? (
        <div className="flex h-full items-center justify-center text-sm text-danger">{t("graphLoadError")}</div>
      ) : graphData ? (
          filtered.nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-8 text-center">
              <div className="text-sm font-medium text-muted/60">{t("graphEmpty")}</div>
              <p className="text-xs text-muted/40">{t("graphEmptyDesc")}</p>
              {apiUrl === "__demo__" && (
                <div className="mt-2 flex gap-2">
                  <a href="https://github.com/imsouza/berrybrain" target="_blank" rel="noreferrer" className="bb-action px-3 py-1.5 text-xs font-medium">GitHub</a>
                  <a href={appPath("/docs")} className="bb-action px-3 py-1.5 text-xs font-medium">Docs</a>
                </div>
              )}
            </div>
          ) : (
          viewMode === "list" ? (
            <GraphListView
              data={filtered}
              selectedId={selectedId}
              onSelect={(id) => {
                setSelectedId(id);
                setShowDetail(true);
              }}
            />
          ) : (
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
              highlightedIds={highlightedIds}
              zoom={zoom}
              setZoom={setZoom}
              pan={pan}
              setPan={setPan}
              layoutMode={layoutMode}
            />
          )
          )
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-muted">{t("loadingGraph")}</div>
        )}

        {viewMode === "visual" && <div className="absolute bottom-4 right-4 z-10 flex flex-col gap-1">
          <button className="size-8 rounded-lg bg-panel/90 backdrop-blur flex items-center justify-center text-muted hover:text-foreground shadow-sm ring-1 ring-border/30 text-xs" onClick={() => setZoom((z) => Math.min(3, z * 1.3))}>+</button>
          <button className="size-8 rounded-lg bg-panel/90 backdrop-blur flex items-center justify-center text-muted hover:text-foreground shadow-sm ring-1 ring-border/30 text-xs" onClick={() => setZoom((z) => Math.max(0.2, z / 1.3))}>-</button>
        </div>}

        {showLegend && (
          <div className="absolute top-3 right-4 z-20 w-56 rounded-xl bg-panel/95 backdrop-blur shadow-lg ring-1 ring-border/30 p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[11px] font-medium text-foreground">{t("legend")}</span>
              <button className="text-[10px] text-muted hover:text-foreground" onClick={() => setShowLegend(false)}>X</button>
            </div>
            <div className="space-y-1 text-[10px]">
              {[
                ["note", "#C2185B"],
                ["concept", "#D98A00"],
                ["topico", "#96B55C"],
                ["entidade", "#2E9D68"],
                ["contexto", "#8B6F9F"],
                ["AI insight", "#4F7CCB"],
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
        <div className="absolute inset-x-0 bottom-0 top-[49px] z-30 overflow-y-auto border-l border-border/50 bg-panel/98 p-4 shadow-lg backdrop-blur sm:left-auto sm:w-[360px]">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-semibold uppercase tracking-wide text-accent">{selectedNode.type}</div>
              <h3 className="truncate text-sm font-medium text-foreground">{nodeSummary?.title || selectedNode.label}</h3>
            </div>
            <button className="text-[10px] text-muted hover:text-foreground" onClick={() => setShowDetail(false)}>X</button>
          </div>

            {summaryLoading ? (
              <div className="text-xs text-muted">{t("loadingNodeSummary")}</div>
            ) : (
              <div className="space-y-3 text-[11px] text-muted/75">
                <p className="rounded-lg bg-surface p-3 text-foreground/80">
                  {nodeSummary?.aiSummary || nodeSummary?.summary || selectedNode.aiSummary || selectedNode.summary || t("summaryNotGenerated")}
                </p>
                <div>{nodeSummary?.whyThisExists || t("nodeFromRealData")}</div>
                <div className="grid grid-cols-2 gap-2">
                  <Meta label={t("status")} value={nodeSummary?.status || selectedNode.status || "-"} />
                  <Meta label={t("confidence")} value={formatConfidence(nodeSummary?.confidence ?? selectedNode.confidence)} />
                  <Meta label={t("origin")} value={nodeSummary?.createdBy || selectedNode.createdBy || "-"} />
                  <Meta label={t("model")} value={nodeSummary?.createdByModel || selectedNode.createdByModel || "-"} />
                  <Meta label="Validation" value={nodeSummary?.validationStatus || selectedNode.validationStatus || "unvalidated"} />
                  <Meta label="Quality" value={nodeSummary?.sourceQuality || selectedNode.sourceQuality || "note_only"} />
                </div>

                {(nodeSummary?.aiContext || selectedNode.aiContext || nodeSummary?.learningValue || selectedNode.learningValue || nodeSummary?.sourceEvidence || selectedNode.sourceEvidence) && (
                  <section className="border-t border-border/30 pt-3">
                    <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">AI understanding</div>
                    {(nodeSummary?.aiContext || selectedNode.aiContext) && (
                      <p className="rounded-lg bg-surface p-2 text-[11px] text-foreground/80">{nodeSummary?.aiContext || selectedNode.aiContext}</p>
                    )}
                    {(nodeSummary?.learningValue || selectedNode.learningValue) && (
                      <p className="mt-2 text-[10px] text-muted/70"><span className="font-medium text-foreground/70">Learning value:</span> {nodeSummary?.learningValue || selectedNode.learningValue}</p>
                    )}
                    {(nodeSummary?.sourceEvidence || selectedNode.sourceEvidence) && (
                      <p className="mt-2 break-words text-[10px] text-muted/70"><span className="font-medium text-foreground/70">Source evidence:</span> {formatEvidenceLabel(nodeSummary?.sourceEvidence || selectedNode.sourceEvidence)}</p>
                    )}
                  </section>
                )}

                <section className="border-t border-border/30 pt-3">
                  <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Graph notes</div>
                  {nodeSummary?.aiNotes && (
                    <p className="mb-2 rounded-lg bg-surface p-2 text-[10px] text-muted/70">{t("aiSubagent")} {nodeSummary.aiNotes}</p>
                  )}
                  <textarea
                    className="min-h-20 w-full resize-none rounded-lg border border-border bg-surface p-2 text-[11px] text-foreground outline-none focus:border-accent"
                    placeholder={t("manualNotePlaceholder")}
                    value={manualNotes}
                    onChange={(event) => setManualNotes(event.target.value)}
                  />
                  <button className="bb-action mt-2 px-3 py-1.5 text-[10px]" onClick={saveManualNodeNotes}>{t("saveManualNote")}</button>
                </section>

                {!!nodeSummary?.notes?.length && (
                  <section className="border-t border-border/30 pt-3">
                    <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">{t("sourceNotes")}</div>
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
                  <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Explained connections</div>
                <div className="space-y-2">
                  {(nodeSummary?.connections?.length ? nodeSummary.connections : selectedEdges).slice(0, 6).map((edge, index) => {
                    const simpleEdge = edge as GraphEdge;
                    const detailedEdge = edge as NodeSummary["connections"][number];
                    const other = simpleEdge.source === selectedId ? simpleEdge.target : simpleEdge.source;
                    const otherNode = graphData?.nodes.find((n) => n.id === other);
                    const isInsightEdge = (detailedEdge.type || simpleEdge.type) === "insight_suggested";
                    return (
                      <div key={`${detailedEdge.id || simpleEdge.id || index}`} className="rounded-lg bg-surface p-2">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="inline-block h-0.5 w-4 rounded" style={{ background: EDGE_COLORS[detailedEdge.type || simpleEdge.type] || EDGE_COLORS.default }} />
                          <span className="truncate text-[11px] font-medium text-foreground">{otherNode?.label || detailedEdge.label || simpleEdge.type}</span>
                        </div>
                        {(detailedEdge.reason || simpleEdge.reason) && (
                          <div>
                            <div className="mb-0.5 text-[9px] font-medium uppercase tracking-wide text-accent">{isInsightEdge ? "Evidence citation" : "Connection reason"}</div>
                            <p>{detailedEdge.reason || simpleEdge.reason}</p>
                          </div>
                        )}
                        {!!(detailedEdge.evidence || simpleEdge.evidence)?.length && (
                          <div className="mt-1 text-[10px] text-muted/60">{t("evidence")}: {(detailedEdge.evidence || simpleEdge.evidence || []).slice(0, 2).map(formatEvidenceLabel).join(" · ")}</div>
                        )}
                        {(detailedEdge.provider || simpleEdge.provider || detailedEdge.model || simpleEdge.model) && (
                          <div className="mt-1 text-[9px] text-muted/50">
                            {detailedEdge.provider || simpleEdge.provider || "system"} {detailedEdge.model || simpleEdge.model ? `· ${detailedEdge.model || simpleEdge.model}` : ""}
                          </div>
                        )}
                        <div className="mt-2 flex flex-wrap items-center gap-1">
                          <span className="rounded-full bg-panel px-2 py-0.5 text-[9px] text-muted/60">{isInsightEdge ? "citation" : detailedEdge.status || simpleEdge.status || "suggested"}</span>
                          {!isInsightEdge && !!detailedEdge.id && (detailedEdge.status || simpleEdge.status || "suggested") === "suggested" && (
                            <button disabled={actionLoading === `confirm-connection-${detailedEdge.id}`} className="rounded-md bg-accent px-2 py-0.5 text-[9px] text-white disabled:opacity-50" onClick={() => updateEdgeStatus(detailedEdge.id, "confirmed")}>Confirm Connection</button>
                          )}
                          {!isInsightEdge && !!detailedEdge.id && (detailedEdge.status || simpleEdge.status || "suggested") === "suggested" && (
                            <button disabled={actionLoading === `ignore-connection-${detailedEdge.id}`} className="rounded-md bg-panel px-2 py-0.5 text-[9px] text-muted hover:text-foreground disabled:opacity-50" onClick={() => updateEdgeStatus(detailedEdge.id, "ignored")}>Ignore Connection</button>
                          )}
                          {!!detailedEdge.id && (detailedEdge.type || simpleEdge.type) !== "insight_suggested" && (
                            <button disabled={actionLoading === `save-insight-${detailedEdge.id}`} className="rounded-md bg-panel px-2 py-0.5 text-[9px] text-muted hover:text-foreground disabled:opacity-50" onClick={() => generateConnectionInsight(detailedEdge.id)}>Save as insight</button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>

              <div className="flex flex-wrap gap-1 pt-1">
                {selectedNode.path && (
                  <button className="bb-action px-3 py-1.5 text-[10px]" onClick={() => onNavigate(selectedNode.path!)}>{t("openNote")}</button>
                )}
                {nodeActions.filter((action) => action.visible && action.variant !== "danger").map((action) => (
                  <GraphActionButton
                    key={action.id}
                    action={action}
                    loading={actionLoading === action.id}
                    onClick={() => {
                      if (action.id === "confirm-node") updateNodeStatus("confirmed");
                      if (action.id === "ignore-node") updateNodeStatus("ignored");
                      if (action.id === "reprocess-node") reprocessSelectedNode();
                      if (action.id === "enrich-node-ai") enrichSelectedNodeWithAI();
                      if (action.id === "validate-node-web") validateSelectedNodeWithWeb();
                    }}
                  />
                ))}
                {selectedNode.type === "concept" && selectedNode.sourceId && (
                  <button className="bb-action px-3 py-1.5 text-[10px] font-medium text-amber-600" onClick={createPermanentConceptNote}>{t("createPermanentNote")}</button>
                )}
              </div>
              {nodeActionStatus && <div className="rounded-lg bg-surface p-2 text-[10px] text-muted/70">{nodeActionStatus}</div>}
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

function GraphActionButton({ action, loading, onClick }: { action: GraphAction; loading: boolean; onClick: () => void }) {
  const className = graphActionClass(action);
  return (
    <button
      className={className}
      disabled={action.disabled || loading}
      title={action.disabled ? action.reasonDisabled : undefined}
      onClick={onClick}
    >
      {loading ? "Working..." : action.label}
    </button>
  );
}

function graphActionClass(action: GraphAction) {
  const base = "bb-action px-3 py-1.5 text-[10px] font-medium";
  if (action.id === "confirm-node") {
    return `${base} text-emerald-600`;
  }
  if (action.id === "ignore-node") {
    return `${base} bb-action--danger`;
  }
  if (action.id === "reprocess-node") {
    return base;
  }
  if (action.id === "enrich-node-ai") {
    return base;
  }
  if (action.id === "validate-node-web") {
    return base;
  }
  if (action.variant === "danger") {
    return `${base} bb-action--danger`;
  }
  return base;
}

function formatConfidence(value?: number) {
  if (value === undefined || value === null) return "-";
  return `${Math.round(value <= 1 ? value * 100 : value)}%`;
}
