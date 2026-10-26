"use client";

import { useState } from "react";
import { askReferenceHref, verifiedReference, type AskReference } from "./ask-markdown";

export type EditorSelectionContext = {
  text: string;
  start: number;
  end: number;
  notePath: string;
  noteRevision: string;
  isUnsavedDraft: boolean;
};

export type EditorDiffTarget = {
  notePath: string;
  noteTitle: string;
  noteRevision: string;
  draft: string;
  isUnsavedDraft: boolean;
  selection: EditorSelectionContext | null;
  applyDraft: (nextText: string) => void;
};

type DiffMode = "append" | "replace_selection";

type PreparedDiffProposal = {
  targetNotePath: string;
  targetNoteTitle: string;
  targetNoteRevision: string;
  baseDraft: string;
  wasUnsavedDraft: boolean;
  selection: EditorSelectionContext | null;
};

function resolvedAnswerMarkdown(answer: string, references: AskReference[]): string {
  const linked = answer.replace(/\[([^\]]+)\]\(bbref:([^)]*)\)/g, (_match, label: string, marker: string) => {
    const reference = verifiedReference(marker, references);
    const href = reference?.current ? askReferenceHref(reference) : null;
    return href ? `[${label.replaceAll("]", "\\]")}](${href})` : label;
  });
  return linked.trim();
}

function buildNextDraft(
  baseDraft: string,
  proposedText: string,
  mode: DiffMode,
  selection: EditorSelectionContext | null,
): string {
  if (mode === "replace_selection" && selection) {
    return `${baseDraft.slice(0, selection.start)}${proposedText}${baseDraft.slice(selection.end)}`;
  }
  const trimmedBase = baseDraft.trimEnd();
  const trimmedProposed = proposedText.trim();
  if (!trimmedBase) return `${trimmedProposed}\n`;
  return `${trimmedBase}\n\n${trimmedProposed}\n`;
}

function formatDiffPreview(
  baseDraft: string,
  proposedText: string,
  mode: DiffMode,
  selection: EditorSelectionContext | null,
): string {
  const lines: string[] = [];
  if (mode === "replace_selection" && selection) {
    const beforeContext = baseDraft.slice(Math.max(0, selection.start - 120), selection.start).split("\n").slice(-2);
    const removed = baseDraft.slice(selection.start, selection.end).split("\n");
    const added = proposedText.split("\n");
    const afterContext = baseDraft.slice(selection.end, selection.end + 120).split("\n").slice(0, 2);
    lines.push(`@@ replace selection (${selection.start}..${selection.end}) @@`);
    for (const line of beforeContext) {
      if (line) lines.push(`  ${line}`);
    }
    for (const line of removed) {
      lines.push(`- ${line}`);
    }
    for (const line of added) {
      lines.push(`+ ${line}`);
    }
    for (const line of afterContext) {
      if (line) lines.push(`  ${line}`);
    }
    return lines.join("\n");
  }
  const tailLines = baseDraft.trimEnd() ? baseDraft.trimEnd().split("\n").slice(-3) : [];
  const addedLines = proposedText.trim().split("\n");
  lines.push("@@ append to end of note @@");
  for (const line of tailLines) {
    lines.push(`  ${line}`);
  }
  for (const line of addedLines) {
    lines.push(`+ ${line}`);
  }
  return lines.join("\n");
}

export function AskEditorDiffPlan({
  answer,
  references = [],
  editorTarget,
}: {
  answer: string;
  references?: AskReference[];
  editorTarget: EditorDiffTarget;
}) {
  const validSelection =
    editorTarget.selection &&
    editorTarget.selection.notePath === editorTarget.notePath &&
    editorTarget.selection.end > editorTarget.selection.start &&
    editorTarget.draft.slice(editorTarget.selection.start, editorTarget.selection.end) === editorTarget.selection.text
      ? editorTarget.selection
      : null;

  const [open, setOpen] = useState(false);
  const [proposal, setProposal] = useState<PreparedDiffProposal | null>(null);
  const [mode, setMode] = useState<DiffMode>(() => (validSelection ? "replace_selection" : "append"));
  const [proposedText, setProposedText] = useState(() => resolvedAnswerMarkdown(answer, references));
  const [applied, setApplied] = useState(false);

  function openDiffPreview() {
    const currentSelection =
      editorTarget.selection &&
      editorTarget.selection.notePath === editorTarget.notePath &&
      editorTarget.selection.end > editorTarget.selection.start &&
      editorTarget.draft.slice(editorTarget.selection.start, editorTarget.selection.end) === editorTarget.selection.text
        ? editorTarget.selection
        : null;
    setProposal({
      targetNotePath: editorTarget.notePath,
      targetNoteTitle: editorTarget.noteTitle,
      targetNoteRevision: editorTarget.noteRevision,
      baseDraft: editorTarget.draft,
      wasUnsavedDraft: editorTarget.isUnsavedDraft,
      selection: currentSelection,
    });
    setMode(currentSelection ? "replace_selection" : "append");
    setProposedText(resolvedAnswerMarkdown(answer, references));
    setApplied(false);
    setOpen(true);
  }

  function refreshProposal() {
    const currentSelection =
      editorTarget.selection &&
      editorTarget.selection.notePath === editorTarget.notePath &&
      editorTarget.selection.end > editorTarget.selection.start &&
      editorTarget.draft.slice(editorTarget.selection.start, editorTarget.selection.end) === editorTarget.selection.text
        ? editorTarget.selection
        : null;
    setProposal({
      targetNotePath: editorTarget.notePath,
      targetNoteTitle: editorTarget.noteTitle,
      targetNoteRevision: editorTarget.noteRevision,
      baseDraft: editorTarget.draft,
      wasUnsavedDraft: editorTarget.isUnsavedDraft,
      selection: currentSelection,
    });
    if (mode === "replace_selection" && !currentSelection) {
      setMode("append");
    }
    setApplied(false);
  }

  if (!open || !proposal) {
    return (
      <div className="mt-2">
        <button className="bb-action px-3 py-1.5 text-xs" onClick={openDiffPreview}>
          Review diff for editor
        </button>
      </div>
    );
  }

  const noteSwitched = editorTarget.notePath !== proposal.targetNotePath;
  const selectionInvalidated =
    mode === "replace_selection" &&
    (!proposal.selection ||
      editorTarget.draft.slice(proposal.selection.start, proposal.selection.end) !== proposal.selection.text);
  const draftChangedConcurrently =
    !noteSwitched &&
    (editorTarget.draft !== proposal.baseDraft ||
      editorTarget.noteRevision !== proposal.targetNoteRevision ||
      selectionInvalidated);

  const diffPreview = formatDiffPreview(
    proposal.baseDraft,
    proposedText,
    mode,
    proposal.selection,
  );

  function approveAndApply() {
    if (!proposal || noteSwitched || draftChangedConcurrently || !proposedText.trim()) return;
    const nextDraft = buildNextDraft(
      proposal.baseDraft,
      proposedText,
      mode,
      proposal.selection,
    );
    editorTarget.applyDraft(nextDraft);
    setProposal({
      ...proposal,
      baseDraft: nextDraft,
      wasUnsavedDraft: true,
    });
    setApplied(true);
  }

  return (
    <section className="mt-3 rounded-xl border border-border bg-panel p-4" aria-label="Review editor diff">
      <div className="mb-2 flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold">Review diff before applying to editor</h3>
        <button className="text-xs text-muted hover:text-foreground" onClick={() => setOpen(false)}>
          Close
        </button>
      </div>
      <p className="mb-3 text-xs text-muted">
        Supervised editor action: nothing is inserted into your note until you approve this diff. Applying updates your editor draft with Undo (Ctrl+Z) support.
      </p>
      <dl className="mb-3 grid gap-2 text-xs sm:grid-cols-3">
        <div>
          <dt className="text-muted">Target note</dt>
          <dd className="truncate font-medium" title={proposal.targetNotePath}>
            {proposal.targetNoteTitle} ({proposal.targetNotePath})
          </dd>
        </div>
        <div>
          <dt className="text-muted">Base revision</dt>
          <dd>
            {proposal.targetNoteRevision ? proposal.targetNoteRevision.slice(0, 8) : "local"} ·{" "}
            {proposal.wasUnsavedDraft ? "unsaved draft" : "saved note"}
          </dd>
        </div>
        <div>
          <dt className="text-muted">Placement</dt>
          <dd>
            <select
              aria-label="Diff placement mode"
              className="mt-0.5 w-full rounded border border-border bg-surface px-2 py-1 text-xs"
              value={mode}
              onChange={(event) => {
                setMode(event.target.value as DiffMode);
                setApplied(false);
              }}
            >
              <option value="append">Append to end of note</option>
              {proposal.selection && (
                <option value="replace_selection">
                  Replace selected excerpt ({proposal.selection.text.length} chars)
                </option>
              )}
            </select>
          </dd>
        </div>
      </dl>

      <label className="block text-xs">
        Proposed Markdown snippet
        <textarea
          aria-label="Proposed Markdown snippet"
          className="mt-1 min-h-28 w-full rounded-lg border border-border bg-surface p-2.5 font-mono text-xs"
          value={proposedText}
          onChange={(event) => {
            setProposedText(event.target.value);
            setApplied(false);
          }}
        />
      </label>

      <p className="mb-1 mt-3 text-[11px] text-muted">Diff preview against current editor draft</p>
      <pre
        aria-label="Editor diff preview"
        className="max-h-56 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-surface p-3 font-mono text-xs"
      >
        {diffPreview}
      </pre>

      {noteSwitched && (
        <p className="mt-3 text-xs text-danger" role="alert">
          Active note changed since this preview was prepared. Cannot apply this diff to a different note.
        </p>
      )}
      {!noteSwitched && draftChangedConcurrently && !applied && (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-danger" role="alert">
          <span>
            The editor draft or saved note changed since this diff was prepared. Refresh the diff preview so text is not inserted at a stale position.
          </span>
          <button className="bb-action px-2.5 py-1 text-xs text-foreground" onClick={refreshProposal}>
            Refresh diff preview
          </button>
        </div>
      )}
      {applied && (
        <p className="mt-3 text-xs text-success" role="status">
          Applied to editor draft. Use Undo (Ctrl+Z) in the editor to revert, or Save to persist.
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          className="bb-action bb-action--primary px-3 py-1.5 text-xs"
          disabled={noteSwitched || draftChangedConcurrently || !proposedText.trim() || applied}
          onClick={approveAndApply}
        >
          Approve and apply to editor
        </button>
        <button className="bb-action px-3 py-1.5 text-xs" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </section>
  );
}
