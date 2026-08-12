"use client";

import { useEffect } from "react";

export function PwaRegister() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;
    if (process.env.NODE_ENV !== "production") {
      navigator.serviceWorker.getRegistrations()
        .then((registrations) => Promise.all(registrations.map((registration) => registration.unregister())))
        .catch(() => {});
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
