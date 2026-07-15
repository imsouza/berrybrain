"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    if (process.env.NEXT_PUBLIC_BERRYBRAIN_LANDING_ONLY === "true") {
      navigator.serviceWorker.getRegistrations()
        .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
        .catch(() => {});
      if ("caches" in window) {
        caches.keys()
          .then((keys) => Promise.all(keys.filter((key) => key.startsWith("berrybrain-")).map((key) => caches.delete(key))))
          .catch(() => {});
      }
      return;
    }
    const host = window.location.hostname;
    const localHost = host === "localhost" || host === "127.0.0.1";
    if (!window.isSecureContext && !localHost) return;

    const base = window.location.pathname.startsWith("/berrybrain") ? "/berrybrain" : "";
    const register = () => {
      navigator.serviceWorker
        .register(base + "/sw.js", { scope: base + "/" })
        .catch(() => {});
    };

    if (document.readyState === "complete") {
      register();
      return;
    }

    window.addEventListener("load", register, { once: true });
    return () => window.removeEventListener("load", register);
  }, []);

  return null;
}
