"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";
import { MermaidDiagram } from "./mermaid-diagram";
import { t } from "@/i18n";

export function MarkdownPreview({ content }: { content: string }) {
  if (!content) {
    return (
      <div className="prose h-full overflow-y-auto p-4 text-[15px] leading-[1.85] lg:p-10">
        <span style={{ color: "var(--color-muted)", opacity: 0.4 }}>{t("empty")}</span>
      </div>
    );
  }

  return (
    <div className="prose prose-slate h-full max-w-none overflow-y-auto p-4 text-[15px] leading-[1.85] lg:p-10">
      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { trust: false, strict: "warn", throwOnError: false, maxExpand: 1000 }]]}
        components={{ code: ({ className, children }) =>
          className === "language-mermaid"
            ? <MermaidDiagram source={String(children).replace(/\n$/, "")} />
            : <code className={className}>{children}</code> }}
      >{content}</ReactMarkdown>
    </div>
  );
}
