// Share concurrent reads only within the same browser session. The CSRF cookie
// changes with login; a request started before logout must not be reused after it.
const pending = new Map<string, Promise<unknown>>();

export function currentWorkspaceReadScope(): string | null {
  if (typeof document === "undefined") return null;
  const token = document.cookie.match(/(?:^|;\s*)bb_csrf=([^;]+)/)?.[1];
  return token || null;
}

export function readResource<T = any>(url: string, timeoutMs = 15_000): Promise<T> {
  const scope = currentWorkspaceReadScope();
  // Unauthenticated requests have no private data to share, so skip deduplication.
  const key = scope ? `${scope}\0${timeoutMs}\0${url}` : null;
  const existing = key ? pending.get(key) : undefined;
  if (existing) return existing as Promise<T>;
  const request = (async () => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { signal: controller.signal, credentials: "include" });
      if (!response.ok) throw new Error(`Request failed (HTTP ${response.status}).`);
      const payload = await response.json() as T;
      if (scope !== currentWorkspaceReadScope()) {
        throw new Error("Session changed during request.");
      }
      return payload;
    } catch (error) {
      if (controller.signal.aborted) throw new Error("Request timed out. Retry when the server is available.");
      throw error;
    } finally {
      window.clearTimeout(timer);
      if (key) pending.delete(key);
    }
  })();
  if (key) pending.set(key, request);
  return request;
}
