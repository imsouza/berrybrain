"use client";

import { useEffect, useRef } from "react";
import { useWorkspace } from "@/contexts/workspace-context";

export function ResizeHandle() {
  const w = useWorkspace();
  const dragging = useRef(false);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragging.current) return;
      const nw = Math.max(220, Math.min(420, e.clientX));
      w.setSidebarWidth(nw);
      localStorage.setItem("bb_sidebar_w", String(nw));
    }
    function onUp() { dragging.current = false; document.body.style.cursor = ""; document.body.style.userSelect = ""; }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => { window.removeEventListener("mousemove", onMove); window.removeEventListener("mouseup", onUp); };
  }, [w.setSidebarWidth]);

  return (
    <div
      className="hidden w-1 flex-shrink-0 cursor-col-resize bg-transparent transition-colors hover:bg-accent/20 lg:block"
      onMouseDown={e => { e.preventDefault(); dragging.current = true; document.body.style.cursor = "col-resize"; document.body.style.userSelect = "none"; }}
      onDoubleClick={() => { w.setSidebarWidth(280); localStorage.setItem("bb_sidebar_w", "280"); }}
    />
  );
}
