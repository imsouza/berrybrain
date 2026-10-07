"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { apiFetch, getApiUrl } from "@/contexts/workspace-context";

type Mode = "cloud" | "local";
type Provider = {
  id: string;
  label: string;
  mode: Mode;
  url: string;
  capabilities?: string[];
};
type ModelSlot = "main" | "embedding" | "judge" | "hipporag";
type ConfigurationGate = {
  required: boolean;
  valid: boolean;
  reason?: string;
};

const STEPS = [
  "Mode",
  "Provider",
  "Main model",
  "Embeddings",
  "Judge",
  "HippoRAG",
  "Test",
  "Summary",
];

export function RequiredAiSetup({ demo = false }: { demo?: boolean }) {
  const apiUrl = getApiUrl();
  const dialogRef = useRef<HTMLElement>(null);
  const [gate, setGate] = useState<ConfigurationGate>({
    required: false,
    valid: false,
    reason: "checking_configuration",
  });
  const [forcedOpen, setForcedOpen] = useState(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [mode, setMode] = useState<Mode>("local");
  const [providerId, setProviderId] = useState("");
  const [endpointUrl, setEndpointUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [models, setModels] = useState<string[]>([]);
  const [modelsByProvider, setModelsByProvider] = useState<Record<string, string[]>>({});
  const [slotProviders, setSlotProviders] = useState<Record<ModelSlot, string>>({
    main: "",
    embedding: "",
    judge: "",
    hipporag: "",
  });
  const [slots, setSlots] = useState<Record<ModelSlot, string>>({
    main: "",
    embedding: "",
    judge: "",
    hipporag: "",
  });
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [initializing, setInitializing] = useState(true);
  const [initializationError, setInitializationError] = useState("");
  const [error, setError] = useState("");
  const [capabilities, setCapabilities] = useState<Record<string, unknown>>({});

  const activeProviders = useMemo(
    () => providers.filter((provider) => provider.mode === mode),
    [mode, providers],
  );
  const activeProvider = providers.find((provider) => provider.id === providerId);
  const required = Boolean(gate.required);
  const open = !demo && (required || forcedOpen);

  const refreshGate = useCallback(async () => {
    const response = await apiFetch(`${apiUrl}/api/v1/bootstrap`);
    if (!response.ok) throw new Error("AI configuration status could not be loaded.");
    const payload = await response.json();
    setGate(payload.configurationGate || {
      required: true,
      valid: false,
      reason: "configuration_status_unavailable",
    });
  }, [apiUrl]);

  const loadSetup = useCallback(async (includeProviders = false) => {
    setInitializing(true);
    setInitializationError("");
    try {
      const bootstrapResponse = await apiFetch(`${apiUrl}/api/v1/bootstrap`);
      if (!bootstrapResponse.ok) {
        throw new Error("AI configuration status could not be loaded.");
      }
      const bootstrapPayload = await bootstrapResponse.json();
      const nextGate = bootstrapPayload.configurationGate || {
        required: true,
        valid: false,
        reason: "configuration_status_unavailable",
      };
      setGate(nextGate);
      if (nextGate.valid && !nextGate.required && !includeProviders) return;

      const providerResponse = await apiFetch(`${apiUrl}/api/v1/ai/providers`);
      if (!providerResponse.ok) {
        throw new Error("AI providers could not be loaded.");
      }
      const providerPayload = await providerResponse.json();
      const nextProviders = providerPayload.providers || [];
      setProviders(nextProviders);
      if (!nextProviders.length) throw new Error("No AI providers are available.");
    } catch (caught) {
      setInitializationError(
        caught instanceof Error ? caught.message : "AI setup could not be loaded.",
      );
      setGate((current) => current.valid ? current : {
        required: true,
        valid: false,
        reason: "configuration_status_unavailable",
      });
    } finally {
      setInitializing(false);
    }
  }, [apiUrl]);

  useEffect(() => {
    void loadSetup(false);
    const openSetup = () => {
      setForcedOpen(true);
      void loadSetup(true);
    };
    window.addEventListener("bb:open-ai-setup", openSetup);
    return () => {
      window.removeEventListener("bb:open-ai-setup", openSetup);
    };
  }, [loadSetup]);

  useEffect(() => {
    if (open) dialogRef.current?.focus();
  }, [open]);

  useEffect(() => {
    const options = providers.filter((provider) => provider.mode === mode);
    if (!options.length) return;
    if (!options.some((provider) => provider.id === providerId)) {
      selectProvider(options[0]);
    }
    // Provider list changes only after bootstrap; selection is handled atomically here.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, providers]);

  function selectProvider(provider: Provider) {
    setProviderId(provider.id);
    setEndpointUrl(provider.url);
    setApiKey(apiKeys[provider.id] || "");
    setModels([]);
    setModelsByProvider({});
    setSlotProviders({
      main: provider.id,
      embedding: provider.capabilities?.includes("embeddings") === false
        ? providers.find((item) => item.mode === provider.mode && item.capabilities?.includes("embeddings") !== false)?.id || ""
        : provider.id,
      judge: provider.id,
      hipporag: provider.id,
    });
    setSlots({ main: "", embedding: "", judge: "", hipporag: "" });
    setCapabilities({});
    setError("");
  }

  function setSlot(slot: ModelSlot, value: string) {
    setSlots((current) => ({ ...current, [slot]: value }));
    setCapabilities({});
    setError("");
  }

  function setSlotProvider(slot: ModelSlot, nextProviderId: string) {
    setSlotProviders((current) => ({ ...current, [slot]: nextProviderId }));
    setSlot(slot, "");
  }

  function setProviderKey(nextProviderId: string, value: string) {
    setApiKeys((current) => ({ ...current, [nextProviderId]: value }));
    if (nextProviderId === providerId) setApiKey(value);
  }

  async function loadModels(targetProviderId = providerId, slot?: ModelSlot) {
    const targetProvider = providers.find((provider) => provider.id === targetProviderId);
    const targetEndpoint = targetProviderId === providerId
      ? endpointUrl.trim()
      : String(targetProvider?.url || "").trim();
    if (!targetProviderId || !targetEndpoint) return;
    const cacheKey = slot ? `${targetProviderId}:${slot}` : targetProviderId;
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch(
        `${apiUrl}/api/v1/ai/providers/${encodeURIComponent(targetProviderId)}/models`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            endpoint_url: targetEndpoint,
            api_key: String(apiKeys[targetProviderId] || (targetProviderId === providerId ? apiKey : "")).trim(),
            capability: slot === "embedding" ? "embeddings" : undefined,
          }),
        },
      );
      const payload = await response.json();
      if (!response.ok) throw new Error(readError(payload));
      const ids = Array.from(
        new Set<string>(
          (payload.models || [])
            .map((model: { id?: unknown }) => String(model.id || "").trim())
            .filter(Boolean),
        ),
      );
      setModelsByProvider((current) => ({ ...current, [cacheKey]: ids }));
      if (!slot && targetProviderId === providerId) setModels(ids);
      if (!ids.length) {
        throw new Error(
          slot === "embedding"
            ? "The provider returned no models that passed the embeddings API probe."
            : "The provider returned no models.",
        );
      }
    } catch (caught) {
      setModelsByProvider((current) => ({ ...current, [cacheKey]: [] }));
      if (!slot && targetProviderId === providerId) setModels([]);
      setError(caught instanceof Error ? caught.message : "Models could not be loaded.");
    } finally {
      setBusy(false);
    }
  }

  function configuration() {
    return {
      schema_version: 2,
      mode,
      endpoint_url: endpointUrl.trim(),
      main: { provider_id: slotProviders.main, model_id: slots.main.trim() },
      embedding: { provider_id: slotProviders.embedding, model_id: slots.embedding.trim() },
      judge: {
        enabled: true,
        mode: "single_model",
        provider_id: slotProviders.judge,
        model_id: slots.judge.trim(),
      },
      hipporag: {
        enabled: true,
        provider_id: slotProviders.hipporag,
        model_id: slots.hipporag.trim(),
      },
      capability_snapshot: capabilities,
    };
  }

  async function validateConfiguration() {
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ai/configuration/validate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          configuration: configuration(),
          api_key: apiKey.trim(),
          api_keys: apiKeys,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(readError(payload));
      setCapabilities(payload.capabilitySnapshot || {});
      setStep(7);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Compatibility test failed.");
    } finally {
      setBusy(false);
    }
  }

  async function commitConfiguration() {
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch(`${apiUrl}/api/v1/ai/configuration`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          configuration: {
            ...configuration(),
            capability_snapshot: capabilities,
          },
          api_key: apiKey.trim(),
          api_keys: apiKeys,
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(readError(payload));
      setGate(payload.configurationGate || { required: false, valid: true });
      setForcedOpen(false);
      setApiKey("");
      setApiKeys({});
      await refreshGate();
      window.dispatchEvent(new Event("bb:ai-configuration-changed"));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Configuration could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  function canContinue() {
    if (step === 0) return activeProviders.length > 0 && !initializationError;
    if (step === 1) {
      return Boolean(
        providerId &&
          endpointUrl.trim() &&
          models.length,
      );
    }
    if (step === 2) return Boolean(slots.main.trim());
    if (step === 3) return Boolean(slots.embedding.trim());
    if (step === 4) return Boolean(slots.judge.trim());
    if (step === 5) return Boolean(slots.hipporag.trim());
    return true;
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/60 p-3 backdrop-blur-sm"
      role="presentation"
      onKeyDown={(event) => {
        if (event.key === "Escape" && required) event.preventDefault();
      }}
    >
      <section
        ref={dialogRef}
        tabIndex={-1}
        className="flex max-h-[94dvh] w-full max-w-3xl flex-col overflow-hidden rounded-md border border-border bg-panel shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-setup-title"
        aria-busy={initializing || busy}
      >
        <header className="border-b border-border px-5 py-4">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase text-accent">AI setup</p>
              <h2 id="ai-setup-title" className="mt-1 text-xl font-semibold">
                {STEPS[step]}
              </h2>
            </div>
            {!required && (
              <button
                type="button"
                className="rounded-md border border-border px-3 py-1.5 text-sm text-muted hover:bg-surface"
                onClick={() => setForcedOpen(false)}
              >
                Close
              </button>
            )}
          </div>
          <ol className="mt-4 grid grid-cols-4 gap-1 sm:grid-cols-8" aria-label="Setup progress">
            {STEPS.map((label, index) => (
              <li key={label}>
                <button
                  type="button"
                  disabled={index > step || busy}
                  onClick={() => setStep(index)}
                  className={`h-1.5 w-full rounded-sm ${
                    index <= step ? "bg-accent" : "bg-surface"
                  }`}
                  aria-label={label}
                  title={label}
                />
              </li>
            ))}
          </ol>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 py-5">
          {initializationError && (
            <div className="mb-5 rounded-md border border-danger/40 bg-danger/10 px-3 py-2 text-sm text-danger" role="alert">
              <p>{initializationError}</p>
              <button type="button" className="bb-action mt-3 px-3 py-1.5 text-xs" onClick={() => void loadSetup(true)} disabled={initializing}>
                {initializing ? "Checking..." : "Retry setup check"}
              </button>
            </div>
          )}
          {initializing && providers.length === 0 && !initializationError && (
            <div className="flex items-center gap-3 py-8 text-sm text-muted" role="status">
              <span className="size-5 animate-spin rounded-full border-2 border-border border-t-accent" />
              Loading AI providers and configuration status...
            </div>
          )}
          {step === 0 && (
            <div className="grid gap-3 sm:grid-cols-2">
              {(["local", "cloud"] as Mode[]).map((item) => (
                <button
                  type="button"
                  key={item}
                  onClick={() => setMode(item)}
                  className={`rounded-md border p-4 text-left ${
                    mode === item
                      ? "border-accent bg-accent-soft"
                      : "border-border bg-background hover:bg-surface"
                  }`}
                >
                  <span className="block text-base font-semibold">
                    {item === "local" ? "Local / Ollama" : "Cloud"}
                  </span>
                  <span className="mt-1 block text-sm text-muted">
                    {item === "local"
                      ? "Models run on this network."
                      : "Each AI role can use its own cloud provider."}
                  </span>
                </button>
              ))}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <Field label="Provider">
                <select
                  value={providerId}
                  onChange={(event) => {
                    const provider = providers.find(
                      (item) => item.id === event.target.value,
                    );
                    if (provider) selectProvider(provider);
                  }}
                  className="w-full rounded-md border border-border bg-background px-3 py-2"
                >
                  {activeProviders.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Provider URL">
                <input
                  value={endpointUrl}
                  onChange={(event) => setEndpointUrl(event.target.value)}
                  readOnly={activeProvider?.id !== "custom-cloud"}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 read-only:text-muted"
                />
              </Field>
              {mode === "cloud" && (
                <Field label="API key">
                  <input
                    type="password"
                    value={apiKey}
                    autoComplete="off"
                    onChange={(event) => setProviderKey(providerId, event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2"
                  />
                  <span className="mt-1 block text-xs text-muted">
                    Leave blank to reuse a saved key for this provider.
                  </span>
                </Field>
              )}
              <button
                type="button"
                onClick={() => void loadModels()}
                disabled={busy || !endpointUrl.trim()}
                className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? "Testing..." : "Load models"}
              </button>
              {models.length > 0 && (
                <p className="text-sm text-success">{models.length} models available.</p>
              )}
            </div>
          )}

          {step >= 2 && step <= 5 && (() => {
            const slot = (["main", "embedding", "judge", "hipporag"] as ModelSlot[])[step - 2];
            const selectedProvider = slotProviders[slot] || providerId;
            return (
              <SlotModelPicker
                label={STEPS[step]}
                slot={slot}
                mode={mode}
                providerId={selectedProvider}
                providers={slot === "embedding" ? activeProviders.filter((provider) => provider.capabilities?.includes("embeddings") !== false) : activeProviders}
                apiKey={apiKeys[selectedProvider] || ""}
                value={slots[slot]}
                models={modelsByProvider[`${selectedProvider}:${slot}`] || (slot === "embedding" ? [] : selectedProvider === providerId ? models : [])}
                busy={busy}
                lockProvider={slot === "main"}
                onProviderChange={(value) => setSlotProvider(slot, value)}
                onApiKeyChange={(value) => setProviderKey(selectedProvider, value)}
                onLoadModels={() => void loadModels(selectedProvider, slot)}
                onChange={(value) => setSlot(slot, value)}
              />
            );
          })()}

          {step === 6 && (
            <div className="space-y-4">
              <Summary mode={mode} providers={slotProviders} slots={slots} />
              <button
                type="button"
                onClick={validateConfiguration}
                disabled={busy}
                className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? "Testing configuration..." : "Run compatibility tests"}
              </button>
            </div>
          )}

          {step === 7 && (
            <div className="space-y-4">
              <Summary mode={mode} providers={slotProviders} slots={slots} />
              <p className="rounded-md border border-success/40 bg-success/10 px-3 py-2 text-sm text-success">
                Provider and model compatibility verified.
              </p>
            </div>
          )}

          {error && (
            <p className="mt-4 rounded-md border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-600">
              {error}
            </p>
          )}
        </div>

        <footer className="flex items-center justify-between border-t border-border px-5 py-4">
          <button
            type="button"
            onClick={() => setStep((current) => Math.max(0, current - 1))}
            disabled={step === 0 || busy || initializing}
            className="rounded-md border border-border px-4 py-2 text-sm disabled:opacity-40"
          >
            Back
          </button>
          {step < 6 && (
            <button
              type="button"
              onClick={() => setStep((current) => Math.min(7, current + 1))}
              disabled={!canContinue() || busy || initializing}
              className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
            >
              Continue
            </button>
          )}
          {step === 7 && (
            <button
              type="button"
              onClick={commitConfiguration}
              disabled={busy || !Object.keys(capabilities).length}
              className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-40"
            >
              {busy ? "Saving..." : "Finish setup"}
            </button>
          )}
        </footer>
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium">{label}</span>
      {children}
    </label>
  );
}

function SlotModelPicker({
  label,
  slot,
  mode,
  providerId,
  providers,
  apiKey,
  value,
  models,
  busy,
  lockProvider,
  onProviderChange,
  onApiKeyChange,
  onLoadModels,
  onChange,
}: {
  label: string;
  slot: ModelSlot;
  mode: Mode;
  providerId: string;
  providers: Provider[];
  apiKey: string;
  value: string;
  models: string[];
  busy: boolean;
  lockProvider: boolean;
  onProviderChange: (value: string) => void;
  onApiKeyChange: (value: string) => void;
  onLoadModels: () => void;
  onChange: (value: string) => void;
}) {
  const listId = `models-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <div className="space-y-4">
      <Field label={`${label} provider`}>
        <select
          value={providerId}
          disabled={lockProvider}
          onChange={(event) => onProviderChange(event.target.value)}
          className="w-full rounded-md border border-border bg-background px-3 py-2 disabled:text-muted"
        >
          {providers.map((provider) => (
            <option key={provider.id} value={provider.id}>{provider.label}</option>
          ))}
        </select>
      </Field>
      {providerId === "opencode-zen" && (
        <p className="text-xs leading-5 text-muted">
          OpenCode Zen: only Chat Completions-compatible models are supported here.
          For embeddings, select another cloud provider and its API key in the embeddings step.
        </p>
      )}
      {mode === "cloud" && (
        <Field label={`${label} provider API key`}>
          <input
            type="password"
            value={apiKey}
            autoComplete="off"
            onChange={(event) => onApiKeyChange(event.target.value)}
            placeholder="Leave blank to reuse a saved key"
            className="w-full rounded-md border border-border bg-background px-3 py-2"
          />
        </Field>
      )}
      <button
        type="button"
        onClick={onLoadModels}
        disabled={busy || !providerId}
        className="bb-action px-3 py-2 text-sm disabled:opacity-50"
      >
        {busy ? "Loading models..." : `Load ${label.toLowerCase()} models`}
      </button>
      <Field label={`${label} model`}>
        <input
          list={listId}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={slot === "embedding" ? "Select an embeddings-capable model" : "Select a chat model"}
          className="w-full rounded-md border border-border bg-background px-3 py-2"
        />
        <datalist id={listId}>
          {models.map((model) => (
            <option key={model} value={model} />
          ))}
        </datalist>
      </Field>
      {slot === "embedding" && (
        <p className="text-xs leading-5 text-muted">
          Changing this model requires a full vector reindex. Indexing and queries must use the same embeddings model.
        </p>
      )}
    </div>
  );
}

function Summary({
  mode,
  providers,
  slots,
}: {
  mode: Mode;
  providers: Record<ModelSlot, string>;
  slots: Record<ModelSlot, string>;
}) {
  return (
    <dl className="grid grid-cols-[minmax(7rem,auto)_1fr] gap-x-4 gap-y-2 rounded-md border border-border bg-background p-4 text-sm">
      <dt className="text-muted">Mode</dt><dd>{mode}</dd>
      <dt className="text-muted">Main</dt><dd className="break-all">{providers.main} / {slots.main}</dd>
      <dt className="text-muted">Embeddings</dt><dd className="break-all">{providers.embedding} / {slots.embedding}</dd>
      <dt className="text-muted">Judge</dt><dd className="break-all">{providers.judge} / {slots.judge}</dd>
      <dt className="text-muted">HippoRAG</dt><dd className="break-all">{providers.hipporag} / {slots.hipporag}</dd>
    </dl>
  );
}

function readError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Request failed.";
  const value = payload as { detail?: unknown; error?: unknown };
  if (typeof value.error === "string") return value.error;
  if (typeof value.detail === "string") return value.detail;
  if (value.detail && typeof value.detail === "object") {
    const detail = value.detail as { code?: unknown; models?: unknown; failures?: unknown; provider?: unknown };
    if (detail.code === "models_unavailable" && Array.isArray(detail.models)) {
      const models = detail.models.map((item) => {
        if (!item || typeof item !== "object") return String(item);
        const missing = item as Record<string, unknown>;
        return `${String(missing.slot || "slot")}: ${String(missing.provider || "provider")} / ${String(missing.model || "model")}`;
      });
      return `Models unavailable: ${models.join(", ")}`;
    }
    if (detail.code === "provider_key_required") {
      return `An API key is required for ${String(detail.provider || "the selected provider")}.`;
    }
    if (detail.code === "provider_compatibility_failed") {
      return `${String(detail.provider || "Provider")} compatibility test failed.`;
    }
    if (detail.code === "model_capability_mismatch" && Array.isArray(detail.failures)) {
      const failures = detail.failures
        .filter((item): item is Record<string, unknown> => Boolean(item && typeof item === "object"))
        .map((item) => {
          const slot = String(item.slot || "model");
          const model = String(item.model || "unknown");
          const capability = String(item.capability || "requested capability");
          const status = item.status ? `, HTTP ${String(item.status)}` : "";
          const reason = typeof item.reason === "string" ? item.reason : "Check the provider configuration and retry.";
          return `${slot}: ${model} — ${capability} validation failed${status}. ${reason}`;
        });
      if (failures.length) return failures.join("; ");
    }
  }
  return "Request failed.";
}
