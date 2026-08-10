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
  note: { fill: "#BF1755", border: "#8F123F", label: "#3E3024" },
  concept: { fill: "#D98A00", border: "#9B6200", label: "#3E3024" },
  topico: { fill: "#83A637", border: "#668329", label: "#3E3024" },
  topic: { fill: "#83A637", border: "#668329", label: "#3E3024" },
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
  selected: { fill: "#BF1755", border: "#3E3024", glow: "rgba(191,23,85,0.3)" },
  central: { fill: "#B90F4D", border: "#5E0A29", label: "#3E3024" },
};
type NodeColorKey = keyof typeof COLORS;

const EDGE_COLORS: Record<string, string> = {
  explicit_link: "#3C8F5A", semantic_relation: "#D98A00", derived_from: "#4F7CCB",
  mentions: "#83A637", supports: "#4A8F6A", contradicts: "#B85C4A",
  contrasts_with: "#8B6F9F", duplicates: "#B85C4A", example_of: "#4A8F6A", applies_to: "#9F6B4A",
  semantic: "#D98A00", semantic_similarity: "#D98A00", shared_concept: "#BF1755",
  shared_context: "#8B6F9F", backlink: "#3C8F5A", prerequisite: "#3C8F5A", related: "#6B4A2D",
  duplicate: "#B85C4A", contrast: "#8B6F9F", example: "#4A8F6A",
  application: "#9F6B4A", inferred: "#9EBF61", default: "#B89B82",
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
  const layoutByIdRef = useRef<Map<string, LN>>(new Map());
  const spatialIndexRef = useRef<Map<string, LN[]>>(new Map());
  const dragRef = useRef({ active: false, ox: 0, oy: 0, nodeIdx: -1, vx: 0, vy: 0, lastT: 0 });
  const simulationRef = useRef<Simulation<LN, undefined> | null>(null);
  const zoomBehaviorRef = useRef<ZoomBehavior<HTMLCanvasElement, unknown> | null>(null);
  const fitGraphRef = useRef<((duration?: number) => void) | null>(null);
  const userMovedCameraRef = useRef(false);
  const viewRef = useRef({ zoom, pan });
  const [renderRevision, setRenderRevision] = useState(0);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; n: any } | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const W = 6000, H = 6000;
  const knownNodes = useRef<Set<string>>(new Set());
  const freshNodes = useRef<Map<string, number>>(new Map()); // id → added timestamp

  const tctx = useRef<Map<string, any>>(new Map());
  useEffect(() => { tctx.current = tooltipCtx(data); }, [data]);
  useEffect(() => { viewRef.current = { zoom, pan }; }, [pan, zoom]);
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
      const r = Math.max(10, Math.min(26, 10 + Math.sqrt(degree) * 3.2 + (n.type === "note" ? 2 : 0)));
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
        setZoom(nextZoom);
        setPan(nextPan);
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
      selection.interrupt().on(".zoom", null);
      zoomBehaviorRef.current = null;
      fitGraphRef.current = null;
    };
  }, [setPan, setZoom]);

  useEffect(() => {
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
    const ids = new Set(nodes.map((node) => node.node.id));
    const links = data.edges
      .filter((edge) => ids.has(edge.source) && ids.has(edge.target))
      .map((edge) => ({ source: edge.source, target: edge.target }));
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // Keep very large vaults off the main thread. The worker runs the same D3
    // forces; normal graphs stay live here so dragging can continuously reheat them.
    if (nodes.length >= 8_000) {
      const worker = new Worker(new URL("./graph-layout.worker.ts", import.meta.url));
      const fitTimers = [550, 1_400, 2_600].map((delay) => window.setTimeout(() => {
        if (!userMovedCameraRef.current) fitGraphRef.current?.(520);
      }, delay));
      worker.onmessage = (event: MessageEvent<{ done: boolean; positions: Array<{ id: string; x: number; y: number }> }>) => {
        for (const target of event.data.positions) {
          const node = layoutByIdRef.current.get(target.id);
          if (!node) continue;
          node.x = target.x;
          node.y = target.y;
        }
        setRenderRevision((value) => value + 1);
        if (event.data.done) persistLayout();
      };
      worker.postMessage({
        nodes: nodes.map((node) => ({
          id: node.node.id,
          x: node.x,
          y: node.y,
          vx: 0,
          vy: 0,
          r: node.r,
        })),
        edges: links,
        width: W,
        height: H,
        iterations: reduceMotion ? 1 : nodes.length >= 5_000 ? 30 : 60,
      });
      return () => {
        worker.terminate();
        fitTimers.forEach(window.clearTimeout);
      };
    }

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
      const ct = ctx;
      ct.clearRect(0, 0, width, height);
      ct.save();
      ct.translate(width / 2 + pan.x, height / 2 + pan.y);
      ct.scale(zoom, zoom);
      ct.translate(-W / 2, -H / 2);

      const nodes = layoutRef.current;
      const nodeIndex = layoutByIdRef.current;
      const margin = 100;
      const visibleCandidates = nodes.filter((node) => {
        const screenX = width / 2 + pan.x + zoom * (node.x - W / 2);
        const screenY = height / 2 + pan.y + zoom * (node.y - H / 2);
        return screenX >= -margin && screenX <= width + margin
          && screenY >= -margin && screenY <= height + margin;
      });
      const largeGraph = data.nodes.length >= 5_000;
      const nodeBudget = largeGraph ? 320 : zoom < 0.5 ? 400 : zoom < 1.5 ? 500 : 2_000;
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

      const edgeBudget = largeGraph ? 600 : zoom < 0.5 ? 800 : zoom < 1.5 ? 900 : 5_000;
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
        ct.lineWidth = isHighlightedEdge ? 1.8 : Math.max(0.65, (e.confidence || 0.5) * 1.35);
        ct.stroke();
        ct.globalAlpha = 1;
        renderedEdges += 1;
      }

      let hasActivePulse = false;
      const showLabels = visibleNodes.length <= 80
        ? zoom >= 0.75
        : visibleNodes.length <= 600
          ? zoom >= 1.35
          : zoom >= 2.5;
      const labelColor = getComputedStyle(containerRef.current!).getPropertyValue("--color-foreground").trim() || "#1D1B18";
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
        const colors = semanticColor
          ? { fill: semanticColor.lightHex, border: semanticColor.border, label: semanticColor.text }
          : n.node.colorId === "pending"
            ? COLORS.orphan
            : fallbackColors;
        const r = isSel ? n.r * 1.2 : n.r;
        const addedAt = freshNodes.current.get(n.node.id);
        const isNew = addedAt && (performance.now() - addedAt) < 4000;
        hasActivePulse = hasActivePulse || Boolean(isNew);
        const pulsePhase = isNew ? (performance.now() - addedAt) / 4000 : 1; // 0 → 1 over 4s

        ct.globalAlpha = isDimmed ? 0.14 : 1;
        if (isSel || isHighlighted) {
          ct.beginPath(); ct.arc(n.x, n.y, r + 6, 0, Math.PI * 2);
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
        ct.beginPath(); ct.arc(n.x, n.y, r, 0, Math.PI * 2);
        ct.fillStyle = colors.fill; ct.fill();
        ct.strokeStyle = isHighlighted ? COLORS.selected.fill : colors.border;
        ct.lineWidth = isHighlighted ? 2.4 : 1.25;
        ct.stroke();
        ct.setLineDash([]);

        ct.globalAlpha = 1;
      }

      const shouldRenderLabels = showLabels || Boolean(selectedId || hoveredId || highlighted.size);
      const labelBoxes: Array<{ left: number; right: number; top: number; bottom: number }> = [];
      const labelCandidates = shouldRenderLabels ? [...visibleNodes].sort((a, b) => {
        const aActive = a.node.id === selectedId || a.node.id === hoveredId || highlighted.has(a.node.id);
        const bActive = b.node.id === selectedId || b.node.id === hoveredId || highlighted.has(b.node.id);
        if (aActive !== bActive) return aActive ? -1 : 1;
        return (tctx.current.get(b.node.id)?.degree || 0) - (tctx.current.get(a.node.id)?.degree || 0);
      }) : [];
      ct.textAlign = "center";
      ct.textBaseline = "middle";
      for (const node of labelCandidates) {
        const isActive = node.node.id === selectedId || node.node.id === hoveredId || highlighted.has(node.node.id);
        if (!showLabels && !isActive) continue;
        const isDimmed = Boolean(focusId) && !focusedIds.has(node.node.id);
        const label = node.node.label.length > 18 ? `${node.node.label.slice(0, 17)}\u2026` : node.node.label;
        ct.font = `${node.node.id === selectedId ? "12px" : "11px"} Inter, system-ui, sans-serif`;
        const halfWidth = ct.measureText(label).width / 2 + 4;
        const centerY = node.y;
        const box = { left: node.x - halfWidth, right: node.x + halfWidth, top: centerY - 7, bottom: centerY + 7 };
        const overlaps = labelBoxes.some((placed) => !(
          box.right < placed.left || box.left > placed.right || box.bottom < placed.top || box.top > placed.bottom
        ));
        if (overlaps && !isActive) continue;
        labelBoxes.push(box);
        ct.globalAlpha = isDimmed ? 0.14 : 1;
        ct.fillStyle = labelColor;
        ct.fillText(label, node.x, centerY);
      }
      ct.globalAlpha = 1;
      ct.restore();
      if (hasActivePulse) raf = requestAnimationFrame(render);
    }
    render();
    return () => cancelAnimationFrame(raf);
  }, [data, zoom, pan, selectedId, hoveredId, focusId, focusRoots, focusedIds, highlighted, renderRevision]);

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

  const releaseDrag = () => {
    const drag = dragRef.current;
    const node = drag.nodeIdx >= 0 ? layoutRef.current[drag.nodeIdx] : undefined;
    drag.active = false;
    drag.nodeIdx = -1;
    if (!node) return;
    node.fx = null;
    node.fy = null;
    node.vx = drag.vx * 16;
    node.vy = drag.vy * 16;
    simulationRef.current?.alphaTarget(0).restart();
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
        onMouseDown={e => {
          const candidate = findNodeAt(e.clientX, e.clientY);
          const hit = candidate ? layoutRef.current.indexOf(candidate) : -1;
          if (hit < 0) return;
          const node = layoutRef.current[hit];
          node.fx = node.x;
          node.fy = node.y;
          simulationRef.current?.alphaTarget(0.3).restart();
          dragRef.current = { active: true, ox: 0, oy: 0, nodeIdx: hit, vx: 0, vy: 0, lastT: performance.now() };
        }}
        onMouseMove={e => {
          if (dragRef.current.active) {
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
            setTooltip({ x: e.clientX, y: e.clientY, n: { ...hit.node, degree: info?.degree, edgeTypes: info?.edgeTypes } });
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
          if (dragRef.current.active) return;
          const hit = findNodeAt(e.clientX, e.clientY);
          onSelect?.(hit ? hit.node.id : null);
        }}
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
                <span key={t} className="inline-block h-1.5 w-3 rounded-sm" style={{ background: edgeColor(t) }} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
