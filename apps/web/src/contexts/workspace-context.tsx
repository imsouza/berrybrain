"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AutosaveStatus, Insight, JobSummary, NoteDetail, NoteSummary, Stats, Toast } from "@/types";
import { acknowledgeDraft, draftKey, forgetDraft, keepDraft, readDraft } from "@/lib/pending-drafts";
import { readResource } from "@/lib/read-resource";

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
  const activeRef = useRef<NoteDetail | null>(null);
  const savingRef = useRef<Promise<boolean> | null>(null);
  const navigationRef = useRef(0);
  const mutationRef = useRef(false);

  const toast = useCallback((text: string, kind: Toast["kind"] = "info") => {
    const id = ++_tid;
    setToasts(t => [...t, { id, text, kind }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  const loadAll = useCallback(async () => {
    if (demo) return;
    try {
      await Promise.allSettled([
        (async () => {
          let offset: number | null = 0;
          const notes: NoteSummary[] = [];
          while (offset !== null) {
            const page: { notes: NoteSummary[]; nextOffset?: number | null } = await readResource(`${api}/api/v1/notes?limit=200&offset=${offset}`);
            notes.push(...(page.notes || []));
            setNotes([...notes]);
            offset = page.nextOffset ?? null;
          }
        })(),
        readResource(`${api}/api/v1/jobs?limit=8`).then(data => setJobs(data.jobs || [])),
        readResource(`${api}/api/v1/monitor/stats`).then(setStats),
        readResource(`${api}/api/v1/insights?limit=5`).then(data => setInsights(data.insights || [])),
      ]);
    } catch {}
  }, [api, demo]);

  async function openNote(path: string) {
    if (mutationRef.current) return;
    if (demo) {
      toast("Demo mode contains no seeded notes.", "info");
      return;
    }
    const navigation = ++navigationRef.current;
    if (!await persistDraft() || navigation !== navigationRef.current) return;
    const r = await apiFetch(`${api}/api/v1/notes/${encode(path)}`);
    if (!r.ok) { toast("Failed to open note.", "error"); return; }
    const n = await r.json();
    if (navigation !== navigationRef.current) return;
    if (activeRef.current && draftRef.current !== activeRef.current.content) {
      toast("Navigation paused: finish saving your latest edits first.", "info");
      return;
    }
    const key = draftKey(api, readCsrf(), n.path);
    const pending = readDraft(key);
    if (pending && pending.text !== n.content) {
      const restored = { ...n, content: pending.baseContent, content_hash: pending.baseHash };
      activeRef.current = restored;
      setActive(restored); setDraft(pending.text); draftRef.current = pending.text;
      const changed = pending.baseHash !== n.content_hash;
      setSaveConflict(changed ? { currentContent: n.content, currentContentHash: n.content_hash } : null);
      setAutosave(changed ? "conflict" : "unsaved");
      toast("Your pending draft was restored.", "info");
    } else {
      forgetDraft(key);
      activeRef.current = n;
      setActive(n); setDraft(n.content); draftRef.current = n.content;
      setSaveConflict(null); setAutosave("saved");
    }
    setRightOpen(false);
  }

  const persistDraft = useCallback(async (baseContentHash?: string): Promise<boolean> => {
    if (mutationRef.current) return false;
    // Serialize saves, including saves initiated by navigation. A later response
    // must never change the identity associated with the current draft.
    if (savingRef.current) {
      await savingRef.current;
      return !activeRef.current || draftRef.current === activeRef.current.content;
    }
    const note = activeRef.current;
    if (!note || (!baseContentHash && draftRef.current === note.content)) return true;
    if (demo) {
      toast("Demo mode is read-only.", "info");
      return false;
    }
    const expectedHash = baseContentHash || note.content_hash;
    if (!expectedHash) {
      toast("Reload this note before saving so BerryBrain can verify its version.", "error");
      setAutosave("conflict");
      return false;
    }
    const contentToSave = draftRef.current;
    const pendingKey = draftKey(api, readCsrf(), note.path);
    setAutosave("saving");
    const pending = (async () => {
    try {
      const r = await apiFetch(`${api}/api/v1/notes/${encode(note.path)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: contentToSave,
          base_content_hash: expectedHash,
        }),
      });
      if (r.ok) {
        const updated = await r.json();
        acknowledgeDraft(pendingKey, contentToSave, updated.content_hash);
        if (activeRef.current?.path !== note.path) return false;
        activeRef.current = updated;
        setActive(updated);
        setSaveConflict(null);
        setAutosave(draftRef.current === contentToSave ? "saved" : "unsaved");
        return draftRef.current === contentToSave;
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
          return false;
        }
      }
      toast("Failed to save note. Your draft is still available.", "error");
      setAutosave("unsaved");
    } catch {
      toast("The API is unavailable. Your draft is still available.", "error");
      setAutosave("unsaved");
    }
    return false;
    })();
    savingRef.current = pending;
    try { return await pending; }
    finally { if (savingRef.current === pending) savingRef.current = null; }
  }, [api, demo, toast]);

  const save = useCallback(async () => {
    await persistDraft();
  }, [persistDraft]);

  async function resolveSaveConflict(strategy: "reload" | "overwrite") {
    if (!active || !saveConflict) return;
    if (strategy === "reload") {
      if (savingRef.current) await savingRef.current;
      if (activeRef.current?.path !== active.path) return;
      forgetDraft(draftKey(api, readCsrf(), active.path));
      const updated = {
        ...active,
        content: saveConflict.currentContent,
        content_hash: saveConflict.currentContentHash,
      };
      activeRef.current = updated;
      setActive(updated);
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
    if (mutationRef.current) return false;
    const navigation = ++navigationRef.current;
    if (!await persistDraft() || navigation !== navigationRef.current) return false;
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
      if (navigation !== navigationRef.current) return true;
      if (activeRef.current && draftRef.current !== activeRef.current.content) {
        toast("Note created. Your current draft remains open until it is saved.", "info");
        return true;
      }
      activeRef.current = n;
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
    if (mutationRef.current || !active || !confirm(`Delete ${active.path}?`)) return;
    if (demo) {
      toast("Demo mode is read-only.", "info");
      return;
    }
    try {
      const path = active.path;
      mutationRef.current = true;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      ++navigationRef.current;
      if (savingRef.current) await savingRef.current;
      const response = await apiFetch(`${api}/api/v1/notes/${encode(active.path)}`, { method: "DELETE" });
      if (!response.ok) {
        toast("Failed to remove note.", "error");
        return;
      }
      forgetDraft(draftKey(api, readCsrf(), path));
      if (activeRef.current?.path === path) {
        activeRef.current = null;
        setActive(null); setDraft(""); draftRef.current = ""; setSaveConflict(null);
      }
      toast("Removed.", "success"); await loadAll();
    } catch {
      toast("Failed to remove note.", "error");
    } finally {
      mutationRef.current = false;
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
    if (mutationRef.current) return;
    const navigation = ++navigationRef.current;
    if (!await persistDraft() || navigation !== navigationRef.current) return;
    activeRef.current = null;
    setActive(null);
    setDraft("");
    draftRef.current = "";
    setSaveConflict(null);
    loadAll();
  }, [loadAll, persistDraft]);

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
    if (mutationRef.current || !active) return;
    const newTitle = window.prompt("New title:", active.title);
    if (!newTitle || newTitle === active.title) return;
    if (demo) {
      toast("Demo mode is read-only.", "info");
      return;
    }
    try {
      const navigation = ++navigationRef.current;
      if (!await persistDraft() || navigation !== navigationRef.current) return;
      mutationRef.current = true;
      if (saveTimer.current) clearTimeout(saveTimer.current);
      const r = await apiFetch(`${api}/api/v1/notes/${encode(active.path)}/rename`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });
      if (!r.ok) { toast("Failed to rename note.", "error"); return; }
      const updated = await r.json();
      if (navigation === navigationRef.current && activeRef.current?.path === active.path) {
        const renamed = { ...activeRef.current, ...updated };
        forgetDraft(draftKey(api, readCsrf(), active.path));
        keepDraft(draftKey(api, readCsrf(), renamed.path), {
          text: draftRef.current, baseContent: renamed.content, baseHash: renamed.content_hash,
        });
        activeRef.current = renamed;
        setActive(renamed);
      }
      toast("Renamed.", "success");
      loadAll();
    } catch { toast("Failed to rename note.", "error"); }
    finally { mutationRef.current = false; }
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
    const note = activeRef.current;
    if (note) keepDraft(draftKey(api, readCsrf(), note.path), {
      text: val, baseContent: note.content, baseHash: note.content_hash || "",
    });
    setAutosave((current) => current === "conflict" ? "conflict" : "unsaved");
    if (val.length > 50 && active && /^(untitled note|untitled-note)/i.test(active.title) && !renameSent.current) {
      renameSent.current = true;
      aiRename(active.path);
    }
  }, [active, aiRename, api]);

  useEffect(() => {
    if (active) renameSent.current = false;
  }, [active]);

  useEffect(() => { loadAll(); }, [loadAll]);
  useEffect(() => {
    const isDirty = () => !!savingRef.current || (!!activeRef.current && draftRef.current !== activeRef.current.content);
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (!isDirty()) return;
      event.preventDefault();
      event.returnValue = "";
    };
    const beforeLinkNavigation = (event: MouseEvent) => {
      const target = event.target instanceof Element ? event.target.closest("a[href]") : null;
      if (!(target instanceof HTMLAnchorElement) || target.target === "_blank" || target.hasAttribute("download")) return;
      if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || !isDirty()) return;
      const url = new URL(target.href, window.location.href);
      if (!["http:", "https:"].includes(url.protocol) || (url.pathname === window.location.pathname && url.search === window.location.search && url.hash)) return;
      event.preventDefault();
      event.stopPropagation();
      void persistDraft().then(saved => { if (saved) window.location.assign(url.href); });
    };
    window.addEventListener("beforeunload", beforeUnload);
    document.addEventListener("click", beforeLinkNavigation, true);
    return () => {
      window.removeEventListener("beforeunload", beforeUnload);
      document.removeEventListener("click", beforeLinkNavigation, true);
    };
  }, [persistDraft]);
  useEffect(() => {
    if (demo) return;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      if (!document.hidden) {
        try {
          const data = await readResource<{ jobs: JobSummary[] }>(`${api}/api/v1/jobs?limit=8`);
          if (!stopped) setJobs(data.jobs);
        } catch { /* Keep the last known state; Monitor exposes read errors. */ }
      }
      if (!stopped) timer = setTimeout(poll, 15_000);
    };
    timer = setTimeout(poll, 15_000);
    return () => { stopped = true; clearTimeout(timer); };
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
