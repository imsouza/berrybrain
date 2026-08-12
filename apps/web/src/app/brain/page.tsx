"use client";

import { NoteWorkspace } from "@/components/note-workspace";
import { useSecureWorkspace } from "@/hooks/use-secure-workspace";

export default function Brain() {
  const allowed = useSecureWorkspace("/brain");

  if (!allowed) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">
        Checking secure session...
      </main>
    );
  }

  return <NoteWorkspace />;
}
