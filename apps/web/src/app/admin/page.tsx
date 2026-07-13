"use client";

import { useEffect } from "react";

import { appPath } from "@/contexts/workspace-context";

export default function AdminRedirect() {
  useEffect(() => {
    window.location.href = appPath("/account");
  }, []);

  return (
    <main className="grid min-h-screen place-items-center bg-background text-sm text-muted">
      Legacy management route removed. Redirecting to account settings...
    </main>
  );
}
