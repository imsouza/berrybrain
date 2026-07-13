"use client";

import { useEffect, useState } from "react";
import { PublicShell } from "@/components/public-site/public-pages";
import { appPath, getApiUrl } from "@/contexts/workspace-context";

function passwordError(password: string): string {
  if (password.length < 12) return "Use at least 12 characters.";
  if (password.toLowerCase() === password || password.toUpperCase() === password) {
    return "Mix uppercase and lowercase letters.";
  }
  if (!/\d/.test(password)) return "Include at least one number.";
  return "";
}

export default function SetupPage() {
  const apiUrl = getApiUrl();
  const [checking, setChecking] = useState(true);
  const [needsSetup, setNeedsSetup] = useState(true);
  const [ownerEmail, setOwnerEmail] = useState("owner@local.berrybrain");
  const [displayName, setDisplayName] = useState("Local Owner");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let alive = true;
    fetch(`${apiUrl}/api/v1/setup/status`, { credentials: "include" })
      .then((response) => response.json())
      .then((data) => {
        if (!alive) return;
        setNeedsSetup(Boolean(data.needsSetup));
        setOwnerEmail(data.adminEmail || "owner@local.berrybrain");
      })
      .catch(() => setStatus("API unavailable. Check the self-hosted backend."))
      .finally(() => {
        if (alive) setChecking(false);
      });
    return () => {
      alive = false;
    };
  }, [apiUrl]);

  async function submit() {
    setStatus("");
    const error = passwordError(password);
    if (error) {
      setStatus(error);
      return;
    }
    if (password !== confirm) {
      setStatus("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      const response = await fetch(`${apiUrl}/api/v1/setup/admin`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password, display_name: displayName }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not configure this instance.");
      window.location.href = appPath("/brain");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not configure this instance.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <main className="grid min-h-[100dvh] place-items-center bg-background px-6 py-12">
        <section className="w-full max-w-md rounded-lg border border-border bg-panel p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Self-hosted setup</p>
          <h1 className="mt-3 text-2xl font-semibold tracking-tight">Create the local owner account</h1>
          <p className="mt-3 text-sm leading-6 text-muted">
            This configures the single account for this BerryBrain instance. No central account is created.
          </p>
          {checking ? (
            <p className="mt-6 text-sm text-muted">Checking instance...</p>
          ) : !needsSetup ? (
            <div className="mt-6 rounded-md border border-border bg-surface p-4">
              <p className="text-sm text-muted">This instance is already configured.</p>
              <a href={appPath("/login")} className="mt-4 inline-flex rounded-md bg-accent px-4 py-2 text-sm font-medium text-black">
                Sign in
              </a>
            </div>
          ) : (
            <form className="mt-6 space-y-4" onSubmit={(event) => event.preventDefault()}>
              <div>
                <label className="block text-xs font-medium text-muted">Owner email</label>
                <input
                  readOnly
                  value={ownerEmail}
                  className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-muted outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted">Display name</label>
                <input
                  value={displayName}
                  onChange={(event) => setDisplayName(event.target.value)}
                  className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted">Password</label>
                <input
                  type="password"
                  minLength={12}
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
                  placeholder="At least 12 characters"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-muted">Confirm password</label>
                <input
                  type="password"
                  minLength={12}
                  value={confirm}
                  onChange={(event) => setConfirm(event.target.value)}
                  className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent"
                  placeholder="Repeat password"
                />
              </div>
              <button
                type="button"
                disabled={busy || !password || !confirm}
                onClick={submit}
                className="w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-60"
              >
                {busy ? "Configuring..." : "Configure local account"}
              </button>
              {status && <p className="rounded-md bg-surface px-3 py-2 text-xs leading-5 text-muted">{status}</p>}
            </form>
          )}
        </section>
      </main>
    </PublicShell>
  );
}
