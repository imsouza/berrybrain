"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { appPath } from "@/contexts/workspace-context";
import { MermaidDiagram } from "./editor/mermaid-diagram";

export type AskReference = {
  kind: "note" | "graph_node" | "attachment";
  id: number;
  stableId: string;
  title: string;
  path?: string;
  nodeType?: string;
  noteTitle?: string;
  vaultId?: string;
  current: boolean;
  evidenceIds: string[];
  sourceNotes?: Array<{ id: number; title: string; path: string; vaultId?: string }>;
};

export function askNoteHref(path: string): string {
  return appPath(`/brain?note=${encodeURIComponent(path)}`);
}

export function askReferenceHref(reference: AskReference): string | null {
  if (reference.kind === "note" && reference.path) {
    return askNoteHref(reference.path);
  }
  if (reference.kind === "attachment" && reference.path) {
    return askNoteHref(reference.path);
  }
  if (reference.kind === "graph_node" && Number.isSafeInteger(reference.id) && reference.id > 0) {
    return appPath(`/graph/nodes/${reference.id}`);
  }
  return null;
}

function verifiedReference(marker: string, references: AskReference[]): AskReference | undefined {
  const resolved = /^resolved:(note|graph_node|attachment):([1-9]\d*)$/.exec(marker);
  if (resolved) {
    const id = Number(resolved[2]);
    return Number.isSafeInteger(id)
      ? references.find((item) => item.kind === resolved[1] && item.id === id)
      : undefined;
  }
  return references.find((item) => item.evidenceIds.includes(marker));
}

/** Model output is untrusted: no raw HTML or automatic remote image requests. */
export function AskMarkdown({ content, className = "", references = [] }: { content: string; className?: string; references?: AskReference[] }) {
  return (
    <div className={`min-w-0 break-words text-sm leading-7 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { trust: false, strict: "warn", throwOnError: false, maxExpand: 1000 }]]}
        skipHtml
        urlTransform={(url) => url.startsWith("bbref:") ? url : ""}
        components={{
          h1: ({ children }) => <h2 className="mb-4 mt-6 text-xl font-semibold first:mt-0">{children}</h2>,
          h2: ({ children }) => <h3 className="mb-3 mt-6 text-lg font-semibold first:mt-0">{children}</h3>,
          h3: ({ children }) => <h4 className="mb-2 mt-4 text-base font-semibold">{children}</h4>,
          h4: ({ children }) => <h5 className="mb-2 mt-4 font-semibold">{children}</h5>,
          p: ({ children }) => <p className="my-3 first:mt-0 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="my-3 list-disc space-y-1 pl-6">{children}</ul>,
          ol: ({ children, start }) => <ol start={start} className="my-3 list-decimal space-y-1 pl-6">{children}</ol>,
          blockquote: ({ children }) => <blockquote className="my-4 border-l-2 border-accent/50 pl-4 text-muted">{children}</blockquote>,
          pre: ({ children }) => <pre className="my-4 overflow-x-auto rounded-lg border border-border bg-surface p-4 text-xs leading-6">{children}</pre>,
          code: ({ children, className }) => className === "language-mermaid"
            ? <MermaidDiagram source={String(children).replace(/\n$/, "")} />
            : <code className={`rounded bg-surface px-1 py-0.5 font-mono text-[0.9em] ${className ?? ""}`}>{children}</code>,
          table: ({ children }) => <div className="my-4 overflow-x-auto"><table className="w-full border-collapse text-left text-sm">{children}</table></div>,
          th: ({ children }) => <th className="border border-border bg-surface px-3 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border border-border px-3 py-2 align-top">{children}</td>,
          a: ({ href, children }) => {
            const evidenceId = href?.startsWith("bbref:") ? href.slice(6) : "";
            const reference = evidenceId ? verifiedReference(evidenceId, references) : undefined;
            const target = reference ? askReferenceHref(reference) : null;
            return target
              ? <a href={target} className="text-accent underline underline-offset-2 focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent" aria-label={`Open ${reference?.kind === "note" ? "note" : reference?.kind === "attachment" ? "attachment in note" : "graph node"}: ${reference?.title || "reference"}`}>{reference?.title || "Reference"}</a>
              : <span title="Unverified link; verified BerryBrain references appear below">{children}</span>;
          },
          img: ({ alt }) => <span className="text-muted">[Imagem: {alt || "não carregada automaticamente"}]</span>,
          hr: () => <hr className="my-6 border-border" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
