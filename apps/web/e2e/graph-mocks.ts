import type { Page } from "@playwright/test";

type Snapshot = { nodes: Record<string, unknown>[]; edges: Record<string, unknown>[] };

/** Mock the paginated read contract, including snapshots changed by a scan. */
export async function mockGraphPages(page: Page, snapshot: () => Snapshot) {
  for (const resource of ["summary", "nodes", "edges", "palette", "delta"]) {
    await page.route(`**/api/v1/graph/${resource}*`, route => {
      const graph = snapshot();
      const body = resource === "summary"
        ? { node_count: graph.nodes.length, edge_count: graph.edges.length, orphan_count: 0, graphVersion: 91 }
        : resource === "palette" ? { colors: [] }
        : resource === "delta" ? { requiresFullRefresh: true, graphVersion: 91 }
        : { [resource]: graph[resource as "nodes" | "edges"], nextCursor: null, graphVersion: 91 };
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
    });
  }
}
