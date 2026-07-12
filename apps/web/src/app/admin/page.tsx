"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { PublicShell } from "@/components/public-site/public-pages";
import { getApiUrl, appPath } from "@/contexts/workspace-context";

type AdminUser = {
  id: number;
  email: string;
  displayName: string;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
  lockedUntil: string | null;
  forcePasswordReset: boolean;
  createdAt: string | null;
  lastLoginAt: string | null;
};

type AuditEvent = {
  id: number;
  actorEmail: string;
  action: string;
  targetType: string;
  targetId: string;
  createdAt: string | null;
};

type UserFormState = {
  email: string;
  displayName: string;
  password: string;
  emailVerified: boolean;
  twoFactorEnabled: boolean;
};

function readCsrf(): string {
  const match = document.cookie.match(/(?:^|;\s*)bb_csrf=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : "";
}

function fmtDate(value: string | null): string {
  if (!value) return "-";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "-" : date.toLocaleString("en-US");
}

const inputClass = "w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-accent";
const primaryBtn = "rounded-md bg-accent px-3 py-2 text-xs font-medium text-black disabled:opacity-60";
const ghostBtn = "rounded-md border border-border px-2.5 py-1.5 text-xs text-muted hover:text-foreground disabled:opacity-60";

function Badge({ tone, children }: { tone: "ok" | "warn" | "muted"; children: React.ReactNode }) {
  const tones = {
    ok: "border-emerald-500/40 text-emerald-400",
    warn: "border-red-500/40 text-red-400",
    muted: "border-border text-muted",
  };
  return <span className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${tones[tone]}`}>{children}</span>;
}

function Modal({ open, title, onClose, children }: { open: boolean; title: string; onClose: () => void; children: React.ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);
  return (
    <dialog ref={ref} onClose={onClose} className="m-auto w-full max-w-md rounded-lg border border-border bg-panel p-0 text-foreground backdrop:bg-black/50">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <h3 className="text-sm font-semibold">{title}</h3>
        <button onClick={onClose} className="rounded-md px-2 py-1 text-xs text-muted hover:bg-surface hover:text-foreground" aria-label="Close">
          Close
        </button>
      </div>
      <div className="px-5 py-4">{children}</div>
    </dialog>
  );
}

export default function Admin() {
  const apiUrl = getApiUrl();
  const [status, setStatus] = useState<"checking" | "ready" | "denied">("checking");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [query, setQuery] = useState("");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<AdminUser | null>(null);
  const [passwordUser, setPasswordUser] = useState<AdminUser | null>(null);
  const [deleting, setDeleting] = useState<AdminUser | null>(null);
  const [me, setMe] = useState<{ id: number } | null>(null);

  async function api(path: string, method: string, body?: unknown) {
    const response = await fetch(`${apiUrl}/api/v1${path}`, {
      method,
      credentials: "include",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": readCsrf() },
      body: body ? JSON.stringify(body) : undefined,
    });
    const payload = response.status === 204 ? {} : await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(payload.detail || "Operation failed");
    return payload;
  }

  async function loadAdmin() {
    setStatus("checking");
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/admin/users`, { credentials: "include" });
      if (response.status === 401) {
        window.location.href = appPath("/admin/login");
        return;
      }
      if (response.status === 403) {
        setStatus("denied");
        setMessage("This session is valid, but it is not the configured administrator account.");
        return;
      }
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || "Could not load admin data");
      setUsers(payload.users || []);
      const meResponse = await fetch(`${apiUrl}/api/v1/auth/me`, { credentials: "include" });
      if (meResponse.ok) setMe(await meResponse.json().catch(() => null));
      const auditResponse = await fetch(`${apiUrl}/api/v1/admin/audit-events`, { credentials: "include" });
      if (auditResponse.ok) {
        const auditPayload = await auditResponse.json();
        setEvents(auditPayload.events || []);
      }
      setStatus("ready");
    } catch (err) {
      setStatus("denied");
      setMessage(err instanceof Error ? err.message : "Could not load admin.");
    }
  }

  async function run(key: string, fn: () => Promise<void>) {
    setBusy(key);
    setError("");
    try {
      await fn();
      await loadAdmin();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Operation failed");
    } finally {
      setBusy("");
    }
  }

  useEffect(() => {
    loadAdmin();
  }, []);

  const filtered = useMemo(() => {
    const text = query.trim().toLowerCase();
    if (!text) return users;
    return users.filter((user) => user.email.toLowerCase().includes(text) || user.displayName.toLowerCase().includes(text));
  }, [query, users]);

  const stats = useMemo(
    () => ({
      total: users.length,
      verified: users.filter((user) => user.emailVerified).length,
      locked: users.filter((user) => user.lockedUntil).length,
      twoFactor: users.filter((user) => user.twoFactorEnabled).length,
    }),
    [users],
  );

  function action(userId: number, kind: "lock" | "unlock" | "revoke-sessions" | "force-password-reset") {
    const reason = kind === "lock" || kind === "unlock"
      ? "Admin panel action"
      : (window.prompt("Reason for this action (optional):", "Admin panel action") ?? "Admin panel action");
    const needsConfirm = kind === "force-password-reset" || kind === "revoke-sessions";
    if (needsConfirm && !window.confirm(`Confirm ${kind.replace(/-/g, " ")} for user ${userId}?`)) return;
    return run(`${kind}-${userId}`, async () => {
      await api(`/admin/users/${userId}/${kind}`, "POST", { reason });
    });
  }

  if (status !== "ready") {
    return (
      <main className="grid min-h-[100dvh] place-items-center bg-background px-6">
        <div className="w-full max-w-sm rounded-xl border border-border bg-panel p-6 text-center">
          {status === "checking" ? (
            <p className="text-sm text-muted">Checking admin session...</p>
          ) : (
            <>
              <h1 className="text-lg font-semibold tracking-tight">Admin access</h1>
              <p className="mt-2 text-sm leading-6 text-muted">{message || "Sign in with the administrator account to continue."}</p>
              <a href={appPath("/admin/login")} className="mt-5 inline-block rounded-md bg-accent px-4 py-2 text-sm font-medium text-black">Sign in</a>
            </>
          )}
        </div>
      </main>
    );
  }

  return (
    <PublicShell>
      <section className="mx-auto w-full max-w-6xl px-5 py-12 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Admin</p>
            <h1 className="mt-3 text-3xl font-semibold tracking-tight">User management</h1>
          </div>
          <div className="flex gap-2">
            <button onClick={loadAdmin} className={ghostBtn}>Refresh</button>
            <button onClick={() => setCreating(true)} className={primaryBtn}>New user</button>
          </div>
        </div>

        {status === "ready" && (
          <>
            <div className="mt-8 grid grid-cols-2 gap-3 md:grid-cols-4">
              {[
                ["Users", stats.total],
                ["Verified", stats.verified],
                ["Locked", stats.locked],
                ["With 2FA", stats.twoFactor],
              ].map(([label, value]) => (
                <div key={label} className="rounded-lg border border-border bg-panel px-4 py-3">
                  <div className="text-2xl font-semibold">{value}</div>
                  <div className="mt-1 text-xs text-muted">{label}</div>
                </div>
              ))}
            </div>

            {error && <div className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">{error}</div>}

            <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_0.62fr]">
              <div className="rounded-lg border border-border bg-panel">
                <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-4">
                  <h2 className="text-sm font-semibold">Users</h2>
                  <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search email or name..." className="w-56 max-w-[55%] rounded-md border border-border bg-surface px-3 py-1.5 text-xs outline-none focus:border-accent" />
                </div>
                <div className="divide-y divide-border">
                  {filtered.map((user) => {
                    const isSelf = me?.id === user.id;
                    return (
                    <div key={user.id} className="p-5">
                      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                        <div className="min-w-0">
                          <div className="truncate text-sm font-medium">{user.displayName || user.email}</div>
                          <div className="truncate text-xs text-muted">{user.email}</div>
                          <div className="mt-2 flex flex-wrap gap-1.5">
                            <Badge tone={user.emailVerified ? "ok" : "muted"}>{user.emailVerified ? "Verified" : "Unverified"}</Badge>
                            <Badge tone={user.lockedUntil ? "warn" : "ok"}>{user.lockedUntil ? "Locked" : "Active"}</Badge>
                            {user.twoFactorEnabled && <Badge tone="muted">2FA</Badge>}
                            {user.forcePasswordReset && <Badge tone="warn">Reset required</Badge>}
                          </div>
                          <div className="mt-2 text-[11px] text-muted">Last login: {fmtDate(user.lastLoginAt)}</div>
                        </div>
                        <div className="flex flex-wrap gap-2 md:justify-end">
                          <button disabled={busy === "edit" || isSelf} onClick={() => setEditing(user)} className={ghostBtn}>Edit</button>
                          <button disabled={busy === "set-password"} onClick={() => setPasswordUser(user)} className={ghostBtn}>Password</button>
                          <button disabled={busy === `${user.lockedUntil ? "unlock" : "lock"}-${user.id}` || isSelf} onClick={() => action(user.id, user.lockedUntil ? "unlock" : "lock")} className={ghostBtn}>
                            {user.lockedUntil ? "Unlock" : "Lock"}
                          </button>
                          <button disabled={busy === `force-password-reset-${user.id}` || isSelf} onClick={() => action(user.id, "force-password-reset")} className={ghostBtn}>Force reset</button>
                          <button disabled={busy === `revoke-sessions-${user.id}` || isSelf} onClick={() => action(user.id, "revoke-sessions")} className={ghostBtn}>Revoke sessions</button>
                          <button disabled={busy === "delete" || isSelf} onClick={() => setDeleting(user)} className="rounded-md border border-red-500/40 px-2.5 py-1.5 text-xs text-red-400 hover:bg-red-500/10 disabled:opacity-60">
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  );
                   })}
                  {filtered.length === 0 && <p className="p-5 text-sm text-muted">No users found.</p>}
                </div>
              </div>

              <div className="rounded-lg border border-border bg-panel">
                <div className="border-b border-border px-5 py-4">
                  <h2 className="text-sm font-semibold">Security audit</h2>
                </div>
                <div className="max-h-[560px] divide-y divide-border overflow-auto">
                  {events.map((event) => (
                    <div key={event.id} className="p-4">
                      <div className="text-xs font-medium">{event.action}</div>
                      <div className="mt-1 text-[11px] text-muted">{event.actorEmail || "system"} | {event.targetType}:{event.targetId}</div>
                      <div className="mt-0.5 text-[11px] text-muted">{fmtDate(event.createdAt)}</div>
                    </div>
                  ))}
                  {events.length === 0 && <p className="p-5 text-sm text-muted">No audit events yet.</p>}
                </div>
              </div>
            </div>
          </>
        )}
      </section>

      <CreateUserModal
        open={creating}
        busy={busy === "create"}
        onClose={() => setCreating(false)}
        onSubmit={(body) => run("create", async () => {
          await api("/admin/users", "POST", body);
          setCreating(false);
        })}
      />
      <EditUserModal
        user={editing}
        busy={busy === "edit"}
        onClose={() => setEditing(null)}
        onSubmit={(body) => run("edit", async () => {
          if (editing) await api(`/admin/users/${editing.id}`, "PATCH", body);
          setEditing(null);
        })}
      />
      <SetPasswordModal
        user={passwordUser}
        busy={busy === "set-password"}
        onClose={() => setPasswordUser(null)}
        onSubmit={(password) => run("set-password", async () => {
          if (passwordUser) await api(`/admin/users/${passwordUser.id}/set-password`, "POST", { password });
          setPasswordUser(null);
        })}
      />
      <DeleteUserModal
        user={deleting}
        busy={busy === "delete"}
        onClose={() => setDeleting(null)}
        onConfirm={() => run("delete", async () => {
          if (deleting) await api(`/admin/users/${deleting.id}`, "DELETE");
          setDeleting(null);
        })}
      />
    </PublicShell>
  );
}

function CreateUserModal({ open, busy, onClose, onSubmit }: { open: boolean; busy: boolean; onClose: () => void; onSubmit: (body: Record<string, unknown>) => void }) {
  const [form, setForm] = useState<UserFormState>({ email: "", displayName: "", password: "", emailVerified: true, twoFactorEnabled: false });
  useEffect(() => {
    if (open) setForm({ email: "", displayName: "", password: "", emailVerified: true, twoFactorEnabled: false });
  }, [open]);
  return (
    <Modal open={open} onClose={onClose} title="New user">
      <UserFields form={form} setForm={setForm} includePassword />
      <button disabled={busy || !form.email.trim() || !form.password.trim()} onClick={() => onSubmit(toPayload(form, true))} className={`${primaryBtn} mt-4`}>
        {busy ? "Creating..." : "Create user"}
      </button>
    </Modal>
  );
}

function EditUserModal({ user, busy, onClose, onSubmit }: { user: AdminUser | null; busy: boolean; onClose: () => void; onSubmit: (body: Record<string, unknown>) => void }) {
  const [form, setForm] = useState<UserFormState>({ email: "", displayName: "", password: "", emailVerified: true, twoFactorEnabled: false });
  useEffect(() => {
    if (user) {
      setForm({
        email: user.email,
        displayName: user.displayName,
        password: "",
        emailVerified: user.emailVerified,
        twoFactorEnabled: user.twoFactorEnabled,
      });
    }
  }, [user]);
  return (
    <Modal open={!!user} onClose={onClose} title="Edit user">
      <UserFields form={form} setForm={setForm} />
      <button disabled={busy || !form.email.trim()} onClick={() => onSubmit(toPayload(form, false))} className={`${primaryBtn} mt-4`}>
        {busy ? "Saving..." : "Save changes"}
      </button>
    </Modal>
  );
}

function SetPasswordModal({ user, busy, onClose, onSubmit }: { user: AdminUser | null; busy: boolean; onClose: () => void; onSubmit: (password: string) => void }) {
  const [password, setPassword] = useState("");
  useEffect(() => {
    if (user) setPassword("");
  }, [user]);
  return (
    <Modal open={!!user} onClose={onClose} title={`Set password | ${user?.email ?? ""}`}>
      <div className="space-y-3">
        <p className="text-xs leading-5 text-muted">This changes the password and revokes all active sessions for the user.</p>
        <input className={inputClass} type="password" placeholder="New password (min. 12, mixed case, number)" value={password} onChange={(event) => setPassword(event.target.value)} />
        <button disabled={busy || !password} onClick={() => onSubmit(password)} className={primaryBtn}>{busy ? "Applying..." : "Set password"}</button>
      </div>
    </Modal>
  );
}

function DeleteUserModal({ user, busy, onClose, onConfirm }: { user: AdminUser | null; busy: boolean; onClose: () => void; onConfirm: () => void }) {
  return (
    <Modal open={!!user} onClose={onClose} title="Delete user">
      <div className="space-y-4">
        <p className="text-sm leading-6 text-muted">
          Delete <span className="text-foreground">{user?.email}</span>? This is permanent and revokes every active session for that account.
        </p>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className={ghostBtn}>Cancel</button>
          <button disabled={busy} onClick={onConfirm} className="rounded-md bg-red-500 px-3 py-2 text-xs font-medium text-white disabled:opacity-60">
            {busy ? "Deleting..." : "Delete permanently"}
          </button>
        </div>
      </div>
    </Modal>
  );
}

function UserFields({ form, setForm, includePassword = false }: { form: UserFormState; setForm: (form: UserFormState) => void; includePassword?: boolean }) {
  return (
    <div className="flex flex-col gap-3">
      <input className={inputClass} placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
      <input className={inputClass} placeholder="Display name" value={form.displayName} onChange={(event) => setForm({ ...form, displayName: event.target.value })} />
      {includePassword && (
        <input className={inputClass} type="password" placeholder="Password (min. 12, mixed case, number)" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
      )}
      <label className="flex items-center gap-2 text-xs text-muted">
        <input type="checkbox" checked={form.emailVerified} onChange={(event) => setForm({ ...form, emailVerified: event.target.checked })} />
        Email verified
      </label>
      <label className="flex items-center gap-2 text-xs text-muted">
        <input type="checkbox" checked={form.twoFactorEnabled} onChange={(event) => setForm({ ...form, twoFactorEnabled: event.target.checked })} />
        Require 2FA
      </label>
    </div>
  );
}

function toPayload(form: UserFormState, includePassword: boolean) {
  return {
    email: form.email,
    display_name: form.displayName,
    ...(includePassword ? { password: form.password } : {}),
    email_verified: form.emailVerified,
    two_factor_enabled: form.twoFactorEnabled,
  };
}
