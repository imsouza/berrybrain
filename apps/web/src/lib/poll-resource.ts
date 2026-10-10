import { readResource } from "./read-resource";

/** Bounded, non-overlapping reads. Hidden tabs make no new requests. */
export function pollResource<T>(
  url: string,
  onData: (data: T) => void,
  intervalMs = 15_000,
  onError?: () => void,
): () => void {
  let stopped = false;
  let running = false;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const poll = async () => {
    if (stopped || running || document.hidden) return;
    running = true;
    try {
      const data = await readResource<T>(url);
      if (!stopped) onData(data);
    } catch {
      if (!stopped) onError?.();
    } finally {
      running = false;
      if (!stopped && !document.hidden) timer = setTimeout(poll, intervalMs);
    }
  };
  const visibilityChanged = () => {
    clearTimeout(timer);
    if (!document.hidden) void poll();
  };
  document.addEventListener("visibilitychange", visibilityChanged);
  void poll();
  return () => {
    stopped = true;
    clearTimeout(timer);
    document.removeEventListener("visibilitychange", visibilityChanged);
  };
}
