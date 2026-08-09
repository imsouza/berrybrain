import {
  forceCollide,
  forceLink,
  forceManyBody,
  forceSimulation,
  forceX,
  forceY,
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
  nodes: LayoutNode[];
  edges: Array<{ source: string; target: string }>;
  width: number;
  height: number;
  iterations?: number;
};

self.onmessage = (event: MessageEvent<LayoutRequest>) => {
  const { nodes, edges, width, height, iterations = 120 } = event.data;
  const ids = new Set(nodes.map((node) => node.id));
  const links = edges
    .filter((edge) => ids.has(edge.source) && ids.has(edge.target))
    .map((edge) => ({ source: edge.source, target: edge.target }));
  const simulation = forceSimulation<LayoutNode>(nodes)
    .stop()
    .alpha(1)
    .alphaMin(0.006)
    .alphaDecay(0.022)
    .velocityDecay(0.15)
    .force("charge", forceManyBody<LayoutNode>().strength(-42).distanceMin(18).distanceMax(520))
    .force(
      "link",
      forceLink<LayoutNode, { source: string | LayoutNode; target: string | LayoutNode }>(links)
        .id((node) => node.id)
        .distance(74)
        .strength(0.11),
    )
    .force(
      "collide",
      forceCollide<LayoutNode>().radius((node) => node.r + 11).strength(0.94).iterations(1),
    )
    .force("x", forceX<LayoutNode>(width / 2).strength(0.018))
    .force("y", forceY<LayoutNode>(height / 2).strength(0.018));

  let iteration = 0;
  const simulate = () => {
    const chunkEnd = Math.min(iterations, iteration + 4);
    for (; iteration < chunkEnd; iteration += 1) simulation.tick();
    self.postMessage({
      done: iteration >= iterations,
      positions: nodes.map(({ id, x, y }) => ({ id, x, y })),
    });
    if (iteration < iterations) setTimeout(simulate, 16);
  };
  simulate();
};

export {};
