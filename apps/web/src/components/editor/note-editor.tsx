"use client";

import { useWorkspace } from "@/contexts/workspace-context";
import { MarkdownPreview } from "./markdown-preview";
import { useState, useEffect, useRef, type KeyboardEvent } from "react";
import { createPortal } from "react-dom";
import { t } from "@/i18n";
import {
  BROWSER_STORAGE_MODE,
  createBrowserAttachment,
  deleteBrowserAttachment,
  listBrowserAttachments,
} from "@/lib/browser-storage";

type AttachmentItem = {
  id: number;
  filename: string;
  mimeType: string;
  category: "image" | "video" | "audio" | "other";
  sizeBytes: number;
  downloadUrl: string;
  createdAt?: string;
  extraction?: { status?: string; extractor?: string; confidence?: number };
};

type NotePipelineProgress = {
  notePath: string;
  completed: number;
  total: number;
  percent: number;
  state: "waiting" | "processing" | "completed" | "degraded" | "failed";
  currentStep?: string | null;
  errors?: { jobId: number; message: string; impact: string; action: string }[];
};

function Backlinks({ notePath }: { notePath: string }) {
  const w = useWorkspace();
  const [links, setLinks] = useState<any[]>([]);
  useEffect(() => {
    if (w.demo || BROWSER_STORAGE_MODE) {
      setLinks([]);
      return;
    }
    const path = notePath.split("/").map(encodeURIComponent).join("/");
    fetch(`${w.api}/api/v1/connections?note_path=${path}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => setLinks(d?.connections || []))
      .catch(() => {});
  }, [notePath, w.api, w.demo]);
  if (!links.length) return null;
  return (
    <div className="border-t border-border/50 px-6 py-4">
      <h3 className="text-xs font-medium text-muted mb-2">{t("backlinks")}</h3>
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
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [attachmentStatus, setAttachmentStatus] = useState("");
  const [pipelineProgress, setPipelineProgress] = useState<NotePipelineProgress | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!w.active || w.demo) {
      setAttachments([]);
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      let objectUrls: string[] = [];
      listBrowserAttachments(w.active.path)
        .then((items) => {
          objectUrls = items.map((item) => item.downloadUrl);
          setAttachments(items);
        })
        .catch(() => setAttachments([]));
      return () => objectUrls.forEach((url) => URL.revokeObjectURL(url));
    }
    const encodedPath = encodeNotePath(w.active.path);
    fetch(`${w.api}/api/v1/notes/${encodedPath}/attachments`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setAttachments(data?.attachments || []))
      .catch(() => setAttachments([]));
  }, [w.active?.path, w.api, w.demo]);

  useEffect(() => {
    setMenuOpen(false);
  }, [w.active?.path]);

  useEffect(() => {
    if (!menuOpen) return;
    const closeOnEscape = (event: globalThis.KeyboardEvent) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    const closeMenu = () => setMenuOpen(false);
    window.addEventListener("keydown", closeOnEscape);
    window.addEventListener("resize", closeMenu);
    window.addEventListener("scroll", closeMenu, true);
    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      window.removeEventListener("resize", closeMenu);
      window.removeEventListener("scroll", closeMenu, true);
    };
  }, [menuOpen]);

  useEffect(() => {
    if (!w.active || w.demo || BROWSER_STORAGE_MODE) {
      setPipelineProgress(null);
      return;
    }
    let cancelled = false;
    const notePath = w.active.path;
    const load = () => {
      fetch(`${w.api}/api/v1/jobs/pipeline-progress`)
        .then((response) => (response.ok ? response.json() : null))
        .then((payload) => {
          if (cancelled) return;
          const progress = (payload?.notes || []).find((item: NotePipelineProgress) => item.notePath === notePath);
          setPipelineProgress(progress || null);
        })
        .catch(() => {
          if (!cancelled) setPipelineProgress(null);
        });
    };
    load();
    const interval = window.setInterval(load, 5000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [w.active?.path, w.api, w.demo]);

  if (!w.active) return null;
  const isDirty = w.draft !== w.active.content;

  function toggleNoteMenu() {
    if (menuOpen) {
      setMenuOpen(false);
      return;
    }
    const rect = menuButtonRef.current?.getBoundingClientRect();
    if (!rect) return;
    const width = 176;
    setMenuPosition({
      top: rect.bottom + 6,
      left: Math.max(8, Math.min(rect.right - width, window.innerWidth - width - 8)),
    });
    setMenuOpen(true);
  }

  function replaceSelection(nextText: string, selectStart?: number, selectEnd?: number) {
    w.setDraft(nextText);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      if (selectStart !== undefined && selectEnd !== undefined) {
        el.setSelectionRange(selectStart, selectEnd);
      }
    });
  }

  function wrapSelection(prefix: string, suffix = prefix, placeholder = "text") {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? w.draft.length;
    const end = el?.selectionEnd ?? w.draft.length;
    const selected = w.draft.slice(start, end) || placeholder;
    const insert = `${prefix}${selected}${suffix}`;
    replaceSelection(
      `${w.draft.slice(0, start)}${insert}${w.draft.slice(end)}`,
      start + prefix.length,
      start + prefix.length + selected.length,
    );
  }

  function toggleMarker(marker: string) {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? w.draft.length;
    const end = el?.selectionEnd ?? w.draft.length;
    const selected = w.draft.slice(start, end);

    if (selected.startsWith(marker) && selected.endsWith(marker) && selected.length >= marker.length * 2) {
      const unwrapped = selected.slice(marker.length, -marker.length);
      const next = `${w.draft.slice(0, start)}${unwrapped}${w.draft.slice(end)}`;
      replaceSelection(next, start, start + unwrapped.length);
      return;
    }

    if (
      start >= marker.length &&
      w.draft.slice(start - marker.length, start) === marker &&
      w.draft.slice(end, end + marker.length) === marker
    ) {
      const next = `${w.draft.slice(0, start - marker.length)}${w.draft.slice(start, end)}${w.draft.slice(end + marker.length)}`;
      replaceSelection(next, start - marker.length, end - marker.length);
      return;
    }

    const before = w.draft.lastIndexOf(marker, Math.max(0, start - 1));
    const after = w.draft.indexOf(marker, end);
    if (start === end && before >= 0 && after > before) {
      const next = `${w.draft.slice(0, before)}${w.draft.slice(before + marker.length, after)}${w.draft.slice(after + marker.length)}`;
      const cursor = Math.max(before, start - marker.length);
      replaceSelection(next, cursor, cursor);
      return;
    }

    wrapSelection(marker, marker, "bold text");
  }

  function insertBlock(block: string) {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? w.draft.length;
    const prefix = start > 0 && !w.draft.slice(0, start).endsWith("\n") ? "\n" : "";
    const insert = `${prefix}${block}`;
    replaceSelection(`${w.draft.slice(0, start)}${insert}${w.draft.slice(el?.selectionEnd ?? start)}`, start + insert.length, start + insert.length);
  }

  function insertAttachmentMarkdown(attachment: AttachmentItem) {
    const url = BROWSER_STORAGE_MODE
      ? `berrybrain-attachment:${attachment.id}`
      : `${w.api}${attachment.downloadUrl}`;
    const name = attachment.filename.replace(/]/g, "");
    if (attachment.category === "image") {
      insertBlock(`![${name}](${url})\n`);
    } else if (attachment.category === "audio") {
      insertBlock(`<audio controls src="${url}"></audio>\n`);
    } else if (attachment.category === "video") {
      insertBlock(`<video controls src="${url}"></video>\n`);
    } else {
      insertBlock(`[${name}](${url})\n`);
    }
  }

  async function fileToBase64(file: File): Promise<string> {
    const dataUrl = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(file);
    });
    return dataUrl.split(",")[1] || "";
  }

  async function uploadFiles(files: FileList | null) {
    if (!files?.length || !w.active) return;
    if (w.demo) {
      setAttachmentStatus("Attachments are disabled in demo mode.");
      return;
    }
    if (BROWSER_STORAGE_MODE) {
      setAttachmentStatus(`Saving ${files.length} attachment${files.length > 1 ? "s" : ""} locally...`);
      const uploaded: AttachmentItem[] = [];
      try {
        for (const file of Array.from(files)) {
          uploaded.push(await createBrowserAttachment(w.active.path, file));
        }
        setAttachments((current) => [...uploaded, ...current]);
        setAttachmentStatus(`${uploaded.length} attachment${uploaded.length > 1 ? "s" : ""} saved in this browser.`);
      } catch (error) {
        uploaded.forEach((item) => URL.revokeObjectURL(item.downloadUrl));
        setAttachmentStatus(error instanceof Error ? error.message : "Attachment storage failed.");
      } finally {
        if (fileInputRef.current) fileInputRef.current.value = "";
        window.setTimeout(() => setAttachmentStatus(""), 4000);
      }
      return;
    }
    setAttachmentStatus(`Uploading ${files.length} attachment${files.length > 1 ? "s" : ""}...`);
    const encodedPath = encodeNotePath(w.active.path);
    const uploaded: AttachmentItem[] = [];
    try {
      for (const file of Array.from(files)) {
        const contentBase64 = await fileToBase64(file);
        const response = await fetch(`${w.api}/api/v1/notes/${encodedPath}/attachments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filename: file.name,
            mime_type: file.type || "application/octet-stream",
            size_bytes: file.size,
            content_base64: contentBase64,
          }),
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.detail || `Upload failed for ${file.name}`);
        }
        if (payload.attachment) uploaded.push(payload.attachment);
      }
      setAttachments((current) => [...uploaded, ...current]);
      uploaded.forEach(insertAttachmentMarkdown);
      setAttachmentStatus(`${uploaded.length} attachment${uploaded.length > 1 ? "s" : ""} uploaded.`);
    } catch (error: any) {
      setAttachmentStatus(error.message || "Attachment upload failed.");
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
      window.setTimeout(() => setAttachmentStatus(""), 4000);
    }
  }

  async function deleteAttachment(id: number) {
    if (w.demo) return;
    if (BROWSER_STORAGE_MODE) {
      const target = attachments.find((item) => item.id === id);
      await deleteBrowserAttachment(id);
      if (target) URL.revokeObjectURL(target.downloadUrl);
      setAttachments((current) => current.filter((item) => item.id !== id));
      return;
    }
    const response = await fetch(`${w.api}/api/v1/notes/attachments/${id}`, { method: "DELETE" });
    if (response.ok) setAttachments((current) => current.filter((item) => item.id !== id));
  }

  async function reprocessAttachment(id: number, extractor: string) {
    if (w.demo) return;
    if (BROWSER_STORAGE_MODE) {
      setAttachmentStatus("OCR and transcription require the self-hosted worker.");
      window.setTimeout(() => setAttachmentStatus(""), 4000);
      return;
    }
    setAttachmentStatus("Queueing attachment reprocessing...");
    const response = await fetch(`${w.api}/api/v1/notes/attachments/${id}/reprocess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ extractor }),
    });
    const payload = await response.json().catch(() => ({}));
    setAttachmentStatus(response.ok ? `Reprocessing queued with ${extractor}.` : payload.detail || "Could not reprocess attachment.");
    window.setTimeout(() => setAttachmentStatus(""), 4000);
  }

  function prefixLines(prefix: string, numbered = false) {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? w.draft.length;
    const end = el?.selectionEnd ?? w.draft.length;
    const lineStart = w.draft.lastIndexOf("\n", Math.max(0, start - 1)) + 1;
    const selected = w.draft.slice(lineStart, end) || "List item";
    const lines = selected.split("\n").map((line, index) => `${numbered ? `${index + 1}. ` : prefix}${line}`);
    const insert = lines.join("\n");
    replaceSelection(`${w.draft.slice(0, lineStart)}${insert}${w.draft.slice(end)}`, lineStart, lineStart + insert.length);
  }

  function onEditorKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) return;
    const key = event.key.toLowerCase();
    if (key === "b") {
      event.preventDefault();
      toggleMarker("**");
    } else if (key === "i") {
      event.preventDefault();
      wrapSelection("*", "*", "italic text");
    } else if (key === "k") {
      event.preventDefault();
      wrapSelection("[", "](https://)", "link text");
    } else if (event.shiftKey && key === "c") {
      event.preventDefault();
      insertBlock("```\ncode\n```\n");
    } else if (event.shiftKey && key === "l") {
      event.preventDefault();
      prefixLines("- ");
    }
  }

  return (
    <>
      <div className="flex min-h-12 shrink-0 flex-wrap items-center gap-2 border-b border-border/50 bg-panel px-3 py-2 lg:h-12 lg:flex-nowrap lg:px-5 lg:py-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface shrink-0" onClick={w.closeNote} aria-label={t("goBack")}>
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <h1 className="truncate text-sm font-medium min-w-0">{w.active.title}</h1>
          <span className={`shrink-0 text-[10px] ${w.autosave === "saving" ? "text-amber-500 animate-pulse-soft" : w.autosave === "conflict" ? "text-red-500" : w.autosave === "unsaved" ? "text-muted/40" : "text-emerald-500"}`}>
            {w.autosave === "saving" ? t("saving") : w.autosave === "conflict" ? "Conflict" : w.autosave === "unsaved" ? t("notSaved") : t("saved")}
          </span>
        </div>

        <div className="flex min-w-0 shrink-0 items-center gap-1 overflow-x-auto">
          <div className="flex rounded-lg bg-surface p-0.5">
            {(["edit", "preview", "split"] as const).map(m => (
              <button
                key={m}
                className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${w.viewMode === m ? "bg-panel text-foreground shadow-sm" : "text-muted hover:text-foreground"}`}
                onClick={() => w.setViewMode(m)}
              >
                {m === "edit" ? t("edit") : m === "preview" ? t("preview") : t("split")}
              </button>
            ))}
          </div>

          <div>
            <button ref={menuButtonRef} className="rounded-lg p-1.5 text-muted hover:bg-surface" onClick={toggleNoteMenu} aria-label={t("moreActions")} aria-haspopup="menu" aria-expanded={menuOpen}>
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01" /></svg>
            </button>
          </div>

          <div className="ml-1 pl-1 border-l border-border/50">
            <button className="rounded-lg p-1.5 text-muted hover:bg-surface" onClick={() => w.setRightOpen(!w.rightOpen)} aria-label={t("panel")}>
              <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
          </div>

          {isDirty && (
            <button className="bb-action ml-1 h-8 px-3 text-xs font-medium" onClick={w.save}>{t("save")}</button>
          )}
        </div>
      </div>

      {menuOpen && typeof document !== "undefined" && createPortal(
        <>
          <button className="fixed inset-0 z-[80] cursor-default" onClick={() => setMenuOpen(false)} aria-label="Close note actions" />
          <div
            className="fixed z-[81] w-44 rounded-xl border border-border bg-panel py-1 shadow-lg"
            style={{ top: menuPosition.top, left: menuPosition.left }}
            role="menu"
            aria-label="Note actions"
          >
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); void w.download(); }}>
              <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
              Export Markdown
            </button>
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); void w.renameNote(); }}>
              <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
              Rename note
            </button>
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-danger hover:bg-danger/10" onClick={() => { setMenuOpen(false); void w.deleteActive(); }}>
              <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              Remove note
            </button>
          </div>
        </>,
        document.body,
      )}

      {w.saveConflict && (
        <div
          className="flex flex-wrap items-center gap-3 border-b border-red-500/25 bg-red-500/10 px-3 py-2 text-xs lg:px-5"
          role="alert"
        >
          <div className="min-w-0 flex-1">
            <strong className="text-foreground">This note changed elsewhere.</strong>{" "}
            <span className="text-muted">Your local draft was not overwritten.</span>
          </div>
          <button
            className="bb-action px-3 py-1.5 font-medium"
            onClick={() => w.resolveSaveConflict("reload")}
          >
            Load latest
          </button>
          <button
            className="bb-action bb-action--danger px-3 py-1.5 font-medium"
            onClick={() => {
              if (window.confirm("Overwrite the newer note with your local draft?")) {
                void w.resolveSaveConflict("overwrite");
              }
            }}
          >
            Overwrite latest
          </button>
        </div>
      )}

      {(w.viewMode === "edit" || w.viewMode === "split") && (
        <div className="flex flex-wrap items-center gap-1 border-b border-border/40 bg-panel/70 px-3 py-2 lg:px-5">
          <ToolbarButton label="B" title="Bold" onClick={() => toggleMarker("**")} />
          <ToolbarButton label="I" title="Italic" onClick={() => toggleMarker("*")} />
          <ToolbarButton label="H2" title="Heading" onClick={() => insertBlock("## Heading\n")} />
          <ToolbarButton label=">" title="Quote" onClick={() => prefixLines("> ")} />
          <ToolbarButton label="*" title="Bullet list" onClick={() => prefixLines("- ")} />
          <ToolbarButton label="1." title="Ordered list" onClick={() => prefixLines("", true)} />
          <ToolbarButton label="Link" title="Link" onClick={() => wrapSelection("[", "](https://)", "link text")} />
          <ToolbarButton label="Img" title="Image" onClick={() => insertBlock("![alt text](image-url)\n")} />
          <ToolbarButton label="Attach" title="Attach file" onClick={() => fileInputRef.current?.click()} />
          <ToolbarButton label="`" title="Inline code" onClick={() => wrapSelection("`", "`", "code")} />
          <ToolbarButton label="Code" title="Code block" onClick={() => insertBlock("```\ncode\n```\n")} />
          <ToolbarButton label="Table" title="Table" onClick={() => insertBlock("| Column | Value |\n| --- | --- |\n| Example | Text |\n")} />
          <ToolbarButton label="HR" title="Horizontal rule" onClick={() => insertBlock("---\n")} />
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            onChange={(event) => uploadFiles(event.target.files)}
          />
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        {(w.viewMode === "edit" || w.viewMode === "split") && (
          <textarea
            ref={textareaRef}
            className={`min-h-0 resize-none bg-transparent px-4 py-5 leading-[1.85] outline-none placeholder:text-muted/20 lg:px-10 ${w.viewMode === "split" ? "flex-1 border-b border-border/50 lg:border-b-0 lg:border-r" : "flex-1"}`}
            value={w.draft}
            onChange={e => w.setDraft(e.target.value)}
            onKeyDown={onEditorKeyDown}
            placeholder={t("placeholderWrite")}
            spellCheck={false}
            autoFocus
            aria-label={t("editor")}
            style={{ fontFamily: "var(--font-editor)", fontSize: `${localStorage.getItem("bb_editor_font_size") || "15"}px` }}
          />
        )}
        {(w.viewMode === "preview" || w.viewMode === "split") && (
          <div className="min-h-0 flex-1">
            <MarkdownPreview content={w.draft} />
          </div>
        )}
      </div>

      <NotePipelineStatus
        progress={pipelineProgress}
        onOpenMonitor={() => w.setMonitorOpen(true)}
      />

      <AttachmentsPanel
        attachments={attachments}
        apiUrl={w.api}
        browserMode={BROWSER_STORAGE_MODE}
        status={attachmentStatus}
        onInsert={insertAttachmentMarkdown}
        onDelete={deleteAttachment}
        onReprocess={reprocessAttachment}
      />

      <Backlinks notePath={w.active.path} />
    </>
  );
}

function NotePipelineStatus({
  progress,
  onOpenMonitor,
}: {
  progress: NotePipelineProgress | null;
  onOpenMonitor: () => void;
}) {
  if (!progress) return null;
  const label = progress.state === "completed"
    ? "Assimilation complete"
    : progress.state === "failed"
      ? "Assimilation needs attention"
      : progress.currentStep || "Waiting for cognitive processing";
  const error = progress.errors?.[0];
  return (
    <section className="border-t border-border/50 px-6 py-3 lg:px-10" aria-label="Note assimilation progress">
      <div className="flex items-center justify-between gap-4 text-[11px]">
        <div>
          <p className="font-medium text-foreground">{label}</p>
          <p className="text-muted">{progress.completed}/{progress.total} stages · {progress.percent}%</p>
        </div>
        {error && (
          <button className="bb-action bb-action--danger px-2.5 py-1 font-medium" onClick={onOpenMonitor}>
            Open Monitor
          </button>
        )}
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-accent/15" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress.percent}>
        <div
          className={`h-full rounded-full transition-[width] duration-500 ${progress.state === "failed" ? "bg-danger" : progress.state === "completed" ? "bg-success" : "bg-accent"}`}
          style={{ width: `${Math.max(0, Math.min(100, progress.percent))}%` }}
        />
      </div>
      {error && (
        <div className="mt-2 text-[11px] text-muted">
          <p className="font-medium text-danger">{error.message}</p>
          <p>{error.impact}</p>
          <p>{error.action}</p>
        </div>
      )}
    </section>
  );
}

function AttachmentsPanel({
  attachments,
  apiUrl,
  browserMode,
  status,
  onInsert,
  onDelete,
  onReprocess,
}: {
  attachments: AttachmentItem[];
  apiUrl: string;
  browserMode: boolean;
  status: string;
  onInsert: (attachment: AttachmentItem) => void;
  onDelete: (id: number) => void;
  onReprocess: (id: number, extractor: string) => void;
}) {
  const [extractors, setExtractors] = useState<Record<number, string>>({});
  if (!attachments.length && !status) return null;
  return (
    <div className="border-t border-border/50 px-6 py-3 lg:px-10">
      <div className="mb-2 flex items-center gap-2">
        <h3 className="text-xs font-medium text-muted">Attachments</h3>
        {status && <span className="text-[11px] text-muted/60">{status}</span>}
      </div>
      <div className="flex flex-wrap gap-2">
        {attachments.map((attachment) => (
          <div key={attachment.id} className="flex items-center gap-2 rounded-lg bg-surface px-2.5 py-1.5 text-[11px] text-muted ring-1 ring-border/35">
            <a className="max-w-[220px] truncate hover:text-accent" href={browserMode ? attachment.downloadUrl : `${apiUrl}${attachment.downloadUrl}`} target="_blank" rel="noreferrer">
              {attachment.filename}
            </a>
            <span className="text-muted/45">{attachment.category}</span>
            <span className="text-muted/45">{formatBytes(attachment.sizeBytes)}</span>
            {!browserMode && <select
              aria-label={`Extractor for ${attachment.filename}`}
              className="rounded border border-border/60 bg-panel px-1 py-0.5 text-[10px] text-foreground"
              value={extractors[attachment.id] || "auto"}
              onChange={(event) => setExtractors((current) => ({ ...current, [attachment.id]: event.target.value }))}
            >
              <option value="auto">Auto extractor</option>
              {attachment.category === "image" && <option value="tesseract">Tesseract OCR</option>}
              {(attachment.category === "audio" || attachment.category === "video") && <option value="faster-whisper">Faster Whisper (local)</option>}
              {(attachment.category === "audio" || attachment.category === "video") && <option value="whisper-cli">Whisper CLI (custom)</option>}
              {attachment.category === "other" && <option value="attachment-text.v1">Text / document</option>}
            </select>}
            {!browserMode && <button className="text-accent hover:underline" onClick={() => onReprocess(attachment.id, extractors[attachment.id] || "auto")}>Reprocess</button>}
            <button className="text-accent hover:underline" onClick={() => onInsert(attachment)}>Insert</button>
            <button className="text-muted/55 hover:text-danger" onClick={() => onDelete(attachment.id)}>Remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function encodeNotePath(path: string) {
  return path.split("/").map(encodeURIComponent).join("/");
}

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function ToolbarButton({ label, title, onClick }: { label: string; title: string; onClick: () => void }) {
  return (
    <button
      className="rounded-md border border-border/40 bg-surface px-2 py-1 text-[11px] font-medium text-muted transition hover:border-accent/40 hover:text-foreground"
      type="button"
      title={title}
      onClick={onClick}
    >
      {label}
    </button>
  );
}
