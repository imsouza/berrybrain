"use client";

import { useParams } from "next/navigation";
import { GraphNodeDetail } from "@/components/graph-node-detail";

export default function GraphNodePage() {
  const params = useParams<{ nodeId: string }>();
  const nodeId = Number(params.nodeId);
  return Number.isInteger(nodeId) && nodeId > 0
    ? <GraphNodeDetail nodeId={nodeId} />
    : <main className="p-6 text-sm text-muted">Invalid node identifier.</main>;
}

