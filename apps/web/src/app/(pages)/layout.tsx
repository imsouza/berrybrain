"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { usePathname } from "next/navigation";
import { WorkspaceProvider, useWorkspace, appPath } from "@/contexts/workspace-context";
import { WorkspaceSidebar } from "@/components/sidebar/workspace-sidebar";
import { ResizeHandle } from "@/components/sidebar/resize-handle";
import { RequiredAiSetup } from "@/components/required-ai-setup";

const CommandPalette = dynamic(() => import("@/components/command-palette").then((module) => module.CommandPalette));
const ObservabilityPanel = dynamic(() => import("@/components/observability-panel").then((module) => module.ObservabilityPanel));
const NotificationsPopover = dynamic(() => import("@/components/notifications-popover").then((module) => module.NotificationsPopover));
const SettingsPanel = dynamic(() => import("@/components/settings-panel").then((module) => module.SettingsPanel));
const OnboardingModal = dynamic(() => import("@/components/onboarding-modal").then((module) => module.OnboardingModal));
const GuidePanel = dynamic(() => import("@/components/guide-panel").then((module) => module.GuidePanel));
const GraphScreen = dynamic(
  () => import("@/components/graph-screen").then((module) => module.GraphScreen),
  {
    ssr: false,
    loading: () => <div className="flex min-h-0 flex-1 items-center justify-center text-sm text-muted">Loading graph...</div>,
  },
);

function Shell({ children }: { children: React.ReactNode }) {
  const w = useWorkspace();
  const pathname = usePathname();
  const prevActive = useRef(w.active);
  const [authState, setAuthState] = useState<"checking" | "allowed">("checking");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  // ponytail: basePath-aware return-to-login link (strip basePath so safeNext can re-apply it)
  const loginHref = () =>
    `${appPath("/login")}?next=${encodeURIComponent(window.location.pathname.replace(new RegExp("^" + (process.env.NEXT_PUBLIC_BERRYBRAIN_API_URL || "")), "") || "/")}`;

  useEffect(() => {
    let alive = true;
    fetch(`${w.api}/api/v1/auth/me`, { credentials: "include" })
      .then((response) => {
        if (!alive) return;
        if (response.ok) setAuthState("allowed");
        else window.location.href = loginHref();
      })
      .catch(() => {
        if (alive) window.location.href = loginHref();
      });
    return () => {
      alive = false;
    };
  }, [w.api]);

  useEffect(() => {
    if (authState !== "allowed") return;
    if (w.active && w.active !== prevActive.current) {
      window.location.href = appPath(`/brain?note=${encodeURIComponent(w.active.path)}`);
    }
    prevActive.current = w.active;
  }, [authState, w.active]);

  if (authState !== "allowed") {
    return (
      <main className="flex h-screen items-center justify-center bg-background text-sm text-muted">
        Checking secure session...
      </main>
    );
  }

  return (
    <div className="flex h-[100dvh] overflow-hidden bg-background text-foreground">
      {w.cmdOpen && <CommandPalette open onClose={() => w.setCmdOpen(false)} onNavigate={w.openNote} onCreateNote={() => w.createDraft()} onScanVault={w.scanVault} onCreateDraft={() => w.createDraft()} apiUrl={w.api} />}
      {w.monitorOpen && <ObservabilityPanel open apiUrl={w.api} onClose={() => w.setMonitorOpen(false)} />}
      {w.notificationsOpen && <NotificationsPopover open onClose={() => w.setNotificationsOpen(false)} apiUrl={w.api} />}
      {w.settingsOpen && <SettingsPanel open onClose={() => w.setSettingsOpen(false)} apiUrl={w.api} />}
      {w.guideOpen && <GuidePanel
        open={w.guideOpen}
        onClose={() => w.setGuideOpen(false)}
        onViewTour={() => setTourOpen(true)}
      />}
      <OnboardingModal open={tourOpen} onOpenChange={setTourOpen} />
      <RequiredAiSetup />

      <WorkspaceSidebar mobileOpen={mobileNavOpen} onMobileClose={() => setMobileNavOpen(false)} />
      <ResizeHandle />

      <section className="min-w-0 flex-1 flex flex-col">
        <MobileWorkspaceBar onMenu={() => setMobileNavOpen(true)} />
        {w.graphOpen ? (
          <GraphScreen apiUrl={w.api} onClose={() => w.setGraphOpen(false)} onOpenSettings={() => w.setSettingsOpen(true)} onNavigate={(path) => { w.setGraphOpen(false); w.openNote(path); }} />
        ) : (
          <>
            {!pathname.includes("/graph/nodes/") && <div className="border-b border-border/50 px-4 py-2 flex items-center gap-2">
              <button
                className="rounded-lg px-2 py-1 text-xs text-muted hover:bg-surface hover:text-foreground"
                onClick={() => {
                  w.setGraphOpen(false);
                  window.location.href = appPath("/brain");
                }}
              >
                Back to Home
              </button>
            </div>}
            {children}
          </>
        )}
      </section>
    </div>
  );
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <Shell>{children}</Shell>
    </WorkspaceProvider>
  );
}

function MobileWorkspaceBar({ onMenu }: { onMenu: () => void }) {
  const w = useWorkspace();
  const title = w.graphOpen ? "Knowledge Graph" : w.active?.title || "BerryBrain";

  return (
    <div className="flex h-12 shrink-0 items-center gap-2 border-b border-border/50 bg-panel px-3 lg:hidden">
      <button className="rounded-lg p-2 text-muted hover:bg-surface hover:text-foreground" onClick={onMenu} aria-label="Open navigation">
        <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7h16M4 12h16M4 17h16" /></svg>
      </button>
      <div className="min-w-0 flex-1">
        <div className="truncate text-sm font-medium">{title}</div>
        <div className="text-[10px] text-muted/55">{w.jobs.filter((job) => job.status === "pending").length ? "Processing queue active" : "Saved workspace"}</div>
      </div>
      <button className="rounded-lg p-2 text-muted hover:bg-surface hover:text-foreground" onClick={() => w.setGraphOpen(!w.graphOpen)} aria-label="Toggle graph">
        <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M17 7h.01M12 17h.01M7 7l5 10m5-10-5 10m-5-10h10" /></svg>
      </button>
      <button className="rounded-lg p-2 text-muted hover:bg-surface hover:text-foreground" onClick={() => w.setGuideOpen(true)} aria-label="Open guide">
        <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.25 9a3.75 3.75 0 117.05 1.79c-.89.52-1.55 1.16-1.55 2.21m-1.5 3.75h.01M12 21a9 9 0 100-18 9 9 0 000 18z" /></svg>
      </button>
      <button className="rounded-lg p-2 text-muted hover:bg-surface hover:text-foreground" onClick={() => w.setSettingsOpen(true)} aria-label="Open settings">
        <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 001.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
      </button>
    </div>
  );
}
