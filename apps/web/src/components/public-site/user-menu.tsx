"use client";

import Link from "next/link";
import { forwardRef, useCallback, useEffect, useRef, useState } from "react";

import { getApiUrl, appPath } from "@/contexts/workspace-context";

export type MeUser = {
  id: number;
  email: string;
  displayName: string;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
};

export function readCsrf(): string {
  const match = document.cookie.match(/(?:^|;\s*)bb_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

export function UserMenu() {
  const apiUrl = getApiUrl();
  const dialogRef = useRef<HTMLDialogElement | null>(null);
  const [user, setUser] = useState<MeUser | null>(null);
  const [ready, setReady] = useState(false);

  const loadMe = useCallback(async () => {
    try {
      const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
        credentials: "include",
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user as MeUser);
      } else {
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setReady(true);
    }
  }, [apiUrl]);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  const logout = useCallback(async () => {
    try {
      await fetch(`${apiUrl}/api/v1/auth/logout`, {
        method: "POST",
        credentials: "include",
        headers: { "X-CSRF-Token": readCsrf() },
      });
    } catch {
      // The page navigation below is still the correct fallback.
    } finally {
      window.location.href = appPath("/");
    }
  }, [apiUrl]);

  if (!ready) return <div className="h-8 w-24" aria-hidden />;

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link href="/login" className="rounded-md px-3 py-2 text-xs text-muted hover:text-foreground">
          Log in
        </Link>
        <Link href="/signup" className="rounded-md bg-accent px-3 py-2 text-xs font-medium text-black">
          Create account
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link href="/brain" className="rounded-md bg-accent px-3 py-2 text-xs font-medium text-black">
        Open app
      </Link>
      <button
        type="button"
        onClick={() => dialogRef.current?.showModal()}
        aria-label="Account settings"
        title={user.displayName || user.email}
        className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-panel text-muted hover:text-foreground"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden>
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <circle cx="12" cy="7" r="4" />
        </svg>
      </button>
      <button type="button" onClick={logout} className="rounded-md border border-border px-3 py-2 text-xs text-muted hover:text-foreground">
        Sign out
      </button>
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

type DialogProps = {
  apiUrl: string;
  user: MeUser;
  onClose: () => void;
  onChanged: () => void;
};

export const AccountSettingsDialog = forwardRef<HTMLDialogElement, DialogProps>(function AccountSettingsDialog(
  { apiUrl, user, onClose, onChanged },
  ref,
) {
  const [displayName, setDisplayName] = useState(user.displayName);
  const [email, setEmail] = useState(user.email);
  const [emailPassword, setEmailPassword] = useState("");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [twoFaPassword, setTwoFaPassword] = useState("");
  const [deleteStage, setDeleteStage] = useState<"idle" | "code">("idle");
  const [deleteCode, setDeleteCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  useEffect(() => {
    setDisplayName(user.displayName);
    setEmail(user.email);
  }, [user]);

  const call = useCallback(
    async (path: string, method: string, body?: unknown) => {
      setBusy(true);
      setMsg(null);
      try {
        const res = await fetch(`${apiUrl}/api/v1/auth${path}`, {
          method,
          credentials: "include",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": readCsrf(),
          },
          body: body ? JSON.stringify(body) : undefined,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || "Operation failed");
        return data;
      } finally {
        setBusy(false);
      }
    },
    [apiUrl],
  );

  const guard = useCallback(
    async (fn: () => Promise<void>, okText: string) => {
      try {
        await fn();
        setMsg({ kind: "ok", text: okText });
        onChanged();
      } catch (err) {
        setMsg({ kind: "err", text: err instanceof Error ? err.message : "Error" });
      }
    },
    [onChanged],
  );

  return (
    <dialog ref={ref} className="m-auto w-full max-w-lg rounded-lg border border-border bg-panel p-0 text-foreground backdrop:bg-black/50">
      <div className="flex items-center justify-between border-b border-border px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold">Account settings</h2>
          <p className="mt-1 text-[11px] text-muted">{user.email}</p>
        </div>
        <button type="button" onClick={onClose} className="rounded-md px-2 py-1 text-xs text-muted hover:text-foreground">
          Close
        </button>
      </div>

      <div className="max-h-[70vh] space-y-6 overflow-y-auto px-5 py-4 text-xs">
        {msg && (
          <p className={msg.kind === "ok" ? "rounded-md bg-accent/10 px-3 py-2 text-accent" : "rounded-md bg-red-500/10 px-3 py-2 text-red-400"}>
            {msg.text}
          </p>
        )}

        <section className="space-y-2">
          <h3 className="font-medium text-foreground">Profile</h3>
          <label className="block text-muted">Display name</label>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <button
            type="button"
            disabled={busy || !displayName.trim()}
            onClick={() =>
              guard(async () => {
                await call("/me", "PATCH", { display_name: displayName });
              }, "Profile updated.")
            }
            className="rounded-md bg-accent px-3 py-2 font-medium text-black disabled:opacity-50"
          >
            Save profile
          </button>
        </section>

        <section className="space-y-2 border-t border-border pt-4">
          <h3 className="font-medium text-foreground">Email</h3>
          <input value={email} onChange={(e) => setEmail(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <input type="password" placeholder="Current password" value={emailPassword} onChange={(e) => setEmailPassword(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <button
            type="button"
            disabled={busy || !email.trim() || !emailPassword}
            onClick={() =>
              guard(async () => {
                await call("/change-email", "POST", { email, password: emailPassword });
                setEmailPassword("");
              }, "Email updated.")
            }
            className="rounded-md bg-accent px-3 py-2 font-medium text-black disabled:opacity-50"
          >
            Change email
          </button>
        </section>

        <section className="space-y-2 border-t border-border pt-4">
          <h3 className="font-medium text-foreground">Password</h3>
          <input type="password" placeholder="Current password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <input type="password" placeholder="New password (min. 12, mixed case, number)" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <button
            type="button"
            disabled={busy || !currentPassword || !newPassword}
            onClick={() =>
              guard(async () => {
                await call("/change-password", "POST", {
                  current_password: currentPassword,
                  new_password: newPassword,
                });
                setCurrentPassword("");
                setNewPassword("");
              }, "Password changed.")
            }
            className="rounded-md bg-accent px-3 py-2 font-medium text-black disabled:opacity-50"
          >
            Change password
          </button>
        </section>

        <section className="space-y-2 border-t border-border pt-4">
          <h3 className="font-medium text-foreground">Two-step verification</h3>
          <p className="text-muted">Status: {user.twoFactorEnabled ? "enabled" : "disabled"}</p>
          <input type="password" placeholder="Current password" value={twoFaPassword} onChange={(e) => setTwoFaPassword(e.target.value)} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
          <button
            type="button"
            disabled={busy || !twoFaPassword}
            onClick={() =>
              guard(async () => {
                await call("/2fa", "POST", { password: twoFaPassword, enabled: !user.twoFactorEnabled });
                setTwoFaPassword("");
              }, "2FA updated.")
            }
            className="rounded-md border border-border px-3 py-2 hover:text-foreground disabled:opacity-50"
          >
            {user.twoFactorEnabled ? "Disable 2FA" : "Enable 2FA"}
          </button>
        </section>

        <section className="space-y-2 border-t border-border pt-4">
          <h3 className="font-medium text-foreground">Sessions</h3>
          <button
            type="button"
            disabled={busy}
            onClick={() =>
              guard(async () => {
                await call("/logout-all", "POST", {});
                window.location.href = appPath("/login");
              }, "Sessions closed.")
            }
            className="rounded-md border border-border px-3 py-2 hover:text-foreground disabled:opacity-50"
          >
            Sign out everywhere
          </button>
        </section>

        <section className="space-y-2 border-t border-red-500/30 pt-4">
          <h3 className="font-medium text-red-400">Delete account</h3>
          <p className="text-muted">A confirmation code will be sent to your email. This action is permanent.</p>
          {deleteStage === "idle" ? (
            <button
              type="button"
              disabled={busy}
              onClick={() =>
                guard(async () => {
                  await call("/delete-account/request", "POST", {});
                  setDeleteStage("code");
                }, "Code sent to your email.")
              }
              className="rounded-md border border-red-500/50 px-3 py-2 text-red-400 hover:bg-red-500/10 disabled:opacity-50"
            >
              Request deletion
            </button>
          ) : (
            <div className="space-y-2">
              <input inputMode="numeric" placeholder="6-digit code" value={deleteCode} onChange={(e) => setDeleteCode(e.target.value.replace(/\D/g, "").slice(0, 12))} className="w-full rounded-md border border-border bg-surface px-3 py-2 outline-none focus:border-accent" />
              <button
                type="button"
                disabled={busy || !deleteCode}
                onClick={() =>
                  guard(async () => {
                    await call("/delete-account/confirm", "POST", { code: deleteCode });
                    window.location.href = appPath("/");
                  }, "Account deleted.")
                }
                className="rounded-md bg-red-500 px-3 py-2 font-medium text-white disabled:opacity-50"
              >
                Confirm permanent deletion
              </button>
            </div>
          )}
        </section>
      </div>
    </dialog>
  );
});
