"use client";

import { useEffect, useRef } from "react";
import { WorkspaceProvider, useWorkspace } from "@/contexts/workspace-context";
import { WorkspaceSidebar } from "@/components/sidebar/workspace-sidebar";
import { ResizeHandle } from "@/components/sidebar/resize-handle";
import { CommandPalette } from "@/components/command-palette";
import { ObservabilityPanel } from "@/components/observability-panel";
import { NotificationsPopover } from "@/components/notifications-popover";
import { SettingsPanel } from "@/components/settings-panel";
import { GuidePanel } from "@/components/guide-panel";
import { GraphScreen } from "@/components/graph-screen";

function Shell({ children }: { children: React.ReactNode }) {
  const w = useWorkspace();
  const prevActive = useRef(w.active);

  useEffect(() => {
    if (w.active && w.active !== prevActive.current) {
      window.location.href = `/?note=${encodeURIComponent(w.active.path)}`;
    }
    prevActive.current = w.active;
  }, [w.active]);
  return (
    <div className="h-screen bg-background text-foreground flex overflow-hidden">
      <CommandPalette open={w.cmdOpen} onClose={() => w.setCmdOpen(false)} onNavigate={w.openNote} onCreateNote={() => w.createDraft()} onScanVault={w.scanVault} onCreateDraft={() => w.createDraft()} apiUrl={w.api} />
      <ObservabilityPanel open={w.monitorOpen} apiUrl={w.api} onClose={() => w.setMonitorOpen(false)} />
      <NotificationsPopover open={w.notificationsOpen} onClose={() => w.setNotificationsOpen(false)} apiUrl={w.api} />
      <SettingsPanel open={w.settingsOpen} onClose={() => w.setSettingsOpen(false)} apiUrl={w.api} />
      <GuidePanel open={w.guideOpen} onClose={() => w.setGuideOpen(false)} />

      <WorkspaceSidebar />
      <ResizeHandle />

      <section className="min-w-0 flex-1 flex flex-col">
        {w.graphOpen ? (
          <GraphScreen apiUrl={w.api} onClose={() => w.setGraphOpen(false)} onNavigate={(path) => { w.setGraphOpen(false); w.openNote(path); }} />
        ) : (
          <>
            <div className="border-b border-border/50 px-4 py-2 flex items-center gap-2">
              <button
                className="rounded-lg px-2 py-1 text-xs text-muted hover:bg-surface hover:text-foreground"
                onClick={() => (window.location.href = "/")}
              >
                ← Voltar para Home
              </button>
            </div>
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