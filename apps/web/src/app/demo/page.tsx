"use client";

import { appPath } from "@/contexts/workspace-context";
import { useEffect } from "react";

export default function Demo() {
  useEffect(() => {
    window.location.href = appPath("/docs");
  }, []);
  return (
    <main className="grid min-h-screen place-items-center bg-background text-sm text-muted">
      Redirecting to documentation...
    </main>
  );
}
