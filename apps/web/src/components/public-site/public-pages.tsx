"use client";

import Image from "next/image";
import berrylogo from "../../../public/berrylogo.png";
import berryPrint from "../../../public/berrybrain-print1.png";
import berryPrint2 from "../../../public/berrybrain-print2.jpeg";
import berryPrint3 from "../../../public/berrybrain-print3.png";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { getApiUrl, appPath } from "@/contexts/workspace-context";

const GITHUB_URL = "https://github.com/imsouza/berrybrain";

const legalContent: Record<string, { title: string; body: string[] }> = {
  security: {
    title: "Security model",
    body: [
      "BerryBrain uses single local owner setup, secure session cookies, CSRF protection, rate limits, progressive lockout, and security audit events.",
      "Passwords use Argon2id when the production dependency set is installed.",
      "Sensitive operations require an authenticated local owner session.",
      "Security controls are designed to resist high-rate and replayed requests from any interception tool. The system blocks behavior, not tool names.",
      "Recommended production settings include HTTPS-only secure cookies, restricted CORS origins, a strong session secret, and a reverse proxy that exposes only the web entrypoint publicly.",
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
      "Self-hosted operators control access, correction, export, and deletion of their local instance data. Local vault files remain under the operator's storage control.",
      "Processing purposes include local authentication, instance security, note indexing, graph construction, retrieval, insight generation, and optional provider integrations configured by the local owner.",
      "For LGPD and GDPR requests, include enough context to verify ownership. Do not include passwords, API keys, tokens, or private notes in email.",
      "Privacy and data protection contact: contato@optlabs.com.br.",
    ],
  },
  terms: {
    title: "Terms",
    body: [
      "BerryBrain is a knowledge system for personal study, research, and note organization. Users are responsible for the material they store and process.",
      "The system may use local or configured cloud providers. Provider use must be configured by the local owner.",
      "Users should not store content they do not have the right to process. Automated insights, graph connections, and generated summaries are assistance outputs and should be reviewed before relying on them.",
      "Account misuse, abuse automation, credential stuffing, or attempts to bypass protective controls may lead to local lockout or instance restrictions.",
      "Support and account requests: contato@optlabs.com.br.",
    ],
  },
  contact: {
    title: "Contact",
    body: [
      "For support, security reports, privacy requests, or project questions, contact contato@optlabs.com.br.",
      "Please do not send passwords, API keys, private notes, or recovery codes by email.",
      "For support, include the page, browser, approximate time, and what action failed. For security reports, include reproducible steps and impact without accessing data that is not yours.",
      "For privacy requests, include enough context for the self-hosted operator or maintainer to understand the request.",
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
      ["Docs", "/docs"],
      ["GitHub", GITHUB_URL],
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

const mobileNavLinks = [
  ...nav,
  ["Security", "legal:security"],
  ["Privacy", "legal:privacy"],
  ["GDPR/LGPD", "legal:gdpr-lgpd"],
  ["Terms", "legal:terms"],
  ["Contact", "legal:contact"],
  ["GitHub", GITHUB_URL],
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
            <Image src={berrylogo} alt="BerryBrain" width={80} height={80} className="rounded-md" sizes="80px" />
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
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noreferrer"
              className="hidden items-center gap-2 rounded-md bg-accent px-3 py-2 text-xs font-semibold text-black hover:opacity-90 sm:inline-flex"
            >
              <svg viewBox="0 0 24 24" fill="currentColor" className="size-4" aria-hidden="true">
                <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.71.08-.71 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.07.78 2.16v3.2c0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
              </svg>
              GitHub
            </a>
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
                    ) : href.startsWith("http") ? (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        onClick={() => setMobileMenuOpen(false)}
                        className="block rounded-md px-3 py-2 text-sm text-muted hover:bg-surface hover:text-foreground"
                      >
                        {label}
                      </a>
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

const GithubIcon = ({ className = "size-4" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56v-2c-3.2.7-3.88-1.54-3.88-1.54-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.71.08-.71 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.55-.29-5.24-1.28-5.24-5.69 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.8 0c2.2-1.49 3.17-1.18 3.17-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.42-2.69 5.39-5.25 5.68.41.36.78 1.07.78 2.16v3.2c0 .31.21.68.8.56A11.51 11.51 0 0 0 23.5 12C23.5 5.73 18.27.5 12 .5Z" />
  </svg>
);

const DockerIcon = ({ className = "size-5" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className} aria-hidden="true">
    <path d="M13.1 7.5h2.4v2.4h-2.4V7.5Zm-3.1 0h2.4v2.4H10V7.5Zm-3 0h2.4v2.4H7V7.5Zm-3.1 3h2.4v2.4H3.9v-2.4Zm3.1 0h2.4v2.4H7v-2.4Zm3 0h2.4v2.4H10v-2.4Zm3.1 0h2.4v2.4h-2.4v-2.4Zm3.1 0h2.4v2.4h-2.4v-2.4ZM2.1 13.6h19.7c-.4 1.9-1.3 3.4-2.8 4.5-1.5 1.2-3.5 1.8-6 1.8H9.2c-2.1 0-3.8-.6-5.1-1.7-1.2-1.1-1.9-2.6-2-4.6Zm20.2-2.4c-.4-.3-.9-.4-1.4-.4-.6 0-1.1.2-1.5.6-.3.3-.5.6-.6 1h3.9c0-.5-.2-.9-.4-1.2Z" />
  </svg>
);

const DocsIcon = ({ className = "size-5" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
    <path d="M7 3.5h7l4 4V20a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 20V5A1.5 1.5 0 0 1 7.5 3.5Z" />
    <path d="M14 3.5V8h4" />
    <path d="M9 12h6M9 15h6M9 18h4" />
  </svg>
);

const GraphIcon = ({ className = "size-5" }: { className?: string }) => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className} aria-hidden="true">
    <circle cx="6" cy="7" r="2.5" />
    <circle cx="18" cy="6" r="2.5" />
    <circle cx="16" cy="18" r="2.5" />
    <circle cx="5" cy="17" r="2.5" />
    <path d="M8.4 6.8 15.6 6.2M7.5 9 14.4 16M7.4 16.8l6.2.8" />
  </svg>
);

function DiagramBox({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-lg border border-border bg-panel p-4">
      <div className="text-sm font-semibold">{title}</div>
      <div className="mt-2 text-xs leading-5 text-muted">{body}</div>
    </div>
  );
}

function DiagramArrow() {
  return <div className="flex justify-center text-accent" aria-hidden="true">↓</div>;
}

function CapabilityMark({ value }: { value: boolean }) {
  return (
    <span
      className={`inline-flex size-7 items-center justify-center rounded-full text-sm font-semibold ${
        value ? "bg-accent text-black" : "bg-surface text-muted"
      }`}
      aria-label={value ? "Included" : "Not included"}
    >
      {value ? "✓" : "–"}
    </span>
  );
}

function LandingContent() {
  const featureCards = [
    { title: "Markdown vault", body: "Real files remain portable, inspectable, and easy to back up.", icon: DocsIcon },
    { title: "Explainable graph", body: "Connections keep evidence, confidence, status, provider, and model trace.", icon: GraphIcon },
    { title: "Docker self-hosting", body: "Run web, API, and worker locally or behind your own reverse proxy.", icon: DockerIcon },
    { title: "GitHub-first", body: "Source, issues, deployment notes, and roadmap stay in the public repository.", icon: GithubIcon },
  ];
  const pipeline = [
    ["Capture", "Write Markdown notes and keep source files portable."],
    ["Parse", "Extract structure, links, headings, and metadata."],
    ["Assimilate", "Generate concepts, summaries, and retrieval chunks."],
    ["Connect", "Create explainable graph edges with evidence."],
    ["Review", "Turn gaps and insights into next study actions."],
  ];
  const comparisonColumns = [
    { label: "BerryBrain", score: 92, note: "Local-first cognitive layer" },
    { label: "Obsidian", score: 72, note: "Local Markdown workspace" },
    { label: "Notion", score: 58, note: "Cloud workspace" },
    { label: "Plain folders", score: 34, note: "Raw files" },
  ];
  const comparisonRows = [
    ["Local Markdown source", true, true, false, true],
    ["Self-hostable stack", true, false, false, true],
    ["Knowledge graph", true, true, false, false],
    ["Explainable AI insights", true, false, false, false],
    ["Evidence per connection", true, false, false, false],
    ["Retrieval / semantic search", true, false, true, false],
    ["Provider/model trace", true, false, false, false],
    ["Collaboration workspace", false, false, true, false],
    ["No vendor lock-in by default", true, true, false, true],
  ];
  return (
    <>
      <style jsx global>{`
        @keyframes bb-float-a {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(0, -10px, 0); }
        }
        @keyframes bb-float-b {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(8px, 8px, 0); }
        }
        @keyframes bb-float-c {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50% { transform: translate3d(-7px, -6px, 0); }
        }
      `}</style>
      <section className="overflow-hidden border-b border-border/70 bg-background">
        <div className="mx-auto grid min-h-[calc(100svh-73px)] w-full max-w-7xl items-center gap-8 px-5 py-14 md:grid-cols-[1.42fr_0.58fr] md:px-6 md:py-20">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-panel px-3 py-1 text-xs font-medium text-muted">
              <span className="size-1.5 rounded-full bg-accent" />
              Open source · Local-first · Evidence-first
            </span>
            <h1 className="mt-6 max-w-[940px] text-4xl font-semibold leading-[1.05] sm:text-5xl md:text-[4.1rem]">
              BerryBrain turns Markdown notes into an evidence-backed knowledge graph.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-muted md:text-lg">
              A self-hosted second brain for local notes, explainable graph reasoning, and auditable AI assistance. Free, open source, and designed around your own vault.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-md bg-accent px-5 py-3 text-sm font-semibold text-black shadow-sm transition hover:opacity-90"
              >
                <GithubIcon />
                View on GitHub
              </a>
              <a href={appPath("/docs")} className="inline-flex items-center justify-center gap-2 rounded-md border border-border bg-panel px-5 py-3 text-sm font-medium text-foreground hover:bg-surface">
                <DocsIcon className="size-4" />
                Read docs
              </a>
            </div>
            <div className="mt-12 grid max-w-xl grid-cols-2 gap-3 sm:grid-cols-4">
              {[
                ["License", "MIT"],
                ["Runtime", "Docker"],
                ["Vault", "Markdown"],
                ["Model", "Local/cloud"],
              ].map(([label, value]) => (
                <div key={label} className="border-l border-border bg-panel/70 px-4 py-3">
                  <div className="text-xs uppercase text-muted">{label}</div>
                  <div className="mt-1 text-sm font-semibold">{value}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="relative min-h-[330px] md:-ml-24 md:min-h-[470px]" aria-label="BerryBrain workspace previews">
            <div className="absolute left-0 top-10 w-[88%] overflow-hidden rounded-lg border border-border bg-panel shadow-2xl shadow-black/10 motion-safe:[animation:bb-float-a_7s_ease-in-out_infinite]">
              <Image
                src={berryPrint}
                alt="BerryBrain home screen"
                priority
                width={1100}
                height={690}
                sizes="(min-width: 768px) 48vw, 88vw"
                className="h-auto w-full"
              />
            </div>
            <div className="absolute right-0 top-0 w-[48%] overflow-hidden rounded-lg border border-border bg-panel shadow-xl shadow-black/10 motion-safe:[animation:bb-float-b_8s_ease-in-out_infinite]">
              <Image
                src={berryPrint2}
                alt="BerryBrain graph preview"
                width={760}
                height={520}
                sizes="(min-width: 768px) 22vw, 42vw"
                className="h-auto w-full"
              />
            </div>
            <div className="absolute bottom-6 right-4 w-[54%] overflow-hidden rounded-lg border border-border bg-panel shadow-xl shadow-black/10 motion-safe:[animation:bb-float-c_7.5s_ease-in-out_infinite]">
              <Image
                src={berryPrint3}
                alt="BerryBrain note preview"
                width={760}
                height={520}
                sizes="(min-width: 768px) 25vw, 48vw"
                className="h-auto w-full"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="bg-background">
        <div className="mx-auto grid w-full max-w-6xl gap-4 px-5 py-12 md:grid-cols-4 md:px-6">
          {featureCards.map((item) => {
            const Icon = item.icon;
            return (
              <article key={item.title} className="rounded-lg border border-border bg-panel p-5">
                <div className="flex size-10 items-center justify-center rounded-md bg-accent-soft text-accent">
                  <Icon />
                </div>
                <h2 className="mt-4 text-sm font-semibold">{item.title}</h2>
                <p className="mt-3 text-sm leading-6 text-muted">{item.body}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="border-y border-border/70 bg-[#182015] text-white">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-16 md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase text-[#CDE69A]">Workflow</p>
            <h2 className="mt-3 text-3xl font-semibold">A second brain that leaves a trail.</h2>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-white/68">
              BerryBrain does not hide generated knowledge. Every assisted artifact is designed to be reviewable before it becomes part of the graph.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-5">
            {pipeline.map(([step, body], index) => (
              <div key={step} className="relative rounded-lg border border-white/12 bg-white/7 p-4">
                <div className="flex items-center justify-between gap-3">
                  <span className="flex size-8 items-center justify-center rounded-full bg-[#CDE69A] text-xs font-semibold text-[#182015]">
                    {String(index + 1).padStart(2, "0")}
                  </span>
                  {index < pipeline.length - 1 && (
                    <span className="hidden text-[#CDE69A] md:block" aria-hidden="true">→</span>
                  )}
                </div>
                <div className="mt-5 text-sm font-semibold">{step}</div>
                <p className="mt-3 text-xs leading-5 text-white/62">{body}</p>
                {index < pipeline.length - 1 && (
                  <div className="mt-4 h-px bg-gradient-to-r from-[#CDE69A]/60 to-transparent md:hidden" aria-hidden="true" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-panel/45">
        <div className="mx-auto grid w-full max-w-6xl gap-10 px-5 py-16 md:grid-cols-[1.08fr_0.92fr] md:px-6">
          <div className="rounded-lg border border-border bg-background p-5">
            <div className="grid gap-4 text-sm">
              <DiagramBox title="Markdown vault" body="Local files, links, attachments" />
              <DiagramArrow />
              <div className="grid gap-3 sm:grid-cols-3">
                <DiagramBox title="API" body="Auth, notes, settings" />
                <DiagramBox title="Worker" body="Jobs, parsing, AI tasks" />
                <DiagramBox title="Models" body="Ollama or cloud provider" />
              </div>
              <DiagramArrow />
              <div className="grid gap-3 sm:grid-cols-3">
                <DiagramBox title="Knowledge Base" body="Chunks, metadata, retrieval" />
                <DiagramBox title="Knowledge Graph" body="Nodes, edges, evidence" />
                <DiagramBox title="Semantic Layer" body="Jobs, stats, diagnostics" />
              </div>
              <DiagramArrow />
              <DiagramBox title="BerryBrain UI" body="Home, graph, insights, monitor" />
            </div>
          </div>
          <div className="flex flex-col justify-center">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Architecture</p>
            <h2 className="mt-3 text-3xl font-semibold">Built as a self-hosted stack, not a closed service.</h2>
            <div className="mt-7 space-y-5">
              {[
                ["Next.js web", "Public project pages and the self-hosted workspace UI."],
                ["FastAPI backend", "Notes, setup, jobs, graph, insights, settings, and authenticated maintenance APIs."],
                ["Worker pipeline", "Background parsing, assimilation, embeddings, graph expansion, and insights."],
              ].map(([title, body]) => (
                <div key={title} className="border-t border-border pt-4">
                  <h3 className="text-sm font-semibold">{title}</h3>
                  <p className="mt-2 text-sm leading-6 text-muted">{body}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto grid w-full max-w-6xl gap-8 px-5 py-16 md:px-6">
        <div className="max-w-2xl">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Why it exists</p>
          <h2 className="mt-3 text-3xl font-semibold">A practical comparison against common knowledge workflows.</h2>
          <p className="mt-4 text-sm leading-7 text-muted">
            BerryBrain keeps Markdown portability, but adds provenance, graph reasoning, retrieval, and reviewable AI outputs.
          </p>
        </div>
        <div className="overflow-x-auto rounded-lg border border-border bg-panel">
          <div className="min-w-[860px]">
          <div className="grid grid-cols-[1.35fr_repeat(4,minmax(0,1fr))] border-b border-border bg-surface text-xs font-semibold uppercase tracking-[0.14em] text-muted">
            <div className="px-4 py-4">Capability</div>
            {comparisonColumns.map((column) => (
              <div key={column.label} className="border-l border-border px-4 py-4">
                <div className="text-foreground">{column.label}</div>
                <div className="mt-1 normal-case tracking-normal text-muted">{column.note}</div>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-[1.35fr_repeat(4,minmax(0,1fr))] border-b border-border">
            <div className="px-4 py-5 text-sm font-semibold">Knowledge fit score</div>
            {comparisonColumns.map((column) => (
              <div key={column.label} className="border-l border-border px-4 py-5">
                <div className="flex items-center justify-between gap-2 text-xs font-semibold">
                  <span>{column.score}%</span>
                  <span className="text-muted">fit</span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface">
                  <div className="h-full rounded-full bg-accent" style={{ width: `${column.score}%` }} />
                </div>
              </div>
            ))}
          </div>
          {comparisonRows.map(([capability, berrybrain, obsidian, notion, folders]) => (
            <div key={String(capability)} className="grid grid-cols-[1.35fr_repeat(4,minmax(0,1fr))] border-b border-border last:border-b-0">
              <div className="px-4 py-4 text-sm font-medium">{capability}</div>
              {[berrybrain, obsidian, notion, folders].map((value, index) => (
                <div key={index} className="flex items-center border-l border-border px-4 py-4">
                  <CapabilityMark value={Boolean(value)} />
                </div>
              ))}
            </div>
          ))}
          </div>
        </div>
        <p className="text-xs leading-5 text-muted">
          Sources checked: Obsidian Help documents Markdown files in a local vault and graph views; Notion Help documents cloud backup/export, AWS-hosted infrastructure, and data residency controls.
        </p>
      </section>

      <section className="border-t border-border/70 bg-accent/10">
        <div className="mx-auto grid w-full max-w-6xl gap-5 px-5 py-14 md:grid-cols-[1fr_auto] md:items-center md:px-6">
          <div>
            <h2 className="text-3xl font-semibold">Explore the source and self-host it your way.</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-muted">
              The public page is only informational. GitHub is the next step for code, issues, deployment notes, and contributions.
            </p>
          </div>
          <div className="flex flex-col gap-3 sm:flex-row md:justify-end">
            <a href={GITHUB_URL} target="_blank" rel="noreferrer" className="inline-flex items-center justify-center gap-2 rounded-md bg-accent px-5 py-3 text-sm font-semibold text-black hover:opacity-90">
              <GithubIcon />
              Open GitHub
            </a>
            <a href={appPath("/docs")} className="inline-flex items-center justify-center gap-2 rounded-md border border-border px-5 py-3 text-sm text-foreground hover:bg-surface">
              <DocsIcon className="size-4" />
              Documentation
            </a>
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

export function AuthPage({ mode: _mode }: { mode: "login" | "signup" }) {
  const isSignup = false;
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
      const endpoint = "/api/v1/auth/login";
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password, remember_me: keepSignedIn }),
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
      const endpoint = "/api/v1/auth/verify-2fa";
      const response = await fetch(`${apiUrl}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(
          { email, code: otp, challenge_id: challengeId, remember_me: keepSignedIn }
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
        ? "Public signup is disabled."
        : "Sign in to this local instance."
      : "Recover your account";

  return (
    <PublicShell>
      <section className="mx-auto grid w-full max-w-5xl gap-8 px-5 py-12 md:grid-cols-[0.9fr_1fr] md:px-6 md:py-16">
        <div className="pt-4">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">
            {isSignup ? "Setup" : "Welcome back"}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight">{leftTitle}</h1>
          <p className="mt-4 text-sm leading-6 text-muted">
            BerryBrain uses one local owner account, secure cookies, CSRF protection, rate limits, lockout, and audit events.
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
                {busy ? "Working..." : isSignup ? "Go to setup" : "Continue"}
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
              {false && !isSignup && !awaitingCode && (
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
            First run uses local setup. Password recovery is handled by the local owner or recovery tooling.
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
            ["Account", "Display name, password changes, active sessions, and logout-all."],
            ["Privacy", "Data export, deletion requests, local-first mode, external provider visibility, and consent history."],
            ["Security", "Local owner setup, session review, lockout events, and audit history."],
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
            href={GITHUB_URL}
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
                    ) : href.startsWith("http") ? (
                      <a href={href} target="_blank" rel="noreferrer" className="text-sm text-muted hover:text-foreground">
                        {label}
                      </a>
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
