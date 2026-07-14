import { getBrowserCloudConfig, type BrowserCloudConfig } from "@/lib/browser-storage";

const basePath = process.env.NEXT_PUBLIC_BERRYBRAIN_BASE_PATH || "";

export type BrowserAiMessage = {
  role: "system" | "user" | "assistant";
  content: string;
};

async function providerRequest<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(`${basePath}/api/browser-ai/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  const payload = await response.json().catch(() => ({})) as { error?: string };
  if (!response.ok) throw new Error(payload.error || `NVIDIA NIM request failed (HTTP ${response.status}).`);
  return payload as T;
}

export async function testBrowserNvidiaConnection(apiKey: string) {
  return providerRequest<{ connected: true; provider: "nvidia-nim"; models: string[] }>("models", { apiKey });
}

export async function askBrowserNvidia(
  messages: BrowserAiMessage[],
  config?: BrowserCloudConfig,
) {
  const activeConfig = config || await getBrowserCloudConfig();
  if (!activeConfig) throw new Error("Configure NVIDIA NIM before using AI.");
  return providerRequest<{ content: string; provider: "nvidia-nim"; model: string; usage: unknown }>("chat", {
    apiKey: activeConfig.apiKey,
    model: activeConfig.model,
    messages,
  });
}
