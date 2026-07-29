export type CloudProviderPreset = {
  id: string;
  label: string;
  url: string;
};

const configuredCloudUrl = process.env.NEXT_PUBLIC_BERRYBRAIN_CLOUD_API_URL || "";

const BUILT_IN_CLOUD_PROVIDERS: CloudProviderPreset[] = [
  { id: "nvidia-nim", label: "NVIDIA NIM", url: "https://integrate.api.nvidia.com/v1" },
  { id: "openai", label: "OpenAI", url: "https://api.openai.com/v1" },
  { id: "openrouter", label: "OpenRouter", url: "https://openrouter.ai/api/v1" },
  { id: "groq", label: "Groq", url: "https://api.groq.com/openai/v1" },
  { id: "deepseek", label: "DeepSeek", url: "https://api.deepseek.com" },
];

export const CLOUD_PROVIDER_PRESETS: CloudProviderPreset[] = [
  ...(configuredCloudUrl
    ? [{ id: "configured", label: "Configured provider", url: configuredCloudUrl }]
    : []),
  ...BUILT_IN_CLOUD_PROVIDERS.filter(
    (provider) => provider.url !== configuredCloudUrl,
  ),
];

export function providerIdForUrl(url: string): string {
  const trimmed = url.trim().replace(/\/$/, "");
  const match = CLOUD_PROVIDER_PRESETS.find(
    (provider) => provider.url.replace(/\/$/, "") === trimmed,
  );
  return match?.id || "custom";
}

export function providerLabelForUrl(url: string): string {
  const match = CLOUD_PROVIDER_PRESETS.find(
    (provider) => provider.url.replace(/\/$/, "") === url.trim().replace(/\/$/, ""),
  );
  return match?.label || "Custom provider";
}

export function normalizeModelIds(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  const ids = value
    .map((model) => {
      if (typeof model === "string") return model;
      if (model && typeof model === "object" && "id" in model) {
        return String((model as { id?: unknown }).id || "");
      }
      return "";
    })
    .map((id) => id.trim())
    .filter(Boolean);
  return Array.from(new Set(ids));
}
