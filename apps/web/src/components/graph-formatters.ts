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
    entity: "Entity",
    context: "Context",
    gap: "Knowledge gap",
    insight: "Insight",
    attachment: "Attachment",
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
    deleted: "Deleted by user",
    corrected: "Corrected by user",
    restored: "Restored by user",
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
    return cleanEvidenceText(parsed
      .replace(/[_-]+/g, " ")
      .replace(/\bexplainedConnections\b/g, "explained connections")
      .replace(/\bgraphNotes\b/g, "graph notes")
      .replace(/\bjobsByType\.[A-Z0-9_]+\b/g, "system activity")
      .replace(/\bGENERATE_NOTE_TITLE\b/g, "automatic title generation"));
  }
  if (!parsed || typeof parsed !== "object") return "";
  const record = parsed as Record<string, unknown>;
  const parts = [
    record.title || record.label || record.source || "",
    record.text || record.reference || record.path || record.reason || "",
    record.whyRelevant || record.quoteOrSummary || "",
  ].filter((part) => Boolean(part) && String(part).trim().toLowerCase() !== "connections");
  return cleanEvidenceText(parts.join(": ")) || "Evidence available in technical details.";
}

function cleanEvidenceText(value: string) {
  return value
    .replace(/\b(connections)(?:\s*[:\-·]\s*\1\b)+/gi, "$1")
    .replace(/\bconnections(?:\s+connections\b)+/gi, "connections")
    .replace(/(?:^|\s)(connections)(?=\s*[:\-·]\s*$)/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}
