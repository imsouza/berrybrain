import { NextRequest, NextResponse } from "next/server";
import {
  NVIDIA_NIM_URL,
  jsonHeaders,
  rejectCrossSite,
  safeJson,
  upstreamError,
  validApiKey,
} from "../provider";

type Message = { role: "system" | "user" | "assistant"; content: string };

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function validMessages(value: unknown): value is Message[] {
  if (!Array.isArray(value) || value.length === 0 || value.length > 12) return false;
  let total = 0;
  for (const item of value) {
    if (!item || typeof item !== "object") return false;
    const message = item as Partial<Message>;
    if (!message.role || !["system", "user", "assistant"].includes(message.role)) return false;
    if (typeof message.content !== "string" || !message.content.trim()) return false;
    total += message.content.length;
  }
  return total <= 60_000;
}

export async function POST(request: NextRequest) {
  if (rejectCrossSite(request)) {
    return NextResponse.json({ error: "Cross-site requests are not allowed." }, { status: 403, headers: jsonHeaders() });
  }
  try {
    const body = await safeJson(request);
    const model = typeof body.model === "string" ? body.model.trim() : "";
    if (!validApiKey(body.apiKey) || !model || model.length > 200 || !validMessages(body.messages)) {
      return NextResponse.json({ error: "Invalid NVIDIA NIM request." }, { status: 400, headers: jsonHeaders() });
    }
    const response = await fetch(`${NVIDIA_NIM_URL}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${body.apiKey.trim()}`,
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        model,
        messages: body.messages,
        temperature: 0.2,
        max_tokens: 1_800,
        stream: false,
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(90_000),
    });
    if (!response.ok) {
      return NextResponse.json({ error: await upstreamError(response) }, { status: response.status, headers: jsonHeaders() });
    }
    const payload = await response.json() as {
      choices?: Array<{ message?: { content?: unknown } }>;
      usage?: unknown;
    };
    const content = payload.choices?.[0]?.message?.content;
    if (typeof content !== "string" || !content.trim()) {
      return NextResponse.json({ error: "NVIDIA NIM returned an empty response." }, { status: 502, headers: jsonHeaders() });
    }
    return NextResponse.json({ content, provider: "nvidia-nim", model, usage: payload.usage || null }, { headers: jsonHeaders() });
  } catch (error) {
    const message = error instanceof Error && error.name !== "TimeoutError"
      ? error.message
      : "NVIDIA NIM did not respond in time.";
    return NextResponse.json({ error: message }, { status: 502, headers: jsonHeaders() });
  }
}
