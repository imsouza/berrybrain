import { NextRequest, NextResponse } from "next/server";
import {
  NVIDIA_NIM_URL,
  jsonHeaders,
  rejectCrossSite,
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
      return NextResponse.json({ connected: false, error: "A valid NVIDIA NIM API key is required." }, { status: 400, headers: jsonHeaders() });
    }
    const response = await fetch(`${NVIDIA_NIM_URL}/models`, {
      headers: { Authorization: `Bearer ${body.apiKey.trim()}`, Accept: "application/json" },
      cache: "no-store",
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
    return NextResponse.json({ connected: true, provider: "nvidia-nim", models }, { headers: jsonHeaders() });
  } catch (error) {
    const message = error instanceof Error && error.name !== "TimeoutError"
      ? error.message
      : "NVIDIA NIM did not respond in time.";
    return NextResponse.json({ connected: false, error: message }, { status: 502, headers: jsonHeaders() });
  }
}
