"use client";

import { WorkspaceProvider, useWorkspace, appPath } from "@/contexts/workspace-context";
import { RequiredAiSetup } from "./required-ai-setup";
import { WorkspaceSidebar } from "./sidebar/workspace-sidebar";
import { NoteEditor } from "./editor/note-editor";
import type { EditorSelectionContext } from "./ask-editor-diff-plan";
import { HomeView } from "./home/home-view";
import { RightPanel } from "./panel/right-panel";
import { ResizeHandle } from "./sidebar/resize-handle";
import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import type { Route } from "next";
import { usePathname, useRouter } from "next/navigation";
import dynamic from "next/dynamic";

const CommandPalette = dynamic(() => import("./command-palette").then((module) => module.CommandPalette));
const ObservabilityPanel = dynamic(() => import("./observability-panel").then((module) => module.ObservabilityPanel));
const loadSettingsPanel = () =>
  import("./settings-panel").then((module) => module.SettingsPanel);
const SettingsPanel = dynamic(loadSettingsPanel, {
  loading: () => (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-4">
      <div
        role="dialog"
        aria-label="Settings"
        aria-modal="true"
        className="w-full max-w-4xl rounded-lg border border-border bg-panel px-5 py-4 text-sm text-muted shadow-xl"
      >
        Loading settings...
      </div>
    </div>
  ),
});
const GuidePanel = dynamic(() => import("./guide-panel").then((module) => module.GuidePanel));
const NotificationsPopover = dynamic(() => import("./notifications-popover").then((module) => module.NotificationsPopover));
const OnboardingModal = dynamic(() => import("./onboarding-modal").then((module) => module.OnboardingModal));
const loadGraphScreen = () =>
  import("./graph-screen").then((module) => module.GraphScreen);

const GraphScreen = dynamic(
  loadGraphScreen,
  {
    ssr: false,
    loading: () => <div className="flex min-h-0 flex-1 items-center justify-center text-sm text-muted">Loading graph...</div>,
  },
);

function Shell({ children }: { children?: ReactNode }) {
  const w = useWorkspace();
  const router = useRouter();
  const pathname = usePathname();
  const isDemo = pathname === "/demo" || pathname.endsWith("/demo");
  const isAskPage = pathname === "/ask" || pathname.endsWith("/ask");
  const [askInitialQuery, setAskInitialQuery] = useState("");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [tourOpen, setTourOpen] = useState(false);
  const [editorAskOpen, setEditorAskOpen] = useState(false);
  const [editorSelection, setEditorSelection] = useState<EditorSelectionContext | null>(null);
  const [editorContextScope, setEditorContextScope] = useState<"saved_note" | "selection" | "vault">("saved_note");
  const [editorPromptSeed, setEditorPromptSeed] = useState("");
  const [focusedGraphNodeId, setFocusedGraphNodeId] = useState("");
  const editorCommitDraftRef = useRef<((nextText: string) => void) | null>(null);

  const registerEditorCommitDraft = useCallback((fn: ((nextText: string) => void) | null) => {
    editorCommitDraftRef.current = fn;
  }, []);

  useEffect(() => {
    setEditorAskOpen(false);
    setEditorSelection(null);
    setEditorContextScope("saved_note");
    setEditorPromptSeed("");
  }, [w.active?.path]);

  useEffect(() => {
    if (!/\/(brain|demo)\/?$/.test(pathname)) w.setGraphOpen(false);
    const params = new URLSearchParams(window.location.search);
    if (params.get("settings") === "open") w.setSettingsOpen(true);
    setAskInitialQuery(params.get("q")?.trim() || "");
    const notePath = params.get("note");
    const vaultPath = params.get("vault")?.trim();
    const newNote = params.get("newNote");
    if (notePath) {
      const url = new URL(window.location.href);
      url.searchParams.delete("note");
      window.history.replaceState({}, "", url.toString());
      w.openNote(notePath);
    }
    if (vaultPath) {
      const url = new URL(window.location.href);
      url.searchParams.delete("vault");
      window.history.replaceState({}, "", url.toString());
      w.setGraphOpen(false);
      w.setFocusedFolder(vaultPath);
    }
    if (newNote === "1") {
      const url = new URL(window.location.href);
      url.searchParams.delete("newNote");
      window.history.replaceState({}, "", url.toString());
      w.createDraft();
    }
    const graph = params.get("graph");
    if (graph === "open" || graph === "1") {
      w.setGraphOpen(true);
    }
    const focusNode = params.get("focusNode")?.trim();
    if (focusNode) {
      const url = new URL(window.location.href);
      url.searchParams.delete("focusNode");
      window.history.replaceState({}, "", url.toString());
      setFocusedGraphNodeId(focusNode);
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
  }, [pathname]);
  useEffect(() => {
    router.prefetch(appPath("/ask") as Route);
    router.prefetch(appPath("/activity") as Route);
    const preloadWorkspaceTools = () => {
      void Promise.all([loadGraphScreen(), loadSettingsPanel()]);
    };
    const idleId = window.requestIdleCallback?.(preloadWorkspaceTools, { timeout: 2500 });
    const timeoutId = idleId === undefined ? window.setTimeout(preloadWorkspaceTools, 1200) : undefined;
    return () => {
      if (idleId !== undefined) window.cancelIdleCallback?.(idleId);
      if (timeoutId !== undefined) window.clearTimeout(timeoutId);
    };
  }, [router]);
  return (
    <main className="bb-workspace flex h-[100dvh] overflow-hidden bg-background text-foreground">
      {w.cmdOpen && <CommandPalette open onClose={() => w.setCmdOpen(false)} onNavigate={w.openNote} onCreateNote={() => w.createDraft()} onScanVault={w.scanVault} onCreateDraft={() => w.createDraft()} apiUrl={w.api} />}
      {w.monitorOpen && <ObservabilityPanel open apiUrl={w.api} onClose={() => w.setMonitorOpen(false)} />}
      {w.settingsOpen && <SettingsPanel open onClose={() => w.setSettingsOpen(false)} apiUrl={w.api} />}
      {w.guideOpen && <GuidePanel
        open={w.guideOpen}
        onClose={() => w.setGuideOpen(false)}
        onViewTour={() => setTourOpen(true)}
      />}
      {w.notificationsOpen && <NotificationsPopover open onClose={() => w.setNotificationsOpen(false)} apiUrl={w.api} />}
      <OnboardingModal
        demo={isDemo}
        open={tourOpen}
        onOpenChange={setTourOpen}
      />
      <RequiredAiSetup demo={isDemo} />

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
        {isAskPage ? (
          <GraphScreen
            apiUrl={w.api}
            askOnly
            autoFocusAsk
            autoSubmitAsk={Boolean(askInitialQuery)}
            initialAskQuery={askInitialQuery}
            onClose={() => router.push(appPath("/brain") as Route)}
            onOpenHome={() => router.push(appPath("/brain") as Route)}
            onOpenGraph={() => router.push(appPath("/brain?graph=open") as Route)}
            onOpenSettings={() => w.setSettingsOpen(true)}
            onNavigate={(path) => { void w.openNote(path); router.push(appPath("/brain") as Route); }}
          />
        ) : w.graphOpen ? (
          <GraphScreen apiUrl={w.api} autoFocusAsk={w.askRequested} initialAskQuery={w.askQuery} focusNodeId={focusedGraphNodeId} onFocusNodeConsumed={() => setFocusedGraphNodeId("")} onAskFocused={w.consumeAskRequest} onClose={() => w.setGraphOpen(false)} onOpenSettings={() => w.setSettingsOpen(true)} onNavigate={(path) => { w.setGraphOpen(false); w.openNote(path); }} />
        ) : children ? children : w.active ? (
          <NoteEditor
            onOpenAsk={(selection) => {
              if (selection) {
                setEditorSelection(selection);
                setEditorContextScope("selection");
              } else {
                setEditorContextScope("saved_note");
              }
              setEditorPromptSeed("");
              setEditorAskOpen(true);
            }}
            onSelectionChange={setEditorSelection}
            onRegisterCommitDraft={registerEditorCommitDraft}
          />
        ) : (
          <HomeView />
        )}
      </section>

      {editorAskOpen && w.active && !isAskPage && !w.graphOpen && (() => {
        const activeNote = w.active;
        const isUnsavedDraft = w.draft !== activeNote.content;
        const activeSelection =
          editorSelection && editorSelection.notePath === activeNote.path && editorSelection.text.trim()
            ? editorSelection
            : null;
        const currentFolder = activeNote.folder || (activeNote.path.includes("/") ? activeNote.path.slice(0, activeNote.path.lastIndexOf("/")) : "inbox");
        const baseQuery = editorPromptSeed || (
          editorContextScope === "selection" && activeSelection
            ? `Sobre o trecho selecionado da nota "${activeNote.title}" (${activeSelection.isUnsavedDraft ? "rascunho local não salvo" : `revisão salva ${(activeSelection.noteRevision || "local").slice(0, 8)}`}): "${activeSelection.text.slice(0, 400)}" — `
            : editorContextScope === "vault"
              ? `Considerando o vault/pasta "${currentFolder}" e a nota "${activeNote.title}": `
              : `Sobre a nota "${activeNote.title}": `
        );
        const buildIntentPrompt = (intent: "explain" | "summarize" | "reorganize" | "connections" | "suggest") => {
          const targetDesc =
            editorContextScope === "selection" && activeSelection
              ? `o trecho selecionado ("${activeSelection.text.slice(0, 400)}") da nota "${activeNote.title}"`
              : editorContextScope === "vault"
                ? `a nota "${activeNote.title}" no contexto de "${currentFolder}"`
                : `a nota "${activeNote.title}"`;
          switch (intent) {
            case "explain":
              return `Explique ${targetDesc} usando as fontes verificadas.`;
            case "summarize":
              return `Resuma ${targetDesc} destacando os pontos principais.`;
            case "reorganize":
              return `Reorganize ${targetDesc} em seções Markdown claras.`;
            case "connections":
              return `Quais conexões verificadas existem no grafo para ${targetDesc}?`;
            case "suggest":
              return `Sugira um complemento fundamentado para ${targetDesc}.`;
          }
        };
        return (
          <aside className="fixed inset-y-0 right-0 z-40 flex w-full flex-col border-l border-border bg-background shadow-2xl lg:w-[min(620px,65vw)]" aria-label="Ask BerryBrain beside note">
            <div className="flex shrink-0 items-center justify-between gap-3 border-b border-border bg-panel px-4 py-2 text-xs">
              <span className="truncate font-semibold">Ask beside: {activeNote.title}</span>
              <button className="bb-action px-2 py-1" onClick={() => setEditorAskOpen(false)} aria-label="Close Ask panel">Close</button>
            </div>
            <div className="shrink-0 space-y-2 border-b border-border bg-surface/40 px-4 py-2.5 text-[11px]">
              <div className="flex flex-wrap items-center justify-between gap-2 text-muted">
                <span>
                  Only saved BerryBrain content is retrieved. Unsaved editor text is not sent automatically.
                </span>
                <span className="rounded border border-border bg-panel px-2 py-0.5 font-mono text-[10px] text-foreground">
                  {isUnsavedDraft
                    ? `Unsaved draft · base rev ${(activeNote.content_hash || "local").slice(0, 8)}`
                    : `Saved rev ${(activeNote.content_hash || "local").slice(0, 8)}`}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Ask context scope">
                <span className="text-muted">Context:</span>
                <button
                  type="button"
                  aria-pressed={editorContextScope === "saved_note"}
                  className={`rounded-md border px-2 py-0.5 text-[11px] ${editorContextScope === "saved_note" ? "border-accent bg-accent-soft text-accent font-medium" : "border-border bg-panel text-muted hover:text-foreground"}`}
                  onClick={() => { setEditorContextScope("saved_note"); setEditorPromptSeed(""); }}
                >
                  Saved note
                </button>
                <button
                  type="button"
                  aria-pressed={editorContextScope === "vault"}
                  className={`rounded-md border px-2 py-0.5 text-[11px] ${editorContextScope === "vault" ? "border-accent bg-accent-soft text-accent font-medium" : "border-border bg-panel text-muted hover:text-foreground"}`}
                  onClick={() => { setEditorContextScope("vault"); setEditorPromptSeed(""); }}
                >
                  Current vault/folder ({currentFolder})
                </button>
                <button
                  type="button"
                  disabled={!activeSelection}
                  aria-pressed={editorContextScope === "selection"}
                  className={`rounded-md border px-2 py-0.5 text-[11px] disabled:opacity-45 ${editorContextScope === "selection" ? "border-accent bg-accent-soft text-accent font-medium" : "border-border bg-panel text-muted hover:text-foreground"}`}
                  onClick={() => { if (activeSelection) { setEditorContextScope("selection"); setEditorPromptSeed(""); } }}
                >
                  {activeSelection
                    ? `Selection (${activeSelection.text.length} chars · ${activeSelection.isUnsavedDraft ? "unsaved draft" : "saved"})`
                    : "Selection (none)"}
                </button>
              </div>
              <div className="flex flex-wrap items-center gap-1.5" role="group" aria-label="Editor Ask actions">
                <span className="text-muted">Intent:</span>
                {(
                  [
                    ["explain", "Explain"],
                    ["summarize", "Summarize"],
                    ["reorganize", "Reorganize"],
                    ["connections", "Connections"],
                    ["suggest", "Suggest"],
                  ] as const
                ).map(([intent, label]) => (
                  <button
                    key={intent}
                    type="button"
                    className="bb-action px-2 py-0.5 text-[11px]"
                    onClick={() => setEditorPromptSeed(buildIntentPrompt(intent))}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
            <GraphScreen
              key={activeNote.path}
              apiUrl={w.api}
              askOnly
              autoFocusAsk
              initialAskQuery={baseQuery}
              editorTarget={{
                notePath: activeNote.path,
                noteTitle: activeNote.title,
                noteRevision: activeNote.content_hash || "",
                draft: w.draft,
                isUnsavedDraft,
                selection: activeSelection,
                applyDraft: (nextText: string) => {
                  if (editorCommitDraftRef.current) {
                    editorCommitDraftRef.current(nextText);
                  } else {
                    w.setDraft(nextText);
                  }
                },
              }}
              onClose={() => setEditorAskOpen(false)}
              onOpenHome={() => setEditorAskOpen(false)}
              onOpenGraph={() => { setEditorAskOpen(false); w.setGraphOpen(true); }}
              onOpenSettings={() => w.setSettingsOpen(true)}
              onNavigate={(path) => { setEditorAskOpen(false); void w.openNote(path); }}
            />
          </aside>
        );
      })()}

      {w.rightOpen && (
        <>
          <div className="fixed inset-0 z-30 bg-black/30 backdrop-blur-[1px] lg:hidden" onClick={() => w.setRightOpen(false)} aria-hidden="true" />
          <RightPanel />
        </>
      )}
    </main>
  );
}

export function NoteWorkspace({ children }: { children?: ReactNode }) {
  const pathname = usePathname();
  const isDemo = pathname === "/demo" || pathname.endsWith("/demo");
  return <WorkspaceProvider demo={isDemo}><Shell>{children}</Shell></WorkspaceProvider>;
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
