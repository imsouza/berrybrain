export type DiagnosticCode =
  | "VAULT_MISSING"
  | "NO_NOTES_SCANNED"
  | "NOTES_SCANNED_JOBS_PENDING"
  | "GRAPH_JOBS_FAILED"
  | "GRAPH_HIDDEN_BY_FILTERS"
  | "LAST_GRAPH_JOB_FAILED"
  | "NO_WORKER_HEARTBEAT"
  | "DB_NOT_WRITABLE";

export interface PipelineDiagnostic {
  api_db_path?: string;
  worker?: unknown;
  notes_total?: number;
  vault?: unknown;
  last_note?: unknown;
  graph_jobs?: unknown;
  graph_nodes?: unknown;
  graph_edges?: unknown;
  last_graph_job?: unknown;
  diagnostics: { code: DiagnosticCode; message: string }[];
}

export const DIAGNOSTIC_KEY: Record<DiagnosticCode, string> = {
  VAULT_MISSING: "diagVaultMissing",
  NO_NOTES_SCANNED: "diagNoNotes",
  NOTES_SCANNED_JOBS_PENDING: "diagJobsPending",
  GRAPH_JOBS_FAILED: "diagJobsFailed",
  GRAPH_HIDDEN_BY_FILTERS: "diagHiddenByFilters",
  LAST_GRAPH_JOB_FAILED: "diagLastGraphJobFailed",
  NO_WORKER_HEARTBEAT: "diagWorkerNoHeartbeat",
  DB_NOT_WRITABLE: "diagDbNotWritable",
};

export const DIAGNOSTIC_DEFAULT_TEXT: Record<DiagnosticCode, string> = {
  VAULT_MISSING: "Vault path not set; the API cannot read your notes.",
  NO_NOTES_SCANNED: "No notes scanned yet. Run a vault scan to populate the graph.",
  NOTES_SCANNED_JOBS_PENDING: "Notes were scanned, but graph jobs are still pending. Wait for the worker to finish.",
  GRAPH_JOBS_FAILED: "One or more graph jobs failed. Check the worker logs and retry.",
  GRAPH_HIDDEN_BY_FILTERS: "Graph has nodes, but the current filters are hiding them.",
  LAST_GRAPH_JOB_FAILED: "The last graph job failed. See worker logs for details.",
  NO_WORKER_HEARTBEAT: "No worker heartbeat received. Make sure the worker process is running.",
  DB_NOT_WRITABLE: "The API database is not writable. Check filesystem permissions.",
};

export function diagnosticMessages(payload: PipelineDiagnostic | null | undefined): { code: DiagnosticCode; text: string }[] {
  if (!payload || !Array.isArray(payload.diagnostics)) return [];
  return payload.diagnostics.map((d) => ({
    code: d.code,
    text: d.message || DIAGNOSTIC_DEFAULT_TEXT[d.code] || d.code,
  }));
}

export interface FilterState {
  filterType?: string;
  filterStatus?: string;
  filterProvider?: string;
  filterConfidence?: number;
}

export interface GraphLikeData {
  nodes?: { id: string; type?: string; status?: string; provider?: string; confidence?: number }[];
  edges?: unknown[];
  stats?: Record<string, unknown>;
}

export function isFilterHidden(graphData: GraphLikeData | null | undefined, filters: FilterState): boolean {
  if (!graphData || (graphData.nodes?.length ?? 0) === 0) return false;
  if (filters.filterType && filters.filterType !== "all" && filters.filterType !== "brain_view") return true;
  if (filters.filterStatus && filters.filterStatus !== "all") return true;
  if (filters.filterProvider && filters.filterProvider !== "all") return true;
  if (filters.filterConfidence && filters.filterConfidence > 0) return true;
  return false;
}

export interface WorkerStats {
  last_heartbeat_at?: string | null;
  status?: string;
}

export function workerHeartbeatStale(
  stats: { worker?: WorkerStats; notes?: number; connections?: number; jobs?: { pending: number } } | null | undefined,
  staleAfterMs = 2 * 60 * 1000,
): boolean {
  if (!stats || !stats.worker) return true;
  const ts = stats.worker.last_heartbeat_at;
  if (!ts) return true;
  const parsed = Date.parse(ts);
  if (Number.isNaN(parsed)) return true;
  return Date.now() - parsed > staleAfterMs;
}
