"use client";

import { useEffect, useState } from "react";
import { useWorkspace } from "@/contexts/workspace-context";

export function WorkspaceSidebar() {
  const w = useWorkspace();
  const [attentionCount, setAttentionCount] = useState(0);
  const [dismissedAt, setDismissedAt] = useState<number>(0);

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

  return (
    <aside className="flex-shrink-0 flex flex-col border-r border-border/50 bg-panel overflow-hidden" style={{ width: `${w.sidebarWidth}px` }} aria-label="Navegacao" suppressHydrationWarning>
      <div className="flex items-center justify-center px-4 py-4">
        <img src="/berrylogo.png" alt="BerryBrain" className="size-28 rounded-2xl cursor-pointer hover:opacity-80 transition-opacity" onClick={() => { window.location.href = "/"; }} />
      </div>

      <div className="px-3 pb-2">
        <button className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-muted transition hover:bg-surface hover:text-foreground" onClick={() => w.createDraft()}>
          <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          Nova nota
        </button>
      </div>

      <nav className="min-h-0 flex-1 overflow-y-auto px-3 py-1">
        <SidebarSection title="Hoje">
          <SidebarItem icon="N" label={`Notas (${w.notes.length})`} />
        </SidebarSection>
        <SidebarSection title="Vault">
          {w.notes.slice(0, 20).map(n => (
            <button key={n.path} className={`flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-left text-sm transition-colors ${w.active?.path === n.path ? "bg-accent-soft text-accent font-medium" : "text-muted hover:bg-surface hover:text-foreground"}`} onClick={() => w.openNote(n.path)}>
              <span className="grid size-5 shrink-0 place-items-center rounded text-[10px] font-medium bg-surface text-muted">{n.title[0]?.toUpperCase()}</span>
              <span className="truncate">{n.title}</span>
            </button>
          ))}
          {w.notes.length === 0 && <div className="px-3 py-2 text-xs text-muted/50">Vazio</div>}
        </SidebarSection>
      </nav>

      <div className="border-t border-border/50 px-3 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[10px] text-muted">
          <span className={`inline-block size-1.5 rounded-full ${w.jobs.filter(j => j.status === "pending").length ? "bg-amber-400" : "bg-emerald-400"}`} />
          {w.jobs.filter(j => j.status === "pending").length ? `${w.jobs.filter(j => j.status === "pending").length} pendentes` : "em dia"}
        </div>
        <div className="flex items-center gap-1">
          <button className="rounded-lg p-1 text-muted hover:bg-surface" onClick={() => w.setGuideOpen(true)} aria-label="Guia">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </button>
          <span className="text-[9px] text-muted/50 font-medium select-none px-0.5">v1.0.0</span>
          <button className={`relative rounded-lg p-1 text-muted hover:bg-surface ${attentionCount ? "text-accent" : ""}`} onClick={() => { localStorage.setItem("bb_notif_dismissed_at", String(Date.now())); setDismissedAt(Date.now()); setAttentionCount(0); w.setNotificationsOpen(true); }} aria-label="Notificações">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0a3 3 0 01-6 0" /></svg>
            {attentionCount > 0 && (
              <span className="absolute -right-1 -top-1 grid min-w-3.5 place-items-center rounded-full bg-accent px-1 text-[8px] font-semibold text-white">
                {attentionCount}
              </span>
            )}
          </button>
          <button className="rounded-lg p-1 text-muted hover:bg-surface" onClick={() => w.setSettingsOpen(true)} aria-label="Config">
            <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /></svg>
          </button>
        </div>
      </div>
    </aside>
  );
}

function SidebarSection({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="mb-3"><div className="px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.1em] text-muted/40">{title}</div>{children}</div>;
}

function SidebarItem({ icon, label, onClick }: { icon: string; label: string; onClick?: () => void }) {
  return <button className="flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors text-muted hover:bg-surface hover:text-foreground" onClick={onClick}><span className="grid size-5 shrink-0 place-items-center rounded text-[10px] font-bold bg-surface text-muted">{icon}</span><span>{label}</span></button>;
}
