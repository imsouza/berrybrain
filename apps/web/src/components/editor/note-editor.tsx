"use client";

import { useWorkspace } from "@/contexts/workspace-context";
import { MarkdownPreview } from "./markdown-preview";
import { useState, useEffect, useMemo, useRef, type KeyboardEvent, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { t } from "@/i18n";
import {
  ArrowLeft,
  Bold,
  CheckSquare,
  Code,
  Download,
  FileCode2,
  Focus,
  Heading2,
  Image as ImageIcon,
  IndentDecrease,
  IndentIncrease,
  Italic,
  Link,
  List,
  ListOrdered,
  MoreVertical,
  Paperclip,
  PanelRight,
  Pencil,
  Pilcrow,
  Quote,
  Redo2,
  Replace,
  Search,
  Strikethrough,
  Table,
  Trash2,
  Undo2,
  WrapText,
} from "lucide-react";

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
  elapsedSeconds?: number;
  estimatedRemainingSeconds?: number | null;
  estimateSampleCount?: number;
  graphVisible?: boolean;
  graphState?: "waiting" | "enriching" | "ready" | "degraded";
  errors?: { jobId: number; message: string; impact: string; action: string }[];
};

function Backlinks({ notePath }: { notePath: string }) {
  const w = useWorkspace();
  const [links, setLinks] = useState<any[]>([]);
  useEffect(() => {
    if (w.demo) {
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
  const [findOpen, setFindOpen] = useState(false);
  const [findText, setFindText] = useState("");
  const [replaceText, setReplaceText] = useState("");
  const [lineWrap, setLineWrap] = useState(true);
  const [focusMode, setFocusMode] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const historyRef = useRef<{ past: string[]; future: string[] }>({ past: [], future: [] });

  useEffect(() => {
    const activePath = w.active?.path;
    if (!activePath || w.demo) {
      setAttachments([]);
      return;
    }
    const encodedPath = encodeNotePath(activePath);
    fetch(`${w.api}/api/v1/notes/${encodedPath}/attachments`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => setAttachments(data?.attachments || []))
      .catch(() => setAttachments([]));
  }, [w.active?.path, w.api, w.demo]);

  useEffect(() => {
    setMenuOpen(false);
    historyRef.current = { past: [], future: [] };
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
    const activePath = w.active?.path;
    if (!activePath || w.demo) {
      setPipelineProgress(null);
      return;
    }
    let cancelled = false;
    const notePath = activePath;
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

  const editorMetrics = useMemo(() => {
    const trimmed = w.draft.trim();
    const words = trimmed ? trimmed.split(/\s+/).length : 0;
    return {
      words,
      characters: w.draft.length,
      lines: w.draft ? w.draft.split("\n").length : 1,
      readingMinutes: words ? Math.max(1, Math.ceil(words / 225)) : 0,
    };
  }, [w.draft]);
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
    commitDraft(nextText);
    requestAnimationFrame(() => {
      const el = textareaRef.current;
      if (!el) return;
      el.focus();
      if (selectStart !== undefined && selectEnd !== undefined) {
        el.setSelectionRange(selectStart, selectEnd);
      }
    });
  }

  function commitDraft(nextText: string) {
    if (nextText === w.draft) return;
    const history = historyRef.current;
    history.past = [...history.past.slice(-99), w.draft];
    history.future = [];
    w.setDraft(nextText);
  }

  function undoDraft() {
    const history = historyRef.current;
    const previous = history.past.pop();
    if (previous === undefined) return;
    history.future = [w.draft, ...history.future].slice(0, 100);
    w.setDraft(previous);
    requestAnimationFrame(() => {
      const editor = textareaRef.current;
      editor?.focus();
      editor?.setSelectionRange(previous.length, previous.length);
    });
  }

  function redoDraft() {
    const history = historyRef.current;
    const next = history.future.shift();
    if (next === undefined) return;
    history.past = [...history.past.slice(-99), w.draft];
    w.setDraft(next);
    requestAnimationFrame(() => {
      const editor = textareaRef.current;
      editor?.focus();
      editor?.setSelectionRange(next.length, next.length);
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
    const url = `${w.api}${attachment.downloadUrl}`;
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
    const response = await fetch(`${w.api}/api/v1/notes/attachments/${id}`, { method: "DELETE" });
    if (response.ok) setAttachments((current) => current.filter((item) => item.id !== id));
  }

  async function reprocessAttachment(id: number, extractor: string) {
    if (w.demo) return;
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

  function indentSelection(outdent = false) {
    const el = textareaRef.current;
    const start = el?.selectionStart ?? w.draft.length;
    const end = el?.selectionEnd ?? w.draft.length;
    const lineStart = w.draft.lastIndexOf("\n", Math.max(0, start - 1)) + 1;
    const selected = w.draft.slice(lineStart, end);
    const lines = selected.split("\n");
    const transformed = lines.map((line) => outdent ? line.replace(/^( {1,2}|\t)/, "") : `  ${line}`).join("\n");
    replaceSelection(`${w.draft.slice(0, lineStart)}${transformed}${w.draft.slice(end)}`, lineStart, lineStart + transformed.length);
  }

  function selectFindMatch(direction: 1 | -1 = 1) {
    const query = findText;
    const el = textareaRef.current;
    if (!query || !el) return;
    const draft = w.draft.toLocaleLowerCase();
    const needle = query.toLocaleLowerCase();
    const anchor = direction === 1 ? el.selectionEnd : el.selectionStart;
    let index = direction === 1 ? draft.indexOf(needle, anchor) : draft.lastIndexOf(needle, Math.max(0, anchor - 1));
    if (index < 0) index = direction === 1 ? draft.indexOf(needle) : draft.lastIndexOf(needle);
    if (index >= 0) {
      el.focus();
      el.setSelectionRange(index, index + query.length);
    }
  }

  function replaceCurrentMatch() {
    const el = textareaRef.current;
    if (!findText || !el) return;
    const selected = w.draft.slice(el.selectionStart, el.selectionEnd);
    if (selected.toLocaleLowerCase() !== findText.toLocaleLowerCase()) {
      selectFindMatch(1);
      return;
    }
    const start = el.selectionStart;
    replaceSelection(`${w.draft.slice(0, start)}${replaceText}${w.draft.slice(el.selectionEnd)}`, start, start + replaceText.length);
  }

  function replaceAllMatches() {
    if (!findText) return;
    const escaped = findText.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    commitDraft(w.draft.replace(new RegExp(escaped, "giu"), replaceText));
  }

  function handleListContinuation(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter") return false;
    const el = textareaRef.current;
    if (!el || el.selectionStart !== el.selectionEnd) return false;
    const lineStart = w.draft.lastIndexOf("\n", Math.max(0, el.selectionStart - 1)) + 1;
    const line = w.draft.slice(lineStart, el.selectionStart);
    const match = line.match(/^(\s*)([-*+] |\d+\. |[-*+] \[[ xX]\] )(.*)$/);
    if (!match) return false;
    event.preventDefault();
    if (!match[3]) {
      replaceSelection(`${w.draft.slice(0, lineStart)}${w.draft.slice(el.selectionStart)}`, lineStart, lineStart);
      return true;
    }
    const marker = /^\d+\. $/.test(match[2]) ? `${Number(match[2].match(/\d+/)?.[0] || 0) + 1}. ` : match[2].replace(/\[[xX]\]/, "[ ]");
    insertBlock(`${match[1]}${marker}`);
    return true;
  }

  function onEditorKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (handleListContinuation(event)) return;
    if (event.key === "Tab") {
      event.preventDefault();
      indentSelection(event.shiftKey);
      return;
    }
    const mod = event.ctrlKey || event.metaKey;
    if (!mod) return;
    const key = event.key.toLowerCase();
    if (key === "z") {
      event.preventDefault();
      if (event.shiftKey) redoDraft();
      else undoDraft();
    } else if (key === "y") {
      event.preventDefault();
      redoDraft();
    } else if (key === "b") {
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
    } else if (key === "f") {
      event.preventDefault();
      setFindOpen(true);
    }
  }

  return (
    <>
      <div className="flex min-h-12 shrink-0 flex-wrap items-center gap-2 border-b border-border/50 bg-panel px-3 py-2 lg:h-12 lg:flex-nowrap lg:px-5 lg:py-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <button className="bb-icon-button shrink-0" onClick={w.closeNote} aria-label={t("goBack")}>
            <ArrowLeft className="size-4" />
          </button>
          <h1 className="truncate text-sm font-medium min-w-0">{w.active.title}</h1>
          <span className={`shrink-0 text-[10px] ${w.autosave === "saving" ? "text-accent animate-pulse-soft" : w.autosave === "conflict" ? "text-danger" : w.autosave === "unsaved" ? "text-muted/40" : "text-success"}`}>
            {w.autosave === "saving" ? t("saving") : w.autosave === "conflict" ? "Conflict" : w.autosave === "unsaved" ? t("notSaved") : t("saved")}
          </span>
        </div>

        <div className="flex min-w-0 shrink-0 items-center gap-1 overflow-x-auto">
          <div className="flex rounded-lg bg-surface p-0.5">
            {(["edit", "preview", "split"] as const).map(m => (
              <button
                key={m}
                className={`rounded-md px-2.5 py-1 text-[10px] font-medium transition ${w.viewMode === m ? "bg-panel text-foreground" : "text-muted hover:text-foreground"}`}
                onClick={() => w.setViewMode(m)}
              >
                {m === "edit" ? t("edit") : m === "preview" ? t("preview") : t("split")}
              </button>
            ))}
          </div>

          <div>
            <button ref={menuButtonRef} className="bb-icon-button" onClick={toggleNoteMenu} aria-label={t("moreActions")} aria-haspopup="menu" aria-expanded={menuOpen}>
              <MoreVertical className="size-4" />
            </button>
          </div>

          <div className="ml-1 pl-1 border-l border-border/50">
            <button className="bb-icon-button" onClick={() => w.setRightOpen(!w.rightOpen)} aria-label={t("panel")}>
              <PanelRight className="size-4" />
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
            className="fixed z-[81] w-44 rounded-md border border-border bg-panel py-1"
            style={{ top: menuPosition.top, left: menuPosition.left }}
            role="menu"
            aria-label="Note actions"
          >
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); void w.download(); }}>
              <Download className="size-3.5" />
              Export Markdown
            </button>
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-muted hover:bg-surface hover:text-foreground" onClick={() => { setMenuOpen(false); void w.renameNote(); }}>
              <Pencil className="size-3.5" />
              Rename note
            </button>
            <button role="menuitem" className="flex w-full items-center gap-2 px-3 py-2 text-xs text-danger hover:bg-danger/10" onClick={() => { setMenuOpen(false); void w.deleteActive(); }}>
              <Trash2 className="size-3.5" />
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
        <div className="flex flex-wrap items-center gap-1 border-b border-border bg-panel px-3 py-2 lg:px-5">
          <ToolbarGroup>
            <ToolbarButton icon={<Undo2 />} title="Undo" onClick={undoDraft} />
            <ToolbarButton icon={<Redo2 />} title="Redo" onClick={redoDraft} />
            <ToolbarButton icon={<Search />} title="Find and replace" active={findOpen} onClick={() => setFindOpen((value) => !value)} />
          </ToolbarGroup>
          <ToolbarGroup>
            <ToolbarButton icon={<Bold />} title="Bold" onClick={() => toggleMarker("**")} />
            <ToolbarButton icon={<Italic />} title="Italic" onClick={() => toggleMarker("*")} />
            <ToolbarButton icon={<Strikethrough />} title="Strikethrough" onClick={() => toggleMarker("~~")} />
            <ToolbarButton icon={<Heading2 />} title="Heading" onClick={() => insertBlock("## Heading\n")} />
            <ToolbarButton icon={<Quote />} title="Quote" onClick={() => prefixLines("> ")} />
          </ToolbarGroup>
          <ToolbarGroup>
            <ToolbarButton icon={<List />} title="Bullet list" onClick={() => prefixLines("- ")} />
            <ToolbarButton icon={<ListOrdered />} title="Ordered list" onClick={() => prefixLines("", true)} />
            <ToolbarButton icon={<CheckSquare />} title="Task list" onClick={() => prefixLines("- [ ] ")} />
            <ToolbarButton icon={<IndentIncrease />} title="Indent" onClick={() => indentSelection()} />
            <ToolbarButton icon={<IndentDecrease />} title="Outdent" onClick={() => indentSelection(true)} />
          </ToolbarGroup>
          <ToolbarGroup>
            <ToolbarButton icon={<Link />} title="Link" onClick={() => wrapSelection("[", "](https://)", "link text")} />
            <ToolbarButton icon={<ImageIcon />} title="Image" onClick={() => insertBlock("![alt text](image-url)\n")} />
            <ToolbarButton icon={<Paperclip />} title="Attach file" onClick={() => fileInputRef.current?.click()} />
            <ToolbarButton icon={<Code />} title="Inline code" onClick={() => wrapSelection("`", "`", "code")} />
            <ToolbarButton icon={<FileCode2 />} title="Code block" onClick={() => insertBlock("```\ncode\n```\n")} />
            <ToolbarButton icon={<Table />} title="Table" onClick={() => insertBlock("| Column | Value |\n| --- | --- |\n| Example | Text |\n")} />
            <ToolbarButton icon={<Pilcrow />} title="Horizontal rule" onClick={() => insertBlock("---\n")} />
          </ToolbarGroup>
          <div className="ml-auto flex gap-1">
            <ToolbarButton icon={<WrapText />} title={lineWrap ? "Disable line wrapping" : "Enable line wrapping"} active={lineWrap} onClick={() => setLineWrap((value) => !value)} />
            <ToolbarButton icon={<Focus />} title={focusMode ? "Exit focus mode" : "Focus mode"} active={focusMode} onClick={() => setFocusMode((value) => !value)} />
          </div>
          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            multiple
            onChange={(event) => uploadFiles(event.target.files)}
          />
        </div>
      )}

      {findOpen && (w.viewMode === "edit" || w.viewMode === "split") && (
        <div className="flex flex-wrap items-center gap-2 border-b border-border bg-surface px-3 py-2 lg:px-5" role="search">
          <Search className="size-4 text-muted" />
          <input className="bb-field h-8 min-w-40 flex-1 text-xs sm:max-w-64" value={findText} onChange={(event) => setFindText(event.target.value)} placeholder="Find in note" autoFocus />
          <input className="bb-field h-8 min-w-40 flex-1 text-xs sm:max-w-64" value={replaceText} onChange={(event) => setReplaceText(event.target.value)} placeholder="Replace with" />
          <button className="bb-action h-8 px-2.5 text-[11px]" onClick={() => selectFindMatch(-1)}>Previous</button>
          <button className="bb-action h-8 px-2.5 text-[11px]" onClick={() => selectFindMatch(1)}>Next</button>
          <button className="bb-action h-8 gap-1.5 px-2.5 text-[11px]" onClick={replaceCurrentMatch}><Replace className="size-3.5" />Replace</button>
          <button className="bb-action h-8 px-2.5 text-[11px]" onClick={replaceAllMatches}>Replace all</button>
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        {(w.viewMode === "edit" || w.viewMode === "split") && (
          <textarea
            ref={textareaRef}
            className={`min-h-0 resize-none bg-transparent px-4 py-5 leading-[1.85] outline-none placeholder:text-muted/20 lg:px-10 ${lineWrap ? "whitespace-pre-wrap" : "whitespace-pre overflow-x-auto"} ${focusMode ? "mx-auto w-full max-w-3xl" : ""} ${w.viewMode === "split" ? "flex-1 border-b border-border/50 lg:border-b-0 lg:border-r" : "flex-1"}`}
            value={w.draft}
            onChange={e => commitDraft(e.target.value)}
            onKeyDown={onEditorKeyDown}
            onPaste={(event) => {
              const files = event.clipboardData.files;
              if (files.length) {
                event.preventDefault();
                void uploadFiles(files);
              }
            }}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              if (!event.dataTransfer.files.length) return;
              event.preventDefault();
              void uploadFiles(event.dataTransfer.files);
            }}
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

      <div className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1 border-t border-border bg-panel px-4 py-1.5 font-mono text-[10px] text-muted lg:px-10" aria-label="Document statistics">
        <span>{editorMetrics.words} words</span>
        <span>{editorMetrics.characters} characters</span>
        <span>{editorMetrics.lines} lines</span>
        <span>{editorMetrics.readingMinutes ? `${editorMetrics.readingMinutes} min read` : "No reading time yet"}</span>
        <span className="ml-auto">Markdown</span>
      </div>

      <NotePipelineStatus
        progress={pipelineProgress}
        onOpenMonitor={() => w.setMonitorOpen(true)}
      />

      <AttachmentsPanel
        attachments={attachments}
        apiUrl={w.api}
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
          <p className="text-muted">
            {progress.completed}/{progress.total} stages · {progress.percent}%
            {progress.estimatedRemainingSeconds != null ? ` · about ${formatDuration(progress.estimatedRemainingSeconds)} remaining` : " · estimating from completed runs"}
          </p>
          <p className="mt-0.5 text-muted">
            Graph: {progress.graphState === "ready" ? "ready" : progress.graphState === "enriching" ? "note visible, knowledge enrichment running" : progress.graphState === "degraded" ? "note visible, enrichment needs attention" : "waiting for source node"}
          </p>
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
  status,
  onInsert,
  onDelete,
  onReprocess,
}: {
  attachments: AttachmentItem[];
  apiUrl: string;
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
            <a className="max-w-[220px] truncate hover:text-accent" href={`${apiUrl}${attachment.downloadUrl}`} target="_blank" rel="noreferrer">
              {attachment.filename}
            </a>
            <span className="text-muted/45">{attachment.category}</span>
            <span className="text-muted/45">{formatBytes(attachment.sizeBytes)}</span>
            <select
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
            </select>
            <button className="text-accent hover:underline" onClick={() => onReprocess(attachment.id, extractors[attachment.id] || "auto")}>Reprocess</button>
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

function formatDuration(seconds: number) {
  if (seconds < 60) return `${Math.max(1, Math.round(seconds))} sec`;
  const minutes = Math.ceil(seconds / 60);
  if (minutes < 60) return `${minutes} min`;
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return remainder ? `${hours} hr ${remainder} min` : `${hours} hr`;
}

function ToolbarGroup({ children }: { children: ReactNode }) {
  return <div className="flex gap-0.5 border-r border-border pr-1 last:border-r-0">{children}</div>;
}

function ToolbarButton({ icon, title, onClick, active = false }: { icon: ReactNode; title: string; onClick: () => void; active?: boolean }) {
  return (
    <button
      className={`bb-icon-button ${active ? "border-border bg-accent-soft text-accent" : ""}`}
      type="button"
      title={title}
      aria-label={title}
      aria-pressed={active}
      onClick={onClick}
    >
      <span className="[&>svg]:size-3.5">{icon}</span>
    </button>
  );
}
