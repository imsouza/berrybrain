import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
  type Simulation,
  type SimulationNodeDatum,
} from "d3";

interface LayoutNode extends SimulationNodeDatum {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}

type LayoutRequest = {
  type?: "init";
  nodes: LayoutNode[];
  edges: Array<{ source: string; target: string }>;
  width: number;
  height: number;
  iterations?: number;
};

type LayoutInteraction =
  | { type: "drag"; id: string; x: number; y: number }
  | { type: "release"; id: string };

type LayoutMessage = LayoutRequest | LayoutInteraction;

let simulation: Simulation<LayoutNode, undefined> | null = null;
let activeNodes: LayoutNode[] = [];
let nodesById = new Map<string, LayoutNode>();
let remainingIterations = 0;
let simulationTimer: ReturnType<typeof setTimeout> | null = null;

function publish(done: boolean) {
  self.postMessage({
    done,
    positions: activeNodes.map(({ id, x, y }) => ({ id, x, y })),
  });
}

function runSimulation() {
  simulationTimer = null;
  if (!simulation || remainingIterations <= 0) {
    publish(true);
    return;
  }
  const ticks = Math.min(3, remainingIterations);
  for (let iteration = 0; iteration < ticks; iteration += 1) simulation.tick();
  remainingIterations -= ticks;
  const done = remainingIterations <= 0;
  // Small and medium graphs animate smoothly. Large projections send fewer
  // transferable snapshots while the physics still runs entirely off-thread.
  if (done || activeNodes.length <= 1_000 || remainingIterations % 12 === 0) publish(done);
  if (!done) simulationTimer = setTimeout(runSimulation, 16);
}

function scheduleSimulation(iterations: number) {
  remainingIterations = Math.max(remainingIterations, iterations);
  if (simulationTimer === null) simulationTimer = setTimeout(runSimulation, 0);
}

self.onmessage = (event: MessageEvent<LayoutMessage>) => {
  if (event.data.type === "drag") {
    const node = nodesById.get(event.data.id);
    if (!node || !simulation) return;
    node.fx = event.data.x;
    node.fy = event.data.y;
    node.x = event.data.x;
    node.y = event.data.y;
    simulation.alpha(Math.max(simulation.alpha(), 0.42));
    scheduleSimulation(9);
    return;
  }
  if (event.data.type === "release") {
    const node = nodesById.get(event.data.id);
    if (!node || !simulation) return;
    // Keep the user's anchor while connected, unpinned nodes settle.
    node.fx = node.x;
    node.fy = node.y;
    simulation.alpha(Math.max(simulation.alpha(), 0.3));
    scheduleSimulation(36);
    return;
  }

  const { nodes, edges, width, height, iterations = 120 } = event.data;
  activeNodes = nodes;
  nodesById = new Map(nodes.map((node) => [node.id, node]));
  const ids = new Set(nodes.map((node) => node.id));
  const links = edges
    .filter((edge) => ids.has(edge.source) && ids.has(edge.target))
    .map((edge) => ({ source: edge.source, target: edge.target }));
  simulation = forceSimulation<LayoutNode>(nodes)
    .stop()
    .alpha(1)
    .alphaMin(0.006)
    .alphaDecay(0.022)
    .velocityDecay(0.32)
    .force("charge", forceManyBody<LayoutNode>().strength(-35).distanceMin(8).distanceMax(320))
    .force(
      "link",
      forceLink<LayoutNode, { source: string | LayoutNode; target: string | LayoutNode }>(links)
        .id((node) => node.id)
        .distance(46)
        .strength(0.065),
    )
    .force(
      "collide",
      forceCollide<LayoutNode>().radius((node) => node.r + 5).strength(0.92).iterations(1),
    )
    .force("x", forceX<LayoutNode>(width / 2).strength(0.025))
    .force("y", forceY<LayoutNode>(height / 2).strength(0.025));

  remainingIterations = 0;
  if (simulationTimer !== null) clearTimeout(simulationTimer);
  simulationTimer = null;
  scheduleSimulation(iterations);
};

export {};
