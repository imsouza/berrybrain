"use client";

import { useEffect, useLayoutEffect, useMemo, useRef, useState, useCallback } from "react";
import { t } from "@/i18n";

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
  createdBy?: string;
  createdByModel?: string;
  semanticState?: string;
  semanticProfileVersion?: number;
  clusterId?: number | null;
  colorId?: string;
  colorConfidence?: number;
  colorReason?: string;
};
type GEdge = {
  id?: number;
  source: string;
  target: string;
  type: string;
  label?: string;
  confidence?: number;
  reason?: string;
  evidence?: string[];
  sourceNoteIds?: number[];
  status?: string;
  provider?: string;
  model?: string;
};

const COLORS = {
  note: { fill: "#C2185B", border: "#8F123F", label: "#3E3024" },
  concept: { fill: "#D98A00", border: "#9B6200", label: "#3E3024" },
  topico: { fill: "#96B55C", border: "#6F8B3F", label: "#3E3024" },
  topic: { fill: "#96B55C", border: "#6F8B3F", label: "#3E3024" },
  entidade: { fill: "#2E9D68", border: "#1E714A", label: "#3E3024" },
  entity: { fill: "#2E9D68", border: "#1E714A", label: "#3E3024" },
  contexto: { fill: "#8B6F9F", border: "#5E3C7A", label: "#3E3024" },
  context: { fill: "#8B6F9F", border: "#5E3C7A", label: "#3E3024" },
  lacuna: { fill: "#B85C4A", border: "#7B3429", label: "#3E3024" },
  gap: { fill: "#B85C4A", border: "#7B3429", label: "#3E3024" },
  insight: { fill: "#4F7CCB", border: "#2E4F8F", label: "#3E3024" },
  tag: { fill: "#6FAF2A", border: "#4D7F1D", label: "#3E3024" },
  fonte: { fill: "#4A8F6A", border: "#2F684B", label: "#3E3024" },
  source: { fill: "#4A8F6A", border: "#2F684B", label: "#3E3024" },
  anexo: { fill: "#6B8FAF", border: "#466984", label: "#3E3024" },
  attachment: { fill: "#6B8FAF", border: "#466984", label: "#3E3024" },
  orphan: { fill: "#F4E6D8", border: "#B89B82", label: "#6B4A2D" },
  selected: { fill: "#C2185B", border: "#3E3024", glow: "rgba(194,24,91,0.3)" },
  central: { fill: "#B90F4D", border: "#5E0A29", label: "#3E3024" },
};
type NodeColorKey = keyof typeof COLORS;

const EDGE_COLORS: Record<string, string> = {
  explicit_link: "#3C8F5A", semantic_relation: "#D98A00", derived_from: "#4F7CCB",
  mentions: "#96B55C", supports: "#4A8F6A", contradicts: "#B85C4A",
  contrasts_with: "#8B6F9F", duplicates: "#B85C4A", example_of: "#4A8F6A", applies_to: "#9F6B4A",
  semantic: "#D98A00", semantic_similarity: "#D98A00", shared_concept: "#C2185B",
  shared_context: "#8B6F9F", backlink: "#3C8F5A", prerequisite: "#3C8F5A", related: "#6B4A2D",
  duplicate: "#B85C4A", contrast: "#8B6F9F", example: "#4A8F6A",
  application: "#9F6B4A", inferred: "#9EBF61", default: "#B89B82",
};

const BG = "#FBF4EC";

interface LN { x: number; y: number; vx: number; vy: number; r: number; node: GNode }
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
        fetchGraphResource(`${apiUrl}/api/v1/graph/summary`),
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
            `${apiUrl}/api/v1/graph/nodes?cursor=${nodeCursor}&limit=${limit}`,
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
            `${apiUrl}/api/v1/graph/edges?cursor=${edgeCursor}&limit=5000`,
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
        `${apiUrl}/api/v1/graph/delta?since_version=${previous.graphVersion}`,
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
            `${apiUrl}/api/v1/graph`,
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
  for (const n of g.nodes) info.set(n.id, { ...n, degree: 0, edgeTypes: [] as string[] });
  for (const e of g.edges) {
    const s = info.get(e.source), t = info.get(e.target);
    if (s) { s.degree++; if (!s.edgeTypes.includes(e.type)) s.edgeTypes.push(e.type); }
    if (t) { t.degree++; if (!t.edgeTypes.includes(e.type)) t.edgeTypes.push(e.type); }
  }
  return info;
}

export function GraphCanvas({
  data, onNavigate, onSelect, selectedId, highlightedIds = [], zoom, setZoom, pan, setPan, layoutMode = "brain",
}: {
  data: {
    nodes: GNode[];
    edges: GEdge[];
    palette?: Record<string, GraphPaletteColor>;
    graphVersion?: number;
  };
  onNavigate?: (path: string) => void;
  onSelect?: (id: string | null) => void;
  selectedId: string | null;
  highlightedIds?: string[];
  zoom: number; setZoom: (z: number) => void;
  pan: { x: number; y: number }; setPan: (p: { x: number; y: number }) => void;
  layoutMode?: GraphLayoutMode;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const layoutRef = useRef<LN[]>([]);
  const spatialIndexRef = useRef<Map<string, LN[]>>(new Map());
  const restoredLayoutRef = useRef(false);
  const dragRef = useRef({ active: false, ox: 0, oy: 0, nodeIdx: -1 });
  const [renderRevision, setRenderRevision] = useState(0);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; n: any } | null>(null);
  const W = 6000, H = 6000;
  const knownNodes = useRef<Set<string>>(new Set());
  const freshNodes = useRef<Map<string, number>>(new Map()); // id → added timestamp

  const tctx = useRef<Map<string, any>>(new Map());
  useEffect(() => { tctx.current = tooltipCtx(data); }, [data]);
  const highlighted = useMemo(() => new Set(highlightedIds), [highlightedIds]);
  const layoutStorageKey = `bb_graph_layout:${data.graphVersion || 0}:${layoutMode || "brain"}`;

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
    restoredLayoutRef.current = (
      data.nodes.length > 0
      && data.nodes.every((node) => storedPositions.has(node.id))
    );
    const layout: LN[] = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, data.nodes.length);
      const r = n.type === "note" ? (n.connectionsCount && n.connectionsCount > 3 ? 28 : 22) : n.type === "concept" ? 24 : 20;
      const stored = storedPositions.get(n.id);
      if (stored && stored.every(Number.isFinite)) {
        return { x: stored[0], y: stored[1], vx: 0, vy: 0, r, node: n };
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
      const nodeRank = rank.get(n.id) || 0;
      const brainRadius = nodeRank < 4 ? 180 : n.type === "note" ? 560 : n.type === "concept" ? 860 : 1120;
      const radius = layoutMode === "radial" ? 950 : brainRadius;
      return { x: W / 2 + radius * Math.cos(angle), y: H / 2 + radius * Math.sin(angle), vx: 0, vy: 0, r, node: n };
    });
    layoutRef.current = layout;
  }, [data, layoutMode, layoutStorageKey]);

  useEffect(() => { initLayout(); }, [initLayout]);

  useEffect(() => {
    if (
      layoutMode !== "brain"
      || !layoutRef.current.length
      || restoredLayoutRef.current
      || data.nodes.length >= 5_000
    ) {
      setRenderRevision((value) => value + 1);
      return;
    }
    const worker = new Worker(new URL("./graph-layout.worker.ts", import.meta.url));
    worker.onmessage = (event: MessageEvent<{ positions: Array<{ id: string; x: number; y: number }> }>) => {
      const positions = new Map(event.data.positions.map((item) => [item.id, item]));
      for (const node of layoutRef.current) {
        const position = positions.get(node.node.id);
        if (position) {
          node.x = position.x;
          node.y = position.y;
        }
      }
      persistLayout();
      setRenderRevision((value) => value + 1);
      worker.terminate();
    };
    worker.postMessage({
      nodes: layoutRef.current.map((node) => ({
        id: node.node.id,
        x: node.x,
        y: node.y,
        vx: 0,
        vy: 0,
        r: node.r,
      })),
      edges: data.edges.map((edge) => ({ source: edge.source, target: edge.target })),
      width: W,
      height: H,
      iterations: data.nodes.length >= 5_000 ? 24 : data.nodes.length >= 1_000 ? 72 : 180,
    });
    return () => worker.terminate();
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
      const ct = ctx;
      ct.clearRect(0, 0, width, height);
      ct.fillStyle = BG; ct.fillRect(0, 0, width, height);
      ct.save();
      ct.translate(width / 2 + pan.x, height / 2 + pan.y);
      ct.scale(zoom, zoom);
      ct.translate(-W / 2, -H / 2);

      const nodes = layoutRef.current;
      const nodeIndex = new Map(nodes.map((node) => [node.node.id, node]));
      const margin = 100;
      const visibleCandidates = nodes.filter((node) => {
        const screenX = width / 2 + pan.x + zoom * (node.x - W / 2);
        const screenY = height / 2 + pan.y + zoom * (node.y - H / 2);
        return screenX >= -margin && screenX <= width + margin
          && screenY >= -margin && screenY <= height + margin;
      });
      const largeGraph = data.nodes.length >= 5_000;
      const nodeBudget = zoom < 0.5 ? 400 : zoom < 1.5 || largeGraph ? 500 : 2_000;
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

      const edgeBudget = zoom < 0.5 ? 800 : zoom < 1.5 || largeGraph ? 900 : 5_000;
      let renderedEdges = 0;
      for (const e of data.edges) {
        if (renderedEdges >= edgeBudget) break;
        const s = nodeIndex.get(e.source);
        const t = nodeIndex.get(e.target);
        if (!s || !t || (!visibleIds.has(e.source) && !visibleIds.has(e.target))) continue;
        const isHighlightedEdge = highlighted.has(e.source) || highlighted.has(e.target);
        ct.beginPath();
        ct.moveTo(s.x, s.y);
        ct.lineTo(t.x, t.y);
        ct.strokeStyle = isHighlightedEdge ? "#D98A00CC" : (EDGE_COLORS[e.type] || EDGE_COLORS.default) + "70";
        ct.lineWidth = isHighlightedEdge ? 3 : (e.confidence || 0.5) * 2;
        ct.stroke();
        renderedEdges += 1;
      }

      let hasActivePulse = false;
      const showLabels = visibleNodes.length <= 600 || zoom >= 2.5;
      for (const n of visibleNodes) {
        const isSel = n.node.id === selectedId;
        const isHighlighted = highlighted.has(n.node.id);
        const isOrphan = (tctx.current.get(n.node.id)?.degree || 0) === 0;
        const nodeType = n.node.type as NodeColorKey;
        const semanticColor = data.palette?.[n.node.colorId || ""];
        const configuredColors = COLORS[nodeType];
        const fallbackColors = configuredColors && "label" in configuredColors
          ? configuredColors
          : COLORS.note;
        const colors = semanticColor
          ? { fill: semanticColor.lightHex, border: semanticColor.border, label: semanticColor.text }
          : n.node.colorId === "pending"
            ? COLORS.orphan
            : fallbackColors;
        const r = isSel ? n.r * 1.2 : n.r;
        const isInsight = n.node.type === "insight";
        const addedAt = freshNodes.current.get(n.node.id);
        const isNew = addedAt && (performance.now() - addedAt) < 4000;
        hasActivePulse = hasActivePulse || Boolean(isNew);
        const pulsePhase = isNew ? (performance.now() - addedAt) / 4000 : 1; // 0 → 1 over 4s

        if (isSel || isHighlighted) {
          ct.beginPath(); ct.arc(n.x, n.y, r + 6, 0, Math.PI * 2);
          ct.fillStyle = isSel ? COLORS.selected.glow : "rgba(217,138,0,0.28)"; ct.fill();
        }

        if (isNew && !isSel) {
          const pulseRadius = r + 8 + Math.sin(pulsePhase * Math.PI * 4) * 4;
          const alpha = (1 - pulsePhase) * 0.4;
          ct.beginPath(); ct.arc(n.x, n.y, pulseRadius, 0, Math.PI * 2);
          ct.fillStyle = `rgba(217,138,0,${alpha})`;
          ct.fill();
        }

        ct.setLineDash(isOrphan ? [5, 3] : []);
        if (isInsight) {
          const bw = Math.max(r * 3, 80);
          const bh = Math.max(r * 1.4, 24);
          ct.beginPath();
          ct.roundRect(n.x - bw / 2, n.y - bh / 2, bw, bh, 6);
          ct.fillStyle = colors.fill;
          ct.fill();
          ct.strokeStyle = colors.border;
          ct.lineWidth = isHighlighted ? 3 : 2;
          ct.stroke();
        } else {
          ct.beginPath(); ct.arc(n.x, n.y, r, 0, Math.PI * 2);
          ct.fillStyle = colors.fill; ct.fill();
          ct.strokeStyle = isHighlighted ? "#D98A00" : colors.border; ct.lineWidth = isHighlighted ? 3 : 2; ct.stroke();
        }
        ct.setLineDash([]);

        ct.fillStyle = colors.label;
        ct.font = `${isSel ? "14px" : "12px"} system-ui, sans-serif`;
        ct.textAlign = "center";
        ct.textBaseline = "middle";
        const lbl = n.node.label.length > 18 ? n.node.label.slice(0, 17) + "\u2026" : n.node.label;
        if (showLabels || isSel || isHighlighted) ct.fillText(lbl, n.x, n.y + 1);
      }
      ct.restore();
      if (hasActivePulse) raf = requestAnimationFrame(render);
    }
    render();
    return () => cancelAnimationFrame(raf);
  }, [data, zoom, pan, selectedId, highlighted, renderRevision]);

  const toWorld = (cx: number, cy: number) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const r = containerRef.current.getBoundingClientRect();
    return {
      x: (cx - r.left - r.width / 2 - pan.x) / zoom + W / 2,
      y: (cy - r.top - r.height / 2 - pan.y) / zoom + H / 2,
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

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden cursor-grab" style={{ background: BG }}>
      <canvas
        ref={canvasRef}
        className="absolute"
        role="img"
        aria-label={`Knowledge graph with ${data.nodes.length} nodes and ${data.edges.length} connections`}
        onMouseDown={e => {
          const candidate = findNodeAt(e.clientX, e.clientY);
          const hit = candidate ? layoutRef.current.indexOf(candidate) : -1;
          if (hit >= 0) { dragRef.current = { active: true, ox: 0, oy: 0, nodeIdx: hit }; return; }
          dragRef.current = { active: true, ox: e.clientX, oy: e.clientY, nodeIdx: -1 };
        }}
        onMouseMove={e => {
          if (dragRef.current.active) {
            if (dragRef.current.nodeIdx >= 0) {
              const n = layoutRef.current[dragRef.current.nodeIdx];
              const w = toWorld(e.clientX, e.clientY);
              n.x = w.x; n.y = w.y;
              setRenderRevision((value) => value + 1);
            } else {
              setPan({ x: pan.x + e.clientX - dragRef.current.ox, y: pan.y + e.clientY - dragRef.current.oy });
              dragRef.current.ox = e.clientX; dragRef.current.oy = e.clientY;
            }
            return;
          }
          const hit = findNodeAt(e.clientX, e.clientY);
          if (hit) {
            const info = tctx.current.get(hit.node.id);
            setTooltip({ x: e.clientX, y: e.clientY, n: { ...hit.node, degree: info?.degree, edgeTypes: info?.edgeTypes } });
          } else setTooltip(null);
        }}
        onMouseUp={() => {
          if (dragRef.current.nodeIdx >= 0) persistLayout();
          dragRef.current.active = false;
          dragRef.current.nodeIdx = -1;
        }}
        onDoubleClick={e => {
          const hit = findNodeAt(e.clientX, e.clientY);
          if (hit?.node.path && onNavigate) { onSelect?.(null); onNavigate(hit.node.path); }
        }}
        onClick={e => {
          if (dragRef.current.active) return;
          const hit = findNodeAt(e.clientX, e.clientY);
          onSelect?.(hit ? hit.node.id : null);
        }}
        onWheel={e => { e.preventDefault(); setZoom(Math.max(0.2, Math.min(4, zoom - e.deltaY * 0.001))); }}
      />

      {tooltip && (
        <div className="absolute pointer-events-none z-30 rounded-xl bg-[#3E3024]/90 backdrop-blur px-3 py-2 text-[11px] text-[#FBF4EC] shadow-lg"
          style={{ left: tooltip.x + 14, top: tooltip.y - 20, maxWidth: 260 }}>
          <div className="font-medium text-xs">{tooltip.n.label}</div>
           <div className="mt-0.5 text-[10px] opacity-70">{tooltip.n.type} · {tooltip.n.degree ?? 0} {t("connections")}</div>
          {tooltip.n.summary && (
            <div className="mt-1 text-[10px] opacity-80 line-clamp-3">{tooltip.n.summary}</div>
          )}
          {tooltip.n.path && (
            <div className="mt-1 text-[9px] opacity-50 truncate">{tooltip.n.path}</div>
          )}
          {(tooltip.n.createdBy || tooltip.n.createdByModel) && (
            <div className="mt-0.5 text-[9px] opacity-40">{tooltip.n.createdBy || ""}{tooltip.n.createdByModel ? ` · ${tooltip.n.createdByModel}` : ""}</div>
          )}
          {tooltip.n.edgeTypes?.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {tooltip.n.edgeTypes.slice(0, 4).map((t: string) => (
                <span key={t} className="inline-block h-1.5 w-3 rounded-sm" style={{ background: EDGE_COLORS[t] || EDGE_COLORS.default }} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
