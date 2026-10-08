"use client";

import { usePathname } from "next/navigation";
import { NoteWorkspace } from "@/components/note-workspace";
import { useSecureWorkspace } from "@/hooks/use-secure-workspace";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const allowed = useSecureWorkspace(pathname);
  if (!allowed) return <main className="grid h-screen place-items-center text-sm text-muted">Checking secure session...</main>;
  const isBrainOrAsk = /\/(brain|ask)\/?$/.test(pathname);
  return <NoteWorkspace>{isBrainOrAsk ? undefined : children}</NoteWorkspace>;
}
