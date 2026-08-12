"use client";

import { NoteWorkspace } from "@/components/note-workspace";
import { useSecureWorkspace } from "@/hooks/use-secure-workspace";

export default function AskPage() {
  const allowed = useSecureWorkspace("/ask");

  if (!allowed) {
    return <main className="flex min-h-screen items-center justify-center bg-background text-sm text-muted">Checking secure session...</main>;
  }

  return <NoteWorkspace />;
}
