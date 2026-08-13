"use client";

import { useVoicePrompt } from "@/hooks/use-voice-prompt";
import { Mic } from "lucide-react";

export function VoicePromptButton({
  value,
  onChange,
  className = "size-10",
}: {
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  const voice = useVoicePrompt({ value, onChange });
  const active = voice.state !== "idle";
  const title = voice.error || (active ? "Stop voice input" : "Use voice prompt");
  const levels = [0.52, 0.82, 1, 0.7, 0.44];

  return (
    <div className="relative shrink-0">
      <button
        type="button"
        className={`bb-action grid ${className} shrink-0 place-items-center p-0 ${active ? "bb-action--active text-accent" : ""}`}
        onClick={() => void voice.toggle()}
        aria-label={active ? "Stop voice input" : "Use voice prompt"}
        aria-pressed={active}
        title={title}
      >
        {active ? (
          <span className={`flex h-5 items-center gap-[2px] ${voice.listening && voice.level === 0 ? "bb-voice-wave--unmetered" : ""}`} aria-hidden="true">
            {levels.map((weight, index) => (
              <span
                key={weight}
                className={`bb-voice-wave-bar w-[2px] rounded-full bg-current transition-[height] duration-75 ${voice.state === "requesting" ? "animate-pulse" : ""}`}
                style={{ height: `${Math.max(4, 5 + voice.level * 14 * weight + (index % 2) * 2)}px` }}
              />
            ))}
          </span>
        ) : (
          <Mic className="size-4" aria-hidden="true" />
        )}
      </button>
      <span className="sr-only" aria-live="polite">
        {voice.error || (voice.state === "requesting" ? "Requesting microphone access" : voice.listening ? "Listening" : "")}
      </span>
      {voice.error && (
        <span role="status" className="absolute right-0 top-full z-[70] mt-2 w-72 rounded-md border border-border bg-panel px-3 py-2 text-left text-[11px] leading-4 text-foreground">
          <span className="block">{voice.error}</span>
          {voice.secureUrl && (
            <a className="mt-2 inline-flex font-semibold text-accent hover:text-accent-hover" href={voice.secureUrl}>
              Open secure BerryBrain
            </a>
          )}
        </span>
      )}
    </div>
  );
}
