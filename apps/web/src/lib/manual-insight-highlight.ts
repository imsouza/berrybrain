// Only manual creations, scoped to this workspace/browser. Never consume on fetch.
const memory = new Map<string, number[]>();
const key = (scope: string) => `bb_manual_insight_highlights:${scope}`;

export function pendingManualInsights(scope: string): number[] {
  try {
    const values: unknown = JSON.parse(localStorage.getItem(key(scope)) || "[]");
    if (Array.isArray(values)) return values.filter((id): id is number => Number.isSafeInteger(id) && id > 0);
  } catch { /* Storage may be unavailable; preserve the in-memory queue. */ }
  return memory.get(scope) || [];
}

function save(scope: string, ids: number[]) {
  memory.set(scope, ids);
  try { localStorage.setItem(key(scope), JSON.stringify(ids)); } catch { /* best effort */ }
}

export function queueManualInsight(scope: string, id: number) {
  if (!Number.isSafeInteger(id) || id <= 0) return;
  save(scope, [...new Set([...pendingManualInsights(scope), id])].slice(-100));
}

export function acknowledgeManualInsight(scope: string, id: number) {
  save(scope, pendingManualInsights(scope).filter(value => value !== id));
}
