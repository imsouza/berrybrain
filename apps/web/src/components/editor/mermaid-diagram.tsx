"use client";
/* SVG data images are intentional: no active HTML/script from a diagram. */
/* eslint-disable @next/next/no-img-element */

import { useEffect, useId, useState } from "react";

export function MermaidDiagram({ source }: { source: string }) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [image, setImage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    setImage("");
    setError("");
    const timer = window.setTimeout(async () => {
      const container = document.createElement("div");
      container.style.cssText = "position:absolute;left:-100000px;visibility:hidden";
      try {
        if (source.length > 20_000) throw new Error("Diagram too large (maximum 20,000 characters).");
        // Do not let diagrams fetch external assets while computing their layout.
        if (/\b(?:img|image|icon)\s*:/i.test(source)) throw new Error("External images/icons are disabled in diagrams.");
        const { default: mermaid } = await import("mermaid");
        if (cancelled) return;
        mermaid.initialize({ startOnLoad: false, securityLevel: "strict", maxTextSize: 20_000,
          maxEdges: 500, suppressErrorRendering: true, flowchart: { htmlLabels: false },
          secure: ["securityLevel", "startOnLoad", "maxTextSize", "maxEdges", "suppressErrorRendering", "flowchart"] });
        document.body.appendChild(container);
        const result = await mermaid.render(`bb-mermaid-${id}`, source, container);
        // An SVG image has no active script, link handlers, or HTML injection.
        if (!cancelled) setImage(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(result.svg)}`);
      } catch {
        if (!cancelled) setError("Diagram could not be rendered. Check Mermaid syntax and size; external images/icons are disabled.");
      } finally { container.remove(); }
    }, 300);
    return () => { cancelled = true; window.clearTimeout(timer); };
  }, [id, source]);
  return <span className="my-4 block overflow-x-auto rounded-lg border border-border bg-panel p-4" data-testid="mermaid-diagram">
    {image ? <img src={image} alt="Mermaid diagram" className="mx-auto max-w-full" />
      : <span role="status" className="text-xs text-muted">{error || "Rendering diagram…"}</span>}
    {error && <code className="mt-2 block whitespace-pre-wrap text-xs">{source}</code>}
  </span>;
}
