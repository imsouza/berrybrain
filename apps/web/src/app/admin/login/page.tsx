"use client";

import { useEffect } from "react";

import { appPath } from "@/contexts/workspace-context";

export default function AdminLoginRedirect() {
  useEffect(() => {
    window.location.href = appPath("/login");
  }, []);

  return (
    <main className="grid min-h-screen place-items-center bg-background text-sm text-muted">
      Redirecting to the local account login...
    </main>
  );
}
