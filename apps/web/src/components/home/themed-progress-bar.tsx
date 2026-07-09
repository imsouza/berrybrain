"use client";

type ProgressStatus = "idle" | "running" | "completed" | "failed" | "waiting_provider" | "offline" | "queued";

type Props = {
  value?: number;
  max?: number;
  indeterminate?: boolean;
  status?: ProgressStatus;
  label?: string;
  description?: string;
  size?: "sm" | "md";
};

export function ThemedProgressBar({
  value = 0,
  max = 100,
  indeterminate = false,
  status = "running",
  label,
  description,
  size = "md",
}: Props) {
  const percent = Math.max(0, Math.min(100, max > 0 ? (value / max) * 100 : 0));
  const height = size === "sm" ? "h-1.5" : "h-2.5";

  return (
    <div className="space-y-2">
      {(label || description) && (
        <div className="flex items-center justify-between gap-3 text-xs">
          <span className="font-medium">{label}</span>
          {description && <span className="text-muted/55">{description}</span>}
        </div>
      )}
      <div className={`${height} overflow-hidden rounded-full bg-[var(--color-accent-muted)] ring-1 ring-border/40`}>
        <div
          className={`${height} rounded-full transition-all duration-500 ${indeterminate ? "animate-progress-indeterminate" : ""}`}
          data-status={status}
          style={{
            width: indeterminate ? "35%" : `${percent}%`,
            background: statusColor(status),
          }}
        />
      </div>
    </div>
  );
}

function statusColor(status: ProgressStatus) {
  if (status === "completed" || status === "idle") return "var(--color-success)";
  if (status === "failed") return "var(--color-danger)";
  if (status === "waiting_provider" || status === "queued") return "var(--color-warning)";
  if (status === "offline") return "var(--color-muted)";
  return "var(--color-accent)";
}
