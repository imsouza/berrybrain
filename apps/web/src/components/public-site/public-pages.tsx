"use client";

import Image from "next/image";
import Link from "next/link";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";
import { UserMenu } from "@/components/public-site/user-menu";

const legalContent: Record<string, { title: string; body: string[] }> = {
  security: {
    title: "Security model",
    body: [
      "BerryBrain uses first-party accounts, secure session cookies, CSRF protection, email verification, email OTP challenges, rate limits, progressive lockout, and security audit events.",
      "Passwords use Argon2id when the production dependency set is installed. OTP codes are short-lived, single-use, and stored only as hashes.",
      "Admin operations require an authenticated session whose email matches the configured administrator account.",
      "Security controls are designed to resist high-rate and replayed requests from any interception tool. The system blocks behavior, not tool names.",
      "Recommended production settings include HTTPS-only secure cookies, restricted CORS origins, a strong session secret, SMTP credentials stored outside git, and a reverse proxy that exposes only the web entrypoint publicly.",
    ],
  },
  privacy: {
    title: "Privacy",
    body: [
      "BerryBrain is local-first. User notes remain in the configured vault unless the user enables external providers.",
      "When cloud AI, email, or external enrichment is configured, BerryBrain records provider, model, purpose, status, and evidence so the user can understand what left the local system.",
      "Account data is separated from note content. Security events may include timestamps, IP-derived request metadata, session state, and administrative actions needed to protect the service.",
      "Knowledge data is processed to build notes, concepts, graph edges, insights, and retrieval indexes. The product should never hide whether a result came from local processing or a configured external provider.",
      "For privacy requests, contact contato@optlabs.com.br.",
    ],
  },
  "gdpr-lgpd": {
    title: "GDPR and LGPD",
    body: [
      "BerryBrain is designed around data minimization, transparency, and user-controlled processing. Notes and graph data are treated as personal knowledge data.",
      "Users may request access, correction, export, or deletion of account data. Local vault files remain under the operator's storage control.",
      "Processing purposes include authentication, account security, note indexing, graph construction, retrieval, insight generation, and optional provider integrations configured by the user or administrator.",
      "For LGPD and GDPR requests, include the account email, request type, and enough context to verify ownership. Do not include passwords, OTP codes, API keys, or private notes in email.",
      "Privacy and data protection contact: contato@optlabs.com.br.",
    ],
  },
  terms: {
    title: "Terms",
    body: [
      "BerryBrain is a knowledge system for personal study, research, and note organization. Users are responsible for the material they store and process.",
      "The system may use local or configured cloud providers. Provider use must be configured by the user or administrator.",
      "Users should not store content they do not have the right to process. Automated insights, graph connections, and generated summaries are assistance outputs and should be reviewed before relying on them.",
      "Administrative access is limited and audited. Account misuse, abuse automation, credential stuffing, or attempts to bypass protective controls may lead to account restrictions.",
      "Support and account requests: contato@optlabs.com.br.",
    ],
  },
  contact: {
    title: "Contact",
    body: [
      "For support, security reports, account help, privacy requests, or business questions, contact contato@optlabs.com.br.",
      "Please do not send passwords, API keys, private notes, or recovery codes by email.",
      "For support, include the page, browser, approximate time, and what action failed. For security reports, include reproducible steps and impact without accessing data that is not yours.",
      "For account or privacy requests, use the email tied to the account whenever possible so ownership can be verified faster.",
    ],
  },
};

const nav = [
  ["Product", "/"],
  ["Security", "legal:security"],
  ["Privacy", "legal:privacy"],
  ["GDPR/LGPD", "legal:gdpr-lgpd"],
  ["Contact", "legal:contact"],
] as const;

const footerGroups = [
  {
    title: "Product",
    links: [
      ["Overview", "/"],
      ["Login", "/login"],
      ["Create account", "/signup"],
    ],
  },
  {
    title: "Trust",
    links: [
      ["Security", "legal:security"],
      ["Privacy", "legal:privacy"],
      ["GDPR/LGPD", "legal:gdpr-lgpd"],
    ],
  },
  {
    title: "Company",
    links: [
      ["Terms", "legal:terms"],
      ["Contact", "legal:contact"],
    ],
  },
] as const;

const LegalModalContext = createContext<(key: string) => void>(() => {});

export function useLegalModal() {
  return useContext(LegalModalContext);
}

function LegalModal({ open, onClose }: { open: string | null; onClose: () => void }) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const content = open ? legalContent[open] : null;

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && content) {
      if (!el.open) el.showModal();
    } else {
      if (el.open) el.close();
    }
  }, [open, content]);

  return (
    <dialog
      ref={dialogRef}
      onClose={onClose}
      onClick={(e) => { if (e.target === dialogRef.current) onClose(); }}
      className="m-auto w-full max-w-2xl rounded-lg border border-border bg-panel p-0 backdrop:bg-black/50"
    >
      {content && (
        <div className="max-h-[70vh] overflow-y-auto p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold tracking-tight">{content.title}</h2>
            <button onClick={onClose} className="rounded-md p-1 text-muted hover:text-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="size-5">
                <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
              </svg>
            </button>
          </div>
          <div className="mt-5 space-y-4 text-sm leading-7 text-muted">
            {content.body.map((p, i) => (
              <p key={i}>{p}</p>
            ))}
          </div>
        </div>
      )}
    </dialog>
  );
}

export function PublicShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [modal, setModal] = useState<string | null>(null);
  const openModal = useCallback((key: string) => setModal(key), []);
  const closeModal = useCallback(() => setModal(null), []);

  return (
    <LegalModalContext.Provider value={openModal}>
      <main className="min-h-screen bg-background text-foreground">
        <header className="sticky top-0 z-40 border-b border-border/70 bg-background/92 backdrop-blur">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-4 md:px-6">
          <Link href="/" aria-label="BerryBrain" className="flex items-center">
            <Image src="/berrylogo.png" alt="BerryBrain" width={64} height={64} className="rounded-md" />
          </Link>
          <nav className="hidden items-center gap-6 text-xs font-medium text-muted lg:flex">
            {nav.map(([label, href]) =>
              href.startsWith("legal:") ? (
                <button key={href} onClick={() => openModal(href.slice(6))} className="hover:text-foreground">
                  {label}
                </button>
              ) : (
                <Link key={href} href={href} className="hover:text-foreground">
                  {label}
                </Link>
              )
            )}
          </nav>
          <div className="flex items-center gap-2">
            <UserMenu />
          </div>
          </div>
        </header>
        {children}
        <Footer onOpenModal={openModal} />
        <LegalModal open={modal} onClose={closeModal} />
      </main>
    </LegalModalContext.Provider>
  );
}

export function LandingPage() {
  return (
    <PublicShell>
      <LandingContent />
    </PublicShell>
  );
}

function LandingContent() {
  const openModal = useLegalModal();
  return (
    <>
      <section className="border-b border-border/70">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-10 md:gap-10 md:px-6 md:py-16 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <p className="mb-4 text-xs font-semibold uppercase tracking-[0.18em] text-muted">Local-first knowledge system</p>
            <h1 className="max-w-3xl text-3xl font-semibold leading-tight sm:text-4xl md:text-5xl">
              A second brain that keeps evidence attached to every idea.
            </h1>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-muted sm:text-base">
              BerryBrain turns notes, graph connections, insights, and source material into a private cognitive layer for studying, reasoning, and preserving context.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/signup" className="rounded-md bg-accent px-5 py-3 text-sm font-medium text-black">
                Start securely
              </Link>
              <Link href="/demo" className="rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface">
                Demo
              </Link>
              <button
                onClick={() => openModal("security")}
                title="Open a concise summary of authentication, CSRF, session, rate-limit, and admin controls."
                className="rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface"
              >
                Security controls
              </button>
            </div>
            <dl className="mt-10 hidden max-w-xl grid-cols-3 divide-x divide-border/70 border-y border-border/70 py-4 text-sm sm:grid">
              {[
                ["Local-first", "storage"],
                ["Evidence", "on every insight"],
                ["Graph", "native"],
              ].map(([value, label]) => (
                <div key={value} className="px-4 first:pl-0">
                  <dt className="font-semibold">{value}</dt>
                  <dd className="mt-1 text-xs text-muted">{label}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div>
            <div className="overflow-hidden rounded-lg border border-border bg-panel shadow-sm">
              <div className="flex items-center justify-between border-b border-border bg-surface/70 px-4 py-3 text-xs text-muted">
                <span>Knowledge workspace</span>
                <span>Evidence-first</span>
              </div>
              <Image
                src="/berrybrain-print1.png"
                alt="BerryBrain home"
                width={900}
                height={560}
                priority
                className="h-auto w-full"
              />
            </div>
          </div>
        </div>
      </section>
      <section className="bg-panel/45">
        <div className="mx-auto grid w-full max-w-6xl gap-0 px-5 py-8 md:grid-cols-3 md:px-6">
          {[
            ["Private by design", "Local-first storage, optional cloud models, and visible provider traceability."],
            ["Security-aware", "Session cookies, CSRF checks, rate limits, lockout, and audit events protect account flows."],
            ["Graph-native", "Notes, concepts, attachments, insights, and gaps become connected records."],
          ].map(([title, body]) => (
            <article key={title} className="border-border py-5 md:border-l md:px-7 md:first:border-l-0 md:first:pl-0 md:last:pr-0">
              <h2 className="text-sm font-semibold">{title}</h2>
              <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-14 md:grid-cols-[0.8fr_1fr] md:px-6">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Cognitive layer</p>
          <h2 className="mt-3 text-3xl font-semibold">Not a chatbot. A structured thinking system.</h2>
          <p className="mt-4 text-sm leading-6 text-muted">
            The product surface is organized around durable knowledge records, not transient prompts.
          </p>
        </div>
        <div className="divide-y divide-border/70 border-y border-border/70">
          {[
            ["Knowledge Base", "Chunks notes and attachments for retrieval."],
            ["Knowledge Graph", "Connects notes, concepts, gaps, insights, and sources."],
            ["Semantic Data", "Answers questions about jobs, state, settings, and history."],
            ["Model Router", "Records provider, model, prompt version, status, and evidence."],
          ].map(([title, body], index) => (
            <div key={title} className="grid gap-3 py-5 sm:grid-cols-[5rem_1fr]">
              <span className="text-xs font-semibold text-accent">{String(index + 1).padStart(2, "0")}</span>
              <div>
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
      <section className="border-y border-border/70 bg-surface/55">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-14 md:grid-cols-[0.9fr_1.1fr] md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Security posture</p>
            <h2 className="mt-3 text-3xl font-semibold">Account safety is part of the workflow.</h2>
            <p className="mt-4 text-sm leading-6 text-muted">
              Login, account settings, admin actions, and sensitive API mutations are designed around explicit sessions, CSRF verification, and auditability.
            </p>
          </div>
          <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {[
              ["Session cookies", "HttpOnly session token with a separate readable CSRF cookie."],
              ["CSRF checks", "Sensitive authenticated requests require an explicit header token."],
              ["Admin boundary", "Admin routes require the configured administrator account."],
              ["Abuse controls", "Rate limits, lockout, OTP limits, and security audit events."],
            ].map(([title, body]) => (
              <div key={title} className="border-t border-border/70 pt-4">
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

function safeNext(): string {
  const n = new URLSearchParams(window.location.search).get("next");
  return n && n.startsWith("/") && !n.startsWith("//") ? n : "/brain";
}

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const isSignup = mode === "signup";
  const apiUrl = getApiUrl();
  const [email, setEmail] = useState(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("email") || "";
  });
  const [displayName, setDisplayName] = useState("");
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
      const endpoint = isSignup ? "/api/v1/auth/signup" : "/api/v1/auth/login";
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(isSignup ? { email, password, display_name: displayName } : { email, password }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Authentication failed");
      if (data.status === "authenticated") {
        window.location.href = safeNext();
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
      const endpoint = isSignup ? "/api/v1/auth/verify-email" : "/api/v1/auth/verify-2fa";
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(
          isSignup ? { email, code: otp } : { email, code: otp, challenge_id: challengeId, remember_me: keepSignedIn }
        ),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Invalid code");
      if (!isSignup && !keepSignedIn) {
        sessionStorage.setItem("bb_session_mode", "session-only");
      }
      window.location.href = safeNext();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Invalid code");
    } finally {
      setBusy(false);
    }
  }

  return (
    <PublicShell>
      <section className="mx-auto grid w-full max-w-5xl gap-8 px-5 py-12 md:grid-cols-[0.9fr_1fr] md:px-6 md:py-16">
        <div className="pt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
            {isSignup ? "Create account" : "Welcome back"}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">
            {isSignup ? "Start with verified email and 2FA." : "Log in with email verification."}
          </h1>
          <p className="mt-4 text-sm leading-6 text-muted">
            BerryBrain uses secure cookies, email OTP, CSRF protection, rate limits, and audit events. Support: contato@optlabs.com.br.
          </p>
        </div>
        <form className="rounded-lg border border-border bg-panel p-6" onSubmit={(event) => event.preventDefault()}>
          <label className="block text-xs font-medium text-muted">Email</label>
          <input required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="you@example.com" type="email" />
          {isSignup && (
            <>
              <label className="mt-4 block text-xs font-medium text-muted">Display name</label>
              <input autoComplete="name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="Your name" />
            </>
          )}
          <label className="mt-4 block text-xs font-medium text-muted">Password</label>
          <input required minLength={12} autoComplete={isSignup ? "new-password" : "current-password"} value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="At least 12 characters" type="password" />
          <p className="mt-2 text-[11px] leading-5 text-muted">Use at least 12 characters with mixed letter case and a number.</p>
          {!isSignup && (
            <label className="mt-4 flex items-center gap-2 text-xs text-muted">
              <input checked={keepSignedIn} onChange={(event) => setKeepSignedIn(event.target.checked)} type="checkbox" className="size-4 accent-[var(--color-accent)]" />
              Keep me signed in on this device
            </label>
          )}
          <button disabled={busy || !email.trim() || !password.trim()} type="button" onClick={submit} className="mt-6 w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-60">
            {busy ? "Working..." : isSignup ? "Create secure account" : "Continue"}
          </button>
          {awaitingCode && (
            <div className="mt-5 rounded-md border border-border bg-surface p-3">
              <label className="block text-xs font-medium text-muted">Email security code</label>
              <input value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 12))} className="mt-2 w-full rounded-md border border-border bg-panel px-3 py-2 text-sm outline-none focus:border-accent" placeholder="000000" inputMode="numeric" autoComplete="one-time-code" />
              <button disabled={busy || !otp} type="button" onClick={verifyCode} className="mt-3 w-full rounded-md border border-border px-4 py-2 text-sm disabled:opacity-60">
                Verify code
              </button>
            </div>
          )}
          {status && <p className="mt-4 rounded-md bg-surface px-3 py-2 text-xs leading-5 text-muted">{status}</p>}
          <p className="mt-4 text-xs leading-5 text-muted">
            This screen is wired for the security API. Email delivery requires SMTP settings on the server.
          </p>
        </form>
      </section>
    </PublicShell>
  );
}

export function LegalPage({
  title,
  children,
}: Readonly<{
  title: string;
  children: React.ReactNode;
}>) {
  return (
    <PublicShell>
      <section className="mx-auto w-full max-w-3xl px-6 py-12">
        <h1 className="text-3xl font-semibold tracking-tight">{title}</h1>
        <div className="mt-6 space-y-5 text-sm leading-7 text-muted">{children}</div>
      </section>
    </PublicShell>
  );
}

export function AccountSettingsPage() {
  return (
    <PublicShell>
      <section className="mx-auto w-full max-w-5xl px-5 py-12 md:px-6 md:py-16">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Account settings</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight">Control identity, privacy, and security.</h1>
          <p className="mt-4 text-sm leading-6 text-muted">
            These account controls sit outside the note vault. They define how you sign in, how sessions behave, and how external providers may be used.
          </p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            ["Account", "Display name, verified email, password reset, active sessions, and logout-all."],
            ["Privacy", "Data export, deletion requests, local-first mode, external provider visibility, and consent history."],
            ["Security", "Email 2FA, trusted devices, session review, lockout events, and audit history."],
          ].map(([title, body]) => (
            <article key={title} className="rounded-lg border border-border bg-panel p-5">
              <h2 className="text-sm font-semibold">{title}</h2>
              <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
            </article>
          ))}
        </div>
      </section>
    </PublicShell>
  );
}

function Footer({ onOpenModal }: { onOpenModal: (key: string) => void }) {
  return (
    <footer className="border-t border-border bg-panel/60">
      <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-10 md:grid-cols-[1.1fr_2fr] md:px-6">
        <div>
          <Image src="/berrylogo.png" alt="BerryBrain" width={160} height={160} className="rounded-md grayscale" />
          <p className="mt-4 max-w-sm text-sm leading-6 text-muted">
            A private, evidence-first second brain for notes, concepts, graph reasoning, and accountable AI assistance.
          </p>
          <p className="mt-4 text-xs text-muted">Support: contato@optlabs.com.br</p>
        </div>
        <div className="grid gap-6 sm:grid-cols-3">
          {footerGroups.map((group) => (
            <div key={group.title}>
              <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{group.title}</h3>
              <ul className="mt-3 space-y-2">
                {group.links.map(([label, href]) => (
                  <li key={href}>
                    {href.startsWith("legal:") ? (
                      <button onClick={() => onOpenModal(href.slice(6))} className="text-sm text-muted hover:text-foreground">
                        {label}
                      </button>
                    ) : (
                      <Link href={href} className="text-sm text-muted hover:text-foreground">
                        {label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </footer>
  );
}
