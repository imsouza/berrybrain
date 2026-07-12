"use client";

import { useEffect, useState } from "react";
import { appPath } from "@/contexts/workspace-context";

type Alert = {
  kind: string;
  title: string;
  description: string;
  action: string;
};

type Props = {
  open: boolean;
  onClose: () => void;
  apiUrl: string;
};

export function NotificationsPopover({ open, onClose, apiUrl }: Props) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!open) return;
    if (apiUrl === "__demo__") {
      setAlerts([]);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function load() {
      try {
        const r = await fetch(`${apiUrl}/api/v1/home/summary`);
        if (r.ok && !cancelled) {
          const data = await r.json();
          setAlerts(data.needsAttention || []);
        }
      } catch {}
      if (!cancelled) setLoading(false);
    }

    load();
    const timer = setInterval(load, 30000);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [open, apiUrl]);

  const handleAction = (alert: Alert) => {
    switch (alert.kind) {
      case "ollama_offline":
      case "failed_jobs":
      case "provider_issue":
        window.location.href = appPath("/brain?monitor=open");
        break;
      case "pending_jobs":
        window.location.href = appPath("/activity");
        break;
      case "no_notes":
        break;
      default:
        window.location.href = appPath("/activity");
    }
    onClose();
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24">
      <div
        className="absolute inset-0 bg-black/40 backdrop-blur-[2px]"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
      />
      <div className="relative z-50 w-80 max-h-[70vh] flex flex-col overflow-hidden rounded-2xl bg-panel shadow-2xl ring-1 ring-black/5">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/35">
          <h2 className="text-sm font-semibold">Alertas</h2>
          <button
            className="rounded-lg p-1.5 text-muted transition hover:bg-black/5 hover:text-foreground"
            onClick={onClose}
            aria-label="Fechar"
          >
            <svg className="size-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="p-4 text-center text-xs text-muted/55">Loading...</div>
          ) : alerts.length === 0 ? (
            <div className="p-4 text-center text-xs text-muted/55">All clear.</div>
          ) : (
            <div className="space-y-1 p-2">
              {alerts.map((a, i) => (
                <button
                  key={a.kind + i}
                  className="w-full rounded-lg p-3 text-left text-sm transition bg-accent/5 hover:bg-accent/10"
                  onClick={() => handleAction(a)}
                >
                  <div className="text-xs font-medium">{a.title}</div>
                  <div className="mt-0.5 text-xs text-muted/60">{a.description}</div>
                  <div className="mt-1 text-[10px] text-accent font-medium">{a.action} →</div>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-border/35 p-2">
          <button
            className="w-full rounded-lg bg-surface px-3 py-1.5 text-xs font-medium text-muted hover:text-foreground"
            onClick={() => {
              window.location.href = appPath("/activity");
              onClose();
            }}
          >
            Ver atividade
          </button>
        </div>
      </div>
    </div>
  );
}
