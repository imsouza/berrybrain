"use client";

import Image from "next/image";
import berrylogo from "../../../public/berrylogo.png";
import berryPrint from "../../../public/berrybrain-print1.png";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getApiUrl, appPath } from "@/contexts/workspace-context";
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
  ["Home", "/"],
  ["Docs", "/docs"],
  ["FAQ", "/faq"],
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

const comparisonRows: Array<[string, number[]]> = [
  ["Local-first privacy", [100, 95, 30, 100]],
  ["AI evidence tracing", [100, 20, 40, 0]],
  ["Automatic knowledge graph", [95, 70, 30, 0]],
  ["Semantic search", [95, 50, 60, 10]],
  ["Works fully offline", [100, 100, 40, 100]],
  ["Cost-efficiency", [90, 85, 50, 100]],
];

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

const mobileNavLinks = [
  ...nav,
  ["Security", "legal:security"],
  ["Privacy", "legal:privacy"],
  ["GDPR/LGPD", "legal:gdpr-lgpd"],
  ["Terms", "legal:terms"],
  ["Contact", "legal:contact"],
] as const;

export function PublicShell({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const [modal, setModal] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const openModal = useCallback((key: string) => setModal(key), []);
  const closeModal = useCallback(() => setModal(null), []);

  return (
    <LegalModalContext.Provider value={openModal}>
      <main className="min-h-screen overflow-x-hidden bg-background text-foreground">
        <header className="sticky top-0 z-40 border-b border-border/70 bg-background/92 backdrop-blur">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-5 py-3.5 md:px-6">
          <a href={appPath("/")} aria-label="BerryBrain" className="flex items-center">
            <Image src={berrylogo} alt="BerryBrain" width={48} height={48} className="rounded-md" sizes="48px" />
          </a>
          <nav className="hidden items-center gap-7 text-sm font-medium text-muted lg:flex">
            {nav.map(([label, href]) =>
              href.startsWith("legal:") ? (
                <button key={href} onClick={() => openModal(href.slice(6))} className="underline-offset-4 transition hover:text-foreground hover:underline">
                  {label}
                </button>
              ) : (
                <a key={href} href={appPath(href)} className="underline-offset-4 transition hover:text-foreground hover:underline">
                  {label}
                </a>
              )
            )}
          </nav>
          <div className="flex items-center gap-2">
            <UserMenu />
            <button
              className="rounded-md p-2 text-muted hover:bg-surface hover:text-foreground lg:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="size-5">
                  <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="size-5">
                  <path fillRule="evenodd" d="M2 4.75A.75.75 0 0 1 2.75 4h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 4.75ZM2 10a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75A.75.75 0 0 1 2 10Zm0 5.25a.75.75 0 0 1 .75-.75h14.5a.75.75 0 0 1 0 1.5H2.75a.75.75 0 0 1-.75-.75Z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          </div>
          </div>
          {mobileMenuOpen && (
            <nav className="border-t border-border/50 bg-panel px-5 pb-4 pt-3 lg:hidden">
              <ul className="space-y-1">
                {mobileNavLinks.map(([label, href]) => (
                  <li key={href}>
                    {href.startsWith("legal:") ? (
                      <button
                        onClick={() => { openModal(href.slice(6)); setMobileMenuOpen(false); }}
                        className="block w-full rounded-md px-3 py-2 text-left text-sm text-muted hover:bg-surface hover:text-foreground"
                      >
                        {label}
                      </button>
                    ) : (
                      <a
                        href={appPath(href)}
                        onClick={() => setMobileMenuOpen(false)}
                        className="block rounded-md px-3 py-2 text-sm text-muted hover:bg-surface hover:text-foreground"
                      >
                        {label}
                      </a>
                    )}
                  </li>
                ))}
              </ul>
            </nav>
          )}
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
      <section className="border-b border-border/70 bg-gradient-to-b from-accent-soft/45 via-background to-background">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-12 md:gap-10 md:px-6 md:py-20 lg:grid-cols-[0.95fr_1.05fr] lg:items-center">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full bg-panel px-3 py-1 text-xs font-medium text-accent ring-1 ring-border/60">
              <span className="size-1.5 rounded-full bg-accent" />
              Local-first · Evidence-first
            </span>
            <h1 className="mt-5 max-w-3xl text-3xl font-semibold leading-tight sm:text-4xl md:text-5xl">
              A second brain that keeps evidence attached to every idea.
            </h1>
            <p className="mt-5 max-w-2xl text-sm leading-7 text-muted sm:text-base">
              BerryBrain turns notes, graph connections, insights, and source material into a private cognitive layer for studying, reasoning, and preserving context.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href={appPath("/signup")} className="rounded-md bg-accent px-5 py-3 text-sm font-medium text-black">
                Start securely
              </a>
              <a href={appPath("/demo")} className="rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface">
                Demo
              </a>
              <a href={appPath("/docs")} className="rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface">
                Read the docs
              </a>
            </div>
          </div>
          <div>
            <div className="overflow-hidden rounded-lg border border-border bg-panel shadow-sm">
              <div className="flex items-center justify-between border-b border-border bg-surface/70 px-4 py-3 text-xs text-muted">
                <span>Knowledge workspace</span>
                <span>Evidence-first</span>
              </div>
              <Image
                src={berryPrint}
                alt="BerryBrain home"
                width={900}
                height={560}
                priority
                sizes="(min-width: 1024px) 50vw, 100vw"
                className="h-auto w-full"
              />
            </div>
          </div>
        </div>
      </section>
      <section className="bg-panel/45">
        <div className="mx-auto grid w-full max-w-6xl gap-4 px-5 py-10 md:grid-cols-3 md:px-6">
          {[
            ["Private by design", "Local-first storage, optional cloud models, and visible provider traceability."],
            ["Security-aware", "Session cookies, CSRF checks, rate limits, lockout, and audit events protect account flows."],
            ["Graph-native", "Notes, concepts, attachments, insights, and gaps become connected records."],
          ].map(([title, body], i) => (
            <article key={title} className="rounded-xl border border-border bg-panel p-5 ring-1 ring-border/30">
              <span className="text-xs font-semibold text-accent">{String(i + 1).padStart(2, "0")}</span>
              <h2 className="mt-2 text-sm font-semibold">{title}</h2>
              <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
            </article>
          ))}
        </div>
      </section>
      <section className="border-y border-border/70 bg-surface/55">
        <div className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-14 md:grid-cols-[0.9fr_1.1fr] md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Cognitive layer</p>
            <h2 className="mt-3 text-3xl font-semibold">Not a chatbot. A structured thinking system.</h2>
            <p className="mt-4 text-sm leading-6 text-muted">
              The product surface is organized around durable knowledge records, not transient prompts.
            </p>
          </div>
          <div className="grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {[
              ["Knowledge Base", "Chunks notes and attachments for retrieval."],
              ["Knowledge Graph", "Connects notes, concepts, gaps, insights, and sources."],
              ["Semantic Data", "Answers questions about jobs, state, settings, and history."],
              ["Model Router", "Records provider, model, prompt version, status, and evidence."],
            ].map(([title, body]) => (
              <div key={title} className="border-t border-border/70 pt-4">
                <h3 className="text-sm font-semibold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
              </div>
            ))}
          </div>
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
      <section className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-14 md:px-6">
        <div className="mx-auto max-w-2xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Why BerryBrain</p>
          <h2 className="mt-3 text-3xl font-semibold">Not another notes app. Not a chatbot.</h2>
          <p className="mt-4 text-sm leading-6 text-muted">
            Most tools store text or generate text. BerryBrain connects them and keeps the source attached to every claim, so your second brain reasons instead of guessing.
          </p>
        </div>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            ["Obsidian", "Great for local Markdown, but linking is manual and AI is bolted on. BerryBrain builds the graph and traces evidence automatically."],
            ["Notion", "Flexible, but cloud-only by default and AI answers without showing its work. BerryBrain is local-first and evidence-first."],
            ["Plain folders", "Cheap, but no retrieval, no graph, no reasoning layer. BerryBrain turns files into a queryable second brain."],
          ].map(([tool, body], index) => (
            <article key={tool} className="rounded-lg border border-border bg-panel p-5">
              <span className="text-xs font-semibold text-accent">{String(index + 1).padStart(2, "0")}</span>
              <h3 className="mt-2 text-sm font-semibold">{tool}</h3>
              <p className="mt-3 text-sm leading-6 text-muted">{body}</p>
            </article>
          ))}
        </div>
          <div className="mt-14">
            <h3 className="text-center text-lg font-semibold">How BerryBrain compares</h3>
            <p className="mt-2 text-center text-sm text-muted">Illustrative scores (0–100) across what matters in a knowledge tool. BerryBrain is highlighted.</p>
            <div className="mt-8 space-y-4 md:hidden">
              {comparisonRows.map(([label, scores]) => (
                <div key={label} className="rounded-lg border border-border bg-panel p-4">
                  <p className="text-sm font-semibold">{label}</p>
                  <div className="mt-3 space-y-3">
                    {["BerryBrain", "Obsidian", "Notion", "Plain folders"].map((t, i) => (
                      <div key={t}>
                        <div className="flex items-center justify-between text-xs">
                          <span className={i === 0 ? "font-medium text-accent" : "text-muted"}>{t}</span>
                          <span className="text-muted">{scores[i]}</span>
                        </div>
                        <div className="mt-1 h-2 w-full rounded-full bg-surface">
                          <div className={`h-2 rounded-full ${i === 0 ? "bg-accent" : "bg-border"}`} style={{ width: `${scores[i]}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-8 hidden md:block">
              <table className="w-full border-separate border-spacing-y-3 text-sm">
                <thead>
                  <tr className="text-left text-muted">
                    <th className="pb-2 pr-4 font-medium">Capability</th>
                    {["BerryBrain", "Obsidian", "Notion", "Plain folders"].map((t) => (
                      <th key={t} className="pb-2 pr-4 font-medium">{t}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {comparisonRows.map(([label, scores]) => (
                    <tr key={label}>
                      <td className="pr-4 align-middle font-medium">{label}</td>
                      {scores.map((s, i) => (
                        <td key={i} className="pr-4 align-middle">
                          <div className="h-2.5 w-full rounded-full bg-surface">
                            <div className={`h-2.5 rounded-full ${i === 0 ? "bg-accent" : "bg-border"}`} style={{ width: `${s}%` }} />
                          </div>
                          <span className="mt-1 block text-xs text-muted">{s}</span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
      </section>
      <section className="border-t border-border/70 bg-accent/10">
        <div className="mx-auto flex w-full max-w-6xl flex-col items-center gap-5 px-5 py-14 text-center md:px-6">
          <h2 className="max-w-2xl text-3xl font-semibold">Start building your evidence-first second brain.</h2>
          <p className="max-w-xl text-sm leading-6 text-muted">Free to self-host. Private by default. Secure by design.</p>
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            <a href={appPath("/signup")} className="rounded-md bg-accent px-5 py-3 text-sm font-medium text-black">Create account</a>
            <a href={appPath("/demo")} className="rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface">Try the demo</a>
          </div>
        </div>
      </section>
    </>
  );
}

function safeNext(): string {
  const n = new URLSearchParams(window.location.search).get("next");
  return appPath(n && n.startsWith("/") && !n.startsWith("//") ? n : "/brain");
}

function validEmail(value: string): boolean {
  const e = value.trim().toLowerCase();
  if (e.length < 3 || e.length > 255) return false;
  const at = e.lastIndexOf("@");
  if (at < 1 || at === e.length - 1) return false;
  return e.slice(at + 1).includes(".");
}

function passwordErrors(p: string): string[] {
  const errs: string[] = [];
  if (p.length < 12) errs.push("Use at least 12 characters.");
  if (p.toLowerCase() === p || p.toUpperCase() === p) errs.push("Mix uppercase and lowercase letters.");
  if (!/\d/.test(p)) errs.push("Include at least one number.");
  return errs;
}

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const isSignup = mode === "signup";
  const apiUrl = getApiUrl();
  const [view, setView] = useState<"auth" | "forgot-request" | "forgot-confirm">("auth");
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
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
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
        body: JSON.stringify(isSignup ? { email, password, display_name: displayName } : { email, password, remember_me: keepSignedIn }),
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

  async function requestReset() {
    setBusy(true);
    setStatus("");
    try {
      if (!validEmail(email)) throw new Error("Enter a valid email address.");
      const normalized = email.trim().toLowerCase();
      const response = await fetch(`${apiUrl}/api/v1/auth/password-reset/request`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: normalized }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not start account recovery.");
      setView("forgot-confirm");
      setStatus("If the account exists, a recovery code was sent to that email.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not start account recovery.");
    } finally {
      setBusy(false);
    }
  }

  async function confirmReset() {
    setBusy(true);
    setStatus("");
    try {
      const normalized = email.trim().toLowerCase();
      if (!validEmail(normalized)) throw new Error("Enter a valid email address.");
      const perrs = passwordErrors(newPassword);
      if (perrs.length) throw new Error(perrs[0]);
      if (newPassword !== confirmPassword) throw new Error("The new passwords do not match.");
      if (!/^\d{6,12}$/.test(otp)) throw new Error("Enter the 6–12 digit code from your email.");
      const response = await fetch(`${apiUrl}/api/v1/auth/password-reset/confirm`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: normalized, code: otp, password: newPassword }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || "Could not reset password.");
      window.location.href = appPath("/login?reset=1");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not reset password.");
    } finally {
      setBusy(false);
    }
  }

  const leftTitle =
    view === "auth"
      ? isSignup
        ? "Start with verified email and 2FA."
        : "Log in with email verification."
      : "Recover your account";

  return (
    <PublicShell>
      <section className="mx-auto grid w-full max-w-5xl gap-8 px-5 py-12 md:grid-cols-[0.9fr_1fr] md:px-6 md:py-16">
        <div className="pt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
            {isSignup ? "Create account" : "Welcome back"}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">{leftTitle}</h1>
          <p className="mt-4 text-sm leading-6 text-muted">
            BerryBrain uses secure cookies, email OTP, CSRF protection, rate limits, and audit events. Support: contato@optlabs.com.br.
          </p>
        </div>
        <form className="rounded-lg border border-border bg-panel p-6" onSubmit={(event) => event.preventDefault()}>
          {view === "auth" && (
            <>
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
              {!isSignup && !awaitingCode && (
                <button type="button" onClick={() => { setStatus(""); setOtp(""); setView("forgot-request"); }} className="mt-4 text-xs text-accent underline-offset-4 hover:underline">
                  Forgot password?
                </button>
              )}
            </>
          )}

          {view === "forgot-request" && (
            <>
              <label className="block text-xs font-medium text-muted">Account email</label>
              <input required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="you@example.com" type="email" />
              <p className="mt-2 text-[11px] leading-5 text-muted">We will send a recovery code to this address if it matches an account.</p>
              <button disabled={busy || !email.trim()} type="button" onClick={requestReset} className="mt-6 w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-60">
                {busy ? "Working..." : "Send recovery code"}
              </button>
              <button type="button" onClick={() => { setStatus(""); setView("auth"); }} className="mt-3 w-full rounded-md border border-border px-4 py-2 text-sm">
                Back to login
              </button>
            </>
          )}

          {view === "forgot-confirm" && (
            <>
              <label className="block text-xs font-medium text-muted">Account email</label>
              <input required autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="you@example.com" type="email" />
              <label className="mt-4 block text-xs font-medium text-muted">Recovery code</label>
              <input value={otp} onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 12))} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="000000" inputMode="numeric" autoComplete="one-time-code" />
              <label className="mt-4 block text-xs font-medium text-muted">New password</label>
              <input required minLength={12} autoComplete="new-password" value={newPassword} onChange={(event) => setNewPassword(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="At least 12 characters" type="password" />
              <label className="mt-4 block text-xs font-medium text-muted">Confirm new password</label>
              <input required minLength={12} autoComplete="new-password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-accent" placeholder="Repeat the password" type="password" />
              <p className="mt-2 text-[11px] leading-5 text-muted">Use at least 12 characters with mixed letter case and a number.</p>
              <button disabled={busy || !email.trim() || !otp || !newPassword.trim() || !confirmPassword.trim()} type="button" onClick={confirmReset} className="mt-6 w-full rounded-md bg-accent px-4 py-2 text-sm font-medium text-black disabled:opacity-60">
                {busy ? "Working..." : "Reset password"}
              </button>
              <button type="button" onClick={() => { setStatus(""); setView("auth"); }} className="mt-3 w-full rounded-md border border-border px-4 py-2 text-sm">
                Back to login
              </button>
            </>
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
          <Image src={berrylogo} alt="BerryBrain" width={160} height={160} className="rounded-md grayscale" sizes="160px" />
          <p className="mt-4 max-w-sm text-sm leading-6 text-muted">
            A private, evidence-first second brain for notes, concepts, graph reasoning, and accountable AI assistance.
          </p>
          <p className="mt-4 text-xs text-muted">Support: contato@optlabs.com.br</p>
          <a
            href="https://github.com/imsouza/berrybrain"
            target="_blank"
            rel="noreferrer"
            aria-label="GitHub repository"
            className="mt-4 inline-flex size-9 items-center justify-center rounded-md border border-border text-muted transition-colors hover:bg-surface hover:text-foreground"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="size-5" aria-hidden="true">
              <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.71.08-.71 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.07.78 2.16v3.2c0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
            </svg>
          </a>
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
                      <a href={appPath(href)} className="text-sm text-muted hover:text-foreground">
                        {label}
                      </a>
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
