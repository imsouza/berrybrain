"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getApiUrl, appPath } from "@/contexts/workspace-context";
import {
  AccountSettingsDialog,
  readCsrf,
  type MeUser,
} from "@/components/public-site/user-menu";

const personIcon = (
  <svg className="size-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth={2}
      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
    />
  </svg>
);

export function AccountMenu() {
  const apiUrl = getApiUrl();
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const [user, setUser] = useState<MeUser | null>(null);
  const [open, setOpen] = useState(false);

  const loadMe = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, { credentials: "include" });
      setUser(res.ok ? ((await res.json()).user as MeUser) : null);
    } catch {
      setUser(null);
    }
  }, [apiUrl]);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const logout = useCallback(
    async (dest: string) => {
      try {
        await fetch(`${apiUrl}/api/v1/auth/logout`, {
          method: "POST",
          credentials: "include",
          headers: { "X-CSRF-Token": readCsrf() },
        });
      } catch {
        // Navigation still moves the user to the expected account boundary.
      } finally {
        window.location.href = appPath(dest);
      }
    },
    [apiUrl],
  );

  if (!user) {
    return (
      <button
        className="rounded-lg p-1 text-muted hover:bg-surface"
        onClick={() => (window.location.href = appPath("/login"))}
        aria-label="Login"
      >
        {personIcon}
      </button>
    );
  }

  return (
    <div className="relative">
      <button
        className="rounded-lg p-1 text-muted hover:bg-surface"
        onClick={() => setOpen((value) => !value)}
        aria-label="Account"
        title={user.displayName || user.email}
      >
        {personIcon}
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute bottom-full right-0 z-50 mb-1 w-48 overflow-hidden rounded-lg border border-border bg-panel text-xs shadow-lg">
            <div className="truncate border-b border-border/50 px-3 py-2 text-[10px] text-muted">
              {user.email}
            </div>
            <button
              className="block w-full px-3 py-2 text-left text-foreground hover:bg-surface"
              onClick={() => {
                setOpen(false);
                dialogRef.current?.showModal();
              }}
            >
              Account settings
            </button>
            <button className="block w-full px-3 py-2 text-left text-foreground hover:bg-surface" onClick={() => logout("/login")}>
              Switch account
            </button>
            <button className="block w-full px-3 py-2 text-left text-red-400 hover:bg-surface" onClick={() => logout("/")}>
              Sign out
            </button>
          </div>
        </>
      )}
      <AccountSettingsDialog
        ref={dialogRef}
        apiUrl={apiUrl}
        user={user}
        onClose={() => dialogRef.current?.close()}
        onChanged={loadMe}
      />
    </div>
  );
}
