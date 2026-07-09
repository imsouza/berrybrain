"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function MarkdownPreview({ content }: { content: string }) {
  if (!content) {
    return (
      <div className="prose overflow-y-auto p-6 lg:p-10 text-[15px] leading-[1.85]">
        <span style={{ color: "var(--color-muted)", opacity: 0.4 }}>Vazio</span>
      </div>
    );
  }

  return (
    <div className="prose prose-slate max-w-none overflow-y-auto p-6 lg:p-10 text-[15px] leading-[1.85]">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
