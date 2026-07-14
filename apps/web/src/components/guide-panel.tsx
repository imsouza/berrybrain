"use client";

import { GUIDE_STEPS, getLang, t } from "@/i18n";
import { useWorkspace } from "@/contexts/workspace-context";

type GuidePanelProps = { open?: boolean; onClose?: () => void };

export function GuidePanel({ open, onClose }: GuidePanelProps) {
  const w = useWorkspace();
  const isOpen = open ?? w.guideOpen;
  const handleClose = onClose ?? (() => w.setGuideOpen(false));
  if (!isOpen) return null;
  const steps = GUIDE_STEPS[getLang()] || GUIDE_STEPS["pt-BR"];

  return (
    <div className="fixed inset-0 z-[80] grid place-items-center bg-background/70 p-4 backdrop-blur-sm">
      <div className="bb-card bb-card--elevated flex max-h-[88vh] w-full max-w-2xl flex-col overflow-hidden">
        <div className="flex items-center justify-between border-b border-border/40 px-6 py-4">
          <h2 className="text-base font-semibold text-foreground">{t("guideTitle")}</h2>
          <button
            onClick={handleClose}
            className="rounded-lg p-1.5 text-muted hover:bg-surface hover:text-foreground"
            aria-label="Close"
          >
            <svg className="size-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
          </button>
        </div>

        <div className="space-y-6 overflow-y-auto px-6 py-5">
          {steps.map((step) => (
            <div key={step.num}>
              <div className="mb-1.5 flex items-center gap-2">
                <span className="grid size-5 place-items-center rounded-full bg-accent text-[10px] font-semibold text-white">
                  {step.num}
                </span>
                <h3 className="text-sm font-semibold text-foreground">{step.title}</h3>
              </div>
              <div
                className="pl-7 text-xs leading-relaxed text-muted [&_code]:rounded [&_code]:bg-surface [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-[11px] [&_kbd]:rounded [&_kbd]:bg-surface [&_kbd]:px-1.5 [&_kbd]:py-0.5 [&_kbd]:text-[10px] [&_strong]:text-foreground"
                dangerouslySetInnerHTML={{ __html: step.html }}
              />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between border-t border-border/40 px-6 py-4">
          <button
            onClick={() => {
              handleClose();
              window.dispatchEvent(new Event("bb:open-tour"));
            }}
            className="bb-action px-4 py-1.5 text-xs font-medium"
          >
            {t("guideViewTour")}
          </button>
          <button
            onClick={handleClose}
            className="bb-action px-4 py-1.5 text-xs font-medium"
          >
            {t("guideClose")}
          </button>
        </div>
      </div>
    </div>
  );
}
