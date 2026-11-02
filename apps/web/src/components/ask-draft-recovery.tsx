"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, useWorkspace } from "@/contexts/workspace-context";
import { AskNotePlan } from "./ask-note-plan";

type ReviewableDraft = {
  id: string;
  title: string;
  resultPath: string;
  createdAt: string;
};

const pageSize = 20;

export function AskDraftRecovery({ apiUrl }: { apiUrl: string }) {
  const workspace = useWorkspace();
  const [drafts, setDrafts] = useState<ReviewableDraft[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [loadedCount, setLoadedCount] = useState(0);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteAll, setConfirmDeleteAll] = useState(false);
  const [deletingAll, setDeletingAll] = useState(false);

  const syncWorkspaceAfterDelete = useCallback((deletedPaths: string[]) => {
    if (!workspace) return;
    if (workspace.active && deletedPaths.includes(workspace.active.path)) {
      workspace.closeNote();
    }
    void workspace.loadAll();
  }, [workspace]);

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

  async function deleteDraft(draft: ReviewableDraft) {
    if (deletingId || deletingAll) return;
    setDeletingId(draft.id);
    setError("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${draft.id}/draft`, {
        method: "DELETE",
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => ({})) as { detail?: unknown };
        const detail = typeof payload.detail === "string" && payload.detail.trim()
          ? payload.detail
          : "Could not delete saved draft.";
        if (response.status === 404 || response.status === 409) {
          await refresh();
        }
        throw new Error(detail);
      }
      if (selectedId === draft.id) setSelectedId(null);
      setConfirmDeleteId(null);
      syncWorkspaceAfterDelete([draft.resultPath]);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete saved draft.");
    } finally {
      setDeletingId(null);
    }
  }

  async function deleteAllDrafts() {
    if (deletingId || deletingAll) return;
    setDeletingAll(true);
    setError("");
    const deletedPaths: string[] = [];
    try {
      let remaining = [...drafts];
      for (let round = 0; round < 10 && remaining.length > 0; round += 1) {
        for (const draft of remaining) {
          const response = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/${draft.id}/draft`, {
            method: "DELETE",
          });
          if (!response.ok && response.status !== 404 && response.status !== 409) {
            const payload = await response.json().catch(() => ({})) as { detail?: unknown };
            throw new Error(typeof payload.detail === "string" ? payload.detail : "Could not delete all saved drafts.");
          }
          deletedPaths.push(draft.resultPath);
        }
        const nextResponse = await apiFetch(`${apiUrl}/api/v1/ask/action-plans/reviewable?limit=${pageSize}&offset=0`);
        if (!nextResponse.ok) break;
        const nextBatch = await nextResponse.json() as ReviewableDraft[];
        if (nextBatch.every((candidate) => remaining.some((prev) => prev.id === candidate.id))) {
          break;
        }
        remaining = nextBatch;
      }
      setSelectedId(null);
      setConfirmDeleteId(null);
      setConfirmDeleteAll(false);
      if (deletedPaths.length > 0) syncWorkspaceAfterDelete(deletedPaths);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete all saved drafts.");
      await refresh();
    } finally {
      setDeletingAll(false);
    }
  }

  if (!drafts.length && !error) return null;

  return (
    <section className="mx-auto w-full max-w-4xl rounded-xl border border-border bg-panel p-4 text-left" aria-label="Ask drafts awaiting review">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-sm font-semibold">Saved drafts awaiting review</h2>
        <div className="flex flex-wrap items-center gap-1.5">
          {drafts.length > 1 && (
            confirmDeleteAll ? (
              <>
                <button
                  type="button"
                  className="bb-action border-danger/50 px-2 py-1 text-xs font-medium text-danger"
                  disabled={deletingAll || deletingId !== null}
                  onClick={() => void deleteAllDrafts()}
                >
                  {deletingAll ? "Deleting..." : "Confirm delete all"}
                </button>
                <button
                  type="button"
                  className="bb-action px-2 py-1 text-xs"
                  disabled={deletingAll || deletingId !== null}
                  onClick={() => setConfirmDeleteAll(false)}
                >
                  Cancel
                </button>
              </>
            ) : (
              <button
                type="button"
                className="bb-action px-2 py-1 text-xs text-muted hover:border-danger/40 hover:text-danger"
                disabled={deletingAll || deletingId !== null}
                onClick={() => {
                  setConfirmDeleteId(null);
                  setConfirmDeleteAll(true);
                }}
              >
                Delete all
              </button>
            )
          )}
          <button
            type="button"
            className="bb-action px-2 py-1 text-xs"
            disabled={deletingAll || deletingId !== null}
            onClick={() => void refresh()}
          >
            Refresh
          </button>
        </div>
      </div>
      <p className="mt-1 text-xs text-muted">These notes stay out of graph and Ask evidence until you review their current contents.</p>
      {error && <p role="alert" className="mt-2 text-xs text-danger">{error}</p>}
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {drafts.map((draft) => (
          <div
            key={draft.id}
            className={`flex items-start justify-between gap-2 rounded-lg border bg-surface p-3 text-xs transition-colors ${
              selectedId === draft.id ? "border-accent" : "border-border hover:border-accent"
            }`}
          >
            <button
              type="button"
              className="min-w-0 flex-1 text-left"
              onClick={() => setSelectedId(draft.id)}
              aria-pressed={selectedId === draft.id}
            >
              <span className="block font-medium text-foreground">{draft.title}</span>
              <span className="mt-1 block break-all text-muted">{draft.resultPath}</span>
            </button>
            <div className="flex shrink-0 items-center gap-1">
              {confirmDeleteId === draft.id ? (
                <>
                  <button
                    type="button"
                    className="bb-action border-danger/50 px-2 py-1 text-[11px] font-medium text-danger"
                    disabled={deletingId !== null || deletingAll}
                    onClick={() => void deleteDraft(draft)}
                  >
                    {deletingId === draft.id ? "Deleting..." : "Confirm"}
                  </button>
                  <button
                    type="button"
                    className="bb-action px-2 py-1 text-[11px]"
                    disabled={deletingId !== null || deletingAll}
                    onClick={() => setConfirmDeleteId(null)}
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  className="bb-action px-2 py-1 text-[11px] text-muted hover:border-danger/40 hover:text-danger"
                  disabled={deletingId !== null || deletingAll}
                  onClick={() => {
                    setConfirmDeleteAll(false);
                    setConfirmDeleteId(draft.id);
                  }}
                >
                  Delete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
      {hasMore && <button type="button" className="bb-action mt-3 px-3 py-1.5 text-xs" disabled={loadingMore || deletingAll} onClick={() => void loadMore()}>{loadingMore ? "Loading..." : "Load more drafts"}</button>}
      {selectedId && (
        <AskNotePlan
          key={selectedId}
          answer=""
          question=""
          apiUrl={apiUrl}
          resumePlanId={selectedId}
          onClose={() => setSelectedId(null)}
          onReleased={() => { setSelectedId(null); void refresh(); }}
          onDeleted={(deletedPath) => {
            setSelectedId(null);
            if (deletedPath) syncWorkspaceAfterDelete([deletedPath]);
            void refresh();
          }}
        />
      )}
    </section>
  );
}
