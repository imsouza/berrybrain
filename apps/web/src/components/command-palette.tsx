"use client";

import { useEffect, useRef, useState } from "react";
import { t } from "@/i18n";

type CommandResult = {
  type: "note" | "command";
  label: string;
  detail?: string;
  action: () => void;
};

export function CommandPalette({
  open,
  onClose,
  onNavigate,
  onCreateNote,
  onScanVault,
  onCreateDraft,
  apiUrl
}: {
  open: boolean;
  onClose: () => void;
  onNavigate: (path: string) => void;
  onCreateNote?: () => void;
  onScanVault: () => void;
  onCreateDraft?: () => void;
  apiUrl: string;
}) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<CommandResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const defaultOnCreate = onCreateNote || (() => {});

  const commands: CommandResult[] = [
    { type: "command", label: t("newNote"), detail: t("startDraft"), action: () => { (onCreateDraft || defaultOnCreate)(); onClose(); } },
    { type: "command", label: t("scanVault"), detail: t("syncVault"), action: () => { onScanVault(); onClose(); } },
  ];

  useEffect(() => {
    if (open) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;

    const trimmed = query.trim();
    if (!trimmed || apiUrl === "__demo__") {
      setResults(commands);
      setSelectedIndex(0);
      return;
    }

    let cancelled = false;
    setLoading(true);

    (async () => {
      try {
        const res = await fetch(
          `${apiUrl}/api/v1/search?q=${encodeURIComponent(trimmed)}&limit=5`
        );
        if (!res.ok || cancelled) return;
        const data = await res.json();
        const noteResults: CommandResult[] = (data.results || []).map(
          (r: any) => ({
            type: "note",
            label: r.title,
            detail: r.path,
            action: () => {
              onNavigate(r.path);
              onClose();
            }
          })
        );
        setResults([...noteResults, ...commands]);
        setSelectedIndex(0);
      } catch {
        setResults(commands);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => { cancelled = true; };
  }, [query, open]);

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (!open) return;
      if (event.key === "Escape") { onClose(); return; }
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, results.length - 1));
        return;
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        results[selectedIndex]?.action();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, results, selectedIndex]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-[18vh]"
      role="dialog"
      aria-modal="true"
      aria-label="Command palette"
    >
      <div className="fixed inset-0 bg-black/40 backdrop-blur-[2px]" onClick={onClose} aria-hidden="true" />
      <div className="relative w-full max-w-lg overflow-hidden rounded-2xl bg-panel shadow-2xl ring-1 ring-black/5">
        <div className="flex items-center gap-3 px-5">
          <svg className="size-4 shrink-0 text-muted/40" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            className="flex-1 bg-transparent py-4 text-sm outline-none placeholder:text-muted/40"
            placeholder={t("searchPlaceholder")}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            aria-label={t("search")}
            autoComplete="off"
            spellCheck={false}
          />
          <kbd className="rounded-md bg-black/[0.04] px-1.5 py-0.5 text-[10px] font-medium text-muted/40">esc</kbd>
        </div>

        <div className="max-h-64 overflow-y-auto border-t border-border/30 p-2">
          {loading ? (
            <div className="space-y-1 p-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-9 animate-pulse rounded-xl bg-black/[0.02]" />
              ))}
            </div>
          ) : results.length ? (
            <ul role="listbox" className="space-y-0.5">
              {results.map((item, i) => (
                <li
                  key={`${item.type}-${i}`}
                  role="option"
                  aria-selected={i === selectedIndex}
                  className={`flex items-center gap-3 rounded-xl px-3 py-2 text-sm cursor-pointer transition-colors ${
                    i === selectedIndex
                      ? "bg-black/[0.04] text-foreground"
                      : "text-muted hover:bg-black/[0.02] hover:text-foreground"
                  }`}
                  onClick={item.action}
                  onMouseEnter={() => setSelectedIndex(i)}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-xs font-medium">{item.label}</div>
                    {item.detail && (
                      <div className="truncate text-[11px] text-muted/60">{item.detail}</div>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-4 text-center text-xs text-muted">{t("noResults")}</div>
          )}
        </div>
      </div>
    </div>
  );
}
