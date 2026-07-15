import { NextRequest, NextResponse } from "next/server";
import {
  CloudProviderUrlError,
  jsonHeaders,
  providerName,
  rejectCrossSite,
  resolveCloudProviderUrl,
  safeJson,
  upstreamError,
  validApiKey,
} from "../provider";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  if (rejectCrossSite(request)) {
    return NextResponse.json({ connected: false, error: "Cross-site requests are not allowed." }, { status: 403, headers: jsonHeaders() });
  }
  try {
    const body = await safeJson(request, 4_096);
    if (!validApiKey(body.apiKey)) {
      return NextResponse.json({ connected: false, error: "A valid cloud API key is required." }, { status: 400, headers: jsonHeaders() });
    }
    const providerUrl = await resolveCloudProviderUrl(body.providerUrl);
    const response = await fetch(`${providerUrl}/models`, {
      headers: { Authorization: `Bearer ${body.apiKey.trim()}`, Accept: "application/json" },
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(15_000),
    });
    if (!response.ok) {
      return NextResponse.json({ connected: false, error: await upstreamError(response) }, { status: response.status, headers: jsonHeaders() });
    }
    const payload = await response.json() as { data?: Array<{ id?: unknown }> };
    const models = (payload.data || [])
      .map((item) => (typeof item.id === "string" ? item.id : ""))
      .filter(Boolean)
      .slice(0, 500);
    return NextResponse.json({ connected: true, provider: providerName(providerUrl), providerUrl, models }, { headers: jsonHeaders() });
  } catch (error) {
    const message = error instanceof Error && error.name !== "TimeoutError"
      ? error.message
      : "Cloud provider did not respond in time.";
    return NextResponse.json({ connected: false, error: message }, { status: error instanceof CloudProviderUrlError ? 400 : 502, headers: jsonHeaders() });
  }
}
