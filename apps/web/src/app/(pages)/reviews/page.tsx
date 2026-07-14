"use client";

import { useCallback, useEffect, useState } from "react";

import { useWorkspace } from "@/contexts/workspace-context";


type ReviewItem = {
  id: number;
  reviewType: string;
  prompt: string;
  expectedPoints: string[];
  evidence: unknown[];
  perceivedDifficulty: number;
  lastPerformance: string;
  intervalDays: number;
};

type Rating = "forgot" | "hard" | "good" | "easy";


export default function ReviewsPage() {
  const w = useWorkspace();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [submitting, setSubmitting] = useState<Rating | "">("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${w.api}/api/v1/reviews?due=true&limit=50`);
      if (!response.ok) throw new Error("Could not load today's review session.");
      const payload = await response.json();
      setItems(payload.reviews || []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not load today's review session.");
    } finally {
      setLoading(false);
    }
  }, [w.api]);

  useEffect(() => {
    load();
  }, [load]);

  async function grade(rating: Rating) {
    const current = items[0];
    if (!current || submitting) return;
    setSubmitting(rating);
    try {
      const response = await fetch(`${w.api}/api/v1/reviews/${current.id}/grade`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating }),
      });
      if (!response.ok) throw new Error("The review result could not be saved.");
      setItems((existing) => existing.slice(1));
      setRevealed(false);
      w.toast("Review scheduled.", "success");
    } catch (reason) {
      w.toast(reason instanceof Error ? reason.message : "The review result could not be saved.", "error");
    } finally {
      setSubmitting("");
    }
  }

  if (loading) {
    return <div className="grid min-h-full place-items-center text-sm text-muted/55">Loading review session...</div>;
  }

  if (error) {
    return (
      <div className="grid min-h-full place-items-center px-6">
        <div className="text-center">
          <p className="text-sm text-danger">{error}</p>
          <button className="bb-action mt-3 px-4 py-2 text-xs font-medium" onClick={load}>Try again</button>
        </div>
      </div>
    );
  }

  const current = items[0];
  if (!current) {
    return (
      <div className="grid min-h-full place-items-center px-6">
        <div className="max-w-md text-center">
          <p className="text-xl font-semibold">Review complete</p>
          <p className="mt-2 text-sm text-muted/60">Nothing else is due today. New items appear only when an insight has enough evidence and retention value.</p>
        </div>
      </div>
    );
  }

  return (
    <main className="min-h-full overflow-y-auto px-5 py-8 lg:px-10">
      <div className="mx-auto max-w-3xl">
        <header className="flex items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-accent">Cognitive review</p>
            <h1 className="mt-1 text-2xl font-semibold">Review today</h1>
          </div>
          <p className="text-xs tabular-nums text-muted/55">{items.length} remaining</p>
        </header>

        <section className="mt-8 rounded-2xl bg-surface p-6 ring-1 ring-border/45 lg:p-8">
          <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-muted/45">{current.reviewType.replaceAll("_", " ")}</p>
          <p className="mt-4 text-lg leading-relaxed text-foreground">{current.prompt}</p>

          {!revealed ? (
            <button className="bb-action mt-8 px-4 py-2.5 text-sm font-medium" onClick={() => setRevealed(true)}>Reveal expected points</button>
          ) : (
            <div className="mt-8 border-t border-border/50 pt-6">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted/50">Expected points</p>
              <ul className="mt-3 space-y-2">
                {current.expectedPoints.map((point, index) => (
                  <li key={`${point}-${index}`} className="flex gap-3 text-sm text-muted/80"><span className="mt-2 size-1.5 shrink-0 rounded-full bg-accent" />{point}</li>
                ))}
              </ul>
              <div className="mt-7 grid grid-cols-2 gap-2 sm:grid-cols-4">
                {(["forgot", "hard", "good", "easy"] as Rating[]).map((rating) => (
                  <button
                    key={rating}
                    disabled={Boolean(submitting)}
                    className="bb-action px-3 py-2.5 text-xs font-medium capitalize"
                    onClick={() => grade(rating)}
                  >
                    {submitting === rating ? "Saving..." : rating}
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
