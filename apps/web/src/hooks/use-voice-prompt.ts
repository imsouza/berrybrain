"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "@/contexts/workspace-context";

type SpeechRecognitionResultLike = {
  length: number;
  [index: number]: { transcript?: string };
};

type SpeechRecognitionEventLike = {
  results?: {
    length: number;
    [index: number]: SpeechRecognitionResultLike;
  };
};

type SpeechRecognitionErrorLike = { error?: string; message?: string };

type SpeechRecognitionLike = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onerror: ((event: SpeechRecognitionErrorLike) => void) | null;
  onend: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  start: () => void;
  stop: () => void;
  abort?: () => void;
};

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;
export type VoicePromptState = "idle" | "requesting" | "listening";

function recognitionConstructor() {
  const browserWindow = window as typeof window & {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  };
  return browserWindow.SpeechRecognition || browserWindow.webkitSpeechRecognition;
}

function voiceErrorMessage(event: SpeechRecognitionErrorLike) {
  if (event.error === "not-allowed" || event.error === "service-not-allowed") {
    return "Microphone access was denied. Allow microphone access in browser settings and try again.";
  }
  if (event.error === "audio-capture") return "No working microphone was detected.";
  if (event.error === "network") return "Voice recognition could not reach the browser speech service.";
  if (event.error === "no-speech") return "No speech was detected. Try again and speak closer to the microphone.";
  return event.message || "Voice recognition stopped unexpectedly. Try again.";
}

function secureEquivalent(publicAppUrl: string) {
  try {
    const target = new URL(publicAppUrl);
    if (target.protocol !== "https:") return "";
    const basePath = process.env.NEXT_PUBLIC_BERRYBRAIN_BASE_PATH || "";
    const suffix = basePath && window.location.pathname.startsWith(basePath)
      ? window.location.pathname.slice(basePath.length)
      : "";
    target.pathname = `${target.pathname.replace(/\/$/, "")}${suffix}`;
    target.search = window.location.search;
    target.hash = window.location.hash;
    return target.toString();
  } catch {
    return "";
  }
}

export function useVoicePrompt({
  value,
  onChange,
  onError,
}: {
  value: string;
  onChange: (value: string) => void;
  onError?: (message: string) => void;
}) {
  const [state, setState] = useState<VoicePromptState>("idle");
  const [level, setLevel] = useState(0);
  const [error, setError] = useState("");
  const [secureUrl, setSecureUrl] = useState("");
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const animationFrameRef = useRef(0);
  const baseValueRef = useRef("");

  const publishError = useCallback((message: string) => {
    setError(message);
    onError?.(message);
  }, [onError]);

  const stopMeter = useCallback(() => {
    if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    animationFrameRef.current = 0;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    const context = audioContextRef.current;
    audioContextRef.current = null;
    if (context && context.state !== "closed") void context.close();
    setLevel(0);
  }, []);

  const stop = useCallback(() => {
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    try {
      recognition?.stop();
    } catch {
      recognition?.abort?.();
    }
    stopMeter();
    setState("idle");
  }, [stopMeter]);

  const startMeter = useCallback((stream: MediaStream) => {
    const AudioContextConstructor = window.AudioContext;
    if (!AudioContextConstructor) return;
    const context = new AudioContextConstructor();
    const analyser = context.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.72;
    context.createMediaStreamSource(stream).connect(analyser);
    const samples = new Uint8Array(analyser.frequencyBinCount);
    audioContextRef.current = context;
    const sample = () => {
      analyser.getByteFrequencyData(samples);
      const average = samples.reduce((sum, item) => sum + item, 0) / Math.max(1, samples.length);
      setLevel(Math.min(1, average / 72));
      animationFrameRef.current = requestAnimationFrame(sample);
    };
    sample();
  }, []);

  const start = useCallback(async () => {
    if (state !== "idle") {
      stop();
      return;
    }
    setError("");
    setSecureUrl("");
    onError?.("");
    let secureTarget = "";
    if (!window.isSecureContext) {
      try {
        const response = await apiFetch("/api/v1/status");
        const payload = response.ok ? await response.json() : {};
        secureTarget = secureEquivalent(String(payload.public_app_url || ""));
        setSecureUrl(secureTarget);
      } catch {
        secureTarget = "";
      }
    }
    const Recognition = recognitionConstructor();
    if (!Recognition) {
      publishError(
        !window.isSecureContext && secureTarget
          ? "This browser blocks voice input on local HTTP. Open the secure BerryBrain address."
          : "Voice input is not supported by this browser. Use a current Chromium-based browser.",
      );
      return;
    }
    setState("requesting");
    baseValueRef.current = value.trim();
    const recognition = new Recognition();
    recognitionRef.current = recognition;
    recognition.lang = navigator.language || "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setState("listening");
    recognition.onresult = (event) => {
      const transcripts: string[] = [];
      const results = event.results;
      for (let index = 0; results && index < results.length; index += 1) {
        const transcript = results[index]?.[0]?.transcript?.trim();
        if (transcript) transcripts.push(transcript);
      }
      const speech = transcripts.join(" ").trim();
      if (speech) onChange([baseValueRef.current, speech].filter(Boolean).join(" ").trim());
    };
    recognition.onerror = (event) => {
      publishError(
        !window.isSecureContext && secureTarget
          ? "This browser blocked microphone access on local HTTP. Open the secure BerryBrain address."
          : voiceErrorMessage(event),
      );
      recognitionRef.current = null;
      stopMeter();
      setState("idle");
    };
    recognition.onend = () => {
      recognitionRef.current = null;
      stopMeter();
      setState("idle");
    };

    try {
      recognition.start();
    } catch (caught) {
      recognitionRef.current = null;
      stopMeter();
      setState("idle");
      publishError(
        !window.isSecureContext && secureTarget
          ? "This browser blocked microphone access on local HTTP. Open the secure BerryBrain address."
          : caught instanceof Error ? caught.message : "Could not start voice input.",
      );
      return;
    }

    if (window.isSecureContext && navigator.mediaDevices?.getUserMedia) {
      void navigator.mediaDevices.getUserMedia({
        audio: { autoGainControl: true, echoCancellation: true, noiseSuppression: true },
      }).then((stream) => {
        if (recognitionRef.current !== recognition) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        streamRef.current = stream;
        startMeter(stream);
      }).catch((caught) => {
        if (recognitionRef.current !== recognition) return;
        const denied = caught instanceof DOMException && ["NotAllowedError", "SecurityError"].includes(caught.name);
        publishError(denied
          ? "Microphone access was denied. Allow microphone access in browser settings and try again."
          : caught instanceof Error ? caught.message : "Could not access the microphone.");
        recognition.abort?.();
        recognitionRef.current = null;
        stopMeter();
        setState("idle");
      });
    }
  }, [onChange, onError, publishError, startMeter, state, stop, stopMeter, value]);

  useEffect(() => () => {
    recognitionRef.current?.abort?.();
    stopMeter();
  }, [stopMeter]);

  return {
    error,
    level,
    listening: state === "listening",
    secureUrl,
    state,
    start,
    stop,
    toggle: start,
  };
}
