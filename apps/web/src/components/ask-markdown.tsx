"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Model output is untrusted: no raw HTML or automatic remote image requests. */
export function AskMarkdown({ content, className = "" }: { content: string; className?: string }) {
  return (
    <div className={`min-w-0 break-words text-sm leading-7 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        skipHtml
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
          code: ({ children, className }) => <code className={`rounded bg-surface px-1 py-0.5 font-mono text-[0.9em] ${className ?? ""}`}>{children}</code>,
          table: ({ children }) => <div className="my-4 overflow-x-auto"><table className="w-full border-collapse text-left text-sm">{children}</table></div>,
          th: ({ children }) => <th className="border border-border bg-surface px-3 py-2 font-semibold">{children}</th>,
          td: ({ children }) => <td className="border border-border px-3 py-2 align-top">{children}</td>,
          a: ({ href, children }) => <a href={href} className="text-accent underline underline-offset-2" target="_blank" rel="noopener noreferrer">{children}</a>,
          img: ({ alt }) => <span className="text-muted">[Imagem: {alt || "não carregada automaticamente"}]</span>,
          hr: () => <hr className="my-6 border-border" />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
