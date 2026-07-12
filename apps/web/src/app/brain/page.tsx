"use client";

import { useEffect, useState } from "react";
import { NoteWorkspace } from "@/components/note-workspace";
import { getApiUrl, appPath } from "@/contexts/workspace-context";

export default function Brain() {
  const apiUrl = getApiUrl();
  const [state, setState] = useState<"checking" | "allowed">("checking");

  useEffect(() => {
    let alive = true;
    fetch(`${apiUrl}/api/v1/setup/status`, { credentials: "include" })
      .then((response) => response.json())
      .then((setup) => {
        if (!alive) return null;
        if (setup.needsSetup) {
          window.location.href = appPath("/setup");
          return null;
        }
        return fetch(`${apiUrl}/api/v1/auth/me`, { credentials: "include" });
      })
      .then((response) => {
        if (!alive || !response) return;
        if (response.ok) setState("allowed");
        else window.location.href = appPath("/login?next=/brain");
      })
      .catch(() => {
        if (alive) window.location.href = appPath("/login?next=/brain");
      });
    return () => {
      alive = false;
    };
  }, []);

  if (state !== "allowed") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">
        Checking secure session...
      </main>
    );
  }

  return <NoteWorkspace />;
}
