"use client";

import { WorkspaceProvider, useWorkspace } from "@/contexts/workspace-context";
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
import { useEffect } from "react";

function Shell() {
  const w = useWorkspace();

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
    <main className="h-screen bg-background text-foreground flex overflow-hidden">
      <CommandPalette open={w.cmdOpen} onClose={() => w.setCmdOpen(false)} onNavigate={w.openNote} onCreateNote={() => w.createDraft()} onScanVault={w.scanVault} onCreateDraft={() => w.createDraft()} apiUrl={w.api} />
      <ObservabilityPanel open={w.monitorOpen} apiUrl={w.api} onClose={() => w.setMonitorOpen(false)} />
      <SettingsPanel open={w.settingsOpen} onClose={() => w.setSettingsOpen(false)} apiUrl={w.api} />
      <GuidePanel open={w.guideOpen} onClose={() => w.setGuideOpen(false)} />
      <NotificationsPopover open={w.notificationsOpen} onClose={() => w.setNotificationsOpen(false)} apiUrl={w.api} />

      {w.toasts.length > 0 && (
        <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="alert" aria-live="polite">
          {w.toasts.map(t => <div key={t.id} className={`animate-slide-up rounded-xl px-3 py-2 text-sm shadow-md ${t.kind === "error" ? "bg-red-600/90 text-white" : t.kind === "success" ? "bg-accent/90 text-white" : "bg-panel/90 text-foreground ring-1 ring-border/50"}`}>{t.text}</div>)}
        </div>
      )}

      <WorkspaceSidebar />
      <ResizeHandle />

      <section className="min-w-0 flex-1 flex flex-col">
        {w.graphOpen ? (
          <GraphScreen apiUrl={w.api} onClose={() => w.setGraphOpen(false)} onNavigate={(path) => { w.setGraphOpen(false); w.openNote(path); }} />
        ) : w.active ? (
          <NoteEditor />
        ) : (
          <HomeView />
        )}
      </section>

      {w.rightOpen && <RightPanel />}
    </main>
  );
}

export function NoteWorkspace() {
  return <WorkspaceProvider><Shell /></WorkspaceProvider>;
}
