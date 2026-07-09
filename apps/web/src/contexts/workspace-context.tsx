"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { AutosaveStatus, Insight, JobSummary, NoteDetail, NoteSummary, Stats, Toast } from "@/types";

export function getApiUrl() {
  if (typeof window === "undefined") return "http://192.168.3.36:8000";
  const host = window.location.hostname;
  if (host === "localhost" || host === "127.0.0.1") return "http://localhost:8000";
  return `http://${host}:8000`;
}
function encode(path: string) { return path.split("/").map(encodeURIComponent).join("/"); }
let _tid = 0;

type Ctx = {
  api: string;
  notes: NoteSummary[]; stats: Stats | null; jobs: JobSummary[];
  active: NoteDetail | null; draft: string; autosave: AutosaveStatus; viewMode: "edit" | "preview" | "split";
  insights: Insight[];
  sidebarWidth: number; rightOpen: boolean;
  cmdOpen: boolean; monitorOpen: boolean; settingsOpen: boolean; graphOpen: boolean; guideOpen: boolean; notificationsOpen: boolean;
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

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const api = useMemo(() => getApiUrl(), []);
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
  const [guideOpen, setGuideOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const toast = useCallback((text: string, kind: Toast["kind"] = "info") => {
    const id = ++_tid;
    setToasts(t => [...t, { id, text, kind }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 4000);
  }, []);

  async function loadAll() {
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
    const r = await fetch(`${api}/api/v1/notes/${encode(path)}`);
    if (!r.ok) { toast("Erro ao abrir.", "error"); return; }
    const n = await r.json();
    setActive(n); setDraft(n.content); setRightOpen(false); setAutosave("saved");
  }

  async function save() {
    if (!active) return;
    setAutosave("saving");
    const r = await fetch(`${api}/api/v1/notes/${encode(active.path)}`, {
      method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content: draft }),
    });
    if (r.ok) { setActive(await r.json()); setAutosave("saved"); }
    else { toast("Erro ao salvar.", "error"); setAutosave("unsaved"); }
  }

  async function createDraft(content = "") {
    try {
      const r = await fetch(`${api}/api/v1/notes`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder: "inbox", content }),
      });
      if (!r.ok) { toast("Erro ao criar nota.", "error"); return; }
      const n = await r.json();
      setNotes((prev) => [n, ...prev]);
      setActive(n); setDraft(n.content || content); setAutosave("saved");
    } catch {
      toast("API indisponivel.", "error");
    }
  }

  async function deleteActive() {
    if (!active || !confirm(`Excluir ${active.path}?`)) return;
    await fetch(`${api}/api/v1/notes/${encode(active.path)}`, { method: "DELETE" });
    setActive(null); setDraft(""); toast("Excluida.", "success"); await loadAll();
  }

  async function scanVault() {
    const r = await fetch(`${api}/api/v1/vault/scan`, { method: "POST" });
    if (r.ok) { await loadAll(); toast("Vault escaneado."); }
  }

  async function closeNote() { setActive(null); setDraft(""); loadAll(); }

  async function download() {
    if (!active) return;
    const a = document.createElement("a");
    a.href = `${api}/api/v1/notes/${encode(active.path)}/download`;
    a.download = `${active.title}.md`;
    a.click();
  }

  async function renameNote() {
    if (!active) return;
    const newTitle = window.prompt("Novo titulo:", active.title);
    if (!newTitle || newTitle === active.title) return;
    try {
      const r = await fetch(`${api}/api/v1/notes/${encode(active.path)}/rename`, {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle }),
      });
      if (!r.ok) { toast("Erro ao renomear.", "error"); return; }
      const updated = await r.json();
      setActive({ ...active, title: updated.title, path: updated.path });
      toast("Renomeado.", "success");
      loadAll();
    } catch { toast("Erro ao renomear.", "error"); }
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
    try {
      await fetch(`${api}/api/v1/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: "GENERATE_NOTE_TITLE", payload: { note_path: path } }),
      });
    } catch {}
  }

  useEffect(() => { loadAll(); }, []);
  useEffect(() => { const iv = setInterval(() => { fetch(`${api}/api/v1/jobs?limit=8`).then(r => { if (r.ok) r.json().then(d => setJobs(d.jobs)); }).catch(() => {}); }, 8000); return () => clearInterval(iv); }, []);
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
    <C.Provider value={{ api, notes, stats, jobs, active, draft, autosave, viewMode, insights, sidebarWidth, rightOpen, graphOpen, guideOpen, cmdOpen, monitorOpen, settingsOpen, notificationsOpen, toasts, setDraft: handleDraft, setViewMode, setSidebarWidth, setRightOpen, setCmdOpen, setMonitorOpen, setSettingsOpen, setGraphOpen, setGuideOpen, setNotificationsOpen, openNote, closeNote, save, download, renameNote, createDraft, deleteActive, scanVault, loadAll, toast }}>
      {children}
    </C.Provider>
  );
}
