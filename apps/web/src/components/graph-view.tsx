"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState, useCallback } from "react";
import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  select,
  zoom as d3Zoom,
  zoomIdentity,
  zoomTransform,
  type Simulation,
  type SimulationNodeDatum,
  type ZoomBehavior,
} from "d3";

type GNode = {
  id: string;
  recordId?: number;
  type: string;
  label: string;
  title?: string;
  summary?: string;
  path?: string;
  folder?: string;
  source?: string;
  sourceId?: number;
  sourceNoteIds?: number[];
  connectionsCount?: number;
  status?: string;
  confidence?: number;
  confidenceInterval?: { score?: number | null; lower?: number | null; upper?: number | null; sampleSize?: number; method?: string };
  createdBy?: string;
  createdByModel?: string;
  semanticState?: string;
  semanticStatus?: string;
  semanticProfileVersion?: number;
  clusterId?: number | null;
  colorId?: string;
  colorConfidence?: number;
  colorReason?: string;
  ontology?: { class?: string; canonicalLabel?: string };
};
type GEdge = {
  id?: number;
  source: string;
  target: string;
  type: string;
  label?: string;
  confidence?: number;
  confidenceInterval?: { lower?: number | null; upper?: number | null };
  reason?: string;
  evidence?: string[];
  sourceNoteIds?: number[];
  status?: string;
  provider?: string;
  model?: string;
};

const COLORS = {
  note: { fill: "#CC4168", border: "#B33654", label: "#1D1B18" },
  concept: { fill: "#D98A00", border: "#9B6200", label: "#1D1B18" },
  topic: { fill: "#96B55C", border: "#7FA04A", label: "#1D1B18" },
  entity: { fill: "#2E9D68", border: "#1E714A", label: "#1D1B18" },
  context: { fill: "#8B6F9F", border: "#5E3C7A", label: "#1D1B18" },
  gap: { fill: "#B85C4A", border: "#7B3429", label: "#1D1B18" },
  insight: { fill: "#4F7CCB", border: "#2E4F8F", label: "#1D1B18" },
  tag: { fill: "#6FAF2A", border: "#4D7F1D", label: "#1D1B18" },
  source: { fill: "#4A8F6A", border: "#2F684B", label: "#1D1B18" },
  attachment: { fill: "#6B8FAF", border: "#466984", label: "#1D1B18" },
  orphan: { fill: "#F4E6D8", border: "#B89B82", label: "#6B4A2D" },
  selected: { fill: "#CC4168", border: "#1D1B18", glow: "rgba(204,65,104,0.3)" },
  central: { fill: "#CC4168", border: "#B33654", label: "#1D1B18" },
};
type NodeColorKey = keyof typeof COLORS;

const EDGE_COLORS: Record<string, string> = {
  references: "#3C8F5A", derived_from: "#4F7CCB", mentions: "#96B55C",
  about: "#D98A00", supports: "#4A8F6A", contradicts: "#B85C4A",
  contrasts_with: "#8B6F9F", same_as: "#B85C4A", example_of: "#4A8F6A",
  applies_to: "#9F6B4A", prerequisite_for: "#3C8F5A", broader: "#557A95",
  narrower: "#557A95", instance_of: "#2E9D68", part_of: "#6B4A2D",
  attached_to: "#7A6F64", contextualizes: "#D98A00", related: "#6B4A2D", default: "#B89B82",
};
const SYMMETRIC_EDGES = new Set(["same_as", "contrasts_with", "related"]);

function edgeColor(type: string): string {
  if (EDGE_COLORS[type]) return EDGE_COLORS[type];
  let hash = 2166136261;
  for (const character of type || "connection") {
    hash ^= character.charCodeAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return `hsl(${Math.abs(hash) % 360} 48% 46%)`;
}

function humanEdgeType(type: string) {
  return (type || "related").replaceAll("_", " ");
}

function formatTooltipConfidence(value: unknown) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "Pending";
  const normalized = value > 1 ? value / 100 : value;
  return `${Math.round(normalized * 100)}%`;
}

type NodeShape =
  | "circle"
  | "square"
  | "diamond"
  | "hexagon"
  | "triangle"
  | "inverted-triangle"
  | "rect"
  | "pill"
  | "octagon"
  | "parallelogram"
  | "chevron"
  | "tag"
  | "stack"
  | "kite";

function normalizedNodeType(type: string) {
  return (type || "note").toLowerCase();
}

function nodeShape(type: string): NodeShape {
  const value = normalizedNodeType(type);
  if (value === "vault") return "square";
  if (value === "concept") return "diamond";
  if (value === "topic") return "hexagon";
  if (value === "entity") return "triangle";
  if (value === "context") return "pill";
  if (value === "gap") return "inverted-triangle";
  if (value === "insight") return "rect";
  if (value === "attachment") return "octagon";
  if (value === "source") return "parallelogram";
  if (value === "study_path") return "chevron";
  if (value === "cluster") return "stack";
  if (value === "tag") return "tag";
  return "circle";
}

function pathNodeShape(ctx: CanvasRenderingContext2D, x: number, y: number, r: number, shape: NodeShape) {
  ctx.beginPath();
  if (shape === "circle") {
    ctx.arc(x, y, r, 0, Math.PI * 2);
    return;
  }
  if (shape === "square") {
    ctx.rect(x - r * 0.9, y - r * 0.9, r * 1.8, r * 1.8);
    return;
  }
  if (shape === "rect") {
    roundedRectPath(ctx, x - r * 1.28, y - r * 0.8, r * 2.56, r * 1.6, Math.max(4, r * 0.22));
    return;
  }
  if (shape === "pill") {
    roundedRectPath(ctx, x - r * 1.45, y - r * 0.72, r * 2.9, r * 1.44, r * 0.72);
    return;
  }
  if (shape === "stack") {
    roundedRectPath(ctx, x - r * 1.15, y - r * 0.78, r * 2.3, r * 1.56, Math.max(3, r * 0.18));
    ctx.moveTo(x - r * 0.92, y - r * 0.42);
    ctx.lineTo(x + r * 0.92, y - r * 0.42);
    ctx.moveTo(x - r * 0.92, y + r * 0.42);
    ctx.lineTo(x + r * 0.92, y + r * 0.42);
    return;
  }
  const points: Array<[number, number]> = [];
  if (shape === "parallelogram") {
    points.push([x - r * 1.18, y + r * 0.78], [x - r * 0.68, y - r * 0.78], [x + r * 1.18, y - r * 0.78], [x + r * 0.68, y + r * 0.78]);
  } else if (shape === "chevron") {
    points.push([x - r * 1.25, y - r * 0.95], [x + r * 0.35, y - r * 0.95], [x + r * 1.25, y], [x + r * 0.35, y + r * 0.95], [x - r * 1.25, y + r * 0.95], [x - r * 0.35, y]);
  } else if (shape === "tag") {
    points.push([x - r * 1.1, y - r * 0.82], [x + r * 0.58, y - r * 0.82], [x + r * 1.18, y], [x + r * 0.58, y + r * 0.82], [x - r * 1.1, y + r * 0.82]);
  } else if (shape === "kite") {
    points.push([x, y - r * 1.3], [x + r * 0.98, y - r * 0.12], [x, y + r * 0.9], [x - r * 0.98, y - r * 0.12]);
  } else if (shape === "diamond") {
    points.push([x, y - r * 1.18], [x + r * 1.18, y], [x, y + r * 1.18], [x - r * 1.18, y]);
  } else if (shape === "triangle") {
    points.push([x, y - r * 1.2], [x + r * 1.12, y + r * 0.82], [x - r * 1.12, y + r * 0.82]);
  } else if (shape === "inverted-triangle") {
    points.push([x - r * 1.12, y - r * 0.82], [x + r * 1.12, y - r * 0.82], [x, y + r * 1.2]);
  } else {
    const sides = shape === "octagon" ? 8 : 6;
    const offset = shape === "octagon" ? Math.PI / 8 : Math.PI / 6;
    for (let i = 0; i < sides; i += 1) {
      const angle = offset + (i * Math.PI * 2) / sides;
      points.push([x + Math.cos(angle) * r * 1.08, y + Math.sin(angle) * r * 1.08]);
    }
  }
  points.forEach(([px, py], index) => index === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py));
  ctx.closePath();
}

function roundedRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, width: number, height: number, radius: number) {
  const r = Math.min(radius, width / 2, height / 2);
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + width - r, y);
  ctx.quadraticCurveTo(x + width, y, x + width, y + r);
  ctx.lineTo(x + width, y + height - r);
  ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  ctx.lineTo(x + r, y + height);
  ctx.quadraticCurveTo(x, y + height, x, y + height - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}

function shortNodeLabel(label: string) {
  return (label || "").trim();
}

type NodeLabelLayout = {
  signature: string;
  lines: string[];
  maxWidth: number;
  size: number;
};

function nodeRadius(node: GNode, degree: number) {
  const label = shortNodeLabel(node.label || node.title || "");
  const visibleLength = Math.min(54, label.length);
  const longestWord = Math.min(18, Math.max(0, ...label.split(/\s+/).map((word) => word.length)));
  const textRadius = 15 + Math.min(20, visibleLength * 0.37) + Math.min(6, longestWord * 0.32);
  const degreeRadius = 13 + Math.sqrt(Math.max(0, degree)) * 3.1 + (node.type === "note" ? 2 : 0);
  return Math.max(16, Math.min(42, Math.max(textRadius, degreeRadius)));
}

function parseHexColor(value: string): [number, number, number] | null {
  const normalized = value.trim().replace(/^#/, "");
  const expanded = normalized.length === 3
    ? normalized.split("").map((character) => `${character}${character}`).join("")
    : normalized;
  if (!/^[0-9a-f]{6}$/i.test(expanded)) return null;
  return [0, 2, 4].map((offset) => Number.parseInt(expanded.slice(offset, offset + 2), 16)) as [number, number, number];
}

function relativeLuminance(color: string): number | null {
  const rgb = parseHexColor(color);
  if (!rgb) return null;
  const channels = rgb.map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

export function nodeTextContrastRatio(background: string, foreground: string): number {
  const backgroundLuminance = relativeLuminance(background);
  const foregroundLuminance = relativeLuminance(foreground);
  if (backgroundLuminance == null || foregroundLuminance == null) return 0;
  const lighter = Math.max(backgroundLuminance, foregroundLuminance);
  const darker = Math.min(backgroundLuminance, foregroundLuminance);
  return (lighter + 0.05) / (darker + 0.05);
}

export function readableNodeTextColor(fill: string, preferred: string) {
  const candidates = [...new Set([preferred, "#1D1B18", "#FFFFFF"].filter(Boolean))];
  return candidates.reduce((best, candidate) => (
    nodeTextContrastRatio(fill, candidate) > nodeTextContrastRatio(fill, best)
      ? candidate
      : best
  ), candidates[0] || "#1D1B18");
}

function drawInnerNodeLabel(
  ctx: CanvasRenderingContext2D,
  node: GNode,
  x: number,
  y: number,
  r: number,
  color: string,
  cache: Map<string, NodeLabelLayout>,
) {
  const label = shortNodeLabel(node.label || node.title || "");
  if (!label) return;
  const shape = nodeShape(node.type);
  const widthFactor = ["rect", "pill", "stack"].includes(shape)
    ? 2.18
    : shape === "parallelogram"
      ? 1.88
      : shape === "diamond"
        ? 1.82
        : 1.58;
  const maxWidth = Math.max(26, r * widthFactor);
  const maxCharacters = Math.max(20, Math.min(58, Math.floor(r * 1.75)));
  const visibleLabel = label.length > maxCharacters
    ? `${label.slice(0, maxCharacters - 3).trimEnd()}...`
    : label;
  const signature = `${visibleLabel}|${node.type}|${r.toFixed(2)}|${maxWidth.toFixed(2)}`;
  const cached = cache.get(node.id);
  if (cached?.signature === signature) {
    ctx.save();
    ctx.font = `600 ${cached.size}px Inter, system-ui, sans-serif`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = color;
    const lineHeight = cached.size * 1.08;
    cached.lines.forEach((line, index) => {
      const offset = (index - (cached.lines.length - 1) / 2) * lineHeight;
      ctx.fillText(line, x, y + offset, cached.maxWidth);
    });
    ctx.restore();
    return;
  }
  let size = Math.max(8, Math.min(11, 7.5 + r * 0.1));
  const words = visibleLabel.split(/\s+/).filter(Boolean);
  ctx.save();
  ctx.font = `600 ${size}px Inter, system-ui, sans-serif`;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const lines: string[] = [];
  for (const word of words) {
    if (!lines.length) {
      lines.push(word);
      continue;
    }
    const candidate = `${lines[lines.length - 1]} ${word}`;
    if (ctx.measureText(candidate).width <= maxWidth) {
      lines[lines.length - 1] = candidate;
    } else if (lines.length < 3) {
      lines.push(word);
    } else {
      let finalLine = `${lines[2]} ${word}`;
      while (finalLine.length > 3 && ctx.measureText(`${finalLine}...`).width > maxWidth) {
        finalLine = finalLine.slice(0, -1).trimEnd();
      }
      lines[2] = `${finalLine.replace(/\.{3}$/, "")}...`;
      break;
    }
  }
  const widest = Math.max(...lines.map((line) => ctx.measureText(line).width), 1);
  if (widest > maxWidth) {
    size = Math.max(8, size * (maxWidth / widest));
    ctx.font = `600 ${size}px Inter, system-ui, sans-serif`;
  }
  cache.set(node.id, { signature, lines, maxWidth, size });
  ctx.fillStyle = color;
  const lineHeight = size * 1.08;
  lines.forEach((line, index) => {
    const offset = (index - (lines.length - 1) / 2) * lineHeight;
    ctx.fillText(line, x, y + offset, maxWidth);
  });
  ctx.restore();
}

interface LN extends SimulationNodeDatum {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  node: GNode;
}
export type GraphLayoutMode = "brain" | "radial" | "type" | "connections";

type GraphPaletteColor = {
  colorId: string;
  lightHex: string;
  darkHex: string;
  border: string;
  text: string;
  namespace: "semantic" | "vault" | "pending";
};

type GraphData = {
  nodes: GNode[];
  edges: GEdge[];
  stats: Record<string, unknown>;
  graphVersion?: number;
  palette?: Record<string, GraphPaletteColor>;
};

async function fetchGraphResource(
  input: string,
  timeoutMs = 2_500,
): Promise<Response> {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(input, { signal: controller.signal });
  } finally {
    window.clearTimeout(timer);
  }
}

export function useGraphData(apiUrl: string) {
  const [data, setData] = useState<GraphData | null>(null);
  const dataRef = useRef<GraphData | null>(null);
  const [error, setError] = useState(false);
  const [reloadVersion, setReloadVersion] = useState(0);
  useEffect(() => {
    if (apiUrl === "__demo__") {
      const demo = { nodes: [], edges: [], stats: {} };
      dataRef.current = demo;
      setData(demo);
      return;
    }
    let cancelled = false;
    function publish(next: GraphData) {
      if (cancelled) return;
      dataRef.current = next;
      setData(next);
    }
    async function loadMetadata() {
      const [summaryResponse, paletteResponse] = await Promise.all([
        fetchGraphResource(`${apiUrl}/api/v1/graph/summary?includeProvisional=true`),
        fetchGraphResource(`${apiUrl}/api/v1/graph/palette`),
      ]);
      if (!summaryResponse.ok) throw new Error("Graph summary unavailable");
      const summary = await summaryResponse.json();
      const stats = {
        ...summary,
        orphan_count: summary.orphan_count ?? summary.orphans ?? 0,
      };
      const palettePayload = paletteResponse.ok ? await paletteResponse.json() : { colors: [] };
      const palette = Object.fromEntries(
        (palettePayload.colors || []).map((color: GraphPaletteColor) => [color.colorId, color]),
      );
      return { stats, palette };
    }
    async function loadFullGraph() {
        const { stats, palette } = await loadMetadata();
        const nodes: GNode[] = [];
        let nodeCursor: number | null = 0;
        let publishedInitialNodes = false;
        while (nodeCursor !== null && !cancelled) {
          const limit = publishedInitialNodes ? 2_000 : 500;
          const response = await fetchGraphResource(
            `${apiUrl}/api/v1/graph/nodes?cursor=${nodeCursor}&limit=${limit}&includeProvisional=true`,
          );
          if (!response.ok) throw new Error("Graph nodes unavailable");
          const page: { nodes?: GNode[]; nextCursor: number | null; graphVersion?: number } = await response.json();
          nodes.push(...(page.nodes || []));
          nodeCursor = page.nextCursor;
          if (!publishedInitialNodes) {
            publishedInitialNodes = true;
            publish({ nodes: [...nodes], edges: [], stats, graphVersion: page.graphVersion, palette });
          }
        }
        const edges: GEdge[] = [];
        let edgeCursor: number | null = 0;
        let publishedInitialEdges = false;
        while (edgeCursor !== null && !cancelled) {
          const response = await fetchGraphResource(
            `${apiUrl}/api/v1/graph/edges?cursor=${edgeCursor}&limit=5000&includeProvisional=true`,
          );
          if (!response.ok) throw new Error("Graph edges unavailable");
          const page: { edges?: GEdge[]; nextCursor: number | null; graphVersion?: number } = await response.json();
          edges.push(...(page.edges || []));
          edgeCursor = page.nextCursor;
          if (!publishedInitialEdges || edgeCursor === null) {
            publishedInitialEdges = true;
            publish({ nodes, edges: [...edges], stats, graphVersion: page.graphVersion, palette });
          }
        }
    }
    async function loadDelta(previous: GraphData): Promise<boolean> {
      if (previous.graphVersion === undefined) return false;
      const response = await fetchGraphResource(
        `${apiUrl}/api/v1/graph/delta?since_version=${previous.graphVersion}&includeProvisional=true`,
      );
      if (!response.ok) return false;
      const delta: {
        graphVersion: number;
        nodes?: GNode[];
        requiresEdgeRefresh?: boolean;
        requiresFullRefresh?: boolean;
        nodeCount?: number;
        edgeCount?: number;
      } = await response.json();
      const merged = new Map(previous.nodes.map((node) => [node.id, node]));
      for (const node of delta.nodes || []) merged.set(node.id, node);
      if (
        delta.requiresFullRefresh ||
        delta.requiresEdgeRefresh ||
        delta.nodeCount !== merged.size ||
        delta.edgeCount !== previous.edges.length
      ) return false;
      const { stats, palette } = await loadMetadata();
      publish({
        nodes: [...merged.values()],
        edges: previous.edges,
        stats,
        graphVersion: delta.graphVersion,
        palette,
      });
      return true;
    }
    async function loadGraph() {
      setError(false);
      try {
        const previous = dataRef.current;
        const updatedByDelta = reloadVersion > 0 && previous
          ? await loadDelta(previous).catch(() => false)
          : false;
        if (!updatedByDelta) await loadFullGraph();
      } catch {
        try {
          const legacyResponse = await fetchGraphResource(
            `${apiUrl}/api/v1/graph?includeProvisional=true`,
            5_000,
          );
          if (!legacyResponse.ok) throw new Error("Legacy graph endpoint unavailable");
          const legacy = await legacyResponse.json();
          publish(legacy);
        } catch {
          if (!cancelled) setError(true);
        }
      }
    }
    loadGraph();
    return () => {
      cancelled = true;
    };
  }, [apiUrl, reloadVersion]);
  const reload = useCallback(() => {
    if (apiUrl === "__demo__") return;
    setReloadVersion((value) => value + 1);
  }, [apiUrl]);
  return { data, error, reload };
}

function tooltipCtx(g: { nodes: GNode[]; edges: GEdge[] }) {
  const info = new Map<string, any>();
  for (const n of g.nodes) info.set(n.id, { ...n, degree: 0, edgeTypes: [] as string[], relations: [] as any[] });
  for (const e of g.edges) {
    const s = info.get(e.source), t = info.get(e.target);
    if (s) {
      s.degree++;
      if (!s.edgeTypes.includes(e.type)) s.edgeTypes.push(e.type);
      s.relations.push({ direction: "out", type: e.type, peer: t?.label || e.target, reason: e.reason, confidence: e.confidenceInterval?.lower ?? e.confidence });
    }
    if (t) {
      t.degree++;
      if (!t.edgeTypes.includes(e.type)) t.edgeTypes.push(e.type);
      t.relations.push({ direction: "in", type: e.type, peer: s?.label || e.source, reason: e.reason, confidence: e.confidenceInterval?.lower ?? e.confidence });
    }
  }
  return info;
}

export function GraphCanvas({
  data, onNavigate, onSelect, onOpen, selectedId, highlightedIds = [], zoom, setZoom, pan, setPan, layoutMode = "brain",
}: {
  data: {
    nodes: GNode[];
    edges: GEdge[];
    palette?: Record<string, GraphPaletteColor>;
    graphVersion?: number;
  };
  onNavigate?: (path: string) => void;
  onSelect?: (id: string | null) => void;
  onOpen?: (id: string) => void;
  selectedId: string | null;
  highlightedIds?: string[];
  zoom: number; setZoom: (z: number) => void;
  pan: { x: number; y: number }; setPan: (p: { x: number; y: number }) => void;
  layoutMode?: GraphLayoutMode;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layoutRef = useRef<LN[]>([]);
  const layoutByIdRef = useRef<Map<string, LN>>(new Map());
  const spatialIndexRef = useRef<Map<string, LN[]>>(new Map());
  const nodeLabelCacheRef = useRef<Map<string, NodeLabelLayout>>(new Map());
  const dragRef = useRef({ active: false, moved: false, startX: 0, startY: 0, nodeIdx: -1, vx: 0, vy: 0, lastT: 0 });
  const suppressClickUntilRef = useRef(0);
  const simulationRef = useRef<Simulation<LN, undefined> | null>(null);
  const zoomBehaviorRef = useRef<ZoomBehavior<HTMLCanvasElement, unknown> | null>(null);
  const fitGraphRef = useRef<((duration?: number) => void) | null>(null);
  const userMovedCameraRef = useRef(false);
  const cameraAnimatingRef = useRef(false);
  const cameraCommitTimerRef = useRef(0);
  const onOpenRef = useRef(onOpen);
  const pendingOpenNodeRef = useRef<LN | null>(null);
  const viewRef = useRef({ zoom, pan });
  const renderedViewRef = useRef({ zoom, pan });
  const [renderRevision, setRenderRevision] = useState(0);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; n: any } | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const W = 6000, H = 6000;
  const knownNodes = useRef<Set<string>>(new Set());
  const freshNodes = useRef<Map<string, number>>(new Map()); // id → added timestamp

  const tctx = useRef<Map<string, any>>(new Map());
  useEffect(() => { tctx.current = tooltipCtx(data); }, [data]);
  useEffect(() => { onOpenRef.current = onOpen; }, [onOpen]);
  useLayoutEffect(() => { viewRef.current = { zoom, pan }; }, [pan, zoom]);
  const highlighted = useMemo(() => new Set(highlightedIds), [highlightedIds]);
  const adjacency = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const node of data.nodes) map.set(node.id, new Set());
    for (const edge of data.edges) {
      map.get(edge.source)?.add(edge.target);
      map.get(edge.target)?.add(edge.source);
    }
    return map;
  }, [data]);
  const focusRoots = useMemo(
    () => new Set([selectedId, hoveredId].filter((value): value is string => Boolean(value))),
    [hoveredId, selectedId],
  );
  const focusId = selectedId || hoveredId;
  const focusedIds = useMemo(() => {
    const ids = new Set<string>();
    for (const root of focusRoots) {
      ids.add(root);
      for (const neighbor of adjacency.get(root) || []) ids.add(neighbor);
    }
    return ids;
  }, [adjacency, focusRoots]);
  const layoutStorageKey = `bb_graph_layout:${data.graphVersion || 0}:${layoutMode || "brain"}`;

  useEffect(() => {
    if (!selectedId || !containerRef.current) return;
    const pendingNode = pendingOpenNodeRef.current;
    const node = layoutByIdRef.current.get(selectedId)
      || (pendingNode?.node.id === selectedId ? pendingNode : undefined);
    if (!node) {
      const fallbackTimer = window.setTimeout(
        () => onOpenRef.current?.(selectedId),
        650,
      );
      return () => window.clearTimeout(fallbackTimer);
    }
    userMovedCameraRef.current = true;
    const currentZoom = viewRef.current.zoom;
    const targetZoom = Math.max(1.8, Math.min(3.2, currentZoom < 1.8 ? 2.15 : currentZoom * 1.28));
    const canvas = canvasRef.current;
    const behavior = zoomBehaviorRef.current;
    const viewport = containerRef.current.getBoundingClientRect();
    if (canvas && behavior) {
      const target = zoomIdentity
        .translate(viewport.width / 2, viewport.height / 2)
        .scale(targetZoom)
        .translate(-node.x, -node.y);
      const selection = select<HTMLCanvasElement, unknown>(canvas).interrupt();
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        cameraAnimatingRef.current = false;
        selection.call(behavior.transform, target);
        pendingOpenNodeRef.current = null;
        onOpenRef.current?.(selectedId);
      } else {
        cameraAnimatingRef.current = true;
        let completed = false;
        let fallbackTimer = 0;
        const finish = () => {
          if (completed) return;
          completed = true;
          if (fallbackTimer) window.clearTimeout(fallbackTimer);
          cameraAnimatingRef.current = false;
          pendingOpenNodeRef.current = null;
          onOpenRef.current?.(selectedId);
        };
        fallbackTimer = window.setTimeout(finish, 650);
        selection
          .transition()
          .duration(480)
          .on("end", finish)
          .on("interrupt", finish)
          .call(behavior.transform, target);
      }
      return;
    }
    setZoom(targetZoom);
    setPan({ x: (W / 2 - node.x) * targetZoom, y: (H / 2 - node.y) * targetZoom });
    pendingOpenNodeRef.current = null;
    onOpenRef.current?.(selectedId);
  }, [selectedId, setPan, setZoom]);

  useEffect(() => {
    const clearFocus = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      setHoveredId(null);
      onSelect?.(null);
    };
    window.addEventListener("keydown", clearFocus);
    return () => window.removeEventListener("keydown", clearFocus);
  }, [onSelect]);

  const persistLayout = useCallback(() => {
    try {
      const positions = Object.fromEntries(
        layoutRef.current.map((node) => [node.node.id, [node.x, node.y]]),
      );
      sessionStorage.setItem(layoutStorageKey, JSON.stringify(positions));
    } catch {
      // Storage can be unavailable or full; layout persistence is an optimization.
    }
  }, [layoutStorageKey]);

  const initLayout = useCallback(() => {
    const now = performance.now();
    if (knownNodes.current.size === 0) {
      // First render — consider all nodes existing, don't pulse
      for (const node of data.nodes) {
        knownNodes.current.add(node.id);
      }
    } else {
      const addedCount = data.nodes.reduce(
        (count, node) => count + (knownNodes.current.has(node.id) ? 0 : 1),
        0,
      );
      const shouldPulseAddedNodes = addedCount <= 200;
      for (const node of data.nodes) {
        if (shouldPulseAddedNodes && !knownNodes.current.has(node.id)) {
          freshNodes.current.set(node.id, now);
        }
      }
    }
    for (const id of freshNodes.current.keys()) {
      if (now - (freshNodes.current.get(id) || now) > 4000) {
        freshNodes.current.delete(id);
      }
    }
    knownNodes.current = new Set(data.nodes.map((n) => n.id));
    const degrees = new Map<string, number>();
    for (const node of data.nodes) degrees.set(node.id, 0);
    for (const edge of data.edges) {
      degrees.set(edge.source, (degrees.get(edge.source) || 0) + 1);
      degrees.set(edge.target, (degrees.get(edge.target) || 0) + 1);
    }
    const sorted = [...data.nodes].sort((a, b) => (degrees.get(b.id) || 0) - (degrees.get(a.id) || 0));
    const rank = new Map(sorted.map((node, index) => [node.id, index]));
    const byType = new Map<string, GNode[]>();
    for (const node of data.nodes) byType.set(node.type, [...(byType.get(node.type) || []), node]);
    const typeOrder = [...byType.keys()].sort();
    const typeIndex = new Map(typeOrder.map((type, index) => [type, index]));
    const typeRanks = new Map(
      [...byType].map(([type, nodes]) => [
        type,
        new Map(nodes.map((node, index) => [node.id, index])),
      ]),
    );

    let storedPositions = new Map<string, [number, number]>();
    try {
      const stored = JSON.parse(sessionStorage.getItem(layoutStorageKey) || "{}") as Record<string, [number, number]>;
      storedPositions = new Map(Object.entries(stored));
    } catch {
      storedPositions = new Map();
    }
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const layout: LN[] = data.nodes.map((n, i) => {
      const angle = i * 2.399963229728653;
      const radialAngle = (2 * Math.PI * i) / Math.max(1, data.nodes.length);
      const degree = degrees.get(n.id) || n.connectionsCount || 0;
      const r = nodeRadius(n, degree);
      const stored = storedPositions.get(n.id);
      if (stored && stored.every(Number.isFinite)) {
        if (layoutMode !== "brain" || reduceMotion) {
          return { x: stored[0], y: stored[1], vx: 0, vy: 0, r, node: n };
        }
        return {
          x: W / 2 + (stored[0] - W / 2) * 0.22,
          y: H / 2 + (stored[1] - H / 2) * 0.22,
          vx: 0,
          vy: 0,
          r,
          node: n,
        };
      }
      if (layoutMode === "type") {
        const col = typeIndex.get(n.type) || 0;
        const group = byType.get(n.type) || [];
        const pos = typeRanks.get(n.type)?.get(n.id) || 0;
        const x = W / 2 - ((typeOrder.length - 1) * 360) / 2 + col * 360;
        const y = H / 2 - ((group.length - 1) * 86) / 2 + pos * 86;
        return { x, y, vx: 0, vy: 0, r, node: n };
      }
      if (layoutMode === "connections") {
        const nodeRank = rank.get(n.id) || 0;
        const radius = nodeRank < 5 ? 160 : 420 + Math.floor(nodeRank / 18) * 260;
        const localAngle = (2 * Math.PI * nodeRank) / Math.max(6, data.nodes.length);
        return { x: W / 2 + radius * Math.cos(localAngle), y: H / 2 + radius * Math.sin(localAngle), vx: 0, vy: 0, r, node: n };
      }
      const radius = layoutMode === "radial"
        ? 950
        : Math.min(180, 26 + Math.sqrt(i + 1) * 15);
      const layoutAngle = layoutMode === "radial" ? radialAngle : angle;
      return { x: W / 2 + radius * Math.cos(layoutAngle), y: H / 2 + radius * (layoutMode === "radial" ? 1 : 0.72) * Math.sin(layoutAngle), vx: 0, vy: 0, r, node: n };
    });
    layoutRef.current = layout;
    layoutByIdRef.current = new Map(layout.map((node) => [node.node.id, node]));
  }, [data, layoutMode, layoutStorageKey]);

  useEffect(() => { initLayout(); }, [initLayout]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const selection = select<HTMLCanvasElement, unknown>(canvas);
    const behavior = d3Zoom<HTMLCanvasElement, unknown>()
      .scaleExtent([0.08, 8])
      .filter((event) => {
        if (event.type === "dblclick") return false;
        if (event.type !== "mousedown") return true;
        if (event.button !== 0) return false;
        const transform = zoomTransform(canvas);
        const rect = canvas.getBoundingClientRect();
        const [worldX, worldY] = transform.invert([event.clientX - rect.left, event.clientY - rect.top]);
        return !layoutRef.current.some(
          (node) => Math.hypot(worldX - node.x, worldY - node.y) <= node.r + 4,
        );
      })
      .on("start", (event) => {
        if (event.sourceEvent) userMovedCameraRef.current = true;
      })
      .on("zoom", (event) => {
        const rect = container.getBoundingClientRect();
        const nextZoom = event.transform.k;
        const nextPan = {
          x: event.transform.x - rect.width / 2 + nextZoom * W / 2,
          y: event.transform.y - rect.height / 2 + nextZoom * H / 2,
        };
        viewRef.current = { zoom: nextZoom, pan: nextPan };
        const renderedView = renderedViewRef.current;
        const scale = nextZoom / renderedView.zoom;
        const offsetX = (1 - scale) * rect.width / 2 + nextPan.x - scale * renderedView.pan.x;
        const offsetY = (1 - scale) * rect.height / 2 + nextPan.y - scale * renderedView.pan.y;
        canvas.style.transformOrigin = "0 0";
        canvas.style.transform = `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
        window.clearTimeout(cameraCommitTimerRef.current);
        cameraCommitTimerRef.current = window.setTimeout(() => {
          setZoom(nextZoom);
          setPan(nextPan);
        }, 300);
      });

    zoomBehaviorRef.current = behavior;
    selection.call(behavior);
    const rect = container.getBoundingClientRect();
    const initial = zoomIdentity
      .translate(rect.width / 2 + viewRef.current.pan.x, rect.height / 2 + viewRef.current.pan.y)
      .scale(viewRef.current.zoom)
      .translate(-W / 2, -H / 2);
    selection.call(behavior.transform, initial);

    fitGraphRef.current = (duration = 520) => {
      if (!layoutRef.current.length) return;
      const bounds = layoutRef.current.reduce(
        (box, node) => ({
          minX: Math.min(box.minX, node.x - node.r),
          maxX: Math.max(box.maxX, node.x + node.r),
          minY: Math.min(box.minY, node.y - node.r),
          maxY: Math.max(box.maxY, node.y + node.r),
        }),
        { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity },
      );
      const viewport = container.getBoundingClientRect();
      const graphWidth = Math.max(1, bounds.maxX - bounds.minX);
      const graphHeight = Math.max(1, bounds.maxY - bounds.minY);
      const padding = Math.min(96, Math.max(40, Math.min(viewport.width, viewport.height) * 0.1));
      const fittedScale = Math.max(
        0.08,
        Math.min(2.2, (viewport.width - padding * 2) / graphWidth, (viewport.height - padding * 2) / graphHeight),
      );
      const centerX = (bounds.minX + bounds.maxX) / 2;
      const centerY = (bounds.minY + bounds.maxY) / 2;
      const target = zoomIdentity
        .translate(viewport.width / 2, viewport.height / 2)
        .scale(fittedScale)
        .translate(-centerX, -centerY);
      selection.interrupt();
      if (duration <= 0) selection.call(behavior.transform, target);
      else selection.transition().duration(duration).call(behavior.transform, target);
    };

    return () => {
      window.clearTimeout(cameraCommitTimerRef.current);
      canvas.style.transform = "";
      selection.interrupt().on(".zoom", null);
      zoomBehaviorRef.current = null;
      fitGraphRef.current = null;
    };
  }, [setPan, setZoom]);

  useEffect(() => {
    if (cameraAnimatingRef.current) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    const behavior = zoomBehaviorRef.current;
    if (!canvas || !container || !behavior) return;
    const rect = container.getBoundingClientRect();
    const desired = zoomIdentity
      .translate(rect.width / 2 + pan.x, rect.height / 2 + pan.y)
      .scale(zoom)
      .translate(-W / 2, -H / 2);
    const current = zoomTransform(canvas);
    if (
      Math.abs(current.k - desired.k) > 0.0001
      || Math.abs(current.x - desired.x) > 0.1
      || Math.abs(current.y - desired.y) > 0.1
    ) {
      select<HTMLCanvasElement, unknown>(canvas).call(behavior.transform, desired);
    }
  }, [pan, zoom]);

  useEffect(() => {
    simulationRef.current?.stop();
    userMovedCameraRef.current = false;
    if (layoutMode !== "brain" || !layoutRef.current.length) {
      setRenderRevision((value) => value + 1);
      return;
    }

    const nodes = layoutRef.current;
    // At this scale a force pass adds CPU cost without producing a readable
    // global layout. Keep the deterministic progressive layout interactive.
    if (nodes.length >= 8_000) {
      const fitTimers = [window.setTimeout(() => {
        if (!userMovedCameraRef.current) fitGraphRef.current?.(0);
      }, 80)];
      setRenderRevision((value) => value + 1);
      return () => {
        fitTimers.forEach(window.clearTimeout);
      };
    }

    const ids = new Set(nodes.map((node) => node.node.id));
    const links = data.edges
      .filter((edge) => ids.has(edge.source) && ids.has(edge.target))
      .map((edge) => ({ source: edge.source, target: edge.target }));
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let renderFrame = 0;
    const simulation = forceSimulation<LN>(nodes)
      .alpha(1)
      .alphaMin(0.006)
      .alphaDecay(0.022)
      // D3's decay value is friction: 0.15 keeps the graph slippery and organic.
      .velocityDecay(0.15)
      .force("charge", forceManyBody<LN>().strength(-42).distanceMin(18).distanceMax(520))
      .force(
        "link",
        forceLink<LN, { source: string | LN; target: string | LN }>(links)
          .id((node) => node.node.id)
          .distance(74)
          .strength(0.11),
      )
      .force(
        "collide",
        forceCollide<LN>().radius((node) => node.r + 11).strength(0.94).iterations(nodes.length > 1_000 ? 1 : 2),
      )
      .force("x", forceX<LN>(W / 2).strength(0.018))
      .force("y", forceY<LN>(H / 2).strength(0.018))
      .on("tick", () => {
        if (renderFrame) return;
        renderFrame = requestAnimationFrame(() => {
          renderFrame = 0;
          setRenderRevision((value) => value + 1);
        });
      })
      .on("end", () => {
        setRenderRevision((value) => value + 1);
        persistLayout();
      });

    simulationRef.current = simulation;
    const fitTimers = reduceMotion
      ? [window.setTimeout(() => fitGraphRef.current?.(0), 0)]
      : [450, 1_250, 2_400].map((delay) => window.setTimeout(() => {
          if (!userMovedCameraRef.current) fitGraphRef.current?.(520);
        }, delay));

    if (reduceMotion) {
      simulation.stop();
      simulation.tick(Math.min(80, Math.max(20, nodes.length)));
      setRenderRevision((value) => value + 1);
      persistLayout();
    }

    return () => {
      simulation.stop();
      simulationRef.current = null;
      if (renderFrame) cancelAnimationFrame(renderFrame);
      fitTimers.forEach(window.clearTimeout);
    };
  }, [data, layoutMode, persistLayout]);

  useLayoutEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const canvasEl = canvas;
    const ctx = canvasEl.getContext("2d")!;

    let raf = 0;
    function prepareCanvas() {
      const rect = containerRef.current?.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect?.width || 1));
      const height = Math.max(1, Math.floor(rect?.height || 1));
      const dpr = window.devicePixelRatio || 1;
      const pixelWidth = Math.floor(width * dpr);
      const pixelHeight = Math.floor(height * dpr);
      if (canvasEl.width !== pixelWidth || canvasEl.height !== pixelHeight) {
        canvasEl.width = pixelWidth;
        canvasEl.height = pixelHeight;
        canvasEl.style.width = `${width}px`;
        canvasEl.style.height = `${height}px`;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      return { width, height };
    }

    function render() {
      const { width, height } = prepareCanvas();
      const currentView = viewRef.current;
      const renderZoom = currentView.zoom;
      const renderPan = currentView.pan;
      canvasEl.style.transform = "";
      const ct = ctx;
      ct.clearRect(0, 0, width, height);
      ct.save();
      ct.translate(width / 2 + renderPan.x, height / 2 + renderPan.y);
      ct.scale(renderZoom, renderZoom);
      ct.translate(-W / 2, -H / 2);

      const nodes = layoutRef.current;
      const nodeIndex = layoutByIdRef.current;
      const margin = 100;
      const visibleCandidates = nodes.filter((node) => {
        const screenX = width / 2 + renderPan.x + renderZoom * (node.x - W / 2);
        const screenY = height / 2 + renderPan.y + renderZoom * (node.y - H / 2);
        return screenX >= -margin && screenX <= width + margin
          && screenY >= -margin && screenY <= height + margin;
      });
      const largeGraph = data.nodes.length >= 5_000;
      const nodeBudget = largeGraph
        ? renderZoom < 0.25 ? 80 : renderZoom < 0.65 ? 160 : 320
        : renderZoom < 0.5 ? 400 : renderZoom < 1.5 ? 500 : 2_000;
      const sampleStride = Math.max(1, Math.ceil(visibleCandidates.length / nodeBudget));
      const visibleNodes = visibleCandidates.filter(
        (node, index) => (
          index % sampleStride === 0
          || node.node.id === selectedId
          || highlighted.has(node.node.id)
        ),
      );
      const spatialIndex = new Map<string, LN[]>();
      for (const node of visibleNodes) {
        const key = `${Math.floor(node.x / 96)}:${Math.floor(node.y / 96)}`;
        spatialIndex.set(key, [...(spatialIndex.get(key) || []), node]);
      }
      spatialIndexRef.current = spatialIndex;
      const visibleIds = new Set(visibleNodes.map((node) => node.node.id));

      const edgeBudget = largeGraph
        ? renderZoom < 0.25 ? 120 : renderZoom < 0.65 ? 260 : 600
        : renderZoom < 0.5 ? 800 : renderZoom < 1.5 ? 900 : 5_000;
      let renderedEdges = 0;
      for (const e of data.edges) {
        if (renderedEdges >= edgeBudget) break;
        const s = nodeIndex.get(e.source);
        const t = nodeIndex.get(e.target);
        if (!s || !t || (!visibleIds.has(e.source) && !visibleIds.has(e.target))) continue;
        const isFocusedEdge = Boolean(focusId)
          && focusedIds.has(e.source)
          && focusedIds.has(e.target)
          && (focusRoots.has(e.source) || focusRoots.has(e.target));
        const isHighlightedEdge = isFocusedEdge || highlighted.has(e.source) || highlighted.has(e.target);
        ct.beginPath();
        ct.moveTo(s.x, s.y);
        ct.lineTo(t.x, t.y);
        ct.globalAlpha = focusId && !isFocusedEdge ? 0.08 : isHighlightedEdge ? 0.82 : 0.28;
        ct.strokeStyle = isHighlightedEdge ? COLORS.selected.fill : edgeColor(e.type);
        const edgeConfidence = e.confidenceInterval?.lower ?? e.confidence ?? 0;
        ct.lineWidth = isHighlightedEdge ? 1.8 : Math.max(0.65, edgeConfidence * 1.35);
        ct.stroke();
        if (!SYMMETRIC_EDGES.has(e.type)) {
          const angle = Math.atan2(t.y - s.y, t.x - s.x);
          const targetRadius = t.r + 2;
          const tipX = t.x - Math.cos(angle) * targetRadius;
          const tipY = t.y - Math.sin(angle) * targetRadius;
          const arrowSize = isHighlightedEdge ? 6 : 4.5;
          ct.beginPath();
          ct.moveTo(tipX, tipY);
          ct.lineTo(tipX - Math.cos(angle - Math.PI / 6) * arrowSize, tipY - Math.sin(angle - Math.PI / 6) * arrowSize);
          ct.lineTo(tipX - Math.cos(angle + Math.PI / 6) * arrowSize, tipY - Math.sin(angle + Math.PI / 6) * arrowSize);
          ct.closePath();
          ct.fillStyle = isHighlightedEdge ? COLORS.selected.fill : edgeColor(e.type);
          ct.fill();
        }
        ct.globalAlpha = 1;
        renderedEdges += 1;
      }

      let hasActivePulse = false;
      for (const n of visibleNodes) {
        const isSel = n.node.id === selectedId;
        const isHovered = n.node.id === hoveredId;
        const isHighlighted = isHovered || highlighted.has(n.node.id);
        const isDimmed = Boolean(focusId) && !focusedIds.has(n.node.id);
        const isOrphan = (tctx.current.get(n.node.id)?.degree || 0) === 0;
        const nodeType = n.node.type as NodeColorKey;
        const semanticColor = data.palette?.[n.node.colorId || ""];
        const configuredColors = COLORS[nodeType];
        const fallbackColors = configuredColors && "label" in configuredColors
          ? configuredColors
          : COLORS.note;
        const colors = nodeType === "note" || nodeType === "insight"
          ? COLORS[nodeType]
          : semanticColor
            ? { fill: semanticColor.lightHex, border: semanticColor.border, label: semanticColor.text }
            : n.node.colorId === "pending"
              ? COLORS.orphan
              : fallbackColors;
        const r = isSel ? n.r * 1.2 : n.r;
        const shape = nodeShape(n.node.type);
        const addedAt = freshNodes.current.get(n.node.id);
        const isNew = addedAt && (performance.now() - addedAt) < 4000;
        hasActivePulse = hasActivePulse || Boolean(isNew);
        const pulsePhase = isNew ? (performance.now() - addedAt) / 4000 : 1; // 0 → 1 over 4s

        ct.globalAlpha = isDimmed ? 0.14 : 1;
        if (isSel || isHighlighted) {
          pathNodeShape(ct, n.x, n.y, r + 6, shape);
          ct.fillStyle = isSel ? COLORS.selected.glow : "rgba(204,65,104,0.18)"; ct.fill();
        }

        if (isNew && !isSel) {
          const pulseRadius = r + 8 + Math.sin(pulsePhase * Math.PI * 4) * 4;
          const alpha = (1 - pulsePhase) * 0.4;
          ct.beginPath(); ct.arc(n.x, n.y, pulseRadius, 0, Math.PI * 2);
          ct.fillStyle = `rgba(217,138,0,${alpha})`;
          ct.fill();
        }

        ct.setLineDash(isOrphan ? [5, 3] : []);
        pathNodeShape(ct, n.x, n.y, r, shape);
        ct.fillStyle = colors.fill; ct.fill();
        ct.strokeStyle = isHighlighted ? COLORS.selected.fill : colors.border;
        ct.lineWidth = isHighlighted ? 2.4 : 1.25;
        ct.stroke();
        ct.setLineDash([]);
        const labelIsReadable = !largeGraph || renderZoom >= 0.4 || isSel || isHighlighted;
        if (labelIsReadable) {
          drawInnerNodeLabel(
            ct,
            n.node,
            n.x,
            n.y,
            r,
            readableNodeTextColor(colors.fill, colors.label),
            nodeLabelCacheRef.current,
          );
        }

        ct.globalAlpha = 1;
      }

      ct.globalAlpha = 1;
      ct.restore();
      renderedViewRef.current = currentView;
      if (hasActivePulse) raf = requestAnimationFrame(render);
    }
    render();
    return () => {
      cancelAnimationFrame(raf);
    };
  }, [data, zoom, pan, selectedId, hoveredId, focusId, focusRoots, focusedIds, highlighted, renderRevision]);

  const toWorld = (cx: number, cy: number) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const r = containerRef.current.getBoundingClientRect();
    const currentView = viewRef.current;
    return {
      x: (cx - r.left - r.width / 2 - currentView.pan.x) / currentView.zoom + W / 2,
      y: (cy - r.top - r.height / 2 - currentView.pan.y) / currentView.zoom + H / 2,
    };
  };

  const findNodeAt = (cx: number, cy: number) => {
    const world = toWorld(cx, cy);
    const cellX = Math.floor(world.x / 96);
    const cellY = Math.floor(world.y / 96);
    for (let x = cellX - 1; x <= cellX + 1; x += 1) {
      for (let y = cellY - 1; y <= cellY + 1; y += 1) {
        const candidates = spatialIndexRef.current.get(`${x}:${y}`) || [];
        const hit = candidates.find(
          (node) => Math.hypot(world.x - node.x, world.y - node.y) < node.r,
        );
        if (hit) return hit;
      }
    }
    return undefined;
  };

  const releaseDrag = () => {
    const drag = dragRef.current;
    const node = drag.nodeIdx >= 0 ? layoutRef.current[drag.nodeIdx] : undefined;
    if (drag.moved) suppressClickUntilRef.current = performance.now() + 300;
    drag.active = false;
    drag.moved = false;
    drag.nodeIdx = -1;
    if (!node) return;
    node.fx = node.x;
    node.fy = node.y;
    node.vx = 0;
    node.vy = 0;
    simulationRef.current?.alphaTarget(0);
    persistLayout();
  };

  return (
    <div ref={containerRef} className="relative h-full w-full cursor-grab overflow-hidden bg-background">
      <canvas
        ref={canvasRef}
        className="absolute"
        role="img"
        aria-label={`Knowledge graph with ${data.nodes.length} nodes and ${data.edges.length} connections`}
        data-layout-engine="d3-force-v7"
        data-velocity-decay="0.15"
        data-collision-padding="11"
        data-node-label-max-lines="3"
        data-node-label-max-characters="58"
        data-node-label-contrast="fill-aware-wcag"
        data-drag-open-threshold="5"
        data-selected-node={selectedId || ""}
        onMouseDown={e => {
          const candidate = findNodeAt(e.clientX, e.clientY);
          const hit = candidate ? layoutRef.current.indexOf(candidate) : -1;
          if (hit < 0) return;
          const node = layoutRef.current[hit];
          node.fx = node.x;
          node.fy = node.y;
          simulationRef.current?.alphaTarget(0.3).restart();
          dragRef.current = { active: true, moved: false, startX: e.clientX, startY: e.clientY, nodeIdx: hit, vx: 0, vy: 0, lastT: performance.now() };
        }}
        onMouseMove={e => {
          if (dragRef.current.active) {
            if (!dragRef.current.moved) {
              dragRef.current.moved = Math.hypot(
                e.clientX - dragRef.current.startX,
                e.clientY - dragRef.current.startY,
              ) >= 5;
              if (!dragRef.current.moved) return;
              setTooltip(null);
              setHoveredId(null);
            }
            if (dragRef.current.nodeIdx >= 0) {
              const n = layoutRef.current[dragRef.current.nodeIdx];
              const w = toWorld(e.clientX, e.clientY);
              const now = performance.now();
              const elapsed = Math.max(1, now - dragRef.current.lastT);
              dragRef.current.vx = (w.x - n.x) / elapsed;
              dragRef.current.vy = (w.y - n.y) / elapsed;
              dragRef.current.lastT = now;
              n.fx = w.x;
              n.fy = w.y;
              n.x = w.x;
              n.y = w.y;
              setRenderRevision((value) => value + 1);
            }
            return;
          }
          const hit = findNodeAt(e.clientX, e.clientY);
          if (hit) {
            setHoveredId(hit.node.id);
            const info = tctx.current.get(hit.node.id);
            const rect = containerRef.current?.getBoundingClientRect();
            if (!rect) return;
            const currentView = viewRef.current;
            const nodeX = rect.width / 2 + currentView.pan.x + currentView.zoom * (hit.x - W / 2);
            const nodeY = rect.height / 2 + currentView.pan.y + currentView.zoom * (hit.y - H / 2);
            const cardWidth = 320;
            const gap = Math.max(10, hit.r * currentView.zoom + 10);
            const x = nodeX + gap + cardWidth <= rect.width - 8
              ? nodeX + gap
              : Math.max(8, nodeX - gap - cardWidth);
            const y = Math.max(8, Math.min(rect.height - 250, nodeY - 72));
            setTooltip({ x, y, n: { ...hit.node, degree: info?.degree, edgeTypes: info?.edgeTypes, relations: info?.relations } });
          } else {
            setHoveredId(null);
            setTooltip(null);
          }
        }}
        onMouseLeave={() => {
          if (dragRef.current.active) releaseDrag();
          setHoveredId(null);
          setTooltip(null);
        }}
        onMouseUp={releaseDrag}
        onDoubleClick={e => {
          const hit = findNodeAt(e.clientX, e.clientY);
          if (hit?.node.path && onNavigate) { onSelect?.(null); onNavigate(hit.node.path); }
        }}
        onClick={e => {
          if (dragRef.current.active || performance.now() < suppressClickUntilRef.current) return;
          const hit = findNodeAt(e.clientX, e.clientY);
          pendingOpenNodeRef.current = hit || null;
          onSelect?.(hit ? hit.node.id : null);
        }}
      />

      {tooltip && (
        <div role="tooltip" className="pointer-events-none absolute z-30 w-80 rounded-md border border-white/10 bg-[#1D1B18]/95 px-3 py-3 text-[11px] text-white backdrop-blur"
          style={{ left: tooltip.x, top: tooltip.y }}>
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0 break-words text-xs font-semibold leading-4">{tooltip.n.label}</div>
            <span className="shrink-0 text-[9px] font-semibold uppercase opacity-65">{tooltip.n.type}</span>
          </div>
          <div className="mt-2 line-clamp-4 text-[10px] leading-4 opacity-85">
            {tooltip.n.summary || tooltip.n.title || tooltip.n.source || "Summary not generated yet."}
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 border-t border-white/10 pt-2 text-[9px]">
            <div><dt className="opacity-55">Connections</dt><dd className="font-medium opacity-90">{tooltip.n.degree ?? 0}</dd></div>
            <div><dt className="opacity-55">Confidence</dt><dd className="font-medium opacity-90">{formatTooltipConfidence(tooltip.n.confidenceInterval?.score ?? tooltip.n.confidence)}</dd></div>
            <div><dt className="opacity-55">Semantic state</dt><dd className="truncate font-medium opacity-90">{tooltip.n.semanticState || "pending"}</dd></div>
            <div><dt className="opacity-55">Context cluster</dt><dd className="truncate font-medium opacity-90">{tooltip.n.clusterId != null ? `Cluster ${tooltip.n.clusterId}` : "Pending"}</dd></div>
          </dl>
          {tooltip.n.relations?.length > 0 && (
            <div className="mt-2 border-t border-white/10 pt-2">
              <div className="mb-1 text-[9px] font-semibold uppercase opacity-55">Key relationships</div>
              <div className="space-y-1">
                {tooltip.n.relations.slice(0, 3).map((relation: any, index: number) => (
                  <div key={`${relation.direction}-${relation.type}-${relation.peer}-${index}`} className="flex min-w-0 items-center gap-1.5 text-[9px] leading-3 opacity-85">
                    <span aria-hidden="true">{relation.direction === "out" ? "->" : "<-"}</span>
                    <span className="shrink-0 font-medium">{humanEdgeType(relation.type)}</span>
                    <span className="truncate opacity-70">{relation.peer}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          {tooltip.n.path && (
            <div className="mt-2 truncate border-t border-white/10 pt-2 text-[9px] opacity-55">{tooltip.n.path}</div>
          )}
          {(tooltip.n.createdBy || tooltip.n.createdByModel) && (
            <div className="mt-1 text-[9px] opacity-45">Created by {tooltip.n.createdBy || "system"}{tooltip.n.createdByModel ? ` using ${tooltip.n.createdByModel}` : ""}</div>
          )}
        </div>
      )}
    </div>
  );
}
