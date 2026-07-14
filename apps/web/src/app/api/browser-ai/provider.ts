import "server-only";

import type { NextRequest } from "next/server";

export const NVIDIA_NIM_URL = "https://integrate.api.nvidia.com/v1";

export function rejectCrossSite(request: NextRequest) {
  const origin = request.headers.get("origin");
  if (!origin) return request.headers.get("sec-fetch-site") === "cross-site";
  try {
    const originHost = new URL(origin).host;
    const requestHost = request.headers.get("x-forwarded-host") || request.headers.get("host");
    return !requestHost || originHost !== requestHost;
  } catch {
    return true;
  }
}

export function validApiKey(value: unknown): value is string {
  return typeof value === "string" && value.trim().length >= 20 && value.trim().length <= 512;
}

export function jsonHeaders() {
  return {
    "Cache-Control": "no-store, max-age=0",
    "Content-Type": "application/json",
    "X-Content-Type-Options": "nosniff",
  };
}

export async function safeJson(request: NextRequest, maxBytes = 64_000): Promise<Record<string, unknown>> {
  const declaredLength = Number(request.headers.get("content-length") || "0");
  if (declaredLength > maxBytes) throw new Error("Request is too large.");
  const raw = await request.text();
  if (raw.length > maxBytes) throw new Error("Request is too large.");
  const parsed = JSON.parse(raw) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Invalid request body.");
  return parsed as Record<string, unknown>;
}

export async function upstreamError(response: Response) {
  const payload = await response.json().catch(() => null) as { detail?: unknown; message?: unknown; error?: unknown } | null;
  const candidate = payload?.detail || payload?.message || payload?.error;
  return typeof candidate === "string" && candidate.length <= 500
    ? candidate
    : `NVIDIA NIM returned HTTP ${response.status}.`;
}
