type LayoutNode = {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
};

type LayoutEdge = {
  source: string;
  target: string;
};

type LayoutRequest = {
  nodes: LayoutNode[];
  edges: LayoutEdge[];
  width: number;
  height: number;
  iterations?: number;
};

self.onmessage = (event: MessageEvent<LayoutRequest>) => {
  const { nodes, edges, width, height, iterations = 180 } = event.data;
  const byId = new Map(nodes.map((node) => [node.id, node]));
  let alpha = 1;

  for (let iteration = 0; iteration < iterations; iteration += 1) {
    alpha *= 0.985;
    for (const node of nodes) {
      node.vx += (width / 2 - node.x) * 0.0008 * alpha;
      node.vy += (height / 2 - node.y) * 0.0008 * alpha;
    }

    for (const edge of edges) {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) continue;
      const dx = target.x - source.x;
      const dy = target.y - source.y;
      const distance = Math.max(Math.hypot(dx, dy), 1);
      const desired = source.r + target.r + 60;
      const force = ((distance - desired) / distance) * 0.018 * alpha;
      source.vx += dx * force;
      source.vy += dy * force;
      target.vx -= dx * force;
      target.vy -= dy * force;
    }

    const cellSize = 100;
    const grid = new Map<string, LayoutNode[]>();
    for (const node of nodes) {
      const cellX = Math.floor(node.x / cellSize);
      const cellY = Math.floor(node.y / cellSize);
      for (let offsetX = -1; offsetX <= 1; offsetX += 1) {
        for (let offsetY = -1; offsetY <= 1; offsetY += 1) {
          const nearby = grid.get(`${cellX + offsetX}:${cellY + offsetY}`) || [];
          for (const other of nearby) {
            const dx = node.x - other.x;
            const dy = node.y - other.y;
            const distance = Math.max(Math.hypot(dx, dy), 1);
            const desired = node.r + other.r + 28;
            if (distance >= desired) continue;
            const force = ((desired - distance) / distance) * 0.035 * alpha;
            node.vx += dx * force;
            node.vy += dy * force;
            other.vx -= dx * force;
            other.vy -= dy * force;
          }
        }
      }
      const key = `${cellX}:${cellY}`;
      grid.set(key, [...(grid.get(key) || []), node]);
    }

    for (const node of nodes) {
      node.vx *= 0.84;
      node.vy *= 0.84;
      node.x = Math.max(node.r, Math.min(width - node.r, node.x + node.vx));
      node.y = Math.max(node.r, Math.min(height - node.r, node.y + node.vy));
    }
  }

  self.postMessage({
    positions: nodes.map(({ id, x, y }) => ({ id, x, y })),
  });
};

export {};
