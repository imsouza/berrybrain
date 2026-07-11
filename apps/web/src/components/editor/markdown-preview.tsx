"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
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
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
