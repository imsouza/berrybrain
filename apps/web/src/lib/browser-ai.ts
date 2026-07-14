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
  if (!response.ok) throw new Error(payload.error || `Cloud AI request failed (HTTP ${response.status}).`);
  return payload as T;
}

export async function testBrowserCloudConnection(providerUrl: string, apiKey: string) {
  return providerRequest<{ connected: true; provider: string; providerUrl: string; models: string[] }>("models", {
    providerUrl,
    apiKey,
  });
}

export async function askBrowserCloud(
  messages: BrowserAiMessage[],
  config?: BrowserCloudConfig,
) {
  const activeConfig = config || await getBrowserCloudConfig();
  if (!activeConfig) throw new Error("Configure a cloud AI provider before using AI.");
  return providerRequest<{ content: string; provider: string; providerUrl: string; model: string; usage: unknown }>("chat", {
    providerUrl: activeConfig.apiUrl,
    apiKey: activeConfig.apiKey,
    model: activeConfig.model,
    messages,
  });
}
