// Share concurrent reads, not a persistent cache of private workspace data.
const pending = new Map<string, Promise<unknown>>();

export function readResource<T = any>(url: string, timeoutMs = 15_000): Promise<T> {
  const existing = pending.get(url);
  if (existing) return existing as Promise<T>;
  const request = (async () => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, { signal: controller.signal, credentials: "include" });
      if (!response.ok) throw new Error(`Request failed (HTTP ${response.status}).`);
      return await response.json() as T;
    } catch (error) {
      if (controller.signal.aborted) throw new Error("Request timed out. Retry when the server is available.");
      throw error;
    } finally {
      window.clearTimeout(timer);
      pending.delete(url);
    }
  })();
  pending.set(url, request);
  return request;
}
