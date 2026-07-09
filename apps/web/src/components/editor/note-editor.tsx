"use client";

import { useWorkspace } from "@/contexts/workspace-context";
import { MarkdownPreview } from "./markdown-preview";
import { useState, useEffect } from "react";

function Backlinks({ notePath }: { notePath: string }) {
  const w = useWorkspace();
  const [links, setLinks] = useState<any[]>([]);
  useEffect(() => {
    const path = notePath.split("/").map(encodeURIComponent).join("/");
    fetch(`${w.api}/api/v1/connections?note_path=${path}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setLinks(d?.connections || []))
      .catch(() => {});
  }, [notePath, w.api]);
  if (!links.length) return null;
  return (
    <div className="border-t border-border/50 px-6 py-4">
      <h3 className="text-xs font-medium text-muted mb-2">Backlinks</h3>
      <div className="flex flex-wrap gap-2">
        {links.map((c: any, i: number) => (
          <button
            key={i}
            className="rounded-lg bg-surface px-3 py-1.5 text-xs hover:bg-accent/10 transition"
            onClick={() => w.openNote(c.source_note_path || c.note_path)}
          >
            {c.source_note_title || c.note_title}
          </button>
        ))}
      </div>
    </div>
  );
}

export function NoteEditor() {
  const w = useWorkspace();
  const [menuOpen, setMenuOpen] = useState(false);
  if (!w.active) return null;
  const isDirty = w.draft !== w.active.content;

  return (
    <>
      <div className="flex h-12 items-center gap-3 border-b border-border/50 bg-panel px-5 shrink-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface shrink-0" onClick={w.closeNote} aria-label="Voltar">
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <h1 className="truncate text-sm font-medium min-w-0">{w.active.title}</h1>
          <span className={`shrink-0 text-[10px] ${w.autosave === "saving" ? "text-amber-500 animate-pulse-soft" : w.autosave === "unsaved" ? "text-muted/40" : "text-emerald-500"}`}>
            {w.autosave === "saving" ? "salvando" : w.autosave === "unsaved" ? "nao salvo" : "salvo"}
          </span>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          <div className="flex rounded-lg bg-surface p-0.5">
            {(["edit", "preview", "split"] as const).map(m => (
              <button
                key={m}
                className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${w.viewMode === m ? "bg-panel text-foreground shadow-sm" : "text-muted hover:text-foreground"}`}
                onClick={() => w.setViewMode(m)}
              >
                {m === "edit" ? "Editar" : m === "preview" ? "Preview" : "Split"}
              </button>
            ))}
          </div>

          <div className="relative">
            <button className="rounded-lg p-1.5 text-muted hover:bg-surface" onClick={() => setMenuOpen(!menuOpen)} aria-label="Mais acoes">
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01" /></svg>
            </button>
            {menuOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setMenuOpen(false)} />
                <div className="absolute right-0 top-full z-50 mt-1 w-36 rounded-xl bg-panel shadow-lg ring-1 ring-black/10 py-1">
                  <button className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); w.download(); }}>
                    <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                    Download
                  </button>
                  <button className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); w.renameNote(); }}>
                    <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                    Renomear
                  </button>
                  <button className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-500 hover:bg-red-50" onClick={() => { setMenuOpen(false); w.deleteActive(); }}>
                    <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                    Excluir
                  </button>
                </div>
              </>
            )}
          </div>

          <div className="ml-1 pl-1 border-l border-border/50">
            <button className="rounded-lg p-1.5 text-muted hover:bg-surface" onClick={() => w.setRightOpen(!w.rightOpen)} aria-label="Painel">
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
          </div>

          {isDirty && (
            <button className="h-8 rounded-lg bg-accent px-3 text-xs font-medium text-white hover:opacity-90 ml-1" onClick={w.save}>Salvar</button>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 flex">
        {(w.viewMode === "edit" || w.viewMode === "split") && (
          <textarea
            className={`min-h-0 resize-none bg-transparent px-6 py-6 leading-[1.85] outline-none lg:px-10 placeholder:text-muted/20 ${w.viewMode === "split" ? "flex-1 border-r border-border/50" : "flex-1"}`}
            value={w.draft}
            onChange={e => w.setDraft(e.target.value)}
            placeholder="Comece a escrever..."
            spellCheck={false}
            autoFocus
            aria-label="Editor"
            style={{ fontFamily: "var(--font-editor)", fontSize: `${localStorage.getItem("bb_editor_font_size") || "15"}px` }}
          />
        )}
        {(w.viewMode === "preview" || w.viewMode === "split") && (
          <div className={w.viewMode === "split" ? "flex-1" : "flex-1"}>
            <MarkdownPreview content={w.draft} />
          </div>
        )}
      </div>

      <Backlinks notePath={w.active.path} />
    </>
  );
}
