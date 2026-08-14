"use client";

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { Route } from "next";
import Link from "next/link";
import { GraphCanvas, useGraphData, type GraphLayoutMode } from "./graph-view";
import { formatEvidenceLabel } from "./graph-formatters";
import { t } from "@/i18n";
import { apiFetch, appPath } from "@/contexts/workspace-context";
import { diagnosticMessages, isFilterHidden, type PipelineDiagnostic } from "@/lib/diagnostics";
import { VoicePromptButton } from "./voice-prompt-button";
import {
  AlertTriangle,
  ArrowLeft,
  BookOpen,
  BrainCircuit,
  ChevronDown,
  Filter,
  Focus,
  Home,
  LayoutDashboard,
  Lightbulb,
  List,
  Maximize2,
  Network,
  RefreshCw,
  Settings,
  Sparkles,
  ThumbsDown,
  ThumbsUp,
} from "lucide-react";

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

function GraphFilter({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: Array<readonly [string, string]> }) {
  return (
    <label className="grid gap-1 text-[11px] font-medium text-muted">
      {label}
      <select className="bb-field h-9 text-xs" value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(([optionValue, optionLabel]) => <option key={optionValue} value={optionValue}>{optionLabel}</option>)}
      </select>
    </label>
  );
}

function ToolbarAction({ icon, title, description, onClick, disabled = false }: { icon: ReactNode; title: string; description: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button type="button" role="menuitem" className="flex w-full gap-3 rounded-md px-3 py-2 text-left hover:bg-surface disabled:cursor-not-allowed disabled:opacity-45" onClick={onClick} disabled={disabled}>
      <span className="mt-0.5 text-accent">{icon}</span>
      <span><span className="block text-xs font-semibold text-foreground">{title}</span><span className="mt-0.5 block text-[11px] leading-4 text-muted">{description}</span></span>
    </button>
  );
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

type GraphMutationStatus = {
  operation: "node_deleted";
  message: string;
  jobIds: number[];
  phase: "working" | "completed" | "failed";
  impact?: { invalidatedInsights?: number; incidentEdgeCount?: number };
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
  onOpenSettings,
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
  onOpenSettings?: () => void;
}) {
  const { data, error, reload } = useGraphData(apiUrl);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [showGraphActions, setShowGraphActions] = useState(false);
  const [viewMode, setViewMode] = useState<"visual" | "list">(() => {
    if (typeof window === "undefined") return "visual";
    return localStorage.getItem("bb_graph_view_mode") === "list" ? "list" : "visual";
  });
  const [query, setQuery] = useState("");
  const askInputRef = useRef<HTMLInputElement>(null);
  const suggestionTrackRef = useRef<HTMLDivElement>(null);
  const autoSubmittedQueryRef = useRef("");
  const [filterType, setFilterType] = useState("brain_view");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterProvider, setFilterProvider] = useState("all");
  const [filterConfidence, setFilterConfidence] = useState(0);
  const [pipelineDiag, setPipelineDiag] = useState<{ code: string; text: string }[]>([]);
  const [graphPipeline, setGraphPipeline] = useState<{ active: number; degraded: number; estimatedRemainingSeconds: number | null; estimatedRemainingSecondsP95: number | null }>({ active: 0, degraded: 0, estimatedRemainingSeconds: null, estimatedRemainingSecondsP95: null });
  const [graphMutationStatus, setGraphMutationStatus] = useState<GraphMutationStatus | null>(null);
  useEffect(() => {
    if (askOnly || apiUrl === "__demo__" || typeof window === "undefined") return;
    const raw = sessionStorage.getItem("bb_graph_mutation_status");
    if (!raw) return;
    let saved: Omit<GraphMutationStatus, "phase">;
    try {
      saved = JSON.parse(raw) as Omit<GraphMutationStatus, "phase">;
    } catch {
      sessionStorage.removeItem("bb_graph_mutation_status");
      return;
    }
    if (!Array.isArray(saved.jobIds) || !saved.jobIds.length) return;
    let cancelled = false;
    let finished = false;
    setGraphMutationStatus({ ...saved, phase: "working" });
    const refreshStatus = async () => {
      try {
        const response = await apiFetch(`${apiUrl}/api/v1/jobs?limit=200`);
        if (!response.ok) return;
        const payload = await response.json();
        const tracked = (payload.jobs || []).filter((job: { id?: number }) => saved.jobIds.includes(Number(job.id)));
        const failed = tracked.some((job: { status?: string }) => ["failed", "dead_letter"].includes(job.status || ""));
        const complete = tracked.length === saved.jobIds.length && tracked.every((job: { status?: string }) => ["completed", "superseded"].includes(job.status || ""));
        if (cancelled || (!failed && !complete)) return;
        finished = true;
        sessionStorage.removeItem("bb_graph_mutation_status");
        setGraphMutationStatus({
          ...saved,
          phase: failed ? "failed" : "completed",
          message: failed
            ? "The node was deleted, but part of the affected-subgraph recalculation needs attention."
            : "Node deletion and affected-subgraph recalculation completed.",
        });
        if (complete) void reload();
      } catch {
        // Keep the visible working state while the job endpoint is temporarily unavailable.
      }
    };
    void refreshStatus();
    const interval = window.setInterval(() => {
      if (!finished) void refreshStatus();
    }, 3000);
    return () => { cancelled = true; window.clearInterval(interval); };
  }, [apiUrl, askOnly, reload]);
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
    apiFetch("/api/v1/vault/debug/vault-graph-pipeline")
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
  useEffect(() => {
    if (askOnly || apiUrl === "__demo__") return;
    let cancelled = false;
    const loadProgress = () => {
      apiFetch(`${apiUrl}/api/v1/jobs/pipeline-progress`)
        .then((response) => response.ok ? response.json() : null)
        .then((payload) => {
          if (cancelled || !payload) return;
          const notes = Array.isArray(payload.notes) ? payload.notes : [];
          const active = notes.filter((item: { state?: string }) => ["waiting", "processing"].includes(item.state || "")).length;
          const degraded = notes.filter((item: { graphState?: string }) => item.graphState === "degraded").length;
          const estimates = notes.map((item: { estimatedRemainingSeconds?: number | null }) => item.estimatedRemainingSeconds).filter((value: unknown): value is number => typeof value === "number");
          const upperEstimates = notes.map((item: { estimatedRemainingSecondsP95?: number | null }) => item.estimatedRemainingSecondsP95).filter((value: unknown): value is number => typeof value === "number");
          setGraphPipeline({ active, degraded, estimatedRemainingSeconds: estimates.length ? Math.max(...estimates) : null, estimatedRemainingSecondsP95: upperEstimates.length ? Math.max(...upperEstimates) : null });
        })
        .catch(() => {});
    };
    loadProgress();
    const interval = window.setInterval(loadProgress, 5000);
    return () => { cancelled = true; window.clearInterval(interval); };
  }, [apiUrl, askOnly]);
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
  const [researchModeEnabled, setResearchModeEnabled] = useState(false);
  const [researchRun, setResearchRun] = useState<ResearchRun | null>(null);
  const [researchStatus, setResearchStatus] = useState("");
  const [flowSessionId, setFlowSessionId] = useState<string | null>(null);
  const [flowTurns, setFlowTurns] = useState<FlowTurn[]>([]);
  const [flowActive, setFlowActive] = useState(false);
  const [askSuggestions, setAskSuggestions] = useState<AskSuggestionPayload | null>(null);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const [askFeedback, setAskFeedback] = useState<"" | "upvoted" | "downvoted" | "error">("");

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
  function changeLayout(mode: GraphLayoutMode) {
    setLayoutMode(mode);
    if (typeof window !== "undefined") localStorage.setItem("bb_graph_layout", mode);
    setPan({ x: 0, y: 0 });
    setZoom(1);
  }

  function toggleInsightNodes() {
    if (showInsightNodes && selectedNode?.type === "insight") {
      setSelectedId(null);
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
    setAskFeedback("");
    try {
      if (flowActive && flowSessionId) {
        const response = await apiFetch(`${apiUrl}/api/v1/ask/sessions/${flowSessionId}/turns`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ content: text }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          const detail = payload.detail;
          if (response.status === 503 && typeof detail === "object" && detail?.code === "provider_unavailable") {
            setInference({
              status: "provider_unavailable",
              question: text,
              answer: detail.message || "The configured AI provider did not return an answer.",
            });
            return;
          }
          throw new Error(typeof detail === "string" ? detail : `Flow failed (HTTP ${response.status}).`);
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
        const detail = payload.detail;
        if (response.status === 503 && typeof detail === "object" && detail?.code === "provider_unavailable") {
          setInference({
            status: "provider_unavailable",
            question: text,
            answer: detail.message || "The configured AI provider did not return an answer.",
          });
          return;
        }
        const message = typeof detail === "string"
          ? detail
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

  async function recordAskFeedback(action: "upvoted" | "downvoted") {
    if (apiUrl === "__demo__" || askFeedback === action) return;
    const assistantTurn = [...flowTurns].reverse().find((turn) => turn.role === "assistant");
    const endpoint = flowActive && flowSessionId && assistantTurn
      ? `${apiUrl}/api/v1/ask/sessions/${flowSessionId}/turns/${assistantTurn.id}/feedback`
      : inference?.inferenceId
        ? `${apiUrl}/api/v1/graph/inferences/${inference.inferenceId}/feedback`
        : "";
    if (!endpoint) return;
    try {
      const response = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action }),
      });
      if (!response.ok) throw new Error("Answer feedback could not be recorded.");
      setAskFeedback(action);
    } catch {
      setAskFeedback("error");
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

  function scrollSuggestions(direction: -1 | 1) {
    const track = suggestionTrackRef.current;
    if (!track) return;
    track.scrollBy({ left: direction * track.clientWidth * 0.82, behavior: "smooth" });
  }

  const activeFilterCount = [
    filterType !== "brain_view",
    filterStatus !== "all",
    filterProvider !== "all",
    filterConfidence > 0,
  ].filter(Boolean).length;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <div className={`bb-graph-toolbar relative z-40 shrink-0 border-b border-border bg-panel px-3 py-2 text-xs lg:px-4 ${askOnly ? "is-ask-only" : ""}`}>
        <div className="bb-graph-toolbar__left">
          <button className="bb-icon-button" onClick={askOnly ? (onOpenHome || onClose) : onClose} aria-label={askOnly ? "Back to Home" : "Back"} title={askOnly ? "Back to Home" : "Back"}>
            <ArrowLeft className="size-4" />
          </button>
          {!askOnly && <div className="mr-2 min-w-0">
            <h2 className="flex items-center gap-2 text-sm font-semibold text-foreground"><Network className="size-4 text-accent" />{t("graphTitle")}</h2>
            {graphData && (
              <div className="text-[10px] text-muted/60">
                {graphData.nodes.length} {t("nodes")} · {graphData.edges.length} {t("edges")} · {graphData.stats?.orphan_count ?? 0} {t("orphans")}
              </div>
            )}
          </div>}
          {askOnly && <div className="flex items-center gap-1">
            <button className="bb-action h-8 gap-1.5 px-2.5 text-[11px]" onClick={onOpenHome || onClose}><Home className="size-3.5" />Home</button>
            <button className="bb-action h-8 gap-1.5 px-2.5 text-[11px]" onClick={onOpenGraph || (() => { window.location.href = appPath("/brain?graph=open"); })}><Network className="size-3.5" />Graph</button>
          </div>}
        </div>
        {!askOnly && <form
          className={`bb-graph-toolbar__ask relative z-50 flex min-w-0 items-center gap-2 rounded-lg border p-1.5 ${
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
          ><Maximize2 className="size-4" /></button>}
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
        {!askOnly && (
          <div className="bb-graph-toolbar__right">
            <div className="bb-segmented" aria-label="Graph view">
              <button className={viewMode === "visual" ? "is-active" : ""} onClick={() => { setViewMode("visual"); localStorage.setItem("bb_graph_view_mode", "visual"); }} aria-label="Visual graph" title="Visual graph"><Network className="size-3.5" /></button>
              <button className={viewMode === "list" ? "is-active" : ""} onClick={() => { setViewMode("list"); localStorage.setItem("bb_graph_view_mode", "list"); }} aria-label="Graph list" title="Graph list"><List className="size-3.5" /></button>
            </div>
            <label className="bb-compact-select" title="Graph layout">
              <LayoutDashboard className="size-3.5" />
              <select value={layoutMode} onChange={(e) => changeLayout(e.target.value as GraphLayoutMode)} aria-label="Graph layout">
                <option value="brain">{t("layoutBrain")}</option>
                <option value="radial">{t("layoutRadial")}</option>
                <option value="type">{t("layoutType")}</option>
                <option value="connections">{t("layoutConnections")}</option>
              </select>
            </label>
            <button className="bb-icon-button" onClick={() => { setPan({ x: 0, y: 0 }); setZoom(1); setSelectedId(null); }} aria-label={t("center")} title={t("center")}><Focus className="size-4" /></button>
            <div className="relative">
              <button className={`bb-toolbar-menu ${activeFilterCount ? "bb-action--active" : ""}`} onClick={() => { setShowFilters((value) => !value); setShowGraphActions(false); }} aria-expanded={showFilters}><Filter className="size-3.5" /><span>Filters</span>{activeFilterCount > 0 && <span className="bb-count">{activeFilterCount}</span>}<ChevronDown className="size-3" /></button>
              {showFilters && (
                <div className="bb-toolbar-popover right-0 w-[min(92vw,420px)]" role="dialog" aria-label="Graph filters">
                  <div className="grid gap-3 sm:grid-cols-2">
                    <GraphFilter label="Node type" value={filterType} onChange={setFilterType} options={[["brain_view", t("filterBrainView")], ["topics", t("filterTopics")], ["note", t("filterNote")], ["concept", t("filterConcept")], ["entity", t("filterEntity")], ["context", t("filterContext")], ["insight", t("filterInsight")], ["gap", t("filterGap")], ["attachment", t("filterAttachment")], ["study_path", t("filterStudyPath")], ["cluster", t("filterCluster")], ["source", t("filterSource")]]} />
                    <GraphFilter label="Status" value={filterStatus} onChange={setFilterStatus} options={[["all", "All statuses"], ["suggested", t("suggested")], ["confirmed", t("confirmed")], ["ignored", t("ignored")]]} />
                    <GraphFilter label="Origin" value={filterProvider} onChange={setFilterProvider} options={[["all", "All origins"], ["ai", t("ai")], ["deterministic", t("system")], ["backlink", t("backlink")]]} />
                    <GraphFilter label="Minimum confidence" value={String(filterConfidence)} onChange={(value) => setFilterConfidence(Number(value))} options={[["0", "Any confidence"], ["90", "90%+"], ["70", "70%+"], ["50", "50%+"]]} />
                  </div>
                  <button className="bb-action mt-3 h-8 px-3 text-[11px]" onClick={() => { setFilterType("brain_view"); setFilterStatus("all"); setFilterProvider("all"); setFilterConfidence(0); }}>Clear filters</button>
                </div>
              )}
            </div>
            <div className="relative">
              <button className="bb-toolbar-menu" onClick={() => { setShowGraphActions((value) => !value); setShowFilters(false); }} aria-expanded={showGraphActions}><Sparkles className="size-3.5" /><span>Knowledge</span><ChevronDown className="size-3" /></button>
              {showGraphActions && (
                <div className="bb-toolbar-popover right-0 w-[min(92vw,360px)]" role="menu" aria-label="Knowledge actions">
                  <ToolbarAction icon={<RefreshCw className="size-4" />} title="Refresh graph" description="Recalculate the graph from current vault evidence." onClick={() => { setShowGraphActions(false); void expandGraph(); }} />
                  <ToolbarAction icon={<Lightbulb className="size-4" />} title={showInsightNodes ? "Hide insight proposals" : "Show insight proposals"} description="Review AI-proposed knowledge before accepting it." onClick={() => { setShowGraphActions(false); toggleInsightNodes(); }} />
                  <ToolbarAction icon={<BrainCircuit className="size-4" />} title="Research Gaps" description={researchModeEnabled ? "Investigate unresolved or low-confidence graph areas using external sources." : "External research is off. Enable Research Mode in Settings first."} disabled={!researchModeEnabled || ["pending", "running"].includes(researchRun?.status || "")} onClick={() => { setShowGraphActions(false); void startOnlineResearch(); }} />
                  <ToolbarAction icon={<BookOpen className="size-4" />} title="Legend" description="Open node geometry and ontology edge meanings." onClick={() => { setShowGraphActions(false); setShowLegend(true); }} />
                </div>
              )}
            </div>
            {flowActive && <button className="bb-action h-8 px-2.5 text-[11px] text-accent" onClick={exitFlow}>Exit Flow · {Math.floor(flowTurns.length / 2)}</button>}
          </div>
        )}
      </div>

      {graphMutationStatus && !askOnly && (
        <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface px-4 py-2 text-[11px]" role="status" aria-live="polite">
          <RefreshCw className={`size-3.5 ${graphMutationStatus.phase === "failed" ? "text-danger" : "text-accent"} ${graphMutationStatus.phase === "working" ? "animate-spin" : ""}`} />
          <span className="font-medium text-foreground">{graphMutationStatus.message}</span>
          {graphMutationStatus.impact?.invalidatedInsights ? <span className="text-muted">{graphMutationStatus.impact.invalidatedInsights} dependent insight{graphMutationStatus.impact.invalidatedInsights === 1 ? "" : "s"} invalidated</span> : null}
          {graphMutationStatus.phase !== "working" && <button type="button" className="ml-auto text-xs text-muted hover:text-foreground" onClick={() => setGraphMutationStatus(null)}>Dismiss</button>}
        </div>
      )}

      {!askOnly && (graphPipeline.active > 0 || graphPipeline.degraded > 0) && (
        <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface px-4 py-2 text-[11px]" role="status">
          <RefreshCw className={`size-3.5 text-accent ${graphPipeline.active ? "animate-spin" : ""}`} />
          <span className="font-medium text-foreground">
            {graphPipeline.active > 0 ? `${graphPipeline.active} note${graphPipeline.active === 1 ? "" : "s"} enriching` : "Graph enrichment needs attention"}
          </span>
          {graphPipeline.estimatedRemainingSeconds != null && <span className="text-muted">{formatGraphEtaRange(graphPipeline.estimatedRemainingSeconds, graphPipeline.estimatedRemainingSecondsP95)}</span>}
          {graphPipeline.degraded > 0 && <button className="bb-action bb-action--danger ml-auto h-7 px-2.5 text-[10px]" onClick={() => { window.location.href = appPath("/activity"); }}>{graphPipeline.degraded} failed pipeline{graphPipeline.degraded === 1 ? "" : "s"}</button>}
        </div>
      )}

      {["pending", "running"].includes(researchRun?.status || "") && !askOnly && (
        <div className="flex items-center gap-3 border-b border-border bg-surface px-4 py-2 text-[11px]" role="status">
          <BrainCircuit className="size-4 text-accent" />
          <span className="font-medium text-foreground">Researching knowledge gaps</span>
          <span className="text-muted">{researchRun?.progress || 0}% · external sources enabled</span>
          <button className="bb-action ml-auto h-7 px-2.5 text-[10px]" onClick={cancelOnlineResearch}>Cancel</button>
        </div>
      )}

      {researchStatus && !askOnly && (
        <div className="border-b border-border/40 bg-surface px-4 py-1.5 text-center text-[11px] text-muted" role="status">
          {researchStatus}
        </div>
      )}

      {inference && !askOnly && (
        <div className="border-b border-border/40 bg-panel/80 px-4 py-3">
          <div className="mx-auto max-w-5xl rounded-xl border border-border/50 bg-surface/70 p-3">
            <div className="mb-1 flex items-center gap-2">
              <span className={`text-[10px] font-semibold uppercase tracking-wide ${inference.status === "provider_unavailable" ? "text-danger" : "text-accent"}`}>
                {inference.status === "provider_unavailable" ? "Provider unavailable" : t("graphInference")}
              </span>
              <span className="rounded-full bg-panel px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
            </div>
            <p className={`text-sm leading-relaxed ${["error", "provider_unavailable"].includes(inference.status) ? "text-danger" : "text-foreground"}`}>{inference.answer}</p>
            {["error", "provider_unavailable"].includes(inference.status) && (
              <p className="mt-2 rounded-lg bg-panel px-2 py-1 text-[11px] text-muted">
                No BerryBrain answer was created. Retry the request or review the active provider and model in Settings.
              </p>
            )}
            {inference.status !== "provider_unavailable" && !!inference.relatedNodes?.length && (
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
            {inference.status !== "provider_unavailable" && !!inference.evidence?.length && (
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
              {!flowActive && !["error", "provider_unavailable"].includes(inference.status) && (
                <button className="bb-action px-3 py-1 text-[10px] font-semibold text-violet-600" onClick={startFlow}>
                  Continue in Flow
                </button>
              )}
              {inference.status === "provider_unavailable" && (
                <button className="bb-action px-3 py-1 text-[10px] font-semibold" onClick={() => void runInference(inference.question)}>
                  <RefreshCw className="mr-1 inline size-3" />Retry
                </button>
              )}
              {inference.status === "provider_unavailable" && onOpenSettings && (
                <button className="bb-action px-3 py-1 text-[10px] font-semibold" onClick={onOpenSettings}>
                  <Settings className="mr-1 inline size-3" />Open Settings
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
                <div className="flex min-w-0 flex-wrap items-center gap-2 sm:flex-nowrap">
                  <input
                    ref={askInputRef}
                    type="text"
                    className="h-14 min-w-0 basis-full rounded-lg border border-border bg-background px-4 text-base text-foreground outline-none placeholder:text-muted/60 focus:border-accent focus:outline focus:outline-3 focus:outline-accent/20 sm:basis-0 sm:flex-1"
                    placeholder="Ask your graph about its content or structure..."
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                  />
                  <VoicePromptButton value={query} onChange={setQuery} className="h-12 w-12" />
                  <button
                    type="submit"
                    className="bb-action bb-action--primary h-12 min-w-0 flex-1 px-4 text-sm font-semibold sm:flex-none sm:px-6"
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
              <section className="mx-auto max-w-4xl border-y border-border py-6 text-left" aria-label={inference.status === "provider_unavailable" ? "Ask unavailable" : "Graph answer"} aria-live="polite">
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase ${inference.status === "provider_unavailable" ? "text-danger" : "text-accent"}`}>
                    {inference.status === "provider_unavailable" && <AlertTriangle className="size-3.5" />}
                    {inference.status === "provider_unavailable" ? "Provider unavailable" : "BerryBrain answer"}
                  </span>
                  <span className="rounded-full border border-border bg-surface px-2 py-0.5 text-[10px] text-muted">{inference.status}</span>
                </div>
                <p className={`whitespace-pre-wrap text-base leading-7 ${["error", "provider_unavailable"].includes(inference.status) ? "text-danger" : "text-foreground"}`}>{inference.answer}</p>
                {inference.status === "provider_unavailable" && (
                  <p className="mt-2 text-sm leading-6 text-muted">No answer was created or added to the conversation. Retry the request or review the active provider and model.</p>
                )}
                {inference.status !== "provider_unavailable" && !!inference.evidence?.length && (
                  <div className="mt-5 space-y-2">
                    <h2 className="text-[11px] font-semibold uppercase text-muted">Evidence</h2>
                    {inference.evidence.slice(0, 6).map((item, index) => (
                      <div key={index} className="border-l-2 border-accent/40 pl-3 text-xs leading-5 text-muted">{formatInferenceEvidence(item)}</div>
                    ))}
                  </div>
                )}
                {inference.status !== "provider_unavailable" && !!relatedInferenceNodes.length && (
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
                  {!flowActive && !["error", "provider_unavailable"].includes(inference.status) && <button className="bb-action px-3 py-1.5 text-xs font-semibold" onClick={startFlow}>Continue in Flow</button>}
                  {inference.status === "provider_unavailable" && <button className="bb-action inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold" onClick={() => void runInference(inference.question)}><RefreshCw className="size-3.5" />Retry</button>}
                  {inference.status === "provider_unavailable" && onOpenSettings && <button className="bb-action bb-action--primary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold" onClick={onOpenSettings}><Settings className="size-3.5" />Open Settings</button>}
                  {inference.status !== "provider_unavailable" && <button
                    className="bb-action px-3 py-1.5 text-xs"
                    disabled={inferenceSaving || inference.status === "saved_as_insight" || (!inference.inferenceId && !flowSessionId) || !["answered", "success", "sufficient_evidence", "insufficient_evidence"].includes(inference.status)}
                    onClick={saveInferenceAsInsight}
                  >{inferenceSaving ? "Creating..." : inference.status === "saved_as_insight" ? "Insight created" : "Create insight"}</button>}
                  {!['error', 'provider_unavailable'].includes(inference.status) && (inference.inferenceId || (flowActive && flowSessionId)) && <>
                    <button className={`bb-action grid size-8 place-items-center p-0 ${askFeedback === "upvoted" ? "text-success" : ""}`} aria-label="Mark answer as useful" title="Mark answer as useful" onClick={() => void recordAskFeedback("upvoted")}><ThumbsUp className="size-3.5" /></button>
                    <button className={`bb-action grid size-8 place-items-center p-0 ${askFeedback === "downvoted" ? "text-danger" : ""}`} aria-label="Mark answer as not useful" title="Mark answer as not useful" onClick={() => void recordAskFeedback("downvoted")}><ThumbsDown className="size-3.5" /></button>
                  </>}
                  <button className="px-2 py-1.5 text-xs text-muted hover:text-foreground" onClick={() => setInference(null)}>{inference.status === "provider_unavailable" ? "Dismiss" : "Clear answer"}</button>
                  {(inference.provider || inference.model) && <span className="ml-auto text-[10px] text-muted">{inference.provider || "provider"}{inference.model ? ` · ${inference.model}` : ""}</span>}
                </div>
                {inferenceSaveStatus && <p className="mt-3 text-xs text-muted">{inferenceSaveStatus}</p>}
                {askFeedback === "error" && <p className="mt-3 text-xs text-danger">Answer feedback could not be recorded.</p>}
                {["upvoted", "downvoted"].includes(askFeedback) && <p className="mt-3 text-xs text-muted">Feedback recorded for future context-aware validation.</p>}
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

    </div>
  );
}

function formatGraphEta(seconds: number) {
  if (seconds < 60) return "under a minute";
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes ? `${hours} hr ${remainingMinutes} min` : `${hours} hr`;
}

function formatGraphEtaRange(p50: number, p95?: number | null) {
  const lower = Math.max(0, p50);
  const upper = Math.max(lower, p95 ?? lower);
  if (upper <= lower) return `About ${formatGraphEta(lower)}`;
  return `${formatGraphEta(lower)}-${formatGraphEta(upper)} estimated`;
}
