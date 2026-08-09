"use client";

import { useEffect, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";

type MeResponse = {
  user?: { email?: string; displayName?: string };
};

type TourStep = {
  title: string;
  eyebrow: string;
  body: string;
  bullets: string[];
};

const STEPS: TourStep[] = [
  {
    eyebrow: "Start",
    title: "Capture first, organize later.",
    body: "BerryBrain starts from plain Markdown notes. Write quickly, link ideas with [[note links]], and let the system build structure around your material.",
    bullets: ["Use New note or Ctrl+K to create notes.", "Drafts are saved in the vault as real files.", "Your note language and wording stay untouched."],
  },
  {
    eyebrow: "Autopilot",
    title: "Watch the pipeline instead of guessing.",
    body: "After notes change, jobs parse, classify, extract concepts, build embeddings, find connections, and expand the graph.",
    bullets: ["Open Monitor to inspect queued and failed jobs.", "Use Activity for a readable history.", "Use Scan vault after importing files externally."],
  },
  {
    eyebrow: "Graph",
    title: "Use the graph as the working map.",
    body: "The graph is where notes, concepts, entities, topics, gaps, and insights become inspectable.",
    bullets: ["Ask the graph a question from the top bar.", "Click a node to review evidence and actions.", "Confirm good nodes and ignore weak suggestions."],
  },
  {
    eyebrow: "Insights",
    title: "Turn evidence into next actions.",
    body: "Insights surface gaps, patterns, hypotheses, and possible contradictions grounded in graph evidence.",
    bullets: ["Review confidence before applying.", "Create notes or reviews from useful insights.", "Ignore low-value suggestions to keep the graph clean."],
  },
  {
    eyebrow: "Account",
    title: "Keep identity and sessions under control.",
    body: "Account settings let the local owner update profile data, change password, and revoke sessions.",
    bullets: ["Use the account button in the sidebar.", "Logout and sensitive updates require CSRF-protected requests.", "Danger operations stay behind authenticated owner controls."],
  },
];

export function OnboardingModal({
  demo = false,
  open,
  onOpenChange,
}: {
  demo?: boolean;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (typeof window === "undefined") return;
    let active = true;

    const openTour = () => {
      setStep(0);
      onOpenChange(true);
    };
    window.addEventListener("bb:open-tour", openTour);

    if (demo) {
      if (localStorage.getItem("bb_tour_seen") !== "1") {
        localStorage.setItem("bb_tour_seen", "1");
        openTour();
      }
    } else {
      fetch(`${getApiUrl()}/api/v1/auth/me`, { credentials: "include" })
        .then((response) => (response.ok ? response.json() : null))
        .then(async (me: MeResponse | null) => {
          if (!active || !me?.user) return;
          const response = await fetch(`${getApiUrl()}/api/v1/settings`, {
            credentials: "include",
          });
          if (!active || !response.ok) return;
          const payload = await response.json();
          const completed = payload?.settings?.some(
            (setting: { key?: string; value?: string }) => (
              setting.key === "onboarding_completed"
              && setting.value === "true"
            ),
          );
          if (!completed) openTour();
        })
        .catch(() => {});
    }

    return () => {
      active = false;
      window.removeEventListener("bb:open-tour", openTour);
    };
  }, [demo, onOpenChange]);

  function continueToAiSetup() {
    onOpenChange(false);
    window.dispatchEvent(new Event("bb:open-ai-setup"));
  }

  if (!open) return null;
  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/55 p-4 backdrop-blur-sm">
      <section
        className="flex max-h-[88dvh] w-full max-w-2xl flex-col overflow-hidden rounded-md border border-border bg-panel shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="onboarding-title"
      >
        <header className="border-b border-border px-6 py-5">
          <div className="flex items-start justify-between gap-5">
            <div>
              <p className="text-xs font-semibold uppercase text-accent">{current.eyebrow}</p>
              <h2 id="onboarding-title" className="mt-1 text-xl font-semibold">{current.title}</h2>
            </div>
            <button type="button" className="bb-action px-3 py-1.5 text-sm" onClick={continueToAiSetup}>
              Skip
            </button>
          </div>
          <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-surface">
            <div
              className="h-full bg-accent transition-[width]"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>
        </header>

        <div className="overflow-y-auto px-6 py-6">
          <p className="max-w-xl text-sm leading-6 text-muted">{current.body}</p>
          <ul className="mt-5 space-y-3">
            {current.bullets.map((item) => (
              <li key={item} className="flex gap-3 text-sm">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        <footer className="flex items-center justify-between border-t border-border px-6 py-4">
          <span className="text-xs text-muted">Step {step + 1} of {STEPS.length}</span>
          <div className="flex gap-2">
            <button
              type="button"
              disabled={step === 0}
              className="bb-action px-4 py-2 text-sm"
              onClick={() => setStep((currentStep) => Math.max(0, currentStep - 1))}
            >
              Back
            </button>
            <button
              type="button"
              className="bb-action px-4 py-2 text-sm font-medium"
              onClick={() => (
                isLast
                  ? continueToAiSetup()
                  : setStep((currentStep) => currentStep + 1)
              )}
            >
              {isLast ? "Set up AI" : "Continue"}
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}
