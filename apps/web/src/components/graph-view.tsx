"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { t } from "@/i18n";
import { getBrowserGraphData } from "@/lib/browser-storage";

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
};
type GEdge = {
  id?: number | string;
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
const TEXT_SEC = "#7A6A5C";

interface LN { x: number; y: number; vx: number; vy: number; r: number; node: GNode }
export type GraphLayoutMode = "brain" | "radial" | "type" | "connections";

export function useGraphData(apiUrl: string) {
  const [data, setData] = useState<{ nodes: GNode[]; edges: GEdge[]; stats: any } | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    // ponytail: demo has no backend, render empty graph instead of erroring
    if (apiUrl === "__demo__") { setData({ nodes: [], edges: [], stats: {} }); return; }
    if (apiUrl === "__browser__") {
      const load = () => getBrowserGraphData().then(setData).catch(() => setError(true));
      void load();
      window.addEventListener("bb:browser-knowledge-updated", load);
      return () => window.removeEventListener("bb:browser-knowledge-updated", load);
    }
    fetch(`${apiUrl}/api/v1/graph`)
      .then(r => r.json()).then(setData).catch(() => setError(true));
  }, [apiUrl]);
  const reload = useCallback(() => {
    if (apiUrl === "__demo__") return;
    if (apiUrl === "__browser__") {
      setError(false);
      getBrowserGraphData()
        .then(setData)
        .catch(() => setError(true));
      return;
    }
    setError(false);
    fetch(`${apiUrl}/api/v1/graph`).then(r => r.json()).then(setData).catch(() => setError(true));
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

function forceStep(layout: LN[], edges: GEdge[], alpha: number, W: number, H: number) {
  for (const n of layout) {
    const cx = W / 2, cy = H / 2;
    n.vx += (cx - n.x) * 0.001 * alpha;
    n.vy += (cy - n.y) * 0.001 * alpha;
  }
  for (const e of edges) {
    const s = layout.find(l => l.node.id === e.source);
    const t = layout.find(l => l.node.id === e.target);
    if (!s || !t) continue;
    const dx = t.x - s.x, dy = t.y - s.y;
    const dist = Math.max(Math.hypot(dx, dy), 1);
    const target = s.r + t.r + 60;
    const force = (dist - target) / dist * 0.02 * alpha;
    s.vx += dx * force; s.vy += dy * force;
    t.vx -= dx * force; t.vy -= dy * force;
  }
  for (let i = 0; i < layout.length; i++) {
    for (let j = i + 1; j < layout.length; j++) {
      const a = layout[i], b = layout[j];
      const dx = b.x - a.x, dy = b.y - a.y;
      const dist = Math.max(Math.hypot(dx, dy), 1);
      const target = a.r + b.r + 30;
      if (dist < target) {
        const force = (target - dist) / dist * 0.04 * alpha;
        a.vx -= dx * force; a.vy -= dy * force;
        b.vx += dx * force; b.vy += dy * force;
      }
    }
  }
  for (const n of layout) {
    n.vx *= 0.85; n.vy *= 0.85;
    n.x += n.vx; n.y += n.vy;
    n.x = Math.max(n.r, Math.min(W - n.r, n.x));
    n.y = Math.max(n.r, Math.min(H - n.r, n.y));
  }
}

export function GraphCanvas({
  data, onNavigate, onSelect, selectedId, highlightedIds = [], zoom, setZoom, pan, setPan, layoutMode = "brain",
}: {
  data: { nodes: GNode[]; edges: GEdge[] };
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
  const dragRef = useRef({ active: false, ox: 0, oy: 0, nodeIdx: -1 });
  const simRef = useRef(false);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; n: any } | null>(null);
  const W = 6000, H = 6000;
  const knownNodes = useRef<Set<string>>(new Set());
  const freshNodes = useRef<Map<string, number>>(new Map()); // id → added timestamp

  const tctx = useRef(tooltipCtx(data));
  useEffect(() => { tctx.current = tooltipCtx(data); }, [data]);
  const highlighted = new Set(highlightedIds);

  const initLayout = useCallback(() => {
    const now = performance.now();
    if (knownNodes.current.size === 0) {
      // First render — consider all nodes existing, don't pulse
      for (const node of data.nodes) {
        knownNodes.current.add(node.id);
      }
    } else {
      for (const node of data.nodes) {
        if (!knownNodes.current.has(node.id)) {
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

    const layout: LN[] = data.nodes.map((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, data.nodes.length);
      const r = n.type === "note" ? (n.connectionsCount && n.connectionsCount > 3 ? 28 : 22) : n.type === "concept" ? 24 : 20;
      if (layoutMode === "type") {
        const col = typeIndex.get(n.type) || 0;
        const group = byType.get(n.type) || [];
        const pos = group.findIndex((item) => item.id === n.id);
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
  }, [data, layoutMode]);

  useEffect(() => { initLayout(); }, [initLayout]);

  useEffect(() => {
    if (simRef.current) return;
    simRef.current = true;
    let alpha = 1;
    let maxIter = 300;
    const sim = () => {
      alpha *= 0.99;
      if (layoutMode === "brain") forceStep(layoutRef.current, data.edges, alpha, W, H);
      if (alpha > 0.01 && --maxIter > 0) requestAnimationFrame(sim);
      else simRef.current = false;
    };
    requestAnimationFrame(sim);
  }, [data]);

  useEffect(() => {
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

      for (const e of data.edges) {
        const s = nodes.find(n => n.node.id === e.source);
        const t = nodes.find(n => n.node.id === e.target);
        if (!s || !t) continue;
        const isHighlightedEdge = highlighted.has(e.source) || highlighted.has(e.target);
        ct.beginPath();
        ct.moveTo(s.x, s.y);
        ct.lineTo(t.x, t.y);
        ct.strokeStyle = isHighlightedEdge ? "#D98A00CC" : (EDGE_COLORS[e.type] || EDGE_COLORS.default) + "70";
        ct.lineWidth = isHighlightedEdge ? 3 : (e.confidence || 0.5) * 2;
        ct.stroke();
      }

      for (const n of nodes) {
        const isSel = n.node.id === selectedId;
        const isHighlighted = highlighted.has(n.node.id);
        const isOrphan = (tctx.current.get(n.node.id)?.degree || 0) === 0;
        const nodeType = n.node.type as NodeColorKey;
        const colors = isSel ? COLORS.selected : isOrphan ? COLORS.orphan : COLORS[nodeType] || COLORS.note;
        const r = isSel ? n.r * 1.2 : n.r;
        const isInsight = n.node.type === "insight";
        const addedAt = freshNodes.current.get(n.node.id);
        const isNew = addedAt && (performance.now() - addedAt) < 4000;
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

        ct.fillStyle = "#3E3024";
        ct.font = `${isSel ? "14px" : "12px"} system-ui, sans-serif`;
        ct.textAlign = "center";
        ct.textBaseline = "middle";
        const lbl = n.node.label.length > 18 ? n.node.label.slice(0, 17) + "\u2026" : n.node.label;
        ct.fillText(lbl, n.x, n.y + 1);
      }
      ct.restore();
      raf = requestAnimationFrame(render);
    }
    render();
    return () => cancelAnimationFrame(raf);
  }, [data, zoom, pan, selectedId, highlightedIds]);

  const toWorld = (cx: number, cy: number) => {
    if (!containerRef.current) return { x: 0, y: 0 };
    const r = containerRef.current.getBoundingClientRect();
    return {
      x: (cx - r.left - r.width / 2 - pan.x) / zoom + W / 2,
      y: (cy - r.top - r.height / 2 - pan.y) / zoom + H / 2,
    };
  };

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden cursor-grab" style={{ background: BG }}>
      <canvas ref={canvasRef} className="absolute"
        onMouseDown={e => {
          const w = toWorld(e.clientX, e.clientY);
          const hit = layoutRef.current.findIndex(n => Math.hypot(w.x - n.x, w.y - n.y) < n.r);
          if (hit >= 0) { dragRef.current = { active: true, ox: 0, oy: 0, nodeIdx: hit }; return; }
          dragRef.current = { active: true, ox: e.clientX, oy: e.clientY, nodeIdx: -1 };
        }}
        onMouseMove={e => {
          if (dragRef.current.active) {
            if (dragRef.current.nodeIdx >= 0) {
              const n = layoutRef.current[dragRef.current.nodeIdx];
              const w = toWorld(e.clientX, e.clientY);
              n.x = w.x; n.y = w.y;
            } else {
              setPan({ x: pan.x + e.clientX - dragRef.current.ox, y: pan.y + e.clientY - dragRef.current.oy });
              dragRef.current.ox = e.clientX; dragRef.current.oy = e.clientY;
            }
            return;
          }
          const w = toWorld(e.clientX, e.clientY);
          const hit = layoutRef.current.find(n => Math.hypot(w.x - n.x, w.y - n.y) < n.r);
          if (hit) {
            const info = tctx.current.get(hit.node.id);
            setTooltip({ x: e.clientX, y: e.clientY, n: { ...hit.node, degree: info?.degree, edgeTypes: info?.edgeTypes } });
          } else setTooltip(null);
        }}
        onMouseUp={() => { dragRef.current.active = false; dragRef.current.nodeIdx = -1; }}
        onDoubleClick={e => {
          const w = toWorld(e.clientX, e.clientY);
          const hit = layoutRef.current.find(n => Math.hypot(w.x - n.x, w.y - n.y) < n.r);
          if (hit?.node.path && onNavigate) { onSelect?.(null); onNavigate(hit.node.path); }
        }}
        onClick={e => {
          if (dragRef.current.active) return;
          const w = toWorld(e.clientX, e.clientY);
          const hit = layoutRef.current.find(n => Math.hypot(w.x - n.x, w.y - n.y) < n.r);
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
