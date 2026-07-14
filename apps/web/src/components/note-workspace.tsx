"use client";

import { WorkspaceProvider, useWorkspace, appPath } from "@/contexts/workspace-context";
import { CommandPalette } from "./command-palette";
import { ObservabilityPanel } from "./observability-panel";
import { SettingsPanel } from "./settings-panel";
import { GraphScreen } from "./graph-screen";
import { GuidePanel } from "./guide-panel";
import { NotificationsPopover } from "./notifications-popover";
import { WorkspaceSidebar } from "./sidebar/workspace-sidebar";
import { NoteEditor } from "./editor/note-editor";
import { HomeView } from "./home/home-view";
import { RightPanel } from "./panel/right-panel";
import { ResizeHandle } from "./sidebar/resize-handle";
import { OnboardingModal } from "./onboarding-modal";
import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

function Shell() {
  const w = useWorkspace();
  const pathname = usePathname();
  const isDemo = pathname === "/demo" || pathname.endsWith("/demo");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const notePath = params.get("note");
    if (notePath) {
      const url = new URL(window.location.href);
      url.searchParams.delete("note");
      window.history.replaceState({}, "", url.toString());
      w.openNote(notePath);
    }
    const graph = params.get("graph");
    if (graph === "open") {
      w.setGraphOpen(true);
    }
    const monitor = params.get("monitor");
    if (monitor === "open") {
      w.setMonitorOpen(true);
      const url = new URL(window.location.href);
      url.searchParams.delete("monitor");
      window.history.replaceState({}, "", url.toString());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <main className="bb-workspace flex h-[100dvh] overflow-hidden bg-background text-foreground">
      <CommandPalette open={w.cmdOpen} onClose={() => w.setCmdOpen(false)} onNavigate={w.openNote} onCreateNote={() => w.createDraft()} onScanVault={w.scanVault} onCreateDraft={() => w.createDraft()} apiUrl={w.api} />
      <ObservabilityPanel open={w.monitorOpen} apiUrl={w.api} onClose={() => w.setMonitorOpen(false)} />
      <SettingsPanel open={w.settingsOpen} onClose={() => w.setSettingsOpen(false)} apiUrl={w.api} />
      <GuidePanel open={w.guideOpen} onClose={() => w.setGuideOpen(false)} />
      <NotificationsPopover open={w.notificationsOpen} onClose={() => w.setNotificationsOpen(false)} apiUrl={w.api} />
      <OnboardingModal demo={isDemo} />

      {w.toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="alert" aria-live="polite">
          {w.toasts.map(t => <div key={t.id} className={`animate-slide-up rounded-xl px-3 py-2 text-sm shadow-md ${t.kind === "error" ? "bg-red-600/90 text-white" : t.kind === "success" ? "bg-accent/90 text-white" : "bg-panel/90 text-foreground ring-1 ring-border/50"}`}>{t.text}</div>)}
        </div>
      )}

      <WorkspaceSidebar mobileOpen={mobileNavOpen} onMobileClose={() => setMobileNavOpen(false)} />
      <ResizeHandle />

       <section className="min-w-0 flex-1 flex flex-col">
        <MobileWorkspaceBar onMenu={() => setMobileNavOpen(true)} />
        {isDemo && <DemoNotice />}
        {w.graphOpen ? (
          <GraphScreen apiUrl={w.api} onClose={() => w.setGraphOpen(false)} onNavigate={(path) => { w.setGraphOpen(false); w.openNote(path); }} />
        ) : w.active ? (
          <NoteEditor />
        ) : (
          <HomeView />
        )}
      </section>

      {w.rightOpen && (
        <>
          <div className="fixed inset-0 z-30 bg-black/30 backdrop-blur-[1px] lg:hidden" onClick={() => w.setRightOpen(false)} aria-hidden="true" />
          <RightPanel />
        </>
      )}
    </main>
  );
}

export function NoteWorkspace() {
  const pathname = usePathname();
  const isDemo = pathname === "/demo" || pathname.endsWith("/demo");
  return <WorkspaceProvider demo={isDemo}><Shell /></WorkspaceProvider>;
}

function DemoNotice() {
  const go = (path: string) => { window.location.href = appPath(path); };
  return (
    <div className="flex flex-wrap items-center gap-3 border-b border-border/50 bg-accent-soft/40 px-4 py-2.5 text-sm">
      <span className="text-muted">Demo is read-only. Set up a local instance to use all features.</span>
      <div className="ml-auto flex gap-2">
        <button className="bb-action px-3 py-1 text-xs font-medium" onClick={() => go("/login")}>Login</button>
        <button className="bb-action px-3 py-1 text-xs font-medium" onClick={() => go("/setup")}>Setup</button>
      </div>
    </div>
  );
}

function MobileWorkspaceBar({ onMenu }: { onMenu: () => void }) {
  const w = useWorkspace();
  const title = w.graphOpen ? "Knowledge Graph" : w.active?.title || "BerryBrain";

  return (
    <div className="bb-mobile-bar flex h-12 shrink-0 items-center gap-2 bg-panel px-3 lg:hidden">
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
