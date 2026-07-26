export function labelize(value: string) {
  return value
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function humanNodeType(type?: string) {
  const labels: Record<string, string> = {
    note: "Note",
    concept: "Concept",
    topic: "Topic",
    topico: "Topic",
    entity: "Entity",
    entidade: "Entity",
    context: "Context",
    contexto: "Context",
    gap: "Knowledge gap",
    lacuna: "Knowledge gap",
    insight: "Insight",
    attachment: "Attachment",
    anexo: "Attachment",
    source: "Source",
    web_source: "Source",
  };
  return labels[(type || "").toLowerCase()] || labelize(type || "Node");
}

export function humanStatus(status?: string) {
  const labels: Record<string, string> = {
    suggested: "Needs review",
    confirmed: "Confirmed",
    ignored: "Ignored",
    stale: "Needs refresh",
    unvalidated: "Not checked",
    validated: "Checked",
  };
  return labels[(status || "suggested").toLowerCase()] || labelize(status || "suggested");
}

export function humanOrigin(origin?: string) {
  const value = (origin || "").toLowerCase();
  if (!value) return "System";
  if (value === "ai" || value.startsWith("subagent")) return "AI";
  if (value === "deterministic" || value === "system") return "System";
  if (value === "backlink") return "Note link";
  return labelize(origin || "System");
}

function parseMaybeJson(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) return value;
  try {
    return JSON.parse(trimmed);
  } catch {
    return value;
  }
}

export function formatEvidenceLabel(item: unknown): string {
  const parsed = typeof item === "string" ? parseMaybeJson(item) : item;
  if (typeof parsed === "string") {
    return parsed
      .replace(/[_-]+/g, " ")
      .replace(/\bexplainedConnections\b/g, "explained connections")
      .replace(/\bgraphNotes\b/g, "graph notes")
      .replace(/\bjobsByType\.[A-Z0-9_]+\b/g, "system activity")
      .replace(/\bGENERATE_NOTE_TITLE\b/g, "automatic title generation");
  }
  if (!parsed || typeof parsed !== "object") return "";
  const record = parsed as Record<string, unknown>;
  const parts = [
    record.title || record.label || record.source || "",
    record.text || record.reference || record.path || record.reason || "",
    record.whyRelevant || record.quoteOrSummary || "",
  ].filter(Boolean);
  return parts.join(": ") || "Evidence available in technical details.";
}
