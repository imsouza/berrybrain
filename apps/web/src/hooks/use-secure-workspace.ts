"use client";

import { useEffect, useState } from "react";
import { appPath, getApiUrl } from "@/contexts/workspace-context";
import {
  hasRecentAuthenticatedSession,
  verifyAuthenticatedSession,
} from "@/lib/auth-session-cache";

export function useSecureWorkspace(nextRoute: string) {
  const apiUrl = getApiUrl();
  const [allowed, setAllowed] = useState(hasRecentAuthenticatedSession);

  useEffect(() => {
    let active = true;
    async function verify() {
      try {
        const authenticated = await verifyAuthenticatedSession(apiUrl);
        if (!active) return;
        if (authenticated) {
          setAllowed(true);
          return;
        }
        const setupResponse = await fetch(`${apiUrl}/api/v1/setup/status`, {
          credentials: "include",
        });
        if (!active) return;
        const setup = setupResponse.ok ? await setupResponse.json() : null;
        window.location.href = setup?.needsSetup
          ? appPath("/setup")
          : appPath(`/login?next=${encodeURIComponent(nextRoute)}`);
      } catch {
        if (active) {
          window.location.href = appPath(`/login?next=${encodeURIComponent(nextRoute)}`);
        }
      }
    }
    void verify();
    return () => {
      active = false;
    };
  }, [apiUrl, nextRoute]);

  return allowed;
}
