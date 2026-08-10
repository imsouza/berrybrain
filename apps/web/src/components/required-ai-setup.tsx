"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { getApiUrl } from "@/contexts/workspace-context";

type Mode = "cloud" | "local";
type Provider = {
  id: string;
  label: string;
  mode: Mode;
  url: string;
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
  const [gate, setGate] = useState<ConfigurationGate | null>(null);
  const [forcedOpen, setForcedOpen] = useState(false);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [mode, setMode] = useState<Mode>("local");
  const [providerId, setProviderId] = useState("");
  const [endpointUrl, setEndpointUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [models, setModels] = useState<string[]>([]);
  const [slots, setSlots] = useState<Record<ModelSlot, string>>({
    main: "",
    embedding: "",
    judge: "",
    hipporag: "",
  });
  const [step, setStep] = useState(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [capabilities, setCapabilities] = useState<Record<string, unknown>>({});

  const activeProviders = useMemo(
    () => providers.filter((provider) => provider.mode === mode),
    [mode, providers],
  );
  const activeProvider = providers.find((provider) => provider.id === providerId);
  const required = Boolean(gate?.required);
  const open = !demo && (required || forcedOpen);

  const refreshGate = useCallback(async () => {
    const response = await fetch(`${apiUrl}/api/v1/bootstrap`, {
      credentials: "include",
    });
    if (!response.ok) return;
    const payload = await response.json();
    setGate(payload.configurationGate || null);
  }, [apiUrl]);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`${apiUrl}/api/v1/ai/providers`, { credentials: "include" }),
      fetch(`${apiUrl}/api/v1/bootstrap`, { credentials: "include" }),
    ])
      .then(async ([providerResponse, bootstrapResponse]) => {
        if (!active) return;
        if (providerResponse.ok) {
          const payload = await providerResponse.json();
          setProviders(payload.providers || []);
        }
        if (bootstrapResponse.ok) {
          const payload = await bootstrapResponse.json();
          setGate(payload.configurationGate || null);
        }
      })
      .catch(() => {});
    const openSetup = () => setForcedOpen(true);
    window.addEventListener("bb:open-ai-setup", openSetup);
    return () => {
      active = false;
      window.removeEventListener("bb:open-ai-setup", openSetup);
    };
  }, [apiUrl]);

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
    setModels([]);
    setSlots({ main: "", embedding: "", judge: "", hipporag: "" });
    setCapabilities({});
    setError("");
  }

  function setSlot(slot: ModelSlot, value: string) {
    setSlots((current) => ({ ...current, [slot]: value }));
    setCapabilities({});
    setError("");
  }

  async function loadModels() {
    if (!providerId || !endpointUrl.trim()) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(
        `${apiUrl}/api/v1/ai/providers/${encodeURIComponent(providerId)}/models`,
        {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            endpoint_url: endpointUrl.trim(),
            api_key: apiKey.trim(),
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
      setModels(ids);
      if (!ids.length) throw new Error("The provider returned no models.");
    } catch (caught) {
      setModels([]);
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
      main: { provider_id: providerId, model_id: slots.main.trim() },
      embedding: { provider_id: providerId, model_id: slots.embedding.trim() },
      judge: {
        enabled: true,
        mode: "single_model",
        provider_id: providerId,
        model_id: slots.judge.trim(),
      },
      hipporag: {
        enabled: true,
        provider_id: providerId,
        model_id: slots.hipporag.trim(),
      },
      capability_snapshot: capabilities,
    };
  }

  async function validateConfiguration() {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`${apiUrl}/api/v1/ai/configuration/validate`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          configuration: configuration(),
          api_key: apiKey.trim(),
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
      const response = await fetch(`${apiUrl}/api/v1/ai/configuration`, {
        method: "PUT",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          configuration: {
            ...configuration(),
            capability_snapshot: capabilities,
          },
          api_key: apiKey.trim(),
        }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(readError(payload));
      setGate(payload.configurationGate || { required: false, valid: true });
      setForcedOpen(false);
      setApiKey("");
      await refreshGate();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Configuration could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  function canContinue() {
    if (step === 0) return true;
    if (step === 1) {
      return Boolean(
        providerId &&
          endpointUrl.trim() &&
          (mode === "local" || apiKey.trim()) &&
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
        className="flex max-h-[94dvh] w-full max-w-3xl flex-col overflow-hidden rounded-md border border-border bg-panel shadow-2xl"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-setup-title"
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
                      : "Models run through one cloud provider."}
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
                    onChange={(event) => setApiKey(event.target.value)}
                    className="w-full rounded-md border border-border bg-background px-3 py-2"
                  />
                </Field>
              )}
              <button
                type="button"
                onClick={loadModels}
                disabled={busy || !endpointUrl.trim() || (mode === "cloud" && !apiKey.trim())}
                className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy ? "Testing..." : "Load models"}
              </button>
              {models.length > 0 && (
                <p className="text-sm text-success">{models.length} models available.</p>
              )}
            </div>
          )}

          {step >= 2 && step <= 5 && (
            <ModelPicker
              label={STEPS[step]}
              value={slots[(["main", "embedding", "judge", "hipporag"] as ModelSlot[])[step - 2]]}
              models={models}
              onChange={(value) =>
                setSlot(
                  (["main", "embedding", "judge", "hipporag"] as ModelSlot[])[step - 2],
                  value,
                )
              }
            />
          )}

          {step === 6 && (
            <div className="space-y-4">
              <Summary mode={mode} provider={activeProvider?.label || providerId} slots={slots} />
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
              <Summary mode={mode} provider={activeProvider?.label || providerId} slots={slots} />
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
            disabled={step === 0 || busy}
            className="rounded-md border border-border px-4 py-2 text-sm disabled:opacity-40"
          >
            Back
          </button>
          {step < 6 && (
            <button
              type="button"
              onClick={() => setStep((current) => Math.min(7, current + 1))}
              disabled={!canContinue() || busy}
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

function ModelPicker({
  label,
  value,
  models,
  onChange,
}: {
  label: string;
  value: string;
  models: string[];
  onChange: (value: string) => void;
}) {
  const listId = `models-${label.toLowerCase().replace(/\s+/g, "-")}`;
  return (
    <Field label={label}>
      <input
        list={listId}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Select a model"
        className="w-full rounded-md border border-border bg-background px-3 py-2"
      />
      <datalist id={listId}>
        {models.map((model) => (
          <option key={model} value={model} />
        ))}
      </datalist>
    </Field>
  );
}

function Summary({
  mode,
  provider,
  slots,
}: {
  mode: Mode;
  provider: string;
  slots: Record<ModelSlot, string>;
}) {
  return (
    <dl className="grid grid-cols-[minmax(7rem,auto)_1fr] gap-x-4 gap-y-2 rounded-md border border-border bg-background p-4 text-sm">
      <dt className="text-muted">Mode</dt><dd>{mode}</dd>
      <dt className="text-muted">Provider</dt><dd>{provider}</dd>
      <dt className="text-muted">Main</dt><dd className="break-all">{slots.main}</dd>
      <dt className="text-muted">Embeddings</dt><dd className="break-all">{slots.embedding}</dd>
      <dt className="text-muted">Judge</dt><dd className="break-all">{slots.judge}</dd>
      <dt className="text-muted">HippoRAG</dt><dd className="break-all">{slots.hipporag}</dd>
    </dl>
  );
}

function readError(payload: unknown): string {
  if (!payload || typeof payload !== "object") return "Request failed.";
  const value = payload as { detail?: unknown; error?: unknown };
  if (typeof value.error === "string") return value.error;
  if (typeof value.detail === "string") return value.detail;
  if (value.detail && typeof value.detail === "object") {
    const detail = value.detail as { code?: unknown; models?: unknown };
    if (detail.code === "models_unavailable" && Array.isArray(detail.models)) {
      return `Models unavailable: ${detail.models.join(", ")}`;
    }
  }
  return "Request failed.";
}
