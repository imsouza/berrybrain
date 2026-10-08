"use client";

import { useCallback, useEffect, useState } from "react";
import { readResource } from "@/lib/read-resource";

type Log = { id: number; action_type: string; description: string; created_at: string };
export function SettingsLogs({ apiUrl }: { apiUrl: string }) {
  const [logs, setLogs] = useState<Log[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [cursor, setCursor] = useState<number | null>(null);
  const load = useCallback(async (before?: number) => {
    if (apiUrl === "__demo__") return;
    setBusy(true); setError("");
    try {
      const data = await readResource(`${apiUrl}/api/v1/automation-logs?limit=50&compact=true${before ? `&before_id=${before}` : ""}`);
      setLogs(previous => before ? [...previous, ...data.logs] : data.logs);
      setCursor(data.nextCursor);
    } catch (error) { setError(error instanceof Error ? error.message : "Logs unavailable."); }
    finally { setBusy(false); }
  }, [apiUrl]);
  useEffect(() => { void load(); }, [load]);
  async function download() {
    setBusy(true); setError("");
    try {
      const data = await readResource(`${apiUrl}/api/v1/automation-logs/export?limit=1000`);
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = "berrybrain-logs.json";
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (error) { setError(error instanceof Error ? error.message : "Export failed."); }
    finally { setBusy(false); }
  }
  return <div className="space-y-3">
    <p className="text-xs text-muted">Recent automation events. Export includes up to 1,000 records; secrets and before/after note snapshots are excluded. Paths and descriptions can still be private: review before sharing.</p>
    <div className="flex gap-2"><button className="bb-action px-3 py-2 text-xs" disabled={busy} onClick={() => void load()}>Refresh logs</button><button className="bb-action px-3 py-2 text-xs" disabled={busy || apiUrl === "__demo__"} onClick={() => void download()}>Export JSON</button></div>
    {busy && <p role="status" className="text-xs text-muted">Loading logs…</p>}
    {error && <p role="alert" className="text-xs text-danger">{error}</p>}
    <ol className="max-h-80 space-y-2 overflow-auto" aria-label="Automation logs">{logs.map(log => <li key={log.id} className="rounded-lg border border-border p-3 text-xs"><time className="text-muted">{log.created_at}</time><strong className="ml-2">{log.action_type}</strong><p className="mt-1 whitespace-pre-wrap break-words">{log.description}</p></li>)}</ol>
    {!busy && !error && !logs.length && <p className="text-xs text-muted">No automation logs.</p>}
    {cursor && <button className="bb-action px-3 py-2 text-xs" disabled={busy} onClick={() => void load(cursor)}>Load older logs</button>}
  </div>;
}
