"use client";

import { useEffect, useState } from "react";
import { apiFetch, appPath } from "@/contexts/workspace-context";
import { askReferenceHref, type AskReference } from "./ask-markdown";

type ActionPlan = {
  id: string;
  arguments: { title: string; folder: string; content: string; newVaultName?: string | null; targetVaultId?: string | null; targetVaultName?: string | null };
  argumentsHash: string;
  attempts?: number;
  status: string;
  expiresAt: string;
  approvedAt: string | null;
  resultPath: string | null;
  vaultId?: string | null;
  recoveryPath?: string | null;
  orphanPath?: string | null;
  evidenceStatus: "draft" | "eligible" | null;
  errorCode?: string | null;
};

type SavedDraft = { content: string; content_hash: string };

const folders = ["inbox", "study", "permanent", "review", "templates"];

function noteContent(answer: string, references: AskReference[]): string {
  const linked = answer.replace(/\[([^\]]+)\]\(bbref:([^)]*)\)/g, (_match, label: string, evidenceId: string) => {
    const reference = references.find((item) => item.current && item.evidenceIds.includes(evidenceId));
    const href = reference ? askReferenceHref(reference) : null;
    return href ? `[${label.replaceAll("]", "\\]")}](${href})` : label;
  });
  return linked.trim();
}

export function AskNotePlan({ answer, question, references = [], apiUrl, resumePlanId, onReleased, onClose }: {
  answer: string;
  question: string;
  references?: AskReference[];
  apiUrl: string;
  resumePlanId?: string;
  onReleased?: () => void;
  onClose?: () => void;
}) {
  const [open, setOpen] = useState(Boolean(resumePlanId));
  const [title, setTitle] = useState(question.slice(0, 100) || "Ask draft");
  const [folder, setFolder] = useState("study");
  const [destination, setDestination] = useState<"default" | "existing_vault" | "new_vault">("default");
  const [newVaultName, setNewVaultName] = useState("");
  const [existingVaultId, setExistingVaultId] = useState("");
  const [vaults, setVaults] = useState<Array<{ id: string; name: string }>>([]);
  const [content, setContent] = useState(() => noteContent(answer, references));
  const [plan, setPlan] = useState<ActionPlan | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [requestKey, setRequestKey] = useState<string | null>(null);
  const [reviewed, setReviewed] = useState(false);
  const [savedDraft, setSavedDraft] = useState<SavedDraft | null>(null);
  const [orphanDraft, setOrphanDraft] = useState<SavedDraft | null>(null);
  const [orphanReviewed, setOrphanReviewed] = useState(false);

  useEffect(() => {
    if (!open || resumePlanId) return;
    let cancelled = false;
    apiFetch(`${apiUrl}/api/v1/vault/namespaces`).then(async (response) => {
      if (!response.ok) return;
      const payload = await response.json() as { vaults?: Array<{ id: string; name: string }> };
      if (cancelled) return;
      const named = (payload.vaults || []).filter((item) => item.id !== "default");
      setVaults(named);
      setExistingVaultId((current) => current || named[0]?.id || "");
    }).catch(() => undefined);
    return () => { cancelled = true; };
  }, [apiUrl, open, resumePlanId]);

  useEffect(() => {
    if (!resumePlanId) return;
    let cancelled = false;
    apiFetch(`${apiUrl}/api/v1/ask/action-plans/${resumePlanId}`).then(async (response) => {
      if (!response.ok) throw new Error("Saved draft could not be reopened.");
      const current = await response.json() as ActionPlan;
      if (!["completed", "partial", "failed"].includes(current.status)) throw new Error("Saved plan is no longer available.");
      if (!cancelled) setPlan(current);
    }).catch((error) => {
      if (!cancelled) setMessage(error instanceof Error ? error.message : "Saved draft could not be reopened.");
    });
    return () => { cancelled = true; };
  }, [apiUrl, resumePlanId]);

  useEffect(() => {
    if (!["completed", "partial"].includes(plan?.status || "") || plan?.evidenceStatus !== "draft" || !plan?.resultPath) return;
    let cancelled = false;
    const path = plan.resultPath.split("/").map(encodeURIComponent).join("/");
    apiFetch(`${apiUrl}/api/v1/notes/${path}`).then(async (response) => {
      if (!response.ok) throw new Error("Could not load the saved draft for review.");
      const note = await response.json() as SavedDraft;
      if (!cancelled) { setSavedDraft(note); setReviewed(false); }
    }).catch(() => { if (!cancelled) setMessage("Could not load the saved draft for review. Try Refresh draft."); });
    return () => { cancelled = true; };
  }, [apiUrl, plan?.id, plan?.status, plan?.evidenceStatus, plan?.resultPath]);

  useEffect(() => {
    if (plan?.status !== "failed" || !plan.orphanPath || plan.recoveryPath) return;
    let cancelled = false;
    setOrphanDraft(null);
    setOrphanReviewed(false);
    const path = plan.orphanPath.split("/").map(encodeURIComponent).join("/");
    apiFetch(`${apiUrl}/api/v1/notes/${path}`).then(async (response) => {
      if (!response.ok) throw new Error("Could not load the saved file for review.");
      const note = await response.json() as SavedDraft;
      if (!cancelled) setOrphanDraft(note);
    }).catch((error) => {
      if (!cancelled) setMessage(error instanceof Error ? error.message : "Could not load the saved file for review.");
    });
    return () => { cancelled = true; };
  }, [apiUrl, plan?.id, plan?.status, plan?.orphanPath, plan?.recoveryPath]);

  async function refreshDraft() {
    if (!plan) return;
    setBusy(true);
    setReviewed(false);
    setSavedDraft(null);
    setMessage("");
    try {
      const planResponse = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}`);
      if (!planResponse.ok) throw new Error("Could not refresh the action plan.");
      const currentPlan = await planResponse.json() as ActionPlan;
      setPlan(currentPlan);
      if (!["completed", "partial"].includes(currentPlan.status) || currentPlan.evidenceStatus !== "draft" || !currentPlan.resultPath) {
        throw new Error("Saved draft is no longer available for review.");
      }
      const path = currentPlan.resultPath.split("/").map(encodeURIComponent).join("/");
      const response = await apiFetch(`${apiUrl}/api/v1/notes/${path}`);
      if (!response.ok) throw new Error("Could not load the saved draft for review.");
      setSavedDraft(await response.json() as SavedDraft);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load the saved draft for review.");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    if (!plan || plan.status !== "executing") return;
    let cancelled = false;
    let checking = false;
    const timer = window.setInterval(async () => {
      if (checking) return;
      checking = true;
      try {
        const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}`);
        if (!response.ok) return;
        const current = await response.json() as ActionPlan;
        if (cancelled) return;
        setPlan(current);
        if (current.status === "completed") setMessage("");
        if (current.status === "executing" && current.approvedAt && Date.now() - Date.parse(current.approvedAt) > 95000) {
          const resumed = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}/approve`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ arguments_hash: plan.argumentsHash }),
          });
          if (resumed.ok && !cancelled) {
            const completed = await resumed.json() as ActionPlan;
            setPlan(completed);
            if (completed.status === "completed") setMessage("");
          }
        }
      } catch {
        if (!cancelled) setMessage("Save status is temporarily unavailable. This plan can be resumed safely.");
      } finally {
        checking = false;
      }
    }, 5000);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [apiUrl, plan]);

  async function propose() {
    const key = requestKey ?? crypto.randomUUID();
    setRequestKey(key);
    setBusy(true);
    setMessage("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title, folder, content, request_key: key,
          ...(destination === "new_vault" ? { new_vault_name: newVaultName } : {}),
          ...(destination === "existing_vault" ? { vault_id: existingVaultId } : {}),
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not prepare note preview.");
      setPlan(payload as ActionPlan);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not prepare note preview.");
    } finally {
      setBusy(false);
    }
  }

  async function approve() {
    if (!plan) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ arguments_hash: plan.argumentsHash }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Note could not be saved.");
      setPlan(payload as ActionPlan);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Note could not be saved.");
      const status = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}`).catch(() => null);
      if (status?.ok) {
        try { setPlan(await status.json() as ActionPlan); } catch { /* Keep the visible error. */ }
      }
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    if (plan?.status === "proposed") {
      await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}/cancel`, { method: "POST" }).catch(() => undefined);
    }
    setPlan(null);
    setRequestKey(null);
    setOpen(false);
    onClose?.();
  }

  async function releaseDraft() {
    if (!plan || !reviewed || !savedDraft) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}/review-draft`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewed: true, content_hash: savedDraft.content_hash }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not release the draft.");
      setPlan(payload as ActionPlan);
      onReleased?.();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not release the draft.");
    } finally {
      setBusy(false);
    }
  }

  async function recoverSavedFile() {
    if (!plan || plan.status !== "failed" || (!plan.recoveryPath && !plan.orphanPath)) return;
    const changed = !plan.recoveryPath;
    if (changed && (!orphanDraft || !orphanReviewed)) return;
    setBusy(true);
    setMessage("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${plan.id}/reconcile`, changed ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reviewed: true, content_hash: orphanDraft!.content_hash }),
      } : { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not recover the saved file.");
      setPlan(payload as ActionPlan);
      setOrphanDraft(null);
      setOrphanReviewed(false);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not recover the saved file.");
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return <button className="bb-action px-3 py-1.5 text-xs" onClick={() => setOpen(true)}>Save answer as note</button>;
  }

  return (
    <section className="mt-4 rounded-xl border border-border bg-panel p-4" aria-label="Review Ask note">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">Review note before saving</h3>
        <button className="text-xs text-muted hover:text-foreground" onClick={() => void cancel()}>Close</button>
      </div>
      <p className="mb-3 text-xs text-muted">This is an Ask-assisted draft. No note or new vault is created until you approve this exact preview. Check facts and references first.</p>
      {plan ? (
        <>
          <dl className="mb-3 grid gap-2 text-xs sm:grid-cols-2">
            <div><dt className="text-muted">Filename</dt><dd>{plan.arguments.title}</dd></div>
            <div><dt className="text-muted">Folder</dt><dd>{plan.arguments.folder}</dd></div>
            {plan.arguments.newVaultName && <div><dt className="text-muted">New vault</dt><dd>{plan.arguments.newVaultName} · shared workspace</dd></div>}
            {plan.arguments.targetVaultId && <div><dt className="text-muted">Existing vault</dt><dd>{plan.arguments.targetVaultName || plan.arguments.targetVaultId} · shared workspace</dd></div>}
          </dl>
          <p className="mb-1 text-[11px] text-muted">Original approved preview</p>
          <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-surface p-3 text-xs">{plan.arguments.content}</pre>
          {["completed", "partial"].includes(plan.status) && plan.resultPath ? (
            <div className="mt-3 space-y-3">
              {plan.status === "partial" && <p className="text-xs text-danger" role="status">The saved note changed during processing. Your edit was preserved; review the current content before releasing it to the graph and Ask.</p>}
              <a className="inline-block text-xs text-accent underline" href={appPath(`/brain?note=${encodeURIComponent(plan.resultPath)}`)}>Open saved note</a>
              {plan.evidenceStatus === "draft" ? (
                <div className="rounded-lg border border-border bg-surface p-3 text-xs">
                  <p className="text-muted">Saved as an unreviewed draft. Ask will not cite it or process it into the graph until you review and release it.</p>
                  <button className="bb-action mt-2 px-2 py-1 text-xs" disabled={busy} onClick={() => void refreshDraft()}>Refresh draft</button>
                  {savedDraft ? <><p className="mt-2 text-[11px] text-muted">Current saved content — review this exact version</p><pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-panel p-3 text-xs">{savedDraft.content}</pre></> : <p className="mt-2 text-muted">Loading saved draft...</p>}
                  <label className="mt-2 flex items-start gap-2"><input type="checkbox" disabled={!savedDraft} checked={reviewed} onChange={(event) => setReviewed(event.target.checked)} />I reviewed the claims and source links in this note.</label>
                  <button className="bb-action bb-action--primary mt-2 px-3 py-1.5 text-xs" disabled={busy || !reviewed || !savedDraft} onClick={() => void releaseDraft()}>{busy ? "Releasing..." : "Release to graph and Ask"}</button>
                </div>
              ) : plan.evidenceStatus === "eligible" ? (
                <p className="text-xs text-muted" role="status">Reviewed note released for processing and Ask evidence.</p>
              ) : null}
            </div>
          ) : plan.status === "completed" ? (
            <p className="mt-3 text-xs text-muted" role="status">The saved note is no longer available under its approved identity. No other note will be released by this plan.</p>
          ) : plan.status === "executing" ? (
            <p className="mt-3 text-xs text-muted" role="status">Saving the approved draft{plan.attempts ? ` (attempt ${plan.attempts} of 2)` : ""}. An interrupted save resumes at most once; status updates automatically.</p>
          ) : plan.status === "failed" ? (
            <div className="mt-3 space-y-2 text-xs" role="status">
              <p className="text-danger">The save could not be completed. Automatic retries stopped; a Markdown file may already exist. Check the selected folder before creating another note.</p>
              {plan.recoveryPath && <>
                <a className="block text-accent underline" href={appPath(`/brain?note=${encodeURIComponent(plan.recoveryPath)}`)}>Inspect matching saved file</a>
                <button className="bb-action px-3 py-1.5" disabled={busy} onClick={() => void recoverSavedFile()}>{busy ? "Recovering..." : "Recover saved file as draft"}</button>
              </>}
              {!plan.recoveryPath && plan.orphanPath && <div className="rounded-lg border border-border bg-surface p-3">
                <p className="text-muted">The file differs from the approved preview. Review its current content before attaching it as an uncitable draft; nothing will be overwritten.</p>
                <a className="mt-2 block text-accent underline" href={appPath(`/brain?note=${encodeURIComponent(plan.orphanPath)}`)}>Open changed saved file</a>
                {orphanDraft ? <><p className="mt-2 text-[11px] text-muted">Current saved content</p><pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-panel p-3 text-xs">{orphanDraft.content}</pre></> : <p className="mt-2 text-muted">Loading current file...</p>}
                <label className="mt-2 flex items-start gap-2"><input type="checkbox" checked={orphanReviewed} disabled={!orphanDraft} onChange={(event) => setOrphanReviewed(event.target.checked)} />I reviewed this exact saved file before recovery.</label>
                <button className="bb-action mt-2 px-3 py-1.5" disabled={busy || !orphanDraft || !orphanReviewed} onClick={() => void recoverSavedFile()}>{busy ? "Recovering..." : "Attach changed file as draft"}</button>
              </div>}
              <button className="bb-action px-3 py-1.5" onClick={() => void cancel()}>Close failed plan</button>
            </div>
          ) : (
            <div className="mt-3 flex flex-wrap gap-2">
              <button className="bb-action bb-action--primary px-3 py-1.5 text-xs" disabled={busy || plan.status !== "proposed"} onClick={() => void approve()}>{busy ? "Saving..." : plan.arguments.newVaultName ? "Approve vault and note" : "Approve and save note"}</button>
              <button className="bb-action px-3 py-1.5 text-xs" disabled={busy} onClick={() => void cancel()}>Reject plan</button>
            </div>
          )}
        </>
      ) : resumePlanId ? (
        <p className="text-xs text-muted" role={message ? "alert" : "status"}>{message || "Loading saved draft..."}</p>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-[1fr_10rem]">
            <label className="text-xs">Note filename<input className="mt-1 w-full rounded-lg border border-border bg-surface p-2 text-sm" maxLength={160} value={title} onChange={(event) => { setTitle(event.target.value); setRequestKey(null); }} /></label>
            <label className="text-xs">Folder<select className="mt-1 w-full rounded-lg border border-border bg-surface p-2 text-sm" value={folder} onChange={(event) => { setFolder(event.target.value); setRequestKey(null); }}>{folders.map((item) => <option key={item} value={item}>{item}</option>)}</select></label>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-[10rem_1fr]">
            <label className="text-xs">Destination<select className="mt-1 w-full rounded-lg border border-border bg-surface p-2 text-sm" value={destination} onChange={(event) => { setDestination(event.target.value as "default" | "existing_vault" | "new_vault"); setRequestKey(null); }}><option value="default">Default vault</option>{vaults.length > 0 && <option value="existing_vault">Existing named vault</option>}<option value="new_vault">New named vault</option></select></label>
            {destination === "existing_vault" && <label className="text-xs">Named vault<select className="mt-1 w-full rounded-lg border border-border bg-surface p-2 text-sm" value={existingVaultId} onChange={(event) => { setExistingVaultId(event.target.value); setRequestKey(null); }}>{vaults.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>}
            {destination === "new_vault" && <label className="text-xs">New vault name<input className="mt-1 w-full rounded-lg border border-border bg-surface p-2 text-sm" maxLength={160} value={newVaultName} onChange={(event) => { setNewVaultName(event.target.value); setRequestKey(null); }} /></label>}
          </div>
          {destination === "new_vault" && <p className="mt-2 text-[11px] text-muted">A new Markdown directory and stable vault identity will be created inside this shared installation. This does not isolate access between users.</p>}
          <label className="mt-3 block text-xs">Markdown draft<textarea className="mt-1 min-h-48 w-full rounded-lg border border-border bg-surface p-3 font-mono text-xs" value={content} onChange={(event) => { setContent(event.target.value); setRequestKey(null); }} /></label>
          <p className="mt-1 text-[11px] text-muted">The first Markdown heading controls the title shown inside BerryBrain.</p>
          <button className="bb-action bb-action--primary mt-3 px-3 py-1.5 text-xs" disabled={busy || !title.trim() || !content.trim() || (destination === "new_vault" && !newVaultName.trim()) || (destination === "existing_vault" && !existingVaultId)} onClick={() => void propose()}>{busy ? "Preparing..." : "Review exact preview"}</button>
        </>
      )}
      {message && plan && <p className="mt-3 text-xs text-danger" role="alert">{message}</p>}
    </section>
  );
}
