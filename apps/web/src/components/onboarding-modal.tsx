"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch, getApiUrl } from "@/contexts/workspace-context";

type MeResponse = {
  user?: { email?: string; displayName?: string };
};

type BootstrapResponse = {
  configurationGate?: { required?: boolean; valid?: boolean };
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
    bullets: ["Inspect confidence before applying.", "Create notes from useful insights.", "Ignore low-value suggestions to keep the graph clean."],
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
  const [onboardingCompleted, setOnboardingCompleted] = useState<boolean | null>(null);
  const [configurationRequired, setConfigurationRequired] = useState(true);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [statusError, setStatusError] = useState("");

  const loadStatus = useCallback(async (openWhenIncomplete: boolean) => {
    if (demo) return;
    setCheckingStatus(true);
    setStatusError("");
    try {
      const meResponse = await apiFetch(`${getApiUrl()}/api/v1/auth/me`);
      if (!meResponse.ok) return;
      const me = await meResponse.json() as MeResponse;
      if (!me.user) return;

      const settingsResponse = await apiFetch(`${getApiUrl()}/api/v1/settings`);
      if (!settingsResponse.ok) throw new Error("Onboarding status could not be loaded.");
      const settingsPayload = await settingsResponse.json();
      const completed = Boolean(settingsPayload?.settings?.some(
        (setting: { key?: string; value?: string }) => (
          setting.key === "onboarding_completed" && setting.value === "true"
        ),
      ));
      setOnboardingCompleted(completed);
      if (completed) return;

      const bootstrapResponse = await apiFetch(`${getApiUrl()}/api/v1/bootstrap`);
      if (!bootstrapResponse.ok) throw new Error("AI configuration status could not be loaded.");
      const bootstrapPayload = await bootstrapResponse.json() as BootstrapResponse;
      const gate = bootstrapPayload.configurationGate;
      setConfigurationRequired(Boolean(gate?.required || !gate?.valid));
      if (!completed && openWhenIncomplete) {
        setStep(0);
        onOpenChange(true);
      }
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : "Onboarding status could not be loaded.");
      setConfigurationRequired(true);
      if (openWhenIncomplete) {
        setStep(0);
        onOpenChange(true);
      }
    } finally {
      setCheckingStatus(false);
    }
  }, [demo, onOpenChange]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const openTour = () => {
      setStep(0);
      onOpenChange(true);
      void loadStatus(false);
    };
    window.addEventListener("bb:open-tour", openTour);

    if (demo) {
      if (localStorage.getItem("bb_tour_seen") !== "1") {
        localStorage.setItem("bb_tour_seen", "1");
        openTour();
      }
    } else {
      void loadStatus(true);
    }

    return () => {
      window.removeEventListener("bb:open-tour", openTour);
    };
  }, [demo, loadStatus, onOpenChange]);

  async function finishTour() {
    if (checkingStatus) return;
    if (statusError) {
      await loadStatus(false);
      return;
    }
    if (demo || onboardingCompleted) {
      onOpenChange(false);
      return;
    }
    if (configurationRequired) {
      onOpenChange(false);
      window.dispatchEvent(new Event("bb:open-ai-setup"));
      return;
    }

    setCheckingStatus(true);
    try {
      const response = await apiFetch(`${getApiUrl()}/api/v1/settings/onboarding_completed`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: "true" }),
      });
      if (!response.ok) throw new Error("Tour completion could not be saved.");
      setOnboardingCompleted(true);
      onOpenChange(false);
    } catch (error) {
      setStatusError(error instanceof Error ? error.message : "Tour completion could not be saved.");
    } finally {
      setCheckingStatus(false);
    }
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
            <button type="button" className="bb-action px-3 py-1.5 text-sm" onClick={() => void finishTour()} disabled={checkingStatus}>
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
          {statusError && (
            <div className="mb-5 rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
              <p>{statusError}</p>
              <button type="button" className="bb-action mt-3 px-3 py-1.5 text-xs" onClick={() => void loadStatus(false)} disabled={checkingStatus}>
                {checkingStatus ? "Checking..." : "Retry status check"}
              </button>
            </div>
          )}
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
              disabled={step === 0 || checkingStatus}
              className="bb-action px-4 py-2 text-sm"
              onClick={() => setStep((currentStep) => Math.max(0, currentStep - 1))}
            >
              Back
            </button>
            <button
              type="button"
              className="bb-action px-4 py-2 text-sm font-medium"
              disabled={checkingStatus}
              onClick={() => (
                isLast
                  ? void finishTour()
                  : setStep((currentStep) => currentStep + 1)
              )}
            >
              {checkingStatus
                ? "Checking..."
                : isLast
                  ? onboardingCompleted || demo
                    ? "Finish"
                    : configurationRequired
                      ? "Set up AI"
                      : "Finish"
                  : "Continue"}
            </button>
          </div>
        </footer>
      </section>
    </div>
  );
}
