"use client";

import Script from "next/script";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";

const OFFICIAL_GOOGLE_ANALYTICS_ID = "G-36YL9QLC5K";
const ANALYTICS_CONSENT_KEY = "bb_analytics_consent";

declare global {
  interface Window {
    dataLayer?: unknown[];
    gtag?: (...args: unknown[]) => void;
  }
}

function analyticsIdForCurrentDeployment() {
  const configuredId = process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID?.trim();
  if (configuredId && /^G-[A-Z0-9]{6,20}$/i.test(configuredId)) return configuredId;
  if (typeof window === "undefined") return "";
  const hostname = window.location.hostname.toLowerCase();
  return hostname === "optlabs.com.br" || hostname === "www.optlabs.com.br"
    ? OFFICIAL_GOOGLE_ANALYTICS_ID
    : "";
}

function GoogleAnalytics({ enabled }: { enabled: boolean }) {
  const [analyticsId, setAnalyticsId] = useState("");
  const [consent, setConsent] = useState<"granted" | "denied" | null>(null);
  const configured = useRef(false);

  useEffect(() => {
    setAnalyticsId(enabled ? analyticsIdForCurrentDeployment() : "");
    const readConsent = () => {
      const saved = window.localStorage.getItem(ANALYTICS_CONSENT_KEY);
      setConsent(saved === "granted" || saved === "denied" ? saved : null);
    };
    readConsent();
    window.addEventListener("bb:analytics-consent", readConsent);
    return () => window.removeEventListener("bb:analytics-consent", readConsent);
  }, [enabled]);

  const choose = (value: "granted" | "denied") => {
    const wasGranted = consent === "granted";
    window.localStorage.setItem(ANALYTICS_CONSENT_KEY, value);
    setConsent(value);
    if (wasGranted && value === "denied") window.location.reload();
  };

  const configure = useCallback(() => {
    if (!analyticsId || configured.current) return;
    window.dataLayer = window.dataLayer || [];
    window.gtag = (...args: unknown[]) => window.dataLayer?.push(args);
    window.gtag("js", new Date());
    window.gtag("config", analyticsId, {
      anonymize_ip: true,
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
    });
    configured.current = true;
  }, [analyticsId]);

  if (!analyticsId) return null;

  return (
    <>
      {consent === "granted" && (
        <>
          <Script
            id="berrybrain-google-analytics"
            src={`https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(analyticsId)}`}
            strategy="afterInteractive"
            onLoad={configure}
            onReady={configure}
          />
        </>
      )}
      {consent === null && (
        <aside
          className="fixed bottom-4 left-4 z-[120] max-w-sm border border-black bg-panel p-4 text-foreground shadow-[4px_4px_0_var(--color-brand-red)]"
          aria-label="Analytics consent"
        >
          <p className="text-sm font-semibold">Privacy choices</p>
          <p className="mt-2 text-xs leading-5 text-muted">
            BerryBrain uses optional Google Analytics on the official website to understand
            aggregate usage. It stays disabled until you allow it.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button className="bb-action px-3 py-1.5 text-xs font-medium" onClick={() => choose("granted")}>
              Allow analytics
            </button>
            <button className="bb-action px-3 py-1.5 text-xs font-medium" onClick={() => choose("denied")}>
              Decline
            </button>
          </div>
        </aside>
      )}
    </>
  );
}

export function ThirdPartyIntegrations() {
  const pathname = usePathname();
  const privateRouteSegments = new Set([
    "brain",
    "activity",
    "insights",
    "notifications",
    "reviews",
    "account",
  ]);
  const isKnowledgeWorkspace = pathname
    .split("/")
    .filter(Boolean)
    .some((segment) => privateRouteSegments.has(segment));

  return (
    <>
      <GoogleAnalytics enabled={!isKnowledgeWorkspace} />
      <a
        href="https://ko-fi.com/berrybrain"
        target="_blank"
        rel="noopener noreferrer"
        className={`bb-action fixed right-4 z-[70] px-3 py-2 text-xs font-semibold ${
          isKnowledgeWorkspace ? "bottom-4" : "bottom-56 sm:bottom-4"
        }`}
        aria-label="Donate to BerryBrain on Ko-fi"
      >
        <span aria-hidden="true">♥</span> Donate
      </a>
    </>
  );
}
