"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AutosaveStatus, Insight, JobSummary, NoteDetail, NoteSummary, Stats, Toast } from "@/types";
import {
  BROWSER_STORAGE_MODE,
  browserStats,
  createBrowserNote,
  deleteBrowserNote,
  getBrowserNote,
  initializeBrowserStorage,
  listBrowserNotes,
  renameBrowserNote,
  saveBrowserNote,
} from "@/lib/browser-storage";

export function getApiUrl() {
  if (process.env.NEXT_PUBLIC_BERRYBRAIN_STORAGE_MODE === "browser") return "__browser__";
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
function readCsrf(): string {
  if (typeof document === "undefined") return "";
  const match = document.cookie.match(/(?:^|;\s*)bb_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}
export function apiFetch(input: string, init: RequestInit = {}) {
  const method = (init.method || "GET").toUpperCase();
  const headers = new Headers(init.headers);
  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const csrf = readCsrf();
    if (csrf) headers.set("X-CSRF-Token", csrf);
  }
  return fetch(input, { ...init, credentials: "include", headers });
}
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
      "- Owner actions limited to the authenticated local account.",
      "- Audit events for account and sensitive activity.",
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
  saveConflict: { currentContent: string; currentContentHash: string } | null;
  toasts: Toast[];
  setDraft: (v: string) => void; setViewMode: (v: "edit" | "preview" | "split") => void;
  setSidebarWidth: (w: number) => void; setRightOpen: (v: boolean) => void;
  setCmdOpen: (v: boolean) => void; setMonitorOpen: (v: boolean) => void; setSettingsOpen: (v: boolean) => void; setGraphOpen: (v: boolean) => void; setGuideOpen: (v: boolean) => void; setNotificationsOpen: (v: boolean) => void;
  openNote: (p: string) => Promise<void>; closeNote: () => void; save: () => Promise<void>; download: () => void; renameNote: () => Promise<void>;
  resolveSaveConflict: (strategy: "reload" | "overwrite") => Promise<void>;
  createDraft: (content?: string) => Promise<boolean>; deleteActive: () => Promise<void>; scanVault: () => Promise<void>;
  loadAll: () => Promise<void>; toast: (t: string, k?: Toast["kind"]) => void;
};

const C = createContext<Ctx>(null!);
export function useWorkspace() { return useContext(C); }

export function WorkspaceProvider({ children, demo = false }: { children: ReactNode; demo?: boolean }) {
  const api = useMemo(
    () => (demo ? "__demo__" : BROWSER_STORAGE_MODE ? "__browser__" : getApiUrl()),
    [demo],
  );
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
  const [saveConflict, setSaveConflict] = useState<{
    currentContent: string;
    currentContentHash: string;
  } | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const draftRef = useRef(draft);

  const toast = useCallback((text: string, kind: Toast["kind"] = "info") => {
    const id = ++_tid;
    setToasts(t => [...t, { id, text, kind }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  async function loadAll() {
    if (demo) return;
    if (BROWSER_STORAGE_MODE) {
      try {
        await initializeBrowserStorage();
        const [localNotes, localStats] = await Promise.all([listBrowserNotes(), browserStats()]);
        setNotes(localNotes);
        setStats(localStats);
        setJobs([]);
        setInsights([]);
      } catch {
        toast("Browser storage could not be opened.", "error");
      }
      return;
    }
    try {
      const [nr, jr, sr, insR] = await Promise.all([
        apiFetch(`${api}/api/v1/notes`), apiFetch(`${api}/api/v1/jobs?limit=8`),
        apiFetch(`${api}/api/v1/monitor/stats`),
        apiFetch(`${api}/api/v1/insights?limit=5`),
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
      setActive(detail); setDraft(detail.content); draftRef.current = detail.content; setSaveConflict(null); setRightOpen(false); setAutosave("saved");
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      const note = await getBrowserNote(path);
      if (!note) {
        toast("Note not found in browser storage.", "error");
        return;
      }
      setActive(note);
      setDraft(note.content);
      draftRef.current = note.content;
      setSaveConflict(null);
      setRightOpen(false);
      setAutosave("saved");
      return;
    }
    const r = await apiFetch(`${api}/api/v1/notes/${encode(path)}`);
    if (!r.ok) { toast("Failed to open note.", "error"); return; }
    const n = await r.json();
    setActive(n); setDraft(n.content); draftRef.current = n.content; setSaveConflict(null); setRightOpen(false); setAutosave("saved");
  }

  async function persistDraft(baseContentHash?: string) {
    if (!active) return;
    if (demo) {
      setDemoContents((current) => ({ ...current, [active.path]: draft }));
      setActive({ ...active, content: draft });
      setSaveConflict(null);
      setAutosave("saved");
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      const contentToSave = draftRef.current;
      setAutosave("saving");
      try {
        const updated = await saveBrowserNote(active, contentToSave);
        setActive(updated);
        setNotes(await listBrowserNotes());
        setSaveConflict(null);
        setAutosave(draftRef.current === contentToSave ? "saved" : "unsaved");
      } catch {
        setAutosave("unsaved");
        toast("Browser storage could not save this note.", "error");
      }
      return;
    }
    const expectedHash = baseContentHash || active.content_hash;
    if (!expectedHash) {
      toast("Reload this note before saving so BerryBrain can verify its version.", "error");
      setAutosave("conflict");
      return;
    }
    const contentToSave = draftRef.current;
    setAutosave("saving");
    try {
      const r = await apiFetch(`${api}/api/v1/notes/${encode(active.path)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: contentToSave,
          base_content_hash: expectedHash,
        }),
      });
      if (r.ok) {
        const updated = await r.json();
        setActive(updated);
        setSaveConflict(null);
        setAutosave(draftRef.current === contentToSave ? "saved" : "unsaved");
        return;
      }
      if (r.status === 409) {
        const payload = await r.json().catch(() => null);
        const detail = payload?.detail;
        if (detail?.code === "note_content_conflict") {
          setSaveConflict({
            currentContent: String(detail.currentContent || ""),
            currentContentHash: String(detail.currentContentHash || ""),
          });
          setAutosave("conflict");
          toast("Save blocked: this note changed elsewhere. Your draft is preserved.", "error");
          return;
        }
      }
      toast("Failed to save note. Your draft is still available.", "error");
      setAutosave("unsaved");
    } catch {
      toast("The API is unavailable. Your draft is still available.", "error");
      setAutosave("unsaved");
    }
  }

  async function save() {
    await persistDraft();
  }

  async function resolveSaveConflict(strategy: "reload" | "overwrite") {
    if (!active || !saveConflict) return;
    if (strategy === "reload") {
      setActive({
        ...active,
        content: saveConflict.currentContent,
        content_hash: saveConflict.currentContentHash,
      });
      setDraft(saveConflict.currentContent);
      draftRef.current = saveConflict.currentContent;
      setSaveConflict(null);
      setAutosave("saved");
      toast("Latest note version loaded.", "success");
      return;
    }
    await persistDraft(saveConflict.currentContentHash);
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
        setActive(note); setDraft(note.content); draftRef.current = note.content; setSaveConflict(null); setAutosave("saved");
        return true;
      }
      if (BROWSER_STORAGE_MODE) {
        const note = await createBrowserNote(content);
        setNotes(await listBrowserNotes());
        setActive(note);
        setDraft(note.content);
        draftRef.current = note.content;
        setSaveConflict(null);
        setAutosave("saved");
        return true;
      }
      const r = await apiFetch(`${api}/api/v1/notes`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: "inbox", content }),
      });
      if (!r.ok) { toast("Failed to create note.", "error"); return false; }
      const n = await r.json();
      setNotes((prev) => [n, ...prev]);
      setActive(n); setDraft(n.content || content); draftRef.current = n.content || content; setSaveConflict(null); setAutosave("saved");
      return true;
    } catch {
      toast("API unavailable.", "error");
      return false;
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
      setActive(null); setDraft(""); draftRef.current = ""; setSaveConflict(null); toast("Demo note deleted.", "success");
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      await deleteBrowserNote(active.path);
      setNotes(await listBrowserNotes());
      setActive(null);
      setDraft("");
      draftRef.current = "";
      setSaveConflict(null);
      toast("Note removed from this browser.", "success");
      return;
    }
    try {
      const response = await apiFetch(`${api}/api/v1/notes/${encode(active.path)}`, { method: "DELETE" });
      if (!response.ok) {
        toast("Failed to remove note.", "error");
        return;
      }
      setActive(null); setDraft(""); draftRef.current = ""; setSaveConflict(null); toast("Removed.", "success"); await loadAll();
    } catch {
      toast("Failed to remove note.", "error");
    }
  }

  async function scanVault() {
    if (demo) {
      toast("Demo vault is already loaded.", "info");
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      await loadAll();
      toast("Browser workspace refreshed.", "success");
      return;
    }
    const r = await apiFetch(`${api}/api/v1/vault/scan`, { method: "POST" });
    if (r.ok) { await loadAll(); toast("Vault scanned."); }
  }

  async function closeNote() { setActive(null); setDraft(""); draftRef.current = ""; setSaveConflict(null); loadAll(); }

  async function download() {
    if (!active) return;
    const blob = new Blob([draft], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${active.title.replace(/[\\/:*?"<>|]/g, "-")}.md`;
    a.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 0);
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
    if (BROWSER_STORAGE_MODE) {
      try {
        const updated = await renameBrowserNote(active, newTitle);
        setActive(updated);
        setNotes(await listBrowserNotes());
        toast("Renamed.", "success");
      } catch {
        toast("Browser storage could not rename the note.", "error");
      }
      return;
    }
    try {
      const r = await apiFetch(`${api}/api/v1/notes/${encode(active.path)}/rename`, {
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
    draftRef.current = val;
    setAutosave((current) => current === "conflict" ? "conflict" : "unsaved");
    if (val.length > 50 && active && /^(rascunho|nota-sem-titulo)/i.test(active.title) && !renameSent.current) {
      renameSent.current = true;
      aiRename(active.path);
    }
  }, [active]);

  useEffect(() => {
    if (active) renameSent.current = false;
  }, [active]);

  async function aiRename(path: string) {
    if (demo || BROWSER_STORAGE_MODE) return;
    try {
      await apiFetch(`${api}/api/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "GENERATE_NOTE_TITLE", payload: { note_path: path } }),
      });
    } catch {}
  }

  useEffect(() => { loadAll(); }, []);
  useEffect(() => {
    if (demo || BROWSER_STORAGE_MODE) return;
    const iv = setInterval(() => { apiFetch(`${api}/api/v1/jobs?limit=8`).then(r => { if (r.ok) r.json().then(d => setJobs(d.jobs)); }).catch(() => {}); }, 8000);
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
    <C.Provider value={{ api, demo, notes, stats, jobs, active, draft, autosave, viewMode, insights, sidebarWidth, rightOpen, graphOpen, guideOpen, cmdOpen, monitorOpen, settingsOpen, notificationsOpen, creatingDraft, saveConflict, toasts, setDraft: handleDraft, setViewMode, setSidebarWidth, setRightOpen, setCmdOpen, setMonitorOpen, setSettingsOpen, setGraphOpen, setGuideOpen, setNotificationsOpen, openNote, closeNote, save, resolveSaveConflict, download, renameNote, createDraft, deleteActive, scanVault, loadAll, toast }}>
      {children}
      {creatingDraft && (
        <div className="fixed inset-0 z-[100] grid place-items-center bg-background/60 backdrop-blur-sm">
          <div className="bb-card bb-card--elevated flex flex-col items-center gap-3 px-6 py-5">
            <span className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-accent" />
            <span className="text-xs text-muted">Creating note...</span>
          </div>
        </div>
      )}
    </C.Provider>
  );
}
