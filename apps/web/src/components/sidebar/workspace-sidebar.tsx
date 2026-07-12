"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import berrylogo from "../../../public/berrylogo.png";
import { useWorkspace, appPath } from "@/contexts/workspace-context";
import { AccountMenu } from "@/components/sidebar/account-menu";
import { t } from "@/i18n";

type FolderInfo = {
  name: string;
  path: string;
  parent_path?: string;
  depth?: number;
  note_count?: number;
  total_note_count?: number;
  has_subfolders?: boolean;
};
function encodeFolder(path: string) { return path.split("/").map(encodeURIComponent).join("/"); }

type WorkspaceSidebarProps = {
  mobileOpen?: boolean;
  onMobileClose?: () => void;
};

export function WorkspaceSidebar({ mobileOpen = false, onMobileClose }: WorkspaceSidebarProps = {}) {
  const w = useWorkspace();
  const pathname = usePathname();
  const isDemo = pathname.startsWith("/demo");
  const [attentionCount, setAttentionCount] = useState(0);
  const router = useRouter();
  const [dismissedAt, setDismissedAt] = useState<number>(0);
  const [folders, setFolders] = useState<FolderInfo[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const stored = localStorage.getItem("bb_notif_dismissed_at");
    if (stored) setDismissedAt(parseInt(stored, 10) || 0);
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadAttention() {
      try {
        const response = await fetch(`${w.api}/api/v1/home/summary`);
        if (!response.ok) return;
        const payload = await response.json();
        if (!cancelled) {
          const now = Date.now();
          const count = (payload.needsAttention || []).length;
          setAttentionCount(dismissedAt > now - 60000 ? 0 : count);
        }
      } catch {
        if (!cancelled) setAttentionCount(0);
      }
    }
    loadAttention();
    const timer = setInterval(loadAttention, 30000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [w.api, dismissedAt]);

  async function loadFolders() {
    try {
      const response = await fetch(`${w.api}/api/v1/folders`);
      if (!response.ok) return;
      const payload = await response.json();
      setFolders(payload.folders || []);
    } catch {}
  }

  useEffect(() => {
    loadFolders();
  }, [w.api, w.notes.length]);

  const notesByFolder = useMemo(() => {
    const map = new Map<string, typeof w.notes>();
    for (const note of w.notes) {
      const folder = note.folder || note.path.split("/").slice(0, -1).join("/") || "inbox";
      map.set(folder, [...(map.get(folder) || []), note]);
    }
    return map;
  }, [w.notes]);

  const visibleFolders = useMemo(() => {
    const merged = new Map<string, FolderInfo>();
    for (const folder of folders) merged.set(folder.path, folder);
    for (const folder of notesByFolder.keys()) {
      if (!merged.has(folder)) merged.set(folder, { name: folder.split("/").pop() || folder, path: folder });
    }
    return [...merged.values()].sort((a, b) => a.path.localeCompare(b.path));
  }, [folders, notesByFolder]);

  async function createFolder(parentPath = "") {
    const name = window.prompt(parentPath ? `New folder inside ${parentPath}:` : "Folder name:");
    if (!name?.trim()) return;
    const response = await fetch(`${w.api}/api/v1/folders`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim(), parent_path: parentPath }),
    });
    if (!response.ok) {
      w.toast("Failed to create folder.", "error");
      return;
    }
    w.toast("Folder created.", "success");
    await loadFolders();
  }

  async function renameFolder(path: string, currentName: string) {
    const name = window.prompt("New folder name:", currentName);
    if (!name?.trim() || name.trim() === currentName) return;
    const response = await fetch(`${w.api}/api/v1/folders/${encodeFolder(path)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name.trim() }),
    });
    if (!response.ok) {
      w.toast("Failed to rename folder.", "error");
      return;
    }
    w.toast("Folder renamed.", "success");
    await loadFolders();
    await w.loadAll();
  }

  async function deleteFolder(path: string) {
    if (!window.confirm(`Delete empty folder "${path}"?`)) return;
    const response = await fetch(`${w.api}/api/v1/folders/${encodeFolder(path)}`, { method: "DELETE" });
    if (!response.ok) {
      w.toast("Only empty folders can be deleted.", "error");
      return;
    }
    w.toast("Folder deleted.", "success");
    await loadFolders();
  }

  function folderIsVisible(path: string) {
    const parts = path.split("/");
    for (let i = 1; i < parts.length; i += 1) {
      const ancestor = parts.slice(0, i).join("/");
      if (expanded[ancestor] === false) return false;
    }
    return true;
  }

  return (
    <>
    <div
      className={`fixed inset-0 z-40 bg-black/35 backdrop-blur-[1px] transition-opacity lg:hidden ${mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"}`}
      onClick={onMobileClose}
      aria-hidden="true"
    />
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex flex-col overflow-hidden border-r border-border/50 bg-panel shadow-xl transition-transform duration-200 lg:static lg:z-auto lg:flex-shrink-0 lg:translate-x-0 lg:shadow-none ${mobileOpen ? "translate-x-0" : "-translate-x-full"}`}
      style={{ width: mobileOpen ? "min(86vw, 22rem)" : `${w.sidebarWidth}px` }}
      aria-label="Navigation"
      suppressHydrationWarning
    >
      <div className="flex items-center justify-center px-4 py-4">
        <img src={berrylogo.src} alt="BerryBrain" className="size-28 rounded-2xl cursor-pointer hover:opacity-80 transition-opacity" onClick={() => { onMobileClose?.(); window.location.href = appPath("/brain"); }} />
      </div>
      <div className="pb-1 text-center text-[9px] font-medium text-muted/50 select-none">v1.0.0</div>

      <div className="px-3 pb-2">
        <button className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-surface hover:text-foreground" onClick={() => { onMobileClose?.(); w.createDraft(); }}>
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          {t("newNote")}
        </button>
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto px-3 py-1">
        <div className="mb-3">
          <div className="flex items-center justify-between px-3 py-1">
            <div className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted/40">{t("vault")}</div>
            <button className="rounded px-1.5 text-[11px] text-muted hover:bg-surface hover:text-foreground" onClick={() => createFolder()} title="Create folder">+</button>
          </div>
          {visibleFolders.filter(folder => folderIsVisible(folder.path)).map(folder => {
            const folderNotes = notesByFolder.get(folder.path) || [];
            const isOpen = expanded[folder.path] ?? true;
            const depth = folder.depth ?? Math.max(0, folder.path.split("/").length - 1);
            const canToggle = folder.has_subfolders || folderNotes.length > 0;
            return (
              <div key={folder.path} className="mb-1">
                <div className="group flex items-center gap-1 rounded-lg py-1 pr-2 text-xs text-muted hover:bg-surface/70" style={{ paddingLeft: `${8 + depth * 14}px` }}>
                  <button className="grid size-5 place-items-center" onClick={() => canToggle && setExpanded((current) => ({ ...current, [folder.path]: !isOpen }))} aria-label={isOpen ? "Collapse folder" : "Expand folder"}>
                    {canToggle ? (isOpen ? "▾" : "▸") : "·"}
                  </button>
                  <button className="min-w-0 flex-1 truncate text-left font-medium" onClick={() => setExpanded((current) => ({ ...current, [folder.path]: !isOpen }))}>
                    <span className="truncate" title={folder.path}>{folder.name}</span>
                  </button>
                  <span className="text-[10px] text-muted/45" title={`${folder.total_note_count ?? folderNotes.length} total notes`}>
                    {folder.note_count ?? folderNotes.length}
                  </span>
                  <button className="hidden rounded px-1 text-[10px] text-muted/60 hover:text-foreground group-hover:inline" onClick={() => createFolder(folder.path)} title="Create subfolder">+</button>
                  <button className="hidden rounded px-1 text-[10px] text-muted/60 hover:text-foreground group-hover:inline" onClick={() => renameFolder(folder.path, folder.name)}>Rename</button>
                  <button className="hidden rounded px-1 text-[10px] text-muted/60 hover:text-danger group-hover:inline" onClick={() => deleteFolder(folder.path)}>Delete</button>
                </div>
                {isOpen && (
                  <div style={{ marginLeft: `${22 + depth * 14}px` }}>
                    {folderNotes.map(n => (
                      <button key={n.path} className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ${w.active?.path === n.path ? "bg-accent-soft text-accent font-medium" : "text-muted hover:bg-surface hover:text-foreground"}`} onClick={() => { onMobileClose?.(); w.setGraphOpen(false); w.openNote(n.path); }}>
                        <span className="grid size-5 shrink-0 place-items-center rounded text-[10px] font-medium bg-surface text-muted">{n.title[0]?.toUpperCase()}</span>
                        <span className="truncate">{n.title}</span>
                      </button>
                    ))}
                    {folderNotes.length === 0 && <div className="px-2 py-1.5 text-[11px] text-muted/40">Empty folder</div>}
                  </div>
                )}
              </div>
            );
          })}
          {visibleFolders.length === 0 && <div className="px-3 py-2 text-xs text-muted/50">{t("empty")}</div>}
        </div>
      </nav>

      <div className="border-t border-border/50 px-3 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[10px] text-muted">
          <span className={`inline-block size-1.5 rounded-full ${w.jobs.filter(j => j.status === "pending").length ? "bg-amber-400" : "bg-emerald-400"}`} />
          {w.jobs.filter(j => j.status === "pending").length ? `${w.jobs.filter(j => j.status === "pending").length} ${t("pending")}` : t("saved")}
        </div>
          <div className="flex items-center gap-1">
          {isDemo ? (
            <>
              <span className="text-[9px] text-muted/50 select-none px-1">Demo</span>
              <button className="rounded-lg bg-accent px-2 py-1 text-[10px] font-medium text-white transition hover:opacity-90" onClick={() => { onMobileClose?.(); window.location.href = appPath("/login"); }} aria-label="Login">
                Login
              </button>
              <button className="rounded-lg bg-foreground px-2 py-1 text-[10px] font-medium text-background transition hover:opacity-90" onClick={() => { onMobileClose?.(); window.location.href = appPath("/signup"); }} aria-label="Create account">
                Create account
              </button>
            </>
          ) : (
            <AccountMenu />
          )}
          <button className="rounded-lg p-1 text-muted hover:bg-surface" onClick={() => { onMobileClose?.(); w.setGuideOpen(true); }} aria-label="Guide" title="Guide">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.25 9a3.75 3.75 0 117.05 1.79c-.89.52-1.55 1.16-1.55 2.21m-1.5 3.75h.01M12 21a9 9 0 100-18 9 9 0 000 18z" /></svg>
          </button>
          <button className={`relative rounded-lg p-1 text-muted hover:bg-surface ${attentionCount ? "text-accent" : ""}`} onClick={() => { onMobileClose?.(); localStorage.setItem("bb_notif_dismissed_at", String(Date.now())); setDismissedAt(Date.now()); setAttentionCount(0); w.setNotificationsOpen(true); }} aria-label="Notifications">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0a3 3 0 01-6 0" /></svg>
            {attentionCount > 0 && (
              <span className="absolute -right-1 -top-1 grid min-w-3.5 place-items-center rounded-full bg-white px-1 text-[8px] font-semibold text-[#CC4168] shadow-sm">
                {attentionCount}
              </span>
            )}
          </button>
          <button className="rounded-lg p-1 text-muted hover:bg-surface" onClick={() => { onMobileClose?.(); w.setSettingsOpen(true); }} aria-label="Settings">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
        </div>
      </div>
    </aside>
    </>
  );
}
