"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "@/contexts/workspace-context";
import { AskNotePlan } from "./ask-note-plan";

type FailedPlan = {
  id: string;
  title: string;
  orphanPath: string | null;
  errorCode: string | null;
  createdAt: string;
};

const pageSize = 20;

export function AskFailedRecovery({ apiUrl }: { apiUrl: string }) {
  const [plans, setPlans] = useState<FailedPlan[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadedCount, setLoadedCount] = useState(0);

  const refresh = useCallback(async () => {
    if (apiUrl === "__demo__") return;
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/failed?limit=${pageSize}&offset=0`);
      if (!response.ok) throw new Error("Could not list failed saves.");
      const current = await response.json() as FailedPlan[];
      setPlans(current);
      setLoadedCount(current.length);
      setHasMore(current.length === pageSize);
      setError("");
    } catch {
      setError("Could not list failed saves. Try again after checking your session.");
    }
  }, [apiUrl]);

  useEffect(() => { void refresh(); }, [refresh]);

  async function loadMore() {
    if (loadingMore || !hasMore) return;
    setLoadingMore(true);
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/failed?limit=${pageSize}&offset=${loadedCount}`);
      if (!response.ok) throw new Error("Could not load more failed saves.");
      const next = await response.json() as FailedPlan[];
      setPlans((current) => [...current, ...next.filter((plan) => !current.some((item) => item.id === plan.id))]);
      setLoadedCount((current) => current + next.length);
      setHasMore(next.length === pageSize);
      setError("");
    } catch {
      setError("Could not load more failed saves. Try again.");
    } finally {
      setLoadingMore(false);
    }
  }

  if (!plans.length && !error) return null;

  return (
    <section className="mx-auto w-full max-w-4xl rounded-xl border border-border bg-panel p-4 text-left" aria-label="Ask failed saves">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Failed saves to inspect</h2>
        <button type="button" className="bb-action px-2 py-1 text-xs" onClick={() => void refresh()}>Refresh</button>
      </div>
      <p className="mt-1 text-xs text-muted">A file may exist even when a save failed. Inspect it before retrying; recovery never overwrites it or releases it as evidence.</p>
      {error && <p role="alert" className="mt-2 text-xs text-danger">{error}</p>}
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {plans.map((plan) => (
          <button key={plan.id} type="button" className="rounded-lg border border-border bg-surface p-3 text-left text-xs hover:border-accent" onClick={() => setSelectedId(plan.id)} aria-pressed={selectedId === plan.id}>
            <span className="block font-medium text-foreground">{plan.title}</span>
            <span className="mt-1 block break-all text-muted">{plan.orphanPath || "No saved file found"}</span>
          </button>
        ))}
      </div>
      {hasMore && <button type="button" className="bb-action mt-3 px-3 py-1.5 text-xs" disabled={loadingMore} onClick={() => void loadMore()}>{loadingMore ? "Loading..." : "Load more failed saves"}</button>}
      {selectedId && <AskNotePlan key={selectedId} answer="" question="" apiUrl={apiUrl} resumePlanId={selectedId} onClose={() => { setSelectedId(null); void refresh(); }} onReleased={() => { setSelectedId(null); void refresh(); }} />}
    </section>
  );
}
