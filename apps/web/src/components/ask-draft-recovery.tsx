"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/contexts/workspace-context";
import { AskNotePlan } from "./ask-note-plan";

type ReviewableDraft = {
  id: string;
  title: string;
  resultPath: string;
  createdAt: string;
};

const pageSize = 20;

export function AskDraftRecovery({ apiUrl }: { apiUrl: string }) {
  const [drafts, setDrafts] = useState<ReviewableDraft[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadedCount, setLoadedCount] = useState(0);

  const refresh = useCallback(async () => {
    if (apiUrl === "__demo__") return;
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/reviewable?limit=${pageSize}&offset=0`);
      if (!response.ok) throw new Error("Could not list saved drafts.");
      const current = await response.json() as ReviewableDraft[];
      setDrafts(current);
      setLoadedCount(current.length);
      setHasMore(current.length === pageSize);
      setError("");
    } catch {
      setError("Could not list saved drafts. Try again after checking your session.");
    }
  }, [apiUrl]);

  useEffect(() => { void refresh(); }, [refresh]);

  async function loadMore() {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/reviewable?limit=${pageSize}&offset=${loadedCount}`);
      if (!response.ok) throw new Error("Could not load more saved drafts.");
      const next = await response.json() as ReviewableDraft[];
      setDrafts((current) => [...current, ...next.filter((draft) => !current.some((item) => item.id === draft.id))]);
      setLoadedCount((current) => current + next.length);
      setHasMore(next.length === pageSize);
      setError("");
    } catch {
      setError("Could not load more saved drafts. Try again.");
    } finally {
      setLoadingMore(false);
    }
  }

  if (!drafts.length && !error) return null;

  return (
    <section className="mx-auto w-full max-w-4xl rounded-xl border border-border bg-panel p-4 text-left" aria-label="Ask drafts awaiting review">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Saved drafts awaiting review</h2>
        <button type="button" className="bb-action px-2 py-1 text-xs" onClick={() => void refresh()}>Refresh</button>
      </div>
      <p className="mt-1 text-xs text-muted">These notes stay out of graph and Ask evidence until you review their current contents.</p>
      {error && <p role="alert" className="mt-2 text-xs text-danger">{error}</p>}
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {drafts.map((draft) => (
          <button key={draft.id} type="button" className="rounded-lg border border-border bg-surface p-3 text-left text-xs hover:border-accent" onClick={() => setSelectedId(draft.id)} aria-pressed={selectedId === draft.id}>
            <span className="block font-medium text-foreground">{draft.title}</span>
            <span className="mt-1 block break-all text-muted">{draft.resultPath}</span>
          </button>
        ))}
      </div>
      {hasMore && <button type="button" className="bb-action mt-3 px-3 py-1.5 text-xs" disabled={loadingMore} onClick={() => void loadMore()}>{loadingMore ? "Loading..." : "Load more drafts"}</button>}
      {selectedId && <AskNotePlan key={selectedId} answer="" question="" apiUrl={apiUrl} resumePlanId={selectedId} onClose={() => setSelectedId(null)} onReleased={() => { setSelectedId(null); void refresh(); }} />}
    </section>
  );
}
