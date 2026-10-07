export type JudgeSelection = { slot: string; provider: string; model: string };

export function judgeSelectionIssues(
  slots: JudgeSelection[], size: number, provider: string, generator: string,
): string[] {
  const issues: string[] = [];
  const seen = new Set<string>();
  const slotIds = new Set<string>();
  if (!provider) issues.push("Save the active AI provider before configuring the committee.");
  for (let index = 0; index < size; index += 1) {
    const slot = slots[index];
    const label = `Judge ${index + 1}`;
    const model = slot?.model.trim() || "";
    if (!model) { issues.push(`${label}: choose a model.`); continue; }
    if (model.toLowerCase() === generator.trim().toLowerCase()) issues.push(`${label}: the generator cannot judge its own output.`);
    if (seen.has(model.toLowerCase())) issues.push(`${label}: choose a different model; this one is already selected.`);
    if (slot.provider.trim() !== provider) issues.push(`${label}: provider changed. Select the model again for ${provider}.`);
    if (!slot.slot.trim() || slotIds.has(slot.slot.trim())) issues.push(`${label}: invalid or duplicate slot identifier.`);
    seen.add(model.toLowerCase());
    slotIds.add(slot.slot.trim());
  }
  return issues;
}
