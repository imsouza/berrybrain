"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { Route } from "next";
import Link from "next/link";
import { GraphCanvas, useGraphData, type GraphLayoutMode } from "./graph-view";
import { formatEvidenceLabel, humanNodeType, humanOrigin, humanStatus } from "./graph-formatters";
import { t } from "@/i18n";
import { apiFetch, appPath } from "@/contexts/workspace-context";
import { diagnosticMessages, isFilterHidden, type PipelineDiagnostic } from "@/lib/diagnostics";
import { VoicePromptButton } from "./voice-prompt-button";

const EDGE_COLORS: Record<string, string> = {
  references: "#3C8F5A",
  derived_from: "#4F7CCB",
  mentions: "#96B55C",
  about: "#D98A00",
  supports: "#4A8F6A",
  contradicts: "#B85C4A",
  contrasts_with: "#8B6F9F",
  same_as: "#B85C4A",
  example_of: "#4A8F6A",
  applies_to: "#9F6B4A",
  prerequisite_for: "#3C8F5A",
  broader: "#557A95",
  narrower: "#557A95",
  instance_of: "#2E9D68",
  part_of: "#6B4A2D",
  attached_to: "#7A6F64",
  contextualizes: "#D98A00",
  related: "#6B4A2D",
  default: "#B89B82",
};

const NODE_LEGEND = [
  ["vault", "■", "Vault namespace"],
  ["note", "●", "Berry red override"],
  ["concept", "◆", "Concept"],
  ["entity", "⬡", "Entity"],
  ["topic", "▲", "Topic"],
  ["context", "▼", "Context"],
  ["insight", "▭", "Insight highlight"],
  ["source", "▰", "Source"],
  ["attachment", "◫", "Attachment"],
  ["gap", "◇", "Knowledge gap"],
  ["study_path", "›", "Study path"],
  ["cluster", "▤", "Computed cluster"],
] as const;

const EDGE_ROLES: Record<string, string> = {
  mentions: "Note identifies knowledge",
  about: "Work has a primary subject",
  references: "Document cites evidence",
  derived_from: "Claim has provenance",
  supports: "Evidence supports knowledge",
  contradicts: "Evidence challenges knowledge",
  broader: "More general concept",
  narrower: "More specific concept",
  instance_of: "Entity instantiates concept",
  part_of: "Knowledge is a component",
  prerequisite_for: "Required before target",
  example_of: "Concrete example of target",
  applies_to: "Knowledge applies to target",
  same_as: "Equivalent identity",
  contrasts_with: "Symmetric contrast",
  attached_to: "Attachment belongs to note",
  contextualizes: "Source adds context",
  related: "Symmetric semantic relation",
};

function edgeColor(type: string): string {
  if (EDGE_COLORS[type]) return EDGE_COLORS[type];
  let hash = 2166136261;
  for (const character of type || "connection") {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `hsl(${Math.abs(hash) % 360} 48% 46%)`;
}

type GraphNode = {
  id: string;
  recordId?: number;
  type: string;
  label: string;
  title?: string;
  summary?: string;
  path?: string;
  folder?: string;
  source?: string;
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
  semanticState?: string;
  semanticProfileVersion?: number;
  clusterId?: number | null;
  colorId?: string;
  colorConfidence?: number;
  colorReason?: string;
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
  inferenceId?: number;
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

type SemanticAnalysis = {
  meaning_in_context: string;
  why_it_matters_here: string;
  supported_findings: string[];
  inferences: string[];
  uncertainties: string[];
  evidence: Array<{ source?: string; reference?: string; claim?: string } | string>;
  connection_assessments: Array<{
    target_node_id?: number;
    relation?: string;
    assessment?: string;
    confidence?: number;
  }>;
  confidence: {
    concept_detection: number;
    semantic_interpretation: number;
    evidence_coverage: number;
  };
  provider: string;
  model: string;
  prompt_version: string;
};

type SemanticAnalysisPayload = {
  nodeId: number;
  state: string;
  analysis: SemanticAnalysis | null;
  historyCount: number;
  profileVersion: number;
  sourceFingerprint: string;
};

type FlowTurn = {
  id: number;
  role: "user" | "assistant";
  content: string;
  evidenceIds: string[];
  provider?: string;
  model?: string;
  status: string;
};

type AskSuggestion = {
  id: string;
  prompt: string;
  topic: string;
  source: string;
  nodeIds: number[];
};

type AskSuggestionPayload = {
  questions: AskSuggestion[];
  topics: string[];
  graph: { nodes: number; edges: number; suggestedInsights?: number; gaps?: number };
  generation?: "live_ai" | "live_ai_augmented" | "cached_ai" | "graph_context" | "unavailable";
};

type ResearchRun = {
  id: number;
  status: string;
  progress: number;
  plannedQueries: number;
  completedQueries: number;
  error?: string;
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
  semanticState?: string;
  semanticProfileVersion?: number;
  clusterId?: string;
  colorId?: string;
  colorConfidence?: number;
  colorReason?: string;
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
  | "retry-semantic-analysis"
  | "regenerate-semantic-analysis";

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
  semanticState?: string,
): GraphAction[] {
  if (!item) return [];
  const status = item.status || "suggested";
  return [
    {
      id: "confirm-node",
      label: item.type === "insight" ? "Apply insight" : "Confirm",
      variant: "primary",
      visible: status === "suggested",
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "ignore-node",
      label: item.type === "insight" ? "Ignore insight" : "Ignore",
      variant: "secondary",
      visible: status === "suggested",
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "retry-semantic-analysis",
      label: "Retry analysis",
      variant: "secondary",
      visible: ["failed", "stale", "not_configured", "needs_review"].includes(semanticState || ""),
      disabled: false,
      requiresConfirmation: false,
    },
    {
      id: "regenerate-semantic-analysis",
      label: "Regenerate analysis",
      variant: "secondary",
      visible: semanticState === "completed",
      disabled: false,
      requiresConfirmation: true,
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

function graphNodeRecordId(node: GraphNode | undefined): number | null {
  if (node?.recordId && Number.isSafeInteger(node.recordId)) return node.recordId;
  const match = node?.id.match(/_(\d+)$/);
  if (!match) return null;
  const parsed = Number(match[1]);
  return Number.isSafeInteger(parsed) && parsed > 0 ? parsed : null;
}

function GraphListView({
  data,
  selectedId,
  onOpen,
}: {
  data: { nodes: GraphNode[]; edges: GraphEdge[] };
  selectedId: string | null;
  onOpen: (id: string) => void;
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
            {nodes.map((node) => {
              const recordId = graphNodeRecordId(node);
              return (
              <Link
                key={node.id}
                href={(recordId ? appPath(`/graph/nodes/${recordId}`) : "#") as Route}
                role="listitem"
                aria-label={node.label}
                aria-current={selectedId === node.id ? "true" : undefined}
                className={`flex w-full items-center gap-3 px-3 py-2.5 text-left hover:bg-surface ${selectedId === node.id ? "bg-surface" : ""}`}
                onClick={(event) => {
                  event.preventDefault();
                  if (recordId) onOpen(node.id);
                }}
              >
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm text-foreground">{node.label}</span>
                  <span className="block text-[10px] uppercase text-muted">{node.type} · {node.status || "suggested"}</span>
                </span>
                <span className="text-xs tabular-nums text-muted" aria-label={`${degree.get(node.id) || 0} connections`}>
                  {degree.get(node.id) || 0}
                </span>
              </Link>
              );
            })}
          </div>
        </section>
        <section aria-labelledby="graph-list-connections">
          <h2 id="graph-list-connections" className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted">Connections</h2>
          <div className="divide-y divide-border/50 overflow-hidden rounded-lg border border-border/60 bg-panel" role="list">
            {data.edges.map((edge, index) => {
              const source = nodeById.get(edge.source);
              const target = nodeById.get(edge.target);
              const sourceRecordId = graphNodeRecordId(source);
              return (
                <Link
                  key={edge.id || `${edge.source}:${edge.target}:${edge.type}:${index}`}
                  href={(sourceRecordId ? appPath(`/graph/nodes/${sourceRecordId}`) : "#") as Route}
                  role="listitem"
                  className="block w-full px-3 py-2.5 text-left hover:bg-surface"
                  onClick={(event) => {
                    event.preventDefault();
                    if (sourceRecordId) onOpen(edge.source);
                  }}
                >
                  <span className="block text-sm text-foreground">{source?.label || edge.source} → {target?.label || edge.target}</span>
                  <span className="block text-[10px] uppercase text-muted">{edge.type} · {edge.status || "suggested"} · {Math.round((edge.confidence || 0) * 100)}%</span>
                  {edge.reason && <span className="mt-1 block text-xs text-muted">{edge.reason}</span>}
                </Link>
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
  autoFocusAsk = false,
  initialAskQuery = "",
  autoSubmitAsk = false,
  askOnly = false,
  onAskFocused,
  onClose,
  onNavigate,
  onOpenGraph,
  onOpenHome,
}: {
  apiUrl: string;
  autoFocusAsk?: boolean;
  initialAskQuery?: string;
  autoSubmitAsk?: boolean;
  askOnly?: boolean;
  onAskFocused?: () => void;
  onClose: () => void;
  onNavigate: (path: string) => void;
  onOpenGraph?: () => void;
  onOpenHome?: () => void;
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
  const askInputRef = useRef<HTMLInputElement>(null);
  const suggestionTrackRef = useRef<HTMLDivElement>(null);
  const autoSubmittedQueryRef = useRef("");
  const [filterType, setFilterType] = useState("brain_view");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterConfidence, setFilterConfidence] = useState(0);
  const [pipelineDiag, setPipelineDiag] = useState<{ code: string; text: string }[]>([]);
  useEffect(() => {
    if (!autoFocusAsk) return;
    const initialQuery = initialAskQuery.trim();
    if (initialQuery) setQuery(initialQuery);
    askInputRef.current?.focus();
    onAskFocused?.();
  }, [autoFocusAsk, initialAskQuery, onAskFocused]);
  useEffect(() => {
    const initialQuery = initialAskQuery.trim();
    if (!autoSubmitAsk || !initialQuery || query !== initialQuery) return;
    if (autoSubmittedQueryRef.current === initialQuery) return;
    autoSubmittedQueryRef.current = initialQuery;
    const frame = requestAnimationFrame(() => askInputRef.current?.form?.requestSubmit());
    return () => cancelAnimationFrame(frame);
  }, [autoSubmitAsk, initialAskQuery, query]);
  useEffect(() => {
    // Check data before graphData is declared (line 391) - use data directly
    const d = data as { nodes: GraphNode[] } | null | undefined;
    if (apiUrl === "__demo__" || !d || d.nodes.length > 0) return;
    let cancelled = false;
    apiFetch("/api/v1/debug/vault-graph-pipeline")
      .then((r) => (r.ok ? r.json() : null))
      .then((p) => {
        if (cancelled || !p) return;
        const msgs = diagnosticMessages(p as PipelineDiagnostic);
        if (!cancelled) setPipelineDiag(msgs);
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [apiUrl, data]);
  const [showInsightNodes, setShowInsightNodes] = useState(() => {
    if (typeof window === "undefined") return true;
    return localStorage.getItem("bb_graph_show_insight_nodes") !== "0";
  });
  const showCognitiveNodes = true;
  const [layoutMode, setLayoutMode] = useState<GraphLayoutMode>(() => {
    if (typeof window === "undefined") return "brain";
    const firstOpenThisSession = sessionStorage.getItem("bb_graph_opened_this_session") !== "1";
    if (firstOpenThisSession) {
      sessionStorage.setItem("bb_graph_opened_this_session", "1");
      return "brain";
    }
    const saved = localStorage.getItem("bb_graph_layout");
    if (saved === "default") return "brain";
    return ["brain", "radial", "type", "connections"].includes(saved || "")
      ? saved as GraphLayoutMode
      : "brain";
  });
  useEffect(() => {
    const raw = sessionStorage.getItem("bb_graph_return_state");
    if (!raw) return;
    try {
      const saved = JSON.parse(raw) as {
        zoom?: number;
        pan?: { x: number; y: number };
        filterType?: string;
        filterStatus?: string;
        filterProvider?: string;
        filterConfidence?: number;
        layoutMode?: GraphLayoutMode;
        viewMode?: "visual" | "list";
      };
      if (typeof saved.zoom === "number") setZoom(saved.zoom);
      if (saved.pan) setPan(saved.pan);
      if (saved.filterType) setFilterType(saved.filterType);
      if (saved.filterStatus) setFilterStatus(saved.filterStatus);
      if (saved.filterProvider) setFilterProvider(saved.filterProvider);
      if (typeof saved.filterConfidence === "number") setFilterConfidence(saved.filterConfidence);
      if (saved.layoutMode) setLayoutMode(saved.layoutMode);
      if (saved.viewMode) setViewMode(saved.viewMode);
      sessionStorage.removeItem("bb_graph_return_state");
    } catch {
      sessionStorage.removeItem("bb_graph_return_state");
    }
  }, []);
  const [inference, setInference] = useState<InferenceResult | null>(null);
  const [inferLoading, setInferLoading] = useState(false);
  const [inferenceSaveStatus, setInferenceSaveStatus] = useState("");
  const [inferenceSaving, setInferenceSaving] = useState(false);
  const [nodeSummary, setNodeSummary] = useState<NodeSummary | null>(null);
  const [semanticAnalysis, setSemanticAnalysis] = useState<SemanticAnalysisPayload | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [manualNotes, setManualNotes] = useState("");
  const [nodeActionStatus, setNodeActionStatus] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [researchModeEnabled, setResearchModeEnabled] = useState(false);
  const [researchRun, setResearchRun] = useState<ResearchRun | null>(null);
  const [researchStatus, setResearchStatus] = useState("");
  const [flowSessionId, setFlowSessionId] = useState<string | null>(null);
  const [flowTurns, setFlowTurns] = useState<FlowTurn[]>([]);
  const [flowActive, setFlowActive] = useState(false);
  const [askSuggestions, setAskSuggestions] = useState<AskSuggestionPayload | null>(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [nodeEdit, setNodeEdit] = useState({
    type: "note",
    label: "",
    title: "",
    summary: "",
    source: "",
    status: "suggested",
  });
  const [nodeEditSaving, setNodeEditSaving] = useState(false);
  const [nodeEditStatus, setNodeEditStatus] = useState("");

  const graphData = data as {
    nodes: GraphNode[];
    edges: GraphEdge[];
    stats?: { orphan_count?: number; node_count?: number; edge_count?: number };
    palette?: Record<string, {
      colorId: string;
      lightHex: string;
      darkHex: string;
      border: string;
      text: string;
      namespace: "semantic" | "vault" | "pending";
    }>;
    graphVersion?: number;
  } | null;
  const relatedInferenceNodes = useMemo(() => resolveRelatedInferenceNodes(inference, graphData), [inference, graphData]);
  const highlightedIds = useMemo(() => relatedInferenceNodes.map((node) => node.id), [relatedInferenceNodes]);
  const graphEdgeTypes = useMemo(
    () => [...new Set((graphData?.edges || []).map((edge) => edge.type || "default"))].sort(),
    [graphData],
  );

  const filtered = useMemo(() => {
    const orphanFilter = typeof window !== "undefined" ? localStorage.getItem("bb_graph_filter_orphans") : null;
    if (orphanFilter) localStorage.removeItem("bb_graph_filter_orphans");
    if (!graphData) return {
      nodes: [],
      edges: [],
      palette: undefined,
      graphVersion: undefined,
    };
    let nodes = graphData.nodes;
    let edges = graphData.edges;
    if (filterType === "brain_view") {
      const base = ["note", "concept", "topic", "entity"];
      const cognitiveTypes = showCognitiveNodes ? ["context", "gap", "insight"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitiveTypes].includes(n.type));
    } else if (filterType === "topics") {
      nodes = nodes.filter((n) => n.type === "topic");
    } else if (filterType !== "all") {
      const typeAliases: Record<string, string[]> = {
        source: ["source", "web_source"],
      };
      nodes = nodes.filter((n) => (typeAliases[filterType] || [filterType]).includes(n.type));
    } else if (layoutMode === "brain") {
      const base = ["note", "concept", "topic", "entity"];
      const cognitiveTypes = showCognitiveNodes ? ["context", "gap", "insight"] : [];
      nodes = nodes.filter((n) => [...base, ...cognitiveTypes].includes(n.type));
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
    return {
      nodes,
      edges,
      palette: graphData.palette,
      graphVersion: graphData.graphVersion,
    };
  }, [graphData, filterType, filterStatus, filterProvider, filterConfidence, layoutMode, showCognitiveNodes, showInsightNodes]);

  const selectedNode = selectedId
    ? graphData?.nodes.find((n) => n.id === selectedId) ?? null
    : null;
  const selectedEdges = selectedId
    ? graphData?.edges.filter((e) => e.source === selectedId || e.target === selectedId) ?? []
      : [];
  const actionNode = selectedNode
    ? { ...selectedNode, status: nodeSummary?.status || selectedNode.status }
    : null;
  const nodeActions = getAvailableGraphActions(
    actionNode,
    semanticAnalysis?.state || nodeSummary?.semanticState || selectedNode?.semanticState,
  );

  useEffect(() => {
    if (!selectedNode) {
      setNodeEdit({ type: "note", label: "", title: "", summary: "", source: "", status: "suggested" });
      setNodeEditStatus("");
      return;
    }
    setNodeEdit({
      type: nodeSummary?.type || selectedNode.type || "note",
      label: nodeSummary?.label || selectedNode.label || "",
      title: nodeSummary?.title || selectedNode.title || selectedNode.label || "",
      summary: nodeSummary?.summary || selectedNode.summary || "",
      source: nodeSummary?.source || selectedNode.source || "",
      status: nodeSummary?.status || selectedNode.status || "suggested",
    });
    setNodeEditStatus("");
  }, [
    nodeSummary?.confidence,
    nodeSummary?.id,
    nodeSummary?.label,
    nodeSummary?.source,
    nodeSummary?.status,
    nodeSummary?.summary,
    nodeSummary?.title,
    nodeSummary?.type,
    selectedNode,
  ]);

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
    if (apiUrl === "__demo__") return;
    apiFetch(`${apiUrl}/api/v1/settings/graph/config`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((config) => {
        const configured = config.default_layout;
        const mode = configured === "default" ? "brain" : configured as GraphLayoutMode;
        if (!mode || typeof window === "undefined" || localStorage.getItem("bb_graph_layout")) return;
        setLayoutMode(mode);
      })
      .catch(() => {});
  }, [apiUrl]);

  useEffect(() => {
    if (!askOnly || apiUrl === "__demo__") return;
    let cancelled = false;
    let refreshTimer: ReturnType<typeof setTimeout> | undefined;
    setSuggestionsLoading(true);
    const loadSuggestions = async (attempt: number) => {
      try {
        const response = await apiFetch(`${apiUrl}/api/v1/ask/suggestions?limit=16`);
        if (!response.ok) throw new Error("Suggestion request failed");
        const payload = await response.json() as AskSuggestionPayload;
        if (cancelled) return;
        setAskSuggestions(payload);
        if (payload.generation === "graph_context" && attempt < 3) {
          refreshTimer = setTimeout(() => void loadSuggestions(attempt + 1), 15_000);
        }
      } catch {
        if (!cancelled && attempt === 0) {
          setAskSuggestions({ questions: [], topics: [], graph: { nodes: 0, edges: 0 } });
        }
      } finally {
        if (!cancelled && attempt === 0) setSuggestionsLoading(false);
      }
    };
    void loadSuggestions(0);
    return () => {
      cancelled = true;
      if (refreshTimer) clearTimeout(refreshTimer);
    };
  }, [apiUrl, askOnly]);

  useEffect(() => {
    if (apiUrl === "__demo__" || !selectedNode?.recordId || !showDetail) {
      setNodeSummary(null);
      setSemanticAnalysis(null);
      return;
    }
    let cancelled = false;
    setSummaryLoading(true);
    Promise.all([
      apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/summary`)
        .then((response) => (response.ok ? response.json() : Promise.reject())),
      apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/semantic-analysis`)
        .then((response) => (response.ok ? response.json() : null)),
    ])
      .then(([payload, semanticPayload]) => {
        if (!cancelled) {
          setNodeSummary(payload);
          setSemanticAnalysis(semanticPayload as SemanticAnalysisPayload | null);
          setManualNotes(payload.userNotes || "");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setNodeSummary(null);
          setSemanticAnalysis(null);
        }
      })
      .finally(() => {
        if (!cancelled) setSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [apiUrl, selectedNode?.recordId, showDetail]);

  useEffect(() => {
    if (apiUrl === "__demo__" || typeof window === "undefined") return;
    const savedSessionId = sessionStorage.getItem("bb_flow_session_id");
    if (!savedSessionId) return;
    let cancelled = false;
    apiFetch(`${apiUrl}/api/v1/ask/sessions/${savedSessionId}`)
      .then((response) => (response.ok ? response.json() : Promise.reject()))
      .then((payload) => {
        if (cancelled || !payload.session?.active) return;
        setFlowSessionId(payload.session.id);
        setFlowTurns(payload.turns || []);
        setFlowActive(true);
      })
      .catch(() => sessionStorage.removeItem("bb_flow_session_id"));
    return () => {
      cancelled = true;
    };
  }, [apiUrl]);

  useEffect(() => {
    if (!researchRun || !["pending", "running"].includes(researchRun.status)) return;
    const timer = window.setTimeout(async () => {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/research-runs/${researchRun.id}`);
      if (!response.ok) {
        setResearchStatus("Could not refresh online research progress.");
        return;
      }
      const payload = await response.json();
      const next = payload.run as ResearchRun;
      setResearchRun(next);
      if (next.status === "completed") {
        setResearchStatus(`Research completed. ${next.completedQueries} queries checked.`);
        reload();
      } else if (next.status === "cancelled") {
        setResearchStatus("Online research cancelled.");
      } else if (next.status === "failed") {
        setResearchStatus(next.error || "Online research failed.");
      }
    }, 1500);
    return () => window.clearTimeout(timer);
  }, [apiUrl, reload, researchRun]);

  useEffect(() => {
    if (apiUrl === "__demo__") {
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
    openNodeDetail(id);
  }

  function rememberGraphState() {
    sessionStorage.setItem("bb_graph_return_state", JSON.stringify({
      zoom,
      pan,
      filterType,
      filterStatus,
      filterProvider,
      filterConfidence,
      layoutMode,
      viewMode,
    }));
  }

  function openNodeDetail(id: string) {
    const node = graphData?.nodes.find((item) => item.id === id);
    const recordId = graphNodeRecordId(node);
    if (!recordId) return;
    rememberGraphState();
    window.location.assign(appPath(`/graph/nodes/${recordId}`));
  }

  function prepareNodeDetail(id: string) {
    const node = graphData?.nodes.find((item) => item.id === id);
    if (!graphNodeRecordId(node)) return;
    setSelectedId(id);
    setShowDetail(false);
    rememberGraphState();
  }

  async function expandGraph() {
    if (apiUrl === "__demo__") return;
    await apiFetch(`${apiUrl}/api/v1/graph/expand`, { method: "POST" });
    reload();
  }

  async function runInference(questionOverride?: string) {
    const text = (questionOverride ?? query).trim();
    if (!text) return;
    if (apiUrl === "__demo__") return;
    if (questionOverride) setQuery(text);
    setInferLoading(true);
    setInferenceSaveStatus("");
    try {
      if (flowActive && flowSessionId) {
        const response = await apiFetch(`${apiUrl}/api/v1/ask/sessions/${flowSessionId}/turns`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: text }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(typeof payload.detail === "string" ? payload.detail : `Flow failed (HTTP ${response.status}).`);
        }
        const userTurn = payload.userTurn as FlowTurn;
        const assistantTurn = payload.assistantTurn as FlowTurn;
        setFlowTurns((current) => [...current, userTurn, assistantTurn]);
        setInference({
          status: assistantTurn.status === "completed" ? "answered" : assistantTurn.status,
          question: text,
          answer: assistantTurn.content,
          evidence: assistantTurn.evidenceIds,
          provider: assistantTurn.provider,
          model: assistantTurn.model,
        });
        setQuery("");
        return;
      }
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

  async function startFlow() {
    if (apiUrl === "__demo__") return;
    const response = await apiFetch(`${apiUrl}/api/v1/ask/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        mode: "flow",
        title: query.trim().slice(0, 120),
        inference_id: inference?.inferenceId,
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.session?.id) {
      setInferenceSaveStatus(payload.detail || "Could not start Flow.");
      return;
    }
    setFlowSessionId(payload.session.id);
    setFlowTurns(payload.turns || []);
    setFlowActive(true);
    sessionStorage.setItem("bb_flow_session_id", payload.session.id);
  }

  async function exitFlow() {
    if (flowSessionId) {
      await apiFetch(`${apiUrl}/api/v1/ask/sessions/${flowSessionId}/close`, { method: "POST" });
    }
    setFlowSessionId(null);
    setFlowTurns([]);
    setFlowActive(false);
    sessionStorage.removeItem("bb_flow_session_id");
  }

  async function cancelFlowRequest() {
    if (!flowSessionId) return;
    await apiFetch(`${apiUrl}/api/v1/ask/sessions/${flowSessionId}/cancel`, { method: "POST" });
    setInferenceSaveStatus("Flow request cancellation requested.");
  }

  async function startOnlineResearch() {
    if (apiUrl === "__demo__" || !researchModeEnabled) {
      setResearchStatus("Enable Research Mode in Settings to check online sources.");
      return;
    }
    const response = await apiFetch(`${apiUrl}/api/v1/graph/research-runs`, { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.run) {
      setResearchStatus(payload.detail || "Could not start online research.");
      return;
    }
    setResearchRun(payload.run as ResearchRun);
    setResearchStatus("Online research queued.");
  }

  async function cancelOnlineResearch() {
    if (!researchRun) return;
    const response = await apiFetch(`${apiUrl}/api/v1/graph/research-runs/${researchRun.id}/cancel`, { method: "POST" });
    const payload = await response.json().catch(() => ({}));
    if (response.ok && payload.run) setResearchRun(payload.run as ResearchRun);
    setResearchStatus("Online research cancelled.");
  }

  async function saveInferenceAsInsight() {
    const text = inference?.question || query.trim();
    if (!text || (!inference?.inferenceId && !flowSessionId)) return;
    if (apiUrl === "__demo__") return;
    setInferenceSaving(true);
    setInferenceSaveStatus(flowActive ? "Saving Flow answer as insight..." : "Saving inference as insight...");
    try {
      const response = flowActive && flowSessionId && !inference?.inferenceId
        ? await apiFetch(`${apiUrl}/api/v1/ask/sessions/${flowSessionId}/insight`, { method: "POST" })
        : await apiFetch(`${apiUrl}/api/v1/insights/from-inference`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ inferenceId: inference?.inferenceId }),
          });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setInferenceSaveStatus(payload.detail || "Could not save this inference.");
        return;
      }
      if (payload.status === "created" || payload.status === "existing") {
        setInference((current) => current ? { ...current, status: "saved_as_insight" } : current);
        setInferenceSaveStatus(`Saved as insight: ${payload.insight?.title || text}`);
        reload();
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

  async function saveGraphNodeEdits() {
    if (!selectedNode?.recordId || apiUrl === "__demo__") return;
    setNodeEditSaving(true);
    setNodeEditStatus("Saving node...");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          label: nodeEdit.label,
          type: nodeEdit.type,
          title: nodeEdit.title,
          summary: nodeEdit.summary,
          source: nodeEdit.source,
          status: nodeEdit.status,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setNodeEditStatus(payload.detail || "Node edit failed.");
        return;
      }
      setNodeSummary((current) => current ? { ...current, ...payload } : current);
      setNodeEditStatus("Node saved. Judge validation and graph recalculation queued.");
      reload();
    } finally {
      setNodeEditSaving(false);
    }
  }

  async function processSemanticAnalysis(action: "retry" | "regenerate") {
    if (!selectedNode?.recordId) return;
    if (apiUrl === "__demo__") return;
    if (action === "regenerate" && !window.confirm("Generate a new semantic analysis version for this node?")) return;
    const actionId = action === "retry" ? "retry-semantic-analysis" : "regenerate-semantic-analysis";
    setActionLoading(actionId);
    setNodeActionStatus(action === "retry" ? "Retrying semantic analysis..." : "New semantic analysis queued...");
    try {
      const response = await apiFetch(
        `${apiUrl}/api/v1/graph/nodes/${selectedNode.recordId}/semantic-analysis/${action}`,
        { method: "POST" },
      );
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        setNodeActionStatus(payload.detail || "Semantic analysis could not be queued.");
        return;
      }
      setSemanticAnalysis((current) => current ? { ...current, state: "pending" } : current);
      setNodeActionStatus(`Semantic analysis queued. Job ${payload.jobId || ""}`.trim());
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

  function scrollSuggestions(direction: -1 | 1) {
    const track = suggestionTrackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction * track.clientWidth * 0.82, behavior: "smooth" });
  }

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className="relative z-40 flex flex-wrap items-center gap-2 px-4 py-2 border-b border-border/50 bg-panel shrink-0 text-xs">
        <button className="rounded-lg p-1.5 text-muted hover:bg-surface shrink-0" onClick={askOnly ? (onOpenHome || onClose) : onClose} aria-label={askOnly ? "Back to Home" : "Back"}>
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
        </button>
        {!askOnly && <div className="min-w-0">
          <h2 className="text-sm font-medium text-foreground">{t("graphTitle")}</h2>
          {graphData && (
            <div className="text-[10px] text-muted/60">
              {graphData.nodes.length} {t("nodes")} · {graphData.edges.length} {t("edges")} · {graphData.stats?.orphan_count ?? 0} {t("orphans")}
            </div>
          )}
        </div>}
        {askOnly && <div className="flex items-center gap-1">
          <button className="bb-action h-8 px-2.5 text-[11px]" onClick={onOpenHome || onClose}>Home</button>
          <button className="bb-action h-8 px-2.5 text-[11px]" onClick={onOpenGraph || (() => { window.location.href = appPath("/brain?graph=open"); })}>Graph</button>
        </div>}
        <div className="flex-1" />
        {!askOnly && <form
          className={`relative z-50 order-last flex min-w-[260px] flex-1 basis-full items-center gap-2 rounded-lg border p-1.5 sm:basis-[360px] lg:order-none lg:max-w-[560px] ${
            flowActive ? "border-violet-500/60 bg-violet-500/10" : "border-accent/30 bg-surface/80"
          }`}
          onSubmit={(e) => {
            e.preventDefault();
            runInference();
          }}
        >
          <span className={`shrink-0 px-1 text-[10px] font-semibold uppercase tracking-wide ${flowActive ? "text-violet-600" : "text-accent"}`}>
            {flowActive ? "Flow" : "Ask"}
          </span>
          <input
            ref={askInputRef}
            type="text"
            className="h-9 min-w-0 flex-1 rounded-md border border-border/50 bg-panel px-3 text-sm outline-none placeholder:text-muted/55 focus:border-accent"
            placeholder="Ask your graph about a note, concept, connection, job, or missing context..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <VoicePromptButton value={query} onChange={setQuery} className="h-9 w-9" />
          {!askOnly && <button
            type="button"
            className="bb-action grid h-9 w-9 shrink-0 place-items-center text-base"
            aria-label="Open Ask workspace"
            title="Open Ask workspace"
            onClick={() => { window.location.href = appPath(`/ask${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ""}`); }}
          >↗</button>}
          <button
            type="submit"
            className="bb-action h-9 min-w-16 shrink-0 px-3 text-xs font-semibold"
            disabled={inferLoading || !query.trim()}
          >
            {inferLoading ? "..." : t("ask")}
          </button>
          {flowActive && inferLoading && (
            <button type="button" className="bb-action h-9 px-2 text-[10px]" onClick={cancelFlowRequest}>
              Cancel
            </button>
          )}
        </form>}
        {flowActive && !askOnly && (
          <button className="bb-action h-8 px-2.5 text-[11px] text-violet-600" onClick={exitFlow}>
            Exit Flow · {Math.floor(flowTurns.length / 2)} turns
          </button>
        )}
        {!askOnly && <>
        <button
          className="bb-action h-8 px-2.5 text-[11px]"
          disabled={!researchModeEnabled || ["pending", "running"].includes(researchRun?.status || "")}
          title={researchModeEnabled ? "Research low-confidence and unresolved graph nodes with external sources" : "Enable Research Mode in Settings"}
          onClick={startOnlineResearch}
        >
          {["pending", "running"].includes(researchRun?.status || "")
            ? `Researching gaps ${researchRun?.progress || 0}%`
            : "Research gaps"}
        </button>
        {["pending", "running"].includes(researchRun?.status || "") && (
          <button className="bb-action h-8 px-2 text-[10px]" onClick={cancelOnlineResearch}>Cancel research</button>
        )}
        </>}
        {!askOnly && <>
        <select className="h-8 rounded-lg border border-border/50 bg-surface px-2 text-[11px] text-muted outline-none" value={filterType} onChange={(e) => setFilterType(e.target.value)}>
          <option value="brain_view">{t("filterBrainView")}</option>
          <option value="topics">{t("filterTopics")}</option>
          <option value="note">{t("filterNote")}</option>
          <option value="concept">{t("filterConcept")}</option>
          <option value="entity">{t("filterEntity")}</option>
          <option value="context">{t("filterContext")}</option>
          <option value="insight">{t("filterInsight")}</option>
          <option value="gap">{t("filterGap")}</option>
          <option value="attachment">{t("filterAttachment")}</option>
          <option value="study_path">{t("filterStudyPath")}</option>
          <option value="cluster">{t("filterCluster")}</option>
          <option value="source">{t("filterSource")}</option>
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
        </>}
      </div>

      {researchStatus && !askOnly && (
        <div className="border-b border-border/40 bg-surface px-4 py-1.5 text-center text-[11px] text-muted" role="status">
          {researchStatus}
        </div>
      )}

      {inference && !askOnly && (
        <div className="border-b border-border/40 bg-panel/80 px-4 py-3">
          <div className="mx-auto max-w-5xl rounded-xl border border-border/50 bg-surface/70 p-3">
            <div className="mb-1 flex items-center gap-2">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-accent">{t("graphInference")}</span>
              <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
            </div>
            <p className={`text-sm leading-relaxed ${inference.status === "error" ? "text-danger" : "text-foreground"}`}>{inference.answer}</p>
            {inference.status === "error" && (
              <p className="mt-2 rounded-lg bg-panel px-2 py-1 text-[11px] text-muted">
                Check Settings, AI / Provider and try again. Local Ollama needs a reachable URL and installed model; cloud mode needs a verified key, model, and consent.
              </p>
            )}
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
              {!flowActive && inference.status !== "error" && (
                <button className="bb-action px-3 py-1 text-[10px] font-semibold text-violet-600" onClick={startFlow}>
                  Continue in Flow
                </button>
              )}
              <button
                className="bb-action px-3 py-1 text-[10px] disabled:cursor-not-allowed disabled:opacity-50"
                disabled={
                  inferenceSaving
                  || inference.status === "saved_as_insight"
                  || (!inference.inferenceId && !flowSessionId)
                  || !["answered", "success", "sufficient_evidence", "insufficient_evidence"].includes(inference.status)
                }
                title={
                  inference.status === "insufficient_evidence"
                    ? "Create a knowledge gap from this unanswered question"
                    : "Create a grounded knowledge insight from this answer"
                }
                onClick={saveInferenceAsInsight}
              >
                {inferenceSaving ? "Creating..." : inference.status === "saved_as_insight" ? "Insight created" : "Create insight"}
              </button>
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

      {askOnly ? (
        <div className="flex flex-1 flex-col overflow-y-auto bg-background px-4 py-8 sm:px-6 sm:py-12 lg:px-10">
          <div className="mx-auto w-full max-w-6xl space-y-10">
            <section className="mx-auto w-full max-w-4xl text-center" aria-labelledby="ask-workspace-title">
              <div className="mx-auto mb-4 grid size-12 place-items-center rounded-xl border border-accent/30 bg-accent-soft text-lg font-semibold text-accent" aria-hidden="true">ASK</div>
              <h1 id="ask-workspace-title" className="text-3xl font-semibold leading-tight text-foreground sm:text-4xl">Ask BerryBrain</h1>
              <form
                className="mt-7 rounded-xl border border-border bg-panel p-2 sm:p-3"
                aria-label="Ask your knowledge graph"
                onSubmit={(event) => {
                  event.preventDefault();
                  void runInference();
                }}
              >
                <div className="flex min-w-0 items-center gap-2">
                  <input
                    ref={askInputRef}
                    type="text"
                    className="h-14 min-w-0 flex-1 rounded-lg border border-border bg-background px-4 text-base text-foreground outline-none placeholder:text-muted/60 focus:border-accent focus:outline focus:outline-3 focus:outline-accent/20"
                    placeholder="Ask your graph about its content or structure..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                  <VoicePromptButton value={query} onChange={setQuery} className="h-12 w-12" />
                  <button
                    type="submit"
                    className="bb-action bb-action--primary h-12 shrink-0 px-4 text-sm font-semibold sm:px-6"
                    disabled={inferLoading || !query.trim()}
                  >
                    {inferLoading ? "Thinking" : "Ask"}
                  </button>
                </div>
                {flowActive && (
                  <div className="mt-2 flex items-center justify-between border-t border-border px-1 pt-2 text-[11px] text-muted">
                    <span>Flow · {Math.floor(flowTurns.length / 2)} turns</span>
                    <div className="flex gap-2">
                      {inferLoading && <button type="button" className="font-semibold text-accent" onClick={cancelFlowRequest}>Cancel response</button>}
                      <button type="button" className="font-semibold text-muted hover:text-foreground" onClick={exitFlow}>Exit Flow</button>
                    </div>
                  </div>
                )}
              </form>
            </section>

            {inferLoading && (
              <div className="mx-auto flex max-w-4xl items-center justify-center gap-3 border-y border-border py-5" role="status">
                <span className="size-5 animate-spin rounded-full border-2 border-border border-t-accent" />
                <p className="text-sm font-medium text-muted">Grounding answer in your graph...</p>
              </div>
            )}

            {inference && !inferLoading && (
              <section className="mx-auto max-w-4xl border-y border-border py-6 text-left" aria-label="Graph answer" aria-live="polite">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold uppercase text-accent">BerryBrain answer</span>
                  <span className="rounded-full border border-border bg-surface px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
                </div>
                <p className={`whitespace-pre-wrap text-base leading-7 ${inference.status === "error" ? "text-danger" : "text-foreground"}`}>{inference.answer}</p>
                {!!inference.evidence?.length && (
                  <div className="mt-5 space-y-2">
                    <h2 className="text-[11px] font-semibold uppercase text-muted">Evidence</h2>
                    {inference.evidence.slice(0, 6).map((item, index) => (
                      <div key={index} className="border-l-2 border-accent/40 pl-3 text-xs leading-5 text-muted">{formatInferenceEvidence(item)}</div>
                    ))}
                  </div>
                )}
                {!!relatedInferenceNodes.length && (
                  <div className="mt-5 flex flex-wrap gap-2">
                    {relatedInferenceNodes.map((node) => {
                      const recordId = graphNodeRecordId(graphData?.nodes.find((item) => item.id === node.id));
                      return <button key={node.id} className="bb-action px-3 py-1.5 text-xs" onClick={() => {
                        if (recordId) window.location.href = appPath(`/graph/nodes/${recordId}`);
                      }}>{node.label}</button>;
                    })}
                  </div>
                )}
                <div className="mt-5 flex flex-wrap items-center gap-2">
                  {!flowActive && inference.status !== "error" && <button className="bb-action px-3 py-1.5 text-xs font-semibold" onClick={startFlow}>Continue in Flow</button>}
                  <button
                    className="bb-action px-3 py-1.5 text-xs"
                    disabled={inferenceSaving || inference.status === "saved_as_insight" || (!inference.inferenceId && !flowSessionId)}
                    onClick={saveInferenceAsInsight}
                  >{inferenceSaving ? "Creating..." : inference.status === "saved_as_insight" ? "Insight created" : "Create insight"}</button>
                  <button className="px-2 py-1.5 text-xs text-muted hover:text-foreground" onClick={() => setInference(null)}>Clear answer</button>
                  {(inference.provider || inference.model) && <span className="ml-auto text-[10px] text-muted">{inference.provider || "provider"}{inference.model ? ` · ${inference.model}` : ""}</span>}
                </div>
                {inferenceSaveStatus && <p className="mt-3 text-xs text-muted">{inferenceSaveStatus}</p>}
              </section>
            )}

            {flowTurns.length > 0 && (
              <section className="mx-auto max-w-4xl" aria-label="Ask conversation">
                <div className="mb-4 flex items-center justify-between"><h2 className="text-xs font-semibold uppercase text-muted">Conversation</h2><span className="text-[11px] text-muted">{Math.floor(flowTurns.length / 2)} turns</span></div>
                <div className="space-y-3">
                  {flowTurns.map((turn) => <article key={turn.id} className={`max-w-[90%] rounded-lg border border-border px-4 py-3 ${turn.role === "user" ? "ml-auto bg-accent-soft" : "bg-panel"}`}>
                    <div className="mb-1 text-[10px] font-semibold uppercase text-muted">{turn.role === "user" ? "You" : "BerryBrain"}</div>
                    <p className="whitespace-pre-wrap text-sm leading-6 text-foreground">{turn.content}</p>
                  </article>)}
                </div>
              </section>
            )}

            {(suggestionsLoading || (askSuggestions?.questions.length || 0) > 0) && (
              <section aria-label="Suggested questions">
                <div className="mb-4 flex items-end justify-between gap-4">
                  <div>
                    <h2 className="text-sm font-semibold text-foreground">Suggested next questions</h2>
                    {askSuggestions && <p className="mt-1 text-[11px] text-muted">{askSuggestions.graph.nodes} nodes · {askSuggestions.graph.edges} relationships</p>}
                  </div>
                  {!suggestionsLoading && (askSuggestions?.questions.length || 0) > 1 && <div className="flex gap-2">
                    <button type="button" className="bb-action grid size-9 place-items-center text-lg" aria-label="Previous suggestions" onClick={() => scrollSuggestions(-1)}>‹</button>
                    <button type="button" className="bb-action grid size-9 place-items-center text-lg" aria-label="Next suggestions" onClick={() => scrollSuggestions(1)}>›</button>
                  </div>}
                </div>
                {suggestionsLoading ? <div className="h-32 animate-pulse rounded-xl border border-border bg-panel" /> : (
                  <div ref={suggestionTrackRef} className="grid snap-x snap-mandatory auto-cols-[minmax(min(19rem,82vw),1fr)] grid-flow-col gap-3 overflow-x-auto pb-3">
                    {askSuggestions?.questions.map((item) => <button key={item.id} className="bb-card bb-card--interactive min-h-32 snap-start p-4 text-left" onClick={() => void runInference(item.prompt)}>
                      <span className="block text-[10px] font-semibold uppercase text-accent">{item.topic}</span>
                      <span className="mt-3 block text-sm leading-6 text-foreground">{item.prompt}</span>
                      <span className="mt-3 block text-[10px] uppercase text-muted">{item.source.replaceAll("_", " ")}</span>
                    </button>)}
                  </div>
                )}
              </section>
            )}

            {(askSuggestions?.topics.length || 0) > 0 && (
              <section className="border-t border-border pt-7 text-center" aria-label="Graph topics">
                <h2 className="mb-4 text-xs font-semibold uppercase text-muted">Topic cloud</h2>
                <div className="flex flex-wrap items-center justify-center gap-2">
                  {askSuggestions?.topics.map((topic, index) => <button key={topic} className="rounded-full border border-border bg-panel px-3 py-1.5 text-foreground hover:border-accent hover:text-accent" style={{ fontSize: `${Math.max(11, 16 - (index % 5))}px` }} onClick={() => { setQuery(topic); askInputRef.current?.focus(); }}>{topic}</button>)}
                </div>
              </section>
            )}
          </div>
        </div>
      ) : (
      <div className="relative flex-1 overflow-hidden bg-background">
      {error ? (
        <div className="flex h-full items-center justify-center text-sm text-danger">{t("graphLoadError")}</div>
      ) : graphData ? (
          filtered.nodes.length === 0 ? (
            <div className="flex h-full flex-col items-center justify-center gap-3 px-8 text-center">
              {pipelineDiag.map((d) => (
                <div key={d.code} className="text-xs font-medium text-warning">
                  {d.text}
                </div>
              ))}
              {graphData && graphData.nodes.length > 0 && isFilterHidden(graphData, { filterType, filterStatus, filterProvider, filterConfidence }) && (
                <p className="text-xs text-muted/60">{t("filterHidden")}</p>
              )}
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
              onOpen={openNodeDetail}
            />
          ) : (
            <GraphCanvas
              data={filtered}
              onNavigate={(path) => {
                onClose();
                setTimeout(() => onNavigate(path), 100);
              }}
              onSelect={(id) => {
                if (id) prepareNodeDetail(id);
                else setSelectedId(null);
              }}
              onOpen={openNodeDetail}
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
          <div className="absolute right-4 top-3 z-20 max-h-[calc(100%-1.5rem)] w-72 overflow-y-auto rounded-lg bg-panel/95 p-3 shadow-lg ring-1 ring-border/30 backdrop-blur">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[11px] font-medium text-foreground">{t("legend")}</span>
              <button className="text-[10px] text-muted hover:text-foreground" onClick={() => setShowLegend(false)}>X</button>
            </div>
            <div className="space-y-1 text-[10px]">
              <div className="mb-1 font-medium text-foreground/80">Shape = ontology type</div>
              {NODE_LEGEND.map(([type, symbol, label]) => (
                <div key={type} className="flex items-center gap-2">
                  <span className={`grid size-4 place-items-center text-[13px] ${type === "note" ? "text-accent" : "text-foreground/70"}`}>{symbol}</span>
                  <span className="text-muted/70">{label}</span>
                </div>
              ))}
              <div className="my-2 h-px bg-border/40" />
              <div className="mb-1 font-medium text-foreground/80">Color = semantic context</div>
              {Object.values(graphData?.palette || {}).map((color) => (
                <div key={color.colorId} className="flex items-center gap-2">
                  <span className="inline-block size-2.5 rounded-full" style={{ background: color.lightHex, border: `1px solid ${color.border}` }} />
                  <span className="truncate text-muted/70">{color.namespace} · {color.colorId.replace(/^(semantic|vault)-/, "")}</span>
                </div>
              ))}
              <div className="text-muted/60">Dashed border = no connections</div>
              <div className="text-muted/60">Halo = selected or highlighted</div>
              <div className="my-2 h-px bg-border/40" />
              <div className="mb-1 font-medium text-foreground/80">Arrow = ontology relationship</div>
              {graphEdgeTypes.map((type) => (
                <div key={type} className="grid grid-cols-[16px_minmax(0,1fr)] items-start gap-2 py-0.5">
                  <span className="inline-block h-0.5 w-4 rounded" style={{ background: edgeColor(type) }} />
                  <span className="min-w-0 text-muted/70"><strong className="block break-words font-medium text-foreground/75">{type.replaceAll("_", " ")}</strong>{EDGE_ROLES[type] || "Typed ontology relation"}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      )}

      {selectedNode && showDetail && (
        <div className="absolute inset-x-0 bottom-0 top-[49px] z-30 flex flex-col border-l border-border/50 bg-panel/98 shadow-xl backdrop-blur sm:left-auto sm:w-[min(720px,58vw)]">
          <div className="flex flex-shrink-0 items-start justify-between gap-3 border-b border-border/50 bg-surface/50 p-5">
            <div className="min-w-0">
              <div className="mb-1 text-[11px] font-bold uppercase tracking-widest text-accent">{humanNodeType(selectedNode.type)}</div>
              <h3 className="break-words text-base font-semibold leading-snug text-foreground">{nodeSummary?.title || selectedNode.label}</h3>
              <div className="mt-2 flex flex-wrap gap-1">
                <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{humanStatus(nodeSummary?.status || selectedNode.status)}</span>
                <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{formatConfidence(nodeSummary?.confidence ?? selectedNode.confidence)}</span>
                <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{humanOrigin(nodeSummary?.createdBy || selectedNode.createdBy)}</span>
              </div>
            </div>
            <button className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-border/50 text-[10px] text-muted hover:bg-border hover:text-foreground" onClick={() => setShowDetail(false)}>✕</button>
          </div>
          
          <div className="flex-1 overflow-y-auto p-5">
            {summaryLoading ? (
              <div className="text-xs text-muted">{t("loadingNodeSummary")}</div>
            ) : (
              <div className="space-y-4 text-[12px] text-muted/80">
                <section>
                  <div className="mb-2 flex items-center justify-between gap-2">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-foreground/80">What this is</div>
                    <button
                      className="bb-action px-3 py-1.5 text-[10px] font-medium text-accent"
                      onClick={() => runInference(`Explain "${nodeSummary?.title || selectedNode.label}" and show the evidence behind it.`)}
                    >
                      Ask about this
                    </button>
                  </div>
                  <div className="rounded-xl border border-border/40 bg-surface/40 p-4 text-[13px] leading-relaxed text-foreground/90 shadow-sm">
                    {nodeSummary?.aiSummary || nodeSummary?.summary || selectedNode.aiSummary || selectedNode.summary || t("summaryNotGenerated")}
                  </div>
                </section>
                {nodeSummary?.whyThisExists && (
                  <div className="text-[11px] italic text-muted/60">{nodeSummary.whyThisExists}</div>
                )}
                <section className="border-t border-border/30 pt-4">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-foreground/80">Edit node</div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <label className="text-[10px] font-medium uppercase tracking-wide text-muted/70">
                      Type
                      <select
                        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                        value={nodeEdit.type}
                        onChange={(event) => setNodeEdit((current) => ({ ...current, type: event.target.value }))}
                      >
                        <option value="note">Note</option>
                        <option value="concept">Concept</option>
                        <option value="entity">Entity</option>
                        <option value="topic">Topic</option>
                        <option value="source">Source</option>
                        <option value="attachment">Attachment</option>
                        <option value="insight">Insight</option>
                        <option value="context">Context</option>
                        <option value="gap">Gap</option>
                        <option value="study_path">Study path</option>
                        <option value="cluster">Cluster</option>
                      </select>
                    </label>
                    <label className="text-[10px] font-medium uppercase tracking-wide text-muted/70">
                      Label
                      <input
                        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                        value={nodeEdit.label}
                        onChange={(event) => setNodeEdit((current) => ({ ...current, label: event.target.value }))}
                      />
                    </label>
                    <label className="text-[10px] font-medium uppercase tracking-wide text-muted/70">
                      Title
                      <input
                        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                        value={nodeEdit.title}
                        onChange={(event) => setNodeEdit((current) => ({ ...current, title: event.target.value }))}
                      />
                    </label>
                    <label className="text-[10px] font-medium uppercase tracking-wide text-muted/70">
                      Status
                      <select
                        className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                        value={nodeEdit.status}
                        onChange={(event) => setNodeEdit((current) => ({ ...current, status: event.target.value }))}
                      >
                        <option value="suggested">Suggested</option>
                        <option value="confirmed">Confirmed</option>
                        <option value="ignored">Ignored</option>
                      </select>
                    </label>
                  </div>
                  <label className="mt-2 block text-[10px] font-medium uppercase tracking-wide text-muted/70">
                    Source
                    <input
                      className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                      value={nodeEdit.source}
                      onChange={(event) => setNodeEdit((current) => ({ ...current, source: event.target.value }))}
                    />
                  </label>
                  <label className="mt-2 block text-[10px] font-medium uppercase tracking-wide text-muted/70">
                    Summary
                    <textarea
                      className="mt-1 min-h-24 w-full resize-y rounded-lg border border-border bg-surface p-2 text-xs normal-case tracking-normal text-foreground outline-none focus:border-accent"
                      value={nodeEdit.summary}
                      onChange={(event) => setNodeEdit((current) => ({ ...current, summary: event.target.value }))}
                    />
                  </label>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <button className="bb-action px-3 py-1.5 text-[10px]" disabled={nodeEditSaving} onClick={saveGraphNodeEdits}>
                      {nodeEditSaving ? "Saving..." : "Save node"}
                    </button>
                    {nodeEditStatus && <span className="text-[10px] text-muted">{nodeEditStatus}</span>}
                  </div>
                </section>
                <div className="grid grid-cols-2 gap-2">
                  <Meta label={t("status")} value={humanStatus(nodeSummary?.status || selectedNode.status)} />
                  <Meta label={t("confidence")} value={formatConfidence(nodeSummary?.confidence ?? selectedNode.confidence)} />
                  <Meta label={t("origin")} value={humanOrigin(nodeSummary?.createdBy || selectedNode.createdBy)} />
                  <Meta label={t("model")} value={nodeSummary?.createdByModel || selectedNode.createdByModel || "-"} />
                  <Meta label="Review" value={humanStatus(nodeSummary?.validationStatus || selectedNode.validationStatus || "unvalidated")} />
                  <Meta label="Evidence" value={formatEvidenceLabel(nodeSummary?.sourceQuality || selectedNode.sourceQuality || "note_only")} />
                </div>

                <section className="border-t border-border/30 pt-4">
                  <div className="mb-3 flex items-center justify-between gap-2">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-foreground/80">What BerryBrain understands</div>
                    <span className="rounded-full bg-surface px-2 py-0.5 text-[9px] uppercase text-muted">
                      {humanSemanticState(semanticAnalysis?.state)}
                    </span>
                  </div>
                  {semanticAnalysis?.analysis ? (
                    <div className="space-y-3 border-l-2 border-accent/40 pl-3">
                      <SemanticText label="Meaning here" value={semanticAnalysis.analysis.meaning_in_context} />
                      <SemanticText label="Why it matters" value={semanticAnalysis.analysis.why_it_matters_here} />
                      <SemanticList label="Supported findings" values={semanticAnalysis.analysis.supported_findings} />
                      <SemanticList label="Inferences" values={semanticAnalysis.analysis.inferences} />
                      <SemanticList label="Uncertainties" values={semanticAnalysis.analysis.uncertainties} />
                      <SemanticList
                        label="Evidence"
                        values={semanticAnalysis.analysis.evidence.map((item) => (
                          typeof item === "string"
                            ? item
                            : [item.claim, item.source, item.reference].filter(Boolean).join(" · ")
                        ))}
                      />
                      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[9px] text-muted/60">
                        <span>Version {semanticAnalysis.profileVersion || 1}</span>
                        <span>{semanticAnalysis.historyCount} saved versions</span>
                        <span>{semanticAnalysis.analysis.provider} · {semanticAnalysis.analysis.model}</span>
                      </div>
                    </div>
                  ) : (
                    <p className="border-l-2 border-border pl-3 text-[11px] leading-relaxed text-muted">
                      {semanticStateMessage(semanticAnalysis?.state)}
                    </p>
                  )}
                </section>

                <section className="border-t border-border/30 pt-3">
                  <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-foreground/70">Your notes about this item</div>
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

                <section className="border-t border-border/30 pt-4">
                  <div className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-foreground/80">
                    Connections
                  </div>
                <div className="space-y-3">
                  {(nodeSummary?.connections?.length ? nodeSummary.connections : selectedEdges).slice(0, 6).map((edge, index) => {
                    const simpleEdge = edge as GraphEdge;
                    const detailedEdge = edge as NodeSummary["connections"][number];
                    const other = simpleEdge.source === selectedId ? simpleEdge.target : simpleEdge.source;
                    const otherNode = graphData?.nodes.find((n) => n.id === other);
                    const isInsightEdge = (detailedEdge.type || simpleEdge.type) === "insight_suggested";
                    return (
                      <div key={`${detailedEdge.id || simpleEdge.id || index}`} className="rounded-lg bg-surface p-2">
                        <div className="mb-1 flex items-center gap-2">
                          <span className="inline-block h-0.5 w-4 rounded" style={{ background: edgeColor(detailedEdge.type || simpleEdge.type) }} />
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
                            <button disabled={actionLoading === `confirm-connection-${detailedEdge.id}`} className="rounded-md bg-accent px-2 py-0.5 text-[9px] text-white disabled:opacity-50" onClick={() => updateEdgeStatus(detailedEdge.id, "confirmed")}>Confirm</button>
                          )}
                          {!isInsightEdge && !!detailedEdge.id && (detailedEdge.status || simpleEdge.status || "suggested") === "suggested" && (
                            <button disabled={actionLoading === `ignore-connection-${detailedEdge.id}`} className="rounded-md bg-panel px-2 py-0.5 text-[9px] text-muted hover:text-foreground disabled:opacity-50" onClick={() => updateEdgeStatus(detailedEdge.id, "ignored")}>Ignore</button>
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
                      if (action.id === "retry-semantic-analysis") processSemanticAnalysis("retry");
                      if (action.id === "regenerate-semantic-analysis") processSemanticAnalysis("regenerate");
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

function SemanticText({ label, value }: { label: string; value: string }) {
  if (!value) return null;
  return (
    <div>
      <div className="mb-1 text-[9px] font-semibold uppercase text-foreground/60">{label}</div>
      <p className="text-[11px] leading-relaxed text-foreground/80">{value}</p>
    </div>
  );
}

function SemanticList({ label, values }: { label: string; values: string[] }) {
  const visible = values.filter(Boolean);
  if (!visible.length) return null;
  return (
    <div>
      <div className="mb-1 text-[9px] font-semibold uppercase text-foreground/60">{label}</div>
      <ul className="space-y-1 text-[11px] leading-relaxed text-foreground/75">
        {visible.map((value, index) => <li key={`${label}-${index}`}>• {value}</li>)}
      </ul>
    </div>
  );
}

function humanSemanticState(state?: string) {
  const states: Record<string, string> = {
    completed: "Ready",
    pending: "Queued",
    running: "Analyzing",
    failed: "Needs retry",
    stale: "Update available",
    needs_review: "Needs review",
    not_configured: "AI setup required",
  };
  return states[state || ""] || "Waiting";
}

function semanticStateMessage(state?: string) {
  const messages: Record<string, string> = {
    pending: "Semantic analysis is queued and will appear here automatically.",
    running: "BerryBrain is analyzing this item and its connections.",
    failed: "The last analysis failed. Use Retry analysis below after checking AI settings.",
    stale: "The source changed. A refreshed analysis can be generated.",
    needs_review: "The analysis needs review before BerryBrain can treat it as reliable.",
    not_configured: "Complete the required AI setup to generate semantic understanding.",
  };
  return messages[state || ""] || "Semantic understanding has not been generated yet.";
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
  if (action.id === "retry-semantic-analysis" || action.id === "regenerate-semantic-analysis") {
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
