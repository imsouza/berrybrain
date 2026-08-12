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

type Ctx = {
  api: string;
  demo: boolean;
  notes: NoteSummary[]; stats: Stats | null; jobs: JobSummary[];
  active: NoteDetail | null; draft: string; autosave: AutosaveStatus; viewMode: "edit" | "preview" | "split";
  insights: Insight[];
  sidebarWidth: number; rightOpen: boolean;
  cmdOpen: boolean; monitorOpen: boolean; settingsOpen: boolean; graphOpen: boolean; askRequested: boolean; askQuery: string; guideOpen: boolean; notificationsOpen: boolean;
  creatingDraft: boolean;
  saveConflict: { currentContent: string; currentContentHash: string } | null;
  toasts: Toast[];
  setDraft: (v: string) => void; setViewMode: (v: "edit" | "preview" | "split") => void;
  setSidebarWidth: (w: number) => void; setRightOpen: (v: boolean) => void;
  setCmdOpen: (v: boolean) => void; setMonitorOpen: (v: boolean) => void; setSettingsOpen: (v: boolean) => void; setGraphOpen: (v: boolean) => void; openAsk: (query?: string) => void; consumeAskRequest: () => void; setGuideOpen: (v: boolean) => void; setNotificationsOpen: (v: boolean) => void;
  openNote: (p: string) => Promise<void>; closeNote: () => void; save: () => Promise<void>; download: () => void; renameNote: () => Promise<void>;
  resolveSaveConflict: (strategy: "reload" | "overwrite") => Promise<void>;
  createDraft: (content?: string) => Promise<boolean>; deleteActive: () => Promise<void>; scanVault: () => Promise<void>;
  loadAll: () => Promise<void>; toast: (t: string, k?: Toast["kind"]) => void;
};

const C = createContext<Ctx>(null!);
export function useWorkspace() { return useContext(C); }

export function WorkspaceProvider({ children, demo = false }: { children: ReactNode; demo?: boolean }) {
  const api = useMemo(() => demo ? "__demo__" : getApiUrl(), [demo]);
  const [notes, setNotes] = useState<NoteSummary[]>([]);
  const [active, setActive] = useState<NoteDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [jobs, setJobs] = useState<JobSummary[]>([]);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [sidebarWidth, setSidebarWidth] = useState(() => typeof window === "undefined" ? 280 : Number(localStorage.getItem("bb_sidebar_w") || 280));
  const [rightOpen, setRightOpen] = useState(false);
  const [autosave, setAutosave] = useState<AutosaveStatus>("saved");
  const [viewMode, setViewMode] = useState<"edit" | "preview" | "split">("edit");
  const [cmdOpen, setCmdOpen] = useState(false);
  const [monitorOpen, setMonitorOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [graphOpen, setGraphOpen] = useState(false);
  const [askRequested, setAskRequested] = useState(false);
  const [askQuery, setAskQuery] = useState("");
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

  const loadAll = useCallback(async () => {
    if (demo) return;
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
  }, [api, demo]);

  async function openNote(path: string) {
    if (demo) {
      toast("Demo mode contains no seeded notes.", "info");
      return;
    }
    const r = await apiFetch(`${api}/api/v1/notes/${encode(path)}`);
    if (!r.ok) { toast("Failed to open note.", "error"); return; }
    const n = await r.json();
    setActive(n); setDraft(n.content); draftRef.current = n.content; setSaveConflict(null); setRightOpen(false); setAutosave("saved");
  }

  const persistDraft = useCallback(async (baseContentHash?: string) => {
    if (!active) return;
    if (demo) {
      toast("Demo mode is read-only.", "info");
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
  }, [active, api, demo, toast]);

  const save = useCallback(async () => {
    await persistDraft();
  }, [persistDraft]);

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
        toast("Demo mode is read-only and contains no seeded data.", "info");
        return false;
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
      toast("Demo mode is read-only.", "info");
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
      toast("Demo mode contains no seeded vault data.", "info");
      return;
    }
    let r = await apiFetch(`${api}/api/v1/vault/scan-and-rebuild`, { method: "POST" });
    if (!r.ok) {
      r = await apiFetch(`${api}/api/v1/vault/scan`, { method: "POST" });
    }
    if (r.ok) { await loadAll(); toast("Vault scanned and graph refreshed."); }
  }

  const closeNote = useCallback(async () => {
    setActive(null);
    setDraft("");
    draftRef.current = "";
    setSaveConflict(null);
    loadAll();
  }, [loadAll]);

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
      toast("Demo mode is read-only.", "info");
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
  const aiRename = useCallback(async (path: string) => {
    if (demo) return;
    try {
      await apiFetch(`${api}/api/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "GENERATE_NOTE_TITLE", payload: { note_path: path } }),
      });
    } catch {}
  }, [api, demo]);

  const handleDraft = useCallback((val: string) => {
    setDraft(val);
    draftRef.current = val;
    setAutosave((current) => current === "conflict" ? "conflict" : "unsaved");
    if (val.length > 50 && active && /^(untitled note|untitled-note)/i.test(active.title) && !renameSent.current) {
      renameSent.current = true;
      aiRename(active.path);
    }
  }, [active, aiRename]);

  useEffect(() => {
    if (active) renameSent.current = false;
  }, [active]);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => {
    if (demo) return;
    const iv = setInterval(() => { apiFetch(`${api}/api/v1/jobs?limit=8`).then(r => { if (r.ok) r.json().then(d => setJobs(d.jobs)); }).catch(() => {}); }, 8000);
    return () => clearInterval(iv);
  }, [api, demo]);
  useEffect(() => {
    if (!active || autosave !== "unsaved") return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(save, 3000);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [active, autosave, draft, save]);
  useEffect(() => {
    function h(e: KeyboardEvent) {
      const key = e.key.toLowerCase();
      if ((e.metaKey || e.ctrlKey) && key === "k") { e.preventDefault(); setCmdOpen(o => !o); return; }
      if ((e.metaKey || e.ctrlKey) && key === "s") { e.preventDefault(); save(); return; }
      if (e.key === "Escape") { if (active) closeNote(); if (cmdOpen) setCmdOpen(false); }
    }
    window.addEventListener("keydown", h); return () => window.removeEventListener("keydown", h);
  }, [active, closeNote, cmdOpen, save]);

  return (
    <C.Provider value={{ api, demo, notes, stats, jobs, active, draft, autosave, viewMode, insights, sidebarWidth, rightOpen, graphOpen, askRequested, askQuery, guideOpen, cmdOpen, monitorOpen, settingsOpen, notificationsOpen, creatingDraft, saveConflict, toasts, setDraft: handleDraft, setViewMode, setSidebarWidth, setRightOpen, setCmdOpen, setMonitorOpen, setSettingsOpen, setGraphOpen, openAsk: (query = "") => { setAskQuery(query.trim()); setAskRequested(true); setGraphOpen(true); }, consumeAskRequest: () => { setAskRequested(false); setAskQuery(""); }, setGuideOpen, setNotificationsOpen, openNote, closeNote, save, resolveSaveConflict, download, renameNote, createDraft, deleteActive, scanVault, loadAll, toast }}>
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
