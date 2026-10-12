"use client";

import { useEffect, useState } from "react";
import { apiFetch, appPath } from "@/contexts/workspace-context";
import { readResource } from "@/lib/read-resource";

type Alert = {
  id: number;
  type: string;
  title: string;
  description: string;
  action: string;
  actionUrl?: string | null;
  read: boolean;
};

type Props = {
  open: boolean;
  onClose: () => void;
  apiUrl: string;
};

export function NotificationsPopover({ open, onClose, apiUrl }: Props) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [unreadCount, setUnreadCount] = useState(0);

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
        const data = await readResource(`${apiUrl}/api/v1/notifications?limit=30`);
        if (!cancelled) {
          setAlerts(data.notifications || []);
          setUnreadCount(data.unreadCount || 0);
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

  const handleAction = async (alert: Alert) => {
    const response = await apiFetch(`${apiUrl}/api/v1/notifications/${alert.id}/read`, { method: "POST" }).catch(() => null);
    if (response?.ok) window.dispatchEvent(new Event("bb:notifications-changed"));
    const destination = alert.actionUrl || "/activity";
    window.location.href = destination.startsWith("/") ? appPath(destination) : destination;
    onClose();
  };

  const markAllRead = async () => {
    setError("");
    const response = await apiFetch(`${apiUrl}/api/v1/notifications/read-all`, { method: "POST" }).catch(() => null);
    if (!response?.ok) { setError("Could not mark notifications as read. Try again."); return; }
    setAlerts((items) => items.map((item) => ({ ...item, read: true })));
    setUnreadCount(0);
    window.dispatchEvent(new Event("bb:notifications-changed"));
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
      <div className="bb-card bb-card--elevated relative z-50 flex max-h-[70vh] w-80 flex-col overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3 border-b border-border/35">
          <h2 className="text-sm font-semibold">Alerts <span className="text-xs text-muted">{unreadCount} unread</span></h2>
          <button
            className="rounded-lg p-1.5 text-muted transition hover:bg-black/5 hover:text-foreground"
            onClick={onClose}
            aria-label="Close"
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
                  key={a.id || i}
                  className={`w-full rounded-lg p-3 text-left text-sm transition hover:bg-accent/10 ${a.read ? "bg-surface" : "bg-accent/5"}`}
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
          {error && <p role="alert" className="px-2 pb-2 text-xs text-danger">{error}</p>}
          <button
            className="bb-action w-full px-3 py-1.5 text-xs font-medium"
            onClick={markAllRead}
          >
            Mark all as read
          </button>
        </div>
      </div>
    </div>
  );
}
