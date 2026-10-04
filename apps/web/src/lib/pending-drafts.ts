// Memory only. Survives SPA remounts without writing note text to browser storage.
// Scope includes the authenticated session's CSRF token; never reuse across logins.
export type PendingDraft = { text: string; baseContent: string; baseHash: string };
const pending = new Map<string, PendingDraft>();

export function draftKey(api: string, sessionScope: string, path: string): string | null {
  return sessionScope ? JSON.stringify([api, sessionScope, path]) : null;
}
export function keepDraft(key: string | null, draft: PendingDraft) {
  if (!key) return;
  if (draft.text === draft.baseContent) pending.delete(key);
  else pending.set(key, draft);
}
export function readDraft(key: string | null): PendingDraft | undefined {
  return key ? pending.get(key) : undefined;
}
export function forgetDraft(key: string | null) {
  if (key) pending.delete(key);
}
export function acknowledgeDraft(key: string | null, savedText: string, savedHash: string) {
  if (!key) return;
  const current = pending.get(key);
  if (!current) return;
  if (current.text === savedText) pending.delete(key);
  else pending.set(key, { ...current, baseContent: savedText, baseHash: savedHash });
}
