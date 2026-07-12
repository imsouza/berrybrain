"use client";

import { useState } from "react";
import { PublicShell } from "@/components/public-site/public-pages";
import { getApiUrl, appPath } from "@/contexts/workspace-context";

function AdminLogin() {
  const apiUrl = getApiUrl();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [keepSignedIn, setKeepSignedIn] = useState(true);
  const [otp, setOtp] = useState("");
  const [challengeId, setChallengeId] = useState("");
  const [awaitingCode, setAwaitingCode] = useState(false);
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit() {
    setBusy(true);
    setStatus("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password, remember_me: keepSignedIn }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Authentication failed");
      if (data.status === "authenticated") {
        window.location.href = appPath("/admin");
        return;
      }
      if (data.challengeId) setChallengeId(data.challengeId);
      if (data.status === "verification_required" || data.status === "2fa_required" || data.challengeId) {
        setAwaitingCode(true);
      }
      setStatus(data.status || "Check your email for the next step.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setBusy(false);
    }
  }

  async function verifyCode() {
    setBusy(true);
    setStatus("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/auth/verify-2fa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, code: otp, challenge_id: challengeId, remember_me: keepSignedIn }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Invalid code");
      window.location.href = appPath("/admin");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Invalid code");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <main className="grid min-h-[100dvh] place-items-center bg-background px-6">
        <div className="w-full max-w-sm rounded-xl border border-border bg-panel p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Admin</p>
          <h1 className="mt-2 text-xl font-semibold tracking-tight">Administrator sign in</h1>
          <form className="mt-6 space-y-4" onSubmit={(event) => event.preventDefault()}>
            <div>
              <label className="block text-xs font-medium text-muted">Email</label>
              <input
                required
                autoComplete="email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
                placeholder="admin@example.com"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted">Password</label>
              <input
                required
                minLength={12}
                autoComplete="current-password"
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
                placeholder="At least 12 characters"
              />
            </div>
            {!awaitingCode && (
              <label className="flex items-center gap-2 text-xs text-muted">
                <input checked={keepSignedIn} onChange={(event) => setKeepSignedIn(event.target.checked)} type="checkbox" className="size-4 accent-[var(--color-accent)]" />
                Keep me signed in on this device
              </label>
            )}
            {awaitingCode && (
              <div className="rounded-md border border-border bg-surface p-3">
                <label className="block text-xs font-medium text-muted">Email security code</label>
                <input
                  value={otp}
                  onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 12))}
                  className="mt-2 w-full rounded-md border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-accent"
                  placeholder="000000"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                />
              </div>
            )}
            <button
              disabled={busy || (awaitingCode ? !otp : !email.trim() || !password.trim())}
              type="button"
              onClick={awaitingCode ? verifyCode : submit}
              className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
            >
              {busy ? "Working..." : awaitingCode ? "Verify code" : "Sign in"}
            </button>
            {status && <p className="rounded-md bg-surface px-3 py-2 text-xs leading-5 text-muted">{status}</p>}
          </form>
          <a href={appPath("/login")} className="mt-4 block text-center text-xs text-muted hover:text-foreground">Back to app login</a>
        </div>
      </main>
    </PublicShell>
  );
}

export default AdminLogin;
