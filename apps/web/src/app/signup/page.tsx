"use client";

import { useEffect } from "react";
import { appPath } from "@/contexts/workspace-context";

export default function Signup() {
  useEffect(() => {
    window.location.href = appPath("/setup");
  }, []);
  return (
    <main className="grid min-h-screen place-items-center bg-background text-sm text-muted">
      Redirecting to setup...
    </main>
  );
}
