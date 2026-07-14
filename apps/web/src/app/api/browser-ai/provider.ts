import "server-only";

import { lookup } from "node:dns/promises";
import { isIP } from "node:net";
import type { NextRequest } from "next/server";

const BLOCKED_HOST_SUFFIXES = [".local", ".localhost", ".internal", ".home", ".lan"];

export class CloudProviderUrlError extends Error {}

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

function privateIpv4(address: string) {
  const parts = address.split(".").map(Number);
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) return true;
  const [a, b] = parts;
  return a === 0
    || a === 10
    || a === 127
    || (a === 100 && b >= 64 && b <= 127)
    || (a === 169 && b === 254)
    || (a === 172 && b >= 16 && b <= 31)
    || (a === 192 && b === 168)
    || (a === 198 && (b === 18 || b === 19))
    || a >= 224;
}

function privateIp(address: string) {
  const normalized = address.toLowerCase().split("%")[0];
  if (isIP(normalized) === 4) return privateIpv4(normalized);
  if (isIP(normalized) !== 6) return true;
  if (normalized.startsWith("::ffff:")) return privateIpv4(normalized.slice(7));
  return normalized === "::"
    || normalized === "::1"
    || normalized.startsWith("fc")
    || normalized.startsWith("fd")
    || /^fe[89ab]/.test(normalized)
    || normalized.startsWith("2001:db8:");
}

export async function resolveCloudProviderUrl(value: unknown) {
  if (typeof value !== "string" || value.length > 2_048) throw new CloudProviderUrlError("A valid cloud provider URL is required.");
  let url: URL;
  try {
    url = new URL(value.trim());
  } catch {
    throw new CloudProviderUrlError("A valid cloud provider URL is required.");
  }
  const hostname = url.hostname.toLowerCase().replace(/\.$/, "");
  if (
    url.protocol !== "https:"
    || url.username
    || url.password
    || (url.port && url.port !== "443")
    || hostname === "localhost"
    || BLOCKED_HOST_SUFFIXES.some((suffix) => hostname.endsWith(suffix))
  ) {
    throw new CloudProviderUrlError("Cloud provider URLs must use public HTTPS endpoints.");
  }
  let addresses: Array<{ address: string }>;
  try {
    addresses = isIP(hostname)
      ? [{ address: hostname }]
      : await lookup(hostname, { all: true, verbatim: true });
  } catch {
    throw new CloudProviderUrlError("Cloud provider hostname could not be resolved.");
  }
  if (!addresses.length || addresses.some(({ address }) => privateIp(address))) {
    throw new CloudProviderUrlError("Private or local cloud provider addresses are not allowed.");
  }
  url.hash = "";
  url.search = "";
  url.pathname = url.pathname.replace(/\/+$/, "");
  return url.toString().replace(/\/$/, "");
}

export function providerName(providerUrl: string) {
  return new URL(providerUrl).hostname;
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
    : `Cloud provider returned HTTP ${response.status}.`;
}
