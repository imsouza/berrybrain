"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { apiFetch, appPath, useWorkspace } from "@/contexts/workspace-context";
import { humanNodeType, humanOrigin, humanStatus } from "./graph-formatters";

type ConfidenceInterval = {
  score?: number | null;
  lower?: number | null;
  upper?: number | null;
  sampleSize?: number;
  method?: string;
  factors?: string[];
  computedAt?: string | null;
};

type NodeConnection = {
  id: number;
  sourceNodeId: number;
  targetNodeId: number;
  type: string;
  label?: string;
  reason?: string;
  confidence?: number | null;
  confidenceInterval?: ConfidenceInterval;
  ontology?: { property?: string };
};

type NodeDetail = {
  id: number;
  type: string;
  label: string;
  title: string;
  summary?: string;
  aiSummary?: string;
  aiContext?: string;
  userNotes?: string;
  source?: string;
  sourceEvidence?: string;
  status?: string;
  createdBy?: string;
  provider?: string;
  model?: string;
  semanticState?: string;
  semanticStatus?: string;
  colorReason?: string;
  confidenceInterval?: ConfidenceInterval;
  ontology?: { class?: string; canonicalLabel?: string };
  notes?: { id: number; title: string; path: string }[];
  connections?: NodeConnection[];
};

type SemanticAnalysis = {
  state?: string;
  analysis?: {
    meaning_in_context?: string;
    use_in_notes?: string;
    why_it_matters_here?: string;
    supported_findings?: string[];
    inferences?: string[];
    uncertainties?: string[];
  } | null;
  historyCount?: number;
};

const NODE_TYPES = [
  "note", "concept", "entity", "topic", "source", "attachment", "insight",
  "context", "gap", "study_path",
];

export function GraphNodeDetail({ nodeId }: { nodeId: number }) {
  const w = useWorkspace();
  const [node, setNode] = useState<NodeDetail | null>(null);
  const [semanticAnalysis, setSemanticAnalysis] = useState<SemanticAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [feedback, setFeedback] = useState("");
  const [draft, setDraft] = useState({ type: "concept", label: "", title: "", summary: "", source: "", status: "suggested", userNotes: "" });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const response = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}/summary`);
      if (!response.ok) throw new Error("Node not found or unavailable.");
      const payload = await response.json() as NodeDetail;
      setNode(payload);
      setDraft({
        type: payload.type,
        label: payload.label,
        title: payload.title,
        summary: payload.summary || "",
        source: payload.source || "",
        status: payload.status || "suggested",
        userNotes: payload.userNotes || "",
      });
      const semanticResponse = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}/semantic-analysis`);
      if (semanticResponse.ok) setSemanticAnalysis(await semanticResponse.json() as SemanticAnalysis);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Could not load node.");
    } finally {
      setLoading(false);
    }
  }, [nodeId, w.api]);

  useEffect(() => { void load(); }, [load]);

  const inbound = useMemo(
    () => (node?.connections || []).filter((edge) => edge.targetNodeId === node?.id),
    [node],
  );
  const outbound = useMemo(
    () => (node?.connections || []).filter((edge) => edge.sourceNodeId === node?.id),
    [node],
  );

  function backToGraph() {
    window.location.href = appPath("/brain?graph=open");
  }

  function editCurrent() {
    if (!node) return;
    if (node.type === "note" && node.notes?.[0]?.path) {
      void w.openNote(node.notes[0].path);
      return;
    }
    setEditing(true);
    setFeedback("");
  }

  async function save() {
    setSaving(true);
    setFeedback("Validating node against its context...");
    try {
      const response = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(draft),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = payload.detail;
        const issues = typeof detail === "object" && Array.isArray(detail?.issues)
          ? detail.issues.join(" ")
          : typeof detail === "string" ? detail : "Node edit was rejected.";
        setFeedback(issues);
        return;
      }
      const notesResponse = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}/notes`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: draft.userNotes }),
      });
      if (!notesResponse.ok) throw new Error("Node fields were saved, but manual notes could not be saved.");
      setFeedback("Edit accepted. Graph retrieval uses the new state; judge, ontology, confidence, and clusters are recalculating.");
      setEditing(false);
      await load();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Node edit failed.");
    } finally {
      setSaving(false);
    }
  }

  async function retrySemanticAnalysis() {
    setFeedback("Queueing semantic analysis...");
    try {
      const response = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}/semantic-analysis/retry`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not queue semantic analysis.");
      setFeedback(`Semantic analysis queued${payload.jobId ? `. Job ${payload.jobId}` : ""}`);
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Could not queue semantic analysis.");
    }
  }

  async function decideInsight(action: "confirm" | "ignore") {
    setDecisionLoading(true);
    setFeedback(action === "confirm" ? "Accepting insight..." : "Rejecting insight...");
    try {
      const response = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}/${action}`, { method: "POST" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Insight decision failed.");
      setFeedback(action === "confirm" ? "Insight accepted. Graph state is updating." : "Insight rejected. Graph state is updating.");
      if (action === "ignore") {
        backToGraph();
        return;
      }
      await load();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Insight decision failed.");
    } finally {
      setDecisionLoading(false);
    }
  }

  async function deleteNode() {
    if (!node || node.type === "note" || deleting) return;
    if (!window.confirm(`Delete "${node.title || node.label}" and its relationships? This cannot be undone.`)) return;
    setDeleting(true);
    setFeedback("Deleting node and scheduling graph recalculation...");
    try {
      const response = await apiFetch(`${w.api}/api/v1/graph/nodes/${nodeId}`, { method: "DELETE" });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Node deletion failed.");
      backToGraph();
    } catch (error) {
      setFeedback(error instanceof Error ? error.message : "Node deletion failed.");
      setDeleting(false);
    }
  }

  if (loading) return <main className="min-h-0 flex-1 overflow-y-auto p-6 text-sm text-muted">Loading node...</main>;
  if (!node) return <main className="min-h-0 flex-1 overflow-y-auto p-6 text-sm text-danger">{feedback || "Node unavailable."}</main>;

  const confidence = node.confidenceInterval;
  return (
    <main className="min-h-0 flex-1 overflow-y-auto bg-background">
      <header className="border-b border-border/60 px-5 py-5 sm:px-8">
        <div className="mx-auto max-w-7xl">
          <nav className="mb-5 flex items-center gap-2" aria-label="Node navigation">
            <button className="bb-action h-9 px-3 text-xs" onClick={backToGraph}>Back to Graph</button>
          </nav>
          <div className="flex flex-col items-start justify-between gap-5 sm:flex-row">
          <div className="min-w-0">
            <div className="text-[11px] font-semibold uppercase text-accent">{humanNodeType(node.type)}</div>
            <h1 className="mt-1 break-words text-2xl font-semibold text-foreground">{node.title || node.label}</h1>
            <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-muted">
              <span>{humanStatus(node.status)}</span><span>·</span>
              <span>{humanOrigin(node.createdBy)}</span><span>·</span>
              <span>{node.semanticState || "pending"}</span>
            </div>
          </div>
          <div className="flex w-full shrink-0 flex-wrap gap-2 sm:w-auto sm:justify-end">
            {node.type === "insight" && node.status === "suggested" && <>
              <button className="bb-action bb-action--primary h-9 px-4 text-xs font-semibold" disabled={decisionLoading} onClick={() => decideInsight("confirm")}>Accept insight</button>
              <button className="bb-action h-9 px-4 text-xs font-semibold" disabled={decisionLoading} onClick={() => decideInsight("ignore")}>Reject insight</button>
            </>}
            <button className="bb-action bb-action--primary h-9 px-4 text-xs font-semibold" onClick={editCurrent}>
              {node.type === "note" ? "Edit note" : "Edit node"}
            </button>
            {node.type !== "note" && <button className="bb-action h-9 px-4 text-xs font-semibold text-danger" disabled={deleting} onClick={deleteNode}>{deleting ? "Deleting..." : "Delete node"}</button>}
          </div>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-7xl gap-10 px-5 py-8 sm:px-8 lg:grid-cols-[minmax(0,1.4fr)_minmax(320px,0.6fr)]">
        <div className="space-y-8">
          {editing ? (
            <section className="border-b border-border/60 pb-8">
              <h2 className="mb-4 text-sm font-semibold text-foreground">Edit node</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Type"><select value={draft.type} onChange={(e) => setDraft((v) => ({ ...v, type: e.target.value }))}>{NODE_TYPES.map((type) => <option key={type} value={type}>{humanNodeType(type)}</option>)}</select></Field>
                <Field label="Status"><select value={draft.status} onChange={(e) => setDraft((v) => ({ ...v, status: e.target.value }))}><option value="suggested">Suggested</option><option value="confirmed">Confirmed</option><option value="ignored">Ignored</option></select></Field>
                <Field label="Label"><input value={draft.label} onChange={(e) => setDraft((v) => ({ ...v, label: e.target.value }))} /></Field>
                <Field label="Title"><input value={draft.title} onChange={(e) => setDraft((v) => ({ ...v, title: e.target.value }))} /></Field>
                <Field label="Source"><input value={draft.source} onChange={(e) => setDraft((v) => ({ ...v, source: e.target.value }))} /></Field>
              </div>
              <Field label="Summary" wide><textarea rows={7} value={draft.summary} onChange={(e) => setDraft((v) => ({ ...v, summary: e.target.value }))} /></Field>
              <Field label="Manual notes" wide><textarea rows={4} value={draft.userNotes} onChange={(e) => setDraft((v) => ({ ...v, userNotes: e.target.value }))} /></Field>
              <div className="mt-4 flex gap-2"><button className="bb-action bb-action--primary px-4 py-2 text-xs" disabled={saving} onClick={save}>{saving ? "Validating..." : "Save"}</button><button className="bb-action px-4 py-2 text-xs" onClick={() => setEditing(false)}>Cancel</button></div>
            </section>
          ) : (
            <section><h2 className="mb-3 text-sm font-semibold text-foreground">Meaning in context</h2><p className="whitespace-pre-wrap text-sm leading-7 text-foreground/85">{node.aiSummary || node.summary || "Summary not generated."}</p>{node.aiContext && <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-muted">{node.aiContext}</p>}</section>
          )}

          <section className="border-t border-border/60 pt-7"><h2 className="mb-3 text-sm font-semibold text-foreground">Evidence and provenance</h2><p className="whitespace-pre-wrap break-words text-sm leading-7 text-muted">{node.sourceEvidence || "No source evidence recorded."}</p><div className="mt-4 text-xs text-muted">Source: {node.source || "system"} · Provider: {node.provider || "local"} · Model: {node.model || "not recorded"}</div></section>

          {semanticAnalysis?.analysis && <section className="border-t border-border/60 pt-7"><h2 className="mb-3 text-sm font-semibold text-foreground">Semantic analysis</h2><div className="space-y-4 text-sm leading-7 text-foreground/85">{semanticAnalysis.analysis.meaning_in_context && <p>{semanticAnalysis.analysis.meaning_in_context}</p>}{semanticAnalysis.analysis.use_in_notes && <p>{semanticAnalysis.analysis.use_in_notes}</p>}{semanticAnalysis.analysis.why_it_matters_here && <p>{semanticAnalysis.analysis.why_it_matters_here}</p>}</div></section>}

          <RelationshipSection title="Outgoing relationships" items={outbound} />
          <RelationshipSection title="Incoming relationships" items={inbound} />
        </div>

        <aside className="space-y-6 border-t border-border/60 pt-6 lg:border-l lg:border-t-0 lg:pl-6 lg:pt-0">
          <section><h2 className="mb-3 text-sm font-semibold text-foreground">Confidence</h2>{confidence?.sampleSize ? <><div className="text-2xl font-semibold text-foreground">{Math.round((confidence.score || 0) * 100)}%</div><div className="mt-1 text-xs text-muted">95% interval: {Math.round((confidence.lower || 0) * 100)}%–{Math.round((confidence.upper || 0) * 100)}%</div><div className="mt-2 text-[11px] text-muted">{confidence.method} · n={confidence.sampleSize}</div></> : <p className="text-xs text-muted">Unavailable until evidence is evaluated.</p>}</section>
          <section className="border-t border-border/60 pt-5"><h2 className="mb-3 text-sm font-semibold text-foreground">Ontology</h2><dl className="space-y-2 text-xs"><Row label="Class" value={node.ontology?.class || "Unmapped"} /><Row label="Canonical label" value={node.ontology?.canonicalLabel || node.label} /><Row label="Semantic status" value={node.semanticStatus || "active"} /><Row label="Cluster" value={node.colorReason || "Pending recalculation"} /></dl></section>
          <section className="border-t border-border/60 pt-5"><h2 className="mb-3 text-sm font-semibold text-foreground">Analysis state</h2><p className="text-xs text-muted">{semanticAnalysis?.state || node.semanticState || "pending"}</p>{["failed", "stale", "not_configured", "needs_review"].includes(semanticAnalysis?.state || node.semanticState || "") && <><p className="mt-2 text-xs leading-5 text-muted">{semanticAnalysis?.state === "failed" ? "The last analysis failed." : "Semantic analysis requires attention."}</p><button className="bb-action mt-3 px-3 py-1.5 text-xs" onClick={retrySemanticAnalysis}>Retry analysis</button></>}</section>
          {feedback && <p className="border-t border-border/60 pt-5 text-xs leading-5 text-muted">{feedback}</p>}
        </aside>
      </div>
    </main>
  );
}

function Field({ label, children, wide = false }: { label: string; children: React.ReactNode; wide?: boolean }) {
  return (
    <label className={`${wide ? "mt-4" : ""} block text-xs font-medium text-muted`}>
      {label}
      <div className="mt-1 [&_input]:w-full [&_input]:rounded-md [&_input]:border [&_input]:border-border [&_input]:bg-surface [&_input]:px-3 [&_input]:py-2 [&_input]:text-foreground [&_select]:w-full [&_select]:rounded-md [&_select]:border [&_select]:border-border [&_select]:bg-surface [&_select]:px-3 [&_select]:py-2 [&_select]:text-foreground [&_textarea]:w-full [&_textarea]:rounded-md [&_textarea]:border [&_textarea]:border-border [&_textarea]:bg-surface [&_textarea]:px-3 [&_textarea]:py-2 [&_textarea]:text-foreground">
        {children}
      </div>
    </label>
  );
}

function RelationshipSection({ title, items }: { title: string; items: NodeConnection[] }) {
  return <section className="border-t border-border/60 pt-7"><h2 className="mb-3 text-sm font-semibold text-foreground">{title}</h2>{items.length ? <div className="divide-y divide-border/50">{items.map((edge) => <div key={edge.id} className="py-3"><div className="flex flex-wrap items-center gap-2 text-xs"><span className="font-semibold text-accent">{edge.type}</span><span className="text-muted">{edge.ontology?.property || ""}</span>{edge.confidenceInterval?.lower != null && <span className="ml-auto text-muted">≥ {Math.round(edge.confidenceInterval.lower * 100)}%</span>}</div><p className="mt-1 text-sm leading-6 text-foreground/80">{edge.reason || edge.label || "No relationship reason recorded."}</p></div>)}</div> : <p className="text-xs text-muted">No relationships in this direction.</p>}</section>;
}

function Row({ label, value }: { label: string; value: string }) {
  return <div className="flex items-start justify-between gap-3"><dt className="text-muted">{label}</dt><dd className="break-words text-right text-foreground">{value}</dd></div>;
}
