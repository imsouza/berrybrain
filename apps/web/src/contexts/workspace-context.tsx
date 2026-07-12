"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AutosaveStatus, Insight, JobSummary, NoteDetail, NoteSummary, Stats, Toast } from "@/types";

export function getApiUrl() {
  const env = process.env.NEXT_PUBLIC_BERRYBRAIN_API_URL;
  if (env) return env;
  if (typeof window === "undefined") return "";
  return "";
}
export function appPath(p: string) {
  const basePath = process.env.NEXT_PUBLIC_BERRYBRAIN_BASE_PATH || "";
  return `${basePath}${p}`;
}
function getRuntimeBasePath() {
  if (typeof window === "undefined") return "";
  const pathname = window.location.pathname;
  return pathname === "/berrybrain" || pathname.startsWith("/berrybrain/") ? "/berrybrain" : "";
}
function encode(path: string) { return path.split("/").map(encodeURIComponent).join("/"); }
let _tid = 0;

const DEMO_NOTE_DETAILS: NoteDetail[] = [
  {
    title: "Evidence-first thinking",
    path: "demo/evidence-first-thinking.md",
    folder: "demo",
    content: [
      "# Evidence-first thinking",
      "",
      "BerryBrain keeps notes, graph links, and generated insights tied to the source material that produced them.",
      "",
      "Use the graph to see how concepts connect, then open each note to inspect the reasoning trail before accepting a connection.",
    ].join("\n"),
  },
  {
    title: "Knowledge graph workflow",
    path: "demo/knowledge-graph-workflow.md",
    folder: "demo",
    content: [
      "# Knowledge graph workflow",
      "",
      "- Capture raw notes.",
      "- Let the system extract concepts and possible relationships.",
      "- Confirm, ignore, or expand graph nodes as your understanding changes.",
      "",
      "The graph is most useful when it remains reviewable instead of becoming a black box.",
    ].join("\n"),
  },
  {
    title: "Account safety checklist",
    path: "demo/account-safety-checklist.md",
    folder: "security",
    content: [
      "# Account safety checklist",
      "",
      "- Verified email before trusted account actions.",
      "- Session cookies with CSRF headers for sensitive mutations.",
      "- Admin access limited to the configured administrator email.",
      "- Audit events for account and admin activity.",
    ].join("\n"),
  },
];

const DEMO_JOBS: JobSummary[] = [
  { id: 1, type: "FIND_CONNECTIONS", status: "completed", payload: { note_path: "demo/evidence-first-thinking.md" }, error_message: null },
  { id: 2, type: "GENERATE_GRAPH_INSIGHTS", status: "completed", payload: { note_path: "demo/knowledge-graph-workflow.md" }, error_message: null },
  { id: 3, type: "ASSIMILATE_NOTE", status: "pending", payload: { note_path: "security/account-safety-checklist.md" }, error_message: null },
];

const DEMO_INSIGHTS: Insight[] = [
  {
    id: 1,
    type: "new_connection",
    title: "Security controls should be visible in the workflow",
    description: "The account safety note connects directly to the evidence-first workflow: users need to inspect why a sensitive action is allowed.",
    priority: 1,
    evidence: ["Account safety checklist", "Evidence-first thinking"],
    suggested_action: "Review the security model before enabling public access.",
    confidence: 0.88,
    status: "suggested",
    provider: "local-demo",
    model: "demo",
  },
  {
    id: 2,
    type: "study_path",
    title: "Start with graph review, then refine notes",
    description: "The demo notes show a useful loop: capture, connect, inspect evidence, then rewrite the source note.",
    priority: 0,
    evidence: ["Knowledge graph workflow"],
    suggested_action: "Open the graph and inspect the connected notes.",
    confidence: 0.81,
    status: "suggested",
    provider: "local-demo",
    model: "demo",
  },
];

const DEMO_STATS: Stats = {
  notes: DEMO_NOTE_DETAILS.length,
  connections: 5,
  metadata: 9,
  jobs: { pending: 1 },
};

function demoNoteSummaries(): NoteSummary[] {
  return DEMO_NOTE_DETAILS.map(({ content: _content, ...note }) => note);
}

function demoContentMap() {
  return Object.fromEntries(DEMO_NOTE_DETAILS.map((note) => [note.path, note.content]));
}

type Ctx = {
  api: string;
  demo: boolean;
  notes: NoteSummary[]; stats: Stats | null; jobs: JobSummary[];
  active: NoteDetail | null; draft: string; autosave: AutosaveStatus; viewMode: "edit" | "preview" | "split";
  insights: Insight[];
  sidebarWidth: number; rightOpen: boolean;
  cmdOpen: boolean; monitorOpen: boolean; settingsOpen: boolean; graphOpen: boolean; guideOpen: boolean; notificationsOpen: boolean;
  creatingDraft: boolean;
  toasts: Toast[];
  setDraft: (v: string) => void; setViewMode: (v: "edit" | "preview" | "split") => void;
  setSidebarWidth: (w: number) => void; setRightOpen: (v: boolean) => void;
  setCmdOpen: (v: boolean) => void; setMonitorOpen: (v: boolean) => void; setSettingsOpen: (v: boolean) => void; setGraphOpen: (v: boolean) => void; setGuideOpen: (v: boolean) => void; setNotificationsOpen: (v: boolean) => void;
  openNote: (p: string) => Promise<void>; closeNote: () => void; save: () => Promise<void>; download: () => void; renameNote: () => Promise<void>;
  createDraft: (content?: string) => Promise<void>; deleteActive: () => Promise<void>; scanVault: () => Promise<void>;
  loadAll: () => Promise<void>; toast: (t: string, k?: Toast["kind"]) => void;
};

const C = createContext<Ctx>(null!);
export function useWorkspace() { return useContext(C); }

export function WorkspaceProvider({ children, demo = false }: { children: ReactNode; demo?: boolean }) {
  const api = useMemo(() => demo ? "__demo__" : getApiUrl(), [demo]);
  const [notes, setNotes] = useState<NoteSummary[]>(() => demo ? demoNoteSummaries() : []);
  const [active, setActive] = useState<NoteDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [jobs, setJobs] = useState<JobSummary[]>(() => demo ? DEMO_JOBS : []);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [stats, setStats] = useState<Stats | null>(() => demo ? DEMO_STATS : null);
  const [insights, setInsights] = useState<Insight[]>(() => demo ? DEMO_INSIGHTS : []);
  const [demoContents, setDemoContents] = useState<Record<string, string>>(() => demo ? demoContentMap() : {});
  const [sidebarWidth, setSidebarWidth] = useState(() => typeof window === "undefined" ? 280 : Number(localStorage.getItem("bb_sidebar_w") || 280));
  const [rightOpen, setRightOpen] = useState(false);
  const [autosave, setAutosave] = useState<AutosaveStatus>("saved");
  const [viewMode, setViewMode] = useState<"edit" | "preview" | "split">("edit");
  const [cmdOpen, setCmdOpen] = useState(false);
  const [monitorOpen, setMonitorOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [guideOpen, setGuideOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [creatingDraft, setCreatingDraft] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const toast = useCallback((text: string, kind: Toast["kind"] = "info") => {
    const id = ++_tid;
    setToasts(t => [...t, { id, text, kind }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  async function loadAll() {
    if (demo) return;
    try {
      const [nr, jr, sr, insR] = await Promise.all([
        fetch(`${api}/api/v1/notes`), fetch(`${api}/api/v1/jobs?limit=8`),
        fetch(`${api}/api/v1/monitor/stats`),
        fetch(`${api}/api/v1/insights?limit=5`),
      ]);
      if (nr.ok) setNotes((await nr.json()).notes);
      if (jr.ok) setJobs((await jr.json()).jobs);
      if (sr.ok) setStats(await sr.json());
      if (insR.ok) setInsights((await insR.json()).insights || []);
    } catch {}
  }

  async function openNote(path: string) {
    if (demo) {
      const note = notes.find((item) => item.path === path);
      if (!note) { toast("Demo note not found.", "error"); return; }
      const detail = { ...note, content: demoContents[path] || "" };
      setActive(detail); setDraft(detail.content); setRightOpen(false); setAutosave("saved");
      return;
    }
    const r = await fetch(`${api}/api/v1/notes/${encode(path)}`);
    if (!r.ok) { toast("Failed to open note.", "error"); return; }
    const n = await r.json();
    setActive(n); setDraft(n.content); setRightOpen(false); setAutosave("saved");
  }

  async function save() {
    if (!active) return;
    if (demo) {
      setDemoContents((current) => ({ ...current, [active.path]: draft }));
      setActive({ ...active, content: draft });
      setAutosave("saved");
      return;
    }
    setAutosave("saving");
    const r = await fetch(`${api}/api/v1/notes/${encode(active.path)}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: draft }),
    });
    if (r.ok) { setActive(await r.json()); setAutosave("saved"); }
    else { toast("Failed to save note.", "error"); setAutosave("unsaved"); }
  }

  async function createDraft(content = "") {
    setCreatingDraft(true);
    try {
      if (demo) {
        const id = Date.now();
        const note: NoteDetail = {
          title: content.trim().split("\n")[0]?.replace(/^#+\s*/, "").slice(0, 48) || "Demo draft",
          path: `demo/demo-draft-${id}.md`,
          folder: "demo",
          content,
        };
        setNotes((prev) => [{ title: note.title, path: note.path, folder: note.folder }, ...prev]);
        setDemoContents((current) => ({ ...current, [note.path]: note.content }));
        setActive(note); setDraft(note.content); setAutosave("saved");
        return;
      }
      const r = await fetch(`${api}/api/v1/notes`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: "inbox", content }),
      });
      if (!r.ok) { toast("Failed to create note.", "error"); return; }
      const n = await r.json();
      setNotes((prev) => [n, ...prev]);
      setActive(n); setDraft(n.content || content); setAutosave("saved");
    } catch {
      toast("API unavailable.", "error");
    } finally {
      setCreatingDraft(false);
    }
  }

  async function deleteActive() {
    if (!active || !confirm(`Delete ${active.path}?`)) return;
    if (demo) {
      const path = active.path;
      setNotes((current) => current.filter((note) => note.path !== path));
      setDemoContents((current) => {
        const next = { ...current };
        delete next[path];
        return next;
      });
      setActive(null); setDraft(""); toast("Demo note deleted.", "success");
      return;
    }
    await fetch(`${api}/api/v1/notes/${encode(active.path)}`, { method: "DELETE" });
    setActive(null); setDraft(""); toast("Deleted.", "success"); await loadAll();
  }

  async function scanVault() {
    if (demo) {
      toast("Demo vault is already loaded.", "info");
      return;
    }
    const r = await fetch(`${api}/api/v1/vault/scan`, { method: "POST" });
    if (r.ok) { await loadAll(); toast("Vault scanned."); }
  }

  async function closeNote() { setActive(null); setDraft(""); loadAll(); }

  async function download() {
    if (!active) return;
    if (demo) {
      const blob = new Blob([draft], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${active.title}.md`;
      a.click();
      URL.revokeObjectURL(url);
      return;
    }
    const a = document.createElement("a");
    a.href = `${api}/api/v1/notes/${encode(active.path)}/download`;
    a.download = `${active.title}.md`;
    a.click();
  }

  async function renameNote() {
    if (!active) return;
    const newTitle = window.prompt("New title:", active.title);
    if (!newTitle || newTitle === active.title) return;
    if (demo) {
      setActive({ ...active, title: newTitle });
      setNotes((current) => current.map((note) => note.path === active.path ? { ...note, title: newTitle } : note));
      toast("Demo note renamed.", "success");
      return;
    }
    try {
      const r = await fetch(`${api}/api/v1/notes/${encode(active.path)}/rename`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });
      if (!r.ok) { toast("Failed to rename note.", "error"); return; }
      const updated = await r.json();
      setActive({ ...active, title: updated.title, path: updated.path });
      toast("Renamed.", "success");
      loadAll();
    } catch { toast("Failed to rename note.", "error"); }
  }

  const renameSent = useRef(false);
  const handleDraft = useCallback((val: string) => {
    setDraft(val);
    setAutosave("unsaved");
    if (val.length > 50 && active && /^(rascunho|nota-sem-titulo)/i.test(active.title) && !renameSent.current) {
      renameSent.current = true;
      aiRename(active.path);
    }
  }, [active]);

  useEffect(() => {
    if (active) renameSent.current = false;
  }, [active]);

  async function aiRename(path: string) {
    if (demo) return;
    try {
      await fetch(`${api}/api/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "GENERATE_NOTE_TITLE", payload: { note_path: path } }),
      });
    } catch {}
  }

  useEffect(() => { loadAll(); }, []);
  useEffect(() => {
    if (demo) return;
    const iv = setInterval(() => { fetch(`${api}/api/v1/jobs?limit=8`).then(r => { if (r.ok) r.json().then(d => setJobs(d.jobs)); }).catch(() => {}); }, 8000);
    return () => clearInterval(iv);
  }, [api, demo]);
  useEffect(() => {
    if (!active || autosave !== "unsaved") return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(save, 3000);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [draft]);
  useEffect(() => {
    function h(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); setCmdOpen(o => !o); return; }
      if ((e.metaKey || e.ctrlKey) && e.key === "s") { e.preventDefault(); save(); return; }
      if (e.key === "Escape") { if (active) closeNote(); if (cmdOpen) setCmdOpen(false); }
    }
    window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h);
  }, [draft, active]);

  return (
    <C.Provider value={{ api, demo, notes, stats, jobs, active, draft, autosave, viewMode, insights, sidebarWidth, rightOpen, graphOpen, guideOpen, cmdOpen, monitorOpen, settingsOpen, notificationsOpen, creatingDraft, toasts, setDraft: handleDraft, setViewMode, setSidebarWidth, setRightOpen, setCmdOpen, setMonitorOpen, setSettingsOpen, setGraphOpen, setGuideOpen, setNotificationsOpen, openNote, closeNote, save, download, renameNote, createDraft, deleteActive, scanVault, loadAll, toast }}>
      {children}
      {creatingDraft && (
        <div className="fixed inset-0 z-[100] grid place-items-center bg-background/60 backdrop-blur-sm">
          <div className="flex flex-col items-center gap-3 rounded-xl bg-panel px-6 py-5 shadow-lg">
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
            <span className="text-xs text-muted">Creating note...</span>
          </div>
        </div>
      )}
    </C.Provider>
  );
}
